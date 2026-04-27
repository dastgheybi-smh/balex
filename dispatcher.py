import inspect
from typing import Callable, List
import asyncio

from .routers import safe_coro
from .models import Message, CallbackQuery, AnswerCallbackQuery


class ReactiveVar:
    def __init__(self, name, default):
        self.data = {}
        self.name = name
        self.default = default

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        NO_VALUE = lambda: None
        if self.data.get(key, NO_VALUE) == NO_VALUE:
            self.data[key] = self.default
        return self.data[key]

class FSM:
    def __init__(self, key, **reactive_vars):
        self.key = key
        for name, rv in reactive_vars.items():
            setattr(
                self.__class__,
                name,
                property(
                    lambda self, rv=rv: rv.get(self.key),
                    lambda self, value, rv=rv: rv.set(self.key, value)
                )
            )


class FSMFactory:
    def __init__(self, reactive_var_class=None):
        self.reactive_var_class = reactive_var_class or ReactiveVar
        self.reactive_vars = {}

    def new_rv(self, name, default=""):
        self.reactive_vars[name] = self.reactive_var_class(name, default)

    def get_fsm(self, key):
        return FSM(key, **self.reactive_vars)


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

    def safe_filter(self, filter, m, fsm):
        sig = inspect.signature(filter)
        if len(sig.parameters) == 1:
            return filter(m)
        if len(sig.parameters) == 2:
            return filter(m, fsm)
        else:
            raise RuntimeError("Filter must have exactly 1 or 2 parameters")


    async def emit_message(self, message: Message):
        for filters, handler in self.message_handlers:
            sig = inspect.signature(handler)
            fsm = self.client.fsm_factory.get_fsm(message.chat_id)
            if len(sig.parameters) == 1 or len(sig.parameters) == 2:
                if filters is None:
                    await self.safe_filter(handler, message, fsm)
                    continue
                if isinstance(filters, (list, tuple)):
                    ok = any(self.safe_filter(f, message, fsm) for f in filters)
                else:
                    ok = self.safe_filter(filters, message, fsm)

                if ok:
                    await self.safe_filter(handler, message, fsm)

            else:
                raise RuntimeError("Handlers must accept exactly one argument or 2 arguments with FSM (message)")

    def user_task(self, func, interval):
        self.user_tasks.append((func, interval))


    async def emit_callback(self, callback_query: CallbackQuery):
        data = callback_query.data
        fsm = self.client.fsm_factory.get_fsm(callback_query.chat_id)

        for handler_data, handler in self._callback_handlers:
            answer = None


            if callable(handler_data):
                if self.safe_filter(handler_data, callback_query, fsm):
                    answer = await self.safe_filter(handler, callback_query, fsm)

            elif handler_data == data:
                answer = await self.safe_filter(handler, callback_query, fsm)


            if not isinstance(answer, AnswerCallbackQuery):
                await self.client.answer_callback_query(callback_query.id)
            else:
                await self.client.answer_callback_query(callback_query.id, answer)

