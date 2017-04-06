#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from PyQt5.QtSql import QSqlQueryModel, QSqlDatabase, QSqlQuery, QSqlRelationalTableModel, QSqlRelation, QSqlTableModel
from PyQt5.QtCore import Qt, QFile, QIODevice, QModelIndex, QAbstractTableModel, QVariant
from PyQt5.QtGui import QStandardItemModel, QStandardItem

DEBUG_SQL = True

class Model(QSqlQueryModel):
    def __init__(self, parent=None):
        super(Model, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        self.parent = parent

    def create_db(self, db_name):
        connected = self.connect_db(db_name)
        if connected:
            with open('create_db.sql', 'r') as create_db_file:
                r = create_db_file.read()
                r = r.replace('\n',' ')
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
        if DEBUG_SQL:
            print(req, ':', self.query.lastQuery())
            if req == False:
                print('SQL ERROR:', self.query.lastError().text())
        return req

    def connect_db(self, db_name):
        self.db.setDatabaseName(db_name)
        opened = self.db.open()
        if opened:
            self._create_models()
            self.exec_("PRAGMA foreign_keys = ON")
        return opened

    def _create_models(self):
        self.query = QSqlQuery()
        self.qt_table_reserve = ReserveTableModel()
        self.qt_table_infos = InfosModel(self, self.db)
        self.qt_table_repas = RepasModel(self, self.db)
        self.qt_table_outputs = OutputsModel()
        self.qt_table_inputs = InputsModel(self, self.db)

        self.previsionnel_model = PrevisionnelModel()
        self.repas_prev_model = RepasPrevModel(self, self.db)
        self.plat_prev_model = PlatPrevModel(self, self.db)
        self.ingredient_prev_model = IngredientPrevModel(self, self.db)

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
        values = ['centre', 'directeur_nom', 'nombre_enfants_6', 
            'nombre_enfants_6_12', 'nombre_enfants_12', 'place',
            'startdate', 'enddate']
        self.exec_("SELECT "+", ".join(values)+" FROM infos")
        result = {}
        while self.query.next():
            for i, value in enumerate(values):
                result[value] = self.query.value(i)
        return result

    def get_prev_products_by_dates(self, date_start, date_stop):
        self.exec_(
            "SELECT products.name, quantity, units.unit FROM ingredients_prev\
            INNER JOIN dishes_prev ON dishes_prev.id = ingredients_prev.dishes_prev_id\
            INNER JOIN repas_prev ON repas_prev.id = dishes_prev.repas_prev_id\
            INNER JOIN products ON products.id = ingredients_prev.product_id\
            INNER JOIN units ON units.id = products.unit_id\
            WHERE repas_prev.date BETWEEN '"+date_start+"' AND '"+date_stop+"'")
        return self._query_to_lists(3)

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
        print(dic)
        self.query.prepare(
            "INSERT INTO "+table+"("+",".join(dic.keys())+")\
            VALUES ("\
            +','.join([':'+x for x in list(dic.keys()) ])+")"
            )
        for k, v in dic.items():
            self.query.bindValue(':'+k, v)
        q = self.exec_()
        return q

    def add_fournisseur(self, name):
        p = self.query.prepare("INSERT INTO fournisseurs (nom) VALUES(:nom)")
        self.query.bindValue(':nom', name)
        req = self.exec_()
        if req == False:
            print(self.query.lastError().databaseText())
            return self.query.lastError().databaseText()
        else:
            return req

    def add_output(self, datas):
        print('outputs datas', datas)
        self.query.prepare("INSERT INTO outputs(quantity, repas_id, product_id)"\
            +" VALUES("+str(datas['quantity'])+', '+str(datas['repas_id'])+', '+\
            str(datas['product_id'])+")")

    def add_product(self, product, unit_id):
        self.query.prepare(
            "INSERT INTO products (name, unit_id) VALUES (:name, :unit_id)")
        self.query.bindValue(':name', product)
        self.query.bindValue(':unit_id', unit_id)
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
        print('update succuss', success)
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
    """ Because SQLite doesn't implement FULL OUTER JOIN, we do the job with
    Python."""
    def __init__(self, parent=None):
        super(ReserveTableModel, self).__init__(parent)
        self.inputs = {}

        query = QSqlQuery(
                "SELECT products.name as produit,\
                sum(inputs.quantity)\
                FROM inputs\
                INNER JOIN products ON inputs.product_id = products.id\
                group by products.id")
        query.exec_()
        while query.next():
            self.inputs[query.value(0)] = query.value(1)
        query = QSqlQuery(
            "SELECT products.name as produit,\
            total(outputs.quantity)\
            FROM outputs\
            INNER JOIN products ON outputs.product_id = products.id\
            group by products.id")
        while query.next():
            print(query.value(0))
            self.inputs[query.value(0)] -= query.value(1)
        self.data_table = [kv for kv in sorted(self.inputs.items())]

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
        f_rel = QSqlRelation("type_repas","id","type")
        self.setRelation(2, f_rel)
        self.setHeaderData(0, Qt.Horizontal, "Identification")
        self.setHeaderData(2, Qt.Horizontal, "Type")
        self.select()

class AbstractPrevisionnelModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(AbstractPrevisionnelModel, self).__init__(parent, db)
        self.parent = parent
        self.setEditStrategy(QSqlTableModel.OnFieldChange)

class RepasPrevModel(AbstractPrevisionnelModel):
    def __init__(self, parent, db):
        super(RepasPrevModel, self).__init__(parent, db)

        self.setTable("repas_prev")
        f_rel = QSqlRelation("type_repas","id","type")
        self.setRelation(3, f_rel)
        self.rel_type = self.relationModel(3) #QsqlTable for combo box
        self.setHeaderData(1, Qt.Horizontal, "Nom")
        self.setHeaderData(3, Qt.Horizontal, "Type")
        self.select()

    def add_row(self, date=""):
        query = QSqlQuery("INSERT INTO repas_prev(name, date, type_id)\
                VALUES(NULL, '"+date+"',1)")
        self.select()

    def del_row(self, id=None):
        if id:
            query = QSqlQuery("DELETE FROM repas_prev WHERE id ="+str(id))
        self.select()
        self.parent.plat_prev_model.select()

class PlatPrevModel(AbstractPrevisionnelModel):
    def __init__(self, parent, db):
        super(PlatPrevModel, self).__init__(parent, db)
        
        self.setTable("dishes_prev")
        rel2 = QSqlRelation("repas_prev","id","name")
        rel3 = QSqlRelation("dishes_types","id","type")
        self.setRelation(2, rel2)
        self.setRelation(3, rel3)
        self.type_repas_model = self.relationModel(3) #QsqlTable for combo box
        self.setHeaderData(1, Qt.Horizontal, "Nom")
        self.setHeaderData(3, Qt.Horizontal, "Type")
        self.select()

    def add_row(self, repas_id):
        query = QSqlQuery("INSERT INTO dishes_prev(name, repas_prev_id, type_id)\
                VALUES(NULL, "+str(repas_id)+", 1)")
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
        rel1 = QSqlRelation("products","id","name")
        rel2 = QSqlRelation("dishes_prev","id","name")
        rel4 = QSqlRelation("units","id","unit")
        self.setRelation(1, rel1)
        self.setRelation(2, rel2)
        self.setRelation(4, rel4)

        self.rel_name = self.relationModel(1) #QsqlTable for combo box
        self.rel_unit = self.relationModel(4) #QsqlTable for combo box
        
        self.setHeaderData(1, Qt.Horizontal, "produit")
        self.setHeaderData(2, Qt.Horizontal, "repas")
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
    def __init__(self):
        super(IngredientPrevQueryModel, self).__init__()
        self.q = "SELECT products.name, quantity, units.unit FROM ingredients_prev\
            INNER JOIN products ON products.id = ingredients_prev.product_id\
            INNER JOIN units ON units.id = products.unit_id"
        self.filter = ""
        self.select()

    def select(self):
        print(self.q + self.filter)
        self.setQuery(self.q + self.filter)
        print(self.lastError().text())

    def setFilter(self, filter_):
        self.filter = ' WHERE '+filter_
        self.select()
    
    def add_row(self, plat_id):
        query = QSqlQuery("INSERT INTO ingredients_prev(\
                product_id, dishes_prev_id, quantity)\
                VALUES(1, "+str(plat_id)+", 0)")
        self.select()
    
    def del_row(self, id_=None):
        if id_:
            query = QSqlQuery("DELETE FROM ingredients_prev WHERE id ="+str(id_))
            self.select()

class OutputsModel(QSqlQueryModel):
    def __init__(self):
        super(OutputsModel, self).__init__()
        self.select()
    
    def select(self):
        self.setQuery("SELECT\
        products.name, outputs.quantity, repas.date, type_repas.type AS 'pour le'\
        FROM outputs\
        INNER JOIN repas ON outputs.repas_id = repas.id\
        INNER JOIN type_repas ON repas.type_id = type_repas.id\
        INNER JOIN products ON outputs.product_id = products.id\
        ")
        self.setHeaderData(0, Qt.Horizontal, "Nom")
        self.setHeaderData(1, Qt.Horizontal, "quantité")

class InputsModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(InputsModel, self).__init__(parent, db)

        self.setEditStrategy(QSqlRelationalTableModel.OnFieldChange)
        self.setTable("inputs")
        fournisseur_rel = QSqlRelation("fournisseurs","id","nom")
        product_rel = QSqlRelation("products","id","name")
        self.setRelation(1, fournisseur_rel)
        self.setRelation(3, product_rel)
        self.setHeaderData(1, Qt.Horizontal, "Fournisseur")
        self.setHeaderData(3, Qt.Horizontal, "Produit")
        self.setHeaderData(5, Qt.Horizontal, "Quantité")
        self.select()
    
class PrevisionnelModel(QStandardItemModel):
    """ Used for QColumnView in tab"""
    def __init__(self):
        super(PrevisionnelModel, self).__init__()
        query_all = QSqlQuery(
            "SELECT repas_prev.name as repas, repas_prev.date, dishes_prev.name as plat, products.name as ingredient, ingredients_prev.quantity, units.unit FROM repas_prev\
            INNER JOIN dishes_prev ON dishes_prev.repas_prev_id = repas_prev.id\
            INNER JOIN ingredients_prev ON ingredients_prev.dishes_prev_id = dishes_prev.id\
            INNER JOIN products ON ingredients_prev.product_id = products.id\
            INNER JOIN units ON ingredients_prev.unit_id = units.id\
            WHERE repas_prev.date = '2017-04-01'")
        self.query_for_day('2017-31-03')

    def query_for_day(self, date):
        self.clear()
        self.setColumnCount(2)
        self.root = self.invisibleRootItem()
        query = QSqlQuery(
            "SELECT repas_prev.id, repas_prev.name, type_repas.type FROM repas_prev\
            INNER JOIN type_repas ON type_repas.id = repas_prev.type_id\
            WHERE repas_prev.date = '"+date+"'")
        repas_items = {}
        while query.next():
            repas_items[query.value(0)] =\
                QStandardItem(query.value(1)+' ('+query.value(2)+')')
        for repas_id, repas_item in repas_items.items():
            self.root.appendRow(repas_item) # ......
            query = QSqlQuery(
                "SELECT dishes_prev.id, name as plat, dishes_types.type\
                FROM dishes_prev\
                INNER JOIN dishes_types ON dishes_prev.type_id = dishes_types.id\
                WHERE repas_prev_id = "+str(repas_id))
            plats_items = {}
            while query.next():
                plats_items[query.value(0)] =\
                        QStandardItem(query.value(1)+' ('+query.value(2)+')')
            for plat_id, plat_item in plats_items.items():
                repas_items[repas_id].appendRow(plat_item)
                query = QSqlQuery(
                    "SELECT ingredients_prev.id,\
                    products.name as ingredient,\
                    ingredients_prev.quantity,\
                    units.unit\
                    FROM ingredients_prev\
                    INNER JOIN products ON products.id = ingredients_prev.product_id\
                    INNER JOIN units ON products.unit_id = units.id\
                    WHERE dishes_prev_id = "+str(plat_id))
                print(query.lastError().text())
                ingredients_items = {}
                while query.next():
                    ingredients_items[query.value(0)] =\
                        QStandardItem(query.value(1)\
                        +' ('+str(round(query.value(2),2))+' '+query.value(3)+')')
                for ingr_id, ingr_item in ingredients_items.items():
                    plats_items[plat_id].appendRow(ingr_item)
        
    def prepareRow(self, array):
        items = [QStandardItem(item) for item in array]
        items_row = QStandardItem()
        items_row.appendRow(items)
        return items_row

if '__main__' == __name__:
    m = Model()
    m.create_db('aa.db')
