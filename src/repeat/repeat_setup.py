__all__ = ['repeat']

from sys import argv
from src.repeat.repeat import RepeatWords
from PyQt5.QtWidgets import QApplication


def repeat(_sample, _title, **params):
    app = QApplication(argv)

    _repeat = RepeatWords(words=_sample,
                          window_title=_title,
                          **params)

    _repeat.test()
    _repeat.show()

    exit(app.exec_())
