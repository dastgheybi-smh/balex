from json import dumps
from typing import Literal

import aiohttp
from .models import *
import asyncio
from traceback import format_exc

def safe_coro(coro):
    async def runner():
        try:
            await coro
        except Exception:
            print(format_exc())

    return asyncio.create_task(runner())



class BaleAPI:
    BASE = "https://tapi.bale.ai/bot{token}/{method}"

    def __init__(self, token: str, session: Optional[aiohttp.ClientSession] = None):
        self.token = token

        self.session = session

    async def request(self, method: str, data=None, session: Optional[aiohttp.ClientSession] = None):
        url = self.BASE.format(token=self.token, method=method)
        current_session = session or self.session

        if not current_session:
            raise RuntimeError("aiohttp.ClientSession not initialized.")

        data = data or {}
        async with current_session.post(url, data=data, timeout=60) as resp:
            try:
                return await resp.json()
            except aiohttp.ContentTypeError:
                return await resp.text()

class BaseRouter:
    def __init__(self):
        self.routers = []
        self.api = None
        self.dp = None
        self._session = None

    def on_message(self, filters=None, add_to: Literal["start", "end"] = "end"):
        return self.dp.on_message(filters, add_to)

    def on_callback(self, data=None, add_to: Literal["start", "end"] = "end"):
        return self.dp.on_callback(data, add_to)

    def task(self, func):
        self.dp.user_task(func)
        return func


    def inline(self, *rows: dict[str | int, str | int | dict[Literal["callback_data", "web_app", "copy_text", "url"], str | int]]):
        keyboard = []

        for row in rows:
            btn_row = []

            for text, data in row.items():
                if isinstance(data, dict):
                    btn_row.append({
                        "text": text
                    }.update(data))
                else:
                    btn_row.append({
                       "text": text,
                       "callback_data": data
                    })


            keyboard.append(btn_row)

        return {
            "inline_keyboard": keyboard
        }

    def keyboard(self, *rows, resize_keyboard=True, one_time_keyboard=False, selective=False):
        keyboard = []

        for row in rows:
            keyboard.append([{"text": str(btn)} for btn in row])

        return {
            "keyboard": keyboard,
            "resize_keyboard": resize_keyboard,
            "one_time_keyboard": one_time_keyboard,
            "selective": selective
        }

    async def send_message(self, chat_id: int, text: str, reply_markup=None):
        if not self._session:
            raise RuntimeError("Client not running or session not initialized.")

        data = {"chat_id": chat_id, "text": text}

        if reply_markup:
            data["reply_markup"] = dumps(reply_markup)

        return await self.api.request("sendMessage", data, self._session)

    async def send_photo(self, chat_id: int, photo, caption=None, reply_markup=None):
        if not self._session:
            raise RuntimeError("Client not running or session not initialized.")

        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        if reply_markup:
            data.add_field("reply_markup", dumps(reply_markup))

        if caption:
            data.add_field("caption", caption)

        if isinstance(photo, str) and photo.endswith((".jpg", ".jpeg", ".png")):
            data.add_field("photo", open(photo, "rb"), filename=photo)
        else:
            data.add_field("photo", photo)

        return await self.api.request("sendPhoto", data, self._session)

    async def send_file(self, chat_id: int, file_path: str, caption=None, reply_markup=None):
        if not self._session:
            raise RuntimeError("Client not running or session not initialized.")

        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        if reply_markup:
            data.add_field("reply_markup", dumps(reply_markup))


        if caption:
            data.add_field("caption", caption)

        data.add_field(
            "document",
            open(file_path, "rb"),
            filename=file_path
        )

        return await self.api.request("sendDocument", data, self._session)

    async def send_voice(self, chat_id: int, voice, caption=None, reply_markup=None):
        if not self._session:
            raise RuntimeError("Client not running or session not initialized.")

        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        if reply_markup:
            data.add_field("reply_markup", dumps(reply_markup))


        if caption:
            data.add_field("caption", caption)

        if isinstance(voice, str) and voice.endswith((".ogg", ".mp3", ".opus")):
            data.add_field("voice", open(voice, "rb"), filename=voice)
        else:
            data.add_field("voice", voice)

        return await self.api.request("sendVoice", data, self._session)

    async def send_video(self, chat_id: int, video, caption=None, reply_markup=None):
        if not self._session:
            raise RuntimeError("Client not running or session not initialized.")
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        if reply_markup:
            data.add_field("reply_markup", dumps(reply_markup))

        if caption:
            data.add_field("caption", caption)

        if isinstance(video, str) and video.endswith((".mp4", ".mkv", ".mov")):
            data.add_field("video", open(video, "rb"), filename=video)
        else:
            data.add_field("video", video)

        return await self.api.request("sendVideo", data, self._session)

    async def send_location(self, chat_id, lat, lon, reply_markup=None):
        if not self._session:
            raise RuntimeError("Client not running or session not initialized.")
        return await self.api.request("sendLocation", {
            "chat_id": chat_id,
            "latitude": lat,
            "longitude": lon,
            "reply_markup": reply_markup
        }, self._session)


    def include_router(self, router):
        for router in router.routers:
            if not router in self.routers:
                self.include_router(router)

        if not router in self.routers: self.routers.append(router)


class Router(BaseRouter):
    def __init__(self):
        super().__init__()
        self._callback_handlers = []
        self.message_handlers = []
        self.tasks = []

    def on_callback(self, filters=None, add_to: Literal["start", "end"] = "end"):
        def decorator(func):
            self._callback_handlers.insert(index, (func, filters))
            return func

        return decorator

    def task(self, func):
        self.tasks.append(func)
        return func

    def on_message(self, filters=None, add_to: Literal["start", "end"] = "end"):
        def decorator(func):
            self.message_handlers.insert(index, (func, filters))
            return func
        return decorator

    def install(self, dispatcher, api, session):
        self.api = api
        self.dp = dispatcher
        self._session = session
        return {"callback_handlers": self._callback_handlers, "message_handlers": self.message_handlers, "tasks": self.tasks}

