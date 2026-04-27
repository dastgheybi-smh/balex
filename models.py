from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: int
    name: Optional[str] = None


@dataclass
class Message:
    message_id: int
    chat_id: int
    text: Optional[str] = None
    user: Optional[User] = None
    raw: dict = None

@dataclass
class CallbackQuery:
    id: int
    chat_id: int
    data: str = None
    user: User = None
    raw: dict = None
    message: Optional[Message] = None

@dataclass
class AnswerCallbackQuery:
    text: str = None
    show_alert: bool = False
