import rnc
from fastapi.testclient import TestClient

from vocabulary.main import app


rnc.logger.disabled = True
client = TestClient(app)


def test_getting_corpus_examples_with_default_args():
    resp = client.get('/examples/corpus/get')
    json = resp.json()

    assert resp.status_code == 200
    # 10 pages by default
    assert json['count'] >= 100
    assert json['count'] == len(json['examples'])
    assert json['lang'] == 'en'
    assert json['examples']
    assert all(
        {'get', 'getting', 'got'} | set(v['found_wordforms'])
        for v in json['examples']
    )


def test_custom_queries(sleep):
    resp = client.get('/examples/corpus/get?pages_count=1&lang=en')
    json = resp.json()

    assert resp.status_code == 200
    # 10 pages by default
    assert json['count'] >= 5
    assert json['count'] == len(json['examples'])
    assert json['examples']
    assert json['lang'] == 'en'
    assert all(
        {'get', 'getting', 'got'} | set(v['found_wordforms'])
        for v in json['examples']
    )


def test_custom_lang_query(sleep):
    resp = client.get('/examples/corpus/пальто?pages_count=1&lang=fr')
    json = resp.json()

    assert resp.status_code == 200
    # 10 pages by default
    assert json['count'] >= 5
    assert json['count'] == len(json['examples'])
    assert json['examples']
    assert json['lang'] == 'fr'

    assert all(
        'пальто' in v['found_wordforms']
        for v in json['examples']
    )


def test_invalid_lang():
    resp = client.get('/examples/corpus/пальто?pages_count=1&lang=shue')
    assert resp.status_code == 422


def test_invalid_pages_count_type():
    resp = client.get('/examples/corpus/пальто?pages_count=ff&lang=en')
    assert resp.status_code == 422


def test_invalid_pages_count_zero():
    resp = client.get('/examples/corpus/пальто?pages_count=0&lang=en')
    assert resp.status_code == 422


def test_examples_is_sorted(sleep):
    resp = client.get('/examples/corpus/я?pages_count=5&lang=en')
    json = resp.json()
    corp_ex = json['examples']

    for ex_index in range(1, json['count']):
        assert len(corp_ex[ex_index - 1]) <= len(corp_ex[ex_index])
