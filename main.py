#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Diabolik Compta
Logiciel de comptabilité léger pour centre de vacances
"""

from PyQt5 import QtSql
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from model import Model
from views import *
from PyQt5.QtSql import QSqlRelationalDelegate

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.initUI()

    def initUI(self):

        menubar = self.menuBar()

        exitAction = self.add_action('&Quitter', qApp.quit, 'Ctrl+Q')
        openAction = self.add_action('&Ouvrir', self.open_db, 'Ctrl+O')
        delRowAction = self.add_action('&Supprimer la ligne', self.remove_current_row)
        addFormAction = self.add_action('&Ligne de comptabilité', self.addDatas)
        addFournisseurAction = self.add_action('&Fournisseur', self.addFournisseur)
        setInfosAction = self.add_action('Editer les infos du centre', self.set_infos)
        ViewRapportAction = self.add_action('Rapport', self.viewRapport)

        fileMenu = menubar.addMenu('&Fichier')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)
        edit_menu = menubar.addMenu('&Édition')
        edit_menu.addAction(delRowAction)
        edit_menu.addAction(setInfosAction)
        view_menu = menubar.addMenu('&Vue')
        view_menu.addAction(ViewRapportAction)
        addMenu = menubar.addMenu('&Ajouter')
        addMenu.addAction(addFormAction)
        addMenu.addAction(addFournisseurAction)

        self.statusBar().showMessage('Ready')
        self.setMinimumSize(850,300)
        self.show()
        
        self.model = Model(self)
        self.retrieve_db()
        self.form = Form(self)

        self.mainView = QTableView(self)
        self.mainView.setModel(self.model.qt_table_reserve)
        self.mainView.setItemDelegate(QSqlRelationalDelegate())
        self.setCentralWidget(self.mainView)

    def add_action(self, name, function_name, shortcut=None):
        action = QAction(name, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(function_name)
        return action

    def viewRapport(self):
        RapportDialog(self)

    def remove_current_row(self):
        row = self.mainView.currentIndex().row()
        model = self.mainView.currentIndex().model()
        row_id = model.index(row, 0).data()
        print("row to remove:", row)
        self.model.qt_table_reserve.removeRow(row)
        self.model.update_table_model()

    def show_row(self):
        row = self.mainView.currentIndex().row()
        model = self.mainView.currentIndex().model()
        print("id:", model.index(row,0).data(), "m2:", m2)
        print("row", row)
        
    def open_db(self):
        file_name = QFileDialog.getOpenFileName(self, 'Open File')
        if file_name[0]:
            self.model.connect_db(file_name[0])

    def retrieve_db(self):
        files = os.listdir('./')
        files = [x for x in files if x.split('.')[-1] == 'db']

        if len(files) == 1:
            QMessageBox.information(self, "Base trouvée","Base de donnée : "+files[0])
            self.model.connect_db(files[0])
        
        elif len(files) == 0:
            reponse = QMessageBox.question(
                None,
                'message',
                'Pas de base de données trouvée. Faut-il en créer une nouvelle ?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
                )
            if reponse == QMessageBox.Yes:
                db_name = self.input_db_name()
                self.model.create_db(db_name)
                self.set_infos()

            if reponse == QMessageBox.No:
                return None

        elif len(files) > 1:
            #QMessageBox.critical(None, "Plusieurs bases trouvées", "Plusieurs bases de données trouvées. Je ne sais que faire...")
            combo = QComboBox(self)
            for db_name in files:
                combo.addItem(db_name)

    def input_db_name(self):
        name, ok = QInputDialog.getText(self, 'Input Dialog', 
            'Entrez le nom de la base:')
        if ok and name != "":
            if name.split('.')[-1] != 'db':
                name = name + '.db'
            return name

    def set_infos(self):
        InfosCentreDialog(self)

    def addDatas(self):
        self.form.show()

    def addFournisseur(self):
        name, ok = QInputDialog.getText(self, 'Input Dialog',
            'Nom du fournisseur:')
        if ok and name != "":
            res = self.model.add_fournisseur(name)
            if res == True:
                self.form.refresh_fournisseurs()
                self.model.update_table_model()
            elif res == "UNIQUE constraint failed: fournisseurs.NOM":
                QMessageBox.warning(self, "Erreur", "Ce nom existe déjà.")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur de requette inconnue!")

if __name__ == '__main__':
    import sys, os
    
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
