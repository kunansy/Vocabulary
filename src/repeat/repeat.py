__all__ = ['RepeatWords']

import sys
import random as rand

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QWidget, QMainWindow
)

from src.main.constants import *
from src.main.common_funcs import *
from src.trouble.trouble import Trouble
from src.examples.examples import (
    ParallelCorpusExamples, SelfExamples
)


class RepeatWords(QMainWindow):
    def __init__(self, words, mode=1,
                 window_title='Repeat'):
        from src.main.main import Word
        _trbl = Trouble(self.__init__)
        assert file_exist(MAIN_WINDOW_PATH), _trbl(MAIN_WINDOW_PATH, _p='w_file')
        assert file_exist(EXAMPLES_WINDOW_PATH), _trbl(EXAMPLES_WINDOW_PATH, _p='w_file')
        assert file_exist(MESSAGE_WINDOW_PATH), _trbl(MESSAGE_WINDOW_PATH, _p='w_file')
        assert file_exist(SHOW_WINDOW_PATH), _trbl(SHOW_WINDOW_PATH, _p='w_file')

        # assert isinstance(words, list) and words and all(isinstance(i, Word) for i in words), \
        #     f"Wrong words: '{words}', func – RepeatWords.__init__"
        assert isinstance(mode, (str, int)) and \
               (mode in range(1, len(ENG_REPEAT_MODS) + 1) or
                mode in RepeatWords), \
            _trbl(f"wrong mode: '{mode}'", "int or str")
        assert isinstance(window_title, str), \
            _trbl(f"Wrong window title: '{window_title}'", str)

        super().__init__()
        uic.loadUi(MAIN_WINDOW_PATH, self)
        self.initUI(window_title)

        self.word = Word('')
        # self.repeating_word_index = None
        # self.repeated_words_indexes = []
        rand.shuffle(words)
        self.words = words[:]
        self.wrong_translations = list(reversed(words[:]))

        self.mode = None
        self.are_you_right = None
        self.init_button = None
        self.main_item = None

        if isinstance(mode, int):
            self.mode = mode
        elif isinstance(mode, str):
            self.mode = ENG_REPEAT_MODS[mode]

        self.init_fit_mode()

        if not file_exist(REPEAT_LOG_PATH):
            with open(REPEAT_LOG_PATH, 'w', encoding='utf-8'): pass

    def initUI(self, window_title):
        self.ExamplesWindow = ExamplesWindow(self, [])
        self.MessageWindow = MessageWindow(self, [])
        self.ShowWindow = ShowWindow(self, [])
        self.setWindowTitle(window_title)

        # кнопки выбора вариантов
        self.choice_buttons = [
            self.ChoiceButton1,
            self.ChoiceButton2,
            self.ChoiceButton3,
            self.ChoiceButton4,
            self.ChoiceButton5,
            self.ChoiceButton6
        ]
        [self.choice_buttons[i].clicked.connect(self.are_you_right)
         for i in range(len(self.choice_buttons))]

        self.ExitButton.clicked.connect(self.close)
        self.ExitButton.setText('Exit')

        self.HintButton.clicked.connect(self.hint)
        self.HintButton.setText('Hint')

        self.ShowButton.clicked.connect(self.show_words)
        self.ShowButton.setText('Show')

    def init_fit_mode(self):
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

    def test(self):
        # чтобы не остаться с пустым списком ошибочных переводов под конец
        if self.word and self.word not in self.wrong_translations:
            self.wrong_translations.append(self.word)

        if len(self.words) == 1:
            self.WordsRemainLabel.setText("The last one")
        else:
            self.WordsRemainLabel.setText(f"Remain {len(self.words)} words")

        self.word = rand.choice(self.words)
        # self.repeating_word_index = CHOICE(range(len(self.words)))
        # self.repeating_word = CHOICE([iter(i) for i in self.words])
        self.words.remove(self.word)
        self.wrong_translations.remove(self.word)

        self.WordToReapeatBrowser.setText(self.main_item())

        self.set_buttons()

    def set_buttons(self):
        [self.choice_buttons[i].setText('')
         for i in range(len(self.choice_buttons))]

        # ставится ли верное определение
        is_right_def = True

        wrong_translations = rand.sample(self.wrong_translations, len(self.choice_buttons))

        for i in rand.sample(range(len(self.choice_buttons)),
                               len(self.choice_buttons)):
            w_item = rand.choice(wrong_translations)
            wrong_translations.remove(w_item)

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

    def show_result(self, result, style):
        self.MessageWindow.display(
            message=result, style=style)

    def are_you_right(self):
        if self.are_you_right(self.sender().text()):
            self.show_result(result='<i>Excellent</i>',
                             style="color: 'green';")
            if len(self.words) > 0:
                self.test()
            else:
                self.close()
        else:
            self.log(w_choice=self.sender().text(),
                     item=self.word)

            self.show_result(result='<b>Wrong</b>',
                             style="color: 'red';")

    def hint(self):
        """ Показать подсказку: связные слова и примеры """
        if self.mode != 1:
            return

        self.ExamplesWindow.display(word=self.word.word,
                                    message=f"{self.HintButton.text()}",
                                    style="color: blue")

    def show_words(self):
        self.ShowWindow.display(items=self.words,
                                window_title=self.windowTitle())

    def show(self):
        super().show()
        self.show_words()

    def close(self):
        """ По нажатии на кнопку 'Exit' закрыть все окна """
        self.ExamplesWindow.close()
        self.MessageWindow.close()
        self.ShowWindow.close()
        super().close()

    def log(self, item, w_choice):
        """ Логгирование ошибочных вариантов в json:
            {ID_слова: {ID ошибочного варианта: количество ошибок}}
        """
        from src.main.main import search_by_attribute
        _trbl = Trouble(self.log)
        assert file_exist(REPEAT_LOG_PATH), \
            _trbl(REPEAT_LOG_PATH, _p='w_file')
        # assert isinstance(item, str) or isinstance(item, Word), \
        #     f"Wrong word: '{item}', func – RepeatWords.log"
        assert isinstance(w_choice, str) and w_choice, \
            _trbl(w_choice, _p='w_str')

        repeating_word_id = word_id(item.word)

        # Найти ID слова по выбранному варианту:
        wrong_choice_id = word_id(search_by_attribute(self.wrong_translations, w_choice))

        data = load_json(REPEAT_LOG_PATH)

        if repeating_word_id in data:
            if wrong_choice_id in data[repeating_word_id]:
                data[repeating_word_id][wrong_choice_id] += 1
            else:
                data[repeating_word_id][wrong_choice_id] = 1
        else:
            data[repeating_word_id] = {wrong_choice_id: 1}

        dump_json(data=data, f_name=REPEAT_LOG_PATH)


class ExamplesWindow(QWidget):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi(EXAMPLES_WINDOW_PATH, self)

        self.s_examples_base = SelfExamples()
        self.c_examples_base = ParallelCorpusExamples()

        self.word = ''
        self.j_word = ''

        self.c_examples = []
        self.s_examples = []
        self.linked_words = []

        # жирный курсив
        self.bi = lambda x: f"<b><i>{x}</i></b>".upper()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Examples')

        self.ResultLabel.setText('')
        self.ExamplesBrowser.setText('')

        self.CorpusExamplesRButton.setChecked(True)

        self.CorpusExamplesRButton.clicked.connect(self.set_corpus_examples)
        self.SelfExamplesRButton.clicked.connect(self.set_self_examples)
        self.LinkedWordsRButton.clicked.connect(self.set_linked_words)

    def get_linked_words(self):
        """ Инициализировать linked_words,
            получив связные слова
        """
        try:
            # для запроса нужно само слово
            # без предлогов и прочего
            content = get_synonyms(self.j_word)
        except:
            content = []
        self.linked_words = list(map(str.capitalize, content))

    def get_corpus_examples(self):
        """ Инициализировать self.c_examples примерами к
            слову из глобальной корпусной базы
        """
        # если примеров мало – запросить ещё
        if self.c_examples_base.count(self.j_word) < 6:
            self.c_examples_base.new_examples(self.j_word)

        if self.c_examples_base.count(self.j_word) > 0:
            # показать только оригиналы,
            # отсортированные по длине
            self.c_examples = list(map(lambda x: x[0], self.c_examples_base(self.j_word)))
            self.c_examples.sort(key=len)

    def get_self_examples(self):
        """ Инициализировать self.s_examples
            примерами к слову
        """
        self.s_examples = self.s_examples_base.find(self.j_word)

    def examples_exist(self):
        """ Существуют ли хоть какие-то примеры """
        return self.c_examples or \
               self.s_examples or \
               self.linked_words

    def set_corpus_examples(self):
        """ Установить в поле 'примеры' корпусные примеры,
            либо 'Corpus examples not found'
        """
        if self.c_examples:
            self.show_examples(self.c_examples)
        else:
            self.show_examples([f"Corpus examples not '{self.word}' found"])

    def set_self_examples(self):
        """ Установить в поле 'примеры' свои примеры,
            либо 'Self examples not found'
        """
        if self.s_examples:
            self.show_examples(self.s_examples)
        else:
            self.show_examples([f"Self examples to '{self.word}' not found"])

    def set_linked_words(self):
        """ Установить в поле 'примеры' связные слова """
        if self.linked_words:
            self.show_examples(self.linked_words)
        self.show_examples([f"Linked words to '{self.word}' not found"])

    def show_examples(self, examples):
        examples = map(lambda x: f"{self.bi(x[0])}. {change_words(x[1], self.j_word, self.bi)}<br>",
                       enumerate(examples, 1))

        self.ExamplesBrowser.setText('\n'.join(examples))

    def set_examples(self):
        if self.CorpusExamplesRButton.isChecked():
            self.set_corpus_examples()
        elif self.SelfExamplesRButton.isChecked():
            self.set_self_examples()
        elif self.LinkedWordsRButton.isChecked():
            self.set_linked_words()

    def display(self, word, message, style=''):
        assert isinstance(word, str) and word, \
            f"Wrong word: '{word}', str expected, func – Examples.display"
        assert isinstance(message, str) and message, \
            f"Wrong result: '{message}', func – Examples.display"

        if word != self.word:
            self.c_examples = []
            self.s_examples = []
            self.linked_words = []

            self.word = word
            self.j_word = just_word(word)

            self.get_linked_words()
            self.get_corpus_examples()
            self.get_self_examples()

        # вывод корпусных примеров по умолчанию
        self.CorpusExamplesRButton.setChecked(True)

        if not self.examples_exist():
            # если примероы нет – не открывать окно
            self.close()
            return

        if style:
            self.ResultLabel.setStyleSheet(style)
        self.ResultLabel.setText(message)
        self.set_examples()
        self.show()


class MessageWindow(QWidget):
    def __init__(self, *args):
        """ Окно отображения сообщений, правильности или
            неправильности ответов
        """
        super().__init__()
        uic.loadUi(MESSAGE_WINDOW_PATH, self)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Message')
        self.MessageText.setText('')

    def display(self, message, style=''):
        assert isinstance(message, str) and message, \
            f"Wrong message: '{message}', str expected, func – Message.display"

        if style:
            self.MessageText.setStyleSheet(style)

        self.MessageText.setText(message)
        self.show()


class ShowWindow(QWidget):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi(SHOW_WINDOW_PATH, self)

    def display(self, items, window_title='Show'):
        assert isinstance(items, list) and items, \
            f"Wrong items: '{items}', func – Show.display"
        assert isinstance(window_title, str) and window_title, \
            f"Wrong window_title: '{window_title}', func – Show.display"

        self.setWindowTitle(window_title)

        self.LearnedWordsBrowser.setText('\n'.join(map(
            lambda x: f"<i><b>{x.word.capitalize()}</b></i> – {x.get_native(def_only=True)}<br>",
            sorted(items))))
        self.show()