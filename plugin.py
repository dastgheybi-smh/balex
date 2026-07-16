from aiohttp import FormData


class Plugin:
    def __init__(self, client):
        self.client = client
        self.name = None
        self.routers = []
        self.plugins = {}
        self.setup()
        for router in self.routers:
            client.include_router(router)
        for name, plugin in self.plugins.items():
            name = None if not name.strip() else name
            self.client.install_plugin(plugin, name)
        if self.name is None:
            raise RuntimeError(f"Plugin name not set(if you are using plugin, contact this error to maker)")

    def include_router(self, router):
        self.routers.append(router)

    def install_plugin(self, plugin, name=None):
        self.plugins[name] = plugin

    def setup(self):
        raise NotImplementedError


# ---------- Built-in Plugins ----------------


class ChatPlugin(Plugin):
    def setup(self):
        self.name = "chat_plugin"

    async def _request(self, method: str, data=None):
        if not self.client._session:
            raise RuntimeError("Client not running.")

        return await self.client.api.request(
            method,
            data or {},
            self.client._session
        )

    async def ban_chat_member(self, chat_id: int, user_id: int, until_date: int = None):
        data = {
            "chat_id": chat_id,
            "user_id": user_id
        }

        if until_date is not None:
            data["until_date"] = until_date

        return await self._request("banChatMember", data)

    async def unban_chat_member(self, chat_id: int, user_id: int):
        return await self._request("unbanChatMember", {
            "chat_id": chat_id,
            "user_id": user_id
        })

    async def promote_chat_member(self, chat_id: int, user_id: int, **permissions):
        data = {
            "chat_id": chat_id,
            "user_id": user_id,
            **permissions
        }

        return await self._request("promoteChatMember", data)

    async def set_chat_photo(self, chat_id: int, photo):
        data = FormData()
        data.add_field("chat_id", str(chat_id))

        if isinstance(photo, str):
            data.add_field(
                "photo",
                open(photo, "rb"),
                filename=photo.split("/")[-1]
            )
        else:
            data.add_field("photo", photo)

        return await self._request("setChatPhoto", data)

    async def leave_chat(self, chat_id: int):
        return await self._request("leaveChat", {
            "chat_id": chat_id
        })

    async def get_chat(self, chat_id: int):
        return await self._request("getChat", {
            "chat_id": chat_id
        })

    async def get_chat_administrators(self, chat_id: int):
        return await self._request("getChatAdministrators", {
            "chat_id": chat_id
        })

    async def get_chat_members_count(self, chat_id: int):
        return await self._request("getChatMembersCount", {
            "chat_id": chat_id
        })

    async def get_chat_member(self, chat_id: int, user_id: int):
        return await self._request("getChatMember", {
            "chat_id": chat_id,
            "user_id": user_id
        })

    async def pin_chat_message(self, chat_id: int, message_id: int, disable_notification: bool = False):
        return await self._request("pinChatMessage", {
            "chat_id": chat_id,
            "message_id": message_id,
            "disable_notification": disable_notification
        })

    async def unpin_chat_message(self, chat_id: int):
        return await self._request("unPinChatMessage", {
            "chat_id": chat_id
        })

    async def unpin_all_chat_messages(self, chat_id: int):
        return await self._request("unpinAllChatMessages", {
            "chat_id": chat_id
        })

    async def set_chat_title(self, chat_id: int, title: str):
        return await self._request("setChatTitle", {
            "chat_id": chat_id,
            "title": title
        })

    async def set_chat_description(self, chat_id: int, description: str):
        return await self._request("setChatDescription", {
            "chat_id": chat_id,
            "description": description
        })

    async def delete_chat_photo(self, chat_id: int):
        return await self._request("deleteChatPhoto", {
            "chat_id": chat_id
        })

    async def create_chat_invite_link(self, chat_id: int, **kwargs):
        data = {
            "chat_id": chat_id,
            **kwargs
        }

        return await self._request("createChatInviteLink", data)

    async def revoke_chat_invite_link(self, chat_id: int, invite_link: str):
        return await self._request("revokeChatInviteLink", {
            "chat_id": chat_id,
            "invite_link": invite_link
        })

    async def export_chat_invite_link(self, chat_id: int):
        return await self._request("exportChatInviteLink", {
            "chat_id": chat_id
        })

