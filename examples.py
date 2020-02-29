from tqdm import tqdm
from requests import get
from os import access, F_OK
from xlrd import open_workbook


from backup_setup import backup
from constants import SELF_EXAMPLES_PATH, CORPUS_EXAMPLES_URL, \
    CORPUS_EXAMPLES_PATH, CORPUS_XLSX_PATH, ORIGINAL_TEXT_END
from common_funcs import file_exist, add_to_file_name, file_name
from random import shuffle


class Examples:
    def __init__(self, f_path):
        """ Отсортированный список примеров """
        assert file_exist(f_path), \
            f"File does not exist: '{f_path}', func – Examples.__init__"

        self.path = f_path
        self.examples = self.load_examples()

    def load_examples(self):
        """ Загрузить отсортированные примеры из файла """
        examples = open(self.path, 'r', encoding='utf-8').readlines()
        return list(sorted(map(str.strip, examples)))

    def find(self, item, count=None):
        """ Вернуть n примеров слова списком """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – Examples.find"

        item = item.lower().strip()
        examples = self.examples[:]
        shuffle(examples)

        res = list(filter(lambda x: item in x.lower(), examples))
        if not res:
            raise ValueError(f"Example to '{item}' not found")
        if count is not None and len(res) < count:
            raise ValueError(f"There are only {len(res)} examples, not {count}")

        return res[:count]

    def backup(self):
        """ Backup примеров """
        f_name = add_to_file_name(file_name(self.path),
                                  f"_{len(self.examples)}")

        print("\nExamples backuping...")
        backup(f_name, self.path)

    def __bool__(self):
        return bool(self.examples)

    def __getitem__(self, item):
        assert isinstance(item, int) or isinstance(item, slice), \
            f"Wrong item: '{item}', int or slice expected, func – Examples.__getitem__"
        return self.examples[item]

    def __contains__(self, item):
        """ Есть ли пример такого слова """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – Examples.__contains__"

        item = item.lower().strip()
        return any(item in i.lower() for i in self.examples)

    def __len__(self):
        """ Общее количество примеров """
        return len(self.examples)

    def __str__(self):
        """ Вернуть пронумерованные примеры """
        return '\n'.join(f"{num}. {item}" for num, item in enumerate(self.examples, 1))

    def __iter__(self):
        return iter(self.examples)

    def __hash__(self):
        return hash(tuple(self.examples))


class SelfExamples(Examples):
    def __init__(self):
        super().__init__(SELF_EXAMPLES_PATH)


class CorpusExamples(Examples):
    def __init__(self):
        super().__init__(CORPUS_EXAMPLES_PATH)

    def find(self, item, count=None):
        res = super().find(item, count)
        # если примеров достаточно
        if len(res) <= count:
            return list(map(lambda x: tuple(x.split(ORIGINAL_TEXT_END)), res))

        # если недостаточно – сделать ещё запрос
        # непосредственно для этого слова
        self.new_examples(item)
        res = super().find(item, count)
        return list(map(lambda x: x.split(ORIGINAL_TEXT_END), res))

    def new_examples(self, item):
        """ Получить новые примеры из НКРЯ и выгрузить их в txt """
        assert isinstance(item, str) and item, \
            f"Wrong item: '{item}', str expected, func – CorpusExamples.new_examples"

        self.download_corpus_examples(item)
        self.convert_xlsx(f"{CORPUS_XLSX_PATH}\\{item}.xlsx")

        self.examples = self.load_examples()

    def download_corpus_examples(self, item):
        """ Скачать примеры из параллельного подкорпуса НКРЯ в xlsx """
        assert isinstance(item, str) and item, \
            f"Wrong word: '{item}', str expected, func – CorpusExamples.get_example"

        f_path = f"{CORPUS_XLSX_PATH}\\{item}.xlsx"
        assert not access(f_path, F_OK), \
            f"File: '{f_path}' still exist, func – CorpusExamples.get_example"

        response = get(CORPUS_EXAMPLES_URL.format(word=item), stream=True)

        with open(f_path, "wb") as handle:
            for data in tqdm(response.iter_content()):
                handle.write(data)

    def convert_xlsx(self, f_path):
        """ Преобразовать скачанные примеры в txt-файл """
        assert isinstance(f_path, str), \
            f"Wrong f_path: '{f_path}', str expected, func – CorpusExamples.convert_xlsx"
        assert access(f_path, F_OK), \
            f"File: '{f_path}' does not exist, func – CorpusExamplesconvert_xlsx."

        rb = open_workbook(f_path)
        sheet = rb.sheet_by_index(0)

        index = lambda item: item.index('[')
        with open(CORPUS_EXAMPLES_PATH, 'a', encoding='utf-8') as f:
            for i in range(sheet.nrows)[1:]:
                item = sheet.row_values(i)

                original, native = item[-2].strip(), item[-1].strip()
                original = original[:index(original)].replace("' ", "'")

                f.write(f"{original}{ORIGINAL_TEXT_END}{native}\n")

    def __str__(self):
        res = map(lambda x: x.replace(ORIGINAL_TEXT_END, ' Перевод: '), self.examples)
        return '\n'.join(f"{num}. {item}" for num, item in enumerate(res))