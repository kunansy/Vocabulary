from configparser import ConfigParser


# база слов
VOC_PATH = 'vocabulary.txt'
# лог повторений слов
REPEAT_LOG_PATH = 'repeat_log.json'
# путь к базе своих примеров
SELF_EX_PATH = 'self_examples.txt'
# путь к базе примеров из корпуса
# CORPUS_EX_PATH = 'corpus_examples.txt'
# путь к xlsx-файлам с примерами
# CORPUS_XLSX_PATH = 'corpus_examples'
# путь к базе неправильных глаголов
IRREGULAR_VERBS_PATH = '..\\..\\data\\user_data\\Irregular_verbs.txt'

# где хранить Word-документы
DOC_FOLDER = '..\\..\\data\\user_data\\docx'
# где хранить Excel-презентации
TABLE_FOLDER = '..\\..\\data\\user_data\\\\xlsx'
# где хранить PDF-документы
PDF_FOLDER = '..\\..\\data\\user_data\\\\pdf'
# куда файлы будут восстанавливаться
RESTORE_FOLDER_PATH = '..\\..\\data\\user_data\\\\restore'

# стандартный формат вывода даты
DATEFORMAT = '%d.%m.%Y'

# разделить при выводе WordsPerDay
DIVIDER = '_' * 50

# отступ в поиске при нескольких айтемах из одного дня
S_TAB = '\n\t\t\t'

# пути к GUI файлам для модуля повторения
MAIN_WINDOW_PATH = '//ui\\MainWindow.ui'
EXAMPLES_WINDOW_PATH = '//ui\\ExamplesWindow.ui'
MESSAGE_WINDOW_PATH = '//ui\\MessageWindow.ui'
SHOW_WINDOW_PATH = '//ui\\ShowWindow.ui'

# режимы работы повторения английских слов
ENG_REPEAT_MODS = {
    'original_word_to_native_defs': 1,
    'native_def_to_original_words': 2,
    'original_def_to_native_defs': 3,
    'native_def_to_original_defs': 4
}
# режимы работы повторения русских слов
RUS_REPEAT_MODS = {
    'word_to_defs': 1,
    'defs_to_word': 2
}

# URL и модель поиска синонимов
SYNONYMS_SEARCH_URL = 'https://rusvectores.org/{model}/{word}/api/json/'
SYNONYMS_SEARCH_MODEL = 'tayga_upos_skipgram_300_2_2019'

ID_LENGTH = 16

# If modifying these scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/drive']
# путь к токену для входа
TOKEN_PATH = '..\\..\\data\\program_data\\token.pickle'
# путь к регистрационным данным для логина
CREDS_PATH = '..\\..\\data\\program_data\\credentials.json'
# имя папки на Drive, куда заливаются бэкапы
BACKUP_FOLDER_NAME = 'backup'


# параллельный подкорпус НКРЯ
# сортированная до дате (сначала новые) выдача 5 документов на
# страницу (это быстрее), лексико-грамматический поиск
# lex – слово, p_num - номер страницы
PCORPUS_URL = "http://processing.ruscorpora.ru/search.xml?sort=i_grcreated&out=normal&dpp=5&spd=5&seed=16210&lex1={lex}" \
              "&parent1=0&max2=1&mysentsize=1608212&mysize=28363771&mycorp=%2528lang%253A%2522eng%2522%257Clang_trans" \
              "%253A%2522eng%2522%2529&p={p_num}&level1=0&level2=0&parent2=0&env=alpha&text=lexgramm&min2=1&mode=para"

# основной корпус НКРЯ (на русском)
# сортированная до дате (сначала новые) выдача 5 документов на
# страницу (это быстрее), лексико-грамматический поиск
# lex – слово, p_num - номер страницы
RCORPUS_URL = "http://processing.ruscorpora.ru/search.xml?sort=i_grcreated&lang=ru&lex1={lex}&env=alpha&startyear=&dpp=5" \
              "&nodia=1&sem-mod1=sem&sem-mod1=sem2&level1=0&seed=19291&mode=main&parent1=0&text=lexgramm&endyear=&spd=10&" \
              "out=normal&p={p_num}"

# разделитель оригинального текста и перевода
# в английских корпусных примерах
# ORIGINAL_TEXT_END = '%END%'

# английские предлоги
ENG_PREPS = [
    'of', 'by', 'with', 'in', 'on', 'for', 'at', 'per', 'as',
    'about', 'into', 'from', 'under', 'over', 'around', 'towards'
]

# расширения файлов и требуемые как параметр
# для обращения к Google Drive API типы
mimeTypes = {
    'txt': 'text/',
    'json': 'application/json',
    'folder': 'application/vnd.google-apps.folder',
    'pdf': 'application/pdf'
}

# TODO: fix Path via Pathlib
_ini = ConfigParser()
_ini.read('E:\\Files\\Python\\PythonProjects\\Vocabulary\\INIT.ini')

__LANGUAGE__ = _ini['settings']['__LANGUAGE__']
__NATIVE__ = _ini['settings']['__NATIVE__']

VOC_PATH = f"E:\\Files\\Python\\PythonProjects\\Vocabulary\\data\\user_data\\\\{__LANGUAGE__}_{VOC_PATH}"
REPEAT_LOG_PATH = f"E:\\Files\\Python\\PythonProjects\\Vocabulary\\data\\user_data\\{__LANGUAGE__}_{REPEAT_LOG_PATH}"
SELF_EX_PATH = f"E:\\Files\\Python\\PythonProjects\\Vocabulary\\data\\user_data\\{__LANGUAGE__}_{SELF_EX_PATH}"
# CORPUS_EX_PATH = f"E:\\Files\\Python\\PythonProjects\\Vocabulary\\{__LANGUAGE__}_{CORPUS_EX_PATH}"
# CORPUS_XLSX_PATH = f"E:\\Files\\Python\\PythonProjects\\Vocabulary\\{__LANGUAGE__}_{CORPUS_XLSX_PATH}"
