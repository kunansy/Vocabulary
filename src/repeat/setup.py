__all__ = 'repeat'

from sys import argv

from PyQt5.QtWidgets import QApplication

from src.repeat.repeat import RepeatWords


def repeat(sample: list,
           title: str,
           **params) -> None:
    """ Run repeating.

    :param sample: list of Word, items to repeat.
    :param title: string, the main window title.
    :keyword mode: int or string, repeating mode.
    :return: None.
    """
    app = QApplication(argv)
    repeat = RepeatWords(sample, title, **params)
    repeat.test()
    repeat.show()
    exit(app.exec_())
