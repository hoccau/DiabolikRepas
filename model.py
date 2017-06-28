#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
This file contains SQL queries and QT models
"""

from PyQt5.QtSql import (
    QSqlQueryModel, QSqlDatabase, QSqlQuery, QSqlRelationalTableModel, 
    QSqlRelation, QSqlTableModel)
from PyQt5.QtCore import Qt, QModelIndex, QAbstractTableModel, QVariant
import logging

DEBUG_SQL = True

class Model(QSqlQueryModel):
    def __init__(self, parent=None):
        super(Model, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.parent = parent

    def create_db(self, db_name):
        connected = self.connect_db(db_name)
        if connected:
            with open('create_db.sql', 'r', encoding='utf-8') as create_db_file:
                r = create_db_file.read()
                r = r.replace('\n', ' ')
                requests = r.split(';')[:-1] #remove the last because empty
            for req in requests:
                self.exec_(req)
            return True

    def exec_(self, request=None):
        """ Execute a request and return True if no error occur """
        if request:
            req = self.query.exec_(request)
        else:
            req = self.query.exec_()
        logging.debug(str(req) + ':' + self.query.lastQuery())
        if req == False:
            logging.warning(self.query.lastError().text())
        return req

    def connect_db(self, db_name):
        self.db.setDatabaseName(db_name)
        opened = self.db.open()
        if opened:
            self._create_models()
            self.exec_("PRAGMA foreign_keys = ON")
            logging.info(db_name + ' open.')
        else:
            logging.warning(db_name + ' not open.')
        return opened

    def _create_models(self):
        self.query = QSqlQuery()
        self.qt_table_products = ProductsModel(self, self.db)
        self.qt_table_fournisseurs = FournisseurModel(self, self.db)
        self.qt_table_reserve = ReserveTableModel()
        self.qt_table_infos = InfosModel(self, self.db)
        self.qt_table_periodes_infos = PeriodesModel(self, self.db)
        self.qt_table_repas = RepasModel(self, self.db)
        self.qt_table_outputs = OutputsModel(self, self.db)
        self.qt_table_inputs = InputsModel(self, self.db)

        self.repas_prev_model = RepasPrevModel(self, self.db)
        self.plat_prev_model = PlatPrevModel(self, self.db)
        self.ingredient_prev_model = IngredientPrevQueryModel(self)
        self.piquenique_conf_model = PiqueniqueConfModel(self, self.db)

    def get_fournisseurs(self):
        self.query.exec_("SELECT NOM, ID FROM fournisseurs")
        return self._query_to_dic()

    def get_all_products_names(self):
        """ return all products names in a list """
        self.exec_("SELECT name FROM products")
        return self._query_to_list()

    def get_quantity(self, product_id):
        self.exec_(
            "SELECT sum(inputs.quantity) - total(outputs.quantity) as quantity\
            FROM inputs\
            INNER JOIN products ON inputs.product_id = products.id\
            LEFT JOIN outputs ON outputs.product_id = products.id\
            WHERE products.id = "+str(product_id)+"\
            GROUP BY products.id")
        while self.query.next():
            return self.query.value(0)

    def get_infos(self):
        values = ['centre', 'directeur_nom', 'place']
        self.exec_("SELECT " + ", ".join(values) + " FROM infos")
        result = {}
        while self.query.next():
            for i, value in enumerate(values):
                result[value] = self.query.value(i)
        self.exec_(
            "SELECT date_start, date_stop "\
            + "FROM infos_periodes ORDER BY date_start")
        if self.query.first():
            result['date_start'] = self.query.value(0)
        if self.query.last():
            result['date_stop'] = self.query.value(1)
        return result

    def get_prev_products_by_dates(self, date_start, date_stop):
        """ used for inputs -> import previsionnel """
        self.exec_(
            "SELECT ingredients_prev.id, products.id, products.name, quantity, "
            + "units.unit, products.fournisseur_id "\
            + "FROM ingredients_prev\
            INNER JOIN dishes_prev ON dishes_prev.id = ingredients_prev.dishes_prev_id\
            INNER JOIN repas_prev ON repas_prev.id = dishes_prev.repas_prev_id\
            INNER JOIN products ON products.id = ingredients_prev.product_id\
            INNER JOIN units ON units.id = products.unit_id\
            WHERE repas_prev.date BETWEEN '"+date_start+"' AND '"+date_stop+"'")
        return self._query_to_lists(6)

    def get_prev_products_by_dates_for_courses(self, date_start, date_stop):
        """ Almost the same request, but for liste PDF export. liste_courses
        is a view. """
        self.exec_(
            "SELECT * FROM liste_courses "\
            + "WHERE date BETWEEN '" + date_start + "' AND '" + date_stop + "'")
        liste = self._query_to_lists(4)
        self.exec_(
            "SELECT product_id, products.name, total(quantity) FROM ( "\
	    + "SELECT inputs.product_id, inputs.quantity "\
	    + "FROM inputs "\
	    + "INNER JOIN products ON products.id = inputs.product_id "\
	    + "LEFT JOIN ingredients_prev ON ingredients_prev.id = inputs.ingredients_prev_id "\
	    + "LEFT JOIN dishes_prev ON dishes_prev.id = ingredients_prev.dishes_prev_id "\
	    + "LEFT JOIN repas_prev ON repas_prev.id = dishes_prev.repas_prev_id "\
	    + "WHERE inputs.ingredients_prev_id is NULL "\
	    + "OR '" + date_start + "' >= repas_prev.date <= '" + date_stop + "' "\
	    + "UNION "
	    + "SELECT outputs.product_id, - outputs.quantity "\
	    + "FROM outputs) "\
	    + "INNER JOIN products ON products.id = product_id "\
	    + "GROUP BY product_id")
        stock = self._query_to_lists(3)
        logging.debug(stock)
        for line in liste:
            # if product is in stock
            if line[1] in [i[1] for i in stock]:
                line[2] = line[2] - [i[2] for i in stock if i[1] == line[1]][0]
        return liste

    def get_prev_products_for_export(self):
        """ Used for 'export previsionnel' """
        self.exec_(
            "SELECT repas_prev.date, type_repas.type, dishes_prev.name, "\
            + "products.name, quantity, units.unit, products.fournisseur_id "\
            + "FROM ingredients_prev "\
            + "INNER JOIN dishes_prev ON dishes_prev.id = ingredients_prev.dishes_prev_id "\
            + "INNER JOIN repas_prev ON repas_prev.id = dishes_prev.repas_prev_id "\
            + "INNER JOIN products ON products.id = ingredients_prev.product_id "\
            + "INNER JOIN type_repas ON type_repas.id = repas_prev.type_id "\
            + "INNER JOIN units ON units.id = products.unit_id "\
            + "ORDER BY repas_prev.date")
        return self._query_to_lists(6)

    def get_prev_ingrs(self, date, repas_type_id):
        self.exec_(
            "SELECT ingredients_prev.product_id, "\
            + "products.name, ingredients_prev.quantity "\
            + "FROM ingredients_prev "\
            + "INNER JOIN products "\
            + "ON products.id = ingredients_prev.product_id "\
            + "WHERE ingredients_prev.dishes_prev_id IN ("\
	    + "SELECT dishes_prev.id FROM dishes_prev "\
	    + "INNER JOIN repas_prev "\
            + "ON repas_prev.id = dishes_prev.repas_prev_id "\
	    + "WHERE repas_prev.date = '" + date + "' "\
            + "AND repas_prev.type_id = " + str(repas_type_id) +")")
        return self._query_to_lists(3)

    def get_plats_by_dates(self, date_start, date_stop):
        plats = []
        self.exec_(
            "SELECT repas_prev.date, type_repas.type, dishes_types.type, name "\
            + "FROM dishes_prev "\
            + "INNER JOIN repas_prev ON repas_prev.id = repas_prev_id "\
            + "INNER JOIN type_repas ON repas_prev.type_id = type_repas.id "\
            + "INNER JOIN dishes_types ON dishes_types.id = dishes_prev.type_id "\
            + "WHERE '" + date_start + "' <= repas_prev.date "\
            + "AND repas_prev.date <= '" + date_stop + "'")
        while self.query.next():
            plats.append([self.query.value(i) for i in range(4)])
        return plats

    def get_(self, values=[], table=None, condition=None, distinct=False):
        sql_values = ",".join(values)
        if not condition:
            condition = ""
        else:
            condition = " WHERE "+str(condition)
        if distinct:
            distinct = "DISTINCT"
        else:
            distinct = ""
        self.exec_("SELECT "+distinct+' '+sql_values+" FROM "+table + condition)
        records = []
        while self.query.next():
            dic = {}
            for i, value in enumerate(values):
                dic[value] = self.query.value(i)
            records.append(dic)
        return records

    def get_all_repas(self):
        self.exec_("SELECT repas.id, date,type FROM repas\
        INNER JOIN type_repas ON type_repas.id = repas.type_id")
        res = []
        while self.query.next():
            dic = {}
            dic['id'] = self.query.value(0)
            dic['date'] = self.query.value(1)
            dic['type'] = self.query.value(2)
            res.append(dic)
        return res

    def get_repas_by_id(self, id_):
        """ return a dict with repas which contain a list of dicts with outputs """
        self.exec_("SELECT date, type, comment FROM repas\
        INNER JOIN type_repas ON type_repas.id = repas.type_id \
        WHERE repas.id = "+str(id_))
        datas = {}
        while self.query.next():
            datas['date'] = self.query.value(0)
            datas['type'] = self.query.value(1)
            datas['comment'] = self.query.value(2)
        self.exec_(
            "SELECT outputs.id, outputs.quantity, outputs.product_id, products.name\
            FROM outputs\
            INNER JOIN products ON outputs.product_id = products.id\
            WHERE outputs.repas_id = "+str(id_)
            )
        datas['outputs'] = []
        while self.query.next():
            datas['outputs'].append({
                'id': self.query.value(0),
                'quantity': self.query.value(1),
                'product_id': self.query.value(2),
                'product_name': self.query.value(3)
                })
        return datas

    def get_avg_price(self, product_id):
        self.exec_("SELECT AVG(prix) FROM inputs WHERE product_id = "+str(product_id))
        if self.query.first():
            return self.query.value(0)

    def get_all_avg_prices(self):
        self.exec_(
            "SELECT inputs.product_id, AVG(prix) FROM inputs "\
	    + "INNER JOIN products ON products.id = inputs.product_id "\
            + "GROUP BY inputs.product_id")
        return self._query_to_dic()

    def get_all_outputs_by_date(self, date):
        self.exec_(
            "SELECT outputs.product_id, products.name, outputs.quantity, "\
	    + "outputs.repas_id, repas.type_id as repas_type_id FROM outputs "\
            + "INNER JOIN products ON products.id = outputs.product_id "\
            + "INNER JOIN repas ON repas.id = outputs.repas_id "\
            + "WHERE repas.date = '" + date + "' "\
            + "ORDER BY repas_type_id")
        return self._query_to_lists(5)

    def get_price_by_repas(self, repas_id):
        self.exec_(
            "SELECT\
            outputs.quantity * AVG(inputs.prix) as prix_total\
            FROM outputs\
            INNER JOIN products ON products.id = outputs.product_id\
            INNER JOIN inputs ON inputs.product_id = products.id\
            WHERE outputs.repas_id = "+str(repas_id)+"\
            GROUP BY products.id")
        return sum(self._query_to_list())

    def get_price_by_day(self, date):
        self.exec_("SELECT id FROM repas WHERE date = '"+date+"'")
        repas_ids = self._query_to_list()
        return sum([self.get_price_by_repas(id_) for id_ in repas_ids])

    def get_dates_repas(self):
        self.exec_("SELECT DISTINCT date FROM repas")
        return self._query_to_list()

    def get_product_id_by_name(self, name):
        self.exec_("SELECT id FROM products WHERE name = '"+name+"'")
        while self.query.next():
            return self.query.value(0)

    def get_product_unit(self, product_name):
        self.exec_("SELECT units.unit FROM products\
            INNER JOIN units ON units.id = products.unit_id\
            WHERE products.name = '"+product_name+"'")
        if self.query.first():
            return self.query.value(0)

    def get_total(self):
        self.exec_("SELECT SUM(quantity * prix) FROM inputs")
        while self.query.next():
            return self.query.value(0)

    def get_last_id(self, table):
        self.exec_("SELECT id FROM "+table+" ORDER BY id DESC LIMIT 1")
        while self.query.next():
            return self.query.value(0)

    def set_(self, dic, table):
        self.query.prepare(
            "INSERT INTO "+table+"("+",".join(dic.keys())+")\
            VALUES ("\
            + ','.join([':'+x for x in list(dic.keys())]) + ")"
            )
        for k, v in dic.items():
            self.query.bindValue(':'+k, v)
        q = self.exec_()
        return q

    def add_fournisseur(self, name):
        self.query.prepare("INSERT INTO fournisseurs (nom) VALUES(:nom)")
        self.query.bindValue(':nom', name)
        req = self.exec_()
        if req == False:
            logging.warning(self.query.lastError().databaseText())
            return self.query.lastError().databaseText()
        else:
            return req

    def add_output(self, datas):
        logging.debug('outputs datas : ' + str(datas))
        self.query.prepare("INSERT INTO outputs(quantity, repas_id, product_id)"\
            +" VALUES("+str(datas['quantity'])+', '+str(datas['repas_id'])+', '+\
            str(datas['product_id'])+")")

    def add_product(self, product, unit_id, recommends):
        self.query.prepare(
            "INSERT INTO products (name, unit_id, "\
            + " recommended_6, recommended_6_12, recommended_12)"\
            + " VALUES (:name, :unit_id, :r_6, :r_6_12, :r_12)")
        self.query.bindValue(':name', product)
        self.query.bindValue(':unit_id', unit_id)
        self.query.bindValue(':r_6', recommends[0])
        self.query.bindValue(':r_6_12', recommends[1])
        self.query.bindValue(':r_12', recommends[2])
        res = self.exec_()
        return res, self.query.lastError().databaseText()

    def add_input(self, datas={}):
        self.query.prepare(
            "INSERT INTO inputs (fournisseur_id, date, product_id, prix, quantity)\
            VALUES (:fournisseur_id, :date, :product_id, :prix, :quantity)")
        for k, v in datas.items():
            self.query.bindValue(':'+k, v)
        self.exec_()

    def add_repas(self, datas):
        req = self.exec_("INSERT INTO repas(date, type_id, comment) VALUES("\
            +"'"+datas['date']+"'"+', '+datas['type_id']+', '\
            +"'"+datas['comment']+"')")
        return req

    def update(self, datas={}, table='', qfilter_key=None, qfilter_value=None):
        l = []
        for k, v in datas.items():
            l += [str(k) + "='" + str(v)+"'"]
        success = self.exec_("UPDATE "+table+" SET "+', '.join(l)+\
        ' WHERE '+qfilter_key+" = '"+qfilter_value+"'")
        logging.info('update success : ' + str(success))
        return success

    def auto_fill_query(self, date, type_):
        self.exec_(
            "SELECT products.name,\
            ingredients_prev.quantity,\
            units.unit FROM ingredients_prev\
            INNER JOIN units on units.id = ingredients_prev.unit_id\
            INNER JOIN products ON products.id = ingredients_prev.product_id\
            INNER JOIN dishes_prev ON dishes_prev.id = ingredients_prev.dishes_prev_id\
            INNER JOIN repas_prev on repas_prev.id = dishes_prev.repas_prev_id\
            WHERE repas_prev.date = '"+date+"'\
            AND repas_prev.type_id = \
            (SELECT id from type_repas WHERE type_repas.type = '"+type_+"')")
        return self._query_to_lists(3)

    def delete(self, table, qfilter_key, qfilter_value):
        self.exec_('DELETE FROM '+table+' WHERE '+qfilter_key+' = '+"'"+qfilter_value+"'")

    def delete_all_previsionnel(self):
        for table in ['ingredients_prev', 'repas_prev', 'dishes_prev']:
            self.exec_("DELETE FROM "+table)

    def get_recommended_quantity(self, day, product):
        self.exec_(
            "SELECT nombre_enfants_6, "\
            + "nombre_enfants_6_12, "\
            + "nombre_enfants_12 "\
            + "FROM infos_periodes "\
            + "WHERE date_start <= '" + day + "' <= date_stop")
        if self.query.first():
            nbr_enfants = [self.query.value(x) for x in range(3)]
        else:
            logging.warning("Pas de périodes trouvées dans les infos du centre")
            return False
        self.exec_(
            "SELECT recommended_6, "\
            + "recommended_6_12, "\
            + "recommended_12, "\
            + "unit_id "
            + "FROM products "\
            + "WHERE name = '" + product + "'")
        if self.query.first():
            recommends = [self.query.value(x) for x in range(3)]
            # below: prevent null values
            recommends = [0 if isinstance(x, str) else x for x in recommends]
            unit_id = self.query.value(3)
        else:
            logging.warning('Pas de produit trouvé')
            return False
        res = [x * recommends[i] for i, x in enumerate(nbr_enfants)]
        logging.debug(res)
        res = sum(res)
        logging.info('result for ' + product + ': ' + str(res))
        if unit_id in (2, 3): # if Kilogrammes or litres
            res = res / 1000.
        return res

    def _query_to_dic(self):
        """ return a dict which contains query results """
        dic = {}
        while self.query.next():
            dic[self.query.value(0)] = self.query.value(1)
        return dic

    def _query_to_lists(self, nbr_values=1):
        """ return a list which contains records as lists 

            Args:
                nbr_values: excepted number of values.
        """
        list_ = []
        while self.query.next():
            record = []
            for i in range(nbr_values):
                record.append(self.query.value(i))
            list_.append(record)
        return list_

    def _query_to_list(self):
        """ return a list of values. The query must return one-value records """
        list_ = []
        while self.query.next():
            list_.append(self.query.value(0))
        return list_

class InfosModel(QSqlTableModel):
    def __init__(self, parent, db):
        super(InfosModel, self).__init__(parent, db)

        self.setTable("infos")
        self.select()

class PeriodesModel(QSqlTableModel):
    def __init__(self, parent, db):
        super(PeriodesModel, self).__init__(parent, db)

        self.setTable('infos_periodes')
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.setHeaderData(1, Qt.Horizontal, "Début")
        self.setHeaderData(2, Qt.Horizontal, "Fin")
        self.setHeaderData(3, Qt.Horizontal, "Enfants de\n moins de 6 ans")
        self.setHeaderData(4, Qt.Horizontal, "Enfants entre\n 6 et 12 ans")
        self.setHeaderData(
            5, Qt.Horizontal, "Enfants de\n plus de 12 ans\n & adultes")
        self.select()

    def get_enfants_by_date(self, date):
        for row in range(self.rowCount()):
            date_start = self.data(self.index(row, 1))
            date_stop = self.data(self.index(row, 2))
            if date_start <= date and date_stop >= date:
                return [self.data(self.index(row, i)) for i in range(3, 6)]

class ReserveModel(QSqlQueryModel):
    def __init__(self):
        super(ReserveModel, self).__init__()
        self.select()

    def select(self):
        self.setQuery(
            "SELECT DISTINCT products.name,\
            total(inputs.quantity) - total(outputs.quantity) as quantité\
            FROM products\
            INNER JOIN inputs on inputs.product_id = products.id\
            LEFT JOIN outputs on outputs.product_id = products.id\
            GROUP BY inputs.id")

class ReserveTableModel(QAbstractTableModel):
    """ Simple difference between inputs and outputs to know which product 
    is in stock. Because SQLite doesn't implement FULL OUTER JOIN, 
    we do the job with UNION clause."""
    def __init__(self, parent=None):
        super(ReserveTableModel, self).__init__(parent)
        self.select()
 
    def select(self):
        self.data_table = []
        query = QSqlQuery(
	    "SELECT product_id, products.name, total(quantity) FROM ( "\
		+ "SELECT inputs.product_id, inputs.quantity "\
		+ "FROM inputs "\
		+ "INNER JOIN products ON products.id = inputs.product_id "\
		+ "UNION "\
		+ "SELECT outputs.product_id, - outputs.quantity "\
		+ "FROM outputs) "\
	    + "INNER JOIN products ON products.id = product_id "\
            + "GROUP BY product_id "\
            + "ORDER BY products.name")
        query.exec_()
        while query.next():
            self.data_table.append([query.value(1), query.value(2)])
        self.layoutChanged.emit()

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if section == 0 and orientation == Qt.Horizontal:
                return 'Produit'
            if section == 1 and orientation == Qt.Horizontal:
                return 'Stock'
        else:
            return QVariant()
    def setHeaderData(self, section, orientation, value):
        self.headerDataChanged()

    def data(self, index, role):
        if role == Qt.DisplayRole:
            i = index.row()
            j = index.column()
            return self.data_table[i][j]
        else:
            return QVariant()

    def rowCount(self, parent=QModelIndex()):
        return len(self.data_table)

    def columnCount(self, parent=QModelIndex()):
        if len(self.data_table) > 0:
            return len(self.data_table[0])
        else:
            return 0

class RepasModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(RepasModel, self).__init__(parent, db)

        self.setTable("repas")
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        f_rel = QSqlRelation("type_repas", "id", "type")
        self.setRelation(2, f_rel)
        self.setHeaderData(0, Qt.Horizontal, "Identification")
        self.setHeaderData(2, Qt.Horizontal, "Type")
        self.select()

class AbstractPrevisionnelModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(AbstractPrevisionnelModel, self).__init__(parent, db)
        self.parent = parent
        self.setEditStrategy(QSqlTableModel.OnFieldChange)

    def get_data(self, row, col):
        return self.data(self.index(row, col))

class RepasPrevModel(AbstractPrevisionnelModel):
    def __init__(self, parent, db):
        super(RepasPrevModel, self).__init__(parent, db)

        self.setTable("repas_prev")
        f_rel = QSqlRelation("type_repas", "id", "type")
        self.setRelation(2, f_rel)
        self.rel_type = self.relationModel(2) #QsqlTable for combo box
        #self.setHeaderData(2, Qt.Horizontal, "Type")
        self.select()

    def add_row(self, date="", type_id=None):
        query = QSqlQuery("INSERT INTO repas_prev(date, type_id)\
                VALUES('" + date + "'," + str(type_id) + ")")
        if query.lastError().text().rstrip(' '):
            logging.warning(query.lastQuery())
            logging.warning(query.lastError().text())
        else:
            self.select()
            return True

    def get_id(self, date, type_id):
        query = QSqlQuery(
            "SELECT id FROM repas_prev WHERE date = '"\
            + str(date) + "' AND type_id = " + str(type_id))
        if query.lastError().text().rstrip(' '):
            logging.warning(query.lastQuery())
            logging.warning(query.lastError().text())
        elif query.first():
            return query.value(0)

    def del_row(self, id=None):
        if id:
            query = QSqlQuery("DELETE FROM repas_prev WHERE id ="+str(id))
        self.select()
        self.parent.plat_prev_model.select()

class PlatPrevModel(AbstractPrevisionnelModel):
    def __init__(self, parent, db):
        super(PlatPrevModel, self).__init__(parent, db)

        self.setTable("dishes_prev")
        rel2 = QSqlRelation("repas_prev", "id", "date")
        rel3 = QSqlRelation("dishes_types", "id", "type")
        self.setRelation(2, rel2)
        self.setRelation(3, rel3)
        self.type_repas_model = self.relationModel(3) #QsqlTable for combo box
        self.setHeaderData(1, Qt.Horizontal, "Nom")
        self.setHeaderData(3, Qt.Horizontal, "Type")

        self.select()

    def add_row(self, repas_id, type_id):
        query = QSqlQuery("INSERT INTO dishes_prev(name, repas_prev_id, type_id)\
                VALUES(NULL, "+str(repas_id)+", " + str(type_id) + ")")
        if query.lastError().text().rstrip(' '):
            logging.warning(query.lastQuery())
            logging.warning(query.lastError().text())
        self.select()

    def del_row(self, id=None):
        if id:
            query = QSqlQuery("DELETE FROM dishes_prev WHERE id ="+str(id))
        self.select()
        self.parent.ingredient_prev_model.select()

class IngredientPrevModel(AbstractPrevisionnelModel):
    def __init__(self, parent, db):
        super(IngredientPrevModel, self).__init__(parent, db)

        self.setTable('ingredients_prev')
        self.setEditStrategy(QSqlRelationalTableModel.OnManualSubmit)
        rel1 = QSqlRelation("products", "id", "name")
        rel2 = QSqlRelation("dishes_prev", "id", "name")
        rel4 = QSqlRelation("units", "id", "unit")
        self.setRelation(1, rel1)
        self.setRelation(2, rel2)
        self.setRelation(4, rel4)

        self.rel_name = self.relationModel(1) #QsqlTable for combo box
        self.products = parent.qt_table_products
        self.rel_name.sort(1, Qt.SortOrder(0))
        self.rel_name.setEditStrategy(QSqlTableModel.OnFieldChange)
        self.rel_unit = self.relationModel(4) #QsqlTable for combo box

        self.setHeaderData(1, Qt.Horizontal, "produit")
        self.setHeaderData(2, Qt.Horizontal, "repas")
        self.setHeaderData(3, Qt.Horizontal, "Quantité")
        self.setHeaderData(4, Qt.Horizontal, "unités")
        self.select()

    def add_row(self, plat_id):
        query = QSqlQuery("INSERT INTO ingredients_prev(\
                product_id, dishes_prev_id, quantity)\
                VALUES(1, "+str(plat_id)+", 0)")
        self.select()

    def del_row(self, id=None):
        if id:
            query = QSqlQuery("DELETE FROM ingredients_prev WHERE id ="+str(id))
        self.select()

class IngredientPrevQueryModel(QSqlQueryModel):
    def __init__(self, parent):
        super(IngredientPrevQueryModel, self).__init__()
        self.parent = parent
        self.filter = ""
        self.select()

    def flags(self, index):
        flags = super().flags(index)

        if index.column() in (1, 2):
            flags |= Qt.ItemIsEditable

        return flags

    def setData(self, index, value, role):
        if index.column() not in (1, 2):
            return False

        id_idx = self.index(index.row(), 0)
        id_ = self.data(id_idx)

        #self.clear()

        if index.column() == 1:
            ok = self.set_product(id_, value)
        elif index.column() == 2:
            ok = self.set_quantity(id_, value)

        self.select()
        return ok

    def select(self):
        q = "SELECT ingredients_prev.id, products.name, quantity, units.unit "\
            + "FROM ingredients_prev "\
            + "INNER JOIN products ON products.id = ingredients_prev.product_id " \
            + "INNER JOIN units ON units.id = products.unit_id "
        if self.filter:
            q += self.filter
        self.setQuery(q)

    def set_product(self, id_, product_id):
        query = QSqlQuery()
        query.prepare('UPDATE ingredients_prev SET product_id = ? where id = ?')
        query.addBindValue(product_id)
        query.addBindValue(id_)
        return query.exec_()

    def set_quantity(self, id_, quantity):
        query = QSqlQuery()
        query.prepare('UPDATE ingredients_prev SET quantity = ? where id = ?')
        query.addBindValue(quantity)
        query.addBindValue(id_)
        return query.exec_()

    def setFilter(self, filter_):
        self.filter = ' WHERE '+filter_
        self.select()

    def add_row(self, plat_id):
        logging.debug(plat_id)
        query = QSqlQuery("INSERT INTO ingredients_prev(\
                product_id, dishes_prev_id, quantity)\
                VALUES(1, "+str(plat_id)+", 0)")
        if query.lastError().text().rstrip(' '):
            logging.warning(query.lastError().text())
            return False
        else:
            self.select()
            return True

    def get_all_by_date(self, date):
        """ id, product - without piquenique """
        query = QSqlQuery("SELECT ingredients_prev.id, products.name, "\
            + "repas_prev.type_id "\
            + "FROM ingredients_prev "\
            + "INNER JOIN dishes_prev ON dishes_prev.id = ingredients_prev.dishes_prev_id "\
            + "INNER JOIN repas_prev ON repas_prev.id = dishes_prev.repas_prev_id "\
            + "INNER JOIN products ON products.id = ingredients_prev.product_id "\
            + "WHERE repas_prev.date = '" + date + "' "\
            + "AND repas_prev.type_id != 5")
            #(" + ', '.join([str(i) for i in type_ids]) + ')' )
        if query.lastError().text().rstrip(' '):
            logging.warning(query.lastError().text())
            return False
        else:
            res = []
            while query.next():
                res.append([query.value(0), query.value(1), query.value(2)])
            return res

    def del_row(self, id_=None):
        if id_:
            query = QSqlQuery("DELETE FROM ingredients_prev WHERE id ="+str(id_))
            self.select()

    def submitAll(self):
        logging.debug('submitAll')

class OutputsModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super().__init__(parent, db)
        self.setTable("outputs")
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        product_rel = QSqlRelation("products", 'id', 'name')
        self.setRelation(3, product_rel)
        self.setHeaderData(1, Qt.Horizontal, "Quantité")
        self.setHeaderData(3, Qt.Horizontal, "Produit")
        self.select()

class InputsModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(InputsModel, self).__init__(parent, db)

        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.setTable("inputs")
        fournisseur_rel = QSqlRelation("fournisseurs", "id", "nom")
        product_rel = QSqlRelation("products", "id", "name")
        self.setRelation(1, fournisseur_rel)
        self.setRelation(3, product_rel)
        self.setHeaderData(1, Qt.Horizontal, "Fournisseur")
        self.setHeaderData(3, Qt.Horizontal, "Produit")
        self.setHeaderData(6, Qt.Horizontal, "Quantité")
        self.select()

class ProductsModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(ProductsModel, self).__init__(parent, db)

        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.setTable("products")
        self.setJoinMode(QSqlRelationalTableModel.LeftJoin)
        units_rel = QSqlRelation("units", "id", "unit")
        fournisseur_rel = QSqlRelation("fournisseurs", "id", "nom")
        self.setRelation(2, units_rel)
        self.setRelation(6, fournisseur_rel)
        self.setHeaderData(1, Qt.Horizontal, "Nom")
        self.setHeaderData(2, Qt.Horizontal, "Unité\n de mesure")
        self.setHeaderData(3, Qt.Horizontal, "Quantité\n pour moins de\n 6 ans")
        self.setHeaderData(4, Qt.Horizontal, "Quantité\n pour 6-12 ans")
        self.setHeaderData(5, Qt.Horizontal, "Quantité\n pour plus de\n 12 ans")
        self.setHeaderData(6, Qt.Horizontal, "Fournisseur")
        self.select()
        logging.debug(self.lastError().text())

    def get_recommends(self, product):
        for row in range(self.rowCount()):
            if self.data(self.index(row, 1)) == product:
                r = [self.data(self.index(row, i)) for i in range(3, 6)]
                if self.data(self.index(row, 2)) in ('Litres', 'Kilogrammes'):
                    r = [x / 1000. for x in r]
                return r

    def get_index_by_name(self, name):
        for row in range(self.rowCount()):
            if self.data(self.index(row, 1)) == name:
                return self.index(row, 0)

class FournisseurModel(QSqlTableModel):
    def __init__(self, parent, db):
        super(FournisseurModel, self).__init__(parent, db)

        self.setTable('fournisseurs')
        self.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.select()

class PiqueniqueConfModel(QSqlTableModel):
    def __init__(self, parent, db):
        super().__init__(parent, db)

        self.setTable('piquenique_conf')
        self.select()

if __name__ == '__main__':
    model = Model()
    model.create_db('aa.db')
