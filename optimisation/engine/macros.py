# ============================================================
# CALCUL DES MACRONUTRIMENTS JOURNALIERS
# optimisation/engine/macros.py
#
# Sources scientifiques :
#   - ISSN Position Stand 2023 — Stecker et al. 2023
#   - Areta et al. 2013 — distribution proteique
#     Journal of Physiology, 591(9), 2319-2331
#   - Burke et al. 2011 — periodisation glucidique
#     Journal of Sports Sciences, 29(S1), S17-S27
#   - Jeukendrup 2014 — Train High / Train Low
#     Sports Medicine, 44(S1), S25-S33
#   - Volek et al. 2006 — lipides et hormones
#     Journal of the American College of Nutrition
#   - Hamalainen et al. 1984 — testosterone et lipides
#   - Loucks et al. 2011 — energie disponible minimum
#     International Journal of Sport Nutrition
#   - Helms et al. 2014 — deficit calorique athlete
#     International Journal of Sport Nutrition
#   - Hall et al. 2012 — metabolisme deficit — Lancet
#   - Barakat et al. 2020 — recomposition corporelle
#     Journal of Strength and Conditioning Research
#   - Antonio et al. 2020 — prise de masse ISSN
#   - Corrigan & Escuro 2017 — nutrition post-trauma cranien
#   - Manore et al. 2009 — NAP athlete repos
# ============================================================

import sys
import os
sys.dont_write_bytecode = True


# ------------------------------------------------------------
# CONSTANTES SCIENTIFIQUES
# Source : Atwater factors
# ------------------------------------------------------------
KCAL_PAR_G = {
    "proteines" : 4.0,
    "glucides"  : 4.0,
    "lipides"   : 9.0,
}


# ------------------------------------------------------------
# SEUILS PAR OBJECTIF
#
# Source :
#   Recomposition / Perte poids : Helms et al. 2014
#   Maintien                    : Loucks et al. 2011
#   Prise de masse              : Antonio et al. 2020
# ------------------------------------------------------------
SEUILS_PAR_OBJECTIF = {

    "recomposition" : {
        "ed_alerte_kcal_kg"  : 20.0,   # danger absolu
        "ed_optimal_kcal_kg" : 25.0,   # acceptable en deficit
        "deficit_max_kcal"   : 500.0,
        "glucides_tolerance" : 1.15,   # +15% borne max toleree
    },

    "perte de poids" : {
        "ed_alerte_kcal_kg"  : 20.0,
        "ed_optimal_kcal_kg" : 25.0,
        "deficit_max_kcal"   : 500.0,
        "glucides_tolerance" : 1.10,
    },

    "maintien" : {
        "ed_alerte_kcal_kg"  : 30.0,
        "ed_optimal_kcal_kg" : 35.0,
        "deficit_max_kcal"   :   0.0,
        "glucides_tolerance" : 1.05,
    },

    "prise de masse" : {
        "ed_alerte_kcal_kg"  : 35.0,
        "ed_optimal_kcal_kg" : 40.0,
        "deficit_max_kcal"   :   0.0,
        "glucides_tolerance" : 1.00,
    },
}


# ------------------------------------------------------------
# MULTIPLICATEURS PROTEIQUES PAR TYPE DE SEANCE
#
# Source : ISSN Position Stand 2023
#   Recomposition       : 2.2 - 3.1 g/kg/j
#   Post-traumatisme    : 1.5 - 2.0 g/kg/j minimum
#     (Corrigan & Escuro 2017)
#   Distribution        : toutes les 3-4h
#     (Areta et al. 2013)
# ------------------------------------------------------------
MULTIPLICATEUR_PROTEINES = {
    "Musculation"  : 1.10,  # +10% synthese musculaire maximale
    "Chariot"      : 1.10,  # +10% effort neuromusculaire intense
    "Pliometrie"   : 1.05,  # +5%  stress musculaire eleve
    "Sprint"       : 1.05,  # +5%  catabolisme proteique modere
    "Technique"    : 1.00,  # =    maintenance
    "Resistance"   : 1.00,  # =    endurance
    "Commando"     : 1.15,  # +15% catabolisme extreme
    "Recuperation" : 0.95,  # -5%  besoins reduits
    "Repos"        : 0.90,  # -10% metabolisme repos
}

SEPARATEURS = [" / ", " + ", " & ", " - "]


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def _split_seance(seance: str) -> list:
    for sep in SEPARATEURS:
        if sep in seance:
            return [s.strip() for s in seance.split(sep)]
    return [seance.strip()]


def _get_seuils(objectif: str) -> dict:
    """
    Retourne les seuils correspondant a l objectif.
    Recherche partielle insensible a la casse.
    """
    objectif_lower = objectif.strip().lower()
    for key, val in SEUILS_PAR_OBJECTIF.items():
        if key in objectif_lower:
            return val
    return SEUILS_PAR_OBJECTIF["recomposition"]


def _get_multiplicateur_proteines(seance: str) -> float:
    """
    Calcule le multiplicateur proteique moyen
    pour une seance composite.
    Ex : "Musculation / Sprint" -> (1.10 + 1.05) / 2 = 1.075
    """
    sous_seances    = _split_seance(seance)
    multiplicateurs = []

    for ss in sous_seances:
        trouve = False
        for key, val in MULTIPLICATEUR_PROTEINES.items():
            if key.lower() in ss.lower():
                multiplicateurs.append(val)
                trouve = True
                break
        if not trouve:
            multiplicateurs.append(1.0)

    return round(sum(multiplicateurs) / len(multiplicateurs), 4)


# ------------------------------------------------------------
# CALCUL DES PROTEINES
#
# Source : ISSN Position Stand 2023
#   Recomposition               : 2.2 - 3.1 g/kg/j
#   Preservation masse deficit  : 2.2 - 2.5 g/kg/j
#     (Helms et al. 2014)
#   Post-traumatisme            : minimum 1.5 - 2.0 g/kg/j
#     (Corrigan & Escuro 2017)
# ------------------------------------------------------------
def calcul_proteines(
    poids_kg       : float,
    ratio_min_g_kg : float,
    ratio_max_g_kg : float,
    seance         : str,
) -> float:
    """
    Calcule les proteines cibles en grammes.
    Plafonnees au ratio max defini dans Excel.
    """
    multiplicateur = _get_multiplicateur_proteines(seance)
    proteines_g    = poids_kg * ratio_min_g_kg * multiplicateur
    proteines_g    = min(proteines_g, poids_kg * ratio_max_g_kg)
    return round(proteines_g, 1)


# ------------------------------------------------------------
# CALCUL DES LIPIDES
#
# Source : Volek et al. 2006
#   Fonction hormonale athlete  : 1.0 - 1.5 g/kg/j
#   Testosterone et performance : minimum 1.0 g/kg/j
#     (Hamalainen et al. 1984)
# ------------------------------------------------------------
def calcul_lipides(
    poids_kg         : float,
    lipides_min_g_kg : float,
) -> float:
    """
    Calcule les lipides minimum en grammes.
    Garantit la fonction hormonale de base.
    """
    return round(poids_kg * lipides_min_g_kg, 1)


# ------------------------------------------------------------
# CALCUL DES GLUCIDES PAR PERIODISATION
#
# Source : Burke et al. 2011 / Jeukendrup 2014
#   Sport puissance/force-vitesse :
#     Entrainement intense : 5-7 g/kg/j
#     Repos                : 3-4 g/kg/j
# ------------------------------------------------------------
def calcul_glucides(
    calories_cible  : float,
    proteines_g     : float,
    lipides_g       : float,
    poids_kg        : float,
    seance          : str,
    glucides_config : dict,
    objectif        : str,
) -> dict:
    """
    Calcule les glucides par difference calorique.
    Verifie les bornes de periodisation.
    Contextualise le statut selon l objectif.
    """
    kcal_proteines = proteines_g * KCAL_PAR_G["proteines"]
    kcal_lipides   = lipides_g   * KCAL_PAR_G["lipides"]
    kcal_glucides  = calories_cible - kcal_proteines - kcal_lipides
    glucides_g     = round(kcal_glucides / KCAL_PAR_G["glucides"], 1)
    glucides_g     = max(glucides_g, 0.0)

    # Recuperation bornes depuis config Excel
    bornes       = None
    sous_seances = _split_seance(seance)

    for ss in sous_seances:
        for key in glucides_config:
            if key.lower() in ss.lower():
                bornes = glucides_config[key]
                break
        if bornes:
            break

    if bornes is None:
        bornes = {"min_g_kg": 3.0, "max_g_kg": 5.0}

    glucides_min_g = round(poids_kg * bornes["min_g_kg"], 1)
    glucides_max_g = round(poids_kg * bornes["max_g_kg"], 1)

    # Tolerance sur borne max selon objectif
    seuils              = _get_seuils(objectif)
    tolerance           = seuils["glucides_tolerance"]
    glucides_max_tolere = round(glucides_max_g * tolerance, 1)

    # Statut contextualise
    objectif_lower = objectif.strip().lower()
    en_deficit     = "perte" in objectif_lower or "recomposition" in objectif_lower

    if glucides_g > glucides_max_tolere:
        statut = "sur_maximum"
    elif glucides_g > glucides_max_g:
        statut = "dans_tolerance"
    elif glucides_g < glucides_min_g:
        statut = "acceptable_deficit" if en_deficit else "sous_minimum"
    else:
        statut = "ok"

    return {
        "glucides_g"          : glucides_g,
        "glucides_min_g"      : glucides_min_g,
        "glucides_max_g"      : glucides_max_g,
        "glucides_max_tolere" : glucides_max_tolere,
        "statut"              : statut,
    }


# ------------------------------------------------------------
# VERIFICATION ENERGIE DISPONIBLE
#
# Source : Loucks et al. 2011
#   Seuil critique  : < 30 kcal/kg/j
#   Optimal athlete : 40-45 kcal/kg/j
#
# Contextualise selon objectif :
#   Perte poids / Recomposition : alerte si < 20 kcal/kg
#     (Helms et al. 2014)
# ------------------------------------------------------------
def verifier_energie_disponible(
    calories_cible : float,
    depense_seance : float,
    poids_kg       : float,
    objectif       : str,
) -> dict:
    """
    Verifie l energie disponible selon l objectif.
    """
    seuils                = _get_seuils(objectif)
    energie_disponible    = calories_cible - depense_seance
    energie_disponible_kg = round(energie_disponible / poids_kg, 1)
    seuil_alerte          = seuils["ed_alerte_kcal_kg"]
    seuil_optimal         = seuils["ed_optimal_kcal_kg"]

    if energie_disponible_kg < seuil_alerte:
        niveau = "danger"
    elif energie_disponible_kg < seuil_optimal:
        niveau = "acceptable"
    else:
        niveau = "optimal"

    return {
        "energie_disponible"    : round(energie_disponible, 1),
        "energie_disponible_kg" : energie_disponible_kg,
        "seuil_alerte"          : seuil_alerte,
        "seuil_optimal"         : seuil_optimal,
        "niveau"                : niveau,
        "alerte"                : niveau == "danger",
    }


# ------------------------------------------------------------
# CALCUL COMPLET DES MACROS — 1 JOUR
# ------------------------------------------------------------
def calcul_macros_jour(
    calories_cible   : float,
    depense_seance   : float,
    seance           : str,
    poids_kg         : float,
    nutrition_config : dict,
    objectif         : str,
) -> dict:
    """
    Calcule les macros cibles pour un jour donne.
    """
    # 1. Proteines
    proteines_g = calcul_proteines(
        poids_kg       = poids_kg,
        ratio_min_g_kg = nutrition_config["proteines_min_g_kg"],
        ratio_max_g_kg = nutrition_config["proteines_max_g_kg"],
        seance         = seance,
    )

    # 2. Lipides
    lipides_g = calcul_lipides(
        poids_kg         = poids_kg,
        lipides_min_g_kg = nutrition_config["lipides_min_g_kg"],
    )

    # 3. Glucides par difference
    glucides_result = calcul_glucides(
        calories_cible  = calories_cible,
        proteines_g     = proteines_g,
        lipides_g       = lipides_g,
        poids_kg        = poids_kg,
        seance          = seance,
        glucides_config = nutrition_config["glucides_par_seance"],
        objectif        = objectif,
    )

    # 4. Calories reelles apres calcul
    calories_reelles = round(
        proteines_g                   * KCAL_PAR_G["proteines"] +
        glucides_result["glucides_g"] * KCAL_PAR_G["glucides"]  +
        lipides_g                     * KCAL_PAR_G["lipides"],
        1
    )

    # 5. Energie disponible contextualisee
    ed = verifier_energie_disponible(
        calories_cible = calories_reelles,
        depense_seance = depense_seance,
        poids_kg       = poids_kg,
        objectif       = objectif,
    )

    # 6. Alertes uniquement — pas d infos pour les cas normaux
    alertes        = []
    objectif_lower = objectif.strip().lower()
    en_deficit     = "perte" in objectif_lower or "recomposition" in objectif_lower
    en_surplus     = "masse" in objectif_lower
    en_maintien    = "maintien" in objectif_lower

    # ---- GLUCIDES --------------------------------------------
    if glucides_result["statut"] == "sur_maximum":
        if not en_surplus:
            alertes.append(
                f"Glucides trop eleves : "
                f"{glucides_result['glucides_g']}g > "
                f"{glucides_result['glucides_max_tolere']}g"
            )

    elif glucides_result["statut"] == "acceptable_deficit":
        ecart_pct = (
            (glucides_result["glucides_min_g"] - glucides_result["glucides_g"])
            / glucides_result["glucides_min_g"]
            * 100
        )
        if ecart_pct > 30:
            alertes.append(
                f"Glucides trop bas ({ecart_pct:.0f}% sous reference) : "
                f"{glucides_result['glucides_g']}g vs "
                f"minimum {glucides_result['glucides_min_g']}g — "
                f"risque catabolisme et recuperation neurologique"
            )

    elif glucides_result["statut"] == "sous_minimum":
        if en_surplus:
            alertes.append(
                f"Glucides insuffisants en prise de masse : "
                f"{glucides_result['glucides_g']}g < "
                f"{glucides_result['glucides_min_g']}g — "
                f"freine la synthese musculaire"
            )
        elif en_maintien:
            alertes.append(
                f"Glucides sous le minimum : "
                f"{glucides_result['glucides_g']}g < "
                f"{glucides_result['glucides_min_g']}g — "
                f"risque fatigue et perte de performance"
            )
        else:
            alertes.append(
                f"Glucides insuffisants : "
                f"{glucides_result['glucides_g']}g < "
                f"{glucides_result['glucides_min_g']}g"
            )

    # ---- ENERGIE DISPONIBLE ----------------------------------
    if ed["alerte"]:
        if en_surplus:
            alertes.append(
                f"DANGER ED en prise de masse : "
                f"{ed['energie_disponible_kg']} kcal/kg — "
                f"impossible de construire du muscle. "
                f"Seuil : {ed['seuil_alerte']} kcal/kg"
            )
        else:
            alertes.append(
                f"DANGER energie disponible : "
                f"{ed['energie_disponible_kg']} kcal/kg "
                f"(seuil : {ed['seuil_alerte']} kcal/kg)"
            )

    elif ed["niveau"] == "acceptable" and (en_surplus or en_maintien):
        alertes.append(
            f"Energie disponible insuffisante pour {objectif} : "
            f"{ed['energie_disponible_kg']} kcal/kg "
            f"(optimal : {ed['seuil_optimal']} kcal/kg)"
        )

    return {
        "proteines_g"           : proteines_g,
        "lipides_g"             : lipides_g,
        "glucides_g"            : glucides_result["glucides_g"],
        "glucides_min_g"        : glucides_result["glucides_min_g"],
        "glucides_max_g"        : glucides_result["glucides_max_g"],
        "glucides_statut"       : glucides_result["statut"],
        "calories_cible"        : calories_cible,
        "calories_reelles"      : calories_reelles,
        "energie_disponible"    : ed["energie_disponible"],
        "energie_disponible_kg" : ed["energie_disponible_kg"],
        "ed_niveau"             : ed["niveau"],
        "alertes"               : alertes,
    }


# ------------------------------------------------------------
# CALCUL COMPLET — 7 JOURS
# ------------------------------------------------------------
def calcul_macros_semaine(
    config             : dict,
    planning_calorique : list,
) -> list:
    """
    Calcule les macros pour chaque jour de la semaine.
    """
    profil    = config["profil"]
    nutrition = config["nutrition"]
    poids_kg  = profil["poids_actuel_kg"]
    objectif  = profil["objectif"]

    print(f"[OK] Objectif detecte  : {objectif}")
    print(f"     Seuil ED danger   : {_get_seuils(objectif)['ed_alerte_kcal_kg']} kcal/kg")
    print(f"     Seuil ED optimal  : {_get_seuils(objectif)['ed_optimal_kcal_kg']} kcal/kg")
    print(f"     Tolerance glucides: +{(_get_seuils(objectif)['glucides_tolerance']-1)*100:.0f}%")

    resultats = []

    for jour_cal in planning_calorique:
        macros = calcul_macros_jour(
            calories_cible   = jour_cal["calories_cible"],
            depense_seance   = jour_cal["depense_seance"],
            seance           = jour_cal["seance"],
            poids_kg         = poids_kg,
            nutrition_config = nutrition,
            objectif         = objectif,
        )

        resultats.append({
            "jour"                  : jour_cal["jour"],
            "seance"                : jour_cal["seance"],
            "calories_cible"        : jour_cal["calories_cible"],
            "proteines_g"           : macros["proteines_g"],
            "glucides_g"            : macros["glucides_g"],
            "lipides_g"             : macros["lipides_g"],
            "glucides_statut"       : macros["glucides_statut"],
            "calories_reelles"      : macros["calories_reelles"],
            "energie_disponible_kg" : macros["energie_disponible_kg"],
            "ed_niveau"             : macros["ed_niveau"],
            "alertes"               : macros["alertes"],
        })

    return resultats


# ------------------------------------------------------------
# AFFICHAGE
# ------------------------------------------------------------
def afficher_macros_semaine(planning_macros: list) -> None:
    print("\n" + "=" * 100)
    print("  PLANNING MACRONUTRIMENTS HEBDOMADAIRE")
    print("=" * 100)
    print(
        f"  {'Jour':<12}"
        f" {'Seance':<32}"
        f" {'Cible':>6}"
        f" {'Reelles':>7}"
        f" {'Prot':>6}"
        f" {'Gluc':>6}"
        f" {'Lip':>5}"
        f" {'ED/kg':>6}"
        f" {'Niveau':>10}"
    )
    print("-" * 100)

    total_cible   = 0
    total_reelles = 0

    for jour in planning_macros:
        print(
            f"  {jour['jour']:<12}"
            f" {jour['seance']:<32}"
            f" {jour['calories_cible']:>6.0f}"
            f" {jour['calories_reelles']:>7.0f}"
            f" {jour['proteines_g']:>5.0f}g"
            f" {jour['glucides_g']:>5.0f}g"
            f" {jour['lipides_g']:>4.0f}g"
            f" {jour['energie_disponible_kg']:>5.1f}"
            f" {jour['ed_niveau']:>10}"
        )
        for alerte in jour["alertes"]:
            print(f"    [ALERTE] {alerte}")

        total_cible   += jour["calories_cible"]
        total_reelles += jour["calories_reelles"]

    nb       = len(planning_macros)
    moy_prot = sum(j["proteines_g"] for j in planning_macros) / nb
    moy_gluc = sum(j["glucides_g"]  for j in planning_macros) / nb
    moy_lip  = sum(j["lipides_g"]   for j in planning_macros) / nb

    print("-" * 100)
    print(
        f"  {'MOYENNE JOURNALIERE':<44}"
        f" {total_cible/nb:>6.0f}"
        f" {total_reelles/nb:>7.0f}"
        f" {moy_prot:>5.0f}g"
        f" {moy_gluc:>5.0f}g"
        f" {moy_lip:>4.0f}g"
    )
    print("=" * 100)
    print("  Source proteines : ISSN Position Stand 2023 / Helms et al. 2014")
    print("  Source glucides  : Burke et al. 2011 / Jeukendrup 2014")
    print("  Source lipides   : Volek et al. 2006 / Hamalainen et al. 1984")
    print("  Source ED        : Loucks et al. 2011 / Helms et al. 2014")
    print("=" * 100)


# ------------------------------------------------------------
# TEST AUTONOME
# ------------------------------------------------------------
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    ))

    from optimisation.excel.reader    import lire_config_athlete
    from optimisation.engine.calories import calcul_calories_semaine

    config             = lire_config_athlete()
    planning_calorique = calcul_calories_semaine(config)
    planning_macros    = calcul_macros_semaine(config, planning_calorique)
    afficher_macros_semaine(planning_macros)