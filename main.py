#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Diabolik Repas
Logiciel d'économat léger pour centre de vacances
"""

from PyQt5 import QtSql
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSettings, QMimeDatabase
from PyQt5.QtSql import QSqlRelationalDelegate
from model import Model
from views import *
import repas_xml_to_db

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.config = QSettings("Kidivid", "DiabolikRepas")
        self.initUI()

    def initUI(self):

        menubar = self.menuBar()
        self.setWindowTitle("Diabolik Repas")

        exitAction = self.add_action('&Quitter', qApp.quit, 'Ctrl+Q')
        newAction = self.add_action('&Nouveau', self.create_new_db, 'Ctrl+N')
        openAction = self.add_action('&Ouvrir', self.open_db, 'Ctrl+O')
        aboutAction = self.add_action('&à propos', self.about_d)
        
        self.db_actions = {}
        self.db_actions['exportPdfAction'] = self.add_action(
            '&Exporter la liste des courses', self.export_pdf)
        self.db_actions['delRowAction'] = self.add_action(
            '&Supprimer la ligne', self.remove_current_row)
        self.db_actions['addFormAction'] = self.add_action(
            '&Denrées', self.add_input)
        self.db_actions['addFournisseurAction'] = self.add_action(
            '&Fournisseur', self.add_fournisseur)
        self.db_actions['addRepasAction'] = self.add_action(
            'Repas', self.add_repas)
        self.db_actions['addProductAction'] = self.add_action(
            'Produit', self.add_product)
        self.db_actions['editRepasAction'] = self.add_action(
            'Repas', self.edit_repas)
        self.db_actions['setInfosAction'] = self.add_action(
            'Editer les infos du centre', self.set_infos)
        self.db_actions['ViewRapportAction'] = self.add_action(
            'Rapport', self.viewRapport)
        self.db_actions['editRepasPrevAction'] = self.add_action(
            'Previsionnel', self.add_previsionnel)
        self.db_actions['import_previsionnel'] = self.add_action(
            'Importer un repas prévisionnel', self.import_xml_repas)
        self.db_actions['init_prev'] = self.add_action(
            'Réinitialiser le prévisonnel', self.init_prev_by_xml_repas)
        self.db_actions['close'] = self.add_action(
            'Fermer', self.close_db, 'Ctrl+W')

        fileMenu = menubar.addMenu('&Fichier')
        fileMenu.addAction(newAction)
        fileMenu.addAction(openAction)
        fileMenu.addAction(self.db_actions['close'])
        fileMenu.addAction(self.db_actions['import_previsionnel'])
        fileMenu.addAction(self.db_actions['init_prev'])
        fileMenu.addAction(self.db_actions['exportPdfAction'])
        fileMenu.addAction(exitAction)
        edit_menu = menubar.addMenu('&Édition')
        edit_menu.addAction(self.db_actions['delRowAction'])
        edit_menu.addAction(self.db_actions['setInfosAction'])
        edit_menu.addAction(self.db_actions['editRepasAction'])
        edit_menu.addAction(self.db_actions['editRepasPrevAction'])
        view_menu = menubar.addMenu('&Vue')
        view_menu.addAction(self.db_actions['ViewRapportAction'])
        addMenu = menubar.addMenu('&Ajouter')
        addMenu.addAction(self.db_actions['addFormAction'])
        addMenu.addAction(self.db_actions['addProductAction'])
        addMenu.addAction(self.db_actions['addFournisseurAction'])
        addMenu.addAction(self.db_actions['addRepasAction'])
        helpmenu = menubar.addMenu('&Aide')
        helpmenu.addAction(aboutAction)

        self.statusBar().showMessage('Ready')
        self.setMinimumSize(850,300)
        self.show()
        
        self.model = Model(self)
        self.retrieve_db()
        
        self.tabs = QTabWidget()
        self.tables = {
            'reserve': self._add_table_model(self.model.qt_table_reserve, 'reserve'),
            'repas': self._add_table_model(self.model.qt_table_repas, 'repas consommés'),
            'arrivages': self._add_table_model(self.model.qt_table_inputs, 'arrivages'),
            'sorties': self._add_table_model(self.model.qt_table_outputs, 'sorties')
            }
        self.tabs.addTab(PrevisionnelColumnView(self), 'Prévisionnel')
        
        # Repas table must be selected by row for editing
        self.tables['repas'].setSelectionBehavior(QAbstractItemView.SelectRows)
        # Autorize Edit for 'arrivages'
        self.tables['arrivages'].setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tables['arrivages'].setItemDelegateForColumn(2, DateDelegate())
        self.setCentralWidget(self.tabs)

    def _add_table_model(self, model, name, size=None):
        table = QTableView(self)
        table.setModel(model)
        table.setItemDelegate(QSqlRelationalDelegate())
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabs.addTab(table, name)
        return table

    def add_action(self, name, function_name, shortcut=None):
        action = QAction(name, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(function_name)
        return action

    def viewRapport(self):
        RapportDialog(self)

    def remove_current_row(self):
        #current_table = self.tabs.currentWidget().model().tableName()
        current_tab = self.tabs.currentIndex()
        select = self.tabs.currentWidget().selectionModel()
        row = select.currentIndex().row()
        if row != -1:
            if current_tab == 1:
                self.remove_repas(row)
            elif current_tab == 2:
                self.remove_input(row)
            else:
                print(current_tab)

    def remove_repas(self, row):
        reponse = QMessageBox.question(
            None,
            'Sûr(e)?',
            'Vous êtes sur le point de supprimer définitivement un'\
             +" repas. Êtes-vous sûr(e) ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
            )
        if reponse == QMessageBox.Yes:
            good = self.model.qt_table_repas.removeRow(row)
            self.model.qt_table_repas.select()
            self.model.qt_table_outputs.select()

    def remove_input(self, row):
        reponse = QMessageBox.question(
            None,
            'Sûr(e)?',
            'Vous êtes sur le point de supprimer définitivement un'\
             +" arrivage de denrée. Êtes-vous sûr(e) ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
            )
        if reponse == QMessageBox.Yes:
            good = self.model.qt_table_inputs.removeRow(row)

    def enable_db_actions(self, toggle=True):
        for name, action in self.db_actions.items():
            action.setEnabled(toggle)

    def connect_db(self, db_path):
        mime_db = QMimeDatabase()
        mime = mime_db.mimeTypeForFile(db_path)
        if mime.name() != 'application/x-sqlite3':
            QMessageBox.warning(self, "Erreur", "Mauvais format de fichier")
            return False
        else:
            self.model.connect_db(db_path)
            self.config.setValue("lastdbpath", db_path)
            self.enable_db_actions(True)
            return True

    def create_new_db(self):
        if self.model.db.isOpen():
            self.close_db()
        db_name = self.input_db_name()
        if db_name:
            user_path = os.path.expanduser('~')
            user_folder_name = "DiabolikRepas"
            if not os.path.isdir(os.path.join(user_path, user_folder_name)):
                os.mkdir(os.path.join(user_path, user_folder_name))
            path = os.path.join(user_path, user_folder_name, db_name)
        created = self.model.create_db(path)
        if created:
            self.connect_db(path)
            self.set_infos()
            self.import_all_xml_default()

    def open_db(self):
        file_name = QFileDialog.getOpenFileName(
            self, 'Ouvrir un fichier', '', "Bases de données (*.db)")
        if file_name[0]:
            if self.model.db.isOpen():
                self.close_db()
            self.connect_db(file_name[0])

    def close_db(self):
        self.model.db.close()
        self.enable_db_actions(False)

    def retrieve_db(self):
        path = self.config.value("lastdbpath")
        if path:
            if os.path.exists(path):
                self.connect_db(path)
        else:
            reponse = QMessageBox.question(
                None,
                'message',
                'Pas de base de données trouvée. Faut-il en créer une nouvelle ?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
                )
            if reponse == QMessageBox.Yes:
                self.create_new_db()
            if reponse == QMessageBox.No:
                return False

    def input_db_name(self):
        name, ok = QInputDialog.getText(self, 'Input Dialog', 
            'Entrez le nom de la base:')
        if ok and name != "":
            if name.split('.')[-1] != 'db':
                name = name + '.db'
            return name

    def set_infos(self):
        InfosCentreDialog(self)

    def add_input(self):
        self.form = InputForm(self)

    def add_product(self):
        self.product_form = ProductForm(self)
    
    def add_repas(self):
        self.repas_window = RepasForm(self)

    def add_previsionnel(self):
        self.prev_window = Previsionnel(self)

    def edit_repas(self):
        current_table =  self.tabs.currentWidget().model().tableName()
        if current_table == 'repas':
            select = self.tabs.currentWidget().selectionModel()
            row = select.currentIndex().row()
            if row != -1:
                id_ = self.tabs.currentWidget().model().record(row).value(0)
                self.repas_window = RepasForm(self, id_)
            else:
                QMessageBox.warning(
                    self,
                    "Erreur", "Veuillez sélectionner un repas dans le tableau."
                    )
        else:
            QMessageBox.warning(
                self,
                "Erreur", 'Veuillez sélectionner un repas dans l\'onglet "repas".'
            )

    def add_outputs(self, repas_id=None):
        self.output_view = OutputForm(self, repas_id)

    def add_fournisseur(self):
        name, ok = QInputDialog.getText(self, 'Ajouter un fournisseur',
            'Nom du fournisseur:')
        if ok and name != "":
            res = self.model.add_fournisseur(name)
            if res:
                return True
            elif res == "UNIQUE constraint failed: fournisseurs.NOM":
                QMessageBox.warning(self, "Erreur", "Ce nom existe déjà.")
            else:
                QMessageBox.warning(self, "Erreur", "Erreur de requette inconnue!")

    def export_pdf(self):
        date_start, date_stop = DatesRangeDialog(self).get_dates()
        filename, _format = QFileDialog.getSaveFileName(
            self, "Exporter la liste des courses", None, 'PDF(*.pdf)')
        if filename:
            if filename[-4:] != '.pdf':
                filename += '.pdf'
            import export_pdf
            export_pdf.create_pdf(filename, self.model, date_start, date_stop)

    def init_prev_by_xml_repas(self):
        reponse = QMessageBox.question(
            None,
            'Réinitialiser le prévisionnel?',
            'Vous allez effacer tout le prévisionnel existant. Êtes-vous sûr(e) ?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
            )
        if reponse == QMessageBox.Yes:
            self.import_all_xml_default()

    def import_all_xml_default(self):
        default_path = './repas_previsionnels/diabolo/'
        repas_files = os.listdir(default_path)
        for repas in repas_files:
            repas = repas_xml_to_db.Repas(os.path.join(default_path, repas))
            repas.xml_to_db(model=self.model)

    def import_xml_repas(self):
        file_name = QFileDialog.getOpenFileName(
            self, 'Ouvrir un repas', '', "Repas XML (*.xml)")
        if file_name[0]:
            repas = repas_xml_to_db.Repas(file_name[0])
            repas.xml_to_db(model=self.model)

    def about_d(self):
        QMessageBox.information(self, "Diabolik Repas", "version 0.0.1")

if __name__ == '__main__':
    import sys, os
    
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
