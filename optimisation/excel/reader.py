# ============================================================
# LECTURE DU FICHIER DE CONFIGURATION ATHLETE
# optimisation/excel/reader.py
# ============================================================

import os
import sys
import openpyxl
sys.dont_write_bytecode = True


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def _get_cell(ws, row, col):
    val = ws.cell(row=row, column=col).value
    if val is None:
        return None
    if isinstance(val, str):
        val = val.strip()
        if val == "" or val.lower() in ["aucun", "aucune"]:
            return None
    return val


def _get_float(ws, row, col, defaut=0.0):
    val = _get_cell(ws, row, col)
    try:
        return float(val)
    except (TypeError, ValueError):
        return defaut


def _get_int(ws, row, col, defaut=0):
    val = _get_cell(ws, row, col)
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return defaut


def _get_str(ws, row, col, defaut=""):
    val = _get_cell(ws, row, col)
    return str(val) if val is not None else defaut


def _is_oui(ws, row, col) -> bool:
    val = _get_str(ws, row, col, "Non")
    return val.strip().lower() in ["oui", "yes", "1", "true"]


# ------------------------------------------------------------
# LECTURE FEUILLE PROFIL
# Structure :
#   Ligne 1  : titre
#   Ligne 2  : sous-titre
#   Ligne 3  : separateur "Informations personnelles"
#   Lignes 4-9  : labels col1/col4 + valeurs col2/col5
#   Ligne 10 : separateur "Parametres sportifs"
#   Lignes 11-14 : labels col1 + valeurs col2
#   Ligne 15 : separateur "Contraintes alimentaires"
#   Lignes 16-20 : labels col1 + valeurs col2
# ------------------------------------------------------------
def _read_profil(ws) -> dict:
    return {
        # Colonne gauche
        "nom"                    : _get_str  (ws,  4, 2),
        "age"                    : _get_int  (ws,  5, 2),
        "sexe"                   : _get_str  (ws,  6, 2, "M"),
        "taille_cm"              : _get_float(ws,  7, 2),
        "poids_actuel_kg"        : _get_float(ws,  8, 2),
        "poids_cible_kg"         : _get_float(ws,  9, 2),

        # Colonne droite
        "sport"                  : _get_str  (ws,  4, 5),
        "niveau"                 : _get_str  (ws,  5, 5, "Elite"),
        "objectif"               : _get_str  (ws,  6, 5, "Recomposition"),
        "contexte_medical"       : _get_str  (ws,  7, 5),
        "date_debut"             : _get_str  (ws,  8, 5),

        # Parametres sportifs
        "frequence_entrainement" : _get_int  (ws, 11, 2),
        "duree_seance_min"       : _get_int  (ws, 12, 2),
        "annees_pratique"        : _get_int  (ws, 13, 2),
        "competitions_prevues"   : _get_str  (ws, 14, 2, "Non"),

        # Contraintes alimentaires
        "allergies"              : _get_str  (ws, 16, 2),
        "intolerances"           : _get_str  (ws, 17, 2),
        "aliments_exclus_texte"  : _get_str  (ws, 18, 2),
        "regime_particulier"     : _get_str  (ws, 19, 2),
        "contraintes_digestives" : _get_str  (ws, 20, 2),
    }


# ------------------------------------------------------------
# LECTURE FEUILLE PLANNING
# Structure :
#   Ligne 3  : header
#   Lignes 4-10 : 7 jours
#     col1 = Jour
#     col2 = Type de seance
#     col3 = Intensite
#     col4 = Duree (min)
#     col5 = Notes
# ------------------------------------------------------------
def _read_planning(ws) -> list:
    planning = []

    for row in range(4, 11):
        jour = _get_str(ws, row, 1)
        if jour:
            planning.append({
                "jour"      : jour,
                "seance"    : _get_str(ws, row, 2, "Repos"),
                "intensite" : _get_str(ws, row, 3, "faible"),
                "duree_min" : _get_int(ws, row, 4, 0),
                "notes"     : _get_str(ws, row, 5),
            })

    return planning


# ------------------------------------------------------------
# LECTURE FEUILLE NUTRITION
# Structure :
#   Ligne 3  : separateur "Proteines"
#   Ligne 4  : Proteines minimum        col2
#   Ligne 5  : Proteines maximum        col2
#   Ligne 6  : separateur "Lipides"
#   Ligne 7  : Lipides minimum          col2
#   Ligne 8  : separateur "Calories"
#   Ligne 9  : Deficit entrainement     col2
#   Ligne 10 : Deficit repos            col2
#   Ligne 11 : Calories minimum         col2
#   Ligne 12 : Repas par jour           col2
#   Ligne 13 : separateur "Glucides"
#   Ligne 14 : header tableau glucides
#   Lignes 15-20 : glucides par seance
#     col1 = Type seance
#     col2 = Glucides min (g/kg)
#     col3 = Glucides max (g/kg)
#     col4 = Moment cle
#     col5 = Notes
# ------------------------------------------------------------
def _read_nutrition(ws) -> dict:
    nutrition = {
        "proteines_min_g_kg"    : _get_float(ws,  4, 2, 1.8),
        "proteines_max_g_kg"    : _get_float(ws,  5, 2, 2.5),
        "lipides_min_g_kg"      : _get_float(ws,  7, 2, 0.8),
        "deficit_entrainement"  : _get_float(ws,  9, 2, 200.0),
        "deficit_repos"         : _get_float(ws, 10, 2, 0.0),
        "calories_min_absolues" : _get_float(ws, 11, 2, 1800.0),
        "repas_par_jour"        : _get_int  (ws, 12, 2, 3),
        "glucides_par_seance"   : {},
    }

    for row in range(15, 21):
        type_seance = _get_str(ws, row, 1)
        if type_seance:
            nutrition["glucides_par_seance"][type_seance] = {
                "min_g_kg"   : _get_float(ws, row, 2, 3.0),
                "max_g_kg"   : _get_float(ws, row, 3, 5.0),
                "moment_cle" : _get_str  (ws, row, 4),
                "notes"      : _get_str  (ws, row, 5),
            }

    return nutrition


# ------------------------------------------------------------
# LECTURE FEUILLE BUDGET
# Structure :
#   Ligne 3  : separateur "Limites budgetaires"
#   Ligne 4  : Budget hebdomadaire      col2
#   Ligne 5  : Budget quotidien         col2
#   Ligne 6  : Budget par repas         col2
#   Ligne 7  : separateur "Preferences"
#   Ligne 8  : Magasin prefere          col2
#   Ligne 9  : Priorite promotions      col2
#   Ligne 10 : Produits bio             col2
#   Ligne 11 : Marque distributeur      col2
# ------------------------------------------------------------
def _read_budget(ws) -> dict:
    return {
        "budget_hebdo_max"     : _get_float(ws,  4, 2, 80.0),
        "budget_quotidien_max" : _get_float(ws,  5, 2, 12.0),
        "budget_repas_max"     : _get_float(ws,  6, 2,  4.0),
        "magasin_prefere"      : _get_str  (ws,  8, 2, "Leclerc"),
        "priorite_promotions"  : _get_str  (ws,  9, 2, "Oui"),
        "bio_accepte"          : _get_str  (ws, 10, 2, "Non"),
        "marque_distributeur"  : _get_str  (ws, 11, 2, "Oui"),
    }


# ------------------------------------------------------------
# LECTURE FEUILLE ALIMENTS EXCLUS
# Structure :
#   Ligne 3  : header
#   Lignes 4+ : aliments exclus
#     col1 = N
#     col2 = Nom ou mot-cle
#     col3 = Type exclusion (exact / contient / categorie)
#     col4 = Raison
#     col5 = Date ajout
# ------------------------------------------------------------
def _read_aliments_exclus(ws) -> list:
    aliments_exclus = []

    for row in range(4, ws.max_row + 1):
        nom = _get_str(ws, row, 2)
        if nom:
            aliments_exclus.append({
                "nom"           : nom,
                "type_exclusion": _get_str(ws, row, 3, "contient"),
                "raison"        : _get_str(ws, row, 4),
                "date_ajout"    : _get_str(ws, row, 5),
            })

    return aliments_exclus


# ------------------------------------------------------------
# LECTURE FEUILLE STRUCTURE REPAS
# Structure :
#   Ligne 3  : header
#   Ligne 4  : separateur petit-dej
#   Ligne 5  : nb recettes petit-dej    col2=semaine col3=weekend
#   Ligne 6  : batch cooking petit-dej  col2=semaine col3=weekend
#   Ligne 7  : separateur dejeuner
#   Ligne 8  : nb recettes dejeuner     col2=semaine col3=weekend
#   Ligne 9  : batch cooking dejeuner   col2=semaine col3=weekend
#   Ligne 10 : separateur diner
#   Ligne 11 : nb recettes diner        col2=semaine col3=weekend
#   Ligne 12 : batch cooking diner      col2=semaine col3=weekend
# ------------------------------------------------------------
def _read_structure_repas(ws) -> dict:
    return {
        "semaine" : {
            "petit_dej" : {
                "nb_recettes"   : _get_int(ws,  5, 2, 1),
                "batch_cooking" : _is_oui (ws,  6, 2),
            },
            "dejeuner" : {
                "nb_recettes"   : _get_int(ws,  8, 2, 1),
                "batch_cooking" : _is_oui (ws,  9, 2),
            },
            "diner" : {
                "nb_recettes"   : _get_int(ws, 11, 2, 5),
                "batch_cooking" : _is_oui (ws, 12, 2),
            },
        },
        "weekend" : {
            "petit_dej" : {
                "nb_recettes"   : _get_int(ws,  5, 3, 1),
                "batch_cooking" : _is_oui (ws,  6, 3),
            },
            "dejeuner" : {
                "nb_recettes"   : _get_int(ws,  8, 3, 2),
                "batch_cooking" : _is_oui (ws,  9, 3),
            },
            "diner" : {
                "nb_recettes"   : _get_int(ws, 11, 3, 2),
                "batch_cooking" : _is_oui (ws, 12, 3),
            },
        },
    }


# ------------------------------------------------------------
# VALIDATION DU PROFIL
# ------------------------------------------------------------
def _valider_profil(profil: dict) -> list:
    erreurs = []

    champs_obligatoires = {
        "age"            : "Age",
        "sexe"           : "Sexe",
        "taille_cm"      : "Taille",
        "poids_actuel_kg": "Poids actuel",
        "poids_cible_kg" : "Poids cible",
        "sport"          : "Sport pratique",
        "objectif"       : "Objectif",
    }

    for champ, label in champs_obligatoires.items():
        val = profil.get(champ)
        if not val or val == 0:
            erreurs.append(f"[ERREUR] Champ obligatoire manquant : {label}")

    if profil.get("sexe") not in ["M", "F"]:
        erreurs.append("[ERREUR] Sexe doit etre 'M' ou 'F'")

    if profil.get("taille_cm", 0) < 100 or profil.get("taille_cm", 0) > 250:
        erreurs.append("[ERREUR] Taille invalide (doit etre entre 100 et 250 cm)")

    if profil.get("poids_actuel_kg", 0) < 30 or profil.get("poids_actuel_kg", 0) > 250:
        erreurs.append("[ERREUR] Poids actuel invalide")

    return erreurs


# ------------------------------------------------------------
# FONCTION PRINCIPALE
# ------------------------------------------------------------
def lire_config_athlete() -> dict:
    """
    Lit l integralite du fichier athlete_config.xlsx
    et retourne un dictionnaire structure utilisable
    par tous les modules du moteur d optimisation.
    """
    # Gestion du path selon mode d execution
    if os.path.exists("optimisation/data/athlete_config.xlsx"):
        config_path = "optimisation/data/athlete_config.xlsx"
    else:
        config_path = os.path.join(
            os.path.dirname(__file__),
            "..", "data", "athlete_config.xlsx"
        )
        config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"[ERREUR] Fichier de configuration introuvable : {config_path}\n"
            f"[INFO]   Lancez scripts/create_excel_config.py pour le generer."
        )

    print(f"[...] Lecture de la configuration : {config_path}")

    wb = openpyxl.load_workbook(config_path, data_only=True)

    profil          = _read_profil         (wb["PROFIL"])
    planning        = _read_planning       (wb["PLANNING"])
    nutrition       = _read_nutrition      (wb["NUTRITION"])
    budget          = _read_budget         (wb["BUDGET"])
    aliments_exclus = _read_aliments_exclus(wb["ALIMENTS_EXCLUS"])
    structure_repas = _read_structure_repas(wb["STRUCTURE_REPAS"])

    wb.close()

    # Validation
    erreurs = _valider_profil(profil)
    if erreurs:
        for e in erreurs:
            print(e)
        raise ValueError(
            "[ERREUR] Configuration incomplete. "
            "Corrigez les erreurs dans athlete_config.xlsx."
        )

    config = {
        "profil"          : profil,
        "planning"        : planning,
        "nutrition"       : nutrition,
        "budget"          : budget,
        "aliments_exclus" : aliments_exclus,
        "structure_repas" : structure_repas,
    }

    # Affichage recapitulatif
    print(f"[OK] Configuration chargee pour : {profil.get('nom', 'Athlete')}")
    print(f"     Poids actuel  : {profil['poids_actuel_kg']} kg")
    print(f"     Poids cible   : {profil['poids_cible_kg']} kg")
    print(f"     Sport         : {profil['sport']}")
    print(f"     Seances/sem   : {len([j for j in planning if j['seance'].lower() != 'repos'])}")
    print(f"     Budget hebdo  : {budget['budget_hebdo_max']} euros")
    print(f"     Aliments exclus : {len(aliments_exclus)}")
    print(f"     Structure semaine :")
    print(f"       Petit-dej : {structure_repas['semaine']['petit_dej']['nb_recettes']} recette(s)"
          f" — batch : {structure_repas['semaine']['petit_dej']['batch_cooking']}")
    print(f"       Dejeuner  : {structure_repas['semaine']['dejeuner']['nb_recettes']} recette(s)"
          f" — batch : {structure_repas['semaine']['dejeuner']['batch_cooking']}")
    print(f"       Diner     : {structure_repas['semaine']['diner']['nb_recettes']} recette(s)"
          f" — batch : {structure_repas['semaine']['diner']['batch_cooking']}")
    print(f"     Structure week-end :")
    print(f"       Petit-dej : {structure_repas['weekend']['petit_dej']['nb_recettes']} recette(s)"
          f" — batch : {structure_repas['weekend']['petit_dej']['batch_cooking']}")
    print(f"       Dejeuner  : {structure_repas['weekend']['dejeuner']['nb_recettes']} recette(s)"
          f" — batch : {structure_repas['weekend']['dejeuner']['batch_cooking']}")
    print(f"       Diner     : {structure_repas['weekend']['diner']['nb_recettes']} recette(s)"
          f" — batch : {structure_repas['weekend']['diner']['batch_cooking']}")

    return config


# ------------------------------------------------------------
# TEST AUTONOME
# ------------------------------------------------------------
if __name__ == "__main__":
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    ))

    config = lire_config_athlete()

    print("\n--- PROFIL ---")
    for k, v in config["profil"].items():
        print(f"  {k:<30} : {v}")

    print("\n--- PLANNING ---")
    for jour in config["planning"]:
        print(f"  {jour['jour']:<12} {jour['seance']:<35} {jour['intensite']}")

    print("\n--- NUTRITION ---")
    for k, v in config["nutrition"].items():
        if k != "glucides_par_seance":
            print(f"  {k:<30} : {v}")

    print("\n--- GLUCIDES PAR SEANCE ---")
    for seance, val in config["nutrition"]["glucides_par_seance"].items():
        print(f"  {seance:<25} min:{val['min_g_kg']} max:{val['max_g_kg']} g/kg")

    print("\n--- BUDGET ---")
    for k, v in config["budget"].items():
        print(f"  {k:<30} : {v}")

    print("\n--- ALIMENTS EXCLUS ---")
    for a in config["aliments_exclus"]:
        print(f"  [{a['type_exclusion']:<10}] {a['nom']}")

    print("\n--- STRUCTURE REPAS ---")
    for periode, repas in config["structure_repas"].items():
        print(f"  {periode} :")
        for type_repas, params in repas.items():
            print(f"    {type_repas:<12} : {params['nb_recettes']} recette(s) — batch : {params['batch_cooking']}")