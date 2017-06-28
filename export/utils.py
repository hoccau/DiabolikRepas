#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
Functions for pdf exports
"""

from PyQt5.QtGui import QTextDocument
import os

def html_doc(html_content):
    doc = QTextDocument()
    module_directory, filename = os.path.split(__file__)
    css_file = os.path.join(module_directory, 'style.css')
    with open(css_file, 'r') as f:
        style = f.read()
    html = "<head><style>" + style + "</style></head>"
    html += "<body>" + html_content + '</body>'
    doc.setHtml(html)
    return doc

def create_infos_table(model):
    infos = model.get_infos()
    html = '<table border="1"><tr>'
    html += '<th> Séjour</th>'
    html += '<th> Directeur</th>'
    html += '<th> Lieu</th>'
    html += "<th> Début du séjour</th>"
    html += "<th> Fin du séjour</th>"
    html += "</tr><tr>"
    html += "<th>"+infos['centre']+"</th>"
    html += "<th>"+infos['directeur_nom']+"</th>"
    html += "<th>"+infos['place']+"</th>"
    html += "<th>"+infos['date_start']+"</th>"
    html += "<th>"+infos['date_stop']+"</th>"
    html += '</tr></table>'
    return html
