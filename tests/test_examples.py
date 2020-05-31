import pytest
from src.examples.examples import *
from pickle import load
from src.trouble.trouble import Trouble


pce = EnglishCorpusExamples('get', 10)


def test_len_pce():
    assert len(pce) == 10


def test_bool_pce():
    assert bool(pce)


def test_get_pce():
    assert len(pce.get(10)) == 10
    assert len(pce.get(5)) == 5


def test_get_zero_pce():
    assert len(pce.get(0)) == 0


def test_wrong_count_larger_pce():
    with pytest.raises(Trouble):
        EnglishCorpusExamples('get', 46)


def test_wrong_count_less_pce():
    with pytest.raises(Trouble):
        EnglishCorpusExamples('get', -1)
        EnglishCorpusExamples('get', 0)


def test_word_type_pce():
    with pytest.raises(Trouble):
        EnglishCorpusExamples(11, 10)


def test_word_length_pce():
    with pytest.raises(Trouble):
        EnglishCorpusExamples('', 10)


def test_dict_keys_pce():
    assert all(i['ru'] and i['en'] and i['source'] for i in pce)


rce = RussianCorpusExamples('мастер', 10)


def test_len_rce():
    assert len(rce) == 10


def test_bool_rce():
    assert bool(rce)


def test_get_rce():
    assert len(rce.get(10)) == 10
    assert len(rce.get(5)) == 5


def test_get_zero_rce():
    assert len(rce.get(0)) == 0


def test_wrong_count_larger_rce():
    with pytest.raises(Trouble):
        RussianCorpusExamples('мир', 46)


def test_wrong_count_less_rce():
    with pytest.raises(Trouble):
        RussianCorpusExamples('привет', -1)
        RussianCorpusExamples('мир', 0)


def test_word_type_rce():
    with pytest.raises(Trouble):
        RussianCorpusExamples(11, 10)


def test_word_length_rce():
    with pytest.raises(Trouble):
        RussianCorpusExamples('', 10)


def test_dict_keys_rce():
    assert all(i['text'] and i['source'] for i in rce)


def test_w_path_se():
    with pytest.raises(Trouble):
        SelfExamples('wrong_f_name.txt')


se = SelfExamples('test_self_ex.txt')


def test_load_se():
    assert se == load(open('pkl_content', 'rb'))


def test_find_se():
    assert len(se.find('get')) == 2


def test_count_se():
    assert se.count('get') == 2


def test_find_count_empty_str_se():
    with pytest.raises(Trouble):
        se.find('')


def test_count_empty_str_se():
    with pytest.raises(Trouble):
        se.count('')


def test_find_count_wrong_type_se():
    with pytest.raises(Trouble):
        se.find(1337)


def test_count_count_wrong_type_se():
    with pytest.raises(Trouble):
        se.count(1337)


def test_call_se():
    assert se('get') == se.find('get')


def test_wrong_call_se():
    assert se('ggget') == se.find('ggget')


def test_in_se():
    assert ('get' in se) is True


def test_wrong_in_se():
    assert ('ggget' in se) is False


def test_length_se():
    assert len(se) == 150


def test_async_req():
    from src.examples.examples import get_htmls
    res = get_htmls("https://yandex.ru", 10)
    assert isinstance(res, list) and isinstance(res[0], str)


if __name__ == '__main__':
    pytest.main()