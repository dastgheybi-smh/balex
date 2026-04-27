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
            name = None if not name.split() else name
            self.client.install_plugin(plugin, name)
        if self.name is None:
            raise RuntimeError(f"Plugin name not set(if you are using plugin, contact this error to maker)")

    def include_router(self, router):
        self.routers.append(router)

    def install_plugin(self, plugin, name=None):
        self.plugins[name] = plugin

    def setup(self):
        raise NotImplementedError

