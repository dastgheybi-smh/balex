from . import FSM
from .models import *


def is_admin(admin_list):
    "a feed-needed filter to determine if a user is an admin"
    def wrapper(message: Message, admin_list=admin_list):
        return message.chat_id in admin_list

    return wrapper

def not_admin(admin_list):
    "a feed-needed filter to determine if a user is not an admin"
    def wrapper(message: Message, admin_list=admin_list):
        return not message.chat_id in admin_list

    return wrapper

def text(text):
    "a filter to check the user's message"
    def wrapper(message: Message, text=text):
        return message.text == text

    return wrapper

def state(state):
    "a filter to check the user's state"
    def wrapper(message: Message, fsm:FSM, state=state):
        return fsm.state == state

    return wrapper

def chat_id(chat_id):
    "a filter to check the user's chat_id"
    def wrapper(message: Message, chat_id=chat_id):
        return message.chat_id == chat_id

    return wrapper

def command(command):
    "a filter to check the user's command(a text starts with '/')"
    return text(f"/{command}")


start = command("start")

def user_id(user_id):
    "a filter to check the user's user_id (it's different with chat_id)"
    def wrapper(message: Message, user_id=user_id):
        try:
            tid = message.user.id
        except AttributeError:
            tid = None

        return user_id == tid

    return wrapper
