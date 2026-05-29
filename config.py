# ============================================================
# CONFIGURATION GLOBALE 
# ============================================================

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
sys.dont_write_bytecode = True

# ------------------------------------------------------------
# RACINE DU PROJET
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).parent.resolve()

# Charge .env si présent (local uniquement)
load_dotenv(ROOT_DIR / ".env")

# ------------------------------------------------------------
# RÉPERTOIRES
# ------------------------------------------------------------
DATA_DIR   = ROOT_DIR / "create_db"    / "data"
SUIVI_DIR  = ROOT_DIR / "suivi"        / "data"
OUTPUT_DIR = ROOT_DIR / "output"
OPTIM_DIR  = ROOT_DIR / "optimisation" / "data"

# ------------------------------------------------------------
# BASES DE DONNÉES
# ------------------------------------------------------------
NUTRITION_DB = DATA_DIR / "nutrition.db"
RECETTES_DB  = DATA_DIR / "recettes.db"

# ------------------------------------------------------------
# FICHIERS SOURCE
# ------------------------------------------------------------
CIQUAL_LOCAL      = DATA_DIR  / "ciqual_2020.xls"
SUIVI_POIDS_XLSX  = SUIVI_DIR / "suivi_poids.xlsx"
EXCEL_CONFIG_PATH = OPTIM_DIR / "athlete_config.xlsm"
EXCEL_CONFIG_XLSX = OPTIM_DIR / "athlete_config.xlsx"

# ------------------------------------------------------------
# APIs EXTERNES
# ------------------------------------------------------------
SPOONACULAR_KEY  = os.getenv("SPOONACULAR_KEY",  "")
PILOTERR_API_KEY = os.getenv("PILOTERR_API_KEY", "")

# ------------------------------------------------------------
# MAGASIN
# ------------------------------------------------------------
MAGASIN_FALLBACK   = "leclerc"
CACHE_PRIX_JOURS = 7

# ------------------------------------------------------------
# IMPORT RECETTES — Spoonacular
# ------------------------------------------------------------
LANGUE_CIBLE          = "fr"
NB_RECETTES_PETIT_DEJ = 30
NB_RECETTES_DEJEUNER  = 60
NB_RECETTES_DINER     = 60

REQUETES_RECETTES = [
    # PETIT-DÉJEUNER
    ("oatmeal banana",           "petit_dej", "all"),
    ("overnight oats",           "petit_dej", "all"),
    ("scrambled eggs toast",     "petit_dej", "all"),
    ("yogurt granola fruit",     "petit_dej", "all"),
    ("protein pancakes",         "petit_dej", "musculation"),
    ("eggs avocado toast",       "petit_dej", "all"),
    ("smoothie bowl protein",    "petit_dej", "all"),
    ("chia pudding",             "petit_dej", "repos"),
    ("peanut butter oatmeal",    "petit_dej", "musculation"),
    ("fruit salad yogurt",       "petit_dej", "repos"),
    # DÉJEUNER
    ("chicken rice vegetables",  "dejeuner",  "musculation"),
    ("salmon sweet potato",      "dejeuner",  "musculation"),
    ("tuna pasta salad",         "dejeuner",  "all"),
    ("chicken quinoa bowl",      "dejeuner",  "musculation"),
    ("lentil soup",              "dejeuner",  "repos"),
    ("turkey rice broccoli",     "dejeuner",  "musculation"),
    ("chickpea salad",           "dejeuner",  "repos"),
    ("beef stir fry rice",       "dejeuner",  "musculation"),
    ("grilled chicken pasta",    "dejeuner",  "musculation"),
    ("tuna rice bowl",           "dejeuner",  "sprint"),
    ("egg fried rice",           "dejeuner",  "all"),
    ("chicken couscous",         "dejeuner",  "all"),
    ("salmon rice vegetables",   "dejeuner",  "musculation"),
    ("pork tenderloin potato",   "dejeuner",  "musculation"),
    ("chicken vegetable soup",   "dejeuner",  "repos"),
    # DÎNER
    ("chicken breast vegetables","diner",     "musculation"),
    ("salmon spinach",           "diner",     "recuperation"),
    ("turkey meatballs pasta",   "diner",     "musculation"),
    ("omelette vegetables",      "diner",     "repos"),
    ("chicken stir fry",         "diner",     "musculation"),
    ("tuna salad",               "diner",     "repos"),
    ("lentils carrots",          "diner",     "recuperation"),
    ("baked salmon broccoli",    "diner",     "recuperation"),
    ("chicken rice zucchini",    "diner",     "musculation"),
    ("pork chop green beans",    "diner",     "musculation"),
    ("egg white omelette",       "diner",     "repos"),
    ("chicken chickpea",         "diner",     "recuperation"),
    ("beef rice peppers",        "diner",     "musculation"),
    ("turkey vegetable",         "diner",     "repos"),
    ("grilled chicken salad",    "diner",     "repos"),
]

# ------------------------------------------------------------
# OPTIMISATION NUTRITIONNELLE
# ------------------------------------------------------------
PROTEINES_MIN_PAR_KG  = 1.6
PROTEINES_MAX_PAR_KG  = 2.5
LIPIDES_MIN_PAR_KG    = 0.8
BUDGET_JOURNALIER_MAX = 15.0
NB_REPAS_PAR_JOUR     = 3
NB_JOURS_SEMAINE      = 7
NB_REPAS_SEMAINE      = NB_REPAS_PAR_JOUR * NB_JOURS_SEMAINE  # 21

# ------------------------------------------------------------
# PRIX & HISTORIQUE
# ------------------------------------------------------------
NB_SEMAINES_HISTORIQUE_PRIX = 12

# ------------------------------------------------------------
# PARAMÈTRES PAR OBJECTIF
# ------------------------------------------------------------
PARAMETRES_PAR_OBJECTIF = {
    "recomposition": {
        "direction"                      : "perte",
        "perte_optimale_min_kg"          :  0.3,
        "perte_optimale_max_kg"          :  0.7,
        "seuil_stagnation_kg"            :  0.1,
        "seuil_changement_rapide_kg"     :  1.0,
        "nb_semaines_stagnation"         :  2,
        "ajustement_deficit_stagnation"  :  100,
        "ajustement_deficit_rapide"      :  100,
        "ajustement_glucides_stagnation" : -0.10,
        "ajustement_glucides_rapide"     :  0.10,
        "deficit_min_absolu"             :    0,
        "deficit_max_absolu"             :  500,
        "surplus_min_absolu"             :    0,
        "surplus_max_absolu"             :    0,
    },
    "perte de poids": {
        "direction"                      : "perte",
        "perte_optimale_min_kg"          :  0.5,
        "perte_optimale_max_kg"          :  1.0,
        "seuil_stagnation_kg"            :  0.2,
        "seuil_changement_rapide_kg"     :  1.5,
        "nb_semaines_stagnation"         :  2,
        "ajustement_deficit_stagnation"  :  150,
        "ajustement_deficit_rapide"      :  150,
        "ajustement_glucides_stagnation" : -0.15,
        "ajustement_glucides_rapide"     :  0.10,
        "deficit_min_absolu"             :  200,
        "deficit_max_absolu"             :  750,
        "surplus_min_absolu"             :    0,
        "surplus_max_absolu"             :    0,
    },
    "prise de masse": {
        "direction"                      : "gain",
        "perte_optimale_min_kg"          :  0.2,
        "perte_optimale_max_kg"          :  0.5,
        "seuil_stagnation_kg"            :  0.1,
        "seuil_changement_rapide_kg"     :  0.7,
        "nb_semaines_stagnation"         :  2,
        "ajustement_deficit_stagnation"  :  100,
        "ajustement_deficit_rapide"      :  100,
        "ajustement_glucides_stagnation" :  0.10,
        "ajustement_glucides_rapide"     : -0.10,
        "deficit_min_absolu"             :    0,
        "deficit_max_absolu"             :    0,
        "surplus_min_absolu"             :  150,
        "surplus_max_absolu"             :  400,
    },
    "maintien": {
        "direction"                      : "maintien",
        "perte_optimale_min_kg"          : -0.2,
        "perte_optimale_max_kg"          :  0.2,
        "seuil_stagnation_kg"            :  0.0,
        "seuil_changement_rapide_kg"     :  0.5,
        "nb_semaines_stagnation"         :  4,
        "ajustement_deficit_stagnation"  :   50,
        "ajustement_deficit_rapide"      :   50,
        "ajustement_glucides_stagnation" :  0.05,
        "ajustement_glucides_rapide"     : -0.05,
        "deficit_min_absolu"             : -100,
        "deficit_max_absolu"             :  200,
        "surplus_min_absolu"             :    0,
        "surplus_max_absolu"             :  100,
    },
    "performance": {
        "direction"                      : "maintien",
        "perte_optimale_min_kg"          : -0.3,
        "perte_optimale_max_kg"          :  0.3,
        "seuil_stagnation_kg"            :  0.0,
        "seuil_changement_rapide_kg"     :  0.5,
        "nb_semaines_stagnation"         :  4,
        "ajustement_deficit_stagnation"  :   50,
        "ajustement_deficit_rapide"      :   50,
        "ajustement_glucides_stagnation" :  0.05,
        "ajustement_glucides_rapide"     : -0.05,
        "deficit_min_absolu"             : -200,
        "deficit_max_absolu"             :  100,
        "surplus_min_absolu"             :    0,
        "surplus_max_absolu"             :  200,
    },
}

# ------------------------------------------------------------
# FONCTION UTILITAIRE
# ------------------------------------------------------------
def get_parametres_objectif(objectif: str) -> dict:
    objectif_lower = objectif.strip().lower()
    for key, val in PARAMETRES_PAR_OBJECTIF.items():
        if key in objectif_lower:
            return {**val, "objectif_detecte": key}
    return {
        **PARAMETRES_PAR_OBJECTIF["recomposition"],
        "objectif_detecte": "recomposition"
    }

# ------------------------------------------------------------
# CRÉATION DES DOSSIERS AU DÉMARRAGE
# ------------------------------------------------------------
for _dir in [DATA_DIR, SUIVI_DIR, OUTPUT_DIR, OPTIM_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)
