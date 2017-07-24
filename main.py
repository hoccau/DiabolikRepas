#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Diabolik Repas
Logiciel d'économat léger pour centre de vacances
"""

import logging
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, qApp, QAction, QInputDialog, QMessageBox, 
    QFileDialog)
from PyQt5.QtCore import QSettings, QMimeDatabase
from model import Model
from views import (
    ProductForm, RepasForm, InfosCentreDialog, RapportDialog, Previsionnel, 
    DatesRangeDialog, InputsArray, MainWidget, DateDialog, AllProducts, 
    FournisseurForm)
import repas_xml_to_db
import repas_db_to_xml

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

VERSION = "0.0.9"

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
        self.db_actions['exportPdfListeAction'] = self.add_action(
            '&Liste des courses', self.export_pdf_liste)
        self.db_actions['exportPdfMenuAction'] = self.add_action(
            '&Menus', self.export_pdf_menu)
        self.db_actions['exportPdfStockAction'] = self.add_action(
            '&Stock', self.export_pdf_stock)
        self.db_actions['exportPdfPriceAction'] = self.add_action(
            '&Prix de journée', self.export_pdf_price)
        self.db_actions['exportPdfPrevisionnelAction'] = self.add_action(
            '&Prévisionnel', self.export_pdf_previsionnel)
        self.db_actions['delRowAction'] = self.add_action(
            '&Supprimer la ligne', self.remove_current_row, 'Del')
        self.db_actions['addFormAction'] = self.add_action(
            '&Denrées', self.add_input)
        self.db_actions['addFournisseurAction'] = self.add_action(
            '&Fournisseur', self.add_fournisseur)
        self.db_actions['addRepasAction'] = self.add_action(
            'Repas', self.add_repas)
        self.db_actions['addProductAction'] = self.add_action(
            'Produit', self.add_product)
        self.db_actions['setInfosAction'] = self.add_action(
            'Editer les infos du centre', self.set_infos)
        self.db_actions['ViewRapportAction'] = self.add_action(
            'Rapport', self.viewRapport)
        self.db_actions['editRepasPrevAction'] = self.add_action(
            'Previsionnel', self.add_previsionnel)
        self.db_actions['editProductsAction'] = self.add_action(
            'Produits', self.edit_products)
        self.db_actions['import_previsionnel'] = self.add_action(
            'Importer un prévisionnel', self.import_xml_repas)
        self.db_actions['export_previsionnel'] = self.add_action(
            'Exporter le prévisonnel', self.export_xml_repas)
        self.db_actions['close'] = self.add_action(
            'Fermer', self.close_db, 'Ctrl+W')

        file_menu = menubar.addMenu('&Fichier')
        file_menu.addAction(newAction)
        file_menu.addAction(openAction)
        file_menu.addAction(self.db_actions['close'])
        file_menu.addAction(self.db_actions['import_previsionnel'])
        file_menu.addAction(self.db_actions['export_previsionnel'])
        export_menu = file_menu.addMenu('&Exporter en PDF')
        export_menu.addAction(self.db_actions['exportPdfListeAction'])
        export_menu.addAction(self.db_actions['exportPdfMenuAction'])
        export_menu.addAction(self.db_actions['exportPdfStockAction'])
        export_menu.addAction(self.db_actions['exportPdfPrevisionnelAction'])
        export_menu.addAction(self.db_actions['exportPdfPriceAction'])
        file_menu.addAction(exitAction)
        edit_menu = menubar.addMenu('&Édition')
        edit_menu.addAction(self.db_actions['delRowAction'])
        edit_menu.addAction(self.db_actions['setInfosAction'])
        edit_menu.addAction(self.db_actions['editRepasPrevAction'])
        edit_menu.addAction(self.db_actions['editProductsAction'])
        view_menu = menubar.addMenu('&Vue')
        view_menu.addAction(self.db_actions['ViewRapportAction'])
        addMenu = menubar.addMenu('&Ajouter')
        addMenu.addAction(self.db_actions['addFormAction'])
        addMenu.addAction(self.db_actions['addProductAction'])
        addMenu.addAction(self.db_actions['addFournisseurAction'])
        addMenu.addAction(self.db_actions['addRepasAction'])
        helpmenu = menubar.addMenu('&Aide')
        helpmenu.addAction(aboutAction)

        self.statusBar().showMessage('')
        self.setMinimumSize(850, 300)
        self.show()
        
        self.enable_db_actions(False) #disabled by default
        self.model = Model(self)
        self.retrieve_db()
        
    def _create_main_view(self):
        self.main_widget = MainWidget(self)
        self.setCentralWidget(self.main_widget)

    def add_action(self, name, function_name, shortcut=None):
        action = QAction(name, self)
        if shortcut:
            action.setShortcut(shortcut)
        action.triggered.connect(function_name)
        return action

    def current_tab_changed(self):
        logging.info('current tab: ' + str(self.main_widget.tabs.currentIndex()))
        if self.main_widget.tabs.currentIndex() in (1, 2):
            self.db_actions['delRowAction'].setEnabled(True)
        else:
            self.db_actions['delRowAction'].setEnabled(False)

    def viewRapport(self):
        RapportDialog(self)

    def remove_current_row(self):
        current_table_widget = self.main_widget.tabs.currentWidget()
        select = current_table_widget.selectionModel()
        row = select.currentIndex().row()
        if row != -1:
            reponse = QMessageBox.question(
                None, 'Sûr(e) ?', "Vous allez détruire définitivement "\
                + "les données. Êtes-vous sûr(e) ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
            if reponse == QMessageBox.Yes:
                removed = current_table_widget.model().removeRow(row)
                self.model.qt_table_inputs.submitAll()
                self.model.qt_table_repas.submitAll()
                if not removed:
                    message = 'Suppression échouée.'
                    logging.warning(message)
                    QMessageBox.warning(self, 'Erreur', message)
        else:
            QMessageBox.warning(
                self, 'Erreur', "Veuillez d'abord sélectionner une ligne "\
                + "dans le tableau ci-dessous.")

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
            self.model.qt_table_repas.removeRow(row)
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
            self.model.qt_table_inputs.removeRow(row)

    def enable_db_actions(self, toggle=True):
        for name, action in self.db_actions.items():
            action.setEnabled(toggle)

    def connect_db(self, db_path):
        mime_db = QMimeDatabase()
        mime = mime_db.mimeTypeForFile(db_path)
        if mime.name() != 'application/x-sqlite3':
            logging.warning("Mauvais format de fichier: " + str(mime.name))
            QMessageBox.warning(self, "Erreur", "Mauvais format de fichier")
            return False
        else:
            self.model.connect_db(db_path)
            self.config.setValue("lastdbpath", db_path)
            self.statusBar().showMessage('Connecté sur ' + db_path)
            self._create_main_view()
            self.enable_db_actions(True)
            self.current_tab_changed() # to enable / disable remove action
            return True

    def create_new_db(self):
        if self.model.db.isOpen():
            self.close_db()
        db_name = self.input_db_name()
        if not db_name:
            return False
        if db_name:
            user_path = os.path.expanduser('~')
            user_folder_name = "DiabolikRepas"
            if not os.path.isdir(os.path.join(user_path, user_folder_name)):
                os.mkdir(os.path.join(user_path, user_folder_name))
            path = os.path.join(user_path, user_folder_name, db_name)
        created = self.model.create_db(path)
        if created:
            self.connect_db(path)
            infos_centre = InfosCentreDialog(self)
            infos_centre.periodes_infos_model.insertRow(
                infos_centre.periodes_infos_model.rowCount())
            #self.import_all_xml_default()

    def open_db(self):
        file_name = QFileDialog.getOpenFileName(
            self, 'Ouvrir un fichier', '', "Bases de données (*.db)")
        if file_name[0]:
            if self.model.db.isOpen():
                self.close_db()
            self.connect_db(file_name[0])

    def close_db(self):
        self.model.db.close()
        self.main_widget.close()
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
        name, ok = QInputDialog.getText(
            self, 'Input Dialog', 'Entrez le nom de la base:')
        if ok and name != "":
            if name.split('.')[-1] != 'db':
                name = name + '.db'
            return name

    def set_infos(self):
        InfosCentreDialog(self)

    def add_input(self):
        InputsArray(self, self.model.qt_table_inputs)

    def add_product(self):
        self.product_form = ProductForm(self)
    
    def add_fournisseur(self):
        FournisseurForm(self)

    def add_repas(self):
        self.repas_window = RepasForm(self)

    def add_previsionnel(self):
        self.prev_window = Previsionnel(self)

    def edit_repas(self, index):
        row = index.row()
        if row != -1:
            #id_ = self.tabs.currentWidget().model().record(row).value(0)
            #index = index.model().index(row, 0)
            logging.debug(index.row())
            self.repas_window = RepasForm(self, index=index)

    def edit_products(self):
        AllProducts(self)

    def export_pdf_liste(self):
        date_start, date_stop = DatesRangeDialog(self).get_dates()
        filename, _format = QFileDialog.getSaveFileName(
            self, "Exporter la liste des courses", None, 'PDF(*.pdf)')
        if filename:
            if filename[-4:] != '.pdf':
                filename += '.pdf'
            from export import liste
            liste.create_pdf(filename, self.model, date_start, date_stop)

    def export_pdf_stock(self):
        filename, _format = QFileDialog.getSaveFileName(
            self, "Exporter le stock", None, 'PDF(*.pdf)')
        if filename:
            if filename[-4:] != '.pdf':
                filename += '.pdf'
            from export import stock
            stock.create_pdf(filename, self.model)

    def export_pdf_menu(self):
        date_start, date_stop = DatesRangeDialog(self).get_dates()
        filename, _format = QFileDialog.getSaveFileName(
            self, "Exporter le menu", None, 'PDF(*.pdf)')
        if filename:
            if filename[-4:] != '.pdf':
                filename += '.pdf'
            from export import menu
            menu.create_pdf(filename, self.model, date_start, date_stop)

    def export_pdf_price(self):
        date = DateDialog(self).get_date()
        filename, _format = QFileDialog.getSaveFileName(
            self, "Exporter le prix de journée", None, 'PDF(*.pdf)')
        if filename:
            if filename[-4:] != '.pdf':
                filename += '.pdf'
            from export import price
            res = price.create_pdf(filename, self.model, date)
            if not res[0]:
                QMessageBox.warning(self, 'Erreur', res[1])
            
    def export_pdf_previsionnel(self):
        filename, _format = QFileDialog.getSaveFileName(
            self, "Exporter le prévisionnel en PDF", None, 'PDF(*.pdf)')
        if filename:
            if filename[-4:] != '.pdf':
                filename += '.pdf'
            from export import previsionnel
            previsionnel.create_pdf(filename, self.model)

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
        self.model.delete_all_previsionnel()
        default_path = './repas_previsionnels/diabolo/'
        repas_files = os.listdir(default_path)
        for repas in repas_files:
            repas = repas_xml_to_db.Repas(os.path.join(default_path, repas))
            repas.xml_to_db(model=self.model)

    def import_xml_repas(self):
        file_name = QFileDialog.getOpenFileName(
            self, 'Ouvrir un prévisionnel', '', "Repas XML (*.xml)")
        if file_name[0]:
            repas = repas_xml_to_db.Repas(file_name[0])
            repas.xml_to_db(model=self.model)

    def export_xml_repas(self):
        filename, _format = QFileDialog.getSaveFileName(
            self, 'Exporter un prévisionnel', '', "Repas XML (*.xml)")
        if filename:
            if filename[-4:] != '.xml':
                filename += '.xml'
            repas = repas_db_to_xml.CreateXml(self.model)
            repas.write_file(filename)

    def about_d(self):
        QMessageBox.information(self, "Diabolik Repas", "version " + VERSION)

if __name__ == '__main__':
    import sys, os

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(
        logging.Formatter('%(levelname)s::%(module)s:%(lineno)d :: %(message)s'))
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(stdout_handler)

    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec_())
