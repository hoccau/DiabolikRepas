#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from PyQt5.QtWidgets import (
    QWidget, QDialog, QGroupBox, QStyledItemDelegate, QGridLayout, QPushButton,
    QCalendarWidget, QTableView, QComboBox, QTextEdit, QLabel, QVBoxLayout,
    QHBoxLayout, QCompleter, QDoubleSpinBox, QButtonGroup, QLineEdit, 
    QFormLayout, QDataWidgetMapper, QDialogButtonBox, QMessageBox, QDateEdit,
    QAbstractItemView, QTabWidget)
from PyQt5.QtCore import QRegExp, QDate, Qt, QStringListModel, QSize, QByteArray
from PyQt5.QtGui import QRegExpValidator, QPen, QPalette, QIcon
from PyQt5.QtSql import QSqlRelationalDelegate
import logging

class MainWidget(QWidget):
    def __init__(self, parent):
        super(MainWidget, self).__init__(parent)
        
        self.parent = parent
        self.buttons = BigButtons(parent)
        self._create_tables_views()
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.buttons)
        main_layout.addWidget(self.tabs)

        self.setLayout(main_layout)
    
    def _create_tables_views(self):
        self.tabs = QTabWidget()
        self.tables = {
            'reserve': self._add_table_model(
                self.parent.model.qt_table_reserve, 'reserve'),
            'arrivages': self._add_table_model(
                self.parent.model.qt_table_inputs, 'arrivages'),
            'repas': self._add_table_model(
                self.parent.model.qt_table_repas, 'repas consommés')
            }
        #self.tabs.addTab(PrevisionnelColumnView(self), 'Prévisionnel')
        self.tabs.currentChanged.connect(self.parent.current_tab_changed)
        
        # Repas table must be selected by row for editing
        self.tables['repas'].setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tables['repas'].doubleClicked.connect(self.parent.edit_repas)
        self.tables['repas'].hideColumn(3) # hide repas_prev_id (not used...)
        date_delegate = DateDelegate(self)
        self.tables['repas'].setItemDelegateForColumn(1, date_delegate)
        # Autorize Edit for 'arrivages'
        self.tables['arrivages'].setEditTriggers(QAbstractItemView.DoubleClicked)
        self.tables['arrivages'].setItemDelegateForColumn(2, DateDelegate())
    
    def _add_table_model(self, model, name, size=None):
        table = QTableView(self)
        table.setModel(model)
        table.setItemDelegate(QSqlRelationalDelegate())
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSortingEnabled(True)
        self.tabs.addTab(table, name)
        return table

class BigButtons(QWidget):
    def __init__(self, parent):
        super(BigButtons, self).__init__(parent)
        
        self.layout = QHBoxLayout()

        products_button = self._create_button('products.png', 'Produits')
        previsionnel_button = self._create_button(
            'previsionnel.png', 'Prévisionnel')
        input_button = self._create_button('input.png', 'Arrivage de denrées')
        output_button = self._create_button('output.png', 'Repas')
        
        self.setLayout(self.layout)

        previsionnel_button.clicked.connect(parent.add_previsionnel)
        input_button.clicked.connect(parent.add_input)
        output_button.clicked.connect(parent.add_repas)
        products_button.clicked.connect(parent.edit_products)

    def _create_button(self, image, text):
        button = QPushButton()
        button.setIcon(QIcon('images/'+image))
        button.setIconSize(QSize(100, 100))
        button.setText(text)
        self.layout.addWidget(button)
        return button

class AllProducts(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.view = QTableView(self)
        self.model = parent.model.qt_table_products
        self.view.setModel(self.model)
        sql_delegate = QSqlRelationalDelegate(self.view)
        self.view.setItemDelegate(sql_delegate)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.doubleClicked.connect(self.edit_product)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.add_button = QPushButton('Nouveau')
        close_button = QPushButton('Fermer')

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(close_button)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

        close_button.clicked.connect(self.close)
        self.add_button.clicked.connect(parent.add_product)
        
        self.view.horizontalHeader().setMinimumHeight(50)
        self.resize(642, 376)

        self.exec_()
        
    def reject(self):
        self.model.revertAll()
        super().reject()

    def add_product(self):
        ProductForm(self.parent)

    def edit_product(self, index):
        ProductForm(self.parent, index.row())

class Form(QDialog):
    """Abstract class"""
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.parent = parent
        self.model = parent.model
        self.grid = QGridLayout()
        self.field_index = 0
        self.submitButton = QPushButton("Enregistrer")
        self.quitButton = QPushButton("Fermer")
        
    def add_field(self, label_name, widget):
        self.field_index += 1
        self.grid.addWidget(QLabel(label_name), self.field_index, 0)
        self.grid.addWidget(widget, self.field_index, 1)

    def add_layout(self, label_name, layout):
        self.field_index += 1
        self.grid.addWidget(QLabel(label_name), self.field_index, 0)
        self.grid.addLayout(layout, self.field_index, 1)

    def initUI(self):
        self.field_index += 1
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.submitButton)
        buttons_layout.addWidget(self.quitButton)
        self.grid.addLayout(buttons_layout, 100, 1) #100 means at the end
        self.setLayout(self.grid)
        self.submitButton.clicked.connect(self.submit_datas)
        self.quitButton.clicked.connect(self.reject)
        self.show()
    
    def resizeEvent(self, size):
        pass
        #logging.debug(size.size())


class ProductForm(QDialog):
    def __init__(self, parent=None, index=None, name=""):
        super(ProductForm, self).__init__(parent)
        self.model = parent.model.qt_table_products

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.model)

        self.warning_label = QLabel(
            "Assurez-vous que le produit que vous allez entrer\n"
            +" n'existe pas déjà sous un autre nom.")
        self.name = QLineEdit()
        self.name.setToolTip("Avec les accents, en minuscule")
        self.units = QComboBox()
        self.units_model = self.model.relationModel(2)
        self.units.setModel(self.units_model)
        self.units.setModelColumn(1)
        self.recommends = [QDoubleSpinBox() for i in range(3)]
        [spin.setMaximum(999) for spin in self.recommends]
        self.fournisseur = QComboBox()
        fournisseur_model = parent.model.qt_table_fournisseurs
        self.fournisseur.setModel(fournisseur_model)
        self.fournisseur.setModelColumn(1)

        add_fournisseur = QPushButton('+')
        self.ok_button = QPushButton('OK')
        self.cancel_button = QPushButton('Annuler')
        
        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.name, 1)
        self.mapper.addMapping(self.units, 2)
        self.mapper.addMapping(self.recommends[0], 3)
        self.mapper.addMapping(self.recommends[1], 4)
        self.mapper.addMapping(self.recommends[2], 5)
        self.mapper.addMapping(self.fournisseur, 6)
        
        for widget in [self.name, self.units] + self.recommends:
            if self.mapper.mappedSection(widget) == -1:
                logging.warning('Widget ' + str(widget) + 'not mapped.')
        
        if index is not None:
            self.mapper.setCurrentIndex(index)
        else:
            inserted = self.model.insertRow(self.model.rowCount())
            if not inserted:
                logging.warning(
                    'Row not inserted in model {0}'.format(self.model))
            self.mapper.toLast()
            self.name.setText(name)
        
        layout = QFormLayout()
        layout.addRow('Nom du produit', self.name)
        layout.addRow('Unité de mesure', self.units)
        recommend_layout = QGridLayout()
        recommends_box = QGroupBox()
        recommends_box.setTitle('Quantités recommandées')
        recommend_layout.addWidget(
            QLabel('Pour un enfant de moins de 6 ans'),
            0, 0)
        recommend_layout.addWidget(self.recommends[0], 0, 1)
        recommend_layout.addWidget(
            QLabel('Pour un enfant entre 6 et 12 ans'),
            1, 0)
        recommend_layout.addWidget(self.recommends[1], 1, 1)
        recommend_layout.addWidget(
            QLabel('Pour un enfant de plus de 12 ans (ou adulte)'),
            2, 0)
        recommend_layout.addWidget(self.recommends[2], 2, 1)
        self.units_labels = [QLabel('Pièces') for x in range(3)]
        [recommend_layout.addWidget(label, x, 2)\
            for x, label in enumerate(self.units_labels)]
        recommends_box.setLayout(recommend_layout)
        g_layout = QVBoxLayout()
        g_layout.addWidget(self.warning_label)
        g_layout.addLayout(layout)
        g_layout.addWidget(recommends_box)
        fournisseur_layout = QHBoxLayout()
        fournisseur_layout.addWidget(QLabel("Fournisseur par défaut"))
        fournisseur_layout.addWidget(self.fournisseur, 2)
        fournisseur_layout.addWidget(add_fournisseur)
        g_layout.addLayout(fournisseur_layout)
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        g_layout.addLayout(button_layout)
        self.setLayout(g_layout)
        
        self.units.currentTextChanged.connect(self.change_units)
        add_fournisseur.clicked.connect(parent.add_fournisseur)
        self.ok_button.clicked.connect(self.submit)
        self.cancel_button.clicked.connect(self.close)

        self.exec_()

    def submit(self):
        mapper_submited = self.mapper.submit() # to init widget default value
        model_submited = self.model.submitAll()
        if model_submited:
            logging.info('Produit ' + self.name.text() + ' ajouté.')
            self.accept()
            return self.name.text()
        else:
            error = self.model.lastError()
            logging.warning(error.text())
            if error.databaseText() == 'UNIQUE constraint failed: products.name':
                QMessageBox.warning(
                      self, "Erreur", "Ce produit existe déjà")
            else:
                QMessageBox.warning(
                    self, "Erreur", "Le produit n'a pas pu être enregistré.\n"\
                    + "Détail:" + error.text())

    def reject(self):
        self.model.revertAll()
        super().reject()
    
    def change_units(self, unit):
        matching = {
           'Unités':'pièces',
           'Kilogrammes':'grammes',
           'Litres':'millilitres'
           }
        [label.setText(matching[unit]) for label in self.units_labels]

class FournisseurForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.model = parent.model.qt_table_fournisseurs
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.model)

        self.name = QLineEdit()
        
        self.ok_button = QPushButton('OK')
        self.cancel_button = QPushButton('Annuler')

        self.mapper.addMapping(self.name, 1)
        inserted = self.model.insertRow(self.model.rowCount())
        self.mapper.toLast()

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout = QVBoxLayout()
        layout.addWidget(self.name)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.ok_button.clicked.connect(self.submit)
        self.cancel_button.clicked.connect(self.close)

        self.exec_()

    def submit(self):
        self.mapper.submit()
        submited = self.model.submitAll()
        if submited:
            self.close()
        if not submited:
            error = self.model.lastError()
            
            logging.warning(error.text())
            logging.warning(error.nativeErrorCode())
            if error.nativeErrorCode() == "19":
                QMessageBox.warning(self, "Erreur", "Ce nom semble déjà exister.")
            else:
                QMessageBox.warning(self, "Erreur", error.text())

    def reject(self):
        self.model.revertAll()
        super().reject()

class InputForm(Form):
    def __init__(self, parent=None):
        super(InputForm, self).__init__(parent)

        self.setWindowTitle("Denrées")
        self.all_products_names = parent.model.get_all_products_names()

        self.fournisseur = QComboBox()
        add_fournisseur = QPushButton('Ajouter')
        self.refresh_fournisseurs()
        self.product = QLineEdit()
        self.product_completer = QCompleter(self.all_products_names)
        self.product.setCompleter(self.product_completer)

        self.price = QLineEdit()
        regexp = QRegExp('\d[\d\,\.]+')
        self.price.setValidator(QRegExpValidator(regexp))
        self.quantity = QLineEdit()
        self.unit = QLabel()
        self.date = QCalendarWidget()

        self.add_field("Fournisseur:", self.fournisseur)
        self.grid.addWidget(add_fournisseur, self.field_index, 2)
        self.add_field("Date:", self.date)
        self.add_field("Produit", self.product)
        self.add_field("quantité:", self.quantity)
        self.grid.addWidget(self.unit, self.field_index, 2)
        self.unit_label = QLabel("par pièce")
        self.add_field("Prix (€):", self.price)
        self.grid.addWidget(self.unit_label, self.field_index, 2)
        self.total = QLabel("")
        self.add_field("Prix total:", self.total)

        self.product.editingFinished.connect(self.verif_product)
        self.price.editingFinished.connect(self.refresh_total)
        self.quantity.textChanged.connect(self.refresh_total)
        add_fournisseur.clicked.connect(self.add_fournisseur)
        
        self.initUI()

    def verif_product(self):
        if self.product.text() not in self.all_products_names\
                and self.product.text() != '':
            reponse = QMessageBox.question(
                    None, 'Produit inexistant',
                    "Ce produit n'existe pas. Voulez-vous l'ajouter ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No)
            if reponse == QMessageBox.No:
                self.product.clear()
                return False
            if reponse == QMessageBox.Yes:
                new_product = ProductForm(self, self.product.text())
                self.all_products_names = self.parent.model.get_all_products_names()
                self.product_completer.setModel(QStringListModel(self.all_products_names))
                self.product.setText(new_product.name.text())
        if self.product.text() != '':
            unit = self.model.get_product_unit(self.product.text())
            self.product_id = self.model.get_product_id_by_name(self.product.text())
            self.refresh_unit_label(unit)
            self.unit.setText(unit)
            return True

    def add_fournisseur(self):
        f = self.parent.add_fournisseur()
        if f:
            self.refresh_fournisseurs()

    def refresh_total(self):
        if self.quantity.text() and self.price.text():
            price = float(self.price.text())
            quantity = float(self.quantity.text())
            total = round(price * quantity, 2)
            self.total.setText(str(total))

    def refresh_unit_label(self, unit):
        matching = {
           'Unités':'par pièce',
           'Kilogrammes':'le kilo',
           'Litres':'le litre'
           }
        unit = matching[unit]
        self.unit_label.setText(unit)

    def clear_all(self):
        self.quantity.clear()
        self.product.clear()
        self.price.clear()

    def submit_datas(self):
        if self.fournisseur.currentText() == "":
            QMessageBox.warning(self, "Erreur", "Il faut entrer un nom de fournisseur")
        elif self.product.text() == "":
            QMessageBox.warning(self, "Erreur", "Il faut entrer un nom de désignation")
        elif self.price.text() == "":
            QMessageBox.warning(self, "Erreur", "Il faut entrer un Prix")
        elif self.quantity.text() == "":
            QMessageBox.warning(self, "Erreur", "Il faut entrer une quantité")
        else:
            record = {}
            #below : can be improved for faster ?
            f_id = self.model.get_fournisseurs()[self.fournisseur.currentText()]
            record["fournisseur_id"] = f_id
            record["date"] = self.date.selectedDate().toString('yyyy-MM-dd')
            record["product_id"] = self.product_id
            record["prix"] = self.price.text()
            record["quantity"] = self.quantity.text()
            self.model.add_input(record)
            self.model.qt_table_reserve.select()
            self.model.qt_table_inputs.select()
            self.clear_all()

    def refresh_fournisseurs(self):
        self.fournisseur.clear()
        for fournisseur, id_ in list(self.model.get_fournisseurs().items()):
            self.fournisseur.addItem(fournisseur)

class InputsArray(QDialog):
    def __init__(self, parent, model):
        super(InputsArray, self).__init__(parent)

        self.model = model
        self.parent = parent

        self.view = QTableView(self)
        self.view.setModel(model)
        self.view.setSortingEnabled(True)
        
        sql_delegate = QSqlRelationalDelegate(self.view)
        self.view.setItemDelegate(sql_delegate)
        date_delegate = DateDelegate()
        self.view.setItemDelegateForColumn(2, date_delegate)
        self.view.hideColumn(0) # hide id

        import_button = QPushButton('Importer le prévisionnel')
        self.add_button = QPushButton('+')
        self.del_button = QPushButton('-')
        save_button = QPushButton('Enregistrer')
        close_button = QPushButton('Fermer')

        layout = QVBoxLayout()
        self.setLayout(layout)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.del_button)
        layout.addWidget(import_button)
        layout.addWidget(self.view)
        layout.addLayout(buttons_layout)
        buttons_layout2 = QHBoxLayout()
        buttons_layout2.addWidget(save_button)
        buttons_layout2.addWidget(close_button)
        layout.addLayout(buttons_layout2)

        self.add_button.clicked.connect(self.add_row)
        self.del_button.clicked.connect(self.del_row)
        import_button.clicked.connect(self.import_prev)
        save_button.clicked.connect(self.save_and_close)
        close_button.clicked.connect(self.close)

        self.resize(660, 360)
        self.exec_()

    def add_row(self):
        if self.model.isDirty():
            submited = self.model.submitAll()
        inserted = self.model.insertRow(self.model.rowCount())
        logging.debug(inserted)
    
    def del_row(self):
        select = self.view.selectionModel()
        row = select.currentIndex().row()
        self.model.removeRow(row)
        self.model.submitAll()

    def import_prev(self):
        date_start, date_stop = DatesRangeDialog(self).get_dates()
        logging.debug(date_start)
        fournisseur_model = self.parent.model.qt_table_fournisseurs
        fournisseur = SelectFournisseur(self.parent, fournisseur_model).get_()
        logging.debug(fournisseur)
        if fournisseur:
            fournisseur_id = self.parent.model.get_(
                ['id'], 'fournisseurs', "nom='" + fournisseur + "'")[0]['id']
        else:
            return False
        logging.debug(fournisseur_id)
        products = self.parent.model.get_prev_products_by_dates(
            date_start, date_stop)
        logging.debug(products)
        for product in products:
            product_id = product[0]
            quantity = product[2]
            date = QDate.currentDate().toString('yyyy-MM-dd')
            logging.debug(date)
            inserted = self.model.insertRow(self.model.rowCount())
            record = self.model.record()
            record.setValue(1, fournisseur_id) # fournisseur_id
            record.setValue(2, date) # date
            record.setValue(3, product_id) # product_id
            record.setValue(4, 0.0) # prix
            record.setValue(5, quantity) # quantité
            record.setGenerated('id', False)
            record_is_set = self.model.setRecord(
                self.model.rowCount() -1, record)
            logging.debug(record_is_set)
            logging.warning(self.model.lastError().text())

    def save_and_close(self):
        self.model.submitAll()
        self.close()

    def reject(self):
        self.model.revertAll()
        super().reject()

class RepasForm(Form):
    """ Form to add or modify an effective repas (with product outputs) """
    def __init__(self, parent=None, index=None):
        super(RepasForm, self).__init__(parent)

        self.model = parent.model.qt_table_repas
        self.type_model = self.model.relationModel(2)
        self.inputs_model = parent.model.qt_table_inputs

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.model)

        self.type = QComboBox()
        self.type.setModel(self.type_model)
        self.type.setModelColumn(1)
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.auto_fill_button = QPushButton('Importer le prévisionnel')
        self.comment = QTextEdit()
        self.comment.setFixedHeight(50)
        self.add_field("Type:", self.type)
        self.add_field("Date:", self.date)
        self.add_field("Commentaire:", self.comment)
        self.add_field('', self.auto_fill_button)

        #outputs 
        self.outputs_view = QTableView(self)
        self.outputs_view.setItemDelegate(QSqlRelationalDelegate(self.outputs_view))
        self.output_model = parent.model.qt_table_outputs
        self.outputs_view.setModel(self.output_model)
        product_delegate = ProductOutputDelegate(self)
        self.outputs_view.setItemDelegateForColumn(3, product_delegate) 
        self.outputs_view.hideColumn(0) # hide id
        self.outputs_view.hideColumn(2) # hide repas id
        self.add_field("sorties", self.outputs_view)
        self.add_output_button = QPushButton("+")
        self.del_output_button = QPushButton("-")
        buttons_outputs_layout = QHBoxLayout()
        buttons_outputs_layout.addWidget(self.add_output_button)
        buttons_outputs_layout.addWidget(self.del_output_button)
        self.grid.addLayout(buttons_outputs_layout, 6, 1)

        self.mapper.setItemDelegate(QSqlRelationalDelegate(self))
        self.mapper.addMapping(self.date, 1)
        self.mapper.addMapping(self.type, 2)
        self.mapper.addMapping(self.comment, 4, QByteArray(b'plainText'))

        for widget in [self.date, self.type, self.comment]:
            if self.mapper.mappedSection(widget) == -1:
                logging.warning('Widget ' + str(widget) + 'not mapped.')
        
        if index is not None:
            logging.debug(index.data())
            self.index = index
            id_ = index.model().data(index)
            logging.info('User want to update repas ' + str(id_))
            self.mapper.setCurrentModelIndex(index)
        else: # if this is a new one
            inserted = self.model.insertRow(self.model.rowCount())
            if not inserted:
                logging.warning(
                    'Row not inserted in model {0}'.format(self.model))
            self.model.setData(
                self.model.index(self.model.rowCount() - 1, 1),
                self.date.date().toString('yyyy-MM-dd'))
            self.model.setData(
                self.model.index(self.model.rowCount() - 1, 2),
                1)
            index = self.model.index(self.model.rowCount() - 1, 0)
            id_ = index.model().data(index)

            self.index = self.model.index(self.model.rowCount() -1, 0)
            self.mapper.toLast()
        
        self.output_model.setFilter('repas_id = ' + str(id_))

        self.add_output_button.clicked.connect(self.add_output_row)
        self.del_output_button.clicked.connect(self.del_output_row)
        self.auto_fill_button.clicked.connect(self.auto_fill)
        self.initUI()
        
        self.setWindowTitle("Repas #" + str(id_))
        
    def add_output_row(self):
        if self.model.isDirty():
            self.model.submitAll()
        if self.output_model.isDirty():
            self.output_model.submitAll()
        nbr_rows = self.output_model.rowCount()
        inserted = self.output_model.insertRow(nbr_rows)
        logging.debug(inserted)

    def del_output_row(self):
        at_least_one_to_submit = False
        for index in self.outputs_view.selectedIndexes():
            if index.model().isDirty(index):
                self.output_model.revertRow(index.row())
            else:
                self.output_model.removeRow(index.row())
                at_least_one_to_submit = True
        if at_least_one_to_submit:
            self.output_model.submitAll()

    def auto_fill(self):
        date = self.date.date()
        rel_model = self.model.relationModel(2)
        type_id = rel_model.data(rel_model.index(self.type.currentIndex(), 0))
        ingrs = self.parent.model.get_prev_ingrs(
            date.toString('yyyy-MM-dd'), type_id)
        logging.debug(ingrs)
        if not ingrs:
            message = "Aucun produit n'a été trouvé dans le prévisionnel"
            logging.warning(message)
            QMessageBox.warning(self, "Erreur", message)
        for ingr in ingrs:
            self.output_model.insertRow(self.output_model.rowCount())
            idx = self.output_model.index(self.output_model.rowCount() -1, 1)
            self.output_model.setData(idx, ingr[2]) # quantity
            idx = self.output_model.index(self.output_model.rowCount() -1, 3)
            self.output_model.setData(idx, ingr[0]) # product
    
    def submit_datas(self):
        repas_submited = self.model.submitAll()
        if repas_submited:
            id_ = self.model.data(self.index)
            logging.info('repas ' + str(id_) + ' submited.')
            self.submit_output(id_)
        if not repas_submited:
            error = self.model.lastError()
            logging.warning(error.text())
            QMessageBox.warning(
                self, "Erreur", "L'enregistrement du repas a échoué.")

    def submit_output(self, id_):
        for i in range(self.output_model.rowCount()):
            index = self.output_model.index(i, 2)
            data_set = self.output_model.setData(index, id_)
            if not data_set:
                logging.warning("data '" + str(id_) + "' set failed.")
        submited = self.output_model.submitAll()
        if submited:
            logging.info('outputs of repas ' + str(id_) + ' submited.')
            self.accept()
        if not submited:
            error = self.output_model.lastError()
            rec = self.output_model.record(self.output_model.rowCount() -1)
            logging.warning(error.text())
            QMessageBox.warning(
                self, "Erreur", "L'enregistrement des sorties a échoué.")

    def reject(self):
        self.model.revertAll()
        self.output_model.revertAll()
        super().reject()

class InfosCentreDialog(QDialog):
    def __init__(self, parent=None):
        super(InfosCentreDialog, self).__init__(parent)

        self.setWindowTitle("Informations du centre")
        self.parent = parent
        infos_model = parent.model.qt_table_infos
        self.periodes_infos_model = parent.model.qt_table_periodes_infos

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(infos_model)

        self.centre = QLineEdit()
        self.directeur_nom = QLineEdit()
        self.place = QLineEdit()

        periode_layout = QVBoxLayout()
        self.period_view = QTableView()
        self.period_view.setModel(self.periodes_infos_model)
        self.period_view.hideColumn(0) # hide id
        # Date delegate must be instanciated otherwise it raises segfault
        date_delegates = [DateDelegate() for x in range(2)]
        self.period_view.setItemDelegateForColumn(1, date_delegates[0])
        self.period_view.setItemDelegateForColumn(2, date_delegates[1])
        self.add_button = QPushButton('+')
        self.del_button = QPushButton('-')
        periode_buttons_layout = QHBoxLayout()
        periode_buttons_layout.addWidget(self.add_button)
        periode_buttons_layout.addWidget(self.del_button)
        periode_layout.addWidget(self.period_view)
        periode_layout.addLayout(periode_buttons_layout)
        
        self.mapper.addMapping(self.centre, infos_model.fieldIndex("centre"))
        self.mapper.addMapping(
            self.directeur_nom, infos_model.fieldIndex("directeur_nom"))
        self.mapper.addMapping(self.place, infos_model.fieldIndex("place"))
        
        self.layout = QFormLayout(self)
        
        self.layout.addRow("Nom du centre:", self.centre)
        self.layout.addRow("Lieu:", self.place)
        self.layout.addRow("Nom du directeur:", self.directeur_nom)
        self.layout.addRow('Périodes:', periode_layout)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            self)

        self.add_button.clicked.connect(self.add_periode)
        self.del_button.clicked.connect(self.del_periode)
        buttons.accepted.connect(self.submit_all_infos)
        buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)
        
        self.mapper.toFirst()
        self.resize(660, 360)
        self.exec_()

    def add_periode(self):
        model = self.period_view.model()
        nbr_rows = self.periodes_infos_model.rowCount()
        if nbr_rows == 0:
            date_start = QDate().currentDate()
        else:
            last_date_stop = model.record(nbr_rows -1).value('date_stop')
            date_start = QDate().fromString(last_date_stop, 'yyyy-MM-dd')
            date_start = date_start.addDays(1)
        if model.isDirty():
            submited = model.submitAll()
        inserted = model.insertRow(nbr_rows)
        record = model.record()
        record.setValue('date_start', date_start.toString('yyyy-MM-dd'))
        record.setValue('date_stop', date_start.toString('yyyy-MM-dd'))
        record.setGenerated('id', False)
        record_is_set = model.setRecord(model.rowCount() -1, record)

    def del_periode(self):
        model = self.period_view.model()
        model.removeRow(model.rowCount() -1)
        model.submitAll()

    def submit_all_infos(self):
        info_submited = self.mapper.submit()
        periode_model = self.period_view.model()
        periode_submited = periode_model.submitAll()
        if info_submited and periode_submited:
            self.accept()

class RapportDialog(QDialog):
    def __init__(self, parent):
        super(RapportDialog, self).__init__(parent)
        self.parent = parent
        self.setMinimumSize(600, 100)
        self.grid_index = 0
        
        self.grid = QGridLayout(self)
        for i in range(2):
            self.grid.setColumnMinimumWidth(i, 300)
        self.repas = QComboBox()
        self.price_by_repas = QLabel("")
        box_repas = self.create_box('Prix par repas', [self.repas, self.price_by_repas])

        self.date = QComboBox()
        self.price_by_day = QLabel("")
        box_day = self.create_box('Prix par journée', [self.date, self.price_by_day])
        self.grid.addWidget(box_repas, 0, 0)
        self.grid.addWidget(box_day, 0, 1)
        self.repas.currentIndexChanged.connect(self.display_price_by_repas)
        self.date.currentTextChanged.connect(self.display_price_by_day)
        self.fill_repas()
        self.fill_date()

        self.exec_()

    def fill_repas(self):
        all_repas = self.parent.model.get_all_repas()
        self.all_repas_dic = {}
        for i, repas in enumerate(all_repas):
            self.all_repas_dic[i] = repas
            self.repas.addItem(repas['type']+" du "+repas['date'])
        self.display_price_by_repas(0)

    def fill_date(self):
        all_dates = self.parent.model.get_dates_repas()
        for date in all_dates:
            self.date.addItem(date)
        if all_dates:
            self.display_price_by_day(all_dates[0])

    def display_price_by_repas(self, index):
        if self.all_repas_dic:
            repas_id = self.all_repas_dic[index]['id']
            price = self.parent.model.get_price_by_repas(repas_id)
            self.price_by_repas.setText(str(round(price, 2)) + " €")

    def display_price_by_day(self, day):
        price = self.parent.model.get_price_by_day(day)
        self.price_by_day.setText(str(round(price, 2)) + " €")
        
    def create_box(self, titre, widgets):
        layout = QGridLayout()
        box = QGroupBox(titre, parent=self)
        for i, widget in enumerate(widgets):
            layout.addWidget(widget, self.grid_index, i)
        self.grid_index += 1
        box.setLayout(layout)
        return box

class Previsionnel(QDialog):
    def __init__(self, parent):
        super(Previsionnel, self).__init__(parent)

        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.layout = QVBoxLayout()
        self.parent = parent

        btn_names = [
            'petit déjeuner',
            'déjeuner',
            'goûter',
            'dîner',
            'piquenique',
            'autre']
        self.repas_buttons_group = QButtonGroup()
        self.repas_buttons_group.setExclusive(True)
        self.repas_buttons_layout = QHBoxLayout()
        self.repas_buttons = {}
        for name in btn_names:
            self.repas_buttons[name] = QPushButton(name)
            self.repas_buttons[name].setCheckable(True)
            self.repas_buttons[name].clicked.connect(self.select_plat)
            self.repas_buttons_group.addButton(self.repas_buttons[name])
            self.repas_buttons_layout.addWidget(self.repas_buttons[name])

        self.add_repas_button = QPushButton('+')
        self.add_plat_button = QPushButton('+')
        self.add_ingredient_button = QPushButton('+')

        self.del_repas_button = QPushButton('-')
        self.del_plat_button = QPushButton('-')
        self.del_ingredient_button = QPushButton('-')
        
        self.plats_prev_view, self.plats_box = self._create_view(
                'Plats', [self.add_plat_button, self.del_plat_button])
        self.ingredients_prev_view, self.ingredients_box = self._create_view(
                'Ingredients', [self.add_ingredient_button, self.del_ingredient_button])
        completer_delegate = CompleterDelegate(self)
        self.ingredients_prev_view.setItemDelegateForColumn(
            1, completer_delegate)

        self.layout.addWidget(self.calendar)
        self.layout.addLayout(self.repas_buttons_layout)
        plats_ingrs_layout = QHBoxLayout()
        plats_ingrs_layout.addWidget(self.plats_box)
        plats_ingrs_layout.addWidget(self.ingredients_box)
        self.layout.addLayout(plats_ingrs_layout)
        self.setLayout(self.layout)
        
        self.repas_model = parent.model.repas_prev_model
        self.plats_model = parent.model.plat_prev_model
        self.ingredients_model = parent.model.ingredient_prev_model
        
        self.calendar.selectionChanged.connect(self.select_repas)
        self.plats_prev_view.clicked.connect(self.select_ingredient)
        
        self.plats_prev_view.setModel(self.plats_model)
        self.plats_prev_view.setColumnHidden(0, True)  #hide id
        self.plats_prev_view.setColumnHidden(2, True)  #hide repas_prev

        self.ingredients_prev_view.setModel(self.ingredients_model)
        self.ingredients_model.relationModel(1).select()
        self.ingredients_prev_view.setColumnHidden(0, True) #hide id
        self.ingredients_prev_view.setColumnHidden(2, True) #hide dish parent
        self.select_repas()
        
        self.add_repas_button.clicked.connect(self.add_repas)
        self.add_plat_button.clicked.connect(self.add_plat)
        self.add_ingredient_button.clicked.connect(self.add_ingredient)
        self.del_repas_button.clicked.connect(self.del_repas)
        self.del_plat_button.clicked.connect(self.del_plat)
        self.del_ingredient_button.clicked.connect(self.del_ingredient)
        
        self.setMinimumSize(377, 500)
        self.exec_()

    def _create_view(self, box_name, buttons):
        """ Return a QTableView (with good relationnal delegate)
        and a box containing it """
        view = QTableView()
        view.setItemDelegate(QSqlRelationalDelegate(view))
        groupbox = QGroupBox(box_name, parent=self)
        layout = QVBoxLayout()
        layout.addWidget(view)
        button_layout = QHBoxLayout()
        for button in buttons:
            button_layout.addWidget(button)
        layout.addLayout(button_layout)
        groupbox.setLayout(layout)
        return view, groupbox

    def select_repas(self):
        self.date = self.calendar.selectedDate()
        self.repas_model.setFilter(
            "date = '"+self.date.toString('yyyy-MM-dd')+"'")
        self.select_plat()

    def select_plat(self):
        # below: buttons must be in same order than db table
        id_ = self.repas_buttons_group.checkedId() * -1 -1
        self.current_repas_id = id_
        self.plats_model.setFilter("relTblAl_2.type_id = " + str(id_)
            + " AND relTblAl_2.date = '" + str(
                self.date.toString('yyyy-MM-dd') + "'"))
        if self.plats_model.lastError().text().rstrip(' '):
            logging.warning(self.plats_model.lastError().text())
        self.plats_box.setTitle('Les plats du repas sélectionné')
        self.select_ingredient()

    def select_ingredient(self):
        row = self.plats_prev_view.selectionModel().currentIndex().row()
        id_ = self.plats_prev_view.model().record(row).value(0)
        self.current_plat_id = id_
        self.ingredients_box.setTitle('Les ingrédients du plat sélectionné')
        self.ingredients_model.setFilter(
                "dishes_prev_id = " + str(id_))

    def add_repas(self):
        self.repas_model.add_row(date=self.date.toString('yyyy-MM-dd'))
    
    def add_plat(self):
        repas_type_id = self.repas_buttons_group.checkedId() * -1 - 1
        date = self.calendar.selectedDate().toString('yyyy-MM-dd')
        repas_id = self.repas_model.get_id(date, repas_type_id)
        plat_type_by_default = {
            1: 4, # petit déj: autre
            2: 1, # déjeuner: entrée
            3: 4, # goûter: autre
            4: 1, # dîner: entrée
            5: 2, # picnique: plat
            6: 4} # autre: autre
        # Add repas if not exist
        if not repas_id:
            self.repas_model.add_row(date, type_id = repas_type_id)
            repas_id = self.repas_model.get_id(date, repas_type_id)
        self.plats_model.add_row(repas_id, plat_type_by_default[repas_type_id])

    def add_ingredient(self):
        inserted = self.ingredients_model.insertRow(self.ingredients_model.rowCount())
        record = self.ingredients_model.record()
        record.setValue(2, self.current_plat_id)
        record.setValue(3, 0) # quantité
        record_is_set = self.ingredients_model.setRecord(
                self.ingredients_model.rowCount() -1, record)
        logging.debug(record_is_set)
        logging.debug(self.ingredients_model.lastError().text())

    def del_repas(self):
        reponse = QMessageBox.question(
                None, 'Sûr(e) ?', "Vous allez détruire définitivement ce repas"\
                + " ainsi que tous les plats et ingrédients associés. "\
                + "Êtes-vous sûr(e) ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
        if reponse == QMessageBox.Yes:
            self.repas_model.del_row(id=self.current_repas_id)
    
    def del_plat(self):
        reponse = QMessageBox.question(
                None, 'Sûr(e) ?', "Vous allez détruire définitivement ce plat"\
                + " ainsi que tous les ingrédients associés. Êtes-vous sûr(e) ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
        if reponse == QMessageBox.Yes:
            self.plats_model.del_row(id=self.current_plat_id)

    def del_ingredient(self):
        reponse = QMessageBox.question(
                None, 'Sûr(e) ?', "Vous allez détruire définitivement cet ingrédient."\
                + " Êtes-vous sûr(e) ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
        if reponse == QMessageBox.Yes:
            row = self.ingredients_prev_view.selectionModel().currentIndex().row()
            id_ = self.ingredients_prev_view.model().record(row).value(0)
            self.ingredients_model.del_row(id=id_)

    def set_auto_quantity(self, product, row):
        date = self.calendar.selectedDate().toString('yyyy-MM-dd')
        quantity = self.parent.model.get_recommended_quantity(
            date, product)
        if quantity is not None:
            index = self.ingredients_model.index(row, 3) # 3: quantity column
            logging.debug(self.ingredients_model.data(index))
            s = self.ingredients_model.setData(index, quantity)
        submited = self.ingredients_model.submitAll()
        if not submited:
            logging.warning(self.ingredients_model.lastError().text())

class PlatPrevisionnel(QWidget):
    """ not finished/used... """
    def __init__(self, parent):
        super(PlatPrevisionnel, self).__init__(parent)
        self.model = parent.model.plat_prev_model
        self.box = QGroupBox('Plat', self)

        self.ingredients = []
        self.type = QComboBox()
        self.name = QLineEdit()
        
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.type)
        vbox.addWidget(self.name)

        self.box.setLayout(vbox)
        layout = QBoxLayout()
        layout.addWidget(self.box)
        self.setLayout(layout)

    def add_ingredient(self):
        self.ingredients.append(IngredientPrevisionnel(self))

    def refresh_type(self):
        pass

class IngredientPrevisionnel(QWidget):
    """ not finished/used... """
    def __init__(self, parent):
        super(IngredientPrevisionnel, self).__init__(parent)
        self.model = parent.model
        self.box = QGroupBox('Ingredient', self)

        self.name = QComboBox()
        self.quantity = QDoubleSpinBox()
        self.unit = QComboBox()
        
        self.name.setModel(self.model.rel_name)
        self.name.setModelColumn(self.model.rel_type.fieldIndex('name'))
        
        vbox = QVBoxLayout(self)
        vbox.addWidget(self.quantity)
        vbox.addWidget(self.unit)

        self.box.setLayout(vbox)
        layout = QVBoxLayout()
        layout.addWidget(self.box)
        self.setLayout(layout)

        mapper = QDataWidgetMapper(self)
        mapper.setModel(self.model)
        mapper.addMapping(self.name, self.model.fieldIndex("product_id"))
        mapper.addMapping(self.quantity, self.model.fieldIndex("quantity"))
        mapper.addMapping(self.unit, self.model.fieldIndex("unit"))

class PrevisionnelColumnView(QGroupBox):
    def __init__(self, parent):
        super(PrevisionnelColumnView, self).__init__(parent)

        self.previsionnel_model = parent.model.previsionnel_model
        self.calendar = QCalendarWidget()
        self.column_view = QColumnView()
        self.column_view.setModel(self.previsionnel_model)
        self.column_view.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout = QVBoxLayout()
        layout.addWidget(self.calendar)
        layout.addWidget(self.column_view)
        self.setLayout(layout)

        self.calendar.selectionChanged.connect(self.select_repas)
        self.select_repas()
    
    def select_repas(self):
        self.date = self.calendar.selectedDate()
        self.previsionnel_model.query_for_day(self.date.toString('yyyy-MM-dd'))

class DateDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        layout = QFormLayout()
        layout.addRow('Du', self.date)
        
        self.ok_button = QPushButton('OK')
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        layout.addRow('', button_layout)
        self.setLayout(layout)
        
        self.ok_button.clicked.connect(self.get_date)
        self.exec_()
    
    def get_date(self):
        self.accept()
        return self.date.date().toString('yyyy-MM-dd')

class DatesRangeDialog(QDialog):
    def __init__(self, parent=None, name=""):
        super(DatesRangeDialog, self).__init__(parent)
        
        self.date_start = QDateEdit()
        self.date_start.setDate(QDate.currentDate())
        self.date_stop = QDateEdit()
        self.date_stop.setDate(QDate.currentDate())

        layout = QFormLayout()
        layout.addRow('Du', self.date_start)
        layout.addRow('Au', self.date_stop)

        self.ok_button = QPushButton('OK')
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        layout.addRow('', button_layout)
        self.setLayout(layout)
        
        self.ok_button.clicked.connect(self.get_dates)
        self.exec_()

    def get_dates(self):
        self.accept()
        return (self.date_start.date().toString('yyyy-MM-dd'),
            self.date_stop.date().toString('yyyy-MM-dd'))

class SelectFournisseur(QDialog):
    def __init__(self, parent=None, model=None):
        super(SelectFournisseur, self).__init__(parent)
        self.parent = parent

        info = QLabel("Sélectionnez un fournisseur dans la liste "\
            + "ou ajoutez-en un nouveau.")

        self.combobox = QComboBox()
        self.combobox.setModel(model)
        self.combobox.setModelColumn(1)
        ok_button = QPushButton('OK')
        add_button = QPushButton('+')
        layout = QVBoxLayout()
        f_layout = QHBoxLayout()
        f_layout.addWidget(self.combobox, 1)
        f_layout.addWidget(add_button)
        layout.addWidget(info)
        layout.addLayout(f_layout)
        layout.addWidget(ok_button)
        self.setLayout(layout)

        ok_button.clicked.connect(self.get_)
        add_button.clicked.connect(self.add_fournisseur)

        self.exec_()

    def get_(self):
        self.accept()
        return  self.combobox.currentText()

    def add_fournisseur(self):
        inserted = self.parent.add_fournisseur()
        if inserted:
            self.combobox.model().select()

class DateDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super(DateDelegate, self).__init__(parent)

    def paint(self, painter, opt, index):
        painter.save()
        date = QDate.fromString(index.data(), 'yyyy-MM-dd')
        color = opt.palette.color(QPalette.Text)
        painter.setPen(QPen(color))
        painter.drawText(opt.rect, Qt.AlignCenter, date.toString('dd/MM/yyyy'))
        painter.restore()
    
    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setDate(QDate.currentDate())
        return editor
        
    def setModelData(self, editor, model, index):
        value = editor.date().toString('yyyy-MM-dd')
        model.setData(index, value)

class CompleterDelegate(QSqlRelationalDelegate):
    def __init__(self, parent=None):
        super(CompleterDelegate, self).__init__(parent)
        self.parent = parent
    
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        self.model_p = index.model().relationModel(1)
        #model_p = index.model().products
        editor.setModel(self.model_p)
        editor.setModelColumn(1)
        editor.setEditable(True)
        editor.currentIndexChanged.connect(self.sender)
        return editor
    
    def setModelData(self, editor, model, index):
        m = model.products
        logging.debug(m)
        products = [m.data(m.index(i, 1)) for i in range(m.rowCount())]
        
        if not editor.currentText().rstrip(' '):
            pass
        elif editor.currentText() not in products:
            reponse = QMessageBox.question(
                None, 'Produit inexistant', 
                "Ce produit n'existe pas. Voulez-vous l'ajouter ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
            if reponse == QMessageBox.Yes:
                p = ProductForm(
                    self.parent.parent, name=editor.currentText()).submit()
                if p:
                    index.model().relationModel(1).select()
                    editor.setCurrentText(p)
        else:
            self.parent.set_auto_quantity(editor.currentText(), index.row())
            super(CompleterDelegate, self).setModelData(editor, model, index)
            self.parent.ingredients_model.submitAll()

class ProductOutputDelegate(QSqlRelationalDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        #model_products = index.model().relationModel(3)
        model_products = self.parent.inputs_model
        logging.debug(model_products)
        editor.setModel(model_products)
        editor.setModelColumn(3)
        editor.setEditable(True)
        editor.currentIndexChanged.connect(self.sender)
        return editor

    def setModelData(self, editor, model, index):
        output_model = model
        input_model = editor.model()
        product_model = input_model.relationModel(3)
        index_input = input_model.index(editor.currentIndex(), 3)
        name = input_model.data(index_input)
        if name:
            product_model.setFilter("name = '" + name + "'")
        value = product_model.data(product_model.index(0, 0))
        logging.debug(value) # il faut récupéreer l'ID, pas le résultat de la relation...
        model.setData(index, value)

class FComboBox(QComboBox):
    """ not used, just for remember the focusOutEvent possibility.
    See TODO file """
    def __init__(self, parent, delegate):
        super(FComboBox, self).__init__(parent)
        self.delegate = delegate

    def focusOutEvent(self, event):
        logging.debug('focusOut!')
        logging.debug(self.currentText())
        logging.debug(self.currentIndex())
        logging.debug(self.completer().currentCompletion())
        self.setCurrentText(self.completer().currentCompletion())
        logging.debug(self.currentIndex())
        self.model().submit()
        completion = self.completer().currentCompletion()
