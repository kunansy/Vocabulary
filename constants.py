rus_alphabet = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

FILENAME = 'content'

gfile_name = 'graph'
sheet_name = 'Graphic'

table_file_ext = 'xlsx'
doc_file_ext = 'docx'
pdf_file_ext = 'pdf'
db_file_ext = 'db'

docx_folder = 'docx'
xlsx_folder = 'xlsx'
pdf_folder = 'pdf'

DATEFORMAT = "%d.%m.%Y"

# разделить при выводе WordsPerDay
divider = '_' * 50

# отступ в поиске при нескольких айтемах из одного дня
s_tab = '\n\t\t\t'

MainRepeatWindow = 'ui\\MainWindow.ui'
AlertWindow = 'ui\\AlertWindow.ui'
MessageWindow = 'ui\\MessageWindow.ui'
ShowWindow = 'ui\\ShowWindow.ui'
log_filename = 'Repeating_of_the_learned_words'

mods = {
    'eng_word_to_rus_defs': 1,
    'rus_def_to_eng_words': 2,
    'eng_def_to_rus_defs': 3,
    'rus_def_to_eng_defs': 4
}

unusual_combinations = ['ou', 'tre', 'nce', 'mm', 'ue', 'se']