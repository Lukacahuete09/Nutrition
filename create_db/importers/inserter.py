# ============================================================
# INSERTION DES ALIMENTS EN BASE
# create_db/importers/inserter.py
# ============================================================

import sys
import sqlite3
import pandas as pd
sys.dont_write_bytecode = True

from database.categories import (
    CIQUAL_SSGROUP_MAPPING,
    CIQUAL_GROUP_FALLBACK,
    KEYWORDS_LEGUMES_CUITS,
    KEYWORDS_FRUITS_SECS,
)
from engine.digestibilite import get_digestibilite
from engine.scoring       import compute_densite_proteique


def get_categorie_id(groupe: str, ssgroupe: str, nom: str) -> int | None:
    """
    Retourne le categorie_id avec logique a trois niveaux :
      Niveau 1 : sous-groupe CIQUAL exact
      Niveau 2 : distinction cru/cuit pour legumes
                 distinction frais/sec pour fruits
      Niveau 3 : fallback sur le groupe principal
    """
    ssgroupe_lower = ssgroupe.strip().lower()
    groupe_lower   = groupe.strip().lower()
    nom_lower      = nom.strip().lower()

    # Niveau 1 : sous-groupe exact
    categorie_brute = None
    for key, val in CIQUAL_SSGROUP_MAPPING.items():
        if key == ssgroupe_lower:
            categorie_brute = val
            break

    # Niveau 2 : fallback groupe
    if categorie_brute is None:
        for key, val in CIQUAL_GROUP_FALLBACK.items():
            if key in groupe_lower:
                categorie_brute = val
                break

    # Distinction legumes crus (1) / legumes cuits (2)
    if categorie_brute == 1:
        for keyword in KEYWORDS_LEGUMES_CUITS:
            if keyword in nom_lower:
                return 2
        return 1

    # Distinction fruits frais (3) / fruits secs (4)
    if categorie_brute == 3:
        for keyword in KEYWORDS_FRUITS_SECS:
            if keyword in nom_lower:
                return 4
        return 3

    return categorie_brute


def insert_aliments(conn: sqlite3.Connection, df: pd.DataFrame) -> None:
    """
    Insere les aliments depuis le DataFrame CIQUAL.
    Utilise le mapping CIQUAL pour determiner la categorie.
    """
    cursor     = conn.cursor()
    inseres    = 0
    ignores    = 0
    non_mappes = []

    for _, row in df.iterrows():
        nom      = str(row.get("nom",      "")).strip()
        groupe   = str(row.get("groupe",   "")).strip()
        ssgroupe = str(row.get("ssgroupe", "")).strip()

        if not nom or nom == "nan":
            ignores += 1
            continue

        categorie_id = get_categorie_id(groupe, ssgroupe, nom)

        if categorie_id is None:
            non_mappes.append(f"{groupe} -> {ssgroupe}")

        calories  = float(row.get("calories_100g", 0) or 0)
        proteines = float(row.get("proteines_g",   0) or 0)

        cursor.execute("""
            INSERT INTO aliments (
                nom, categorie_id,
                calories_100g, proteines_g, glucides_g, lipides_g,
                fibres_g, eau_g, sodium_mg, potassium_mg,
                calcium_mg, magnesium_mg, fer_mg, zinc_mg,
                vitamine_c_mg, vitamine_d_ug, vitamine_b12_ug, omega3_g,
                digestibilite, cout_kg,
                densite_proteique, score_nutritionnel, source
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?
            )
        """, (
            nom,
            categorie_id,
            calories,
            proteines,
            float(row.get("glucides_g",      0) or 0),
            float(row.get("lipides_g",        0) or 0),
            float(row.get("fibres_g",         0) or 0),
            float(row.get("eau_g",            0) or 0),
            float(row.get("sodium_mg",        0) or 0),
            float(row.get("potassium_mg",     0) or 0),
            float(row.get("calcium_mg",       0) or 0),
            float(row.get("magnesium_mg",     0) or 0),
            float(row.get("fer_mg",           0) or 0),
            float(row.get("zinc_mg",          0) or 0),
            float(row.get("vitamine_c_mg",    0) or 0),
            float(row.get("vitamine_d_ug",    0) or 0),
            float(row.get("vitamine_b12_ug",  0) or 0),
            float(row.get("omega3_g",         0) or 0),
            get_digestibilite(nom),
            0.0,
            compute_densite_proteique(proteines, calories),
            0.0,
            "CIQUAL 2020",
        ))
        inseres += 1

    conn.commit()
    print(f"[OK] {inseres} aliments inseres. {ignores} lignes ignorees.")

    if non_mappes:
        non_mappes_uniques = list(set(non_mappes))
        print(f"[WARN] {len(non_mappes_uniques)} sous-groupes non mappes :")
        for nm in sorted(non_mappes_uniques):
            print(f"  -> {nm}")


def print_repartition(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.nom, COUNT(a.id) AS nb
        FROM categories c
        LEFT JOIN aliments a ON a.categorie_id = c.id
        GROUP BY c.nom
        ORDER BY nb DESC
    """)
    print("\nRepartition par categorie :")
    for row in cursor.fetchall():
        print(f"  {row['nom']:<35} : {row['nb']} aliments")