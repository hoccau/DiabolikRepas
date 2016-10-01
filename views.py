#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator
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

class ProductForm(Form):
    def __init__(self, parent=None):
        super(ProductForm, self).__init__(parent)

        self.fournisseurs = []

        comp = QCompleter(self.fournisseurs)
        
        self.fournisseur = QComboBox() #Choisir plutôt dans une liste de fournisseurs
        self.refresh_fournisseurs()
        self.fournisseur.setCompleter(comp)
        self.product = QLineEdit()
        self.price = QLineEdit()
        #self.price.decimals = 2
        #self.price.setInputMask('00.00€')
        regexp = QRegExp('\d[\d\,\.]+')
        self.price.setValidator(QRegExpValidator(regexp))
        self.quantity = QLineEdit()
        self.date = QCalendarWidget()

        self.add_field("Fournisseur:", self.fournisseur)
        self.add_field("Date:", self.date)
        self.add_field("Désignation", self.product)
        self.add_field("Prix (€):", self.price)
        self.add_field("quantité:", self.quantity)
        
        self.initUI()

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
            record["product"] = self.product.text()
            record["price"] = self.price.text()
            record["quantity"] = self.quantity.text()
            self.model.set_line(record)
            self.model.update_table_model()

    def refresh_fournisseurs(self):
        self.fournisseur.clear()
        for fournisseur, id_ in list(self.model.get_fournisseurs().items()):
            self.fournisseur.addItem(fournisseur)

class RepasForm(Form):
    def __init__(self, parent=None):
        super(RepasForm, self).__init__(parent)
        
        self.type = QComboBox()
        self.refresh_type()
        self.date = QCalendarWidget()
        self.add_field("Type:", self.type)
        self.add_field("Date:", self.date)
        self.addOutputButton = QPushButton("Ajouter une sortie")
        self.outputs = []
        self.add_output()
        self.initUI()
        self.grid.addWidget(self.addOutputButton, 100, 0)
        self.addOutputButton.clicked.connect(self.add_output)
    
    def refresh_type(self):
        self.type.clear()
        for type_, id_ in list(self.model.get_(['type','id'], 'type_repas').items()):
            self.type.addItem(type_)

    def add_output(self):
        output = OutputLine(self)
        self.outputs.append(output)

    def submit_datas(self):
        datas = {
            'type_id':str(self.model.get_(['type', 'id'], 'type_repas')[self.type.currentText()]),
            'date':self.date.selectedDate().toString('yyyy-MM-dd')
            }
        self.model.set_(datas, 'repas')
        repas_id = self.model.get_last_id(table='repas')
        datas = {'repas_id':repas_id, 'product_id':'', quantity:0}

class OutputLine():
    def __init__(self, parent):
        line_widgets = QHBoxLayout()
        self.parent = parent
        self.quantity = QSpinBox()
        self.quantity.setEnabled(False)
        self.produit = QLineEdit()
        line_widgets.addWidget(self.produit)
        line_widgets.addWidget(self.quantity)
        self.parent.add_layout("Sortie:", line_widgets)
        #self.quantity.valueChanged.connect(self.verif_stock)
        self.produit.editingFinished.connect(self.verif_stock)

    def verif_stock(self):
        quantity = self.parent.model.get_(
            values=['quantity'],
            table='reserve',
            condition=["product", "=", self.produit.text()])
        print("quantity in stock:", quantity)
        if len(quantity.keys()) >= 1:
            quantity = list(quantity)[0]
            self.quantity.setMaximum(quantity)
            self.quantity.setEnabled(True)
        else:
            QMessageBox.warning(self.parent, "Erreur", "Le produit n'est pas dans la réserve")

class InfosCentreDialog(QDialog):
    def __init__(self, parent=None):
        super(InfosCentreDialog, self).__init__(parent)

        model = parent.model.qt_table_infos
        mapper = QDataWidgetMapper(self)
        mapper.setModel(model)

        self.centre = QLineEdit()
        self.directeur_nom = QLineEdit()
        self.directeur_prenom = QLineEdit()

        mapper.addMapping(self.centre, model.fieldIndex("centre"))
        mapper.addMapping(self.directeur_nom, model.fieldIndex("directeur_nom"))
        mapper.addMapping(self.directeur_prenom, model.fieldIndex("directeur_prenom"))
        
        layout = QFormLayout(self)
        
        layout.addRow("Nom du centre:", self.centre)
        layout.addRow("Nom du directeur:", self.directeur_nom)
        layout.addRow("Prénom du directeur:", self.directeur_prenom)
        
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
        self.setMinimumSize(500, 500)
        
        grid = QGridLayout(self)

        self.exec_()

    def create_chart(self, dic):
        series = QPieSeries()
        for k, v in dic.items():
            series.append(k,v)
        chart = QChart()
        #chart.setTitle("Graphique")
        chart.addSeries(series)
        chartView = QChartView(chart)
        return chartView
        
    def create_text(self, dic, titre):
        layout = QFormLayout()
        box1 = QGroupBox(titre, parent=self)
        for k, v in list(dic.items()):
            layout.addRow(k+":", QLabel(str(v)+"€"))
        layout.addRow("Total:", QLabel(str(self.parent.model.get_total())+"€"))
        box1.setLayout(layout)
        return box1

