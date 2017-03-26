#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from PyQt5.QtSql import QSqlQueryModel, QSqlDatabase, QSqlQuery, QSqlRelationalTableModel, QSqlRelation, QSqlTableModel
from PyQt5.QtCore import Qt, QFile, QIODevice

DEBUG_SQL = True

class Model(QSqlQueryModel):
    def __init__(self, parent=None):
        super(Model, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE')

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
        return opened

    def _create_models(self):
        self.query = QSqlQuery()
        self.qt_table_reserve = ReserveModel(self, self.db)
        self.qt_table_infos = InfosModel(self, self.db)
        self.qt_table_repas = RepasModel(self, self.db)
        self.qt_table_outputs = OutputsModel()

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

    def set_infos(self, directeur_nom=None, directeur_prenom=None, centre=None):
        q = "UPDATE infos SET \
        directeur_nom = '"+directeur_nom+"',\
        directeur_prenom = '" +directeur_prenom+"',\
        centre = '"+centre+"'"
        req = self.query.exec_(q)
        print("set-infos", q, req)

    def get_infos(self):
        q= "SELECT directeur_nom, directeur_prenom, centre FROM infos"
        req = self.query.exec_(q)
        if self.query.isValid():
            while self.query.next():
                print(self.query.value(0), self.query.value(1), self.query.value(2))
                return self.query.value(0), self.query.value(1), self.value(2)
        else:
            return " ", " ", " "
    
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

if '__main__' == __name__:
    m = Model()
    m.create_db('aa.db')
    
