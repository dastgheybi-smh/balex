is_admin = lambda l: lambda F: F.chat_id in l
not_admin = lambda l: lambda F: not F.chat_id in l
text = lambda txt: lambda F: F.text == txt
state = lambda status: lambda F: F.state == status
chat_id = lambda cid: lambda F: F.chat_id == cid
command = lambda cmd: text(f"/{cmd}")
start = command("start")
