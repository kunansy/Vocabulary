import pytest
from datetime import date as DATE
from src.main.common_funcs import (
    up_word, str_to_date, get_synonyms
)
from src.trouble.trouble import Trouble


def test_str_to_date_1():
    assert str_to_date('1.12.1970') == DATE(1970, 12, 1)


def test_str_to_date_2():
    assert str_to_date('12.1.1970') == DATE(1970, 1, 12)


def test_str_to_date_3():
    assert str_to_date('12.1.1970') == DATE(1970, 1, 12)


def test_str_to_date_4():
    assert str_to_date('12_1_1970') == DATE(1970, 1, 12)


def test_str_to_date_5():
    assert str_to_date('12_1_1970/1488') == DATE(1970, 1, 12)


def test_str_to_date_6():
    assert str_to_date('12_1_19701488') == DATE(1970, 1, 12)


def test_str_to_date_swap_1():
    assert str_to_date('1.12.1970', True) == DATE(1970, 1, 12)


def test_str_to_date_swap_2():
    assert str_to_date('12.1.1970', True) == DATE(1970, 12, 1)


def test_str_to_date_raise():
    with pytest.raises(Trouble):
        str_to_date([])


def test_str_to_date_by_date_1():
    assert str_to_date(DATE(1970, 1, 12)) == DATE(1970, 1, 12)


def test_str_to_date_by_date_2():
    assert str_to_date(DATE(1970, 12, 12)) == DATE(1970, 12, 12)


def test_str_to_date_by_date_swap():
    assert str_to_date(DATE(1970, 12, 1), True) == DATE(1970, 1, 12)


def test_str_to_date_by_date_swap_2():
    assert str_to_date(DATE(1970, 1, 12), True) == DATE(1970, 12, 1)


def test_up_word_1():
    assert up_word("can YoU show me your preferences?", 'pref') == \
           "can YoU show me your PREFERENCES?"


def test_up_word_3():
    assert up_word('getting the got is getted the god', 'get') == \
           'GETTING the got is GETTED the god'


def test_up_word_4():
    with pytest.raises(Trouble):
        up_word('strinh', '')


def test_up_word_5():
    assert up_word('ungetted the get getted gett gget', 'get') == \
           'UNGETTED the GET GETTED GETT GGET'


def test_up_word_6():
    with pytest.raises(Trouble):
        up_word('', 'get')


def test_up_word_7():
    assert up_word('ungetted the get getted gett gget', 'GeT') == \
           'UNGETTED the GET GETTED GETT GGET'


def test_up_word_8():
    assert up_word('thing the thought thin fault fethef', 'th') == \
           'THING THE THOUGHT THIN fault FETHEF'


def test_up_word_9():
    assert up_word("can YoU show me your preferences?", 'e') == \
           "can YoU show ME your PREFERENCES?"


def test_up_word_10():
    assert up_word("can YoU show me your preferenc9e9s?", 'e') == \
           "can YoU show ME your PREFERENC9E9S?"


def test_up_word_12():
    assert up_word('can', 'can') == 'CAN'


def test_get_synonyms_assert():
    with pytest.raises(Trouble):
        get_synonyms('get the')


def test_get_synonyms_assert2():
    with pytest.raises(Trouble):
        get_synonyms(111)


def test_get_synonyms_assert3():
    with pytest.raises(Trouble):
        get_synonyms('')


def test_get_synonyms_assert4():
    with pytest.raises(Trouble):
        get_synonyms('   ')


def test_get_synonyms_normal():
    res = ['find sth/sb', 'getting sth/sb', 'obtain sth/sb', 'crawled sth/sb',
           'try sth/sb', 'receive sth/sb', 'tell sth/sb', 'scare sth/sb',
           'otherwise PROPN', 'steal sth/sb']
    assert get_synonyms('get') == res


def test_get_synonyms_normal_with_spaces():
    res = ['find sth/sb', 'getting sth/sb', 'obtain sth/sb', 'crawled sth/sb',
           'try sth/sb', 'receive sth/sb', 'tell sth/sb', 'scare sth/sb',
           'otherwise PROPN', 'steal sth/sb']
    assert get_synonyms(' get ') == res

