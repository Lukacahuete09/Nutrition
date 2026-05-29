# ============================================================
# CALCUL DU COÛT PAR RECETTE
# suivi/prix/pricer.py
# ============================================================

import sys
import sqlite3
from pathlib import Path
sys.dont_write_bytecode = True

# ------------------------------------------------------------
# RACINE DU PROJET
# suivi/prix/pricer.py → suivi/prix/ → suivi/ → NUTRITION/
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from config import (
    RECETTES_DB,
    NUTRITION_DB,
    MAGASIN_FALLBACK,       # ✅ FALLBACK pas DEFAUT
)
from suivi.prix.matcher import Matcher


# ============================================================
# CLASSE PRINCIPALE
# ============================================================
class Pricer:
    """
    Calcule le coût réel d'une recette en récupérant
    les prix de chaque ingrédient via le Matcher.
    """

    def __init__(self, magasin: str = MAGASIN_FALLBACK):   # ✅ FALLBACK
        self.magasin = magasin
        self.matcher = Matcher(magasin=magasin)

    # ----------------------------------------------------------
    # CALCUL COÛT D'UNE RECETTE
    # ----------------------------------------------------------
    def calculer_cout_recette(self, recette_id: int) -> dict:
        conn             = sqlite3.connect(RECETTES_DB)
        conn.row_factory = sqlite3.Row
        cursor           = conn.cursor()

        cursor.execute("""
            SELECT nom_fr, nom_en, nb_personnes
            FROM recettes
            WHERE id = ?
        """, (recette_id,))

        recette = cursor.fetchone()
        conn.close()

        if not recette:
            print(f"[ERREUR] Recette {recette_id} introuvable.")
            return {}

        nom     = recette["nom_fr"] or recette["nom_en"] or f"Recette {recette_id}"
        nb_pers = recette["nb_personnes"] or 1

        print(f"\n[PRICER] Calcul coût : {nom}")
        print(f"         Magasin     : {self.magasin.upper()}")

        resultats_match = self.matcher.matcher_ingredients_recette(recette_id)

        details        = []
        cout_total     = 0.0
        nb_trouves     = 0
        nb_non_trouves = 0

        for match in resultats_match:
            nom_en     = match["nom_en"]     or ""
            nom_fr     = match["nom_fr"]     or ""
            quantite_g = match["quantite_g"] or 0
            produit    = match["produit"]

            if produit and produit.get("prix_kg", 0) > 0:
                cout_ingredient = (quantite_g / 1000) * produit["prix_kg"]
                cout_total     += cout_ingredient
                nb_trouves     += 1

                details.append({
                    "nom_en"          : nom_en,
                    "nom_fr"          : nom_fr,
                    "quantite_g"      : quantite_g,
                    "produit_trouve"  : produit.get("nom_produit", ""),
                    "prix_kg"         : produit["prix_kg"],
                    "cout_ingredient" : round(cout_ingredient, 3),
                    "depuis_cache"    : produit.get("depuis_cache", False),
                    "score_match"     : produit.get("score", 0),
                    "trouve"          : True,
                })
            else:
                nb_non_trouves += 1
                details.append({
                    "nom_en"          : nom_en,
                    "nom_fr"          : nom_fr,
                    "quantite_g"      : quantite_g,
                    "produit_trouve"  : None,
                    "prix_kg"         : None,
                    "cout_ingredient" : None,
                    "depuis_cache"    : False,
                    "score_match"     : 0,
                    "trouve"          : False,
                })

        nb_total     = nb_trouves + nb_non_trouves
        couverture   = (nb_trouves / nb_total * 100) if nb_total > 0 else 0
        cout_portion = round(cout_total / nb_pers, 3)

        print(f"\n[OK] {nom}")
        print(f"     Ingrédients trouvés : {nb_trouves}/{nb_total} ({couverture:.0f}%)")
        print(f"     Coût total          : {cout_total:.2f} €")
        print(f"     Coût / portion      : {cout_portion:.2f} €")

        if nb_non_trouves > 0:
            non_trouves = [d["nom_en"] for d in details if not d["trouve"]]
            print(f"     Non trouvés         : {', '.join(non_trouves)}")

        return {
            "recette_id"     : recette_id,
            "nom"            : nom,
            "nb_ingredients" : nb_total,
            "nb_trouves"     : nb_trouves,
            "nb_non_trouves" : nb_non_trouves,
            "cout_total"     : round(cout_total, 2),
            "cout_portion"   : cout_portion,
            "couverture_pct" : round(couverture, 1),
            "ingredients"    : details,
            "magasin"        : self.magasin,
        }

    # ----------------------------------------------------------
    # CALCUL COÛT DE PLUSIEURS RECETTES
    # ----------------------------------------------------------
    def calculer_cout_semaine(self, recette_ids: list) -> dict:  
        print(f"\n{'='*60}")
        print(f"  CALCUL COÛT SEMAINE — {self.magasin.upper()}")
        print(f"  {len(recette_ids)} recettes à pricer")
        print(f"{'='*60}")

        resultats  = []
        cout_total = 0.0

        for recette_id in recette_ids:
            resultat = self.calculer_cout_recette(recette_id)
            if resultat:
                resultats.append(resultat)
                cout_total += resultat["cout_portion"]

        if not resultats:
            return {}

        couts       = [r["cout_portion"]   for r in resultats]
        couvertures = [r["couverture_pct"] for r in resultats]

        rapport = {
            "nb_recettes"    : len(resultats),
            "cout_total"     : round(cout_total, 2),
            "cout_moyen"     : round(sum(couts) / len(couts), 2),
            "cout_min"       : round(min(couts), 2),
            "cout_max"       : round(max(couts), 2),
            "couverture_moy" : round(sum(couvertures) / len(couvertures), 1),
            "recettes"       : resultats,
            "magasin"        : self.magasin,
        }

        print(f"\n{'='*60}")
        print(f"  RAPPORT COÛT SEMAINE")
        print(f"{'='*60}")
        print(f"  Recettes pricées  : {rapport['nb_recettes']}")
        print(f"  Coût total        : {rapport['cout_total']:.2f} €")
        print(f"  Coût moyen/repas  : {rapport['cout_moyen']:.2f} €")
        print(f"  Coût min          : {rapport['cout_min']:.2f} €")
        print(f"  Coût max          : {rapport['cout_max']:.2f} €")
        print(f"  Couverture moy.   : {rapport['couverture_moy']:.1f}%")
        print(f"{'='*60}")

        return rapport

    # ----------------------------------------------------------
    # MISE À JOUR COÛT EN BASE
    # ----------------------------------------------------------
    def mettre_a_jour_cout_db(self, recette_id: int, cout_portion: float) -> None:
        conn   = sqlite3.connect(RECETTES_DB)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE recettes
            SET cout_portion = ?
            WHERE id = ?
        """, (cout_portion, recette_id))

        conn.commit()
        conn.close()

    def close(self):
        self.matcher.close()


# ============================================================
# TEST AUTONOME
# ============================================================
if __name__ == "__main__":

    pricer = Pricer(magasin=MAGASIN_FALLBACK) 

    conn             = sqlite3.connect(RECETTES_DB)
    conn.row_factory = sqlite3.Row
    cursor           = conn.cursor()
    cursor.execute("SELECT id, nom_fr FROM recettes LIMIT 3")
    recettes = cursor.fetchall()
    conn.close()

    if not recettes:
        print("[WARN] Aucune recette en base.")
        print("       Lancez : python main.py import-recettes")
        sys.exit(0)

    ids     = [r["id"] for r in recettes]
    rapport = pricer.calculer_cout_semaine(ids)

    print(f"\n[OK] Test terminé — {rapport.get('nb_recettes', 0)} recettes pricées")
    pricer.close()
