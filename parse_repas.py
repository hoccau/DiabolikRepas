#!/usr/bin/python3

"""
This script parse the repas xml files
"""

from PyQt5.QtCore import QUrl, QFile, QIODevice
from PyQt5.QtXmlPatterns import QXmlSchema, QXmlSchemaValidator

schema_file = QFile('repas.xsd')
schema_file.open(QIODevice.ReadOnly)

schema = QXmlSchema()
schema.load(schema_file, QUrl.fromLocalFile(schema_file.fileName()))

def xml_is_valid(xml_file_name):
    xml_file = QFile(xml_file_name)
    xml_file.open(QIODevice.ReadOnly)
    validator = QXmlSchemaValidator(schema)
    return validator.validate(xml_file, QUrl.fromLocalFile(xml_file.fileName()))

if '__main__' == __name__:
    import sys
    if schema.isValid():
        print(xml_is_valid(sys.argv[1]))
