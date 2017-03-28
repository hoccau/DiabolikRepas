#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
This script parse the repas xml files
"""

from PyQt5.QtCore import QUrl, QFile, QIODevice, QDate
from PyQt5.QtXml import QDomDocument, QXmlInputSource
from PyQt5.QtXmlPatterns import QXmlSchema, QXmlSchemaValidator 
from PyQt5.QtSql import QSqlQuery
        
class Repas():
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.dom = QDomDocument()
        self.query = QSqlQuery()

    def xml_is_valid(self):
        schema_file = QFile('repas.xsd')
        schema_file.open(QIODevice.ReadOnly)
        schema = QXmlSchema()
        schema.load(schema_file, QUrl.fromLocalFile(schema_file.fileName()))

        if schema.isValid():
            xml_file = QFile(self.xml_file)
            xml_file.open(QIODevice.ReadOnly)
            validator = QXmlSchemaValidator(schema)
            valid = validator.validate(
                xml_file, QUrl.fromLocalFile(xml_file.fileName()))
        xml_file.close()
        schema_file.close()
        return valid

    def _set_dom(self):
        if self.xml_is_valid():
            with open(self.xml_file) as f:
                xml = f.read()
            w = self.dom.setContent(xml)
            print(w)

    def xml_to_db(self, model=None, day_start= None):
        self.query = model.query
        range_age = self._get_nbr_children()
        if not range_age:
            print('Ages non entrés')
            return False
        self._set_dom()
        repas_list = self.dom.elementsByTagName('repas')
        for i in range(repas_list.length()):
            repas = repas_list.at(i).toElement()
            self.query.prepare('INSERT INTO repas_prev(name, date, type_id) VALUES\
            (:name, :date, (SELECT id FROM type_repas WHERE type= :type))')
            self.query.bindValue(':name', repas.attribute('nom'))
            offset = int(repas.attribute('offset'))
            day = day_start.addDays(offset)
            self.query.bindValue(':date', day_start.addDays(offset))
            self.query.bindValue(':type', repas.attribute('type'))
            s = self.query.exec_()
            print(self.query.executedQuery(), s, self.query.lastError().text())
            self.query.exec_('SELECT last_insert_rowid()')
            if self.query.first():
                repas_id = self.query.value(0)
            plats = repas.elementsByTagName('plat')
            for i in range(plats.length()):
                ingrs = plats.at(i).toElement().elementsByTagName('ingrédient')
                for i in range(ingrs.length()):
                    quantities = []
                    ingr = ingrs.at(i).toElement().attribute('nom')
                    print('ingr', ingr)
                    q = ingrs.at(i).firstChildElement('quantité')
                    unit = q.toElement().attribute('unit')
                    print('unit:', unit)
                    quantities.append(q.firstChildElement('age-6'))
                    quantities.append(q.firstChildElement('age6-12'))
                    quantities.append(q.firstChildElement('age12'))
                    quantities = [float(el.text()) for el in quantities]
                    print('aft:',quantities)
                    if unit in ['gr','ml']:
                        quantities = [i / 1000. for i in quantities]
                        if unit == 'gr':
                            unit_id = 2
                        if unit == 'ml':
                            unit_id = 3
                    elif unit == 'pièce':
                        unit_id = 1
                    quantities[0] *= range_age['6']
                    quantities[1] *= range_age['6-12']
                    quantities[2] *= range_age['12']
                    total_quantity = sum(quantities)
                
                    product_id = self._get_product_id(ingr)
                    if not product_id:
                        self.query.prepare('INSERT INTO products(name) VALUES (:name)')
                        self.query.bindValue(':name', ingr)
                        self.query.exec_()
                        product_id = self._get_product_id(ingr)
                    self.query.prepare('INSERT INTO ingredient_prev\
                    (product_id, repas_prev_id, quantity, unit_id)\
                    VALUES(:product_id, :repas_prev_id, :quantity, :unit_id)')
                    self.query.bindValue(':product_id', product_id)
                    self.query.bindValue(':repas_prev_id', repas_id)
                    self.query.bindValue(':quantity', total_quantity)
                    self.query.bindValue(':unit_id', unit_id)
                    self.query.exec_()

    def _get_product_id(self, name):
        self.query.prepare("SELECT id FROM products WHERE name = :name")
        self.query.bindValue(':name', name)
        self.query.exec_()
        if self.query.first():
             product_id = self.query.value(0)
             return product_id
        else:
            print(self.query.lastError().text())
            return False

    def _get_nbr_children(self):
        result = {}
        self.query.exec_(
            'SELECT nombre_enfants_6, nombre_enfants_6_12, nombre_enfants_12\
            FROM infos')
        if self.query.first():
            result['6'] = self.query.value(0)
            result['6-12'] = self.query.value(1)
            result['12'] = self.query.value(2)
            return result
        else:
            return False

if '__main__' == __name__:
    import sys
    import model
    sqlmodel = model.Model()
    sqlmodel.connect_db(sys.argv[2])
    repas = Repas(sys.argv[1])
    repas.xml_to_db(model=sqlmodel, day_start = QDate.currentDate())
