# ============================================================
# INSERTION DES CATEGORIES ET MAPPING CIQUAL
# ============================================================

import sqlite3

# ------------------------------------------------------------
# Categories internes du projet
# ------------------------------------------------------------
CATEGORIES = [
    (1,  "Legumes crus",         "Legumes frais crus"),
    (2,  "Legumes cuits",        "Legumes cuits et surgeles"),
    (3,  "Fruits frais",         "Fruits frais et en conserve"),
    (4,  "Fruits secs",          "Fruits seches et oleagineux secs"),
    (5,  "Viandes",              "Viandes rouges et blanches"),
    (6,  "Poissons",             "Poissons et fruits de mer"),
    (7,  "Legumineuses",         "Lentilles, pois, haricots secs"),
    (8,  "Feculents",            "Cereales, pates, riz, pain"),
    (9,  "Produits laitiers",    "Lait, yaourts, fromages"),
    (10, "Oeufs",                "Oeufs entiers et derives"),
    (11, "Matieres grasses",     "Huiles, beurre, margarines"),
    (12, "Epices et aromates",   "Epices, herbes, condiments"),
    (13, "Noix et graines",      "Oleagineux, graines"),
    (14, "Boissons",             "Eau, jus, boissons"),
    (15, "Produits sucres",      "Miel, confiture, chocolat"),
    (16, "Plats composes",       "Plats prepares, entrees composees"),
    (17, "Substituts proteines", "Proteines en poudre, tofu, tempeh"),
]


# ------------------------------------------------------------
# Mapping EXACT sous-groupes CIQUAL -> categorie_id interne
# La distinction cru/cuit est faite via les mots-cles
# dans le nom de l aliment (traite dans l inserter)
# ------------------------------------------------------------
CIQUAL_SSGROUP_MAPPING = {

    # --- Legumes crus (1) et cuits (2) ---
    # La distinction est faite dans get_categorie_id()
    # selon les mots-cles dans le nom de l aliment
    "légumes"                                           : 1,
    "pommes de terre et autres tubercules"              : 1,

    # --- Fruits frais (3) ---
    "fruits"                                            : 3,

    # --- Viandes (5) ---
    "viandes crues"                                     : 5,
    "viandes cuites"                                    : 5,
    "charcuteries et assimilés"                         : 5,
    "autres produits à base de viande"                  : 5,

    # --- Poissons (6) ---
    "poissons crus"                                     : 6,
    "poissons cuits"                                    : 6,
    "produits à base de poissons et produits de la mer" : 6,
    "mollusques et crustacés crus"                      : 6,
    "mollusques et crustacés cuits"                     : 6,

    # --- Legumineuses (7) ---
    "légumineuses"                                      : 7,

    # --- Feculents (8) ---
    "pâtes, riz et céréales"                            : 8,
    "pains et assimilés"                                : 8,
    "biscuits apéritifs"                                : 8,
    "barres céréalières"                                : 8,
    "céréales de petit-déjeuner"                        : 8,

    # --- Produits laitiers (9) ---
    "fromages et assimilés"                             : 9,
    "laits"                                             : 9,
    "produits laitiers frais et assimilés"              : 9,
    "crèmes et spécialités à base de crème"             : 9,

    # --- Oeufs (10) ---
    "œufs"                                              : 10,

    # --- Matieres grasses (11) ---
    "huiles et graisses végétales"                      : 11,
    "beurres"                                           : 11,
    "margarines"                                        : 11,
    "autres matières grasses"                           : 11,
    "huiles de poissons"                                : 11,

    # --- Epices et aromates (12) ---
    "épices"                                            : 12,
    "herbes"                                            : 12,
    "condiments"                                        : 12,
    "sauces"                                            : 12,
    "sels"                                              : 12,
    "aides culinaires"                                  : 12,
    "ingrédients divers"                                : 12,

    # --- Noix et graines (13) ---
    "fruits à coque et graines oléagineuses"            : 13,

    # --- Boissons (14) ---
    "eaux"                                              : 14,
    "boissons sans alcool"                              : 14,
    "boisson alcoolisées"                               : 14,

    # --- Produits sucres (15) ---
    "sucres, miels et assimilés"                        : 15,
    "confitures et assimilés"                           : 15,
    "chocolats et produits à base de chocolat"          : 15,
    "confiseries non chocolatées"                       : 15,
    "gâteaux et pâtisseries"                            : 15,
    "viennoiseries"                                     : 15,
    "biscuits sucrés"                                   : 15,
    "glaces"                                            : 15,
    "sorbets"                                           : 15,
    "desserts glacés"                                   : 15,

    # --- Plats composes (16) ---
    "plats composés"                                    : 16,
    "soupes"                                            : 16,
    "sandwichs"                                         : 16,
    "pizzas, tartes et crêpes salées"                   : 16,
    "feuilletées et autres entrées"                     : 16,
    "salades composées et crudités"                     : 16,
    "petits pots salés et plats infantiles"             : 16,
    "céréales et biscuits infantiles"                   : 16,
    "desserts infantiles"                               : 16,
    "laits et boissons infantiles"                      : 16,

    # --- Substituts proteines (17) ---
    "substitus de produits carnés"                      : 17,
    "aides culinaires et ingrédients pour végétariens"  : 17,
    "denrées destinées à une alimentation particulière" : 17,

    # --- Cas particuliers ---
    "algues"                                            : 1,
    "-"                                                 : 16,
}

# ------------------------------------------------------------
# Mots-cles pour distinguer fruits frais / fruits secs
# et legumes crus / legumes cuits
# Appliques dans get_categorie_id() de l inserter
# ------------------------------------------------------------
KEYWORDS_LEGUMES_CUITS = [
    "cuit", "cuite", "cuits", "cuites",
    "surgel", "vapeur", "poche", "grille",
    "braise", "etuve", "bouilli",
    "conserve", "en boite",
]

KEYWORDS_FRUITS_SECS = [
    "sec", "seche", "secs", "seches",
    "deshydrat", "confit", "confite",
    "raisin sec", "datte", "pruneau",
    "abricot sec", "figue seche",
    "mangue sech", "cranberry",
    "banane sech",
]

# ------------------------------------------------------------
# Fallback niveau groupe si sous-groupe non reconnu
# ------------------------------------------------------------
CIQUAL_GROUP_FALLBACK = {
    "fruits, légumes, légumineuses et oléagineux"       : 1,
    "viandes, œufs, poissons et assimilés"              : 5,
    "produits laitiers et assimilés"                    : 9,
    "produits céréaliers"                               : 8,
    "matières grasses"                                  : 11,
    "produits sucrés"                                   : 15,
    "eaux et autres boissons"                           : 14,
    "entrées et plats composés"                         : 16,
    "aides culinaires et ingrédients divers"            : 12,
    "aliments infantiles"                               : 16,
    "glaces et sorbets"                                 : 15,
}


def insert_categories(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    for cat in CATEGORIES:
        cursor.execute("""
            INSERT OR IGNORE INTO categories (id, nom, description)
            VALUES (?, ?, ?)
        """, cat)
    conn.commit()
    print("[OK] Categories inserees.")