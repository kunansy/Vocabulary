import comtypes.client
from constants import *


from sys import argv
from PyQt5 import uic
from hashlib import sha3_512
from docx import Document
from docx.shared import Pt
from functools import reduce
from itertools import groupby
from datetime import datetime, timedelta
from datetime import date as dt
from xlrd import open_workbook
from xlsxwriter import Workbook
from random import shuffle, sample, choice
from os import system, getcwd, access, F_OK
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow


def str_to_date(string, swap=False):
    """
    :param string: строку формата dd.mm.yy
    :param: swap: менять ли местами день и месяц
    :return: date-объект
    """
    if isinstance(string, dt):
        return string

    split_symbol = '.' if string.count('.') == 2 else '_'

    if isinstance(string, str):
        string = ''.join(filter(lambda x: x.isdigit() or x in split_symbol, string))

        if swap:
            month, day, year = map(int, string.split(split_symbol))
        else:
            day, month, year = map(int, string.split(split_symbol))

        return dt(year, month, day)
    

def does_file_exist(filename):
    """
    :param filename: имя файла
    :return: существует ли такой файл
    """
    return access(filename, F_OK)


def init_vocabulary_from_file(filename=FILENAME):
    """
    :param filename: имя файла, где хранятся данные
    :return: список WordsPerDay
    """
    assert does_file_exist(filename)

    with open(filename, 'r', encoding='utf-8') as file:
        content = file.readlines()
        dates = list(map(clean_date, filter(lambda x: x.startswith('[') and '/' not in x, content)))

        index = lambda elem: content.index(elem)

        words_per_day = [WordsPerDay(list(map(Word, content[index(f"[{i}]\n") + 1: index(f"[/{i}]\n")])), i) for i in dates]
    file.close()
    return words_per_day


def fix_filename(name, extension):
    """
    :param name: имя файла
    :param extension: расширение файла
    :return: имя + расширение
    """
    return name if name.endswith(f".{extension}") else f"{name}.{extension}"


def clean_date(date, split_symbol='.'):
    """
    :param date: str, date
    :return: str, looks like '01.01.1970'
    it needs date format: dd.mm.yy
    """
    res = ''.join(filter(lambda x: x.isdigit() or x in split_symbol, date)).split(split_symbol)
    return '.'.join(map(lambda x: f"0{x}" if len(x) == 1 else x, res))


def language(item: str):
    # TODO: speed up
    assert isinstance(item, str)

    if any(i in rus_alphabet for i in item):
        return 'rus'
    return 'eng'


def is_russian(item: str):
    return language(item) == 'rus'


def is_english(item: str):
    return language(item) == 'eng'


def first_rus_index(item):
    # TODO: speed up
    return list(map(lambda x: x in rus_alphabet, item)).index(True)


def does_word_fit_with_american_spelling(word: str, by_str=True):
    assert isinstance(word, str)

    if word.endswith('e') or \
            (word.endswith('re') and not word.endswith('ogre')) or \
            any(i in word for i in unusual_combinations) or \
            any(word[i] == 'l' and word[i + 1] != 'l' for i in range(len(word) - 1)):
        return f"Вероятное, в слове '{word}' встречаются сочетания, несвойственные американской манере написания" if by_str else False
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

    example = []
    if 'Example: ' in other:
        ex_index = other.index('Example: ')
        example = [other[ex_index + 8:]]
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

    if any(word in i for i in english):
        print(f"'{word.capitalize()}' встречается также и в определении, замените его на ***")

    return word, properties, english, russian, example


def init_from_xlsx(filename, out='tmp'):
    """
    Функция преобразует xlsx файл в список объектов класса Word,
    выводит их в файл, вывод осуществляется с дополнением старого содержимого:
    [date]
    ...words...
    [/date]
    :param filename: имя xlsx файла
    :param out: имя файла, в который будет выведен список слов формата Word, по умолчанию – tmp
    """
    assert does_file_exist(filename)

    rb = open_workbook(filename)
    sheet = rb.sheet_by_index(0)

    # удаляется заглавие, введение и прочие некорректные данные
    value = list(filter(lambda x: len(x[0]) and (len(x[2]) or len(x[3])), [sheet.row_values(i) for i in range(sheet.nrows)]))
    value.sort(key=lambda x: x[0])

    value = list(map(lambda x: Word(x[0], '', x[2], x[3]), value))

    # группировка одинаковых слов вместе
    value = groupby(value, key=lambda x: x.word)

    file_out = open(out, 'a', encoding='utf-8')

    # суммирование одинаковых слов в один объект класса Word
    result = [reduce(lambda res, elem: res + elem, list(group[1]), Word('')) for group in value]

    # файл, скачанный из Cambridge Dictionary, содержит дату в английском формате
    filename = filename.replace(f".{gfile_ext}", '')
    date = str_to_date(filename, swap=True).strftime(DATEFORMAT)

    print(f"\n\n[{date}]", file=file_out)
    print(*result, sep='\n', file=file_out)
    print(f"[/{date}]", file=file_out)

    file_out.close()


def create_docx(content=[], out_file=None, header='General', russian_only=False):
    """
    :param content: список объектов класса Word, которые будут выведены в файл
    :param out_file: имя файла, если не передано – именем файла будет header
    :param header: заголовок документа
    :param russian_only: True: слово – русские опредления; False: слово – английское определение; русское
    """
    words = Document()

    style = words.styles['Normal']
    font = style.font
    font.name = 'Avenir Next Cyr'
    font.size = Pt(16)

    if out_file is None:
        out_file = f"{header}.{dfile_ext}"

    out_file = fix_filename(out_file, dfile_ext)

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

    words.save(f"{getcwd()}\\{docx_folder}\\{out_file}")


def create_pdf(content=[], in_file=None, out_file=None, russian_only=False):
    """
    :param content: список объектов класса Word, которые будут выведены в файл
    :param in_file: имя входного файла docx, который будет преобразован в pdf
    если его нет – создаётся временный docx файл, по завершение выполнения функции удаляется
    :param out_file: имя файла, если не передано – именем файла будет header
    :param russian_only: True: слово – русские опредления; False: слово – английское определение; русское
    """
    # нужно ли удалять файл потом
    flag = False

    if in_file is None or not \
            (does_file_exist(fix_filename(in_file, dfile_ext)) or
             does_file_exist(f"{docx_folder}\\{fix_filename(in_file, dfile_ext)}")):
        flag = True
        in_file = f"temp.{dfile_ext}"
        create_docx(content, out_file=in_file, russian_only=russian_only)

    in_file = fix_filename(in_file, dfile_ext)
    out_file = fix_filename(out_file, pfile_ext)

    word = comtypes.client.CreateObject('Word.Application')
    doc = word.Documents.Open(f"{getcwd()}\\{docx_folder}\\{in_file}")
    doc.SaveAs(f"{getcwd()}\\{pdf_folder}\\{out_file}", FileFormat=17)

    doc.Close()
    word.Quit()

    if flag:
        system(f'del "{getcwd()}\\{docx_folder}\\{in_file}"')


def word_id(item):
    """
    :param item: слово: слока или объект класса Word
    :return: первые и последние четыре символа sha3_512 хеша этого слова
    """
    assert isinstance(item, str) or isinstance(item, Word)

    word = item if isinstance(item, str) else item.word

    id = sha3_512(bytes(word, encoding='utf-8')).hexdigest()
    return id[:4] + id[-4:]


class RepeatWords(QMainWindow):
    def __init__(self, words, mode=1, filename=log_filename, window_title='Repeat'):
        super().__init__()
        uic.loadUi(MainRepeatWindow, self)

        self.initUI(window_title)

        self.word = Word('')
        self.mode = None
        self.you_are_right_if = None
        self.init_button = None

        if isinstance(mode, int):
            assert mode in range(1, 5)
            self.mode = mode
        elif isinstance(mode, str):
            assert mode in mods
            self.mode = mods[mode]
        else:
            raise TypeError(f"Wrong mode type: '{mode}', {type(mode)}, correct int or str expected")

        if self.mode == 1:
            self.you_are_right_if = lambda choice: choice.lower() == self.word.get_russian(def_only=True)
            self.init_button = lambda item: item.get_russian(def_only=True).capitalize()
        elif self.mode == 2:
            self.you_are_right_if = lambda choice: choice.lower() == self.word.word
            self.init_button = lambda item: item.word.capitalize()
        elif self.mode == 3:
            self.you_are_right_if = lambda choice: choice.lower() == self.word.get_russian(def_only=True)
            self.init_button = lambda item: item.get_russian(def_only=True).capitalize()
        elif self.mode == 4:
            self.you_are_right_if = lambda choice: choice.lower() == self.word.get_english(def_only=True)
            self.init_button = lambda item: item.get_english(def_only=True).capitalize()

        shuffle(words)
        self.words = words[:]

        shuffle(words)
        self.wrong_translations = words[:]

        # имя файла, в который будут логгироваться результаты
        self.filename = filename

    def initUI(self, window_title):
        self.AlertWindow = Alert(self, [])
        self.MessageWindow = Message(self, [])
        self.setWindowTitle(window_title)

        self.choice_buttons = [
            self.Translation1,
            self.Translation2,
            self.Translation3,
            self.Translation4,
            self.Translation5,
            self.Translation6
        ]

        self.ExitButton.clicked.connect(self.close)
        self.ExitButton.setText('Exit')

        self.HintButton.clicked.connect(self.hint)
        self.HintButton.setText('Hint')

        [self.choice_buttons[i].clicked.connect(self.are_you_right) for i in range(len(self.choice_buttons))]

    def test(self):
        if self.word:
            self.wrong_translations.append(self.word)

        if len(self.words) == 1:
            self.WordsRemain.setText("The last one")
        else:
            self.WordsRemain.setText(f"Remain: {len(self.words)} words")

        self.word = choice(self.words)
        self.words.remove(self.word)
        self.wrong_translations.remove(self.word)

        if self.mode == 1:
            self.WordToReapeat.setText(self.word.word.capitalize())
        elif self.mode == 2:
            self.WordToReapeat.setText(self.word.get_russian(def_only=True).capitalize())
        elif self.mode == 3:
            self.WordToReapeat.setText(self.word.get_english(def_only=True).capitalize())
        elif self.mode == 4:
            self.WordToReapeat.setText(self.word.get_russian(def_only=True).capitalize())

        self.set_buttons()

    def set_buttons(self):
        # ставится ли верное определение
        is_right_def = True

        wrong_translations = sample(self.wrong_translations, len(self.choice_buttons))

        for i in sample(range(len(self.choice_buttons)), len(self.choice_buttons)):
            if is_right_def:
                [self.choice_buttons[j].setText('') for j in range(len(self.choice_buttons))]

            w_item = choice(wrong_translations)
            wrong_translations.remove(w_item)

            if is_right_def:
                self.choice_buttons[i].setText(self.init_button(self.word))
                is_right_def = False
            else:
                self.choice_buttons[i].setText(self.init_button(w_item))

    def are_you_right(self):
        if self.you_are_right_if(self.sender().text()):
            self.log(
                self.word,
                "excellent"
            )
            if self.word.get_examples(examples_only=True):
                self.AlertWindow.display(
                    result='excellent',
                    example=self.word.get_examples(examples_only=True, by_list=True),
                    style="color: 'green';"
                )
            else:
                self.MessageWindow.display(
                    message='excellent',
                    style="color: 'green';"
                )

            if len(self.words) > 0:
                self.test()
            else:
                self.MessageWindow.display(
                    message='The end',
                    style="color: 'black';"
                )
                self.close()
        else:
            self.log(
                self.word,
                'wrong',
                w_choice=self.sender().text()
            )

            if self.word.get_examples(examples_only=True):
                self.AlertWindow.display(
                    result='wrong',
                    example=self.word.get_examples(examples_only=True, by_list=True),
                    style="color: 'red';"
                )
            else:
                self.MessageWindow.display(
                    message='wrong',
                    style="color: 'red';"
                )

    def hint(self):
        if self.word.get_examples(examples_only=True):
            self.AlertWindow.display(
                f"{self.HintButton.text()}",
                self.word.get_examples(examples_only=True),
                style="color: blue"
            )

    def log(self, word, result, w_choice=''):
        """
        :param word: слово и результат
        :return: логгирование в файл
        """
        if not does_file_exist(self.filename):
            temp = open(self.filename, 'a', encoding='utf-8')
            temp.close()

        if len(w_choice) > 0:
            w_choice = f", выбранный вариант: '{w_choice}'"

        content = open(self.filename, 'r').readlines()

        with open(self.filename, 'a', encoding='utf-8') as log_file:
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
        uic.loadUi(AlertWindow, self)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Alert')

        self.Result.setText('')
        self.Examples.setText('')

    def display(self, result, example, style=''):
        self.Result.setText(result.capitalize())

        if style:
            self.Result.setStyleSheet(style)

        assert len(example) > 0

        self.Examples.setText('\n'.join(map(lambda x: f"{x[0]}. {x[1]}", enumerate(example, 1))))

        self.show()


class Message(QWidget):
    def __init__(self, *args):
        super().__init__()
        uic.loadUi(MessageWindow, self)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Alert')
        self.MessageText.setText('')

    def display(self, message, style=''):
        if style:
            self.MessageText.setStyleSheet(style)

        self.MessageText.setText(message.capitalize())
        self.show()


class Properties:
    def __init__(self, properties: str):
        # TODO
        assert isinstance(properties, str) or isinstance(properties, list) or isinstance(properties, dict)
        self.properties = {}

        if isinstance(properties, dict):
            self.properties = properties
            return

        properties = ', '.join(properties) if isinstance(properties, list) else properties

        properties = properties.replace('[', '').replace(']', '').strip()

        if not len(properties):
            return

        self.properties = {key.strip(): True for key in properties.split(',')}

    def __eq__(self, other):
        if isinstance(other, Properties):
            return self.properties == other.properties
        return self.properties.get(other, False)

    def __ne__(self, other):
        return not (self == other)

    def __getitem__(self, item):
        return self.properties.get(item, False)

    def __getattr__(self, item):
        return self.properties.get(item, False)

    def __len__(self):
        return len(self.properties)

    def __add__(self, other):
        if isinstance(other, Properties):
            res = self.properties.copy()

            for key, value in other.properties.items():
                res[key] = value

            return Properties(res)

    def __hash__(self):
        return hash(self.properties)

    def __str__(self):
        return f"[{', '.join(map(lambda key: f'{key}', self.properties.keys()))}]"


class Word:
    def __init__(self, word='', properties='', english_def=[], russian_def=[], example=[]):
        """
        :param word: english word to learn
        :param properties: POS, language level, formal, ancient,
        if verb (transitivity, ) if noun (countable, )
        :param english_def: english definitions of the word: list
        :param russian_def: russian definitions of the word (maybe don't exist): list
        :param example: examples of the word using
        """
        assert isinstance(word, str)
        assert isinstance(properties, str) or isinstance(properties, Properties)
        assert isinstance(english_def, list) or isinstance(english_def, str)
        assert isinstance(russian_def, list) or isinstance(russian_def, str)

        if ' – ' in word:
            self.__init__(*parse_str(word))
        else:
            self.word = word.lower().strip()

            if isinstance(russian_def, str) and isinstance(english_def, str):
                english_def = english_def.split(';')
                russian_def = russian_def.split(';')

            self.english = list(map(str.strip, english_def))
            self.russian = list(map(str.strip, russian_def))

            self.properties = ''

            if isinstance(properties, Properties):
                self.properties = properties
            elif isinstance(properties, str):
                self.properties = Properties(properties)

            if isinstance(example, str):
                self.examples = list(map(str.strip, example.split(';')))
            elif isinstance(example, list):
                self.examples = list(map(str.strip, example))

            self.id = word_id(self.word)

    def get_russian(self, def_only=False, by_list=False):
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

    def get_english(self, def_only=False, by_list=False):
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

    def get_examples(self, examples_only=False, by_list=False):
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

    def word_id(self):
        return self.id if self.id else word_id(self.word)

    def is_fit(self, *properties):
        return all(self.properties[i] for i in properties)

    def __getitem__(self, index: int):
        """
        :param index: int value
        :return: the letter under the index
        """
        assert isinstance(index, int) and len(self.word) >= abs(index)

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
        properties = f" {self.properties}" * (len(self.properties) != 0)
        eng = f"{'; '.join(self.english)}\t" * (len(self.english) != 0)
        rus = f"{'; '.join(self.russian)}" * (len(self.russian) != 0)

        return f"{self.word.capitalize()}{properties} – {eng}{rus}"

    def __hash__(self):
        return hash(
            hash(self.word) +
            hash(self.properties) +
            hash(self.russian) +
            hash(self.english) +
            hash(self.examples)
        )


class WordsPerDay:
    def __init__(self, content: list, datation):
        """
        :param content: список объектов класса Word
        :param date: дата изучения
        """
        self.datation = str_to_date(datation)
        self.content = list(sorted(content))

    def russian_only(self, def_only=False):
        """
        :param def_only: return words with its definitions or not
        :return: the list of the words with its Russian definitions, the day contains
        """
        return reduce(
            lambda res, elem: res + [elem.get_russian(def_only)], 
            self.content, 
            []
        )

    def english_only(self, def_only=False):
        """
        :param def_only: return words with its definitions or not
        :return: the list of the words with its English definitions, the day contains
        """
        return reduce(
            lambda res, elem: res + [elem.get_english(def_only)], 
            self.content, 
            []
        )

    def examples_only(self, examples_only=False):
        res = reduce(
            lambda res, elem: res + [elem.get_examples(examples_only)], 
            self.content, 
            []
        )
        
        return list(filter(len, res))

    def get_words_list(self, with_eng=False, with_rus=False):
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

    def get_examples(self, examples_only=False):
        return reduce(
            lambda res, elem: res + [elem.get_examples(examples_only=examples_only)],
            self.content,
            []
        )

    def get_date(self, dateformat=DATEFORMAT):
        return self.datation.strftime(dateformat)

    def get_information(self):
        return f"{self.get_date()}\n{len(self)}"

    def repeat(self, **params):
        app = QApplication(argv)

        repeat = RepeatWords(
            words=self.content,
            window_title=self.get_date(),
            **params
        )
        repeat.test()
        repeat.show()

        exit(app.exec_())

    def create_docx(self, russian_only=False):
        create_docx(
            self.content, 
            header=self.get_date(), 
            russian_only=russian_only
        )

    def create_pdf(self, russian_only=False):
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
        assert isinstance(item, str) or isinstance(item, Word)

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
    def __init__(self, list_of_days=None):
        if list_of_days is None or len(list_of_days) == 0:
            self.list_of_days = init_vocabulary_from_file(FILENAME)[:]
        else:
            self.list_of_days = list_of_days[:]

        self.graphic_name = f"{xlsx_folder}\\{gfile_name}_{self.get_date_range()}.{gfile_ext}"

    def get_pairs_date_count(self):
        return {i.get_date(): len(i) for i in self.list_of_days}

    def get_max_day(self, with_inf=False):
        maximum_day = max(self.list_of_days)

        if with_inf:
            return f"Maximum day {maximum_day.get_date()}: {len(maximum_day)}"
        return maximum_day

    def get_min_day(self, with_inf=False):
        minimum_day = min(list(filter(lambda x: len(x) > 1, self.list_of_days)))

        if with_inf:
            return f"Minimum day {minimum_day.get_date()}: {len(minimum_day)}"
        return minimum_day

    def get_avg_count_of_words(self):
        """
        :return: среднее количество изученных за день слов
        """
        return sum(len(i) for i in self.list_of_days) // len(self.list_of_days)

    def get_empty_days_count(self):
        """
        :return: количество пустых дней
        """
        return len(list(filter(lambda x: len(x) == 0, self.list_of_days)))

    def get_statistics(self):
        """
        :return: статистику о словаре
        """
        avg_value = self.get_avg_count_of_words()
        empty_count = self.get_empty_days_count()

        avg_inf = f"Average value = {avg_value}"
        days_count = f"Days = {len(self.list_of_days)}"
        total_amount = f"Total = {len(self)}"
        would_total = f"Would be total = {len(self) + avg_value * empty_count}\n" \
                      f"Lost = {self.get_avg_count_of_words() * empty_count} items per " \
                      f"{empty_count} empty days"
        min_max = f"{self.get_max_day(with_inf=True)}\n{self.get_min_day(with_inf=True)}"

        return f"{days_count}\n{avg_inf}\n{total_amount}\n{would_total}\n\n{min_max}"

    def get_all_examples(self, examples_only=False):
        return reduce(
            lambda res, elem: res + [elem.get_examples(examples_only=examples_only)],
            self.list_of_days,
            []
        )

    def get_date_list(self, by_str=False):
        """
        :param by_str: строками или объектами date
        :return: список дат
        """
        if by_str:
            return list(map(lambda x: x.get_date(), self.list_of_days))
        return list(map(lambda x: x.datation, self.list_of_days))

    def get_date_range(self):
        return f"{self.begin(True)}–{self.end(True)}"

    def get_item_before_now(self, days_count):
        """
        :param days_count: количество дней отступа от текущей даты, int > 0
        :return: непустой айтем, чей индекс = len - days_count
        """
        assert isinstance(days_count, int) and days_count > 0

        index = len(list(filter(len, self.list_of_days))) - days_count

        assert index >= 0

        return list(filter(len, self.list_of_days))[index]

    def get_common_list(self):
        """
        :return: отсортированный общий список слов
        """
        return list(sorted(reduce(
            lambda result, element: result + element.get_content(),
            self.list_of_days,
            []
        )))

    def get_examples(self, examples_only=False):
        """
        :return: все существующие примеры из слов(*)
        """
        return reduce(
            lambda result, element: result + element.examples_only(examples_only),
            self.list_of_days,
            []
        )

    def create_xlsx(self):
        """
        :return: создаст Excel файл со статистикой, имя файла – границы ведения дневника
        """
        if does_file_exist(self.graphic_name):
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

        worksheet = workbook.add_worksheet(sheet_name)

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
            'values': f"={sheet_name}!B1:B{row}",
            'categories': f"={sheet_name}!A1:A{row}",
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

    def create_docx(self, russian_only=False):
        create_docx(
            content=self.get_common_list(),
            out_file=self.get_date_range(),
            header=self.get_date_range(),
            russian_only=russian_only
        )

    def create_pdf(self, russian_only=False):
        create_pdf(
            content=self.get_common_list(),
            in_file=self.get_date_range(),
            out_file=self.get_date_range(),
            russian_only=russian_only
        )

    def search(self, item):
        """
        :param item: искомый элемент: строка или объект класа Word
        :return: словарь с датой в ключе и словами из дня с этой датой в значении
        """
        assert len(item) > 1
        assert isinstance(item, str) or isinstance(item, Word)
        assert item.lower().strip() in self

        item = item.lower().strip() if isinstance(item, str) else item

        return {i.get_date(): i[item] for i in filter(lambda x: item in x, self.list_of_days)}

    def show_graph(self):
        assert does_file_exist(self.graphic_name)

        system(self.graphic_name)

    def information(self):
        """
        создаёт xlsx-файл
        :return: строку с полной информацией о словаре и самим словарём
        """
        self.create_xlsx()

        return '\n'.join(map(lambda day_count: f"{day_count[0]}: {day_count[1]}", self.get_pairs_date_count().items())) + \
               f"\n{divider}\n{self.get_statistics()}"

    def repeat(self, day_before_now=None, date=None, **params):
        # TODO: повторение изученных 1, 3, 7, 21 день назад слов
        repeating_day = []

        if date is None and day_before_now is not None:
            repeating_day = self.get_item_before_now(day_before_now)

        if day_before_now is None and date is not None:
            repeating_day = self[date]

        assert len(repeating_day) != 0

        app = QApplication(argv)

        repeat = RepeatWords(
            words=repeating_day.get_content(),
            window_title=repeating_day.get_date(),
            **params
        )

        repeat.test()
        repeat.show()

        exit(app.exec_())

    def remember_via_example(self, word):
        """
        :param word: искомое слово
        :return: пример с употреблением этого слова
        """
        return self(word, by_list=True)

    def begin(self, by_str=False):
        if by_str:
            return self.list_of_days[0].get_date()
        return self.list_of_days[0].datation

    def end(self, by_str=False):
        if by_str:
            return self.list_of_days[-1].get_date()
        return self.list_of_days[-1].datation

    def search_by_properties(self, *properties):
        return list(filter(lambda x: x.is_fit(*properties), self.get_common_list()))

    def how_to_say_in_russian(self):
        return reduce(
            lambda res, elem: res + elem.get_words_list(),
            self.list_of_days,
            []
        )

    def how_to_say_in_english(self):
        return reduce(
            lambda res, elem: res + elem.russian_only(def_only=True),
            self.list_of_days,
            []
        )

    def __contains__(self, item):
        """
        :param item: искомое слово строкой или объектом класса Word
        :return: содержится ли такое слово в словаре
        """
        if isinstance(item, str):
            return any(item.lower().strip() in i for i in self.list_of_days)
        if isinstance(item, Word):
            return any(item in i for i in self.list_of_days)

    def __len__(self):
        """
        :return: общее количество слов в словаре
        """
        return sum(len(i) for i in self.list_of_days)

    def __bool__(self):
        return bool(len(self.list_of_days))

    def __getitem__(self, item):
        """
        :param item: дату строкой, классом date или срезом
        :return: айтем с соответствующей датой
        """
        item = str_to_date(item) if isinstance(item, str) else item
        
        if isinstance(item, dt):
            assert item in self.get_date_list()

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

    def __call__(self, desired_word, **kwargs):
        """
        :param desired_word: words to search
        :param kwargs: дополнительные параметры:
            :param by_def: ищет по определениям либо при указании этого параметра True,
            либо при введении русского слова в поиск
            :param by_example: ищёт слово в примерах(*)
        :return: строку с результатами, объединённую символом '\n'
        """
        # TODO
        up_word = lambda string, item: ' '.join(i if item not in i else i.upper() for i in string.split())

        in_def = lambda string, item: string[:dash(string)] + up_word(string[dash(string):], item)
        dash = lambda x: x.index('–')

        word = desired_word.lower().strip()

        assert len(word) > 1

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
            return '\n'.join([f"{date}: {s_tab.join(map(lambda x: in_def(str(x), word), words))}" for date, words in self.search(word).items()])
        except Exception:
            return f"Word '{word}' not found"

    def __str__(self):
        """
        :return: string version of te Vocabulary and information about it
        """
        return f"{self.information()}\n{divider}\n" + \
               f"\n{divider}\n\n".join(map(str, self.list_of_days))


try:
    pass
    # init_from_xlsx('2_3_2020.xlsx', 'content')
    dictionary = Vocabulary()
    # print(dictionary.information())
    # print(dictionary('think'))

    # eng = dictionary.how_to_say_in_russian()
    # shuffle(eng)
    # create_pdf(eng, out_file='How to say in it Russian')

    # dictionary.repeat(date='31.1.2020', mode=1)
    # dictionary.repeat(date='31.1.2020', mode=2)
except Exception as trouble:
    print(trouble)

# TODO: окно со списком всех изученных за день слов перед их повторением

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
