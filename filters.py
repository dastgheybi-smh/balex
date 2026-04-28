is_admin = lambda l: lambda F, li=l: F.chat_id in li
not_admin = lambda l: lambda F, li=l: not F.chat_id in li
text = lambda txt: lambda F, txt2=txt : F.text == txt2
state = lambda status: lambda M, F, stat=status: F.state == stat
chat_id = lambda cid: lambda F, id=cid: F.chat_id == id
command = lambda cmd: text(f"/{cmd}")
start = command("start")
