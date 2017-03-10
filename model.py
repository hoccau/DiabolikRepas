#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from PyQt5.QtSql import QSqlQueryModel, QSqlDatabase, QSqlQuery, QSqlRelationalTableModel, QSqlRelation, QSqlTableModel
from PyQt5.QtCore import Qt

DEBUG_SQL = True

class Model(QSqlQueryModel):
    def __init__(self, parent=None):
        super(Model, self).__init__(parent)

        self.db = QSqlDatabase.addDatabase('QSQLITE')

    def create_db(self, db_name):
        self.connect_db(db_name)
        self.exec_("CREATE TABLE infos(\
        centre varchar(20),\
        directeur_nom varchar(20),\
        nombre_enfants int,\
        place varchar(20),\
        startdate varchar(10),\
        enddate varchar(10)\
        )")
        self.exec_("INSERT INTO infos(\
        centre, directeur_nom, nombre_enfants, place, startdate, enddate) VALUES (\
        NULL, NULL, NULL, NULL, NULL, NULL)")
        self.exec_("CREATE TABLE fournisseurs(\
        id integer PRIMARY KEY,\
        NOM varchar(20)\
        )")
        req = self.exec_("CREATE TABLE reserve(\
        id integer PRIMARY KEY,\
        Fournisseur_id integer NOT NULL,\
        Date varchar(10),\
        Product varchar(20),\
        Prix real NOT NULL,\
        start_quantity real NOT NULL,\
        quantity real NOT NULL,\
        unit_id integer NOT NULL,\
        FOREIGN KEY (unit_id) REFERENCES units(id)\
        FOREIGN KEY (Fournisseur_id) REFERENCES fournisseurs(id)\
        )")
        self.exec_("CREATE UNIQUE INDEX idx_NOM ON fournisseurs (NOM)")
        self.exec_("CREATE TABLE units(\
        id integer PRIMARY KEY,\
        unit varchar(20) NOT NULL\
        )")
        self.exec_("INSERT INTO units(unit) VALUES\
        ('unités'), ('Kilogrammes'), ('Litres')")
        self.exec_("CREATE TABLE repas(\
        id integer PRIMARY KEY,\
        date varchar(10) NOT NULL,\
        type_id integer NOT NULL,\
        comment TEXT,\
        FOREIGN KEY (type_id) REFERENCES type_repas(id)\
        )")
        self.exec_("CREATE TABLE type_repas(\
        id integer PRIMARY KEY,\
        type varchar(20)\
        )")
        repas_types = ['petit déjeuner','déjeuner','gouter','souper','cinquième','autre']
        for repas_type in repas_types:
            req = self.exec_("INSERT INTO type_repas(type) VALUES ('"\
            +repas_type+"')")
        self.exec_("CREATE TABLE outputs(\
        id integer PRIMARY KEY,\
        quantity integer,\
        repas_id integer,\
        product_id integer,\
        FOREIGN KEY (repas_id) REFERENCES repas(id)\
        FOREIGN KEY (product_id) REFERENCES reserve(id)\
        )")
        
    def exec_(self, request):
        req = self.query.exec_(request)
        if DEBUG_SQL:
            print(req,":",request)
            if req == False:
                print(self.query.lastError().databaseText())
        return req

    def connect_db(self, db_name):
        self.db.setDatabaseName(db_name)
        self.db.open()
        self.query = QSqlQuery()
        self.qt_table_reserve = QSqlRelationalTableModel(self, self.db)
        self.update_reserve_model()
        self.qt_table_infos = InfosModel(self, self.db)
        self.qt_table_repas = RepasModel(self, self.db)
        self.qt_table_outputs = OutputsModel(self, self.db)

    def update_reserve_model(self):
        self.qt_table_reserve.setTable('reserve')
        rel1 = QSqlRelation("fournisseurs","id","NOM")
        rel2 = QSqlRelation("units","id","unit")
        self.qt_table_reserve.setRelation(1, rel1)
        self.qt_table_reserve.setRelation(7, rel2)
        self.qt_table_reserve.select()
        self.qt_table_reserve.setHeaderData(0, Qt.Horizontal, "Identification")
        self.qt_table_reserve.setHeaderData(1, Qt.Horizontal, "Fournisseur")
        self.qt_table_reserve.setHeaderData(3, Qt.Horizontal, "Produit")
        self.qt_table_reserve.setHeaderData(5, Qt.Horizontal, "Quantité\nde départ")
        self.qt_table_reserve.setHeaderData(6, Qt.Horizontal, "Quantité\n actuelle")

    def get_fournisseurs(self):
        self.query.exec_("SELECT NOM, ID FROM fournisseurs")
        return self.query2dic()

    def get_product_datas(self, product):
        req = "SELECT reserve.id, quantity, prix, fournisseurs.nom\
        FROM reserve INNER JOIN fournisseurs on fournisseurs.id = reserve.Fournisseur_id\
        WHERE product = '"+product+"'"
        self.exec_(req)
        result = []
        while self.query.next():
            line = [self.query.value(x) for x in range(4)]
            result.append(line)
        return result

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
        self.exec_("SELECT outputs.id, outputs.quantity, reserve.product, product_id\
        FROM outputs INNER JOIN reserve WHERE repas_id = "+str(id_))
        datas['outputs'] = []
        while self.query.next():
            datas['outputs'].append({
                'id': self.query.value(0),
                'quantity': self.query.value(1),
                'product_name': self.query.value(2),
                'product_id': self.query.value(3)
                })
        return datas

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
        self.query.prepare(
            "INSERT INTO "+table+"("+",".join(dic.keys())+")\
            VALUES ("\
            +','.join([':'+x for x in list(dic.keys()) ])+")"
            )
        for k, v in dic.items():
            self.query.bindValue(':'+k, v)
        q = self.query.exec_()
        return q

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

    def add_fournisseur(self, name):
        req = self.query.exec_("insert into fournisseurs (nom) values('"+name+"')")
        if req == False:
            print(self.query.lastError().databaseText())
            return self.query.lastError().databaseText()
        else:
            return req

    def add_output(self, datas):
        req = "INSERT INTO outputs ('quantity', 'repas_id', 'product_id')\
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
    
    def set_line(self, datas):
        query = "INSERT INTO reserve (Fournisseur_id,  Date, Product, Prix, start_quantity, quantity, unit_id)"
        query += " VALUES "
        query += "("\
        +str(datas["fournisseur_id"])+",'"\
        +str(datas["date"])+"','"\
        +datas["product"]+"',"\
        +datas["price"]+","\
        +datas["quantity"]+','\
        +datas["quantity"]+','\
        +str(datas["unit_id"])\
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
        req = "SELECT id FROM "+table+" ORDER BY id DESC LIMIT 1"
        self.exec_(req)
        while self.query.next():
            return self.query.value(0)

class InfosModel(QSqlTableModel):
    def __init__(self, parent, db):
        super(InfosModel, self).__init__(parent, db)

        self.setTable("infos")
        self.select()

class RepasModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(RepasModel, self).__init__(parent, db)

        self.setTable("repas")
        f_rel = QSqlRelation("type_repas","id","type")
        self.setRelation(2, f_rel)
        self.select()
        self.setHeaderData(0, Qt.Horizontal, "Identification")
        self.setHeaderData(2, Qt.Horizontal, "Type")

class OutputsModel(QSqlRelationalTableModel):
    def __init__(self, parent, db):
        super(OutputsModel, self).__init__(parent, db)

        self.setTable("outputs")
        self.setRelation(2, QSqlRelation("repas","id","date"))
        self.setRelation(3, QSqlRelation("reserve","id","product"))
        self.select()
        self.setHeaderData(0, Qt.Horizontal, "Identification")
        self.setHeaderData(1, Qt.Horizontal, "Quantité")
        self.setHeaderData(2, Qt.Horizontal, "date")
        self.setHeaderData(3, Qt.Horizontal, "produit")
