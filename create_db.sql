CREATE TABLE infos(
centre varchar(20),
directeur_nom varchar(20),
nombre_enfants int,
place varchar(20),
startdate varchar(10),
enddate varchar(10)
);
INSERT INTO infos(
centre, directeur_nom, nombre_enfants, place, startdate, enddate) VALUES (
NULL, NULL, NULL, NULL, NULL, NULL);

CREATE TABLE fournisseurs(
id integer PRIMARY KEY,
NOM varchar(20)
);
CREATE TABLE products(
id integer PRIMARY KEY,
name VARCHAR(20) NOT NULL
);
CREATE TABLE reserve(
id integer PRIMARY KEY,
Fournisseur_id integer NOT NULL,
Date varchar(10),
product_id INTEGER NOT NULL,
Prix real NOT NULL,
start_quantity real NOT NULL,
quantity real NOT NULL,
unit_id integer NOT NULL,
FOREIGN KEY (unit_id) REFERENCES units(id)
FOREIGN KEY (Fournisseur_id) REFERENCES fournisseurs(id)
FOREIGN KEY (product_id) REFERENCES products(id)
);
CREATE UNIQUE INDEX idx_NOM ON fournisseurs (NOM);

CREATE TABLE units(
id integer PRIMARY KEY,
unit varchar(20) NOT NULL
);
INSERT INTO units(unit) VALUES
('unités'), ('Kilogrammes'), ('Litres');

CREATE TABLE repas(
id integer PRIMARY KEY,
date varchar(10) NOT NULL,
type_id integer NOT NULL,
comment TEXT,
FOREIGN KEY (type_id) REFERENCES type_repas(id)
);
CREATE TABLE type_repas(
id integer PRIMARY KEY,
type varchar(20)
);
INSERT INTO type_repas(type) VALUES ('petit déjeuner');
INSERT INTO type_repas(type) VALUES ('déjeuner');
INSERT INTO type_repas(type) VALUES ('gouter');
INSERT INTO type_repas(type) VALUES ('souper');
INSERT INTO type_repas(type) VALUES ('cinquième');
INSERT INTO type_repas(type) VALUES ('autre');

CREATE TABLE outputs(
id integer PRIMARY KEY,
quantity integer,
repas_id integer,
stock_id integer,
FOREIGN KEY (repas_id) REFERENCES repas(id)
FOREIGN KEY (stock_id) REFERENCES reserve(id)
);

CREATE TABLE dishes(
id integer PRIMARY KEY,
name VARCHAR(20) NOT NULL,
ingredients_rel_id NOT NULL,
FOREIGN KEY (ingredients_rel_id) REFERENCES dishes_ingredients_rel(id)
);

CREATE TABLE ingredients(
id integer PRIMARY KEY,
product_id INTEGER NOT NULL,
quantity REAL,
FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE dishes_ingredients_rel(
id INTEGER PRIMARY KEY,
dish_id INTEGER NOT NULL,
ingredient_id INTEGER NOT NULL,
FOREIGN KEY (dish_id) REFERENCES dishes(id)
FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
);
