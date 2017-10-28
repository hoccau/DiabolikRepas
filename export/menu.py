#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
Export menus as pdf file
"""

from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QPageLayout
from collections import OrderedDict
import model
from .utils import html_doc, create_infos_table

def create_pdf(filename='menu.pdf', model=None, date_start=None, date_stop=None):
    menu = get_menu_dict(model, date_start, date_stop)
    html = create_infos_table(model) + html_menu(menu)
    doc = html_doc(html)
    printer = QPrinter()
    printer.setOutputFileName(filename)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setPageSize(QPrinter.A4)
    printer.setPageOrientation(QPageLayout.Landscape)
    doc.print_(printer)

def get_menu_dict(model=None, date_start=None, date_stop=None):
    plats = model.get_plats_by_dates(date_start, date_stop)
    dates = set([plat[0] for plat in plats])
    repas_type = set([plat[1] for plat in plats])
    plats_type = set([plat[2] for plat in plats])
    plats_dict = OrderedDict()
    for date in dates:
        plats_dict[date] = OrderedDict()
        for rep_type in repas_type:
            plats_dict[date][rep_type] = OrderedDict()
            for plat_type in plats_type:
                plats_dict[date][rep_type][plat_type] = ''
    for plat in plats:
        plats_dict[plat[0]][plat[1]][plat[2]] = plat[3]
    return plats_dict

def html_menu(menu={}):
    html = "<div id='main'>\n"
    menu = OrderedDict(sorted(menu.items(), key=lambda t: t[0]))
    html += "<table border=1><tbody><tr>"
    for date, repas in menu.items():
        html += "<th><H1>" + human_date(date) + '</H1>\n'
        for rep in ['petit déjeuner', 'déjeuner', 'goûter', 'dîner', 'piquenique']:
            if rep in repas.keys():
                html += "<div class='repas'><H2>" + rep + "</H2></div>\n"
                for plat in ['entrée', 'plat', 'dessert', 'autre']:
                    if plat in repas[rep].keys():
                        html += '<p>' + repas[rep][plat] + '</p>\n'

        html += '</th>\n' #EOF date
    
    html += '</tr></tbody></table></div>' #EOF #main
    return html

def human_date(date):
    date = QDate.fromString(date, 'yyyy-MM-dd')
    return date.toString('dddd d MMMM')

if '__main__' == __name__:
    from PyQt5.QtWidgets import QApplication
    import sys
    m = model.Model()
    m.connect_db(sys.argv[1])
    app = QApplication(sys.argv)
    create_pdf(model=m, date_start='2017-05-13', date_stop='2017-05-15')
