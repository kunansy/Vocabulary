__all__ = 'RepeatWords'

import random as rand
from typing import List

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QWidget, QMainWindow
)

from src.examples.examples import (
    EnglishCorpusExamples, RussianCorpusExamples, SelfExamples
)
from src.main.common_funcs import *
from src.main.constants import *
from src.trouble.trouble import Trouble


# TODO: working with Russian


class RepeatWords(QMainWindow):
    def __init__(self,
                 _sample: List,
                 _title: str = 'Repeat',
                 mode: int = 1) -> None:
        from src.main.main import Word
        trbl = Trouble(self.__init__, _t=True)

        if not MAIN_WINDOW_PATH.exists():
            raise trbl(MAIN_WINDOW_PATH, _p='w_file')
        if not EXAMPLES_WINDOW_PATH.exists():
            raise trbl(EXAMPLES_WINDOW_PATH, _p='w_file')
        if not MESSAGE_WINDOW_PATH.exists():
            raise trbl(MESSAGE_WINDOW_PATH, _p='w_file')
        if not SHOW_WINDOW_PATH.exists():
            raise trbl(SHOW_WINDOW_PATH, _p='w_file')

        if not (isinstance(_sample, list) and list):
            raise trbl(_sample, _p='w_list')
        # if not all(isinstance(i, Word) for i in words):
        #     raise trbl(f"Wrong list elements", "Word obj")
        if not isinstance(mode, (str, int)):
            raise trbl(f"Wrong mode type: '{mode}'", "int or str")
        if not (mode in ENG_REPEAT_MODS or mode in range(1, len(ENG_REPEAT_MODS) + 1)):
            raise trbl(f"Wrong mode: '{mode}'")
        if not isinstance(_title, str):
            raise trbl(f"Wrong window title: '{_title}'", "str")

        super().__init__()
        uic.loadUi(MAIN_WINDOW_PATH, self)
        self.initUI(_title)

        self.word = Word('')
        # self.repeating_word_index = None
        # self.repeated_words_indexes = []
        rand.shuffle(_sample)
        self.words = _sample[:]
        self.w_trans = list(reversed(_sample[:]))

        self.mode = None
        self.are_you_right = None
        self.init_button = None
        self.main_item = None

        self.mode = mode if isinstance(mode, int) else ENG_REPEAT_MODS[mode]
        self.init_fit_mode()

        # TODO: open it in init, write to the file while program works,
        #  close the file in __del__
        # create log file if there's no
        if not REPEAT_LOG_PATH.exists():
            with REPEAT_LOG_PATH.open('w', encoding='utf-8'):
                pass

    def initUI(self,
               _title: str) -> None:
        self.s_ex = SelfExamples()
        self.ExamplesWindow = ExamplesWindow(self, [], _s_ex=self.s_ex, _c_name='en')
        self.MessageWindow = MessageWindow(self, [])
        self.ShowWindow = ShowWindow(self, [])
        self.setWindowTitle(_title)

        # кнопки выбора вариантов
        self.choice_buttons = [
            self.ChoiceButton1,
            self.ChoiceButton2,
            self.ChoiceButton3,
            self.ChoiceButton4,
            self.ChoiceButton5,
            self.ChoiceButton6
        ]
        for i in range(len(self.choice_buttons)):
            self.choice_buttons[i].clicked.connect(self.are_you_right)

        self.ExitButton.clicked.connect(self.close)
        self.ExitButton.setText('Exit')

        self.HintButton.clicked.connect(self.hint)
        self.HintButton.setText('Hint')

        self.ShowButton.clicked.connect(self.show_words)
        self.ShowButton.setText('Show')

    def init_fit_mode(self) -> None:
        """ Работа в соответствии с mode """
        self.are_you_right = lambda x: x.lower() == self.init_button(self.word).lower()

        if self.mode == 1:
            self.init_button = lambda x: x.get_native(def_only=True).capitalize()
            self.main_item = lambda: self.word.word.capitalize()
        elif self.mode == 2:
            self.init_button = lambda x: x.word.capitalize()
            self.main_item = lambda: self.word.get_native(def_only=True).capitalize()
        elif self.mode == 3:
            self.init_button = lambda x: x.get_native(def_only=True).capitalize()
            self.main_item = lambda: self.word.get_original(def_only=True).capitalize()
        elif self.mode == 4:
            self.init_button = lambda x: x.get_original(def_only=True).capitalize()
            self.main_item = lambda: self.word.get_native(def_only=True).capitalize()

    def test(self) -> None:
        # чтобы не остаться с пустым списком ошибочных переводов под конец
        if self.word and self.word not in self.w_trans:
            self.w_trans += [self.word]

        _len = len(self.words)
        label = "The last one" if _len is 1 else f"Remain {_len} words"
        self.WordsRemainLabel.setText(label)

        self.word = rand.choice(self.words)
        # self.repeating_word_index = CHOICE(range(len(self.words)))
        # self.repeating_word = CHOICE([iter(i) for i in self.words])
        self.words.remove(self.word)
        self.w_trans.remove(self.word)

        self.WordToReapeatBrowser.setText(self.main_item())

        self.set_buttons()

    def set_buttons(self) -> None:
        for i in range(len(self.choice_buttons)):
            self.choice_buttons[i].setText('')

        # ставится ли верное определение
        is_right_def = True

        w_tran = rand.sample(self.w_trans, len(self.choice_buttons))
        length = len(self.choice_buttons)
        for i in rand.sample(range(length), length):
            w_item = rand.choice(w_tran)
            w_tran.remove(w_item)

            if is_right_def:
                self.choice_buttons[i].setText(self.init_button(self.word))
                is_right_def = False
            else:
                self.choice_buttons[i].setText(self.init_button(w_item))

    # def next(self):
    #     if self.repeating_word_index < len(self.words):
    #         self.repeating_word_index += 1
    #         self.text()
    #
    # def past(self):
    #     if self.repeating_word_index > 0:
    #         self.repeating_word_index -= 1
    #         self.test()

    def show_result(self,
                    _result: str,
                    _style: str) -> None:
        self.MessageWindow.display(message=_result, style=_style)

    def are_you_right(self) -> None:
        if self.are_you_right(self.sender().text()):
            self.show_result(_result='<i>Excellent</i>', _style="color: 'green';")

            self.test() if len(self.words) > 0 else self.close()
        else:
            self.log(_w_choice=self.sender().text(), _item=self.word.word)
            self.show_result(_result='<b>Wrong</b>', _style="color: 'red';")

    def hint(self) -> None:
        """ Показать подсказку: связные слова и примеры """
        if self.mode != 1:
            return

        self.ExamplesWindow.display(word=self.word.word,
                                    message=f"{self.HintButton.text()}",
                                    style="color: blue")

    def show_words(self) -> None:
        self.ShowWindow.display(items=self.words,
                                window_title=self.windowTitle())

    def show(self) -> None:
        super().show()
        self.show_words()

    def close(self) -> None:
        """ По нажатии на кнопку 'Exit' закрыть все окна """
        self.ExamplesWindow.close()
        self.MessageWindow.close()
        self.ShowWindow.close()
        super().close()

    def log(self,
            _item: str,
            _w_choice: str) -> None:
        """ Логгирование ошибочных вариантов в json:
            {ID_слова: {ID ошибочного варианта: количество ошибок}}
        """
        from src.main.main import search_by_attribute

        repeating_word_id = word_id(_item)

        # Найти ID слова по выбранному варианту:
        wrong_choice_id = word_id(search_by_attribute(self.w_trans, _w_choice))

        data = load_json(REPEAT_LOG_PATH)

        if repeating_word_id in data:
            if wrong_choice_id in data[repeating_word_id]:
                data[repeating_word_id][wrong_choice_id] += 1
            else:
                data[repeating_word_id][wrong_choice_id] = 1
        else:
            data[repeating_word_id] = {wrong_choice_id: 1}

        dump_json(data=data, f_path=REPEAT_LOG_PATH)

    def backup(self) -> None:
        """ Backup лога повторений """
        from src.backup.setup import backup

        print("Repeat log backupping...")
        backup(REPEAT_LOG_PATH.name, REPEAT_LOG_PATH)


class ExamplesWindow(QWidget):
    CORPORA = {
        'en': EnglishCorpusExamples,
        'ru': RussianCorpusExamples
    }
    CORP_EX_COUNT = 10

    def __init__(self,
                 *args,
                 _s_ex: SelfExamples,
                 _c_name: str) -> None:
        super().__init__()
        uic.loadUi(EXAMPLES_WINDOW_PATH, self)

        self.word = ''
        self.j_word = ''

        self.self_examples_base = _s_ex
        self.corp_name = _c_name
        self.corpus_examples_base = self.CORPORA[_c_name]

        self.c_examples = []
        self.s_examples = []
        self.linked_words = []

        # жирный курсив
        self.marker = lambda x: f"<b><i>{x}</i></b>".upper()
        self.initUI()

    def initUI(self) -> None:
        self.setWindowTitle('Examples')

        self.ResultLabel.setText('')
        self.ExamplesBrowser.setText('')

        self.CorpusExamplesRButton.setChecked(True)

        self.CorpusExamplesRButton.clicked.connect(self.show_corpus_examples)
        self.SelfExamplesRButton.clicked.connect(self.show_self_examples)
        self.LinkedWordsRButton.clicked.connect(self.show_linked_words)

    def get_linked_words(self) -> None:
        """ Инициализировать linked_words,
            получив связные слова
        """
        try:
            # needed word without preps etc
            content = get_synonyms(self.j_word)
        except:
            content = []
        self.linked_words = list(map(str.capitalize, content))[:]

    def get_corpus_examples(self) -> None:
        """ Init self.c_examples by request to the corpus.
        Put there only texts in the language. """
        word = self.word.replace('sth', '').replace('sb', '')

        examples = self.corpus_examples_base(
            word, self.CORP_EX_COUNT, marker=self.marker)
        examples = [
            i[self.corp_name]
            for i in examples
        ]
        rand.shuffle(examples)
        self.c_examples = examples[:]

    def get_self_examples(self) -> None:
        """ Init self.s_examples """
        self.s_examples = self.self_examples_base.find(self.j_word)

    def examples_exist(self) -> bool:
        """ Is there any example """
        return bool(self.c_examples or self.s_examples or self.linked_words)

    def show_corpus_examples(self) -> None:
        """ Установить в поле 'примеры' корпусные примеры,
            либо 'Corpus examples not found'
        """
        if self.c_examples:
            self.show_examples(self.c_examples)
        else:
            self.show_examples([f"Corpus examples to '{self.word}' not found"])

    def show_self_examples(self) -> None:
        """ Установить в поле 'примеры' свои примеры,
            либо 'Self examples not found'
        """
        if self.s_examples:
            self.show_examples(self.s_examples)
        else:
            self.show_examples([f"Self examples to '{self.word}' not found"])

    def show_linked_words(self) -> None:
        """ Установить в поле 'примеры' связные слова """
        if self.linked_words:
            self.show_examples(self.linked_words)
        else:
            self.show_examples([f"Linked words to '{self.word}' not found"])

    def show_examples(self,
                      _ex: List[str]) -> None:
        """ Set examples to the browser, enumerated with 1 end marked words """
        res = [
            f"{self.marker(num)}. {ex}<br>"
            for num, ex in enumerate(_ex, 1)
        ]
        self.ExamplesBrowser.setText('\n'.join(res))

    def show_examples_by_button(self) -> None:
        if self.CorpusExamplesRButton.isChecked():
            self.show_corpus_examples()
        elif self.SelfExamplesRButton.isChecked():
            self.show_self_examples()
        elif self.LinkedWordsRButton.isChecked():
            self.show_linked_words()

    def display(self,
                word: str,
                message: str,
                style: str = '') -> None:
        if word != self.word:
            self.c_examples = []
            self.s_examples = []
            self.linked_words = []

            self.word = word
            self.j_word = just_word(word)

            self.get_linked_words()
            self.get_corpus_examples()
            self.get_self_examples()

        # output corpus examples by default
        self.CorpusExamplesRButton.setChecked(True)

        # if there's no examples found, don't open the window
        if not self.examples_exist():
            self.close()
            return

        self.ResultLabel.setStyleSheet(style) if style else ...
        self.ResultLabel.setText(message)
        self.show_examples_by_button()
        self.show()


class MessageWindow(QWidget):
    def __init__(self,
                 *args) -> None:
        """ Окно отображения сообщений, правильности или
            неправильности ответов
        """
        super().__init__()
        uic.loadUi(MESSAGE_WINDOW_PATH, self)

        self.initUI()

    def initUI(self) -> None:
        self.setWindowTitle('Message')
        self.MessageText.setText('')

    def display(self,
                message: str,
                style: str) -> None:
        if not (isinstance(message, str) and message):
            raise Trouble(self.display, message, _p='w_str')

        self.MessageText.setStyleSheet(style) if style else ...
        self.MessageText.setText(message)
        self.show()


class ShowWindow(QWidget):
    def __init__(self,
                 *args) -> None:
        super().__init__()
        uic.loadUi(SHOW_WINDOW_PATH, self)
        self.marker = lambda x: f"<b><i>{x.capitalize()}</i></b>"

    def display(self,
                items: List,
                window_title: str = 'Show') -> None:
        trbl = Trouble(self.display)
        if not (isinstance(items, list) and items):
            raise trbl(items, _p='w_list')
        if not isinstance(window_title, str):
            raise trbl(window_title, _p='w_str')

        self.setWindowTitle(window_title)
        ex = [
            f"{self.marker(i.word)} – {i.get_native(def_only=True)}<br>"
            for i in sorted(items)
        ]
        self.LearnedWordsBrowser.setText(''.join(ex))
        self.show()