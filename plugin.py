from logging import debug

class Plugin:
    def __init__(self, client):
        self.client = client
        self.name = None
        self.setup()
        if self.name is None:
            raise RuntimeError(f"Plugin name not set(if you are using plugin, contact this error to maker)")


    def setup(self):
        raise NotImplementedError

