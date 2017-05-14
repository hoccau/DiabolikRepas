#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
Export Stock as pdf file
"""

from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtPrintSupport import QPrinter
import model
from pdf_utils import html_doc

def create_pdf(filename='stock.pdf', model=None):
    html = header(model) + html_stock(model)
    print(html)
    doc = html_doc(html)
    printer = QPrinter()
    printer.setOutputFileName(filename)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setPageSize(QPrinter.A4)
    doc.print_(printer)

def header(model):
    infos = model.get_infos()
    html = "<h1>Stock de " + infos['centre'] + " au "
    html += QDate.currentDate().toString('dd/MM/yyyy') + "</h1>"
    return html

def html_stock(model):
    nbr_rows = model.qt_table_reserve.rowCount()
    nbr_cols = model.qt_table_reserve.columnCount()

    html = '<table border=1>'
    for row in range(nbr_rows):
        html += '<tr>'
        for col in range(nbr_cols):
            html += '<th>'
            index = model.qt_table_reserve.index(row, col)
            value = model.qt_table_reserve.data(index, 0)
            if isinstance(value, float):
                value = round(value, 2)
            html += str(value)
            html += '</th>'
        html += '</tr>'
    html += '</table>'
    return html
    
if '__main__' == __name__:
    from PyQt5.QtWidgets import QApplication
    import sys
    m = model.Model()
    m.connect_db(sys.argv[1])
    app = QApplication(sys.argv)
    create_pdf(model=m)
