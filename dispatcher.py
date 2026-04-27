import inspect
from typing import Callable, List
import asyncio

from .routers import safe_coro
from .models import Message, CallbackQuery, AnswerCallbackQuery


class Dispatcher:
    def __init__(self, client):
        self.client = client
        self._callback_handlers = []
        self.message_handlers: List[tuple] = []
        self.user_tasks = []
        self.running_tasks = []

    def on_callback(self, data=None):
        def decorator(func):
            self._callback_handlers.append((data, func))
            return func

        return decorator

    def on_message(self, filters=None):
        def decorator(func):
            self.message_handlers.append((filters, func))
            return func
        return decorator

    def task(self, interval=None):
        def decorator(func):
            self.user_task(func, interval)
            return func
        return decorator

    def start_tasks(self):
        for func, interval in self.user_tasks:
            task = asyncio.create_task(self._task_runner(func, interval))
            self.running_tasks.append(task)

    async def _task_runner(self, func, interval):

        while True:
            try:
                if inspect.iscoroutinefunction(func):
                    await func()
                else:
                    func()

            except Exception as e:
                print(f"Task crashed: {func.__name__}: {e}")

            if interval is None:
                break

            await asyncio.sleep(interval)

    async def stop_tasks(self):
        for t in self.running_tasks:
            t.cancel()

        await asyncio.gather(*self.running_tasks, return_exceptions=True)
        self.running_tasks.clear()

    async def emit_message(self, message: Message):
        for filters, handler in self.message_handlers:
            sig = inspect.signature(handler)
            if len(sig.parameters) != 1:
                raise RuntimeError("Handlers must accept exactly one argument (message)")

            # بدون فیلتر => همیشه اجرا
            if filters is None:
                await handler(message)
                continue

            # اگر لیست فیلتر بود => هرکدوم True بشه، اجرا
            if isinstance(filters, (list, tuple)):
                ok = any(f(message) for f in filters)
            else:
                ok = filters(message)

            if ok:
                await handler(message)

    def user_task(self, func, interval):
        self.user_tasks.append((func, interval))


    async def emit_callback(self, callback_query: CallbackQuery):
        data = callback_query.data

        for handler_data, handler in self._callback_handlers:
            answer = None

            if callable(handler_data):
                # MagicFilter یا هر callable
                if handler_data(callback_query):
                    answer = await handler(callback_query)
            elif handler_data == data:
                answer = await handler(callback_query)

            if not isinstance(answer, AnswerCallbackQuery):
                await self.client.answer_callback_query(callback_query.id)
            else:
                await self.client.answer_callback_query(callback_query.id, answer)
