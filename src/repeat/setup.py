__all__ = 'repeat'

from sys import argv

from PyQt5.QtWidgets import QApplication

from src.repeat.repeat import RepeatWords
from src.trouble.trouble import Trouble


def repeat(sample: list,
           title: str,
           **params) -> None:
    """ Run repeating.

    :param sample: list of Word, items to repeat.
    :param title: string, the main window title.
    :keyword mode: int or string, repeating mode.
    :return: None.
    :exception Trouble: if wrong type given.
    """
    trbl = Trouble(repeat, _t=True)

    if not (isinstance(sample, list) and sample):
        raise trbl(sample, _p='w_list')
    if not isinstance(title, str):
        raise trbl(title, _p='w_str')

    _app = QApplication(argv)
    _repeat = RepeatWords(sample, title, **params)
    _repeat.test()
    _repeat.show()
    exit(_app.exec_())
