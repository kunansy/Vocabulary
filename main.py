import comtypes.client
from constants import *


from sys import argv
from PyQt5 import uic
from hashlib import sha3_512
from docx import Document
from docx.shared import Pt
from functools import reduce
from itertools import groupby
from datetime import datetime
from datetime import date as dt
from xlrd import open_workbook
from xlsxwriter import Workbook
from random import shuffle, sample, choice
from os import system, getcwd, access, F_OK
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow


def str_to_date(
        string,
        swap=False
):
    """
    :param string: строку формата dd.mm.yy
    :param swap: менять ли местами день и месяц
    :return: date-объект
    """
    if isinstance(string, dt):
        return string

    assert isinstance(string, str), f"Wrong date: '{string}', func – str_to_date"

    split_symbol = '.' if string.count('.') == 2 else '_'

    if isinstance(string, str):
        string = ''.join(filter(lambda x: x.isdigit() or x in split_symbol, string))

        if swap:
            month, day, year = map(int, string.split(split_symbol))
        else:
            day, month, year = map(int, string.split(split_symbol))

        return dt(year, month, day)
    

def file_exist(filename):
    """
    :param filename: имя файла
    :return: существует ли такой файл
    """
    return access(filename, F_OK)


def init_vocabulary_from_file(filename=DATA):
    """
    :param filename: имя файла, где хранятся данные
    :return: список WordsPerDay
    """
    assert file_exist(filename), f"Wrong file: '{filename}', func – init_vocabulary_from_file"

    with open(filename, 'r', encoding='utf-8') as file:
        content = file.readlines()
        dates = list(map(clean_date, filter(lambda x: x.startswith('[') and '/' not in x, content)))

        begin = lambda elem: content.index(f"[{elem}]\n")
        end = lambda elem: content.index(f"[/{elem}]\n")

        words_per_day = [WordsPerDay(list(map(Word, content[begin(i) + 1: end(i)])), i) for i in dates]
    file.close()
    return words_per_day


def fix_filename(
        name,
        extension
):
    """
    :param name: имя файла
    :param extension: расширение файла
    :return: имя + расширение
    """
    return name if name.endswith(f".{extension}") else f"{name}.{extension}"


def clean_date(
        date,
        split_symbol='.'
):
    """
    :param date: str, date
    :param split_symbol: date is expected to be splitted by this symbol
    :return: str, looks like '01.01.1970'
    it needs date format: dd.mm.yy
    """
    res = ''.join(filter(lambda x: x.isdigit() or x in split_symbol, date)).split(split_symbol)
    return '.'.join(map(lambda x: f"0{x}" if len(x) == 1 else x, res))


def language(item: str):
    # TODO: speed up: C++ or NumPy, CPython etc
    assert isinstance(item, str), f"Wrong item: '{item}', func – language"

    if any(i in RUS_ALPHABET for i in item):
        return 'rus'
    return 'eng'


def is_russian(item: str):
    return language(item) == 'rus'


def is_english(item: str):
    return language(item) == 'eng'


def first_rus_index(item: str):
    # TODO: speed up
    return list(map(lambda x: x in RUS_ALPHABET, item)).index(True)


def does_word_fit_with_american_spelling(
        word: str,
        by_str=True
):
    assert isinstance(word, str), f"Wrong word: '{word}', func – does_word_fit_with_american_spelling"

    # TODO: to correct style
    if word.endswith('e') or \
            (word.endswith('re') and not word.endswith('ogre')) or \
            any(i in word for i in UNUSUAL_COMBINATIONS) or \
            any(word[i] == 'l' and word[i + 1] != 'l' for i in range(len(word) - 1)):
        return f"Probably, there are wring combinations is the word '{word}'" if by_str else False
    return "OK" if by_str else True


def parse_str(string):
    """
    Разбирает строку на: термин, свойства, английское определение, русское, пример употребления
    :param string: строка на разбор
    :return: word, properties, English definition, Russian definition
    """
    word_properties, other = string.split(' – ')

    if '[' in word_properties:
        prop_begin = word_properties.index('[')
        word, properties = word_properties[:prop_begin], Properties(word_properties[prop_begin:])
    else:
        word = word_properties
        properties = Properties('')

    if word.count("'") == 2:
        trans_begin = word.index("'")
        word, transcription = word[:trans_begin], word[trans_begin:]

    else:
        transcription = ''

    example = []
    if 'Example: ' in other:
        ex_index = other.index('Example: ')
        example = list(filter(len, map(str.strip, other[ex_index + 8:].split(';'))))
        other = other[:ex_index]

    if other:
        if is_russian(other):
            fri = first_rus_index(other)
            english = other[:fri].split(';')
            russian = other[fri:].split(';')
        else:
            english = other.split(';')
            russian = []
    else:
        english = []
        russian = []

    # TODO: work with expressions
    if any(word.lower() in i.split() for i in english):
        print(f"'{word.capitalize()}' is situated in the definition too. It is recommended to replace it on ***")

    if any('.' in i for i in english):
        print(f"There is wrong symbol in the definition of the word '{word}'")

    return word, transcription, properties, english, russian, example


def init_from_xlsx(
        filename,
        out='tmp'
):
    """
    Функция преобразует xlsx файл в список объектов класса Word,
    выводит их в файл, вывод осуществляется с дополнением старого содержимого:
    [date]
    ...words...
    [/date]
    :param filename: имя xlsx файла
    :param out: имя файла, в который будет выведен список слов формата Word, по умолчанию – tmp
    """
    assert file_exist(filename), f"Wrong file: '{filename}', func – init_from_xlsx"

    # файл, скачанный из Cambridge Dictionary, содержит дату в английском формате
    date = str_to_date(filename.replace(f".{TABLE_EXT}", ''), swap=True).strftime(DATEFORMAT)

    content = open(out, 'r', encoding='utf-8').readlines()

    assert f"[{date}]\n" not in content, f"Date '{date}' is currently exist in the '{out}' file, func – init_from_xlsx"

    rb = open_workbook(filename)
    sheet = rb.sheet_by_index(0)

    # удаляется заглавие, введение и прочие некорректные данные
    value = list(filter(lambda x: len(x[0]) and (len(x[2]) or len(x[3])),
                        [sheet.row_values(i) for i in range(sheet.nrows)]))
    value.sort(key=lambda x: x[0])

    value = list(map(lambda x: Word(x[0], '', x[2], x[3]), value))

    # группировка одинаковых слов вместе
    value = groupby(value, key=lambda x: x.word)

    file_out = open(out, 'a', encoding='utf-8')

    # суммирование одинаковых слов в один объект класса Word
    result = [reduce(lambda res, elem: res + elem, list(group[1]), Word('')) for group in value]

    print(f"\n\n[{date}]", file=file_out)
    print(*result, sep='\n', file=file_out)
    print(f"[/{date}]", file=file_out)

    file_out.close()


def create_docx(
        content,
        out_file=None,
        header='General',
        russian_only=False
):
    """
    :param content: список объектов класса Word, которые будут выведены в файл
    :param out_file: имя файла, если не передано – именем файла будет header
    :param header: заголовок документа
    :param russian_only: True: слово – русские опредления; False: слово – английское определение; русское
    если файл с таким именем уже существует – не создаёт новый
    """
    assert isinstance(content, list) and len(content), f"Wrong content '{content}', func – create_docx"
    assert isinstance(header, str), f"Wrong header '{header}', func – create_docx"
    assert isinstance(russian_only, bool), f"Wrong russian_only '{russian_only}', func – create_docx"

    if out_file is None:
        out_file = f"{header}.{DOC_EXT}"

    out_file = fix_filename(out_file, DOC_EXT)
    if file_exist(f"{DOC_FOLDER}\\{out_file}"):
        print(f"docx file with the name '{out_file}' still exist")
        return

    words = Document()

    style = words.styles['Normal']
    font = style.font
    font.name = 'Avenir Next Cyr'
    font.size = Pt(16)

    words.add_heading(f"{header}", 0)

    for num, word in enumerate(content, 1):
        item = words.add_paragraph()
        item.style = style

        item.add_run(f"{num}. ")

        if isinstance(word, str):
            item.add_run(f"{word[0].upper()}{word[1:]}")

        elif isinstance(word, Word):
            item.add_run(f"{word.word}".capitalize()).bold = True

            if russian_only:
                item.add_run(f" – {word.get_russian(def_only=True)}")
            else:
                item.add_run(f" – {word.get_english(def_only=True)} {word.get_russian(def_only=True)}")

    words.save(f"{getcwd()}\\{DOC_FOLDER}\\{out_file}")


def create_pdf(
        content,
        in_file=None,
        out_file=None,
        russian_only=False
):
    """
    :param content: список объектов класса Word, которые будут выведены в файл
    :param in_file: имя входного файла docx, который будет преобразован в pdf
        если его нет – создаётся временный docx файл, по завершение выполнения функции удаляется
    :param out_file: имя файла, если не передано – именем файла будет header
    :param russian_only: True: слово – русские опредления; False: слово – английское определение; русское
    если файл с таким именем уже существует – не создаёт новый
    """
    assert isinstance(content, list) and len(content), f"Wrong content: '{content}', func – create_pdf"
    assert isinstance(out_file, str), f"Wrong out_file: '{out_file}', func – create_pdf"
    assert isinstance(russian_only, bool), f"Wrong russian_only: '{russian_only}', func – create_pdf"

    if file_exist(f"{PDF_FOLDER}\\{fix_filename(out_file, PDF_EXT)}"):
        print(f"PDF-file with name '{out_file}' still exist")
        return

    # нужно ли удалять файл потом
    flag = False

    if in_file is None or not \
            (file_exist(fix_filename(in_file, DOC_EXT)) or
             file_exist(f"{DOC_FOLDER}\\{fix_filename(in_file, DOC_EXT)}")):
        flag = True
        in_file = f"temp.{DOC_EXT}"

        create_docx(
            content,
            out_file=in_file,
            russian_only=russian_only
        )

    in_file = fix_filename(in_file, DOC_EXT)
    out_file = fix_filename(out_file, PDF_EXT)

    word = comtypes.client.CreateObject('Word.Application')
    doc = word.Documents.Open(f"{getcwd()}\\{DOC_FOLDER}\\{in_file}")
    doc.SaveAs(f"{getcwd()}\\{PDF_FOLDER}\\{out_file}", FileFormat=17)

    doc.Close()
    word.Quit()

    if flag:
        system(f'del "{getcwd()}\\{DOC_FOLDER}\\{in_file}"')


def word_id(item):
    """
    :param item: слово: слока или объект класса Word
    :return: первые и последние четыре символа sha3_512 хеша этого слова
    """
    assert isinstance(item, str) or isinstance(item, Word), f"Wrong word: '{item}', func – word_id"

    word = item if isinstance(item, str) else item.word

    _id = sha3_512(bytes(word, encoding='utf-8')).hexdigest()
    return _id[:4] + _id[-4:]


class RepeatWords(QMainWindow):
    def __init__(
            self,
            words,
            mode=1,
            log_filename=REPEAT_LOG_FILENAME,
            window_title='Repeat'
    ):
        assert file_exist(MAIN_WINDOW_PATH), "Main window does not exist, func – RepeatWords.__init__"
        assert file_exist(ALERT_WINDOW_PATH), "Alert window does not exist, func – RepeatWords.__init__"
        assert file_exist(MESSAGE_WINDOW_PATH), "Message window does not exist, func – RepeatWords.__init__"
        assert file_exist(SHOW_WINDOW_PATH), "Show window does not exist, func – RepeatWords.__init__"

        assert isinstance(words, list) and len(words) and isinstance(words[0], Word), \
            f"Wrong words: '{words}', func – RepeatWords.__init__"
        assert (isinstance(mode, int) and mode in range(1, 5)) or (isinstance(mode, str) and mode in MODS), \
            f"Wrong mode: '{mode}', func – RepeatWords.__init__"
        assert isinstance(log_filename, str), \
            f"Wrong log_filename: '{log_filename}', func – RepeatWords.__init__"
        assert isinstance(window_title, str), \
            f"Wrong window title: '{window_title}', func – RepeatWords.__init__"

        super().__init__()
        uic.loadUi(MAIN_WINDOW_PATH, self)
        self.initUI(window_title)

        self.word = Word('')
        shuffle(words)
        self.words = words[:]
        self.wrong_translations = list(reversed(words[:]))
        
        self.mode = None
        self.are_you_right = None
        self.init_button = None
        self.set_main_word = None

        if isinstance(mode, int):
            self.mode = mode
        elif isinstance(mode, str):
            self.mode = MODS[mode]

        self.init_fit_mode()

        self.log_filename = log_filename
        if not file_exist(self.log_filename):
            temp = open(self.log_filename, 'w', encoding='utf-8')
            temp.close()

    def initUI(
            self,
            window_title
    ):
        self.AlertWindow = Alert(self, [])
        self.MessageWindow = Message(self, [])
        self.ShowWindow = Show(self, [])
        self.setWindowTitle(window_title)

        self.choice_buttons = [
            self.ChoiceButton1,
            self.ChoiceButton2,
            self.ChoiceButton3,
            self.ChoiceButton4,
            self.ChoiceButton5,
            self.ChoiceButton6
        ]
        [self.choice_buttons[i].clicked.connect(self.are_you_right) for i in range(len(self.choice_buttons))]

        self.ExitButton.clicked.connect(self.close)
        self.ExitButton.setText('Exit')

        self.HintButton.clicked.connect(self.hint)
        self.HintButton.setText('Hint')

        self.ShowButton.clicked.connect(self.show_words)
        self.ShowButton.setText('Show')

    def init_fit_mode(self):
        if self.mode == 1:
            self.are_you_right = lambda x: x.lower() == self.word.get_russian(def_only=True)
            self.init_button = lambda x: x.get_russian(def_only=True).capitalize()
            self.set_main_word = lambda x: x.word.capitalize()
        elif self.mode == 2:
            self.are_you_right = lambda x: x.lower() == self.word.word
            self.init_button = lambda x: x.word.capitalize()
            self.set_main_word = lambda x: x.get_russian(def_only=True).capitalize()
        elif self.mode == 3:
            self.are_you_right = lambda x: x.lower() == self.word.get_russian(def_only=True)
            self.init_button = lambda x: x.get_russian(def_only=True).capitalize()
            self.set_main_word = lambda x: x.get_english(def_only=True).capitalize()
        elif self.mode == 4:
            self.are_you_right = lambda x: x.lower() == self.word.get_english(def_only=True)
            self.init_button = lambda x: x.get_english(def_only=True).capitalize()
            self.set_main_word = lambda x: x.get_russian(def_only=True).capitalize()

    def test(self):
        if self.word:
            self.wrong_translations.append(self.word)

        if len(self.words) == 1:
            self.WordsRemainLabel.setText("The last one")
        else:
            self.WordsRemainLabel.setText(f"Remain: {len(self.words)} words")

        self.word = choice(self.words)
        self.words.remove(self.word)
        self.wrong_translations.remove(self.word)

        self.WordToReapeatBrowser.setText(self.set_main_word(self.word))

        self.set_buttons()

    def set_buttons(self):
        [self.choice_buttons[i].setText('') for i in range(len(self.choice_buttons))]

        # ставится ли верное определение
        is_right_def = True

        wrong_translations = sample(self.wrong_translations, len(self.choice_buttons))

        for i in sample(range(len(self.choice_buttons)), len(self.choice_buttons)):
            w_item = choice(wrong_translations)
            wrong_translations.remove(w_item)

            if is_right_def:
                self.choice_buttons[i].setText(self.init_button(self.word))
                is_right_def = False
            else:
                self.choice_buttons[i].setText(self.init_button(w_item))

    def show_result(
            self,
            result,
            style
    ):
        if self.word.get_examples(examples_only=True):
            self.AlertWindow.display(
                word=self.word,
                result=result,
                example=self.word.get_examples(examples_only=True, by_list=True),
                style=style
            )
        else:
            self.MessageWindow.display(
                message=result,
                style=style
            )

    def are_you_right(self):
        if self.are_you_right(self.sender().text()):
            self.log(
                self.word,
                "Excellent"
            )
            self.show_result(
                result='<i>Excellent</i>',
                style="color: 'green';"
            )

            if len(self.words) > 0:
                self.test()
            else:
                self.close()
        else:
            self.log(
                self.word,
                'wrong',
                w_choice=self.sender().text()
            )

            self.show_result(
                result='<b>Wrong</b>',
                style="color: 'red';"
            )

    def hint(self):
        if self.word.get_examples(examples_only=True):
            self.AlertWindow.display(
                word=self.word,
                result=f"{self.HintButton.text()}",
                example=self.word.get_examples(examples_only=True, by_list=True),
                style="color: blue"
            )

    def show_words(self):
        self.ShowWindow.display(
            items=self.words,
            window_title=self.windowTitle()
        )

    def show(self):
        super().show()
        self.show_words()

    def close(self):
        self.AlertWindow.close()
        self.MessageWindow.close()
        self.ShowWindow.close()
        super().close()

    def log(
            self,
            word,
            result,
            w_choice=''
    ):
        """
        :param word: слово
        :param result: кезультат
        :param w_choice: ощибочный вариант
        :return: логгирование в файл
        """
        assert file_exist(self.log_filename), "Wrong log file, func – RepeatWords.log"

        if len(w_choice) > 0:
            w_choice = f", chosen variant: '{w_choice}'"

        content = open(self.log_filename, 'r').readlines()

        with open(self.log_filename, 'a', encoding='utf-8') as log_file:
            current_date = datetime.now().strftime(DATEFORMAT)

            if f"[{current_date}]\n" in content:
                log_file.write(f"\t{word.word.capitalize()} – {result}{w_choice}\n")
            else:
                log_file.write(f"\n[{current_date}]\n")
                log_file.write(f"\t{word.word.capitalize()} – {result}{w_choice}\n")

        log_file.close()


class Alert(QWidget):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi(ALERT_WINDOW_PATH, self)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Alert')

        self.ResultLabel.setText('')
        self.ExamplesBrowser.setText('')

    def display(
            self,
            word,
            result,
            example,
            style=''
    ):
        assert isinstance(word, Word), f"Wrong word: '{word}', func – Alert.display"
        assert isinstance(result, str), f"Wrong result: '{result}', func – Alert.display"
        assert len(example) > 0, "Empty example, choose the Message window instead, func – Alert.display"

        self.ResultLabel.setText(result)

        if style:
            self.ResultLabel.setStyleSheet(style)

        bold_word = lambda string, x: ' '.join(f"<b>{i}</b>" if x.lower() in i.lower() else i for i in string.split())

        self.ExamplesBrowser.setText('\n'.join(map(lambda x: f"{x[0]}. {bold_word(x[1], word.word)}<br>",
                                                   enumerate(example, 1))))

        self.show()


class Message(QWidget):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi(MESSAGE_WINDOW_PATH, self)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Alert')
        self.MessageText.setText('')

    def display(
            self,
            message,
            style=''
    ):
        assert isinstance(message, str), f"Wrong message: '{message}', func – Message.display"

        if style:
            self.MessageText.setStyleSheet(style)

        self.MessageText.setText(message)

        self.show()


class Show(QWidget):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi(SHOW_WINDOW_PATH, self)

    def display(
            self,
            items,
            window_title='Show'
    ):
        assert isinstance(items, list) and len(items), f"Wrong items: '{items}', func – Show.display"
        assert isinstance(window_title, str), f"Wrong window_title: '{window_title}', func – Show.display"

        self.setWindowTitle(window_title)

        self.EnglishWordsBrowser.setText(
            '\n'.join(map(
                    lambda x: f"<i><b>{x.word.capitalize()}</b></i> – {x.get_russian(def_only=True)}<br>",
                    sorted(items)
                )
            )
        )
        self.show()


class Properties:
    def __init__(
            self,
            properties
    ):
        assert isinstance(properties, str) or isinstance(properties, list), \
            f"Wrong properties: '{properties}', func – Properties.__init__"

        properties = properties.replace('[', '').replace(']', '').split(',') if isinstance(properties, str) else properties
        properties = list(filter(len, map(lambda x: x.strip().lower(), properties)))

        self.properties = properties[:]

    def __eq__(self, other):
        if isinstance(other, Properties):
            return sorted(self.properties) == sorted(other.properties)
        return other.lower() in self.properties

    def __ne__(self, other):
        return not (self == other)

    def __getitem__(self, item):
        return self == item

    def __getattr__(self, item):
        return self == item

    def __len__(self):
        return len(self.properties)

    def __add__(self, other):
        if isinstance(other, Properties):
            return Properties(self.properties + other.properties)

    def __hash__(self):
        return hash(self.properties)

    def __str__(self):
        return f"[{', '.join(map(str.capitalize, self.properties))}]"


class Word:
    def __init__(
            self,
            word='',
            transcription='',
            properties='',
            english_def=[],
            russian_def=[],
            example=[]
    ):
        """
        :param word: english word to learn
        :param properties: POS, language level, formal, ancient,
        if verb (transitivity, ) if noun (countable, )
        :param english_def: english definitions of the word: list
        :param russian_def: russian definitions of the word (maybe don't exist): list
        :param example: examples of the word using
        """
        assert isinstance(word, str), f"Wrong word: '{type(word)}', '{word}', func – Word.__init__"
        assert isinstance(transcription, str), f"Wrong transcription: '{transcription}', func – Word.__init__"
        assert isinstance(properties, str) or isinstance(properties, Properties) or isinstance(properties, dict), \
            f"Wrong properties: '{type(properties)}', '{properties}', func – Word.__init__"
        assert isinstance(english_def, list) or isinstance(english_def, str), \
            f"Wrong english_def: '{type(english_def)}', '{english_def}', func – Word.__init__"
        assert isinstance(russian_def, list) or isinstance(russian_def, str), \
            f"Wrong russian_def: '{type(russian_def)}', '{russian_def}', func – Word.__init__"
        assert isinstance(example, list) or isinstance(example, str), \
            f"Wrong example: {type(example)}, '{example}', func – Word.__init__"

        if ' – ' in word:
            self.__init__(*parse_str(word))
        else:
            self.word = word.lower().strip()
            self.transcription = transcription.replace("'", '').strip()

            if isinstance(russian_def, str) and isinstance(english_def, str):
                english_def = english_def.split(';')
                russian_def = russian_def.split(';')

            self.english = list(filter(len, map(str.strip, english_def)))
            self.russian = list(filter(len, map(str.strip, russian_def)))

            self.properties = ''

            if isinstance(properties, Properties):
                self.properties = properties
            elif isinstance(properties, str):
                self.properties = Properties(properties)

            if isinstance(example, str):
                self.examples = list(filter(len, map(str.strip, example.split(';'))))
            elif isinstance(example, list):
                self.examples = list(filter(len, map(str.strip, example)))

            # self.id = word_id(self.word)

    def get_russian(
            self,
            def_only=False,
            by_list=False
    ):
        """
        Вовзращает русские определения
        :param def_only: True – только определения, False – термин и определения
        :param by_list: списком или строкой; если True – значение параметра def_only игнорируется
        """
        if by_list:
            return self.russian
        if def_only:
            return '; '.join(self.russian)
        return f"{self.word} – {'; '.join(self.russian)}".capitalize()

    def get_english(
            self,
            def_only=False,
            by_list=False
    ):
        """
        Возвращает английские определения
        :param def_only: True – только определения, False – термин и определения
        :param by_list: списком или строкой; если True – значение параметра def_only игнорируется
        """
        if by_list:
            return self.english
        if def_only:
            return '; '.join(self.english)
        return f"{self.word} – {'; '.join(self.english)}".capitalize()

    def get_examples(
            self,
            examples_only=False,
            by_list=False
    ):
        """
        Возвращает примеры
        :param def_only: True – только примеры, False – термин и примеры
        :param by_list: списком или строкой; если True – значение параметра def_only игнорируется
        """
        if by_list:
            return self.examples
        if examples_only:
            return '; '.join(self.examples)
        return f"{self.word.capitalize()} – {'; '.join(self.examples)}"

    def get_properties(self):
        return self.properties

    def get_transcription(self):
        return self.transcription

    # def word_id(self):
    #     return self.id if self.id else word_id(self.word)

    def is_fit(
            self,
            *properties
    ):
        return all(self.properties[i] for i in properties)

    def __getitem__(
            self,
            index: int
    ):
        """
        :param index: int value
        :return: the letter under the index
        """
        assert isinstance(index, int) and len(self.word) >= abs(index), \
            f"Wrong index: '{index}', func – Word.__getitem__"

        return self.word[index]

    def __iter__(self):
        return iter(self.word)

    def __add__(self, other):
        """
        :param other: строку с ' – ' для преобразования к Word или сам объект класса Word
        :return: если термины одни и те же – просуммирует списки определений и свойств
        """
        if isinstance(other, str) and ' – ' not in other or not isinstance(other, Word):
            raise ValueError(f"'Operation +' between 'class Word' and '{type(other)}' does not support")

        if isinstance(other, str):
            other = Word(other)

        if self != other and len(self) != 0 and len(other) != 0:
            raise ValueError(f"'Operator +' demands for the equality words")

        return Word(
            max(self.word, other.word),
            self.transcription,
            other.properties + self.properties,
            other.english[:] + self.english[:],
            other.russian[:] + self.russian[:],
            other.examples[:] + self.examples[:]
        )

    def __eq__(self, other):
        """
        :param other: str, Word or int value
        :return: are words equal
        """
        if isinstance(other, str):
            return self.word == other.lower().strip()
        if isinstance(other, Word):
            # TODO: свойства могут быть и пустыми
            return self.word == other and \
                   self.properties == other.properties
        if isinstance(other, int):
            return len(self.word) == other

    def __ne__(self, other):
        """
        :param other: str, Word or int
        :return: not equal for them
        """
        return not (self == other)

    def __gt__(self, other):
        """
        :param other: str, Word or int
        :return: self.word > other(.word)
        """
        if isinstance(other, str):
            return self.word > other.lower().strip()
        if isinstance(other, Word):
            return self.word > other.word
        if isinstance(other, int):
            return len(self.word) > other

    def __lt__(self, other):
        """
        :param other: str, Word or int
        :return: self.word < other(.word)
        """
        return self != other and not (self > other)

    def __ge__(self, other):
        """
        :param other: str or Word
        :return: self.word >= other(.word)
        """
        return self > other or self == other

    def __le__(self, other):
        """
        :param other: str or Word
        :return: self.word <= other(.word)
        """
        return self < other or self == other

    def __len__(self):
        """
        :return: len of the self.word
        """
        return len(self.word)

    def __bool__(self):
        """
        :return: does self.word exist
        """
        return bool(len(self))

    def __contains__(self, item):
        """
        :param item: str или Word
        :return: если в item есть '–', или item содержит кириллические символы – ищет по определениям
        """
        if isinstance(item, str):
            item = item.lower().strip()

            # работает по определениям
            if '–' in item or is_russian(item):
                item = item.replace('–', '').strip()

                if is_russian(item):
                    return item in self.get_russian(def_only=True)
                return item in self.get_english(def_only=True)

            # по словам
            return item in self.word or self.word in item

        if isinstance(item, Word):
            return self.word in item.word or item.word in self.word

    def __str__(self):
        transcription = f" /{self.transcription}/" * (len(self.transcription) != 0)
        properties = f" {self.properties}" * (len(self.properties) != 0)
        eng = f"{'; '.join(self.english)}\t" * (len(self.english) != 0)
        rus = f"{'; '.join(self.russian)}" * (len(self.russian) != 0)

        return f"{self.word.capitalize()}{transcription}{properties} – {eng}{rus}"

    def __hash__(self):
        return hash(
            hash(self.word) +
            hash(self.transcription) +
            hash(self.properties) +
            hash(self.russian) +
            hash(self.english) +
            hash(self.examples)
        )


class WordsPerDay:
    def __init__(
            self,
            content: list,
            datation):
        """
        :param content: список объектов класса Word
        :param date: дата изучения
        """
        self.datation = str_to_date(datation)
        self.content = list(sorted(content))

    def russian_only(
            self,
            def_only=False
    ):
        """
        :param def_only: return words with its definitions or not
        :return: the list of the words with its Russian definitions, the day contains
        """
        return reduce(
            lambda res, elem: res + [elem.get_russian(def_only)], 
            self.content, 
            []
        )

    def english_only(
            self,
            def_only=False
    ):
        """
        :param def_only: return words with its definitions or not
        :return: the list of the words with its English definitions, the day contains
        """
        return reduce(
            lambda res, elem: res + [elem.get_english(def_only)], 
            self.content, 
            []
        )

    def examples_only(
            self,
            examples_only=False
    ):
        res = reduce(
            lambda res, elem: res + [elem.get_examples(examples_only)], 
            self.content, 
            []
        )
        
        return list(filter(len, res))

    def get_words_list(
            self,
            with_eng=False,
            with_rus=False
    ):
        """
        :param with_eng: return words with English its definitions or not
        :param with_rus: return words with its Russian definitions or not
        :return: the list of the words, the day contains, with its English/Russian definitions
        """
        rus = lambda x: f"{x.get_russian(def_only=True)}" * int(with_rus)
        eng = lambda x: f"{x.get_english(def_only=True)}" * int(with_eng)

        devis = lambda x: ' – ' * ((len(rus(x)) + len(eng(x))) != 0)

        value = lambda x: f"{x.word}{devis(x)}{eng(x)}{rus(x)}"

        return reduce(
            lambda res, elem: res + [value(elem)], 
            self.content,
            []
        )

    def get_content(self):
        return self.content[:]

    def get_examples(
            self,
            examples_only=False
    ):
        return reduce(
            lambda res, elem: res + [elem.get_examples(examples_only=examples_only)],
            self.content,
            []
        )

    def get_date(
            self,
            dateformat=DATEFORMAT
    ):
        return self.datation.strftime(dateformat)

    def get_information(self):
        return f"{self.get_date()}\n{len(self)}"

    def repeat(
            self,
            **params
    ):
        app = QApplication(argv)

        repeat = RepeatWords(
            words=self.content,
            window_title=self.get_date(),
            **params
        )
        repeat.test()
        repeat.show()

        exit(app.exec_())

    def create_docx(
            self,
            russian_only=False
    ):
        create_docx(
            self.content, 
            header=self.get_date(), 
            russian_only=russian_only
        )

    def create_pdf(
            self,
            russian_only=False
    ):
        create_pdf(
            self.content, 
            out_file=self.get_date(), 
            russian_only=russian_only
        )

    def search_by_properties(self, *properties):
        return list(filter(lambda x: x.is_fit(*properties), self.content))

    def __len__(self):
        """
        :return: количество слов
        """
        return len(self.content)

    def __str__(self):
        date = f"{self.get_date()}\n"
        if len(self.content) == 0:
            return date + 'Empty'
        return date + '\n'.join(map(str, self.content))

    def __contains__(self, item):
        """
        :param item: word or its diff
        :return: does it exist here?
        """
        assert isinstance(item, str) or isinstance(item, Word), \
            f"Wrong item: '{type(item)}', func – WordsPerDay.__contains__"

        return any(item in i for i in self.content)

    def __getitem__(self, item):
        # TODO: slice
        """
        :param item: word or index
        :return: object Word
        """
        if (isinstance(item, str) or isinstance(item, Word)) and item in self:
            return list(filter(lambda x: item in x, self.content))
        if isinstance(item, int) and abs(item) <= len(self.content):
            return self.content[item]

        raise IndexError(f"Wrong index or item {item} does not exist in {self.get_date()}")

    def __iter__(self):
        return iter(self.content)

    def __lt__(self, other):
        if isinstance(other, WordsPerDay):
            return len(self.content) < len(other.content)
        if isinstance(other, int):
            return len(self.content) < other

    def __eq__(self, other):
        if isinstance(other, WordsPerDay):
            return len(self.content) == len(other.content)
        if isinstance(other, int):
            return len(self.content) == other

    def __gt__(self, other):
        return not self < other and not self == other

    def __hash__(self):
        return hash(
            hash(self.content) +
            hash(self.datation)
        )


class Vocabulary:
    def __init__(
            self,
            list_of_days=None
    ):
        if list_of_days is None or len(list_of_days) == 0:
            self.list_of_days = init_vocabulary_from_file(DATA)[:]
        else:
            assert isinstance(list_of_days, list) and len(list_of_days) and isinstance(list_of_days[0], WordsPerDay), \
                f"Wrong list_of_days: '{list_of_days}', func – Vocabulary.__init__"

            self.list_of_days = list_of_days[:]

        self.graphic_name = f"{TABLE_FOLDER}\\Information_{self.get_date_range()}.{TABLE_EXT}"

    def get_pairs_date_count(self):
        """
        :return: dict{str version of the date: length of the item with that date..}
        """
        return {i.get_date(): len(i) for i in self.list_of_days}

    def get_max_day(
            self,
            with_inf=False
    ):
        """
        :param with_inf: True – "date: len", False – class WordsPerDay
        :return: the biggest item by the count of the learned words
        """
        maximum_day = max(self.list_of_days)

        if with_inf:
            return f"Maximum day {maximum_day.get_date()}: {len(maximum_day)}"
        return maximum_day

    def get_min_day(
            self,
            with_inf=False
    ):
        """
        :param with_inf: True – "date: len", False – class WordsPerDay
        :return: the smallest item by the count of the learned words
        """
        minimum_day = min(self.list_of_days)

        if with_inf:
            return f"Minimum day {minimum_day.get_date()}: {len(minimum_day)}"
        return minimum_day

    def get_avg_count_of_words(self):
        """
        :return: среднее количество изученных за день слов
        """
        return sum(len(i) for i in self.list_of_days) // self.duration()

    def get_empty_days_count(self):
        """
        :return: количество пустых дней
        """
        return self.duration() - len(self.list_of_days) + 1

    def get_statistics(self):
        """
        :return: статистику о словаре
        """
        avg_value = self.get_avg_count_of_words()
        empty_count = self.get_empty_days_count()

        avg_inf = f"Average value = {avg_value}"
        duration = f"Duration = {self.duration()}"
        total_amount = f"Total = {len(self)}"
        would_total = f"Would be total = {len(self) + avg_value * empty_count}\n" \
                      f"Lost = {self.get_avg_count_of_words() * empty_count} items per " \
                      f"{empty_count} empty days"
        min_max = f"{self.get_max_day(with_inf=True)}\n{self.get_min_day(with_inf=True)}"

        return f"{duration}\n{avg_inf}\n{total_amount}\n{would_total}\n\n{min_max}"

    def get_date_list(
            self,
            by_str=False
    ):
        """
        :param by_str: True – date with str, False – date by class Date
        :return: the list of the date
        """
        if by_str:
            return list(map(lambda x: x.get_date(), self.list_of_days))
        return list(map(lambda x: x.datation, self.list_of_days))

    def get_date_range(self):
        """
        :return: separated with '–' symbol the date of the first element and the date of the last element
        """
        return f"{self.begin(by_str=True)}–{self.end(by_str=True)}"

    def get_item_before_now(
            self,
            days_count
    ):
        """
        :param days_count: количество дней отступа от текущей даты, int > 0
        :return: непустой айтем, чей индекс = len - days_count
        """
        assert isinstance(days_count, int) and days_count > 0, \
            f"Wrong days_count: '{type(days_count)}', '{days_count}', func – Vocabulary.get_item_before_now"

        index = len(self.list_of_days) - days_count

        assert index >= 0, f"Wrong index: '{index}', func – Vocabulary.get_item_before_now"

        return self.list_of_days[index]

    def get_common_list(self):
        """
        :return: sorted list of the all words
        """
        return list(sorted(reduce(
            lambda result, element: result + element.get_content(),
            self.list_of_days,
            []
        )))

    def get_examples(
            self,
            examples_only=False
    ):
        """
        :return: все существующие примеры из слов(*)
        """
        return reduce(
            lambda result, element: result + element.examples_only(examples_only=examples_only),
            self.list_of_days,
            []
        )

    def duration(self):
        return (self.end() - self.begin()).days

    def create_xlsx(self):
        """
        :return: to create Excel file with statistics and graphic,
         name of file – str version of the date of the first and the last day
        """
        if file_exist(self.graphic_name):
            return

        workbook = Workbook(self.graphic_name)
        workbook.set_properties({
            'title': "Learning English",
            'author': "Kolobov Kirill",
            'company': "SHUE PPSH",
            'comments': "Created with Python and XlsxWriter"
        })

        cell_format = workbook.add_format({
            'size': 16,
            'font': "Avenir Next Cyr",
            'align': "vcenter"
        })

        worksheet = workbook.add_worksheet(SHEET_NAME)

        date_count = self.get_pairs_date_count()

        worksheet.set_column('A:A', 17)

        for row, (date, count) in enumerate([(date, count) for date, count in date_count.items()]):
            worksheet.write(row, 0, date, cell_format)
            worksheet.write(row, 1, count, cell_format)

        row += 1

        worksheet.write(row, 0, "Total:", cell_format)
        worksheet.write(row, 1, f"=SUM(B1:B{row})", cell_format)

        chart = workbook.add_chart({
            'type': "line"
        })
        # line, area, bar, column

        chart.set_title({
            'name': "Amount of the learned words",
            'name_font': {
                'name': "Avenir Next Cyr",
                'color': "black",
                'size': 16
            },
        })

        chart.add_series({
            'values': f"={SHEET_NAME}!B1:B{row}",
            'categories': f"={SHEET_NAME}!A1:A{row}",
            'line': {
                'color': "orange"
            },
        })

        chart.set_legend({
            'none': True
        })

        chart.set_x_axis({
            'name': 'Days',
            'name_font': {
                'name': "Avenir Next Cyr",
                'italic': True,
                'size': 16
            },
            'num_font': {
                    'name': "Avenir Next Cyr",
                    'italic': True,
                    'size': 14
                }
        })

        chart.set_y_axis({
            'name': 'Count',
            'name_font': {
                'name': "Avenir Next Cyr",
                'italic': True,
                'size': 16
            },
            'num_font': {
                'name': "Avenir Next Cyr",
                'italic': True,
                'bold': True,
                'size': 14
            }
        })

        chart.set_size({
            'width': 1280,
            'height': 520
        })

        worksheet.insert_chart('C1', chart)

        workbook.close()

    def create_docx(
            self,
            russian_only=False
    ):
        """
        :param russian_only: True – words with the only Russian definitions,
                            False – words with all definition
        :return: to create docx with:
            all words in the dictionary,
            name = date range of the dictionary
        """
        create_docx(
            content=self.get_common_list(),
            out_file=self.get_date_range(),
            header=self.get_date_range(),
            russian_only=russian_only
        )

    def create_pdf(
            self,
            russian_only=False
    ):
        """
        :param russian_only: True – words with the only Russian definitions,
                            False – words with all definition
        :return: to create pdf with:
            all words in the dictionary,
            name = date range of the dictionary
        """
        create_pdf(
            content=self.get_common_list(),
            in_file=self.get_date_range(),
            out_file=self.get_date_range(),
            russian_only=russian_only
        )

    def search(
            self,
            item
    ):
        """
        :param item: word to search: str or Word
        :return: dict{date: [items with the word]...}
        """
        assert len(item) > 1, f"Wrong item: '{item}', func – Vocabulary.search"
        assert isinstance(item, str) or isinstance(item, Word), f"Wrong item: '{item}', func – Vocabulary.search"
        assert item in self, f"Word is not in the Vocabulary '{item}', func – Vocabulary.search"

        item = item.lower().strip() if isinstance(item, str) else item

        return {i.get_date(): i[item] for i in filter(lambda x: item in x, self.list_of_days)}

    def show_graph(self):
        """
        :return: show graphic
        """
        assert file_exist(self.graphic_name), f"Wrong file: '{self.graphic_name}', func – Vocabulary.show_graph"

        system(self.graphic_name)

    def information(self):
        """
        to create xslx file
        :return: str with information about dictionary and the dictionary
        """
        self.create_xlsx()

        return '\n'.join(map(lambda day_count: f"{day_count[0]}: {day_count[1]}", self.get_pairs_date_count().items())) + \
               f"\n{DIVIDER}\n{self.get_statistics()}"

    def repeat(
            self,
            day_before_now=None,
            date=None,
            **params
    ):
        """
        :param day_before_now:
        :param date: day with the date to repeat
        :param params: additional params to RepeatWord class
        """
        # TODO: повторение изученных 1, 3, 7, 21 день назад слов
        repeating_day = []

        if date is None and day_before_now is not None:
            repeating_day = self.get_item_before_now(day_before_now)

        if day_before_now is None and date is not None:
            repeating_day = self[date]

        assert len(repeating_day) != 0, f"Wrong item to repeat, func – Vocabulary.repeat"

        app = QApplication(argv)

        repeat = RepeatWords(
            words=repeating_day.get_content(),
            window_title=repeating_day.get_date(),
            **params
        )

        repeat.test()
        repeat.show()

        exit(app.exec_())

    def remember_via_example(
            self,
            word
    ):
        """
        :param word: word to remember via examples, str or Word
        :return: examples with this word
        """
        return self(word, by_example=True)

    def begin(
            self,
            by_str=False
    ):
        """
        :param by_str: True – date by str, False – by class date
        :return: the first day
        """
        if by_str:
            return self.list_of_days[0].get_date()
        return self.list_of_days[0].datation

    def end(
            self,
            by_str=False
    ):
        """
        :param by_str: True – date by str, False – by class date
        :return: the last day
        """
        if by_str:
            return self.list_of_days[-1].get_date()
        return self.list_of_days[-1].datation

    def search_by_properties(
            self,
            *properties
    ):
        """
        words with these properties will be found
        """
        return list(filter(lambda x: x.is_fit(*properties), self.get_common_list()))

    def how_to_say_in_russian(self):
        """
        :return: ony English words
        """
        return list(map(lambda x: x.word, self.get_common_list()))

    def how_to_say_in_english(self):
        """
        :return: only Russian definition of the words
        """
        return reduce(
            lambda res, elem: res + elem.russian_only(def_only=True),
            self.list_of_days,
            []
        )

    def __contains__(
            self,
            item
    ):
        """
        :param item: words to find, str or Word
        :return: does this word in the Vocabulary
        """
        if isinstance(item, str):
            return any(item.lower().strip() in i for i in self.list_of_days)
        if isinstance(item, Word):
            return any(item in i for i in self.list_of_days)
        if isinstance(item, dt):
            if not any(i.datation == item for i in self.list_of_days):
                if self.begin() <= item <= self.end():
                    return True
                return False
            return True

    def __len__(self):
        """
        :return: overall amount of the words
        """
        return sum(len(i) for i in self.list_of_days)

    def __bool__(self):
        return bool(len(self.list_of_days))

    def __getitem__(
            self,
            item
    ):
        """
        :param item: date by str, date or slice
        :return: element with that date
        """
        # TODO: it could be some troubles after empty days removing
        item = str_to_date(item) if isinstance(item, str) else item
        
        if isinstance(item, dt):
            assert item in self, f"Wrong date: '{item}' func – Vocabulary.__getitem__"

            if item not in self.get_date_list():
                return WordsPerDay([], item)

            for i in filter(lambda x: item == x.datation, self.list_of_days):
                return i
        elif isinstance(item, slice):
            start = str_to_date(item.start) if item.start is not None else item.start
            stop = str_to_date(item.stop) if item.stop is not None else item.stop

            if start is not None and stop is not None and start > stop:
                raise ValueError(f"Start '{start}' cannot be more than stop '{stop}'")

            if start is not None and (start < self.list_of_days[0].datation or start > self.list_of_days[-1].datation):
                raise ValueError(f"Wrong start: '{start}'")

            if stop is not None and (stop > self.list_of_days[-1].datation or stop < self.list_of_days[0].datation):
                raise ValueError(f"Wrong stop: '{stop}'")

            begin = start if start is None else list(map(lambda x: x.datation == start, self.list_of_days)).index(True)
            end = stop if stop is None else list(map(lambda x: x.datation == stop, self.list_of_days)).index(True)

            return self.__class__(self.list_of_days[begin:end])

    def __iter__(self):
        return iter(self.list_of_days)

    def __call__(
            self,
            desired_word,
            **kwargs
    ):
        """
        :param desired_word: words to search
        :param kwargs: additional params:
            :param by_def: True – search for the word in defs, False – not
            if there is any Russian symbol – search in defs too
            :param by_example: ищёт слово в примерах(*)
        :return: joined with '\n' result string
        """
        up_word = lambda string, item: ' '.join(i.upper() if item.replace('–', '').strip() in i else i for i in string.split())

        in_def = lambda string, item: string[:dash(string)] + up_word(string[dash(string):], item)
        dash = lambda x: x.index('–')

        word = desired_word.lower().strip()

        assert len(word) > 1, f"Wrong word '{word}', func – Vocabulary.__call__"

        if 'by_def' in kwargs and kwargs['by_def']:
            word = f" – {word}"

        if 'by_example' in kwargs and kwargs['by_example']:
            res = reduce(
                lambda res, elem: res + [up_word(elem.get_examples(examples_only=True), word)],
                sum(list(self.search(word).values()), []),
                [])
            res = list(filter(len, res))

            return None if not res else '\n'.join(res)

        try:
            return '\n'.join([f"{date}: {S_TAB.join(map(lambda x: in_def(str(x), word), words))}" for date, words in self.search(word).items()])
        except Exception:
            return f"Word '{word}' not found"

    def __str__(self):
        """
        :return: string version of the Vocabulary and information about it
        """
        return f"{self.information()}\n{DIVIDER}\n" + \
               f"\n{DIVIDER}\n\n".join(map(str, self.list_of_days))


try:
    pass
    # init_from_xlsx('1_1_2020.xlsx', 'content')
    dictionary = Vocabulary()
    # print(dictionary.duration())
    # dictionary.create_pdf()

    # print(dictionary.information())
    # print(dictionary('возбуж'))

    # dictionary.repeat(date='7.12.2019', mode=1)
except Exception as trouble:
    print(trouble)

# TODO: в случае выбора ошибочного варианта при повторении логгировать id выбранного слова
# TODO: проверку наличия даты в файле из функции логгирования вынести в отдельную
# TODO: названия всех элементов абстрагировать от 'английский', заменив на learned

# TODO: сделать все функции выполняющими только одну поставленную задачу

# TODO: создать SQL (?) базу данных, ноч то делать с датами?:
#  id – слово – транскрипция – свойства – английское определение – русское определение

# TODO: создать SQL базу данных примеров:
#  id присутствующих в оригинальном тексте слов – оригинальный текст – перевод

# TODO: подогнаять размер кнопок под самый длинный айтем
# TODO: метод быстрого чтения из гифки в ВК

# TODO: парсер html – добавить возможность получать примеры употребления слов
#  из параллельного подкоруса в составе НКРЯ, BNC или COCA

# TODO: окно с галочками для выбора дней для повторения
# TODO: окно с вводом свойств слов для повторения
