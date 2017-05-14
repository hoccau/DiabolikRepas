#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
Export courses list as pdf file
"""

from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrinter
import model

def create_infos_table(model):
    infos = model.get_infos()
    html = '<table border="1"><tr>'
    html += '<th> Nom du directeur</th>'
    html += '<th> Lieu</th>'
    html += "<th> Enfants de moins de 6 ans</th>"
    html += "<th> Enfants entre 6 ans et 12 ans</th>"
    html += "<th> Enfants de plus de 12 ans</th>"
    html += "<th> Début du séjour</th>"
    html += "<th> Fin du séjour</th>"
    html += "</tr><tr>"
    html += "<th>"+infos['directeur_nom']+"</th>"
    html += "<th>"+infos['place']+"</th>"
    #start_date = QDate.fromString(infos['startdate'],'yyyy-MM-dd')
    #end_date = QDate.fromString(infos['enddate'],'yyyy-MM-dd')
    #html += "<th>"+start_date.toString('dd/MM/yyyy')+"</th>"
    #html += "<th>"+end_date.toString('dd/MM/yyyy')+"</th>"
    html += '</tr></table>'
    return html

def create_about():
    html = 'Généré par Diabolik Repas le <span id="date">'
    html += QDateTime.currentDateTime().toString('dd/MM/yyyy à HH:mm')
    html += '</span>'
    return html

def create_liste(products):
    html = '<table border="1"><tr>'
    html += '<th>Produit</th>'
    html += '<th>quantité</th>'
    html += '<th>unité de mesure</th>'
    html += "</tr>"
    for p in products:
        html += '<tr><th>'\
            +p[1]+'</th>'\
            +'<th>'+str(round(p[2], 2))+'</th>'\
            +'<th>'+p[3]+'</th></tr>'
    html += '</table>'
    return html

def create_pdf(filename='foo.pdf', model=None, date_start=None, date_stop=None):
    infos_centre = model.get_infos()
    products = model.get_prev_products_by_dates(date_start, date_stop)
    
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
    create_pdf(model=sqlmodel, date_start='2017-04-05', date_stop='2017-04-08')
