import os
from score.init import init
import configparser
from elasticsearch_dsl import Search
from score.es6.dsl import DslExtension


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
        assert isinstance(ctx.es, DslExtension)
        assert isinstance(ctx.es.dsl.search(), Search)
