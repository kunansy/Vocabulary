RUS_ALPHABET = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

DATA = 'user_data\\content'

SHEET_NAME = 'Graphic'

TABLE_EXT = 'xlsx'
DOC_EXT = 'docx'
PDF_EXT = 'pdf'
DB_EXT = 'db'

DOC_FOLDER = 'user_data\\docx'
TABLE_FOLDER = 'user_data\\xlsx'
PDF_FOLDER = 'user_data\\pdf'

DATEFORMAT = "%d.%m.%Y"

# разделить при выводе WordsPerDay
DIVIDER = '_' * 50

# отступ в поиске при нескольких айтемах из одного дня
S_TAB = '\n\t\t\t'

MAIN_WINDOW_PATH = 'program_data\\ui\\MainWindow.ui'
ALERT_WINDOW_PATH = 'program_data\\ui\\AlertWindow.ui'
MESSAGE_WINDOW_PATH = 'program_data\\ui\\MessageWindow.ui'
SHOW_WINDOW_PATH = 'program_data\\ui\\ShowWindow.ui'
REPEAT_LOG_FILENAME = 'user_data\\repeating_log.json'

REPEATING_MODS = {
    'eng_word_to_rus_defs': 1,
    'rus_def_to_eng_words': 2,
    'eng_def_to_rus_defs': 3,
    'rus_def_to_eng_defs': 4
}

UNUSUAL_COMBINATIONS = ['ou', 'tre', 'nce', 'mm', 'ue', 'se']

SYNONYMS_SEARCH_URL = "https://rusvectores.org/{model}/{word}/api/json/"
SYNONYMS_SEARCH_MODEL = 'tayga_upos_skipgram_300_2_2019'
# похоже, это чудо даёт рифмовки
# 'araneum_none_fasttextcbow_300_5_2018'

ID_LENGTH = 16

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_PATH = 'program_data\\token.pickle'
CREDENTIALS_PATH = 'program_data\\credentials.json'
FOLDER_ID = '1C990uxIFIZJOIS7ZhuXQWj4izeivTPB-'