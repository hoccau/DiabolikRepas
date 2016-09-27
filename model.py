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
        Designation varchar(20),\
        Prix real,\
        Quantite real\
        FOREIGN KEY (Fournisseur_id) REFERENCES fournisseurs(id)\
        )")
        if req == False:
            print(self.query.lastError().text())
        self.query.exec_("CREATE UNIQUE INDEX idx_NOM ON fournisseurs (NOM)")

    def connect_db(self, db_name):
        self.db.setDatabaseName(db_name)
        self.db.open()
        self.query = QSqlQuery()
        self.qt_table_reserve = QSqlRelationalTableModel(self, self.db)
        self.update_table_model()
        self.qt_table_infos = InfosModel(self, self.db)

    def update_table_model(self):
        self.qt_table_reserve.setTable('reserve')
        f_rel = QSqlRelation("fournisseurs","id","NOM")
        self.qt_table_reserve.setRelation(1, f_rel)
        self.qt_table_reserve.select()
        self.qt_table_reserve.setHeaderData(0, Qt.Horizontal, "Identification")
        self.qt_table_reserve.setHeaderData(1, Qt.Horizontal, "Fournisseur")

    def get_fournisseurs(self):
        fournisseurs = {}
        self.query.exec_("SELECT NOM, ID FROM fournisseurs")
        while self.query.next():
            fournisseurs[self.query.value(0)] = self.query.value(1)
        return fournisseurs

    def add_fournisseur(self, name):
        req = self.query.exec_("insert into fournisseurs (nom) values('"+name+"')")
        if req == False:
            print(self.query.lastError().databaseText())
            return self.query.lastError().databaseText()
        else:
            return req

    def set_line(self, datas):
        query = "INSERT INTO reserve (Fournisseur_id,  Date, Designation, Prix, Cumul, CodeCompta, TypePayement_id)"
        query += " VALUES "
        query += "("\
        +str(datas["fournisseur_id"])+",'"\
        +str(datas["date"])+"','"\
        +datas["product"]+"',"\
        +datas["price"]+","\
        +str(last_cumul + float(datas["price"]))+","\
        +str(datas["codeCompta_id"])+","\
        +str(datas["typePayement_id"])\
        +")"
        print(query)
        q = self.query.exec_(query)
        print("query success:", q)
        if q == False:
            print(self.query.lastError().databaseText())

    def get_last_id(self):
        query = "SELECT id FROM reserve ORDER BY id DESC LIMIT 1"
        self.query.exec_(query)
        while self.query.next():
            return self.query.value(0)

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
        

class InfosModel(QSqlTableModel):
    def __init__(self, parent, db):
        super(InfosModel, self).__init__(parent, db)

        self.setTable("infos")
        self.select()
