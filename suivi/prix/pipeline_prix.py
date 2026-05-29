# ============================================================
# PIPELINE PRIX — ORCHESTRATEUR COMPLET
# suivi/prix/pipeline_prix.py
# ============================================================

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
sys.dont_write_bytecode = True

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from config import (
    RECETTES_DB,
    NUTRITION_DB,
    MAGASIN_FALLBACK,
    NB_SEMAINES_HISTORIQUE_PRIX,
)
from optimisation.excel.reader  import lire_config_athlete 
from suivi.prix.pricer          import Pricer
from suivi.prix.updater         import mettre_a_jour_depuis_pricer


# ------------------------------------------------------------
# RÉCUPÉRATION DES RECETTES DU PLANNING
# ------------------------------------------------------------
def _get_recettes_planning() -> list:
    conn             = sqlite3.connect(RECETTES_DB)
    conn.row_factory = sqlite3.Row
    cursor           = conn.cursor()

    cursor.execute("""
        SELECT id, nom_fr, nom_en, type_repas, type_seance
        FROM recettes
        WHERE valide = 1
        ORDER BY RANDOM()
        LIMIT 21
    """)

    recettes = cursor.fetchall()
    conn.close()

    if not recettes:
        print("[WARN] Aucune recette valide en base.")
        print("       Lancez : python main.py import-recettes")
        return []

    print(f"[OK] {len(recettes)} recettes récupérées pour le pricing")
    return [dict(r) for r in recettes]


# ------------------------------------------------------------
# RAPPORT FINAL
# ------------------------------------------------------------
def _afficher_rapport(rapport: dict, magasin: str) -> None:
    print(f"\n{'='*60}")
    print(f"  RAPPORT PIPELINE PRIX")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  Magasin : {magasin.upper()}")
    print(f"{'='*60}")
    print(f"  Recettes pricées   : {rapport.get('nb_recettes', 0)}")
    print(f"  Coût total semaine : {rapport.get('cout_total', 0):.2f} €")
    print(f"  Coût moyen / repas : {rapport.get('cout_moyen', 0):.2f} €")
    print(f"  Coût min           : {rapport.get('cout_min', 0):.2f} €")
    print(f"  Coût max           : {rapport.get('cout_max', 0):.2f} €")
    print(f"  Couverture moy.    : {rapport.get('couverture_moy', 0):.1f}%")
    print(f"{'='*60}")

    recettes = rapport.get("recettes", [])
    if recettes:
        print(f"\n  Détail par recette :")
        print(f"  {'Recette':<35} {'Coût':>6} {'Couv.':>6} {'Trouvés':>8}")
        print(f"  {'-'*57}")
        for r in sorted(recettes, key=lambda x: x["cout_portion"]):
            print(
                f"  {r['nom'][:35]:<35}"
                f" {r['cout_portion']:>5.2f}€"
                f" {r['couverture_pct']:>5.0f}%"
                f" {r['nb_trouves']:>3}/{r['nb_ingredients']:<3}"
            )

    non_trouves = []
    for r in recettes:
        for ing in r.get("ingredients", []):
            if not ing["trouve"]:
                non_trouves.append(ing["nom_en"])

    if non_trouves:
        uniques = list(set(non_trouves))
        print(f"\n Ingrédients non trouvés ({len(uniques)}) :")
        for nom in sorted(uniques):
            print(f"     → {nom}")
        print(f"\n  [INFO] Ajoutez-les dans TRADUCTIONS_EN_FR (matcher.py)")

    print(f"{'='*60}\n")


# ============================================================
# PIPELINE PRINCIPAL
# ============================================================
def lancer_pipeline_prix(magasin: str = None) -> dict:
    """
    Lance le pipeline complet de pricing.
    Magasin lu depuis Excel si non fourni.
    """
    if magasin is None:
        try:
            config  = lire_config_athlete()
            magasin = config["budget"]["magasin"]  
            print(f"  Magasin lu depuis Excel : {magasin.upper()}")
        except Exception as e:
            print(f"[WARN] Impossible de lire Excel : {e}")
            print(f"[WARN] Fallback : {MAGASIN_FALLBACK.upper()}")
            magasin = MAGASIN_FALLBACK

    print(f"\n{'='*60}")
    print(f"  PIPELINE PRIX — {magasin.upper()}")
    print(f"  {datetime.now().strftime('%A %d/%m/%Y %H:%M')}")
    print(f"{'='*60}")

    rapport = {
        "magasin"        : magasin,
        "nb_recettes"    : 0,
        "cout_total"     : 0.0,
        "cout_moyen"     : 0.0,
        "cout_min"       : 0.0,
        "cout_max"       : 0.0,
        "couverture_moy" : 0.0,
        "recettes"       : [],
        "statut"         : "ok",
    }

    try:
        # --------------------------------------------------
        # ÉTAPE 1 — Récupérer les recettes
        # --------------------------------------------------
        print("\n[1/3] Récupération des recettes du planning...")
        recettes = _get_recettes_planning()

        if not recettes:
            rapport["statut"] = "erreur"
            return rapport

        recette_ids = [r["id"] for r in recettes]

        # --------------------------------------------------
        # ÉTAPE 2 — Pricer toutes les recettes
        # --------------------------------------------------
        print(f"\n[2/3] Pricing des recettes via {magasin.upper()}...")
        pricer         = Pricer(magasin=magasin)
        rapport_pricer = pricer.calculer_cout_semaine(recette_ids)

        if not rapport_pricer:
            print("[WARN] Aucun résultat de pricing.")
            rapport["statut"] = "warning"
            pricer.close()
            return rapport

        # Mettre à jour cout_portion dans recettes.db
        for recette in rapport_pricer.get("recettes", []):
            pricer.mettre_a_jour_cout_db(
                recette_id   = recette["recette_id"],
                cout_portion = recette["cout_portion"],
            )

        pricer.close()

        rapport.update({
            "nb_recettes"    : rapport_pricer["nb_recettes"],
            "cout_total"     : rapport_pricer["cout_total"],
            "cout_moyen"     : rapport_pricer["cout_moyen"],
            "cout_min"       : rapport_pricer["cout_min"],
            "cout_max"       : rapport_pricer["cout_max"],
            "couverture_moy" : rapport_pricer["couverture_moy"],
            "recettes"       : rapport_pricer["recettes"],
        })

        # --------------------------------------------------
        # ÉTAPE 3 — Mise à jour nutrition.db
        # --------------------------------------------------
        print(f"\n[3/3] Mise à jour des prix dans nutrition.db...")
        mettre_a_jour_depuis_pricer(rapport_pricer.get("recettes", [])) 

        _afficher_rapport(rapport, magasin)

    except Exception as e:
        print(f"\n[ERREUR] Pipeline prix : {e}")
        rapport["statut"] = "erreur"
        rapport["erreur"] = str(e)

    return rapport


# ============================================================
# TEST AUTONOME
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline prix — Nutrition Sportive"
    )
    parser.add_argument(
        "--magasin",
        choices = ["leclerc", "auchan"],
        default = None,                   
        help    = "Override magasin Excel"
    )
    args = parser.parse_args()

    rapport = lancer_pipeline_prix(magasin=args.magasin)
    print(f"[OK] Statut : {rapport['statut']}")
