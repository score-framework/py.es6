import os
from score.init import init
import configparser


config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__),
                         '..', 'pytest.ini'))
valid_host = config['es6']['valid_host']
index = config['es6'].get('index', 'score-test')


def test_insert_and_retrieve():
    score = init({
        'score.init': {'modules': 'score.es6'},
        'es6': {'args.hosts': valid_host},
    })
    client = score.es6.client
    client.indices.create(
        index=index, ignore=400)
    client.index(
        index=index, doc_type='text', id=1, body={
            'title': 'foo',
            'body': 'bar',
        })
    query = {"query": {"match_all": {}}}
    hits = client.search(index=index, body=query)['hits']['hits']
    assert len(hits) == 1
    assert hits[0]['_id'] == '1'
    assert hits[0]['_source']['title'] == 'foo'
    assert hits[0]['_source']['body'] == 'bar'
