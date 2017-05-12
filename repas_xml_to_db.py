#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
This script parse the "previsionnel repas" xml files to add it in database. 
database must have a start date and correct number of children to adapt 
ingredients quantity.
"""

from PyQt5.QtCore import QUrl, QFile, QIODevice, QDate
from PyQt5.QtXml import QDomDocument, QXmlInputSource
from PyQt5.QtXmlPatterns import QXmlSchema, QXmlSchemaValidator 
import logging
        
class Repas():
    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.dom = QDomDocument()

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
            with open(self.xml_file, 'r', encoding='utf-8') as f:
                xml = f.read()
            w = self.dom.setContent(xml)
            logging.debug(w)

    def repas_prev_to_db(self, repas, date_start):
        logging.info('repas: '+repas.attribute('type'))
        self.query.prepare('INSERT INTO repas_prev(date, type_id) VALUES\
        (:date, (SELECT id FROM type_repas WHERE type= :type))')
        self.query.bindValue(':date', date_start)
        self.query.bindValue(':type', repas.attribute('type'))
        s = self.query.exec_()
        if self.query.lastError().text().rstrip(' '):
            logging.info(self.query.executedQuery())
            logging.warning(self.query.lastError().text())

    def plat_prev_to_db(self, plat_name, plat_type, repas_id):
        self.query.exec_(
        "SELECT id FROM dishes_types WHERE type='"+plat_type+"'")
        if self.query.first():
            plat_type_id = self.query.value(0)
        self.query.prepare(
            'INSERT INTO dishes_prev(name, repas_prev_id, type_id)\
            VALUES (:name, :repas_prev_id, :type_id)')
        self.query.bindValue(':name', plat_name)
        self.query.bindValue(':repas_prev_id', repas_id)
        self.query.bindValue(':type_id', plat_type_id)
        self.query.exec_()

    def ingr_prev_to_db(self, ingr, quantities, periode, plat_id):
        quantities_array = []
        unit = quantities.toElement().attribute('unit')
        logging.info('ingr: '+ str(ingr)+ ' unit:' + str(unit))
        quantities_array.append(quantities.firstChildElement('age-6'))
        quantities_array.append(quantities.firstChildElement('age6-12'))
        quantities_array.append(quantities.firstChildElement('age12'))
        quantities_array = [float(el.text()) for el in quantities_array]
        if unit in ['gr','ml']:
            quantities_array = [i / 1000. for i in quantities_array]
            if unit == 'gr':
                unit_id = 2
            if unit == 'ml':
                unit_id = 3
        elif unit == 'pièce':
            unit_id = 1
        quantities_array[0] *= periode['nombre_enfants_6']
        quantities_array[1] *= periode['nombre_enfants_6_12']
        quantities_array[2] *= periode['nombre_enfants_12']
        total_quantity = sum(quantities_array)
    
        product_id = self._get_product_id(ingr)
        if not product_id:
            self.query.prepare(
                'INSERT INTO products(name, unit_id, '\
                + 'recommended_6, recommended_6_12, recommended_12) '\
                + 'VALUES (:name, :unit_id, :r_6, :r_6_12, :r_12)')
            self.query.bindValue(':name', ingr)
            self.query.bindValue(':unit_id', unit_id)
            self.query.bindValue(':r_6', quantities_array[0])
            self.query.bindValue(':r_6_12', quantities_array[1])
            self.query.bindValue(':r_12', quantities_array[2])
            res = self.query.exec_()
            if not res:
                logging.warning(self.query.lastError())
            product_id = self._get_product_id(ingr)
        self.query.prepare('INSERT INTO ingredients_prev\
        (product_id, dishes_prev_id, quantity)\
        VALUES(:product_id, :dishes_prev_id, :quantity)')
        self.query.bindValue(':product_id', product_id)
        self.query.bindValue(':dishes_prev_id', plat_id)
        self.query.bindValue(':quantity', total_quantity)
        s = self.query.exec_()
        if not s:
            logging.info(self.query.executedQuery())
            logging.warning(self.query.lastError().text())

    def xml_to_db(self, model=None):
        self.query = model.query
        periodes = self._get_periodes()
        if not periodes:
            logging.warning('Pas de periodes.')
            return False
        else:
            self._set_dom()

        # repas
        repas_list = self.dom.elementsByTagName('repas')
        for i in range(repas_list.length()):
            repas = repas_list.at(i).toElement()
            offset = int(repas.attribute('offset'))
            day = periodes[0]['date_start'].addDays(offset)
            periode = self._get_periode_for_date(day, periodes)
            # If offset value is out of range for periods, we set the last
            if not periode:
                periode = periodes[-1]
            self.repas_prev_to_db(repas, day)

            # plats
            repas_id = self._get_last_id()
            plats = repas.elementsByTagName('plat')
            for i in range(plats.length()):
                plat_type = plats.at(i).toElement().attribute('type')
                plat_name = plats.at(i).toElement().attribute('nom')
                self.plat_prev_to_db(plat_name, plat_type, repas_id)

                # ingredients
                plat_id = self._get_last_id()
                ingrs = plats.at(i).toElement().elementsByTagName('ingrédient')
                for i in range(ingrs.length()):
                    ingr = ingrs.at(i).toElement().attribute('nom')
                    ingr = ingr.lower()
                    quantities = ingrs.at(i).firstChildElement('quantité')
                    self.ingr_prev_to_db(ingr, quantities, periode, plat_id)

    def _get_product_id(self, name):
        self.query.prepare("SELECT id FROM products WHERE name = :name")
        self.query.bindValue(':name', name)
        self.query.exec_()
        if self.query.first():
             product_id = self.query.value(0)
             return product_id
        else:
            logging.warning(self.query.lastError().text())
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

    def _get_periodes(self):
        periodes = []
        q = self.query.exec_(
            "SELECT date_start, date_stop, nombre_enfants_6,"\
            + " nombre_enfants_6_12, nombre_enfants_12 "\
            + "FROM infos_periodes")
        while self.query.next():
            periode = {}
            periode['date_start'] = QDate.fromString(
                self.query.value(0), 'yyyy-MM-dd')
            periode['date_stop'] = QDate.fromString(
                self.query.value(1), 'yyyy-MM-dd')
            periode['nombre_enfants_6'] = self.query.value(2)
            periode['nombre_enfants_6_12'] = self.query.value(3)
            periode['nombre_enfants_12'] = self.query.value(4)
            periodes.append(periode)
        if q:
            return periodes
        else:
            logging.warning(self.query.lastQuery())
            logging.warning(self.query.lastError().text())
            return False

    def _get_last_id(self):
        self.query.exec_('SELECT last_insert_rowid()')
        if self.query.first():
            return self.query.value(0)

    def _get_periode_for_date(self, date, periodes):
        for periode in periodes:
            if periode['date_start'] <= date and date <= periode['date_stop']:
                return periode

if '__main__' == __name__:
    import sys
    import model
    import os
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(
        logging.Formatter('%(levelname)s::%(module)s:%(lineno)d :: %(message)s'))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)
    sqlmodel = model.Model()
    sqlmodel.connect_db(sys.argv[2])
    if os.path.isdir(sys.argv[1]):
        repas_files = os.listdir(sys.argv[1])
        for repas_file in repas_files:
            repas = Repas(os.path.join(sys.argv[1], repas_file))
            repas.xml_to_db(model=sqlmodel)
    else:
        repas = Repas(sys.argv[1])
        repas.xml_to_db(model=sqlmodel)
