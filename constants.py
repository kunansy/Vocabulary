RUS_ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

DATA = 'content'

SHEET_NAME = 'Graphic'

TABLE_EXT = 'xlsx'
DOC_EXT = 'docx'
PDF_EXT = 'pdf'
DB_EXT = 'db'

DOC_FOLDER = 'docx'
TABLE_FOLDER = 'xlsx'
PDF_FOLDER = 'pdf'

DATEFORMAT = "%d.%m.%Y"

# разделить при выводе WordsPerDay
DIVIDER = '_' * 50

# отступ в поиске при нескольких айтемах из одного дня
S_TAB = '\n\t\t\t'

MAIN_WINDOW_PATH = 'ui\\MainWindow.ui'
ALERT_WINDOW_PATH = 'ui\\AlertWindow.ui'
MESSAGE_WINDOW_PATH = 'ui\\MessageWindow.ui'
SHOW_WINDOW_PATH = 'ui\\ShowWindow.ui'
REPEAT_LOG_FILENAME = 'repeating_log.json'

REPEATING_MODS = {
    'eng_word_to_rus_defs': 1,
    'rus_def_to_eng_words': 2,
    'eng_def_to_rus_defs': 3,
    'rus_def_to_eng_defs': 4
}

UNUSUAL_COMBINATIONS = ['ou', 'tre', 'nce', 'mm', 'ue', 'se']

SYNONYMS_SEARCH_URL = "https://rusvectores.org/{model}/{word}/api/json/"
SYNONYMS_SEARCH_MODEL = 'tayga_upos_skipgram_300_2_2019'

ID_LENGTH = 16

# похоже, это чудо даёт рифмовки
# 'araneum_none_fasttextcbow_300_5_2018'