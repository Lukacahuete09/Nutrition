# ============================================================
# IMPORT DES RECETTES DEPUIS SPOONACULAR
# create_db/recettes/spoonacular_importer.py
# ============================================================

import sys
import os
import requests
import time
import sqlite3
from pathlib import Path
from datetime import datetime
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

from config import (
    SPOONACULAR_KEY,
    REQUETES_RECETTES,
    NB_RECETTES_PETIT_DEJ,
    NB_RECETTES_DEJEUNER,
    NB_RECETTES_DINER,
)

BASE_URL = "https://api.spoonacular.com"
HEADERS  = {"x-api-key": SPOONACULAR_KEY}

# Pause entre les appels pour respecter les limites
PAUSE_SECONDES = 1.0


# ------------------------------------------------------------
# TRADUCTION SIMPLE EN -> FR
# Utilise un dictionnaire de termes courants
# Pour eviter de dependre d une API de traduction
# ------------------------------------------------------------
TRADUCTIONS_BASIQUES = {
    "chicken"       : "poulet",
    "rice"          : "riz",
    "salmon"        : "saumon",
    "tuna"          : "thon",
    "beef"          : "boeuf",
    "pork"          : "porc",
    "turkey"        : "dinde",
    "egg"           : "oeuf",
    "eggs"          : "oeufs",
    "oatmeal"       : "flocons d avoine",
    "oats"          : "avoine",
    "broccoli"      : "brocoli",
    "spinach"       : "epinard",
    "carrot"        : "carotte",
    "zucchini"      : "courgette",
    "pepper"        : "poivron",
    "tomato"        : "tomate",
    "potato"        : "pomme de terre",
    "sweet potato"  : "patate douce",
    "pasta"         : "pates",
    "bread"         : "pain",
    "yogurt"        : "yaourt",
    "milk"          : "lait",
    "butter"        : "beurre",
    "oil"           : "huile",
    "olive oil"     : "huile d olive",
    "garlic"        : "ail",
    "onion"         : "oignon",
    "lemon"         : "citron",
    "salt"          : "sel",
    "pepper"        : "poivre",
    "chickpea"      : "pois chiche",
    "lentil"        : "lentille",
    "banana"        : "banane",
    "strawberry"    : "fraise",
    "blueberry"     : "myrtille",
    "apple"         : "pomme",
    "avocado"       : "avocat",
    "quinoa"        : "quinoa",
    "couscous"      : "couscous",
    "pancake"       : "pancake",
    "smoothie"      : "smoothie",
    "bowl"          : "bol",
    "salad"         : "salade",
    "soup"          : "soupe",
    "stir fry"      : "poele",
    "grilled"       : "grille",
    "baked"         : "au four",
    "roasted"       : "roti",
    "scrambled"     : "brouille",
    "fried"         : "frit",
    "steamed"       : "vapeur",
    "boiled"        : "bouilli",
    "brown"         : "",
    "white"         : "",
    "lean"          : "maigre",
    "low fat"       : "allege",
    "healthy"       : "sain",
    "protein"       : "proteine",
    "high protein"  : "riche en proteines",
    "green beans"   : "haricots verts",
    "mushroom"      : "champignon",
    "peanut butter" : "beurre de cacahuete",
    "chia"          : "chia",
    "granola"       : "granola",
    "overnight"     : "nuit",
    "toast"         : "toast",
    "meatballs"     : "boulettes de viande",
    "omelette"      : "omelette",
    "vegetable"     : "legume",
    "vegetables"    : "legumes",
    "with"          : "aux",
    "and"           : "et",
}


def _traduire_titre(titre_en: str) -> str:
    """
    Traduit un titre de recette anglais en francais
    via un dictionnaire de termes courants.
    """
    titre_lower = titre_en.lower()
    for en, fr in sorted(
        TRADUCTIONS_BASIQUES.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):
        titre_lower = titre_lower.replace(en, fr)

    # Nettoyer les espaces multiples
    titre_fr = " ".join(titre_lower.split())

    # Capitaliser la premiere lettre
    return titre_fr.capitalize()


def _traduire_instruction(instruction_en: str) -> str:
    """
    Traduit une instruction de recette.
    Version simplifiee : remplacement de mots courants.
    """
    instruction_lower = instruction_en.lower()
    for en, fr in sorted(
        TRADUCTIONS_BASIQUES.items(),
        key=lambda x: len(x[0]),
        reverse=True
    ):
        instruction_lower = instruction_lower.replace(en, fr)
    return instruction_lower.capitalize()


# ------------------------------------------------------------
# APPELS API SPOONACULAR
# ------------------------------------------------------------
def _search_recipes(
    query      : str,
    type_repas : str,
    nb         : int = 5,
) -> list:
    """
    Recherche des recettes sur Spoonacular.
    Retourne une liste d IDs de recettes.
    """
    # Mapping type_repas -> meal_type Spoonacular
    meal_type_map = {
        "petit_dej" : "breakfast",
        "dejeuner"  : "main course",
        "diner"     : "main course",
    }
    meal_type = meal_type_map.get(type_repas, "main course")

    params = {
        "query"              : query,
        "type"               : meal_type,
        "number"             : nb,
        "addRecipeNutrition" : True,
        "instructionsRequired": True,
        "language"           : "en",
    }

    try:
        r = requests.get(
            f"{BASE_URL}/recipes/complexSearch",
            headers=HEADERS,
            params=params,
            timeout=10
        )
        r.raise_for_status()
        data = r.json()
        return data.get("results", [])
    except requests.RequestException as e:
        print(f"[ERREUR] Recherche '{query}' : {e}")
        return []


def _get_recipe_details(recipe_id: int) -> dict:
    """
    Recupere les details complets d une recette
    incluant les instructions etape par etape.
    """
    try:
        r = requests.get(
            f"{BASE_URL}/recipes/{recipe_id}/information",
            headers=HEADERS,
            params={"includeNutrition": True},
            timeout=10
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        print(f"[ERREUR] Details recette {recipe_id} : {e}")
        return {}


def _extraire_macros(nutrition_data: dict) -> dict:
    """
    Extrait les macros depuis les donnees nutritionnelles
    Spoonacular.
    """
    macros = {
        "calories"   : 0.0,
        "proteines_g": 0.0,
        "glucides_g" : 0.0,
        "lipides_g"  : 0.0,
        "fibres_g"   : 0.0,
    }

    if not nutrition_data:
        return macros

    nutrients = nutrition_data.get("nutrients", [])
    mapping = {
        "Calories"          : "calories",
        "Protein"           : "proteines_g",
        "Carbohydrates"     : "glucides_g",
        "Fat"               : "lipides_g",
        "Fiber"             : "fibres_g",
    }

    for nutrient in nutrients:
        nom = nutrient.get("name", "")
        if nom in mapping:
            macros[mapping[nom]] = round(
                float(nutrient.get("amount", 0)), 1
            )

    return macros


def _detecter_digestibilite(ingredients: list) -> str:
    """
    Detecte la digestibilite d une recette
    selon ses ingredients.
    """
    mots_low = [
        "cabbage", "broccoli", "cauliflower", "onion",
        "garlic", "bean", "lentil", "chickpea",
        "sausage", "bacon", "fried", "deep fried",
    ]
    mots_high = [
        "rice", "chicken breast", "turkey breast",
        "egg white", "banana", "zucchini", "carrot",
        "sweet potato", "oatmeal", "yogurt",
    ]

    ingredients_lower = " ".join([
        i.get("name", "").lower()
        for i in ingredients
    ])

    for mot in mots_low:
        if mot in ingredients_lower:
            return "low"

    for mot in mots_high:
        if mot in ingredients_lower:
            return "high"

    return "medium"


# ------------------------------------------------------------
# INSERTION EN BASE
# ------------------------------------------------------------
def _inserer_recette(
    conn       : sqlite3.Connection,
    details    : dict,
    type_repas : str,
    type_seance: str,
    macros     : dict,
) -> int | None:
    """
    Insere une recette et ses ingredients en base.
    Retourne l ID insere ou None si doublon.
    """
    cursor = conn.cursor()

    spoonacular_id = details.get("id")
    nom_en         = details.get("title", "")
    nom_fr         = _traduire_titre(nom_en)
    source_url     = details.get("sourceUrl", "")
    image_url      = details.get("image", "")
    nb_personnes   = details.get("servings", 1) or 1
    temps_prep     = details.get("readyInMinutes", 0) or 0
    ingredients    = details.get("extendedIngredients", [])
    digestibilite  = _detecter_digestibilite(ingredients)

    # Calories par portion
    cal_portion = round(macros["calories"] / nb_personnes, 1)
    pro_portion = round(macros["proteines_g"] / nb_personnes, 1)
    glu_portion = round(macros["glucides_g"]  / nb_personnes, 1)
    lip_portion = round(macros["lipides_g"]   / nb_personnes, 1)
    fib_portion = round(macros["fibres_g"]    / nb_personnes, 1)

    # Score nutritionnel simple
    score = round(
        pro_portion * 0.4
        + fib_portion * 0.1
        - lip_portion * 0.05
        , 2
    )

    # Verifier doublon
    cursor.execute(
        "SELECT id FROM recettes WHERE spoonacular_id = ?",
        (spoonacular_id,)
    )
    if cursor.fetchone():
        return None

    # Inserer la recette
    cursor.execute("""
        INSERT INTO recettes (
            spoonacular_id, nom_fr, nom_en,
            type_repas, type_seance,
            nb_personnes, temps_prep_min,
            source_url, image_url,
            digestibilite,
            calories_portion, proteines_g, glucides_g,
            lipides_g, fibres_g,
            score_nutritionnel, valide, date_import
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, (
        spoonacular_id, nom_fr, nom_en,
        type_repas, type_seance,
        nb_personnes, temps_prep,
        source_url, image_url,
        digestibilite,
        cal_portion, pro_portion, glu_portion,
        lip_portion, fib_portion,
        score, 1,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))

    recette_id = cursor.lastrowid

    # Inserer les ingredients
    for ing in ingredients:
        nom_ing_en = ing.get("name", "")
        nom_ing_fr = _traduire_titre(nom_ing_en)
        quantite   = ing.get("measures", {}).get("metric", {})
        qte_g      = quantite.get("amount", 0) or 0
        unite      = quantite.get("unitLong", "g")

        cursor.execute("""
            INSERT INTO recette_ingredients (
                recette_id, nom_fr, nom_en,
                quantite_g, unite
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            recette_id, nom_ing_fr, nom_ing_en,
            round(qte_g, 1), unite
        ))

    # Inserer les instructions
    analyzed = details.get("analyzedInstructions", [])
    etape_num = 1
    for bloc in analyzed:
        for step in bloc.get("steps", []):
            instruction_en = step.get("step", "")
            instruction_fr = _traduire_instruction(instruction_en)

            cursor.execute("""
                INSERT INTO recette_instructions (
                    recette_id, etape,
                    instruction_fr, instruction_en
                ) VALUES (?, ?, ?, ?)
            """, (
                recette_id, etape_num,
                instruction_fr, instruction_en
            ))
            etape_num += 1

    conn.commit()
    return recette_id


# ------------------------------------------------------------
# IMPORT COMPLET
# ------------------------------------------------------------
def importer_toutes_recettes(conn: sqlite3.Connection) -> None:
    """
    Importe toutes les recettes selon la config.
    """
    print("\n[...] Import des recettes Spoonacular...")

    # Compteurs par type
    nb_par_type = {
        "petit_dej" : NB_RECETTES_PETIT_DEJ,
        "dejeuner"  : NB_RECETTES_DEJEUNER,
        "diner"     : NB_RECETTES_DINER,
    }
    inseres_par_type = {
        "petit_dej" : 0,
        "dejeuner"  : 0,
        "diner"     : 0,
    }

    for query, type_repas, type_seance in REQUETES_RECETTES:

        # Verifier si on a atteint le quota pour ce type
        if inseres_par_type[type_repas] >= nb_par_type[type_repas]:
            continue

        nb_a_chercher = min(
            5,
            nb_par_type[type_repas] - inseres_par_type[type_repas]
        )

        print(
            f"\n  Recherche : '{query}' "
            f"({type_repas} / {type_seance}) "
            f"-> {nb_a_chercher} recettes"
        )

        # Recherche
        resultats = _search_recipes(query, type_repas, nb_a_chercher)
        time.sleep(PAUSE_SECONDES)

        for recette in resultats:
            recipe_id = recette.get("id")
            nom_en    = recette.get("title", "")

            # Macros depuis la recherche
            nutrition = recette.get("nutrition", {})
            macros    = _extraire_macros(nutrition)

            # Details complets
            details = _get_recipe_details(recipe_id)
            time.sleep(PAUSE_SECONDES)

            if not details:
                continue

            # Insertion
            inserted_id = _inserer_recette(
                conn, details, type_repas, type_seance, macros
            )

            if inserted_id:
                inseres_par_type[type_repas] += 1
                print(
                    f"    [OK] [{type_repas}] "
                    f"{nom_en} -> {_traduire_titre(nom_en)}"
                    f" | {macros['calories']:.0f} kcal"
                    f" P:{macros['proteines_g']:.0f}g"
                )
            else:
                print(f"    [SKIP] Doublon : {nom_en}")

    # Bilan
    print("\n" + "=" * 60)
    print("  BILAN IMPORT RECETTES")
    print("=" * 60)
    for type_repas, nb in inseres_par_type.items():
        print(f"  {type_repas:<15} : {nb} recettes importees")

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM recettes")
    total = cursor.fetchone()[0]
    print(f"  Total en base  : {total} recettes")
    print("=" * 60)