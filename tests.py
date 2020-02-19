import pytest
from main import *


def test_str_to_date_1():
    assert str_to_date('1.12.1970') == DATE(1970, 12, 1)


def test_str_to_date_2():
    assert str_to_date('12.1.1970') == DATE(1970, 1, 12)


def test_str_to_date_3():
    assert str_to_date('12.1.1970.1488') == DATE(1970, 1, 12)


def test_str_to_date_4():
    assert str_to_date('12_1_1970_1488') == DATE(1970, 1, 12)


def test_str_to_date_swap_1():
    assert str_to_date('1.12.1970', True) == DATE(1970, 1, 12)


def test_str_to_date_swap_2():
    assert str_to_date('12.1.1970', True) == DATE(1970, 12, 1)


def test_str_to_date_raise():
    with pytest.raises(AssertionError):
        str_to_date([])


def test_str_to_date_by_date_1():
    assert str_to_date(DATE(1970, 1, 12)) == DATE(1970, 1, 12)


def test_str_to_date_by_date_2():
    assert str_to_date(DATE(1970, 12, 12)) == DATE(1970, 12, 12)
