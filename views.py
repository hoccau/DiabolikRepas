#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QRegExp, QDate
from PyQt5.QtGui import QRegExpValidator, QIntValidator
from PyQt5.QtChart import *

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

class ProductForm(Form):
    def __init__(self, parent=None):
        super(ProductForm, self).__init__(parent)

        self.setWindowTitle("Denrées")
        self.fournisseurs = []

        comp = QCompleter(self.fournisseurs)
        
        self.fournisseur = QComboBox()
        self.refresh_fournisseurs()
        self.fournisseur.setCompleter(comp)
        self.product = QLineEdit()
        self.price = QLineEdit()
        regexp = QRegExp('\d[\d\,\.]+')
        self.price.setValidator(QRegExpValidator(regexp))
        self.quantity = QLineEdit()
        self.unit = QComboBox()
        self.date = QCalendarWidget()

        self.add_field("Fournisseur:", self.fournisseur)
        self.add_field("Date:", self.date)
        self.add_field("Désignation", self.product)
        self.add_field("Prix (€):", self.price)
        self.add_field("quantité:", self.quantity)
        self.grid.addWidget(self.unit, self.field_index, 2)
        self.total = QLabel("")
        self.add_field("Prix total:", self.total)
        self.refresh_unit()

        self.price.editingFinished.connect(self.refresh_total)
        self.quantity.editingFinished.connect(self.refresh_total)
        
        self.initUI()

    def refresh_total(self):
        if self.quantity.text() and self.price.text():
            price = float(self.price.text())
            quantity = float(self.quantity.text())
            total = round(price * quantity, 2)
            self.total.setText(str(total))

    def clear_all(self):
        self.quantity.clear()
        self.product.clear()
        self.price.clear()

    def refresh_unit(self):
        self.unit.clear()
        for unit in self.model.get_(['unit'], 'units'):
            self.unit.addItem(unit['unit'])

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
            record["product"] = self.product.text().lower()
            record["price"] = self.price.text()
            record["quantity"] = self.quantity.text()
            self.model.set_line(record)
            self.model.update_table_model()
            self.clear_all()

    def refresh_fournisseurs(self):
        self.fournisseur.clear()
        for fournisseur, id_ in list(self.model.get_fournisseurs().items()):
            self.fournisseur.addItem(fournisseur)

class OutputForm(Form):
    def __init__(self, parent=None, repas_id=None):
        super(OutputForm, self).__init__(parent)

        self.setWindowTitle('Sortie de denrées')
        repas = parent.model.get_repas_by_id(repas_id)
        self.setWindowTitle(repas['type']+" du "+repas['date'])
        self.repas_id = repas_id
        self.addOutputButton = QPushButton("Ajouter une sortie")
        self.outputs = []
        self.outputs.append(OutputLine(self))
        self.grid.addWidget(self.addOutputButton, 100, 0)
        self.addOutputButton.clicked.connect(self.add_output)
        self.initUI()
    
    def add_output(self):
        submit = self.outputs[-1].submit_datas()
        if submit:
            output = OutputLine(self)
            self.outputs.append(output)

    def submit_datas(self):
        submit = self.outputs[-1].submit_datas()
        if submit:
            self.close()

class RepasForm(Form):
    def __init__(self, parent=None):
        super(RepasForm, self).__init__(parent)
        
        self.setWindowTitle("Repas")
        self.type = QComboBox()
        self.refresh_type()
        self.date = QCalendarWidget()
        self.add_field("Type:", self.type)
        self.add_field("Date:", self.date)
        self.initUI()
    
    def refresh_type(self):
        self.type.clear()
        for record in self.model.get_(['type'], 'type_repas'):
            self.type.addItem(record['type'])

    def submit_datas(self):
        type_id = self.model.get_(
            ['id'],
            'type_repas',
            ['type','=',self.type.currentText()]
            )[0]['id']
        datas = {
            'type_id':str(type_id),
            'date':self.date.selectedDate().toString('yyyy-MM-dd')
            }
        submited = self.model.set_(datas, 'repas')
        if submited:
            self.parent.add_outputs(self.model.get_last_id('repas'))
            self.close()
        else:
            QMessageBox.warning(self.parent, "Erreur", "La requête n'a pas fonctionnée")

class OutputLine():
    def __init__(self, parent):
        line_widgets = QHBoxLayout()
        self.parent = parent
        self.quantity = QSpinBox()
        self.quantity.setEnabled(False)
        self.product_variant = QComboBox()
        self.product_variant.setEnabled(False)
        self.produit = QLineEdit()
        self.produit.setCompleter(QCompleter(self.get_products()))
        line_widgets.addWidget(self.produit)
        line_widgets.addWidget(self.product_variant)
        line_widgets.addWidget(self.quantity)
        self.parent.add_layout("Sortie:", line_widgets)
        #self.quantity.valueChanged.connect(self.verif_stock)
        self.produit.editingFinished.connect(self.select_variant)
        self.product_variant.currentIndexChanged.connect(self.select_quantity)
        self.ready_to_submit = False

    def get_products(self):
        records = self.parent.model.get_(['product'], 'reserve', distinct=True)
        result = []
        for record in records:
            result.append(record['product'])
        return result

    def select_variant(self):
        self.product_variant.setEnabled(False)
        self.product_variant.clear()
        stock = self.parent.model.get_product_datas(self.produit.text())
        print("stock:",stock)
        if len(stock) >= 1:
            self.indexes = {}
            for i, line in enumerate(stock):
                self.indexes[i] = line
                self.product_variant.addItem(str(line[2])+"€ à "+ line[3])
            self.product_variant.setEnabled(True)
        elif self.produit.text() != "":
            QMessageBox.warning(self.parent, "Erreur",\
            "Le produit n'est pas dans la réserve")

    def select_quantity(self, index):
        if index != -1:
            self.quantity.setMaximum(self.indexes[index][1])
            self.quantity.setEnabled(True)
            self.ready_to_submit = True

    def submit_datas(self):
        if self.ready_to_submit:
            product_id = self.indexes[self.product_variant.currentIndex()][0]
            datas = {'repas_id':self.parent.repas_id,
            'product_id':product_id,
            'quantity':self.quantity.value()
            }
            self.parent.model.add_output(datas)
            self.parent.model.update_table_model()
            return True
        else:
            QMessageBox.warning(self.parent, "Erreur",\
            "Veuillez compléter la sortie avant d'en ajouter une nouvelle.")
            return False

class InfosCentreDialog(QDialog):
    def __init__(self, parent=None):
        super(InfosCentreDialog, self).__init__(parent)

        self.setWindowTitle("Informations du centre")
        model = parent.model.qt_table_infos
        mapper = QDataWidgetMapper(self)
        mapper.setModel(model)

        self.centre = QLineEdit()
        self.directeur_nom = QLineEdit()
        self.nbr_children = QLineEdit()
        validator = QIntValidator()
        validator.setBottom(0)
        self.nbr_children.setValidator(validator)
        self.place = QLineEdit()
        self.startdate = QDateEdit()
        self.startdate.setDate(QDate.currentDate())
        self.enddate = QDateEdit()
        self.enddate.setDate(QDate.currentDate())

        mapper.addMapping(self.centre, model.fieldIndex("centre"))
        mapper.addMapping(self.directeur_nom, model.fieldIndex("directeur_nom"))
        mapper.addMapping(self.nbr_children, model.fieldIndex("nombre_enfants"))
        mapper.addMapping(self.place, model.fieldIndex("place"))
        mapper.addMapping(self.startdate, model.fieldIndex("startdate"))
        mapper.addMapping(self.enddate, model.fieldIndex("enddate"))
        
        layout = QFormLayout(self)
        
        layout.addRow("Nom du centre:", self.centre)
        layout.addRow("Lieu:", self.place)
        layout.addRow("Nom du directeur:", self.directeur_nom)
        layout.addRow("Nombre d'enfants:", self.nbr_children)
        layout.addRow("Début:", self.startdate)
        layout.addRow("Fin:", self.enddate)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            self)
        buttons.accepted.connect(mapper.submit)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        mapper.toFirst()
        self.exec_()

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
        self.fill_repas()
        box_repas = self.create_box('Prix par repas', [self.repas, self.price_by_repas])

        self.date = QComboBox()
        self.fill_date()
        self.price_by_day = QLabel("")
        box_day = self.create_box('Prix par journée', [self.date, self.price_by_day])
        self.grid.addWidget(box_repas, 0, 0)
        self.grid.addWidget(box_day, 0, 1)
        self.repas.currentIndexChanged.connect(self.display_price_by_repas)
        self.date.currentTextChanged.connect(self.display_price_by_day)

        self.exec_()

    def fill_repas(self):
        all_repas = self.parent.model.get_all_repas()
        self.all_repas_dic = {}
        for i, repas in enumerate(all_repas):
            self.all_repas_dic[i] = repas
            self.repas.addItem(repas['type']+" du "+repas['date'])

    def fill_date(self):
        all_dates = self.parent.model.get_dates_repas()
        for date in all_dates:
            self.date.addItem(date)

    def display_price_by_repas(self, index):
        repas_id = self.all_repas_dic[index]['id']
        price = self.parent.model.get_price_by_repas(repas_id)
        self.price_by_repas.setText(str(price) + " €")

    def display_price_by_day(self, day):
        price = self.parent.model.get_price_by_day(day)
        self.price_by_day.setText(str(price) + " €")

    def create_chart(self, dic):
        series = QPieSeries()
        for k, v in dic.items():
            series.append(k,v)
        chart = QChart()
        #chart.setTitle("Graphique")
        chart.addSeries(series)
        chartView = QChartView(chart)
        return chartView
        
    def create_box(self, titre, widgets):
        layout = QGridLayout()
        box = QGroupBox(titre, parent=self)
        for i, widget in enumerate(widgets):
            layout.addWidget(widget, self.grid_index, i)
        self.grid_index += 1
        box.setLayout(layout)
        return box

