PRAGMA foreign_keys = ON;
PRAGMA encoding = "UTF-8";

CREATE TABLE infos(
centre varchar(20),
directeur_nom varchar(20),
place varchar(20),
startdate varchar(10),
enddate varchar(10)
);
INSERT INTO infos
    VALUES (NULL, NULL, NULL, NULL, NULL);

CREATE TABLE infos_periodes(
    id integer PRIMARY KEY,
    date_start varchar(10),
    date_stop varchar(10),
    nombre_enfants_6 int,
    nombre_enfants_6_12 int,
    nombre_enfants_12 int
    );

CREATE TABLE fournisseurs(
id integer PRIMARY KEY,
NOM varchar(20)
);
CREATE UNIQUE INDEX idx_NOM ON fournisseurs (NOM);

CREATE TABLE products(
id integer PRIMARY KEY,
name VARCHAR(20) NOT NULL,
unit_id integer NOT NULL,
recommended_6 real,
recommended_6_12 real,
recommended_12 real,
fournisseur_id integer,
FOREIGN KEY (unit_id) REFERENCES units(id)
FOREIGN KEY (fournisseur_id) REFERENCES fournisseurs(id)
);
CREATE UNIQUE INDEX idx_name ON products (name);

CREATE TABLE inputs(
id integer PRIMARY KEY,
Fournisseur_id integer NOT NULL,
Date varchar(10),
product_id INTEGER NOT NULL,
ingredients_prev_id INTEGER,
Prix real NOT NULL,
quantity real NOT NULL,
FOREIGN KEY (Fournisseur_id) REFERENCES fournisseurs(id)
FOREIGN KEY (product_id) REFERENCES products(id)
FOREIGN KEY (ingredients_prev_id) REFERENCES ingredients_prev(id)
);
CREATE UNIQUE INDEX idx_ingredients_prev_id ON inputs (ingredients_prev_id);

CREATE TABLE units(
id integer PRIMARY KEY,
unit varchar(20) NOT NULL
);
INSERT INTO units(unit) VALUES
('Unités'), ('Kilogrammes'), ('Litres');

CREATE TABLE repas_prev(
id integer PRIMARY KEY,
date varchar(10) NOT NULL,
type_id integer NOT NULL,
FOREIGN KEY (type_id) REFERENCES type_repas(id)
);

CREATE TABLE dishes_types(
id integer PRIMARY KEY,
type varchar(30)
);
INSERT INTO dishes_types(type) VALUES
('entrée'), ('plat'), ('dessert'), ('autre');

CREATE TABLE dishes_prev(
id integer PRIMARY KEY,
name varchar(50),
repas_prev_id integer NOT NULL,
type_id integer,
FOREIGN KEY (repas_prev_id) REFERENCES repas_prev(id) ON DELETE CASCADE
FOREIGN KEY (type_id) REFERENCES dishes_types(id)
);

CREATE TABLE ingredients_prev(
id integer PRIMARY KEY,
product_id integer NOT NULL,
dishes_prev_id integer NOT NULL,
quantity real NOT NULL,
FOREIGN KEY (product_id) REFERENCES products(id)
FOREIGN KEY (dishes_prev_id) REFERENCES dishes_prev(id) ON DELETE CASCADE
);

CREATE TABLE repas(
id integer PRIMARY KEY,
date varchar(10) NOT NULL,
type_id integer NOT NULL,
repas_prev_id integer,
comment TEXT,
FOREIGN KEY (type_id) REFERENCES type_repas(id) 
FOREIGN KEY (repas_prev_id) REFERENCES repas_prev(id)
);

CREATE TABLE type_repas(
id integer PRIMARY KEY,
type varchar(20)
);
INSERT INTO type_repas(type) VALUES ('petit déjeuner');
INSERT INTO type_repas(type) VALUES ('déjeuner');
INSERT INTO type_repas(type) VALUES ('goûter');
INSERT INTO type_repas(type) VALUES ('dîner');
INSERT INTO type_repas(type) VALUES ('piquenique');
INSERT INTO type_repas(type) VALUES ('autre');

CREATE TABLE piquenique_conf(
    id INTEGER PRIMARY KEY,
    repas_prev_id INTEGER,
    nombre_enfants_6 int,
    nombre_enfants_6_12 int,
    nombre_enfants_12 int,
    petit_dej int,
    dej int,
    gouter int,
    diner int,
    FOREIGN KEY (repas_prev_id) REFERENCES repas_prev(id) ON DELETE CASCADE
    );
CREATE UNIQUE INDEX idx_piquenique_conf ON piquenique_conf (repas_prev_id);

CREATE TABLE outputs(
id integer PRIMARY KEY,
quantity real,
repas_id integer NOT NULL,
product_id integer,
FOREIGN KEY (repas_id) REFERENCES repas(id) ON DELETE CASCADE,
FOREIGN KEY (product_id) REFERENCES products(id)
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

CREATE VIEW `xml_export` AS
SELECT repas_prev.id, repas_prev.date, type_repas.type, 
dishes_prev.id, dishes_prev.name, dishes_types.type,
ingredients_prev.id, products.name, products.recommended_6, products.recommended_6_12, 
products.recommended_12, quantity, units.unit, 
infos_periodes.nombre_enfants_6, infos_periodes.nombre_enfants_6_12, infos_periodes.nombre_enfants_12 
FROM ingredients_prev 
INNER JOIN dishes_prev ON dishes_prev.id = ingredients_prev.dishes_prev_id
INNER JOIN repas_prev ON repas_prev.id = dishes_prev.repas_prev_id 
INNER JOIN products ON products.id = ingredients_prev.product_id 
INNER JOIN type_repas ON type_repas.id = repas_prev.type_id 
INNER JOIN dishes_types ON dishes_prev.type_id = dishes_types.id
INNER JOIN units ON units.id = products.unit_id 
INNER JOIN infos_periodes ON repas_prev.date >= infos_periodes.date_start 
AND repas_prev.date <=infos_periodes.date_stop ORDER BY repas_prev.date;

CREATE VIEW `liste_courses` AS
SELECT fournisseurs.nom as 'fournisseur', products.name as 'product', 
total(quantity), units.unit, repas_prev.date
FROM ingredients_prev
INNER JOIN dishes_prev ON dishes_prev.id = ingredients_prev.dishes_prev_id
INNER JOIN repas_prev ON repas_prev.id = dishes_prev.repas_prev_id
INNER JOIN products ON products.id = ingredients_prev.product_id
INNER JOIN units ON units.id = products.unit_id
LEFT JOIN fournisseurs ON fournisseurs.id = products.fournisseur_id
GROUP BY products.id
ORDER BY fournisseurs.nom;

