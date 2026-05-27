# ============================================================
# DETECTION DES PROMOTIONS
# suivi/prix/promo_detector.py
#
# Analyse la base historique_prix pour identifier
# les aliments en promotion cette semaine.
#
# Retourne une liste d aliments priorises pour
# l optimizer en fonction de leur promo_score.
# ============================================================

import os
import sys
import sqlite3
from datetime import datetime
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    NUTRITION_DB,
    PROMO_SCORE_MIN,
)


# ------------------------------------------------------------
# CONNEXION BASE DE DONNEES
# ------------------------------------------------------------
def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(NUTRITION_DB)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------------------
# RECUPERATION DES PROMOTIONS ACTUELLES
# ------------------------------------------------------------
def get_promotions_semaine() -> list:
    """
    Retourne la liste des aliments en promotion
    pour la semaine courante.

    Critere : promo_score >= PROMO_SCORE_MIN (0.15 = -15%)

    Retourne :
    [
        {
            "aliment_id"  : id dans nutrition.db,
            "nom"         : nom de l aliment,
            "categorie"   : categorie de l aliment,
            "prix_actuel" : prix cette semaine (e/kg),
            "prix_moyen"  : prix moyen historique (e/kg),
            "promo_score" : score de promotion (0 a 1),
            "reduction_pct": pourcentage de reduction,
            "magasin"     : magasin concerne,
            "economie_kg" : economie par kg en euros,
        },
        ...
    ]
    Trie par promo_score decroissant.
    """
    conn    = _get_connection()
    cursor  = conn.cursor()

    semaine = datetime.now().isocalendar()[1]
    annee   = datetime.now().year

    cursor.execute("""
        SELECT
            h.aliment_id,
            h.nom_aliment,
            h.magasin,
            h.prix_actuel,
            h.prix_moyen,
            h.promo_score,
            a.categorie_id,
            c.nom AS categorie_nom,
            a.digestibilite,
            a.score_nutritionnel
        FROM historique_prix h
        JOIN aliments a    ON a.id   = h.aliment_id
        JOIN categories c  ON c.id   = a.categorie_id
        WHERE h.semaine     = ?
          AND h.annee       = ?
          AND h.promo_score >= ?
        ORDER BY h.promo_score DESC
    """, (semaine, annee, PROMO_SCORE_MIN))

    rows        = cursor.fetchall()
    conn.close()

    promotions = []
    for row in rows:
        promotions.append({
            "aliment_id"   : row["aliment_id"],
            "nom"          : row["nom_aliment"],
            "categorie"    : row["categorie_nom"],
            "digestibilite": row["digestibilite"],
            "prix_actuel"  : round(row["prix_actuel"], 2),
            "prix_moyen"   : round(row["prix_moyen"],  2),
            "promo_score"  : round(row["promo_score"],  4),
            "reduction_pct": round(row["promo_score"] * 100, 1),
            "magasin"      : row["magasin"],
            "economie_kg"  : round(
                row["prix_moyen"] - row["prix_actuel"], 2
            ),
            "score_nutritionnel": row["score_nutritionnel"],
        })

    return promotions


# ------------------------------------------------------------
# SCORE COMBINE PROMOTION + NUTRITION
# ------------------------------------------------------------
def _calculer_score_combine(
    promo_score         : float,
    score_nutritionnel  : float,
    poids_promo         : float = 0.4,
    poids_nutrition     : float = 0.6,
) -> float:
    """
    Calcule un score combine promotion + nutrition.

    Permet de prioriser les aliments qui sont
    a la fois en promotion ET nutritionnellement interessants.

    Ponderation par defaut :
      60% score nutritionnel (priorite sante)
      40% score promo        (opportunite economique)

    Les poids sont parametrables selon la priorite
    de l utilisateur (budget vs nutrition).
    """
    score_promo_normalise = min(promo_score * 2, 1.0)
    return round(
        poids_promo     * score_promo_normalise +
        poids_nutrition * score_nutritionnel,
        4
    )


# ------------------------------------------------------------
# PROMOTIONS CLASSEES PAR CATEGORIE
# ------------------------------------------------------------
def get_promotions_par_categorie() -> dict:
    """
    Retourne les promotions groupees par categorie
    d aliment pour faciliter la construction
    des menus de la semaine.

    Retourne :
    {
        "Viandes"          : [...],
        "Poissons"         : [...],
        "Legumes cuits"    : [...],
        "Feculents"        : [...],
        ...
    }
    """
    promotions = get_promotions_semaine()
    par_categorie = {}

    for promo in promotions:
        cat = promo["categorie"]
        if cat not in par_categorie:
            par_categorie[cat] = []
        par_categorie[cat].append(promo)

    return par_categorie


# ------------------------------------------------------------
# ALIMENTS PRIORITAIRES POUR L OPTIMIZER
# ------------------------------------------------------------
def get_aliments_prioritaires(
    poids_promo     : float = 0.4,
    poids_nutrition : float = 0.6,
) -> list:
    """
    Retourne la liste des aliments prioritaires
    pour l optimizer cette semaine.

    Combine le score de promotion et le score nutritionnel
    pour identifier les meilleurs achats de la semaine.

    Retourne une liste triee par score combine decroissant.
    Utilisee par recipe_optimizer.py pour prioriser
    les recettes contenant ces aliments.
    """
    promotions = get_promotions_semaine()

    for promo in promotions:
        promo["score_combine"] = _calculer_score_combine(
            promo["promo_score"],
            promo["score_nutritionnel"],
            poids_promo,
            poids_nutrition,
        )

    return sorted(
        promotions,
        key=lambda x: x["score_combine"],
        reverse=True
    )


# ------------------------------------------------------------
# HISTORIQUE DES PROMOTIONS
# ------------------------------------------------------------
def get_historique_promotions(nb_semaines: int = 4) -> list:
    """
    Retourne l historique des promotions
    sur les nb_semaines dernieres semaines.

    Utile pour identifier les cycles de promotions
    recurrents (ex : saumon en promo toutes les 3 semaines).
    """
    conn   = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            h.nom_aliment,
            h.semaine,
            h.annee,
            h.prix_actuel,
            h.prix_moyen,
            h.promo_score,
            h.magasin,
            h.date_releve
        FROM historique_prix h
        WHERE h.promo_score >= ?
          AND h.date_releve >= datetime('now', ? || ' weeks')
        ORDER BY h.date_releve DESC, h.promo_score DESC
    """, (PROMO_SCORE_MIN, f"-{nb_semaines}"))

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


# ------------------------------------------------------------
# RESUME HEBDOMADAIRE
# ------------------------------------------------------------
def afficher_resume_promotions() -> None:
    """
    Affiche un resume lisible des promotions
    de la semaine avec les economies potentielles.
    """
    semaine = datetime.now().isocalendar()[1]
    annee   = datetime.now().year

    print(f"\n{'=' * 65}")
    print(f"  PROMOTIONS SEMAINE {semaine}/{annee}")
    print(f"{'=' * 65}")

    promotions = get_promotions_semaine()

    if not promotions:
        print("  Aucune promotion detectee cette semaine.")
        print(f"  [INFO] Seuil minimum : {PROMO_SCORE_MIN*100:.0f}% de reduction")
        print(f"{'=' * 65}")
        return

    print(
        f"  {'Aliment':<35}"
        f" {'Actuel':>8}"
        f" {'Moyen':>8}"
        f" {'Reduction':>10}"
        f" {'Magasin':>12}"
    )
    print(f"  {'-' * 60}")

    economie_totale = 0.0
    for promo in promotions:
        print(
            f"  {promo['nom']:<35}"
            f" {promo['prix_actuel']:>7.2f}e"
            f" {promo['prix_moyen']:>7.2f}e"
            f" {promo['reduction_pct']:>9.1f}%"
            f" {promo['magasin']:>12}"
        )
        economie_totale += promo["economie_kg"]

    print(f"  {'-' * 60}")
    print(f"  {len(promotions)} promotions detectees")
    print(f"  Economie cumulee : {economie_totale:.2f} e/kg")

    # Aliments prioritaires
    print(f"\n  Top 5 aliments prioritaires (promo + nutrition) :")
    prioritaires = get_aliments_prioritaires()[:5]
    for i, p in enumerate(prioritaires, 1):
        print(
            f"    {i}. {p['nom']:<35}"
            f" score combine : {p['score_combine']:.3f}"
        )

    print(f"{'=' * 65}")


# ------------------------------------------------------------
# TEST AUTONOME
# ------------------------------------------------------------
if __name__ == "__main__":
    afficher_resume_promotions()

    print("\n  Promotions par categorie :")
    par_cat = get_promotions_par_categorie()
    for cat, promos in par_cat.items():
        print(f"\n  {cat} :")
        for p in promos:
            print(f"    {p['nom']} -> -{p['reduction_pct']}%")