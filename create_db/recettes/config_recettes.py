# ============================================================
# CONFIGURATION — BASE DE RECETTES
# create_db/recettes/config_recettes.py
# ============================================================

import os
import sys
sys.dont_write_bytecode = True

# Remonte deux niveaux : recettes/ -> create_db/ -> data/
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
RECETTES_DB = os.path.join(DATA_DIR, "recettes.db")

# Cle API Spoonacular
SPOONACULAR_KEY = "206a53f3f304446b9778d72ff2d2702f"

# Langue de traduction cible
LANGUE_CIBLE = "fr"

# Nombre de recettes a importer par type
NB_RECETTES_PETIT_DEJ = 30
NB_RECETTES_DEJEUNER  = 60
NB_RECETTES_DINER     = 60

# Requetes de recherche par type de repas
# Format : (query_anglais, type_repas, type_seance)
REQUETES_RECETTES = [

    # ----------------------------------------------------------
    # PETIT-DEJEUNER
    # ----------------------------------------------------------
    ("oatmeal banana",              "petit_dej", "all"),
    ("overnight oats",              "petit_dej", "all"),
    ("scrambled eggs toast",        "petit_dej", "all"),
    ("yogurt granola fruit",        "petit_dej", "all"),
    ("protein pancakes",            "petit_dej", "musculation"),
    ("eggs avocado toast",          "petit_dej", "all"),
    ("smoothie bowl protein",       "petit_dej", "all"),
    ("chia pudding",                "petit_dej", "repos"),
    ("peanut butter oatmeal",       "petit_dej", "musculation"),
    ("fruit salad yogurt",          "petit_dej", "repos"),

    # ----------------------------------------------------------
    # DEJEUNER
    # ----------------------------------------------------------
    ("chicken rice vegetables",     "dejeuner",  "musculation"),
    ("salmon sweet potato",         "dejeuner",  "musculation"),
    ("tuna pasta salad",            "dejeuner",  "all"),
    ("chicken quinoa bowl",         "dejeuner",  "musculation"),
    ("lentil soup",                 "dejeuner",  "repos"),
    ("turkey rice broccoli",        "dejeuner",  "musculation"),
    ("chickpea salad",              "dejeuner",  "repos"),
    ("beef stir fry rice",          "dejeuner",  "musculation"),
    ("grilled chicken pasta",       "dejeuner",  "musculation"),
    ("tuna rice bowl",              "dejeuner",  "sprint"),
    ("egg fried rice",              "dejeuner",  "all"),
    ("chicken couscous",            "dejeuner",  "all"),
    ("salmon rice vegetables",      "dejeuner",  "musculation"),
    ("pork tenderloin potato",      "dejeuner",  "musculation"),
    ("chicken vegetable soup",      "dejeuner",  "repos"),

    # ----------------------------------------------------------
    # DINER
    # ----------------------------------------------------------
    ("chicken breast vegetables",   "diner",     "musculation"),
    ("salmon spinach",              "diner",     "recuperation"),
    ("turkey meatballs pasta",      "diner",     "musculation"),
    ("omelette vegetables",         "diner",     "repos"),
    ("chicken stir fry",            "diner",     "musculation"),
    ("tuna salad",                  "diner",     "repos"),
    ("lentils carrots",             "diner",     "recuperation"),
    ("baked salmon broccoli",       "diner",     "recuperation"),
    ("chicken rice zucchini",       "diner",     "musculation"),
    ("pork chop green beans",       "diner",     "musculation"),
    ("egg white omelette",          "diner",     "repos"),
    ("chicken chickpea",            "diner",     "recuperation"),
    ("beef rice peppers",           "diner",     "musculation"),
    ("turkey vegetable",            "diner",     "repos"),
    ("grilled chicken salad",       "diner",     "repos"),
]
