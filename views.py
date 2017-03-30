#!/usr/bin/python3
# -*- coding: utf-8 -*- 

from PyQt5.QtWidgets import *
from PyQt5.QtCore import QRegExp, QDate, Qt
from PyQt5.QtGui import QRegExpValidator, QStandardItem
from PyQt5.QtChart import *
from PyQt5.QtSql import QSqlRelationalDelegate

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
        add_fournisseur = QPushButton('Ajouter')
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
        self.grid.addWidget(add_fournisseur, self.field_index, 2)
        self.add_field("Date:", self.date)
        self.add_field("Désignation", self.product)
        self.add_field("quantité:", self.quantity)
        self.grid.addWidget(self.unit, self.field_index, 2)
        self.unit_label = QLabel("par pièce")
        self.add_field("Prix (€):", self.price)
        self.grid.addWidget(self.unit_label, self.field_index, 2)
        self.total = QLabel("")
        self.add_field("Prix total:", self.total)
        self.refresh_unit()

        self.price.editingFinished.connect(self.refresh_total)
        self.quantity.editingFinished.connect(self.refresh_total)
        self.unit.currentIndexChanged.connect(self.refresh_unit_label)
        add_fournisseur.clicked.connect(self.add_fournisseur)
        
        self.initUI()
    
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

    def refresh_unit_label(self):
        matching = {
           'unités':'par pièce',
           'Kilogrammes':'le kilo',
           'Litres':'le litre'
           }
        unit = matching[self.unit.currentText()]
        self.unit_label.setText(unit)

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
            unit_id = self.model.get_(
                ['id'],
                'units',
                condition='unit = ' + "'" + self.unit.currentText() + "'"
                )[0]['id']
            record["fournisseur_id"] = f_id
            record["date"] = self.date.selectedDate().toString('yyyy-MM-dd')
            record["product"] = self.product.text().lower()
            record["price"] = self.price.text()
            record["quantity"] = self.quantity.text()
            record["unit_id"] = unit_id
            self.model.add_product(record)
            self.model.qt_table_reserve.select()
            self.clear_all()

    def refresh_fournisseurs(self):
        self.fournisseur.clear()
        for fournisseur, id_ in list(self.model.get_fournisseurs().items()):
            self.fournisseur.addItem(fournisseur)

class RepasForm(Form):
    def __init__(self, parent=None, id_=None):
        super(RepasForm, self).__init__(parent)

        model = parent.model
        self.availables_products = self.model.get_all_products_names()
        self.already_used_products_ids = []

        self.type = QComboBox()
        self.refresh_type()
        self.date = QCalendarWidget()
        self.comment = QTextEdit()
        self.comment.setFixedHeight(50)
        self.add_field("Type:", self.type)
        self.add_field("Date:", self.date)
        self.add_field("Commentaire:", self.comment)

        #outputs 
        output_box = QGroupBox('', self)
        self.outputs_layout = QVBoxLayout()
        self.outputs = []
        output_box.setLayout(self.outputs_layout)
        self.add_field("sorties", output_box)
        self.add_output_button = QPushButton("Ajouter une sortie")
        self.grid.addWidget(self.add_output_button, 100, 0)
        self.add_output_button.clicked.connect(self.add_output)
        self.initUI()

        if not id_:
            if self.model.get_last_id('repas'):
                self.id = self.model.get_last_id('repas') + 1
            else:
                self.id = 1
            self.new_record = True
            output = OutputLine(self)
            self.outputs.append(output)
        else:
            self.id = id_
            self.new_record = False
            self.populate(id_)
        
        self.setWindowTitle("Repas #"+str(self.id))

    def populate(self, id_):
        repas = self.model.get_repas_by_id(id_)
        self.type.setCurrentText(repas['type'])
        self.date.setSelectedDate(QDate.fromString(repas['date'],'yyyy-MM-dd'))
        self.comment.setPlainText(repas['comment'])
        for output in repas['outputs']:
            output_line = OutputLine(self, output)
            self.outputs.append(output_line)
    
    def get_all_used_products_ids(self):
        result = []
        for output in self.outputs:
            if output.datas:
                result.append(output.datas['product_id'])
        return result
    
    def add_output(self):
        if len(self.outputs) > 0:
            if not self.outputs[-1].datas:
                QMessageBox.warning(self.parent, "Erreur",\
                    "Veuillez compléter la sortie de denrées.")
                return False
        output = OutputLine(self)
        self.outputs.append(output)

    def refresh_type(self):
        self.type.clear()
        for record in self.model.get_(['type'], 'type_repas'):
            self.type.addItem(record['type'])

    def verif_datas(self):
        pass

    def submit_datas(self):
        type_id = self.model.get_(
            ['id'],
            'type_repas',
            'type = \''+self.type.currentText()+'\''
            )[0]['id']
        datas = {
            'id':str(self.id),
            'type_id':str(type_id),
            'date':self.date.selectedDate().toString('yyyy-MM-dd'),
            'comment':self.comment.toPlainText()
            }
        if self.new_record:
            for output in self.outputs:
                if output.datas:
                    self.model.add_output(output.datas)
            submited = self.model.set_(datas, 'repas')
        else:
            self.model.delete('outputs', 'repas_id', str(self.id))
            for output in self.outputs:
                if output.datas:
                    self.model.add_output(output.datas)
            submited = self.model.update(datas, 'repas', 'id', str(self.id))
        if submited:
            self.parent.model.qt_table_reserve.select()
            self.parent.model.qt_table_repas.select()
            self.parent.model.qt_table_outputs.select()
            self.close()
        else:
            QMessageBox.warning(self.parent, "Erreur", "La requête n'a pas fonctionnée")

class OutputLine():
    def __init__(self, parent, datas=None):
        self.parent = parent
        self.line_widgets = QHBoxLayout()
        self.parent.outputs_layout.addLayout(self.line_widgets)
        self.produit = QComboBox()
        for product in self.parent.availables_products:
            self.produit.addItem(product)
        self.produit.setEditable(True)
        self.produit.clearEditText()
        self.produit.setCurrentIndex(-1)
        self.product_variant = QComboBox()
        self.product_variant.setEnabled(False)
        self.quantity = QDoubleSpinBox()
        self.quantity.setEnabled(False)
        self.suppr_button = QPushButton('Suppr')

        self.line_widgets.addWidget(self.produit)
        self.line_widgets.addWidget(self.product_variant)
        self.line_widgets.addWidget(self.quantity)
        self.line_widgets.addWidget(self.suppr_button)
        self.produit.currentIndexChanged.connect(self.select_product_name)
        self.product_variant.currentIndexChanged.connect(self.select_variant)
        self.quantity.valueChanged.connect(self.set_datas)
        self.suppr_button.clicked.connect(self.clear_layout)
        self.datas = False

        if datas:
            self.populate(datas)

    def populate(self, datas):
        self.produit.setCurrentText(datas['product_name'])
        self.select_product_name()
        for k, v in self.variants_indexes.items():
            if v[0] == datas['product_id']:
                variant_index = k
                break
        variant = self.variants_indexes[variant_index]
        self.product_variant.setCurrentText(
           self.variant_combo_name(variant[2], variant[3])
           )
        self.quantity.setValue(datas['quantity'])

    def select_product_name(self):
        self.product_variant.setEnabled(False) #by default
        self.product_variant.clear()
        self.datas = False
        stock = self.parent.model.get_product_datas(self.produit.currentText())
        if len(stock) >= 1:
            #struct: {combo_box_index:[id,quantity,prix,fournisseur]}
            self.variants_indexes = {}
            stock = [x for x in stock #filter already used\
                if x[0] not in self.parent.get_all_used_products_ids()]
            if len(stock) == 0:
                QMessageBox.warning(self.parent, "Erreur",\
                "Ce produit est déjà utilisé")
                return False
            else:
                stock = [x for x in stock if x[1] > 0] # filter 0 quantity
                if len(stock) == 0:
                    QMessageBox.warning(self.parent, "Erreur",\
                    "Ce produit est épuisé.")
                    return False
            for i, line in enumerate(stock):
                self.variants_indexes[i] = line
                self.product_variant.addItem(
                    self.variant_combo_name(line[2], line[3])
                    )
            if len(self.variants_indexes) >= 1:
                print("product_variant enabled")
                self.product_variant.setEnabled(True)
        elif self.produit.currentText() != "":
            QMessageBox.warning(self.parent, "Erreur",\
            "Le produit n'est pas dans la réserve")

    def variant_combo_name(self, price, supplier):
        return str(price)+"€ à "+ supplier

    def select_variant(self, index):
        if index != -1:
            self.quantity.setMaximum(self.variants_indexes[index][1])
            self.quantity.setEnabled(True)

    def set_datas(self):
        product_id = self.variants_indexes[self.product_variant.currentIndex()][0]
        self.datas = {'repas_id':self.parent.id,
            'product_id':product_id,
            'quantity':self.quantity.value()
            }
        #self.parent.already_used_products_ids.append(product_id)

    def clear_layout(self):
        while self.line_widgets.count():
            item = self.line_widgets.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                self.clearLayout(item.layout())
        self.parent.outputs.remove(self)
        self.parent.adjustSize()

class InfosCentreDialog(QDialog):
    def __init__(self, parent=None):
        super(InfosCentreDialog, self).__init__(parent)

        self.setWindowTitle("Informations du centre")
        self.parent = parent
        model = parent.model.qt_table_infos
        mapper = QDataWidgetMapper(self)
        mapper.setModel(model)

        self.centre = QLineEdit()
        self.directeur_nom = QLineEdit()
        self.nbr_children_6 = QSpinBox()
        self.nbr_children_6_12 = QSpinBox()
        self.nbr_children_12 = QSpinBox()
        self.nbr_children_6.setMinimum(0)
        self.nbr_children_6_12.setMinimum(0)
        self.nbr_children_12.setMinimum(0)
        self.place = QLineEdit()
        self.startdate = QDateEdit()
        self.startdate.setDate(QDate.currentDate())
        self.enddate = QDateEdit()
        self.enddate.setDate(QDate.currentDate())

        mapper.addMapping(self.centre, model.fieldIndex("centre"))
        mapper.addMapping(self.directeur_nom, model.fieldIndex("directeur_nom"))
        mapper.addMapping(self.nbr_children_6, model.fieldIndex("nombre_enfants_6"))
        mapper.addMapping(self.nbr_children_6_12, model.fieldIndex("nombre_enfants_6_12"))
        mapper.addMapping(self.nbr_children_12, model.fieldIndex("nombre_enfants_12"))
        mapper.addMapping(self.place, model.fieldIndex("place"))
        mapper.addMapping(self.startdate, model.fieldIndex("startdate"))
        mapper.addMapping(self.enddate, model.fieldIndex("enddate"))
        
        layout = QFormLayout(self)
        
        layout.addRow("Nom du centre:", self.centre)
        layout.addRow("Lieu:", self.place)
        layout.addRow("Nom du directeur:", self.directeur_nom)
        layout.addRow("Enfants de moins de 6 ans:", self.nbr_children_6)
        layout.addRow("Enfants entre 6 et 12 ans:", self.nbr_children_6_12)
        layout.addRow("Enfants de plus de 12 ans:", self.nbr_children_12)
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
        self.price_by_day = QLabel("")
        self.fill_date()
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
        self.display_price_by_repas(0)

    def fill_date(self):
        all_dates = self.parent.model.get_dates_repas()
        for date in all_dates:
            self.date.addItem(date)
        self.display_price_by_day(all_dates[0])

    def display_price_by_repas(self, index):
        repas_id = self.all_repas_dic[index]['id']
        price = self.parent.model.get_price_by_repas(repas_id)
        self.price_by_repas.setText(str(round(price, 2)) + " €")

    def display_price_by_day(self, day):
        price = self.parent.model.get_price_by_day(day)
        self.price_by_day.setText(str(round(price, 2)) + " €")

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

class Previsionnel(QDialog):
    def __init__(self, parent):
        super(Previsionnel, self).__init__(parent)

        self.calendar = QCalendarWidget()
        self.layout = QVBoxLayout()

        self.add_repas_button = QPushButton('+')
        self.add_plat_button = QPushButton('+')
        self.add_ingredient_button = QPushButton('+')

        self.del_repas_button = QPushButton('-')
        self.del_plat_button = QPushButton('-')
        self.del_ingredient_button = QPushButton('-')
        
        self.repas_prev_view, self.repas_box = self._create_view(
                'Repas', [self.add_repas_button, self.del_repas_button])
        self.plats_prev_view, self.plats_box = self._create_view(
                'Plats', [self.add_plat_button, self.del_plat_button])
        self.ingredients_prev_view, self.ingredients_box = self._create_view(
                'Ingredients', [self.add_ingredient_button, self.del_ingredient_button])

        self.layout.addWidget(self.calendar)
        self.layout.addWidget(self.repas_box)
        self.layout.addWidget(self.plats_box)
        self.layout.addWidget(self.ingredients_box)
        self.setLayout(self.layout)
        
        self.repas_model = parent.model.repas_prev_model
        self.plats_model = parent.model.plat_prev_model
        self.ingredients_model = parent.model.ingredient_prev_model
        
        self.calendar.selectionChanged.connect(self.select_repas)
        self.repas_prev_view.clicked.connect(self.select_plat)
        self.plats_prev_view.clicked.connect(self.select_ingredient)
        
        self.repas_prev_view.setModel(self.repas_model)
        self.repas_prev_view.setColumnHidden(0, True) # hide id
        self.repas_prev_view.setColumnHidden(2, True) # hide date

        self.plats_prev_view.setModel(self.plats_model)
        self.plats_prev_view.setColumnHidden(0, True)  #hide id
        self.plats_prev_view.setColumnHidden(2, True)  #hide repas_prev

        self.ingredients_prev_view.setModel(self.ingredients_model)
        self.ingredients_prev_view.setColumnHidden(0, True) #hide id
        self.ingredients_prev_view.setColumnHidden(2, True) #hide dish parent
        self.select_repas()
        
        self.add_repas_button.clicked.connect(self.add_repas)
        self.add_plat_button.clicked.connect(self.add_plat)
        self.add_ingredient_button.clicked.connect(self.add_ingredient)
        self.del_repas_button.clicked.connect(self.del_repas)
        self.del_plat_button.clicked.connect(self.del_plat)
        self.del_ingredient_button.clicked.connect(self.del_ingredient)

        self.exec_()
    
    def _create_view(self, box_name, buttons):
        """ Return a QTableView (with good relationnal delegate) and a box containing it """
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
        self.repas_model.setFilter("date = '"+self.date.toString('yyyy-MM-dd')+"'")
        self.repas_box.setTitle('Les repas du '+self.date.toString('dddd d MMM yyyy'))
        self.select_plat()

    def select_plat(self):
        row = self.repas_prev_view.selectionModel().currentIndex().row()
        id_ = self.repas_prev_view.model().record(row).value(0)
        self.current_repas_id = id_
        self.plats_model.setFilter("repas_prev_id = "+str(id_))
        self.plats_box.setTitle('Les plats du repas sélectionné')
        self.select_ingredient()

    def select_ingredient(self):
        row = self.plats_prev_view.selectionModel().currentIndex().row()
        id_ = self.plats_prev_view.model().record(row).value(0)
        self.current_plat_id = id_
        self.ingredients_box.setTitle('Les ingrédients du plat sélectionné')
        self.ingredients_model.setFilter(
                "dishes_prev_id = "+str(id_))

    def add_repas(self):
        self.repas_model.add_row(date=self.date.toString('yyyy-MM-dd'))
    
    def add_plat(self):
        self.plats_model.add_row(repas_id=self.current_repas_id)

    def add_ingredient(self):
        self.ingredients_model.add_row(plat_id=self.current_plat_id)

    def del_repas(self):
        reponse = QMessageBox.question(
                None, 'Sûr(e) ?', "Vous allez détruire définitivement ce repas"\
                + "ainsi que tous les plats et ingrédients associés. Êtes-vous sûr(e) ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
        if reponse == QMessageBox.Yes:
            self.repas_model.del_row(id=self.current_repas_id)
    
    def del_plat(self):
        reponse = QMessageBox.question(
                None, 'Sûr(e) ?', "Vous allez détruire définitivement ce plat"\
                + "ainsi que tous les ingrédients associés. Êtes-vous sûr(e) ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
        if reponse:
            self.plats_model.del_row(id=self.current_plat_id)

    def del_ingredient(self):
        reponse = QMessageBox.question(
                None, 'Sûr(e) ?', "Vous allez détruire définitivement cet ingrédient."\
                + " Êtes-vous sûr(e) ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No)
        if reponse:
            self.ingredients_model.del_row(id=None)

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
        print(parent)
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
