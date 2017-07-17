#!/usr/bin/python3
# -*- coding: utf-8 -*- 

"""
contains QT views and delegates
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QDialog, QGroupBox, QStyledItemDelegate, QGridLayout, QPushButton,
    QCalendarWidget, QTableView, QComboBox, QTextEdit, QLabel, QVBoxLayout,
    QHBoxLayout, QCompleter, QDoubleSpinBox, QButtonGroup, QLineEdit, 
    QFormLayout, QDataWidgetMapper, QDialogButtonBox, QMessageBox, QDateEdit,
    QAbstractItemView, QTabWidget, QCheckBox, QSpinBox)
from PyQt5.QtCore import (
    QRegExp, QDate, Qt, QStringListModel, QSize, QByteArray, 
    QSortFilterProxyModel)
from PyQt5.QtGui import QRegExpValidator, QPen, QPalette, QIcon
from PyQt5.QtSql import QSqlRelationalDelegate

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
        proxy = QSortFilterProxyModel()
        proxy.setSourceModel(model)
        table.setModel(proxy)
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
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(parent.model.qt_table_products)
        self.view.setModel(self.proxy)
        self.view.setSortingEnabled(True)
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
        self.add_button.clicked.connect(self.add_product)
        
        self.view.horizontalHeader().setMinimumHeight(50)
        self.resize(780, 376)

        self.exec_()
        
    def reject(self):
        super().reject()

    def add_product(self):
        ProductForm(self.parent, name='')

    def edit_product(self, index):
        ProductForm(self.parent, self.proxy.mapToSource(index).row())

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
        self.parent = parent

        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.model)

        self.warning_label = QLabel(
            "Assurez-vous que le produit que vous allez entrer\n"
            +" n'existe pas déjà sous un autre nom.")
        self.name = QLineEdit()
        self.name.setToolTip("Avec les accents, en minuscule")
        self.units = QComboBox()
        self.units_model = self.model.relationModel(2)
        logging.debug(self.units_model)
        for row in range(self.units_model.rowCount()):
            logging.debug(self.units_model.data(self.units_model.index(row, 1)))
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
            logging.debug("this is a new product")
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
        add_fournisseur.clicked.connect(self.add_fournisseur)
        self.ok_button.clicked.connect(self.submit)
        self.cancel_button.clicked.connect(self.close)

        self.exec_()

    def add_fournisseur(self):
        FournisseurForm(self.parent)
        # below : we need to refresh the relation model because it's other
        # instance than qt_fournisseur_model
        self.model.relationModel(6).select() 

    def submit(self):
        mapper_submited = self.mapper.submit() # to init widget default value
        if not mapper_submited:
            logging.warning('product mapper not submited.')
        logging.debug(self.units.currentText())
        logging.debug(self.mapper.mappedWidgetAt(6))
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

class InputsArray(QDialog):
    def __init__(self, parent, model):
        super(InputsArray, self).__init__(parent)

        self.model = model
        self.parent = parent

        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.date = self.calendar.selectedDate()
        self.view = QTableView(self)
        self.view.setModel(model)
        self.view.setSortingEnabled(True)
        
        sql_delegate = QSqlRelationalDelegate(self.view)
        self.view.setItemDelegate(sql_delegate)
        date_delegate = DateDelegate()
        self.view.setItemDelegateForColumn(2, date_delegate)
        products_delegate = ProductInputDelegate(self) 
        self.view.setItemDelegateForColumn(3, products_delegate)
        self.view.hideColumn(0) # hide id
        self.view.hideColumn(2) # hide date
        self.view.hideColumn(4) # hide ingredient_prev_id

        import_button = QPushButton('Importer le prévisionnel')
        self.add_button = QPushButton('+')
        self.del_button = QPushButton('-')
        save_button = QPushButton('Enregistrer')
        close_button = QPushButton('Fermer')

        config_layout = QGridLayout()
        layout = QVBoxLayout()
        self.setLayout(layout)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.del_button)
        config_layout.addWidget(self.calendar, 0, 0)
        config_layout.addWidget(import_button, 0, 1)
        layout.addLayout(config_layout)
        layout.addWidget(self.view, 10)
        layout.addLayout(buttons_layout)
        buttons_layout2 = QHBoxLayout()
        buttons_layout2.addWidget(save_button)
        buttons_layout2.addWidget(close_button)
        layout.addLayout(buttons_layout2)

        self.calendar.selectionChanged.connect(self.set_day_filter)
        self.add_button.clicked.connect(self.add_row)
        self.del_button.clicked.connect(self.del_row)
        import_button.clicked.connect(self.import_prev)
        save_button.clicked.connect(self.save_and_close)
        close_button.clicked.connect(self.close)

        self.resize(660, 360)
        self.exec_()
        self.set_day_filter()

    def set_day_filter(self):
        self.date = self.calendar.selectedDate()
        self.model.setFilter(
            "date = '" + self.date.toString('yyyy-MM-dd') + "'")

    def add_row(self):
        if self.model.isDirty():
            submited = self.model.submitAll()
        inserted = self.model.insertRow(self.model.rowCount())
        if inserted:
            self.model.setData(
                self.model.index(self.model.rowCount() -1, 2),
                self.date.toString('yyyy-MM-dd'))
        logging.debug(inserted)
    
    def del_row(self):
        select = self.view.selectionModel()
        row = select.currentIndex().row()
        self.model.removeRow(row)
        self.model.submitAll()

    def import_prev(self):
        date_start, date_stop = DatesRangeDialog(self).get_dates()
        products = self.parent.model.get_prev_products_by_dates(
            date_start, date_stop)
        prev_ids = []
        for i in range(self.model.rowCount()):
            idx = self.model.index(i, 4)
            prev_ids.append(self.model.data(idx))
        logging.debug(prev_ids)
        already_set_products = []
        if not products:
            QMessageBox.warning(self, "Erreur", "Aucun produit trouvé.")
        for product in products:
            if product[0] not in prev_ids:
                product_id = product[1]
                quantity = product[3]
                fournisseur_id = product[5]
                ingr_prev_id = product[0]
                date = self.calendar.selectedDate().toString('yyyy-MM-dd')
                inserted = self.model.insertRow(self.model.rowCount())
                record = self.model.record()
                record.setValue(1, fournisseur_id) # fournisseur_id
                record.setValue(2, date) # date
                record.setValue(3, product_id) # product_id
                record.setValue(4, ingr_prev_id) # product_id
                record.setValue(5, 0.0) # prix
                record.setValue(6, quantity) # quantité
                record.setGenerated('id', False)
                record_is_set = self.model.setRecord(
                    self.model.rowCount() -1, record)
                logging.debug(record_is_set)
                logging.warning(self.model.lastError().text())
            else:
                already_set_products.append(product[2])
        if already_set_products:
            QMessageBox.warning(self, "Erreur", "Ces produits ont déjà été "
                + "importés : " + ', '.join(already_set_products))

    def save_and_close(self):
        submited = self.model.submitAll()
        if submited:
            self.parent.model.qt_table_reserve.select()
        if not submited:
            error = self.model.lastError()
            logging.warning(error.text())
        self.close()

    def reject(self):
        self.model.revertAll()
        super().reject()

class RepasForm(Form):
    """ Form to add or modify an effective repas (with product outputs) """
    def __init__(self, parent=None, index=None):
        super(RepasForm, self).__init__(parent)

        self.parent = parent
        self.model = parent.model.qt_table_repas
        self.products_model = parent.model.qt_table_products
        self.type_model = self.model.relationModel(2)
        self.inputs_proxy = QSortFilterProxyModel()
        self.inputs_proxy.setSourceModel(parent.model.qt_table_inputs)

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
        if inserted:
            id_ = self.model.data(self.model.index(self.model.rowCount() -1, 0))
            self.output_model.setData(
                self.output_model.index(self.output_model.rowCount() - 1, 2),
                id_)
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
            id_ = self.model.data(self.model.index(self.model.rowCount() -1, 0))
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
            self.parent.model.qt_table_reserve.select()
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
            model.submitAll()
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

        self.current_repas_id = 1
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.layout = QVBoxLayout()
        self.parent = parent
        
        self.repas_model = parent.model.repas_prev_model
        self.plats_model = parent.model.plat_prev_model
        self.ingredients_model = parent.model.ingredient_prev_model

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

        self.piquenique_box = PiqueniqueBox(self)

        self.add_repas_button = QPushButton('+')
        self.add_plat_button = QPushButton('+')
        self.add_ingredient_button = QPushButton('+')

        self.del_repas_button = QPushButton('-')
        self.del_plat_button = QPushButton('-')
        self.del_ingredient_button = QPushButton('-')
        
        self.compute_quantities_button = QPushButton(
            'Recalculer toutes les quantités')

        self.plats_prev_view, self.plats_box = self._create_view(
                'Plats', [self.add_plat_button, self.del_plat_button])
        self.ingredients_prev_view, self.ingredients_box = self._create_view(
                'Ingredients', [self.add_ingredient_button, self.del_ingredient_button])
        completer_delegate = CompleterDelegate(self)
        self.ingredients_prev_view.setItemDelegateForColumn(
            1, completer_delegate)

        self.layout.addWidget(self.calendar, stretch=0)
        self.layout.addLayout(self.repas_buttons_layout)
        self.layout.addWidget(self.piquenique_box)
        plats_ingrs_layout = QHBoxLayout()
        plats_ingrs_layout.addWidget(self.plats_box, 2)
        plats_ingrs_layout.addWidget(self.ingredients_box, 3)
        self.layout.addLayout(plats_ingrs_layout, stretch=10)
        self.setLayout(self.layout)
        
        self.calendar.selectionChanged.connect(self.select_repas)
        self.plats_prev_view.clicked.connect(self.select_ingredient)
        
        self.plats_prev_view.setModel(self.plats_model)
        self.plats_prev_view.setColumnHidden(0, True)  #hide id
        self.plats_prev_view.setColumnHidden(2, True)  #hide repas_prev
        plat_delegate = PlatPrevNameDelegate(self)
        self.plats_prev_view.setItemDelegateForColumn(1, plat_delegate)

        self.ingredients_prev_view.setModel(self.ingredients_model)
        #self.ingredients_model.relationModel(1).select()
        self.ingredients_prev_view.setColumnHidden(0, True) #hide id
        #self.ingredients_prev_view.setColumnHidden(2, True) #hide dish parent
        self.ingredients_prev_view.setColumnWidth(1, 150)
        self.select_repas()
        
        self.layout.addWidget(self.compute_quantities_button)
        
        self.add_repas_button.clicked.connect(self.add_repas)
        self.add_plat_button.clicked.connect(self.add_plat)
        self.add_ingredient_button.clicked.connect(self.add_ingredient)
        self.del_repas_button.clicked.connect(self.del_repas)
        self.del_plat_button.clicked.connect(self.del_plat)
        self.del_ingredient_button.clicked.connect(self.del_ingredient)
        self.compute_quantities_button.clicked.connect(
            self.compute_q_for_periode)
        
        self.setMinimumSize(700, 650)
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
        if id_ == 5: # piquenique
            self.piquenique_box.model.revertAll()
            self.piquenique_box.setVisible(True)
            date = self.calendar.selectedDate()
            self.repas_model.setFilter(
                "date = '" + date.toString('yyyy-MM-dd') + "' AND type_id = "\
                + str(id_))
            self.current_repas_id = self.repas_model.data(
                self.repas_model.index(0, 0))
            if not self.current_repas_id:
                self.current_repas_id = 0
            self.piquenique_box.model.setFilter(
                'repas_prev_id = ' + str(self.current_repas_id))
            if self.piquenique_box.model.rowCount() == 0:
                self.piquenique_box.add_row()
            self.piquenique_box.mapper.toLast()
        else:
            self.piquenique_box.setVisible(False)

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
        if repas_type_id:
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
            self.plats_model.add_row(
                repas_id, plat_type_by_default[repas_type_id])
        else:
            QMessageBox.warning(self, 'Erreur', "Veuillez choisir un repas")

    def add_ingredient(self):
        inserted = self.ingredients_model.add_row(self.current_plat_id)
        if not inserted:
            if self.parent.model.qt_table_products.rowCount() == 0:
                reponse = QMessageBox.question(None, 'Ajouter un produit ?',
                    "Il semble n'y avoir aucun produit dans la base de donnée. "\
                    + "En ajouter un nouveau ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No)
                if reponse == QMessageBox.Yes:
                    ProductForm(self.parent)

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
            m = self.ingredients_prev_view.model()
            id_ = m.data(m.index(row, 0))
            self.ingredients_model.del_row(id_=id_)

    def set_auto_q_fast(self, product, row):
        date = self.calendar.selectedDate().toString('yyyy-MM-dd')
        if self.repas_model.data(self.repas_model.index(0, 2)) == 'piquenique':
            quantity = self.get_recommend_quantity_piquenique(product)
        else:
            quantity = self.get_recommend_quantity(product, date)
        if quantity is not None:
            index = self.ingredients_model.index(row, 2) # 3: quantity column
            logging.debug(self.ingredients_model.data(index))
            self.ingredients_model.setData(index, quantity, None)
        submited = self.ingredients_model.submitAll()
        if not submited:
            logging.warning(self.ingredients_model.lastError().text())

    def get_recommend_quantity(self, product, date, piquenique=None):
        periodes_model = self.parent.model.qt_table_periodes_infos
        products_model = self.parent.model.qt_table_products
        enfants = periodes_model.get_enfants_by_date(date)
        if not enfants:
            QMessageBox.warning(self, "Erreur",
                "Pas d'enfants trouvés pour cette période")
            return False
        if piquenique:
            enfants = [x - piquenique[i] for i, x in enumerate(enfants)]
        logging.debug(enfants)
        recommends = products_model.get_recommends(product)
        quantities = [x * recommends[i] for i, x in enumerate(enfants)]
        return sum(quantities)

    def get_recommend_quantity_piquenique(self, product):
        products_model = self.parent.model.qt_table_products
        m = self.parent.model.piquenique_conf_model
        enfants = [m.data(m.index(0, i)) for i in range(2, 5)]
        if not enfants:
            QMessageBox.warning(self, "Erreur",
                "Pas d'enfants trouvés pour ce piquenique")
            return False
        recommends = products_model.get_recommends(product)
        quantities = [x * recommends[i] for i, x in enumerate(enfants)]
        return sum(quantities)

    def compute_q_for_periode(self):
        reponse = QMessageBox.question(
                None, 'Sûr(e) ?', "Vous allez écraser définitivement toutes les"\
                + " quantités sur une péride donnée. "\
                + "Êtes-vous sûr(e) ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
        if reponse == QMessageBox.Yes:
            date_start, date_stop = DatesRangeDialog(self).get_dates()
            logging.debug(date_start)
            logging.debug(date_stop)
            for l in self.parent.model.get_auto_q_all(date_start, date_stop):
                self.parent.model.update_ingredient_prev(l[0], l[2])
                if l[4]:
                    self.compute_all_quantities(l[3])
                logging.debug(l)
        self.ingredients_model.select()

    def compute_all_quantities(self, date=None):
        """ substract quantities from piquenique datas """
        piquenique_m = self.parent.model.piquenique_conf_model
        enfants_piquenique = [piquenique_m.data(
            piquenique_m.index(0, i)) for i in range(2, 5)]
        logging.debug(enfants_piquenique)
        sub_dishes = [i for i in range(1, 5) \
            if piquenique_m.data(piquenique_m.index(0, i + 4)) == 1]
        if not date:
            date = self.calendar.selectedDate().toString('yyyy-MM-dd')
        ingrs = self.ingredients_model.get_all_by_date(date)
        logging.debug(ingrs)
        #self.ingredients_model.setFilter('')
        for id_, product, repas_type_id in ingrs:
            has_enfants = None
            if repas_type_id in sub_dishes:
                has_enfants = enfants_piquenique
            quantity = self.get_recommend_quantity(product, date, has_enfants)
            self.ingredients_model.set_quantity(id_, quantity)
        
class PiqueniqueBox(QGroupBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.model = parent.parent.model.piquenique_conf_model
        
        self.age6 = QSpinBox()
        self.age6_12 = QSpinBox()
        self.age12 = QSpinBox()
        self.submit_button = QPushButton('Re-calculer les quantités')
        check_petit_dej = QCheckBox()
        check_dej = QCheckBox()
        check_gouter = QCheckBox()
        check_diner = QCheckBox()
        
        self.mapper = QDataWidgetMapper()
        self.mapper.setModel(self.model)
        self.mapper.addMapping(self.age6, 2)
        self.mapper.addMapping(self.age6_12, 3)
        self.mapper.addMapping(self.age12, 4)
        self.mapper.addMapping(check_petit_dej, 5)
        self.mapper.addMapping(check_dej, 6)
        self.mapper.addMapping(check_gouter, 7)
        self.mapper.addMapping(check_diner, 8)

        h_layout = QHBoxLayout()
        piquenique_layout = QFormLayout()
        piquenique_layout.addRow('6', self.age6)
        piquenique_layout.addRow('6-12', self.age6_12)
        piquenique_layout.addRow('12', self.age12)
        h_layout.addLayout(piquenique_layout)
        p_repas_layout = QFormLayout()
        p_repas_layout.addRow('petit déjeuner', check_petit_dej)
        p_repas_layout.addRow('déjeuner', check_dej)
        p_repas_layout.addRow('goûter', check_gouter)
        p_repas_layout.addRow('diner', check_diner)
        h_layout.addLayout(p_repas_layout)
        h_layout.addWidget(self.submit_button)
        self.setLayout(h_layout)

        self.submit_button.clicked.connect(self.submit)

    def add_row(self):
        self.model.insertRow(self.model.rowCount())
        for i in range(5, 9): # because checkboxes are not init
            self.model.setData(
                self.model.index(self.model.rowCount() -1, i), 0)
        self.mapper.toLast()

    def submit(self):
        repas_id = self.parent.repas_model.data(
                self.parent.repas_model.index(0, 0))
        if not repas_id:
            QMessageBox.warning(self, 'Erreur', 'Veuillez créer un plat')
        self.model.setData(self.model.index(
            self.model.rowCount() -1, 1), repas_id)
        self.mapper.submit()
        submited = self.model.submitAll()
        if not submited:
            error = self.model.lastError()
            logging.warning(error.text())
        if submited:
            self.parent.compute_all_quantities()

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
    def __init__(self, parent=None):
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
        editor.setInsertPolicy(QComboBox.NoInsert)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(index.model().parent.qt_table_products)
        self.proxy.sort(1)
        self.model_p = index.model().parent.qt_table_products
        editor.setModel(self.proxy)
        editor.setModelColumn(1)
        editor.setEditable(True)
        editor.currentIndexChanged.connect(self.sender)
        return editor

    def setEditorData(self, editor, index):
        m = self.model_p
        self.initial_products = [m.data(m.index(i, 1)) for i in range(m.rowCount())]
    
    def setModelData(self, editor, model, index):
        product_idx = editor.currentIndex()
        products_model = index.model().parent.qt_table_products
        if not editor.currentText().rstrip(' '):
            logging.warning('Champs produit vide')
        elif editor.currentText() not in self.initial_products:
            reponse = QMessageBox.question(
                None, 'Produit inexistant', 
                "Ce produit n'existe pas. Voulez-vous l'ajouter ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
            if reponse == QMessageBox.Yes:
                logging.debug(self.parent.parent)
                p = ProductForm(
                    self.parent.parent, index=None, name=editor.currentText())
                if p:
                    #index.model().relationModel(1).select()
                    #editor.setCurrentText(p)
                    pass
        else:
            #self.parent.set_auto_quantity(editor.currentText(), index.row())
            self.parent.set_auto_q_fast(editor.currentText(), index.row())
            m = self.proxy
            idx_product = m.index(editor.currentIndex(), 0)
            model.setData(index, m.data(idx_product), None)
            #super(CompleterDelegate, self).setModelData(editor, model, index)
            self.parent.ingredients_model.submitAll()

class ProductOutputDelegate(QSqlRelationalDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        #model_products = index.model().relationModel(3)
        proxy = QSortFilterProxyModel()
        proxy.setSourceModel(self.parent.parent.model.qt_table_products)
        proxy.sort(1)
        editor.setModel(proxy)
        editor.setModelColumn(1)
        editor.setEditable(True)
        #editor.currentIndexChanged.connect(self.sender)
        return editor

    def setModelData(self, editor, model, index):
        #output_model = model
        #input_model = editor.model()
        #product_model = input_model.relationModel(3)
        #index_input = input_model.index(editor.currentIndex(), 3)
        product_id = self.parent.products_model.get_index_by_name(
            editor.currentText()).data()
        #name = input_model.data(index_input)
        #if name:
        #    product_model.setFilter("name = '" + name + "'")
        #value = product_model.data(product_model.index(0, 0))
        #logging.debug(value) # il faut récupéreer l'ID, pas le résultat de la relation...o
        logging.debug(product_id)
        model.setData(index, product_id)

class ProductInputDelegate(QSqlRelationalDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.parent.parent.model.qt_table_products)
        self.proxy.sort(1)
        editor.setModel(self.proxy)
        editor.setModelColumn(1)
        return editor

    def setModelData(self, editor, model, index):
        id_ = self.proxy.data(self.proxy.index(editor.currentIndex(), 0))
        model.setData(index, id_)

class PlatPrevNameDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_db = parent.parent.model
        self.parent = parent

    def setModelData(self, editor, model, index):
        plats_prev = self.model_db.get_plats_prev()
        super().setModelData(editor, model, index)
        if editor.text() in plats_prev.keys():
            reponse = QMessageBox.question(
                    None, "Copier l'existant ?", "Voulez-vous copier le plat "\
                    + "du même nom ?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes)
            if reponse == QMessageBox.Yes:
                id_source = plats_prev[editor.text()]
                id_dest = model.data(model.index(index.row(), 0))
                ingrs = self.model_db.get_ingrs_prev_by_plat(id_source)
                for ingr in ingrs:
                    self.model_db.set_(
                        {
                        'product_id':ingr[0],
                        'dishes_prev_id':id_dest,
                        'quantity':ingr[1]
                        },
                        'ingredients_prev')
                self.parent.select_ingredient()

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
