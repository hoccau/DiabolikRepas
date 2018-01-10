#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
This script exports previsionnel into one XML file
"""

import logging
from PyQt5.QtCore import QDate
from PyQt5.QtXml import QDomDocument

class CreateXml():
    def __init__(self, model):
        self.model = model
        self.doc = QDomDocument()
        self.root = self.doc.createElement('root')
        self.doc.appendChild(self.root)
        self.first_date = self.get_first_date()

        self.model.exec_("SELECT * FROM xml_export")
        datas = self.model._query_to_lists(16)
        self.create_xml_doc(datas)
                    
    def create_xml_doc(self, datas):
        repas = {}
        plats = {}
        ingrs = {}
        for data in datas:
            (
                repas_id, date, repas_type,
                plat_id, plat_name, plat_type,
                ingr_id, product_name, recommends_6,
                recommends6_12, recommends_12, quantity, unit, nbr_6,
                nbr_6_12, nbr_12) = data
            
            if repas_id not in list(repas.keys()):
                repas[repas_id] = self.doc.createElement('repas')
            repas[repas_id].setAttribute('type', repas_type)
            repas[repas_id].setAttribute('offset', self.date_to_offset(date))
            self.root.appendChild(repas[repas_id])
            
            if plat_id not in list(plats.keys()):
                plats[plat_id] = self.doc.createElement('plat')
            plats[plat_id].setAttribute('nom', plat_name)
            plats[plat_id].setAttribute('type', plat_type)
            repas[repas_id].appendChild(plats[plat_id])
            
            if ingr_id not in list(ingrs.keys()):
                ingrs[ingr_id] = self.doc.createElement('ingrédient')
            ingrs[ingr_id].setAttribute('nom', product_name)
            quant_el = self.doc.createElement('quantité')
            quant_el.setAttribute('unit', self.get_unit(unit))
            plats[plat_id].appendChild(ingrs[ingr_id])
            ingrs[ingr_id].appendChild(quant_el)
            if unit in ['Kilogrammes', 'Litres']:
                factor = 1000.
            else:
                factor = 1.
            
            # Si la quantité calculée automatiquement à partir du produit et 
            # des nombres d'enfants 
            # est égale à la quantité de l'ingredient_prev, on enregistre 
            # dans le XML les quantités recommandées du produit. Sinon, 
            # il faut calculer une estimation aproximative à partir 
            # du nombre d'enfants et de la quantité totale
            # TODO
            # pondérer en fonction des tranches d'âge.     

            excepted_quantity = (recommends_6 * nbr_6 
                + recommends6_12 * nbr_6_12
                + recommends_12 * nbr_12)
            if excepted_quantity == quantity:
                r = data[8:11]
            else:
                r = [quantity / sum([nbr_6, nbr_6_12, nbr_12]) * factor] * 3
            for tag, recommends, nbr_enfants in zip(
                ['age-6', 'age6-12', 'age-12'],
                r,
                data[13:16]):
                tag = self.doc.createElement(tag)
          
                value_node = self.doc.createTextNode(str(round(recommends, 2)))
                tag.appendChild(value_node)
                quant_el.appendChild(tag)

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
    
    def get_unit(self, unit):
        if unit == 'Unités':
            return 'pièce'
        elif unit == 'Kilogrammes':
            return 'gr'
        elif unit == 'Litres':
            return 'ml'
    
    def write_file(self, name='xml_test.xml'):
        with open(name, 'w', encoding="utf-8") as f:
            f.write(self.doc.toString())

if '__main__' == __name__:
    import model
    import sys
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    sqlmodel = model.Model()
    sqlmodel.connect_db(sys.argv[1])
    worker = CreateXml(sqlmodel)
    worker.write_file()
