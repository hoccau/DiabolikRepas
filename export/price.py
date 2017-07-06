#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
Export "prix de journée" as pdf file
"""

from PyQt5.QtCore import QDateTime, QDate
from PyQt5.QtPrintSupport import QPrinter
import model
from .utils import html_doc, create_infos_table
import logging

def create_pdf(filename='prix.pdf', model=None, date='2017-05-16'):
    """ 
    Return (False, "ErrorName") if it is not possible to calculate price. If  
    PDF is correctly exported, return (True, '')
    """
    res = html_price(model, date)
    if not res[0]:
        logging.warning(res[1])
        return res
    html = header(model) + html_price(model, date)
    print(html)
    doc = html_doc(html)
    printer = QPrinter()
    printer.setOutputFileName(filename)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setPageSize(QPrinter.A4)
    doc.print_(printer)
    return (True, '')

def header(model):
    infos = model.get_infos()
    html = "<h1>Prix de journée de " + infos['centre'] + " au "
    html += QDate.currentDate().toString('dd/MM/yyyy') + "</h1>"
    return html

def html_price(model, date):
    avg_prices = model.get_all_avg_prices() # {id: [name, avg(price)]}
    # below: product_id, product.name, quantity, repas_id, repas.type_id
    outputs = model.get_all_outputs_by_date(date)
    logging.debug(avg_prices)
    logging.debug(outputs)
    m = model.qt_table_periodes_infos
    if m.rowCount() < 1:
        return False, "Pas de periode définie."
    enfants = False
    for row in range(m.rowCount()):
        date_start, date_stop = m.data(m.index(row, 1)), m.data(m.index(row, 2))
        if date >= date_start and date <= date_stop:
            enfants = [m.data(m.index(row, i)) for i in range(3, 6)]
            logging.debug(enfants)
            break
    if not enfants:
        return False, "Pas d'enfants sur la période demandée"
    repas_type = {1:'petit déjeuner',
            2:'déjeuner',
            3:'dîner',
            4:'souper',
            5:'picnique',
            6:'autre'}
    
    html = '<table border=1>'
    html += '<tr>'
    html += '<th> <h3>Repas</h3> </th>'
    html += '<th> Ingredient </th>'
    html += '<th> Quantité </th>'
    html += '<th> Prix Unitaire Moyen </th>'
    html += '<th> Prix moyen total</th>'
    html += '</tr>'
    total_day = 0
    for output in outputs:
        html += '<tr>'
        html += '<th>' + repas_type[output[4]] + '</th>'
        html += '<th>' + output[1] + '</th>'
        html += '<th>' + str(output[2]) + '</th>'
        try:
            html += '<th>' + str(avg_prices[output[0]]) + '</th>'
        except KeyError:
            logging.warning("Erreur: un produit n'a pas été entré")
            return False, "Un produit n'a pas été entré en arrivage de denrées"
        total_price = avg_prices[output[0]] * output[2]
        total_day += total_price
        html += '<th>' + str(round(total_price, 2)) + '</th>'
        html += '</tr>'
    html += '</table>'
    html += '<h2>Résultats</h2>'
    html += '<table border=0><tr>'
    html += '<th><H3>Prix total</H3></th>'
    html += "<th><H3>Nombre de personnes</H3></th>"
    html += '<th><H3>Prix par personne</H3></th>'
    html += '</tr><tr>'
    html +=  '<th>' + str(total_day) + '</th>'
    html +=  '<th>' + str(round(sum(enfants), 2)) + '</th>'
    if sum(enfants) > 0:
        html +=  '<th>' + str(round(total_day / sum(enfants), 2)) + '</th>'
    html += '</tr></table>'

    return html
    
if '__main__' == __name__:
    from PyQt5.QtWidgets import QApplication
    import sys
    m = model.Model()
    m.connect_db(sys.argv[1])
    app = QApplication(sys.argv)
    create_pdf(model=m)
