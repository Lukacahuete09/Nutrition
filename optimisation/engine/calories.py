# ============================================================
# CALCUL DES BESOINS CALORIQUES JOURNALIERS
# optimisation/engine/calories.py
# ============================================================

import sys
import os
sys.dont_write_bytecode = True


# ------------------------------------------------------------
# COEFFICIENTS D ACTIVITE — MODE DE VIE GENERAL
# Source : FAO/WHO/UNU 2001
# ------------------------------------------------------------
COEFFICIENTS_ACTIVITE = {
    "haute"   : 1.55,
    "moyenne" : 1.375,
    "faible"  : 1.2,
}


# ------------------------------------------------------------
# BLOCS DE BASE — COMPOSITIONS UNITAIRES
#
# Chaque bloc est une liste de tuples (phase, MET, fraction)
# Les fractions de chaque bloc doivent sommer a 1.0
#
# Source MET : Ainsworth et al. 2011
#   Medicine & Science in Sports & Exercise, 43(8), 1575-1581
# ------------------------------------------------------------
BLOCS = {

    # ---- BLOCS ECHAUFFEMENT --------------------------------
    "echauffement_leger" : [
        ("Echauffement leger",   3.5,  0.70),
        ("Mobilite articulaire", 2.5,  0.30),
    ],

    "echauffement_intense" : [
        ("Echauffement course",  4.5,  0.60),
        ("Mobilite dynamique",   3.5,  0.40),
    ],

    # ---- BLOCS MUSCULATION ---------------------------------
    "musculation_lourde" : [
        ("Musculation lourde",   6.0,  0.60),
        ("Repos inter-series",   1.5,  0.40),
    ],

    "musculation_moderee" : [
        ("Musculation moderee",  5.0,  0.60),
        ("Repos inter-series",   1.5,  0.40),
    ],

    "gainage_core" : [
        ("Gainage / core",       3.8,  0.70),
        ("Repos",                1.5,  0.30),
    ],

    # ---- BLOCS SPRINT / VITESSE ----------------------------
    "sprint_pur" : [
        ("Sprint effort max",   14.5,  0.20),
        ("Recuperation",         2.0,  0.80),
    ],

    "chariot_leste" : [
        # (2x20m charge lourde + 2x30m sprint libre) x2
        # Source : Cahill et al. 2019 / Morin & Samozino 2016
        ("Chariot 20m leste",   13.0,  0.15),
        ("Sprint 30m libre",    14.5,  0.15),
        ("Recuperation",         2.0,  0.70),
    ],

    # ---- BLOCS PLIOMETRIE ----------------------------------
    "pliometrie" : [
        ("Pliometrie",           7.0,  0.55),
        ("Repos inter-series",   1.5,  0.45),
    ],

    # ---- BLOCS TECHNIQUE PERCHE ----------------------------
    "technique_perche" : [
        ("Technique perche",     4.0,  0.55),
        ("Sauts complets",       6.0,  0.25),
        ("Analyse / pause",      1.5,  0.20),
    ],

    # ---- BLOCS ENDURANCE -----------------------------------
    "course_moderee" : [
        ("Course moderee",       9.0,  1.00),
    ],

    "fractionne" : [
        ("Sprint fractionne",   12.0,  0.30),
        ("Recuperation",         2.5,  0.70),
    ],

    # ---- BLOCS COMMANDO ------------------------------------
    # Circuit militaire : 1min exo PDC / 50m course en continu
    # Source : Scott et al. 2011 / Gibala et al. 2006
    "circuit_commando" : [
        ("Exercices PDC",        8.5,  0.45),  # burpees, fentes, squats
        ("Course 50m liaison",  11.0,  0.35),  # course entre exos
        ("Transition",           3.0,  0.20),
    ],

    "sprint_300m" : [
        # 300m a fond ~ 45-50sec effort maximal
        # Source : Ainsworth et al. 2011
        ("300m sprint max",     14.0,  0.25),
        ("Recuperation",         2.5,  0.75),
    ],

    # ---- BLOCS RECUPERATION --------------------------------
    "recuperation_active" : [
        ("Marche",               3.0,  0.35),
        ("Etirements",           2.3,  0.40),
        ("Bains froids",         1.5,  0.25),
    ],

    "retour_au_calme" : [
        ("Retour au calme",      2.0,  0.60),
        ("Etirements",           2.3,  0.40),
    ],

    "repos_complet" : [
        ("Repos",                1.3,  1.00),
    ],
}


# ------------------------------------------------------------
# COMPOSITIONS DE SEANCES
#
# Chaque seance est une liste de tuples :
#   (nom_bloc, fraction_de_la_seance_totale)
#
# La somme des fractions doit etre egale a 1.0
#
# SEPARATEUR : utilisez "/" entre les noms de blocs
# dans le planning Excel pour combiner des seances.
# Ex : "Musculation / Sprint" -> concatene les deux
# ------------------------------------------------------------
COMPOSITIONS_SEANCES = {

    "Musculation" : [
        # Bloc                    Fraction   ~duree 120min
        ("echauffement_leger",    0.15),     # 18min
        ("musculation_lourde",    0.55),     # 66min
        ("gainage_core",          0.20),     # 24min
        ("retour_au_calme",       0.10),     # 12min
    ],

    "Sprint" : [
        ("echauffement_intense",  0.20),     # 24min
        ("sprint_pur",            0.55),     # 66min
        ("gainage_core",          0.15),     # 18min
        ("retour_au_calme",       0.10),     # 12min
    ],

    "Chariot" : [
        # Protocol : (2x20m leste + 2x30m sprint) x2
        # Source : Cahill et al. 2019
        ("echauffement_intense",  0.15),     # 18min
        ("chariot_leste",         0.55),     # 66min
        ("gainage_core",          0.20),     # 24min
        ("retour_au_calme",       0.10),     # 12min
    ],

    "Pliometrie" : [
        ("echauffement_intense",  0.20),     # 24min
        ("pliometrie",            0.60),     # 72min
        ("gainage_core",          0.10),     # 12min
        ("retour_au_calme",       0.10),     # 12min
    ],

    "Technique" : [
        ("echauffement_leger",    0.15),     # 18min
        ("technique_perche",      0.70),     # 84min
        ("retour_au_calme",       0.15),     # 18min
    ],

    "Resistance" : [
        ("echauffement_intense",  0.10),     # 12min
        ("course_moderee",        0.50),     # 60min
        ("fractionne",            0.25),     # 30min
        ("retour_au_calme",       0.15),     # 18min
    ],

    # Seance militaire extreme
    # Structure : 2x (30min circuit commando + 300m max)
    # avec 10min pause active entre les deux blocs
    # Source : Gibala et al. 2006 / Scott et al. 2011
    "Commando" : [
        ("echauffement_intense",  0.05),     # 4min
        ("circuit_commando",      0.33),     # 30min bloc 1
        ("sprint_300m",           0.04),     # 3min  300m bloc 1
        ("recuperation_active",   0.11),     # 10min pause
        ("circuit_commando",      0.33),     # 30min bloc 2
        ("sprint_300m",           0.04),     # 3min  300m bloc 2
        ("retour_au_calme",       0.10),     # 9min
    ],

    "Recuperation" : [
        ("recuperation_active",   0.85),
        ("retour_au_calme",       0.15),
    ],

    "Repos" : [
        ("repos_complet",         1.00),
    ],
}


# ------------------------------------------------------------
# ASSEMBLAGE DYNAMIQUE DES SEANCES
#
# Si le nom de seance contient un separateur (/ ou +),
# on decoupe et on concatene les compositions.
#
# Ex : "Musculation / Sprint"
#   -> 50% Musculation + 50% Sprint
#
# Ex : "Musculation / Chariot / Pliometrie"
#   -> 33% Musculation + 33% Chariot + 33% Pliometrie
# ------------------------------------------------------------
SEPARATEURS = [" / ", " + ", " & ", " - "]


def _split_seance(seance: str) -> list:
    """
    Decoupe un nom de seance composite en sous-seances.
    Ex : "Musculation / Sprint" -> ["Musculation", "Sprint"]
    """
    for sep in SEPARATEURS:
        if sep in seance:
            return [s.strip() for s in seance.split(sep)]
    return [seance.strip()]


def _get_composition(seance: str) -> list:
    """
    Retourne la composition d une seance.
    Si la seance est composite, concatene les blocs
    en redistribuant les fractions proportionnellement.
    """
    sous_seances = _split_seance(seance)
    nb           = len(sous_seances)

    composition_finale = []

    for sous_seance in sous_seances:
        # Recherche exacte
        if sous_seance in COMPOSITIONS_SEANCES:
            blocs = COMPOSITIONS_SEANCES[sous_seance]
        else:
            # Recherche partielle
            blocs = None
            for key in COMPOSITIONS_SEANCES:
                if key.lower() in sous_seance.lower():
                    blocs = COMPOSITIONS_SEANCES[key]
                    break

        if blocs is None:
            print(f"[WARN] Seance inconnue : '{sous_seance}' -> ignoree")
            continue

        # Redistribution des fractions : chaque sous-seance
        # occupe 1/nb de la seance totale
        for nom_bloc, fraction in blocs:
            composition_finale.append(
                (nom_bloc, fraction / nb)
            )

    return composition_finale


# ------------------------------------------------------------
# CALCUL DEPENSE SEANCE VIA MET COMPOSITE
# Source : Ainsworth et al. 2011
# ------------------------------------------------------------
def calcul_depense_seance(
    seance    : str,
    poids_kg  : float,
    duree_min : int,
) -> float:
    """
    Calcule la depense calorique d une seance.
    Formule : kcal = MET x poids_kg x duree_heures
    """
    if duree_min == 0:
        return 0.0

    duree_heures      = duree_min / 60.0
    composition       = _get_composition(seance)
    depense           = 0.0

    for nom_bloc, fraction_seance in composition:
        if nom_bloc not in BLOCS:
            print(f"[WARN] Bloc inconnu : '{nom_bloc}' -> ignore")
            continue

        for _, met, fraction_bloc in BLOCS[nom_bloc]:
            depense += met * poids_kg * duree_heures * fraction_seance * fraction_bloc

    return round(depense, 1)


# ------------------------------------------------------------
# FORMULE MIFFLIN-ST JEOR
# Source : Mifflin MD et al., 1990
#   American Journal of Clinical Nutrition, 51(2), 241-247
# ------------------------------------------------------------
def calcul_metabolisme_base(
    poids_kg  : float,
    taille_cm : float,
    age       : int,
    sexe      : str,
) -> float:
    mb = 10 * poids_kg + 6.25 * taille_cm - 5 * age
    mb += 5 if sexe.upper() == "M" else -161
    return round(mb, 1)


# ------------------------------------------------------------
# CALCUL CALORIES CIBLES PAR JOUR
# ------------------------------------------------------------
def calcul_calories_jour(
    mb                      : float,
    seance                  : str,
    intensite               : str,
    duree_min               : int,
    poids_kg                : float,
    deficit_entrainement    : float,
    deficit_repos           : float,
    calories_min            : float,
) -> dict:

    coeff          = COEFFICIENTS_ACTIVITE.get(intensite.lower(), 1.2)
    depense_base   = round(mb * coeff, 1)
    depense_seance = calcul_depense_seance(seance, poids_kg, duree_min)
    depense_totale = round(depense_base + depense_seance, 1)

    # Choix du deficit selon le type de jour
    if intensite.lower() == "faible" or seance.lower() == "repos":
        deficit = deficit_repos
    else:
        deficit = deficit_entrainement

    calories_cible = round(depense_totale - deficit, 1)
    calories_cible = max(calories_cible, calories_min)

    return {
        "mb"               : mb,
        "coeff_activite"   : coeff,
        "depense_base"     : depense_base,
        "depense_seance"   : depense_seance,
        "depense_totale"   : depense_totale,
        "deficit_applique" : deficit,
        "calories_cible"   : calories_cible,
    }


# ------------------------------------------------------------
# CALCUL COMPLET — 7 JOURS
# ------------------------------------------------------------
def calcul_calories_semaine(config: dict) -> list:
    profil    = config["profil"]
    planning  = config["planning"]
    nutrition = config["nutrition"]

    mb = calcul_metabolisme_base(
        poids_kg  = profil["poids_actuel_kg"],
        taille_cm = profil["taille_cm"],
        age       = profil["age"],
        sexe      = profil["sexe"],
    )

    print(f"[OK] Metabolisme de base : {mb} kcal/jour")

    resultats = []

    for jour_data in planning:
        calcul = calcul_calories_jour(
            mb                   = mb,
            seance               = jour_data["seance"],
            intensite            = jour_data["intensite"],
            duree_min            = jour_data["duree_min"],
            poids_kg             = profil["poids_actuel_kg"],
            deficit_entrainement = nutrition["deficit_entrainement"],
            deficit_repos        = nutrition["deficit_repos"],
            calories_min         = nutrition["calories_min_absolues"],
        )


        resultats.append({
            "jour"             : jour_data["jour"],
            "seance"           : jour_data["seance"],
            "intensite"        : jour_data["intensite"],
            "duree_min"        : jour_data["duree_min"],
            "mb"               : calcul["mb"],
            "coeff_activite"   : calcul["coeff_activite"],
            "depense_base"     : calcul["depense_base"],
            "depense_seance"   : calcul["depense_seance"],
            "depense_totale"   : calcul["depense_totale"],
            "deficit_applique" : calcul["deficit_applique"],
            "calories_cible"   : calcul["calories_cible"],
        })

    return resultats


# ------------------------------------------------------------
# AFFICHAGE DU PLANNING CALORIQUE
# ------------------------------------------------------------
def afficher_planning_calorique(planning_calorique: list) -> None:
    print("\n" + "=" * 85)
    print("  PLANNING CALORIQUE HEBDOMADAIRE")
    print("=" * 85)
    print(
        f"  {'Jour':<12}"
        f" {'Seance':<35}"
        f" {'Base':>7}"
        f" {'Seance':>7}"
        f" {'Total':>7}"
        f" {'Cible':>7}"
    )
    print("-" * 85)

    total_depense = 0
    total_cible   = 0

    for jour in planning_calorique:
        print(
            f"  {jour['jour']:<12}"
            f" {jour['seance']:<35}"
            f" {jour['depense_base']:>6.0f}"
            f" {jour['depense_seance']:>7.0f}"
            f" {jour['depense_totale']:>7.0f}"
            f" {jour['calories_cible']:>7.0f}"
        )
        total_depense += jour["depense_totale"]
        total_cible   += jour["calories_cible"]

    print("-" * 85)
    print(
        f"  {'TOTAL SEMAINE':<55}"
        f" {total_depense:>7.0f}"
        f" {total_cible:>7.0f}"
    )
    print(
        f"  {'MOYENNE JOURNALIERE':<55}"
        f" {total_depense/7:>7.0f}"
        f" {total_cible/7:>7.0f}"
    )
    print("=" * 85)
    print("  Source MB             : Mifflin-St Jeor 1990")
    print("  Source MET            : Ainsworth et al. 2011")
    print("  Source complex train  : Cahill et al. 2019")
    print("  Source HIIT commando  : Gibala et al. 2006")
    print("=" * 85)


# ------------------------------------------------------------
# TEST AUTONOME
# ------------------------------------------------------------
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    ))

    from optimisation.excel.reader import lire_config_athlete

    config             = lire_config_athlete()
    planning_calorique = calcul_calories_semaine(config)
    afficher_planning_calorique(planning_calorique)