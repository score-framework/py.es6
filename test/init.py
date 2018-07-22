import os
from score.init import init
import configparser


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__),
                         '..', 'pytest.ini'))
valid_host = config['es6']['valid_host']


def test_defaults():
    score = init({
        'score.init': {'modules': 'score.es6'},
        'es6': {'args.hosts': valid_host},
    })
    assert score.es6.client


def test_destroy():
    score = init({
        'score.init': {'modules': 'score.es6'},
        'es6': {'args.hosts': valid_host},
    })
    score.es6.destroy()


def test_create():
    score = init({
        'score.init': {'modules': 'score.es6'},
        'es6': {'args.hosts': valid_host},
    })
    score.es6.create()
