#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
Export courses list as pdf file
"""

import logging
from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from collections import OrderedDict
import model
from .utils import create_infos_table

def create_about():
    html = 'Généré par Diabolik Repas le <span id="date">'
    html += QDateTime.currentDateTime().toString('dd/MM/yyyy à HH:mm')
    html += '</span>'
    return html

def create_liste(products):
    fournisseurs = list(set([i[0] for i in products]))
    logging.debug('fournisseurs:' + str(fournisseurs))
    dic = OrderedDict()
    for fournisseur in fournisseurs:
        dic[fournisseur] = []
    for product in products:
        dic[product[0]].append(product[1:])
    html = ''
    for fournisseur, product in dic.items():
        html += '<h3>' + fournisseur + '</h3>'
        html += '<table border="1"><tr>'
        html += '<th>Produit</th>'
        html += '<th>quantité</th>'
        html += '<th>unité de mesure</th>'
        html += "</tr>"
        for p in product:
            html += '<tr><th>'\
            +p[0]+'</th>'\
            +'<th>'+str(round(p[1], 2))+'</th>'\
            +'<th>'+p[2]+'</th></tr>'
        html += '</table>'
    return html

def create_pdf(filename='foo.pdf', model=None, date_start=None, date_stop=None):
    infos_centre = model.get_infos()
    products = model.get_prev_products_by_dates_for_courses(
        date_start, date_stop)
    
    #create header infos
    qdate_start = QDate.fromString(date_start,'yyyy-MM-dd')
    qdate_stop = QDate.fromString(date_stop,'yyyy-MM-dd')
    infos_liste = '<H2>Produit nécessaires aux repas compris entre le '
    infos_liste += qdate_start.toString('dd/MM/yyyy') + ' et le '
    infos_liste += qdate_stop.toString('dd/MM/yyyy') + ' (inclus).</H2>'

    liste = create_liste(products)
    doc = QTextDocument()
    title = '<h1>Liste des courses du séjour '+infos_centre['centre']+'</h1>'
    about = '<div id="about">'+create_about()+'</div>'
    logo = '<img src="design/logo.png" align="right"/>'
    infos = '<div id="infos">'+create_infos_table(model)+'</div>'
    html = '<body>' + logo + title + about + infos + infos_liste + liste\
        +'</body>'
    doc.setHtml(html)
    printer = QPrinter()
    printer.setOutputFileName(filename)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setPageSize(QPrinter.A4)
    doc.print_(printer)

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    sqlmodel = model.Model()
    sqlmodel.connect_db(sys.argv[1])
    app = QApplication(sys.argv)
    create_pdf(model=sqlmodel, date_start='2017-05-24', date_stop='2017-05-25')
