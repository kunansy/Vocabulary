rus_alphabet = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"

FILENAME = 'content'

gfile_name = 'graph'
sheet_name = 'Graphic'

gfile_ext = 'xlsx'
dfile_ext = 'docx'
pfile_ext = 'pdf'

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
log_filename = 'Repeating of the learned words'

mods = {
    'eng_word_to_rus_defs': 1,
    'rus_def_to_eng_words': 2,
    'eng_def_to_rus_defs': 3,
    'rus_def_to_eng_defs': 4
}

unusual_combinations = ['ou', 'tre', 'nce', 'mm', 'ue', 'se']