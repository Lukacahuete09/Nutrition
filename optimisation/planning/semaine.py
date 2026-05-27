# ============================================================
# CONSTRUCTION DU PLANNING HEBDOMADAIRE COMPLET
# optimisation/planning/semaine.py
#
# Ce module assemble :
#   - Le planning calorique (calories.py)
#   - Les macros journalieres (macros.py)
#   - Les regles de seances (seances.py)
#
# Et produit pour chaque jour :
#   - Les cibles nutritionnelles globales
#   - La repartition par repas (matin / midi / soir)
#   - Les contraintes de digestibilite
#   - Les priorites de macros
#
# Sources :
#   - Areta et al. 2013 — distribution proteique
#   - Burke et al. 2011 — periodisation glucidique
#   - Thomas et al. 2016 — IOC Consensus Statement
# ============================================================

import sys
import os
sys.dont_write_bytecode = True


def _calculer_repas(
    macros_jour : dict,
    regles      : dict,
) -> list:
    """
    Calcule les valeurs nutritionnelles de chaque repas
    en appliquant les parts definies dans seances.py
    aux totaux journaliers calcules par macros.py.

    Retourne une liste de 3 repas avec leurs valeurs exactes.
    """
    repas_liste = []

    for nom_repas in ["repas_1", "repas_2", "repas_3"]:
        if nom_repas not in regles["timing_repas"]:
            continue

        repas_regles = regles["timing_repas"][nom_repas]

        calories_repas  = round(
            macros_jour["calories_reelles"] * repas_regles["part_calories"], 1
        )
        proteines_repas = round(
            macros_jour["proteines_g"] * repas_regles["part_proteines"], 1
        )
        glucides_repas  = round(
            macros_jour["glucides_g"] * repas_regles["part_glucides"], 1
        )
        lipides_repas   = round(
            macros_jour["lipides_g"] * repas_regles["part_lipides"], 1
        )

        # Verification calories calculees vs repartition macros
        calories_verif = round(
            proteines_repas * 4 +
            glucides_repas  * 4 +
            lipides_repas   * 9,
            1
        )

        repas_liste.append({
            "numero"         : int(nom_repas[-1]),
            "nom"            : repas_regles["nom"],
            "moment"         : repas_regles["moment"],
            "digestibilite"  : repas_regles["digestibilite"],
            "calories"       : calories_repas,
            "calories_verif" : calories_verif,
            "proteines_g"    : proteines_repas,
            "glucides_g"     : glucides_repas,
            "lipides_g"      : lipides_repas,
        })

    return repas_liste


def construire_planning_semaine(
    config             : dict,
    planning_calorique : list,
    planning_macros    : list,
) -> list:
    """
    Construit le planning hebdomadaire complet.

    Pour chaque jour :
      - Recapitulatif nutritionnel journalier
      - 3 repas avec valeurs exactes
      - Contraintes digestibilite
      - Priorites macros
      - Alertes

    Retourne une liste de 7 jours.
    """
    # Import ici pour eviter les imports circulaires
    from optimisation.planning.seances import get_regles_seance

    planning_semaine = []

    for i, jour_cal in enumerate(planning_calorique):
        jour_macros = planning_macros[i]
        seance      = jour_cal["seance"]

        # Regles nutritionnelles de la seance
        regles = get_regles_seance(seance)

        # Calcul des repas
        repas = _calculer_repas(jour_macros, regles)

        planning_semaine.append({
            # Identification
            "jour"                  : jour_cal["jour"],
            "seance"                : seance,
            "intensite"             : jour_cal["intensite"],
            "duree_min"             : jour_cal["duree_min"],

            # Cibles journalieres
            "calories_cible"        : jour_cal["calories_cible"],
            "calories_reelles"      : jour_macros["calories_reelles"],
            "proteines_g"           : jour_macros["proteines_g"],
            "glucides_g"            : jour_macros["glucides_g"],
            "lipides_g"             : jour_macros["lipides_g"],

            # Informations depense
            "depense_totale"        : jour_cal["depense_totale"],
            "depense_seance"        : jour_cal["depense_seance"],
            "deficit_applique"      : jour_cal["deficit_applique"],
            "energie_disponible_kg" : jour_macros["energie_disponible_kg"],
            "ed_niveau"             : jour_macros["ed_niveau"],

            # Regles seance
            "digestibilite_avant"   : regles["digestibilite_avant"],
            "priorite_macro"        : regles["priorite_macro"],

            # Repas detailles
            "repas"                 : repas,

            # Alertes
            "alertes"               : jour_macros["alertes"],
        })

    return planning_semaine


def afficher_planning_semaine(planning_semaine: list) -> None:
    """
    Affiche le planning hebdomadaire complet.
    """
    print("\n" + "=" * 90)
    print("  PLANNING HEBDOMADAIRE COMPLET")
    print("=" * 90)

    for jour in planning_semaine:
        print(f"\n  {jour['jour'].upper()} — {jour['seance']}")
        print(f"  {'-' * 60}")
        print(
            f"  Calories : {jour['calories_reelles']:.0f} kcal  |  "
            f"Proteines : {jour['proteines_g']:.0f}g  |  "
            f"Glucides : {jour['glucides_g']:.0f}g  |  "
            f"Lipides : {jour['lipides_g']:.0f}g"
        )
        print(
            f"  Depense seance : {jour['depense_seance']:.0f} kcal  |  "
            f"Deficit : {jour['deficit_applique']:.0f} kcal  |  "
            f"ED : {jour['energie_disponible_kg']:.1f} kcal/kg ({jour['ed_niveau']})"
        )
        print(
            f"  Digestibilite avant effort : {jour['digestibilite_avant']}  |  "
            f"Priorite : {' > '.join(jour['priorite_macro'])}"
        )

        print(f"\n  {'Repas':<30} {'Kcal':>6} {'Prot':>6} {'Gluc':>6} {'Lip':>5} {'Digest':>8}")
        print(f"  {'-' * 65}")

        for repas in jour["repas"]:
            print(
                f"  {repas['nom']:<30}"
                f" {repas['calories']:>5.0f}"
                f" {repas['proteines_g']:>5.0f}g"
                f" {repas['glucides_g']:>5.0f}g"
                f" {repas['lipides_g']:>4.0f}g"
                f" {repas['digestibilite']:>8}"
            )

        if jour["alertes"]:
            print()
            for alerte in jour["alertes"]:
                print(f"  [ALERTE] {alerte}")

    # Recapitulatif semaine
    print("\n" + "=" * 90)
    print("  RECAPITULATIF SEMAINE")
    print("=" * 90)

    nb            = len(planning_semaine)
    moy_kcal      = sum(j["calories_reelles"] for j in planning_semaine) / nb
    moy_prot      = sum(j["proteines_g"]      for j in planning_semaine) / nb
    moy_gluc      = sum(j["glucides_g"]       for j in planning_semaine) / nb
    moy_lip       = sum(j["lipides_g"]        for j in planning_semaine) / nb
    total_depense = sum(j["depense_totale"]   for j in planning_semaine)
    total_deficit = sum(j["deficit_applique"] for j in planning_semaine)

    print(f"  Moyenne calories/jour  : {moy_kcal:.0f} kcal")
    print(f"  Moyenne proteines/jour : {moy_prot:.0f} g")
    print(f"  Moyenne glucides/jour  : {moy_gluc:.0f} g")
    print(f"  Moyenne lipides/jour   : {moy_lip:.0f} g")
    print(f"  Depense totale semaine : {total_depense:.0f} kcal")
    print(f"  Deficit total semaine  : {total_deficit:.0f} kcal")
    print(
        f"  Deficit hebdo theor.   : "
        f"{total_deficit / 7700 * 1000:.0f} g de graisse/semaine"
    )
    print("=" * 90)


# ------------------------------------------------------------
# TEST AUTONOME
# ------------------------------------------------------------
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    ))

    from optimisation.excel.reader     import lire_config_athlete
    from optimisation.engine.calories  import calcul_calories_semaine
    from optimisation.engine.macros    import calcul_macros_semaine

    config             = lire_config_athlete()
    planning_calorique = calcul_calories_semaine(config)
    planning_macros    = calcul_macros_semaine(config, planning_calorique)
    planning_semaine   = construire_planning_semaine(
        config, planning_calorique, planning_macros
    )
    afficher_planning_semaine(planning_semaine)
