# ============================================================
# PARSING DU FICHIER CIQUAL 2020
# create_db/importers/ciqual_parser.py
# ============================================================

import os
import sys
import pandas as pd
sys.dont_write_bytecode = True

CIQUAL_LOCAL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "data", "ciqual_2020.xls"
)

# ------------------------------------------------------------
# CORRESPONDANCE COLONNES CIQUAL -> NOMS INTERNES
# ------------------------------------------------------------
RENAME_MAP = {
    "alim_nom_fr"       : "nom",
    "alim_grp_nom_fr"   : "groupe",
    "alim_ssgrp_nom_fr" : "ssgroupe",
    "Energie, Règlement UE N° 1169/2011 (kcal/100 g)"       : "calories_100g",
    "Protéines, N x facteur de Jones (g/100 g)"              : "proteines_g",
    "Glucides (g/100 g)"                                     : "glucides_g",
    "Lipides (g/100 g)"                                      : "lipides_g",
    "Fibres alimentaires (g/100 g)"                          : "fibres_g",
    "Eau (g/100 g)"                                          : "eau_g",
    "Sodium (mg/100 g)"                                      : "sodium_mg",
    "Potassium (mg/100 g)"                                   : "potassium_mg",
    "Calcium (mg/100 g)"                                     : "calcium_mg",
    "Magnésium (mg/100 g)"                                   : "magnesium_mg",
    "Fer (mg/100 g)"                                         : "fer_mg",
    "Zinc (mg/100 g)"                                        : "zinc_mg",
    "Vitamine C (mg/100 g)"                                  : "vitamine_c_mg",
    "Vitamine D (µg/100 g)"                                  : "vitamine_d_ug",
    "Vitamine B12 (µg/100 g)"                                : "vitamine_b12_ug",
    "AG 18:3 c9,c12,c15 (n-3), alpha-linolénique (g/100 g)" : "omega3_g",
}

NUMERIC_COLS = [
    "calories_100g", "proteines_g", "glucides_g", "lipides_g",
    "fibres_g", "eau_g", "sodium_mg", "potassium_mg",
    "calcium_mg", "magnesium_mg", "fer_mg", "zinc_mg",
    "vitamine_c_mg", "vitamine_d_ug", "vitamine_b12_ug", "omega3_g",
]


# ------------------------------------------------------------
# NETTOYAGE DES COLONNES NUMERIQUES
# Dans CIQUAL :
#   '-'  = valeur non renseignee -> NaN (pas 0)
#   '<X' = valeur inferieure a X -> prendre X
#   ','  = separateur decimal -> remplacer par '.'
# ------------------------------------------------------------
def _clean_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace(",",  ".", regex=False)
        .str.replace("<",  "",  regex=False)
        .str.replace(" ",  "",  regex=False)
        .str.replace("-",  "",  regex=False)  # vide -> NaN naturellement
        .pipe(pd.to_numeric, errors="coerce")
        # NaN reste NaN -> filtre apres sur calories > 0
    )


# ------------------------------------------------------------
# FONCTION PRINCIPALE
# ------------------------------------------------------------
def parse_ciqual() -> pd.DataFrame:
    """
    Lit et nettoie le fichier CIQUAL 2020.
    Retourne un DataFrame pret pour insertion.

    Filtres appliques :
      - Aliments sans nom supprimes
      - Aliments sans calories renseignees supprimes
        (le tiret '-' dans CIQUAL = non mesure, pas zero)
    """
    if not os.path.exists(CIQUAL_LOCAL):
        raise FileNotFoundError(
            f"[ERREUR] Fichier CIQUAL introuvable : {CIQUAL_LOCAL}\n"
            f"[INFO]   Placez le fichier dans create_db/data/"
        )

    print("[...] Lecture du fichier CIQUAL...")

    df = pd.read_excel(
        CIQUAL_LOCAL,
        sheet_name=0,
        header=0,
        dtype=str
    )

    print(f"[INFO] {len(df)} lignes brutes lues")

    # Renommage des colonnes
    df = df.rename(columns=RENAME_MAP)

    # Nettoyage des colonnes numeriques
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = _clean_numeric(df[col])
        else:
            print(f"[WARN] Colonne manquante : {col} -> mise a 0")
            df[col] = 0.0

    # Verification colonne nom
    if "nom" not in df.columns:
        raise ValueError(
            "[ERREUR] Colonne 'nom' introuvable.\n"
            "[INFO]   Verifier le nom exact dans le fichier CIQUAL."
        )

    # Supprimer les lignes sans nom
    avant = len(df)
    df = df.dropna(subset=["nom"])
    df = df[df["nom"].astype(str).str.strip() != ""]

    # Supprimer les aliments sans calories renseignees
    # '-' dans CIQUAL = valeur non mesuree, pas zero
    df = df[df["calories_100g"].notna()]
    df = df[df["calories_100g"] > 0]
    apres = len(df)

    print(
        f"[OK] {apres} aliments charges "
        f"({avant - apres} ignores : calories non renseignees ou nom manquant)"
    )

    # Remplir les NaN restants par 0 pour les autres colonnes
    for col in NUMERIC_COLS:
        if col != "calories_100g" and col in df.columns:
            df[col] = df[col].fillna(0.0)

    # Ajouter colonnes groupe et ssgroupe si manquantes
    if "groupe" not in df.columns:
        df["groupe"] = ""
    if "ssgroupe" not in df.columns:
        df["ssgroupe"] = ""

    df["groupe"]   = df["groupe"].fillna("").astype(str)
    df["ssgroupe"] = df["ssgroupe"].fillna("").astype(str)

    return df