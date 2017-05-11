#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
This script exports previsionnel into one XML file
"""

import logging
from PyQt5.QtCore import QDate
from PyQt5.QtXml import QDomDocument
import pprint

class CreateXml():
    def __init__(self, model):
        self.model = model
        self.doc = QDomDocument()
        self.root = self.doc.createElement('root')
        self.doc.appendChild(self.root)
        self.first_date = self.get_first_date()

        repas = self.repas()
        for rep in repas:
            rep['plats'] = self.plats(rep['id'])
            for plat in rep['plats']:
                plat['ingrs'] = self.ingrs(plat['id'])
                logging.debug(plat['ingrs'])
                for ingr in plat['ingrs']:
                    ingr['quantité'] = self.quantities(
                        ingr['quantité'], ingr['unit_id'], rep['date'])
                    ingr['unit'] = self.get_unit_by_id(ingr['unit_id'])
                    
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(repas)
        self.create_xml_doc(repas)

    def create_xml_doc(self, repas):
        for rep in repas:
            repas_el = self.doc.createElement('repas')
            repas_el.setAttribute('type', rep['type'])
            repas_el.setAttribute('offset', rep['offset'])
            self.root.appendChild(repas_el)
            for plat in rep['plats']:
                plat_el = self.doc.createElement('plat')
                plat_el.setAttribute('nom', plat['name'])
                plat_el.setAttribute('type', plat['type'])
                repas_el.appendChild(plat_el)
                for ingr in plat['ingrs']:
                    ingr_el = self.doc.createElement('ingrédient')
                    ingr_el.setAttribute('nom', ingr['nom'])
                    quant_el = self.doc.createElement('quantité')
                    quant_el.setAttribute('unit', ingr['unit'])
                    plat_el.appendChild(ingr_el)
                    ingr_el.appendChild(quant_el)
                    for k, v in ingr['quantité'].items():
                        age_el = self.doc.createElement(k)
                        age_value = self.doc.createTextNode(str(round(v, 2)))
                        age_el.appendChild(age_value)
                        quant_el.appendChild(age_el)

    def repas(self):
        repas = []
        self.model.query.exec_("SELECT repas_prev.id, date, type_repas.type "\
            + "FROM repas_prev "\
            + "INNER JOIN type_repas ON type_id = type_repas.id")
        logging.debug(self.model.query.lastError().text())
        while self.model.query.next():
            repas.append({
                'id': self.model.query.value(0),
                'date': self.model.query.value(1),
                'offset': self.date_to_offset(self.model.query.value(1)),
                'type': self.model.query.value(2)})
        return repas

    def plats(self, repas_id):
        plats = []
        plat = {}
        self.model.query.exec_("SELECT dishes_prev.id, dishes_prev.name, repas_prev_id, "\
            + "dishes_types.type FROM dishes_prev "\
            + "INNER JOIN dishes_types ON type_id = dishes_types.id "\
            + "WHERE repas_prev_id = " + str(repas_id))
        logging.debug(self.model.query.lastError().text())
        while self.model.query.next():
            plats.append({
                'id': self.model.query.value(0),
                'name': self.model.query.value(1),
                'type': self.model.query.value(3)})
        return plats

    def ingrs(self, plat_id):
        ingrs = []
        ingr = {}
        self.model.query.exec_("SELECT products.name, products.unit_id, quantity "\
            + "FROM ingredients_prev "\
            + "INNER JOIN products ON products.id = product_id "\
            + "WHERE dishes_prev_id = " + str(plat_id))
        while self.model.query.next():
            ingrs.append({
                'nom': self.model.query.value(0),
                'unit_id': self.model.query.value(1),
                'quantité': self.model.query.value(2)})
        return ingrs

    def quantities(self, quantity, unit_id, day):
        if unit_id in [2, 3]: # for Kilogrammes and Litres
            factor = 1000
        else: # for 'piece'
            factor = 1
        self.model.query.exec_("SELECT nombre_enfants_6, nombre_enfants_6_12, "\
            + "nombre_enfants_12 FROM infos_periodes "\
            + "WHERE date_start <= '" + day + "' AND date_stop >= '" + day + "'")
        logging.debug(self.model.query.lastQuery())
        res = {}
        while self.model.query.next():
            res['age-6'] = quantity / float(self.model.query.value(0)) * factor
            res['age6-12'] = quantity / float(self.model.query.value(1)) * factor
            res['age-12'] = quantity / float(self.model.query.value(2)) * factor
            return res
    
    def date_to_offset(self, date):
        date = QDate.fromString(date, 'yyyy-MM-dd')
        return self.first_date.daysTo(date)

    def get_first_date(self):
        self.model.query.exec_("SELECT date_start FROM infos_periodes "\
            + "ORDER BY date_start LIMIT 1")
        if self.model.query.first():
            return QDate.fromString(self.model.query.value(0), 'yyyy-MM-dd')

    def get_unit_by_id(self, id_):
        if id_ == 1:
            return 'pièce'
        elif id_ == 2:
            return 'gr'
        elif id_ == 3:
            return 'ml'
    
    def write_file(self, name='xml_test.xml'):
        with open(name, 'w') as f:
            f.write(self.doc.toString())

if '__main__' == __name__:
    import model
    import sys
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    sqlmodel = model.Model()
    sqlmodel.connect_db(sys.argv[1])
    #db_to_xml(sqlmodel, sys.argv[2])
    worker = CreateXml(sqlmodel)
    #worker.repas()
    worker.write_file()
