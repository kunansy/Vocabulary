__all__ = (
    'TABLE_FOLDER', 'DOC_FOLDER', 'PDF_FOLDER',
    'ID_LENGTH', 'DATEFORMAT', 'RESTORE_FOLDER_PATH',
    'ENG_PREPS', 'RUS_REPEAT_MODS', 'ENG_REPEAT_MODS',
    'VOCABULARY_DB_PATH', 'REPEAT_LOG_PATH', 'IRREGULAR_VERBS_PATH',
    'MESSAGE_WINDOW_PATH', 'EXAMPLES_WINDOW_PATH', 'MAIN_WINDOW_PATH',
    'SHOW_WINDOW_PATH'
)

from configparser import ConfigParser
from pathlib import Path

# absolute paths needed to test (otherwise it does not work)
DATA_BASE_PATH = Path('/home/kirill/Python/PythonProjects/Vocabulary/data')

USER_DATA_PATH = DATA_BASE_PATH / 'user_data'
PROGRAM_DATA_PATH = DATA_BASE_PATH / 'program_data'
UI_BASE_PATH = Path('/home/kirill/Python/PythonProjects/Vocabulary/src/repeat/ui')

# name of vocabulary base
VOCABULARY_DB_PATH = 'Vocabulary.db'
# name of repeat log
REPEAT_LOG_PATH = 'repeat_log.json'
# name of irregular verbs base
IRREGULAR_VERBS_PATH = USER_DATA_PATH / 'Irregular_verbs.txt'

# Word-docs path
DOC_FOLDER = USER_DATA_PATH / 'docx'
# Excel-docs path
TABLE_FOLDER = USER_DATA_PATH / 'xlsx'
# PDF-docs path
PDF_FOLDER = USER_DATA_PATH / 'pdf'
# restore files path
RESTORE_FOLDER_PATH = USER_DATA_PATH / 'restore'

# standard date output format
DATEFORMAT = '%d.%m.%Y'

# path to GUI of repeat module
MAIN_WINDOW_PATH = UI_BASE_PATH / 'MainWindow.ui'
EXAMPLES_WINDOW_PATH = UI_BASE_PATH / 'ExamplesWindow.ui'
MESSAGE_WINDOW_PATH = UI_BASE_PATH / 'MessageWindow.ui'
SHOW_WINDOW_PATH = UI_BASE_PATH / 'ShowWindow.ui'

# repeating mods for eng
ENG_REPEAT_MODS = {
    'original_word_to_native_defs': 1,
    'native_def_to_original_words': 2,
    'original_def_to_native_defs': 3,
    'native_def_to_original_defs': 4
}

# repeating mods for rus
RUS_REPEAT_MODS = {
    'word_to_defs': 1,
    'defs_to_word': 2
}

ID_LENGTH = 16

# English prepositions
ENG_PREPS = [
    'of', 'by', 'with', 'in', 'on', 'for', 'at', 'per', 'as',
    'about', 'into', 'from', 'under', 'over', 'around', 'towards'
]

# _ini = ConfigParser()
# _ini.read('D:\\Python\\Projects\\Vocabulary\\INIT.ini')


# __LANGUAGE__ = _ini['settings']['__LANGUAGE__']
# __NATIVE__ = _ini['settings']['__NATIVE__']

VOCABULARY_DB_PATH = USER_DATA_PATH / f"en_{VOCABULARY_DB_PATH}"
REPEAT_LOG_PATH = USER_DATA_PATH / f"en_{REPEAT_LOG_PATH}"
