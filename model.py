#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from PyQt5.QtSql import QSqlQueryModel, QSqlDatabase, QSqlQuery, QSqlRelationalTableModel, QSqlRelation, QSqlTableModel
from PyQt5.QtCore import Qt

class Model(QSqlQueryModel):
    def __init__(self, parent=None):
        super(Model, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE')

    def create_db(self, db_name):
        self.connect_db(db_name)
        self.query.exec_("CREATE TABLE infos(\
        centre varchar(20),\
        directeur_nom varchar(20),\
        directeur_prenom varchar(20)\
        )")
        self.query.exec_("INSERT INTO infos(\
        centre, directeur_nom, directeur_prenom) VALUES (\
        NULL, NULL, NULL)")
        self.query.exec_("CREATE TABLE fournisseurs(\
        id integer PRIMARY KEY,\
        NOM varchar(20)\
        )")
        req = self.query.exec_("CREATE TABLE reserve(\
        id integer PRIMARY KEY,\
        Fournisseur_id integer NOT NULL,\
        Date varchar(10),\
        Product varchar(20),\
        Prix real NOT NULL,\
        start_quantity integer NOT NULL,\
        quantity NOT NULL,\
        FOREIGN KEY (Fournisseur_id) REFERENCES fournisseurs(id)\
        )")
        self.query.exec_("CREATE UNIQUE INDEX idx_NOM ON fournisseurs (NOM)")

        req = self.query.exec_("CREATE TABLE repas(\
        id integer PRIMARY KEY,\
        date varchar(10) NOT NULL,\
        type_id integer NOT NULL,\
        FOREIGN KEY (type_id) REFERENCES type_repas(id)\
        )")
        req = self.query.exec_("CREATE TABLE type_repas(\
        id integer PRIMARY KEY,\
        type varchar(20)\
        )")
        repas_types = ['petit déjeuner','déjeuner','gouter','souper','cinquième','autre']
        for repas_type in repas_types:
            req = self.query.exec_("INSERT INTO type_repas(type) VALUES ('"\
            +repas_type+"')")
        req = self.query.exec_("CREATE TABLE outputs(\
        id integer PRIMARY KEY,\
        quantity integer,\
        repas_id integer,\
        product_id integer,\
        FOREIGN KEY (repas_id) REFERENCES repas(id)\
        FOREIGN KEY (product_id) REFERENCES reserve(id)\
        )")
        if req == False:
            print(self.query.lastError().databaseText())

    def connect_db(self, db_name):
        self.db.setDatabaseName(db_name)
        self.db.open()
        self.query = QSqlQuery()
        self.qt_table_reserve = QSqlRelationalTableModel(self, self.db)
        self.update_table_model()
        self.qt_table_infos = InfosModel(self, self.db)
        self.qt_table_repas = RepasModel(self, self.db)

    def update_table_model(self):
        self.qt_table_reserve.setTable('reserve')
        f_rel = QSqlRelation("fournisseurs","id","NOM")
        self.qt_table_reserve.setRelation(1, f_rel)
        self.qt_table_reserve.select()
        self.qt_table_reserve.setHeaderData(0, Qt.Horizontal, "Identification")
        self.qt_table_reserve.setHeaderData(1, Qt.Horizontal, "Fournisseur")

    def get_fournisseurs(self):
        self.query.exec_("SELECT NOM, ID FROM fournisseurs")
        return self.query2dic()

    def get_product_datas(self, product):
        req = "SELECT reserve.id, quantity, prix, fournisseurs.nom\
        FROM reserve INNER JOIN fournisseurs on fournisseurs.id = reserve.Fournisseur_id\
        WHERE product = '"+product+"'"
        self.query.exec_(req)
        if req == False:
           print(req, self.query.lastError().databaseText())
        else: 
            result = []
            while self.query.next():
                line = [self.query.value(x) for x in range(4)]
                result.append(line)
            return result

    def get_quantity(self, product_id):
        self.exec_("SELECT quantity FROM reserve WHERE id = "+str(product_id))
        while self.query.next():
            return self.query.value(0)

    def get_(self, values=[], table=None, condition=None):
        sql_values = ",".join(values)
        if condition == None:
            condition = ""
        else:
            if type(condition[2]) == str:
                condition[2] = "'"+condition[2]+"'"
            condition = " WHERE "+str(condition[0])+condition[1]+condition[2]
        self.exec_("SELECT "+sql_values+" FROM "+table + condition)
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

    def get_price_by_repas(self, repas_id):
        self.exec_("SELECT prix, outputs.quantity FROM reserve\
        INNER JOIN outputs ON outputs.product_id = reserve.id\
        WHERE outputs.repas_id = "+str(repas_id))
        price = 0
        while self.query.next():
            price += self.query.value(0) * self.query.value(1)
        return price

    def get_price_by_day(self, date):
        self.exec_("SELECT prix, outputs.quantity FROM reserve\
        INNER JOIN outputs ON outputs.product_id = reserve.id\
        INNER JOIN repas ON repas.id = outputs.repas_id\
        WHERE repas.date = '"+str(date)+"'")
        price = 0
        while self.query.next():
            price += self.query.value(0) * self.query.value(1)
        return price

    def get_dates_repas(self):
        self.exec_("SELECT DISTINCT date FROM repas")
        dates = []
        while self.query.next():
            dates.append(self.query.value(0))
        return dates

    def set_(self, dic={}, table=None):
        q = "INSERT INTO "+table+"("+",".join(dic.keys())+")  VALUES('"
        q += "','".join(dic.values())+"')"
        req = self.query.exec_(q)
        if req == False:
            print(q, self.query.lastError().databaseText())
        else:
            print(q, "success!")
        return req

    def add_fournisseur(self, name):
        req = self.query.exec_("insert into fournisseurs (nom) values('"+name+"')")
        if req == False:
            print(self.query.lastError().databaseText())
            return self.query.lastError().databaseText()
        else:
            return req

    def add_output(self, datas):
        req = "INSERT INTO outputs ("\
        +','.join(datas.keys())+") VALUES("\
        +','.join([str(x) for x in list(datas.values())])+')'
        self.exec_(req)
        new_quantity = self.get_quantity(datas['product_id']) - datas['quantity']
        self.exec_("UPDATE reserve SET quantity = "+str(new_quantity)\
        +" WHERE id = "+str(datas['product_id']))
    
    def exec_(self, request):
        print(request)
        req = self.query.exec_(request)
        if not req:
            print(self.query.lastError().databaseText())

    def set_line(self, datas):
        query = "INSERT INTO reserve (Fournisseur_id,  Date, Product, Prix, start_quantity, quantity)"
        query += " VALUES "
        query += "("\
        +str(datas["fournisseur_id"])+",'"\
        +str(datas["date"])+"','"\
        +datas["product"]+"',"\
        +datas["price"]+","\
        +datas["quantity"]+','\
        +datas["quantity"]\
        +")"
        self.exec_(query)

    def add_repas(self, datas):
        req = self.query.exec_("INSERT INTO repas(date, type) VALUES("\
        +datas['date']+","+datas['type']+')')
        if req == False:
            print(self.query.lastError().databaseText())

    def query2dic(self):
        dic = {}
        while self.query.next():
            dic[self.query.value(0)] = self.query.value(1)
        return dic

    def get_total(self):
        self.query.exec_("SELECT sum(prix) FROM reserve")
        while self.query.next():
            return self.query.value(0)

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

    def get_last_id(self, table):
        req = "SELECT DISTINCT last_insert_rowid() FROM "+table
        self.exec_(req)
        while self.query.next():
            return self.query.value(0)

class InfosModel(QSqlTableModel):
    def __init__(self, parent, db):
        super(InfosModel, self).__init__(parent, db)

        self.setTable("infos")
        self.select()

class RepasModel(QSqlTableModel):
    def __init__(self, parent, db):
        super(RepasModel, self).__init__(parent, db)

        self.setTable("repas")
        self.select()
