from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal, Any


@dataclass
class User:
    id: int
    is_bot: bool
    username: Optional[str] = None
    name: Optional[str] = None
    language_code: Optional[str] = None
    raw: dict = None

@dataclass
class Chat:
    id: int
    type: Literal["channel", "group", "private"]
    title: Optional[str] = None
    username: Optional[str] = None
    name: Optional[str] = None
    raw: dict = None

# @dataclass
# class ChatPhoto:
#     small_image_id: str
#     small_image_unique_id: str
#     large_image_id: str
#     large_image_unique_id: str
#     raw: dict = None
#
# @dataclass
# class ChatFullInfo:
#     id: int
#     type: Literal["channel", "group", "private"]
#     title: Optional[str] = None
#     username: Optional[str] = None
#     name: Optional[str] = None
#     photo: Optional[ChatPhoto] = None
#     bio: Optional[str] = None
#     description: Optional[str] = None
#     invite_link: Optional[str] = None
#     linked_chat_id: Optional[str] = None
#     raw: dict = None

@dataclass
class Message:
    id: int
    chat_id: int
    chat: Chat
    date: int
    client: Any = None
    text: Optional[str] = None
    user: Optional[User] = None
    forward_from: Optional[User] = None
    reply_to: Optional["Message"] = None
    edit_date: Optional[int] = None
    raw: dict = None

    async def reply(self, text, reply_markup=None):
        await self.client.send_message(self.chat_id, text, reply_markup=reply_markup, reply_to_message_id=self.id)

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
