RUS_ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

# пути к пользовательским данным
DATA_PATH = 'user_data\\vocabulary.txt'
REPEAT_LOG_PATH = 'user_data\\repeating_log.json'
SELF_EXAMPLES_PATH = 'user_data\\self_examples.txt'
CORPUS_EXAMPLES_PATH = 'user_data\\corpus_examples.txt'
CORPUS_XLSX_PATH = 'user_data\\corpus_examples'
IRREGULAR_VERBS_PATH = 'user_data\\Irregular_verbs.txt'

TABLE_EXT = 'xlsx'
DOC_EXT = 'docx'
PDF_EXT = 'pdf'
DB_EXT = 'db'

DOC_FOLDER = 'user_data\\docx'
TABLE_FOLDER = 'user_data\\xlsx'
PDF_FOLDER = 'user_data\\pdf'

DATEFORMAT = '%d.%m.%Y'

# разделить при выводе WordsPerDay
DIVIDER = '_' * 50

# отступ в поиске при нескольких айтемах из одного дня
S_TAB = '\n\t\t\t'

# пути к GUI файлам для модуля повторения
MAIN_WINDOW_PATH = 'ui\\MainWindow.ui'
ALERT_WINDOW_PATH = 'ui\\AlertWindow.ui'
MESSAGE_WINDOW_PATH = 'ui\\MessageWindow.ui'
SHOW_WINDOW_PATH = 'ui\\ShowWindow.ui'

# режимы работы повторения
REPEATING_MODS = {
    'eng_word_to_rus_defs': 1,
    'rus_def_to_eng_words': 2,
    'eng_def_to_rus_defs': 3,
    'rus_def_to_eng_defs': 4
}

# несвойственные американской манере письма сочетания
W_MIXES = ['ou', 'tre', 'nce', 'mm', 'ue', 'se']

# URL и модель поиска синонимов
SYNONYMS_SEARCH_URL = 'https://rusvectores.org/{model}/{word}/api/json/'
SYNONYMS_SEARCH_MODEL = 'tayga_upos_skipgram_300_2_2019'

ID_LENGTH = 16

# If modifying these scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/drive']
# путь к токену для входа
TOKEN_PATH = 'program_data\\token.pickle'
# путь к регистрационным данным для логина
CREDS_PATH = 'program_data\\credentials.json'
# ID попки на Drive, куда заливаются бэкапы
BACKUP_FOLDER_ID = '1C990uxIFIZJOIS7ZhuXQWj4izeivTPB-'

# URL для скачивания xlsx файлос примерами
# слов из параллельного подкорпуса НКРЯ
CORPUS_EXAMPLES_URL = "http://processing.ruscorpora.ru/download-excel.xml?sort=i_grtagging&lex1={word}&parent1=0" \
                      "&mysize=24677638&max2=1&mysentsize=1608212&mycorp=%28lang%3A%22eng%22%7Clang_trans%3A%22eng%22" \
                      "%29&level1=0&level2=0&mode=para&env=alpha&text=lexgramm&min2=1&parent2=0&p=0&dpp=1000&spd=10" \
                      "&spp=1000&out=kwic&dl=excel"

# разделитель оригинального текста и
# перевода а корпусных примерах
ORIGINAL_TEXT_END = '%END%'