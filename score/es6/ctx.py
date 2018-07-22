class CtxProxy:

    def __init__(self, conf, ctx):
        self._es6_conf = conf
        self._ctx = ctx

    @property
    def client(self):
        return self._es6_conf.client
