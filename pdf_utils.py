#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
Functions to export pdf file with QT
"""

from PyQt5.QtGui import QTextDocument

def html_doc(html_content, style_file=None):
    doc = QTextDocument()
    if style_file:
        with open(style_file, 'r') as f:
            style = f.read()
            print(style)
    else:
        style = 'th{padding-left:10; padding-right:10;}'
    html = "<head><style>" + style + "</style></head>"
    html += "<body>" + html_content + '</body>'
    doc.setHtml(html)
    return doc
