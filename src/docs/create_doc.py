__all__ = [
    'create_pdf', 'visual_info', 'create_docx'
]

import os

import docx
import xlsxwriter
import comtypes.client
from docx.shared import Pt
from typing import List, Dict

from src.main.common_funcs import (
    today, add_ext, file_exist
)
from src.main.constants import (
    DOC_FOLDER, PDF_FOLDER, DATEFORMAT
)
from src.trouble.trouble import Trouble


def create_docx(f_name: str,
                _content: List,
                _header='General') -> None:
    """
    Создать docx файл с контентом (strable), если файл с таким
    именем уже существует – не создавать новый;

    Пронумерует строки, у первого символа строки подниматеся регистр;
    Шрифт 'Avenir Next Cyr', 16 размер

    :param f_name: имя файла
    :param _content: список объектов, которые можно преобразовать к str
    :param _header: заголовок документа, 'General' по умолчанию
    """
    _trbl = Trouble(create_docx)
    assert isinstance(_content, list) and _content, \
        _trbl(_content, _p='w_list')
    assert hasattr(_content[0], "__str__"), \
        _trbl("Content must be strable")
    assert isinstance(_header, str) and _header, \
        _trbl(_header, _p='w_str')

    f_name = add_ext(f_name, 'docx')

    if file_exist(f"{DOC_FOLDER}\\{f_name}"):
        print(f"Document, named '{f_name}', still exist")
        return

    _docx = docx.Document()

    # Шрифт и его параметры
    doc_style = _docx.styles['Normal']
    _font = doc_style.font
    _font.name = 'Avenir Next Cyr'
    _font.size = Pt(16)

    # добавляем заглавие
    _docx.add_heading(f"{_header}", 0)

    for num, word in enumerate(_content, 1):
        new_paragraph = _docx.add_paragraph()
        new_paragraph.style = doc_style

        new_paragraph.add_run(f"{num}. ").bold = True
        word = str(word)
        new_paragraph.add_run(f"{word[0].upper()}{word[1:]}")

    _docx.save(f"{DOC_FOLDER}\\{f_name}")


def create_pdf(f_name: str,
               _content: List) -> None:
    """
    Создать pdf-файл через docx-посредника;
    если файл с таким именем уже существует – не создавать новый;

    :param f_name: имя файла
    :param _content: список объектов, которые можно преобразовать к строкам
    """
    _trbl = Trouble(create_pdf)
    assert isinstance(_content, list) and _content, \
        _trbl(_content, _p='w_list')
    assert isinstance(f_name, str) and f_name, \
        _trbl(f_name, _p='w_str')

    f_name = add_ext(f_name, 'pdf')

    if file_exist(f"{PDF_FOLDER}\\{f_name}"):
        print(f"PDF-file named '{f_name}' still exist")
        return
    # файл-посредник
    _med = f"temp_{len(_content)}_{today(DATEFORMAT)}.docx"
    create_docx(_med, _content)

    word_client = comtypes.client.CreateObject('Word.Application')
    _med = word_client.Documents.Open(f"{os.getcwd()}\\{DOC_FOLDER}\\{_med}")
    _med.SaveAs(f"{os.getcwd()}\\{PDF_FOLDER}\\{f_name}", FileFormat=17)

    _med.Close()
    word_client.Quit()

    # удалить временный файл
    os.system(f'del "{os.getcwd()}\\{DOC_FOLDER}\\{f_name}"')


def visual_info(f_name: str,
                _content: Dict,
                **kwargs) -> None:
    """
    Создать Excel файл с графиком: по оси x – ключи,
    по y – их значения словаря _content
    Ключи – произвольные типы, значения – числа целые
    или вещественные

    Именнованные параметры:
    имя параметра – что это; значение по умолчанию
    sheet_name – имя листа; 'Graphic'
    chart_type – тип графика: line, area, bar, column; 'line'
    chart_title – заглавие графика; 'Title'
    font_name – имя шрифта; 'Avenir Next Cyr'
    x_axis_name – имя значения по оси х; 'Keys'
    y_axis_name – имя значений по оси y; 'Values'
    wb_title – заглавие документа; 'Title'
    author – автор документа; 'Author'
    total – добавлять ли в конце сумму всех значений; True

    :param _content: словарь из пар значение
    :param f_name: имя файла
    """
    _trbl = Trouble(visual_info)

    assert isinstance(_content, dict) and _content, \
        _trbl(_content, _p='w_dict')
    assert all(isinstance(i, (int, float)) for i in _content.values()), \
        _trbl("Wrong keys", "int or float")
    assert isinstance(f_name, str) and f_name, \
        _trbl(f_name, _p='w_str')
    if file_exist(f_name, 'xlsx'):
        return

    sheet_name = kwargs.pop('sheet_name', 'Graphic')
    chart_type = kwargs.pop('chart_type', 'line')
    chart_title = kwargs.pop('chart_title', 'Title')
    _font = kwargs.pop('font_name', "Avenir Next Cyr")
    x_axis_name = kwargs.pop('x_axis_name', 'Keys')
    y_axis_name = kwargs.pop('y_axis_name', 'Values')
    wb_title = kwargs.pop('wb_title', 'Title')
    _author = kwargs.pop('author', 'Author')
    # TODO: 'xlsx' и фолдер
    _wb = xlsxwriter.Workbook(f_name)
    _wb.set_properties({
        'title': wb_title,
        'author': _author,
        'comments': "Created with Python and XlsxWriter"
    })

    cell_format = _wb.add_format({
        'size': 16,
        'font': _font,
        'align': "vcenter"
    })

    _wsh = _wb.add_worksheet(sheet_name)
    _wsh.set_column('A:A', 17)

    enum_cont = [(num, (key, val)) for num, (key, val) in
                 enumerate(_content.items())]
    for row, (key, val) in enum_cont:
        if not isinstance(val, (int, float)):
            _nums = False
        _wsh.write(row, 0, str(key), cell_format)
        _wsh.write(row, 1, val, cell_format)

    row += 1

    _wsh.write(row, 0, "Total:", cell_format)
    _wsh.write(row, 1, f"=SUM(B1:B{row})", cell_format)

    _chart = _wb.add_chart({
        'type': chart_type
    })

    _chart.set_title({
        'name': chart_title,
        'name_font': {
            'name': _font,
            'color': "black",
            'size': 16
        },
    })

    _chart.add_series({
        'values': f"={sheet_name}!B1:B{row}",
        'categories': f"={sheet_name}!A1:A{row}",
        'line': {
            'color': "orange"
        },
    })

    _chart.set_legend({
        'none': True
    })

    _chart.set_x_axis({
        'name': x_axis_name,
        'name_font': {
            'name': _font,
            'italic': True,
            'size': 16
        },
        'num_font': {
                'name': _font,
                'italic': True,
                'size': 14
            }
    })
    _chart.set_y_axis({
        'name': y_axis_name,
        'name_font': {
            'name': _font,
            'italic': True,
            'size': 16
        },
        'num_font': {
            'name': _font,
            'italic': True,
            'bold': True,
            'size': 14
         }
    })

    _chart.set_size({
        'width': 1280,
        'height': 520
    })

    _wsh.insert_chart('C1', _chart)

    _wb.close()