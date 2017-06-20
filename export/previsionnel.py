#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
Export Previsionnel for chef as pdf file
"""

from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtPrintSupport import QPrinter
import model
from .utils import html_doc, create_infos_table
from collections import OrderedDict

def create_pdf(filename='previsionnel.pdf', model=None):
    html = header(model) + create_infos_table(model) + html_stock(model)
    doc = html_doc(html)
    printer = QPrinter()
    printer.setOutputFileName(filename)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setPageSize(QPrinter.A4)
    doc.print_(printer)

def header(model):
    infos = model.get_infos()
    html = "<h1>Prévisionnel de " + infos['centre'] + "</h1>"
    return html

def html_stock(model):
    nbr_rows = model.qt_table_reserve.rowCount()
    nbr_cols = model.qt_table_reserve.columnCount()
    datas = model.get_prev_products_for_export()
    dates = sorted(list(set([i[0] for i in datas])))
    dic = OrderedDict()
    for date in dates:
        dic[date] = OrderedDict([
            ('petit déjeuner',[]),
            ('déjeuner',[]),
            ('goûter',[]),
            ('dîner',[]),
            ('piquenique',[]),
            ('autre',[])])
    for data in datas:
        dic[data[0]][data[1]].append(data[2:])
    html = ''
    for date, repas in dic.items():
        date = QDate().fromString(date, 'yyyy-MM-dd')
        html += '<H2> '+ date.toString('dddd d MMMM yyyy') + '</H2>'
        for rep, table in repas.items():
            if table:
                name = ' : ' + table[0][0]
                html += '<h3>' + rep + name + '</h3>'
                html += '<table border=1>'
                for row in table:
                    html += '<tr>'
                    for cell in row[1:]:
                        html += '<th>' + str(cell) + '</th>'
                    html += '</tr>'
                html += '</table>'
    return html
    
if '__main__' == __name__:
    from PyQt5.QtWidgets import QApplication
    import sys
    model = model.Model()
    model.connect_db(sys.argv[1])
    app = QApplication(sys.argv)
    create_pdf(model=model)
