import asyncio
import aiohttp
from typing import Literal, Type
from traceback import format_exc
from .models import CallbackQuery, AnswerCallbackQuery
from .dispatcher import Dispatcher, FSMFactory
from .models import Message, User
import logging as log

from .plugin import Plugin
from .routers import BaleAPI, BaseRouter, Router, safe_coro




class Client(BaseRouter):
    def __init__(self, token: str,
                 mode: Literal['webhook', 'polling'] = "polling",
                 webhook_url: str = None,
                 default_state: str = None,
                 without_state: bool = False,
                 reactive_var_class = None,
                 wallet_token: str = None):
        super().__init__()
        self.token = token
        self.fsm_factory = FSMFactory(reactive_var_class)
        if not without_state:
            self.fsm_factory.new_rv("state", default_state)
        self.dp = Dispatcher(self)
        self.offset = 0
        self.running = False
        self.mode = mode
        self.webhook_url = webhook_url
        self.wallet_token = wallet_token
        self.plugins = {}


    async def answer_callback_query(
            self,
            callback_query_id: str,
            answer: AnswerCallbackQuery = None
    ):

        data = {
            "callback_query_id": callback_query_id
        }

        answer = answer or AnswerCallbackQuery()

        if answer.text:
            data["text"] = answer.text

        if answer.show_alert:
            data["show_alert"] = answer.show_alert

        return await self.api.request("answerCallbackQuery", data, self._session)

    def install_plugin(self, plugin: Type[Plugin], name: str = None):
        plg = plugin(self)
        name = name or plg.name
        for router in plg.routers:
            self.include_router(router)
        for name, plugin in plg.plugins.items():
            self.install_plugin(plugin, name)
        setattr(self, name, plg)

    async def _install_routers_plugins(self):
        for router in self.routers:
            callbacks = router.install(self.dp, self.api, self._session)
            self.dp._callback_handlers.extend(callbacks["callback_handlers"])
            self.dp.message_handlers.extend(callbacks["message_handlers"])
            self.dp.user_tasks.extend(callbacks["tasks"])

    def task(self, interval=None):
        return self.dp.task(interval)

    async def poll_updates(self):
        self._session = aiohttp.ClientSession()
        self.api = BaleAPI(self.token, self._session)

        await self._install_routers_plugins()
        self.dp.start_tasks()

        while self.running:
            try:
                result = await self.api.request("getUpdates", {"offset": self.offset, "timeout": 20})

                if not result or not result.get("result"):
                    await asyncio.sleep(1)
                    continue

                for upd in result["result"]:
                    self.offset = upd["update_id"] + 1
                    log.debug(f"Update received with {self.offset=}")

                    if "callback_query" in upd:
                        raw = upd["callback_query"]
                        safe_coro(self.dp.emit_callback(CallbackQuery(
                            id=raw["id"],
                            chat_id=raw["chat_instance"],
                            data=raw.get("data"),
                            user=User(id=raw["from"]["id"], name=raw["from"].get("first_name")),
                            message=Message(
                                message_id=raw["message"]["message_id"],
                                chat_id=raw["message"]["chat"]["id"],
                                text=raw["message"].get("text"),
                                user=User(id=raw["from"]["id"], name=raw["from"].get("first_name")),
                                raw=raw["message"],
                            ),
                            raw=raw,
                        )))

                    if "message" in upd:
                        raw = upd["message"]
                        msg = Message(
                            message_id=raw["message_id"],
                            chat_id=raw["chat"]["id"],
                            text=raw.get("text"),
                            user=User(id=raw["from"]["id"], name=raw["from"].get("first_name")),
                            raw=raw,
                        )
                        safe_coro(self.dp.emit_message(msg))

            except aiohttp.ClientError as e:
                print(f"aiohttp error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"An unexpected error occurred: \n{format_exc()}")
                await asyncio.sleep(5)
        await self.dp.stop_tasks()
        await self._session.close()

    async def setup_webhook(self):
        self._session = aiohttp.ClientSession()
        self.api = BaleAPI(self.token, self._session)

        await self._install_routers_plugins()
        safe_coro(self.dp.start_tasks())

        await self.api.request("setWebhook", {"url": self.webhook_url})
        print(f"Webhook set to: {self.webhook_url}")

        from aiohttp import web

        async def handle(request):
            try:
                upd = await request.json()
                if "callback_query" in upd:
                    raw = upd["callback_query"]
                    safe_coro(self.dp.emit_callback(CallbackQuery(
                        id=raw["id"],
                        chat_id=raw["chat_instance"],
                        data=raw.get("data"),
                        user=User(id=raw["from"]["id"], name=raw["from"].get("first_name")),
                        message=Message(
                            message_id=raw["message"]["message_id"],
                            chat_id=raw["message"]["chat"]["id"],
                            text=raw["message"].get("text"),
                            user=User(id=raw["from"]["id"], name=raw["from"].get("first_name")),
                            raw=raw["message"],
                        ),
                        raw=raw,
                    )))

                if "message" in upd:
                    raw = upd["message"]
                    msg = Message(
                        message_id=raw["message_id"],
                        chat_id=raw["chat"]["id"],
                        text=raw.get("text"),
                        user=User(id=raw["from"]["id"], name=raw["from"].get("first_name")),
                        raw=raw,
                    )
                    safe_coro(self.dp.emit_message(msg))
            except Exception as e:
                print(f"Error processing webhook request: {e}")
            return web.Response(text="OK")

        app = web.Application()
        app.router.add_post(f"/{self.token}", handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        print(f"Webhook server running on port 8080 with route /{self.token}")
        await site.start()
        while self.running:
            await asyncio.sleep(1)

        await runner.cleanup()
        await self._session.close()

    def run(self):
        log.basicConfig(level=log.DEBUG)
        log.info(f"Starting BaleX Client {self.mode} mode...")
        self.running = True
        try:
            if self.mode == "polling":
                asyncio.run(self.poll_updates())
            elif self.mode == "webhook":
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    safe_coro(self.setup_webhook())
                else:
                    asyncio.run(self.setup_webhook())
            else:
                raise ValueError("mode must be 'polling' or 'webhook'")
        except KeyboardInterrupt:
            log.info("Shutting down...")
            self.running = False
        finally:
            self.running = False
            if self._session and not self._session.closed:
                asyncio.run(self._session.close())

Bot = Client