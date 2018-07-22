import os
from score.ctx import Context
from score.init import init, InitializationError
from score.es6 import CtxProxy
import configparser
from unittest.mock import Mock
import pytest


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
    mock = Mock()

    class ProxyExtension(CtxProxy):

        def __init__(self, *args):
            mock(*args)
            super().__init__(*args)

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
        mock.assert_called_once()
        mock.assert_called_with(score.es6, ctx)


def test_invalid_ctx_extension():

    class ProxyExtension:  # Error: does not inherit CtxProxy
        pass

    with pytest.raises(InitializationError):
        score = init({
            'score.init': {'modules': ['score.es6', 'score.ctx']},
            'es6': {'args.hosts': host, 'ctx.extensions': [ProxyExtension]},
        })
