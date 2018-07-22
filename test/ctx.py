import os
from score.ctx import Context
from score.init import init
from score.es6 import CtxProxy
import configparser


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__),
                         '..', 'pytest.ini'))
host = config['es6']['valid_host']


def test_defaults():
    score = init({
        'score.init': {'modules': ['score.es6', 'score.ctx']},
        'es6': {'args.hosts': host},
    })
    with score.ctx.Context() as ctx:
        assert isinstance(ctx.es, CtxProxy)


def test_ctx_extension():

    class ProxyExtension:

        def __init__(self, **kwargs):
            assert 'conf' in kwargs
            assert isinstance(kwargs['conf'], ConfiguredEs6Module)
            assert isinstance(kwargs['ctx'], Context)

        def foo(self):
            return 'bar'

    score = init({
        'score.init': {'modules': ['score.es6', 'score.ctx']},
        'es6': {'args.hosts': host, 'ctx.extensions': [ProxyExtension]},
    })
    with score.ctx.Context() as ctx:
        assert isinstance(ctx.es, CtxProxy)
        assert isinstance(ctx.es, ProxyExtension)
        assert ctx.es.foo() == 'bar'
