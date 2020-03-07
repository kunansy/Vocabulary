from tqdm import tqdm
from time import sleep
from requests import get
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
        """ Загрузить примеры из файла """
        if not file_exist(self.path):
            print(f"'{self.path}' not found. func – Examples.load_examples")
            return []

        examples = open(self.path, 'r', encoding='utf-8').readlines()
        return list(map(str.strip, examples))[:]

    def find(self, item: str):
        """ Вернуть примеры слова списком """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – Examples.find"

        return list(filter(lambda x: item in x.lower(),
                           self.examples))[:]

    def count(self, item: str):
        """ Количество примеров слова """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – Examples.count"

        return len(self.find(item))

    def backup(self):
        """ Backup примеров """
        f_name = add_to_file_name(file_name(self.path),
                                  f"_{len(self.examples)}")
        print(f"{self.__class__.__name__} backupping...")
        backup(f_name, self.path)

    def __bool__(self):
        return bool(self.examples)

    def __getitem__(self, item):
        assert isinstance(item, int) or isinstance(item, slice), \
            f"Wrong item: '{item}', int or slice expected, func – Examples.__getitem__"
        if isinstance(item, slice):
            res = self.__class__()
            res.examples = self.examples[item][:]
            return res
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
        res = list(map(lambda x: f"{x[0]}. {x[1]}",
                       enumerate(self.examples, 1)))
        return '\n'.join(res)

    def __iter__(self):
        return iter(self.examples)


class SelfExamples(Examples):
    def __init__(self):
        super().__init__(SELF_EXAMPLES_PATH)


# TODO: если переводить поиск к re, то вместо
#  readlines ипользовать read?
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
            print(f"Examples to '{item}' have requested...")
            self.download_corpus_examples(item)
        except Exception as trouble:
            print(trouble, f"Requesting examples to '{item}'",
                  "Terminating...", sep='\n')
            return

        try:
            path = self.xlsx_path.format(name=item)
            new_examples = self.convert_xlsx(path)[:]
        except Exception as trouble:
            print(trouble, f"Converting examples to '{item}'", "Terminating...", sep='\n')
        else:
            # пополнить текущую базу примеров
            self.examples += new_examples[:]
            print(f"Examples to: '{item}' successfully obtained")

    def download_corpus_examples(self, item: str):
        """ Скачать примеры в xlsx """
        assert isinstance(item, str) and item, \
            f"Wrong word: '{item}', str expected, func – CorpusExamples.get_example"

        f_path = self.xlsx_path.format(name=item)
        # если примеры такого слова уже есть,
        # то не надо качать их заново
        assert not file_exist(f_path), \
            f"File: '{f_path}' still exist, func – CorpusExamples.get_example"

        url = CORPUS_EXAMPLES_URL.format(word=item)
        response = get(url, stream=True)
        while response.status_code == 429:
            print("Запросов к корпусу слишком много, стоит немного подождать...")
            sleep(5)
            response = get(url, stream=True)

        # бывает, что запрос возвращается с 500 ошибкой
        assert response.ok, \
            f"Examples to '{item}' not found, {response}"

        with open(f_path, "wb") as handle:
            for data in tqdm(response.iter_content()):
                handle.write(data)

    def convert_xlsx(self, f_path: str):
        """ Преобразовать xlsx-примеры в txt,
            вернуть список новых примеров
        """
        assert file_exist(f_path), \
            f"File: '{f_path}' does not exist, func – CorpusExamples.convert_xlsx"
        assert file_ext(f_path) == 'xlsx', \
            f"Wrong file type: '{file_ext(f_path)}', xlsx expected, func – CorpusExamples.convert_xlsx"

        rb = open_workbook(f_path)
        sheet = rb.sheet_by_index(0)
        new_examples = []

        index = lambda x: x.index('[')
        with open(self.path, 'a', encoding='utf-8') as f:
            for i in range(sheet.nrows)[1:]:
                # TODO: циклы ускорять через numba?
                item = sheet.row_values(i)
                # бывает, что запрос был по русскому слову
                # в таком случае оригинал и перевод меняются местами
                if is_russian(item[-1]):
                    original, native = item[-2].strip(), item[-1].strip()
                elif is_russian(item[-2]):
                    native, original = item[-2].strip(), item[-1].strip()
                else:
                    raise ValueError("One of items: must be in Russian, "
                                     "func – CorpusExamples.convert_xlsx")
                # если источник указан — убрать его
                if '[' in original:
                    original = original[:index(original)]
                else:
                    print("Source is not mentioned, func – CorpusExamples.convert_xlsx")

                original = original.replace("' ", "'")
                if is_russian(native) and is_english(original):
                    f.write(f"{original}{ORIGINAL_TEXT_END}{native}\n")
                    new_examples.append((original, native))
                else:
                    print("Original must be in Eng, native – in Rus, "
                          "func – CorpusExamples.convert_xlsx")
        return new_examples[:]

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
            raise ValueError(f"Wrong item: '{item}', undefinable language, "
                             f"func – CorpusExamples.where")

    def count(self, item: str):
        """ Количество примеров слова """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – CorpusExamples.count"
        return len(self(item))

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
        """ Есть ли пример в базе """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – CorpusExamples.__contains__"
        return bool(self(item))

    def __str__(self):
        """ Оригинал и перевод через ' Перевод: ', пронумерованно """
        res = map(lambda x: f"{x[0]}. {x[1][0]} Перевод: {x[1][1]}",
                  enumerate(self.examples, 1))
        return '\n'.join(res)
