#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from PyQt5.QtSql import QSqlQueryModel, QSqlDatabase, QSqlQuery, QSqlRelationalTableModel, QSqlRelation, QSqlTableModel
from PyQt5.QtCore import Qt, QFile, QIODevice, QModelIndex
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

    def exec_(self, request=None):
        """ Execute a request and return True if no error occur """
        if request:
            req = self.query.exec_(request)
        else:
            req = self.query.exec_()
        if DEBUG_SQL:
            print(req,":",request)
            if req == False:
                print(self.query.lastError().databaseText())
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
        self.qt_table_reserve = ReserveModel(self, self.db)
        self.qt_table_infos = InfosModel(self, self.db)
        self.qt_table_repas = RepasModel(self, self.db)
        self.qt_table_outputs = OutputsModel()

        self.previsionnel_model = PrevisionnelModel()
        self.repas_prev_model = RepasPrevModel(self, self.db)
        self.plat_prev_model = PlatPrevModel(self, self.db)
        self.ingredient_prev_model = IngredientPrevModel(self, self.db)

    def get_fournisseurs(self):
        self.query.exec_("SELECT NOM, ID FROM fournisseurs")
        return self._query_to_dic()

    def get_product_datas(self, product):
        self.exec_("SELECT reserve.id, quantity, prix, fournisseurs.nom\
        FROM reserve INNER JOIN fournisseurs on fournisseurs.id = reserve.Fournisseur_id\
        WHERE product_id = \
        (SELECT id FROM products WHERE name = '"+str(product)+"')")
        return self._query_to_lists(4)

    def get_all_products_names(self):
        """ return all products names in a list """
        self.exec_("SELECT name FROM products")
        return self._query_to_list()

    def get_quantity(self, product_id):
        self.exec_("SELECT quantity FROM reserve WHERE id = "+str(product_id))
        while self.query.next():
            return self.query.value(0)

    def get_(self, values=[], table=None, condition=None, distinct=False):
        sql_values = ",".join(values)
        if condition == None:
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
            "SELECT outputs.id, outputs.quantity, outputs.stock_id, products.name\
            FROM outputs\
            INNER JOIN reserve ON outputs.stock_id = reserve.id\
            INNER JOIN products ON reserve.product_id = products.id\
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

    def get_price_by_repas(self, repas_id):
        self.exec_("SELECT prix, outputs.quantity FROM reserve\
        INNER JOIN outputs ON outputs.stock_id = reserve.id\
        WHERE outputs.repas_id = "+str(repas_id))
        price = 0
        while self.query.next():
            price += self.query.value(0) * self.query.value(1)
        return price

    def get_price_by_day(self, date):
        self.exec_("SELECT prix, outputs.quantity FROM reserve\
        INNER JOIN outputs ON outputs.stock_id = reserve.id\
        INNER JOIN repas ON repas.id = outputs.repas_id\
        WHERE repas.date = '"+str(date)+"'")
        price = 0
        while self.query.next():
            price += self.query.value(0) * self.query.value(1)
        return price

    def get_dates_repas(self):
        self.exec_("SELECT DISTINCT date FROM repas")
        return self._query_to_list()

    def get_product_id_by_name(self, name):
        self.exec_("SELECT id FROM products WHERE name = '"+name+"'")
        while self.query.next():
            return self.query.value(0)
    
    def get_total(self):
        self.query.exec_("SELECT sum(prix) FROM reserve")
        while self.query.next():
            return self.query.value(0)

    def get_last_id(self, table):
        self.exec_("SELECT id FROM "+table+" ORDER BY id DESC LIMIT 1")
        while self.query.next():
            return self.query.value(0)

    def set_(self, dic={}, table=None):
        self.query.prepare(
            "INSERT INTO "+table+"("+",".join(dic.keys())+")\
            VALUES ("\
            +','.join([':'+x for x in list(dic.keys()) ])+")"
            )
        for k, v in dic.items():
            self.query.bindValue(':'+k, v)
        q = self.query.exec_()
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
        req = "INSERT INTO outputs ('quantity', 'repas_id', 'stock_id')\
        VALUES ("+\
        ','.join([
            str(datas['quantity']),
            str(datas['repas_id']),
            str(datas['product_id'])
            ])\
        + ")"
        self.exec_(req)
        new_quantity = self.get_quantity(datas['product_id']) - datas['quantity']
        self.exec_("UPDATE reserve SET quantity = "+str(new_quantity)\
        +" WHERE id = "+str(datas['product_id']))

    def add_product(self, datas):
        # if the product name is not in products table, we add it. 
        product_id = self.get_product_id_by_name(datas["product"])
        if not product_id:
            self.exec_("INSERT INTO products (name) VALUES ('"+datas["product"]+"')")
            product_id = self.get_product_id_by_name(datas['product'])
        # add it in reserve
        query = "INSERT INTO reserve (Fournisseur_id,  Date, product_id, Prix, start_quantity, quantity, unit_id)"
        query += " VALUES("\
        +str(datas["fournisseur_id"])+",'"\
        +str(datas["date"])+"',"\
        +str(product_id)+","\
        +str(datas["price"])+","\
        +str(datas["quantity"])+','\
        +str(datas["quantity"])+','\
        +str(datas["unit_id"])\
        +")"
        self.exec_(query)

    def add_repas(self, datas):
        req = self.query.exec_("INSERT INTO repas(date, type) VALUES("\
        +datas['date']+","+datas['type']+')')
        if req == False:
            print(self.query.lastError().databaseText())

    def update(self, datas={}, table='', qfilter_key=None, qfilter_value=None):
        l = []
        for k, v in datas.items():
            l += [str(k) + "='" + str(v)+"'"]
        success = self.exec_("UPDATE "+table+" SET "+', '.join(l)+\
        ' WHERE '+qfilter_key+" = '"+qfilter_value+"'")
        print('update succuss', success)
        return success
    
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

class ReserveModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(ReserveModel, self).__init__(parent, db)

        self.setTable('reserve')
        rel1 = QSqlRelation("fournisseurs","id","NOM")
        rel2 = QSqlRelation("units","id","unit")
        rel3 = QSqlRelation("products","id","name")
        self.setRelation(1, rel1)
        self.setRelation(3, rel3)
        self.setRelation(7, rel2)
        self.select()
        self.setHeaderData(0, Qt.Horizontal, "Identification")
        self.setHeaderData(1, Qt.Horizontal, "Fournisseur")
        self.setHeaderData(3, Qt.Horizontal, "Produit")
        self.setHeaderData(5, Qt.Horizontal, "Quantité\nde départ")
        self.setHeaderData(6, Qt.Horizontal, "Quantité\n actuelle")

class RepasModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(RepasModel, self).__init__(parent, db)

        self.setTable("repas")
        f_rel = QSqlRelation("type_repas","id","type")
        self.setRelation(2, f_rel)
        self.select()
        self.setHeaderData(0, Qt.Horizontal, "Identification")
        self.setHeaderData(2, Qt.Horizontal, "Type")

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
                product_id, dishes_prev_id, quantity, unit_id)\
                VALUES(1, "+str(plat_id)+", 0, 1)")
        self.select()
    
    def del_row(self, id=None):
        if id:
            query = QSqlQuery("DELETE FROM ingredients_prev WHERE id ="+str(id))
        self.select()

class OutputsModel(QSqlQueryModel):
    def __init__(self):
        super(OutputsModel, self).__init__()
        self.select()
    
    def select(self):
        self.setQuery("SELECT\
        outputs.id, products.name, outputs.quantity, repas.date, repas.id AS repas_id\
        FROM outputs\
        INNER JOIN repas ON outputs.repas_id = repas.id\
        INNER JOIN reserve ON outputs.stock_id = reserve.id\
        INNER JOIN products ON reserve.product_id = products.id\
        ")
        self.setHeaderData(0, Qt.Horizontal, "Name")
        self.setHeaderData(1, Qt.Horizontal, "quantité")

class PrevisionnelModel(QStandardItemModel):
    """ Not used yes. Maybe for creating read-only views like QColumnView """
    def __init__(self):
        super(PrevisionnelModel, self).__init__()
        #self.setColumnCount(5)
        self.root = self.invisibleRootItem()

        query_all = QSqlQuery(
            "SELECT repas_prev.name as repas, repas_prev.date, dishes_prev.name as plat, products.name as ingredient, ingredients_prev.quantity, units.unit FROM repas_prev\
            INNER JOIN dishes_prev ON dishes_prev.repas_prev_id = repas_prev.id\
            INNER JOIN ingredients_prev ON ingredients_prev.dishes_prev_id = dishes_prev.id\
            INNER JOIN products ON ingredients_prev.product_id = products.id\
            INNER JOIN units ON ingredients_prev.unit_id = units.id\
            WHERE repas_prev.date = '2017-04-01'")

    def query_for_day(self, date):
        query = QSqlQuery(
            "SELECT repas_prev.id, repas_prev.name, type_repas.type FROM repas_prev\
            INNER JOIN type_repas ON type_repas.id = repas_prev.type_id\
            WHERE repas_prev.date = '"+date+"'")
        repas_items = {}
        while query.next():
            repas_items[query.value(0)] = [
                QStandardItem(query.value(1)),
                QStandardItem(query.value(2))]
        for repas_id, repas_item in repas_items.items():
            self.root.appendRow(repas_item) # ......
            query = QSqlQuery("SELECT id, name as plat FROM dishes_prev\
            WHERE repas_prev_id = "+str(repas_id))
            plats_items = {}
            while query.next():
                plats_items[query.value(0)] = QStandardItem(query.value(1))
            for plat_id, plat_item in plats_items.items():
                repas_items[repas_id][0].appendRow(plat_item)
                query = QSqlQuery(
                    "SELECT ingredients_prev.id,\
                    products.name as ingredient,\
                    ingredients_prev.quantity\
                    FROM ingredients_prev\
                    INNER JOIN products ON products.id = ingredients_prev.product_id\
                    WHERE dishes_prev_id = "+str(plat_id))
                ingredients_items = {}
                while query.next():
                    ingredients_items[query.value(0)] = [
                        QStandardItem(query.value(1)),
                        QStandardItem(query.value(2))]
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
