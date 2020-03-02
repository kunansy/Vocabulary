from tqdm import tqdm
from requests import get
from os import access, F_OK
from xlrd import open_workbook


from backup_setup import backup
from constants import (SELF_EXAMPLES_PATH, CORPUS_EXAMPLES_URL,
                       CORPUS_EXAMPLES_PATH, CORPUS_XLSX_PATH, ORIGINAL_TEXT_END)
from common_funcs import (file_exist, add_to_file_name, file_name,
                          is_russian, is_english, file_ext)


class Examples:
    def __init__(self, f_path: str):
        """ Инициализация списка примеров по пути """
        assert file_exist(f_path), \
            f"File does not exist: '{f_path}', func – Examples.__init__"

        self.path = f_path
        self.examples = self.load_examples()

    def load_examples(self):
        """ Загрузить отсортированные примеры из файла """
        if not file_exist(self.path):
            print(f"'{self.path}' not found. func – Examples.load_examples")
            return []

        examples = open(self.path, 'r', encoding='utf-8').readlines()
        return list(sorted(map(str.strip, examples)))[:]

    def find(self, item: str):
        """ Вернуть примеры слова списком """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – Examples.find"

        item = item.lower().strip()
        return list(filter(lambda x: item in x.lower(), self.examples))[:]

    def count(self, item: str):
        """ Количество примеров слова """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – Examples.count"

        return len(self.find(item))

    def backup(self):
        """ Backup примеров """
        f_name = add_to_file_name(file_name(self.path),
                                  f"_{len(self.examples)}")

        backup(f_name, self.path)

    def __bool__(self):
        return bool(self.examples)

    def __getitem__(self, item):
        assert isinstance(item, int) or isinstance(item, slice), \
            f"Wrong item: '{item}', int or slice expected, func – Examples.__getitem__"
        return self.examples[item]

    def __contains__(self, item: str):
        """ Есть ли пример такого слова """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – Examples.__contains__"

        item = item.lower().strip()
        return any(item in i.lower() for i in self.examples)

    def __len__(self):
        """ Количество примеров """
        return len(self.examples)

    def __str__(self):
        """ Пронумерованные примеры """
        return '\n'.join(f"{num}. {item}" for num, item in enumerate(self.examples, 1))

    def __iter__(self):
        return iter(self.examples)

    def __hash__(self):
        return hash(tuple(self.examples))


class SelfExamples(Examples):
    def __init__(self):
        super().__init__(SELF_EXAMPLES_PATH)

    def backup(self):
        print("Self examples backupping...")
        super().backup()


class CorpusExamples(Examples):
    def __init__(self):
        """ Инициализация списка примеров по пути;
            список из (оригинал, перевод);
            путь, где храняться xlsx-файлы с запросами из НКРЯ
        """
        super().__init__(CORPUS_EXAMPLES_PATH)
        self.xlsx_path = CORPUS_XLSX_PATH + "\\{name}.xlsx"

    def load_examples(self):
        """ Разделено на (оригинал, перевод) """
        base = super().load_examples()
        return list(map(lambda x: tuple(x.split(ORIGINAL_TEXT_END)), base))[:]

    def find(self, item):
        """ Поиск в оригинале и переводе, если примеров нет
            в базе – запросить ещё
        """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – CorpusExamples.find"

        item = item.lower().strip()
        # если есть русский символ, то соответствие может
        # быть только в переводе
        where = self.where(item)

        res = list(filter(lambda x: item in where(x), self.examples))
        if res:
            return list(filter(lambda x: item in where(x), self.examples))[:]
        else:
            # если примера нет – сделать ещё запрос
            # непосредственно для этого слова
            self.new_examples(item)

            return list(filter(lambda x: item in where(x), self.examples))

    def new_examples(self, item: str):
        """ Получить примеры и выгрузить их в txt,
            пополнив self.examples
        """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – CorpusExamples.new_examples"

        try:
            self.download_corpus_examples(item)
        except Exception as trouble:
            print(trouble)
            return

        try:
            self.convert_xlsx(self.xlsx_path.format(name=item))
        except Exception as trouble:
            print(trouble)
        else:
            self.examples = self.load_examples()[:]
            print(f"Примеры употребления слова: '{item}' успешно получены")

    def download_corpus_examples(self, item: str):
        """ Скачать примеры в xlsx """
        assert isinstance(item, str) and item, \
            f"Wrong word: '{item}', str expected, func – CorpusExamples.get_example"

        f_path = self.xlsx_path.format(name=item)

        # если примеры такого слова уже есть,
        # то не надо качать их заново
        assert not access(f_path, F_OK), \
            f"File: '{f_path}' still exist, func – CorpusExamples.get_example"

        response = get(CORPUS_EXAMPLES_URL.format(word=item), stream=True)

        # бывает, что запрос возвращается с 500 ошибкой
        assert response.ok, f"Пример к '{item}' в корпусе не найден, {response}"

        with open(f_path, "wb") as handle:
            for data in tqdm(response.iter_content()):
                handle.write(data)

    def convert_xlsx(self, f_path: str):
        """ Преобразовать xlsx-примеры в txt """
        assert isinstance(f_path, str), \
            f"Wrong f_path: '{f_path}', str expected, func – CorpusExamples.convert_xlsx"
        assert access(f_path, F_OK), \
            f"File: '{f_path}' does not exist, func – CorpusExamples.convert_xlsx"
        assert file_ext(f_path) == 'xlsx', \
            f"Wrong file type: '{file_ext(f_path)}', xlsx expected, func – CorpusExamples.convert_xlsx"

        rb = open_workbook(f_path)
        sheet = rb.sheet_by_index(0)

        index = lambda item: item.index('[')
        with open(self.path, 'a', encoding='utf-8') as f:
            for i in range(sheet.nrows)[1:]:
                item = sheet.row_values(i)

                # бывает, что запрос был по русскому слову
                # в таком случае оригинал и перевод меняются местами
                if is_russian(item[-1]):
                    original, native = item[-2].strip(), item[-1].strip()
                    original = original[:index(original)].replace("' ", "'")
                elif is_russian(item[-2]):
                    native, original = item[-2].strip(), item[-1].strip()
                    original = original[:index(original)].replace("' ", "'")
                else:
                    raise ValueError("Something went wrong, func – CorpusExamples.convert_xlsx")

                if is_russian(native) and is_english(original):
                    f.write(f"{original}{ORIGINAL_TEXT_END}{native}\n")
                else:
                    print("Original must be in Eng, native – in Rus, func – CorpusExamples.convert_xlsx")

    def where(self, item: str):
        """ Определить, где искать: если is_rus(item) – в
            переводе, иначе – в оригинале
        """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – CorpusExamples.where"

        if is_russian(item.lower()):
            return lambda x: x[1]
        elif is_english(item.lower()):
            return lambda x: x[0]
        else:
            raise ValueError(f"Wrong item: '{item}', undefinable language")

    def count(self, item: str):
        """ Количество примеров слова """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – CorpusExamples.count"

        item = item.lower().strip()
        where = self.where(item)

        res = list(filter(lambda x: item in where(x), self.examples))
        return len(res)

    def backup(self):
        print("Corpus examples backupping...")
        super().backup()

    def __call__(self, item: str):
        """ Найти пример слова в базе. Если примера
            нет  – не запршивать новый
        """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – CorpusExamples.__call__"

        where = self.where(item)
        item = item.lower().strip()
        return list(filter(lambda x: item in where(x), self.examples))

    def __contains__(self, item: str):
        """ Есть ли пример в базе,
            Если в item есть русский символ, то поиск в переводах,
            а иначе в оригинальных предложениях
        """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – CorpusExamples.__contains__"

        item = item.lower().strip()

        # если есть русский символ, то соответствие
        # может быть только в переводе
        where = self.where(item)

        return any(item in where(i) for i in self.examples)

    def __str__(self):
        """ Оригинал и перевод через ' Перевод: ' """
        res = map(lambda x: f"{x[0]}. Перевод: {x[1]}", self.examples)
        return '\n'.join(f"{num}. {item}" for num, item in enumerate(res))