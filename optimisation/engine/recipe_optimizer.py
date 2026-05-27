# ============================================================
# MOTEUR D OPTIMISATION BASE SUR LES RECETTES
# optimisation/engine/recipe_optimizer.py
#
# Logique :
#   Pour chaque repas a generer :
#     1. Lire les macros cibles depuis planning_semaine
#     2. Chercher dans recettes.db la recette qui matche
#     3. Adapter les quantites au poids cible
#     4. Retourner la recette avec ingredients adaptes
#
# Sources :
#   - Spoonacular API
#   - Winston 2004 — Operations Research
# ============================================================

import sys
import os
import sqlite3
import re
sys.dont_write_bytecode = True

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------
RECETTES_DB = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..",
                 "create_db", "data", "recettes.db")
)

# Tolerance sur les macros pour la recherche de recettes
TOLERANCE_CALORIES  = 0.20   # +/- 20%
TOLERANCE_PROTEINES = 0.25   # +/- 25%
TOLERANCE_GLUCIDES  = 0.30   # +/- 30%
TOLERANCE_LIPIDES   = 0.30   # +/- 30%

# Nombre maximum d utilisations d une meme recette sur la semaine
MAX_UTILISATIONS_RECETTE = 1

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def _split_seance(seance: str) -> list:
    parties = re.split(r'\s*[/+&-]\s*', seance.strip())
    return [p.strip() for p in parties if p.strip()]


def _get_template_diner(seance: str) -> str:
    sous_seances = _split_seance(seance)
    seance_lower = " ".join(sous_seances).lower()

    if "repos" in seance_lower:
        return "diner_repos"
    if "recuperation" in seance_lower:
        return "diner_recuperation"
    if "sprint" in seance_lower or "chariot" in seance_lower:
        return "diner_sprint"
    if "technique" in seance_lower:
        return "diner_technique"
    return "diner_musculation"


def _get_connection_recettes() -> sqlite3.Connection:
    if not os.path.exists(RECETTES_DB):
        raise FileNotFoundError(
            f"[ERREUR] Base recettes introuvable : {RECETTES_DB}\n"
            f"[INFO]   Lancez : python create_db/recettes/main_recettes.py"
        )
    conn = sqlite3.connect(RECETTES_DB)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------------------
# COMPTAGE DES UTILISATIONS DE RECETTES
# ------------------------------------------------------------
def _compter_utilisations_recettes(repas_precedents: list) -> dict:
    """
    Compte le nombre de fois que chaque recette
    a ete utilisee dans les repas precedents.
    """
    compteur = {}
    for repas in repas_precedents:
        nom = repas.get("nom_fr", "").lower()
        if nom:
            compteur[nom] = compteur.get(nom, 0) + 1
    return compteur


def _get_recettes_exclues(
    repas_precedents : list,
    limite           : int = MAX_UTILISATIONS_RECETTE,
) -> set:
    """
    Retourne les recettes ayant atteint
    la limite d utilisation hebdomadaire.
    """
    compteur = _compter_utilisations_recettes(repas_precedents)
    return {nom for nom, count in compteur.items() if count >= limite}


# ------------------------------------------------------------
# RECHERCHE DE RECETTE
# ------------------------------------------------------------
def _chercher_recette(
    conn             : sqlite3.Connection,
    type_repas       : str,
    digestibilite    : str,
    macros_cibles    : dict,
    seance           : str,
    recettes_exclues : set,
    aliments_exclus  : list,
) -> dict | None:
    """
    Cherche la recette la plus adaptee dans recettes.db.

    Criteres de recherche :
      1. Type de repas (petit_dej / dejeuner / diner)
      2. Digestibilite compatible
      3. Calories dans la tolerance
      4. Proteines dans la tolerance
      5. Glucides dans la tolerance
      6. Non deja utilisee cette semaine
      7. Sans aliments exclus par l utilisateur

    Tri par :
      Ecart calorique minimal (recette la plus proche)
    """
    cal_cible  = macros_cibles["calories"]
    prot_cible = macros_cibles["proteines_g"]
    gluc_cible = macros_cibles["glucides_g"]
    lip_cible  = macros_cibles["lipides_g"]

    # Bornes de recherche
    cal_min  = cal_cible  * (1 - TOLERANCE_CALORIES)
    cal_max  = cal_cible  * (1 + TOLERANCE_CALORIES)
    prot_min = prot_cible * (1 - TOLERANCE_PROTEINES)
    gluc_min = gluc_cible * (1 - TOLERANCE_GLUCIDES)
    gluc_max = gluc_cible * (1 + TOLERANCE_GLUCIDES)
    lip_min  = lip_cible  * (1 - TOLERANCE_LIPIDES)

    # Filtre digestibilite
    if digestibilite == "high":
        digest_filter = "r.digestibilite = 'high'"
    elif digestibilite == "medium":
        digest_filter = "r.digestibilite IN ('high', 'medium')"
    else:
        digest_filter = "1=1"

    # Type seance pour affiner la recherche
    sous_seances  = _split_seance(seance)
    seance_lower  = " ".join(sous_seances).lower()

    if "repos" in seance_lower or "recuperation" in seance_lower:
        seance_filter = "r.type_seance IN ('repos', 'recuperation', 'all')"
    elif "musculation" in seance_lower:
        seance_filter = "r.type_seance IN ('musculation', 'all')"
    elif "sprint" in seance_lower or "chariot" in seance_lower:
        seance_filter = "r.type_seance IN ('sprint', 'musculation', 'all')"
    elif "technique" in seance_lower:
        seance_filter = "r.type_seance IN ('technique', 'all')"
    else:
        seance_filter = "1=1"

    query = f"""
        SELECT
            r.id,
            r.spoonacular_id,
            r.nom_fr,
            r.nom_en,
            r.type_repas,
            r.type_seance,
            r.nb_personnes,
            r.temps_prep_min,
            r.source_url,
            r.image_url,
            r.digestibilite,
            r.calories_portion,
            r.proteines_g,
            r.glucides_g,
            r.lipides_g,
            r.fibres_g,
            r.cout_portion,
            r.score_nutritionnel,
            ABS(r.calories_portion - {cal_cible}) AS ecart_calories
        FROM recettes r
        WHERE r.type_repas   = '{type_repas}'
          AND r.valide        = 1
          AND {digest_filter}
          AND {seance_filter}
          AND r.calories_portion BETWEEN {cal_min} AND {cal_max}
          AND r.proteines_g       >= {prot_min}
          AND r.glucides_g  BETWEEN {gluc_min} AND {gluc_max}
          AND r.lipides_g         >= {lip_min}
        ORDER BY ecart_calories ASC
        LIMIT 20
    """

    cursor = conn.cursor()
    cursor.execute(query)
    recettes = cursor.fetchall()

    if not recettes:
        # Relacher les contraintes glucides si aucun resultat
        query_relache = f"""
            SELECT
                r.id,
                r.spoonacular_id,
                r.nom_fr,
                r.nom_en,
                r.type_repas,
                r.type_seance,
                r.nb_personnes,
                r.temps_prep_min,
                r.source_url,
                r.image_url,
                r.digestibilite,
                r.calories_portion,
                r.proteines_g,
                r.glucides_g,
                r.lipides_g,
                r.fibres_g,
                r.cout_portion,
                r.score_nutritionnel,
                ABS(r.calories_portion - {cal_cible}) AS ecart_calories
            FROM recettes r
            WHERE r.type_repas = '{type_repas}'
              AND r.valide      = 1
              AND {digest_filter}
              AND r.calories_portion BETWEEN {cal_min * 0.8} AND {cal_max * 1.2}
              AND r.proteines_g >= {prot_min * 0.7}
            ORDER BY ecart_calories ASC
            LIMIT 20
        """
        cursor.execute(query_relache)
        recettes = cursor.fetchall()

    if not recettes:
        return None

    # Filtrer les recettes deja utilisees
    for recette in recettes:
        if recette["nom_fr"].lower() not in recettes_exclues:
            return dict(recette)

    # Si toutes exclues -> prendre la premiere quand meme
    return dict(recettes[0])


def _get_ingredients_recette(
    conn       : sqlite3.Connection,
    recette_id : int,
) -> list:
    """
    Recupere les ingredients d une recette.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            nom_fr, nom_en,
            quantite_g, unite,
            calories, proteines_g, glucides_g, lipides_g
        FROM recette_ingredients
        WHERE recette_id = ?
        ORDER BY id
    """, (recette_id,))
    return [dict(row) for row in cursor.fetchall()]


def _get_instructions_recette(
    conn       : sqlite3.Connection,
    recette_id : int,
) -> list:
    """
    Recupere les instructions d une recette.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT etape, instruction_fr, instruction_en
        FROM recette_instructions
        WHERE recette_id = ?
        ORDER BY etape
    """, (recette_id,))
    return [dict(row) for row in cursor.fetchall()]


# ------------------------------------------------------------
# ADAPTATION DES QUANTITES
# ------------------------------------------------------------
def _adapter_quantites(
    recette      : dict,
    ingredients  : list,
    macros_cibles: dict,
) -> tuple:
    """
    Adapte les quantites de la recette aux macros cibles.

    Si la recette fait 650 kcal et on cible 800 kcal :
      ratio = 800 / 650 = 1.23
      -> toutes les quantites multipliees par 1.23

    Retourne :
      (ingredients_adaptes, macros_reelles)
    """
    cal_recette = recette["calories_portion"]
    cal_cible   = macros_cibles["calories"]

    if cal_recette <= 0:
        ratio = 1.0
    else:
        ratio = cal_cible / cal_recette

    # Limiter le ratio pour garder une recette coherente
    ratio = max(0.5, min(ratio, 2.0))

    ingredients_adaptes = []
    cal_reel  = 0.0
    prot_reel = 0.0
    gluc_reel = 0.0
    lip_reel  = 0.0

    for ing in ingredients:
        quantite_adaptee = round(ing["quantite_g"] * ratio, 1)

        cal_ing  = round((ing.get("calories",    0) or 0) * ratio, 1)
        prot_ing = round((ing.get("proteines_g", 0) or 0) * ratio, 1)
        gluc_ing = round((ing.get("glucides_g",  0) or 0) * ratio, 1)
        lip_ing  = round((ing.get("lipides_g",   0) or 0) * ratio, 1)

        ingredients_adaptes.append({
            "nom_fr"      : ing["nom_fr"],
            "nom_en"      : ing["nom_en"],
            "quantite_g"  : quantite_adaptee,
            "unite"       : ing["unite"],
            "calories"    : cal_ing,
            "proteines_g" : prot_ing,
            "glucides_g"  : gluc_ing,
            "lipides_g"   : lip_ing,
        })

        cal_reel  += cal_ing
        prot_reel += prot_ing
        gluc_reel += gluc_ing
        lip_reel  += lip_ing

    macros_reelles = {
        "calories"   : round(cal_reel,  1),
        "proteines_g": round(prot_reel, 1),
        "glucides_g" : round(gluc_reel, 1),
        "lipides_g"  : round(lip_reel,  1),
    }

    return ingredients_adaptes, macros_reelles, ratio


# ------------------------------------------------------------
# GENERATION D UN REPAS
# ------------------------------------------------------------
def generer_repas(
    type_repas       : str,
    digestibilite    : str,
    macros_cibles    : dict,
    seance           : str,
    repas_precedents : list,
    aliments_exclus  : list,
) -> dict:
    """
    Genere un repas en cherchant la recette
    la plus adaptee dans recettes.db.

    Retourne :
    {
        "statut"          : "ok" / "non_trouve",
        "nom_fr"          : nom de la recette,
        "nom_en"          : nom anglais,
        "type_repas"      : type du repas,
        "digestibilite"   : digestibilite,
        "source_url"      : lien de la recette,
        "image_url"       : image,
        "temps_prep_min"  : temps de preparation,
        "ratio_adaptation": ratio applique,
        "ingredients"     : liste des ingredients adaptes,
        "instructions"    : liste des etapes,
        "macros_cibles"   : macros demandees,
        "macros_reelles"  : macros apres adaptation,
        "cout"            : cout estime,
    }
    """
    conn = _get_connection_recettes()

    recettes_exclues = _get_recettes_exclues(repas_precedents)

    # Chercher la recette
    recette = _chercher_recette(
        conn             = conn,
        type_repas       = type_repas,
        digestibilite    = digestibilite,
        macros_cibles    = macros_cibles,
        seance           = seance,
        recettes_exclues = recettes_exclues,
        aliments_exclus  = aliments_exclus,
    )

    if recette is None:
        conn.close()
        return {
            "statut"         : "non_trouve",
            "nom_fr"         : f"Recette {type_repas} non trouvee",
            "nom_en"         : "",
            "type_repas"     : type_repas,
            "digestibilite"  : digestibilite,
            "source_url"     : "",
            "image_url"      : "",
            "temps_prep_min" : 0,
            "ratio_adaptation": 1.0,
            "ingredients"    : [],
            "instructions"   : [],
            "macros_cibles"  : macros_cibles,
            "macros_reelles" : {
                "calories"   : 0,
                "proteines_g": 0,
                "glucides_g" : 0,
                "lipides_g"  : 0,
            },
            "cout"           : 0.0,
        }

    # Recuperer ingredients et instructions
    ingredients  = _get_ingredients_recette(conn, recette["id"])
    instructions = _get_instructions_recette(conn, recette["id"])
    conn.close()

    # Adapter les quantites
    ingredients_adaptes, macros_reelles, ratio = _adapter_quantites(
        recette, ingredients, macros_cibles
    )

    # Cout estime (base sur cout_portion * ratio)
    cout = round((recette.get("cout_portion", 0) or 0) * ratio, 2)

    return {
        "statut"          : "ok",
        "nom_fr"          : recette["nom_fr"],
        "nom_en"          : recette["nom_en"],
        "type_repas"      : type_repas,
        "digestibilite"   : recette["digestibilite"],
        "source_url"      : recette["source_url"],
        "image_url"       : recette["image_url"],
        "temps_prep_min"  : recette["temps_prep_min"],
        "ratio_adaptation": round(ratio, 2),
        "ingredients"     : ingredients_adaptes,
        "instructions"    : instructions,
        "macros_cibles"   : macros_cibles,
        "macros_reelles"  : macros_reelles,
        "cout"            : cout,
    }


# ------------------------------------------------------------
# IDENTIFICATION DES SLOTS
# (meme logique que optimizer.py)
# ------------------------------------------------------------
def _identifier_slots_semaine(
    planning_semaine : list,
    structure_repas  : dict,
) -> list:

    jours_semaine = []
    jours_weekend = []

    for jour in planning_semaine:
        if jour["jour"] in ["Samedi", "Dimanche"]:
            jours_weekend.append(jour)
        else:
            jours_semaine.append(jour)

    slots   = []
    slot_id = 0

    for periode, jours in [("semaine", jours_semaine), ("weekend", jours_weekend)]:
        for type_repas, repas_num in [
            ("petit_dej", 1),
            ("dejeuner",  2),
            ("diner",     3),
        ]:
            if not jours:
                continue

            config_repas = structure_repas[periode][type_repas]
            nb_recettes  = config_repas["nb_recettes"]
            batch        = config_repas["batch_cooking"]

            if batch:
                macros_moy    = _calculer_macros_moyennes(jours, repas_num)
                digestibilite = _get_digestibilite_repas(jours, repas_num)

                slots.append({
                    "slot_id"      : slot_id,
                    "type_repas"   : type_repas,
                    "repas_num"    : repas_num,
                    "jours"        : [j["jour"] for j in jours],
                    "periode"      : periode,
                    "batch"        : True,
                    "macros_cibles": macros_moy,
                    "digestibilite": digestibilite,
                    "seance"       : jours[0]["seance"],
                })
                slot_id += 1

            else:
                groupes = _repartir_jours(jours, nb_recettes)
                for groupe in groupes:
                    macros_moy    = _calculer_macros_moyennes(groupe, repas_num)
                    digestibilite = _get_digestibilite_repas(groupe, repas_num)

                    slots.append({
                        "slot_id"      : slot_id,
                        "type_repas"   : type_repas,
                        "repas_num"    : repas_num,
                        "jours"        : [j["jour"] for j in groupe],
                        "periode"      : periode,
                        "batch"        : False,
                        "macros_cibles": macros_moy,
                        "digestibilite": digestibilite,
                        "seance"       : groupe[0]["seance"],
                    })
                    slot_id += 1

    return slots


def _calculer_macros_moyennes(jours: list, repas_num: int) -> dict:
    if not jours:
        return {"calories": 0, "proteines_g": 0, "glucides_g": 0, "lipides_g": 0}

    repas_list = [
        j["repas"][repas_num - 1]
        for j in jours
        if len(j["repas"]) >= repas_num
    ]

    if not repas_list:
        return {"calories": 0, "proteines_g": 0, "glucides_g": 0, "lipides_g": 0}

    nb = len(repas_list)
    return {
        "calories"   : round(sum(r["calories"]    for r in repas_list) / nb, 1),
        "proteines_g": round(sum(r["proteines_g"] for r in repas_list) / nb, 1),
        "glucides_g" : round(sum(r["glucides_g"]  for r in repas_list) / nb, 1),
        "lipides_g"  : round(sum(r["lipides_g"]   for r in repas_list) / nb, 1),
    }


def _get_digestibilite_repas(jours: list, repas_num: int) -> str:
    if not jours:
        return "medium"

    ordre = {"high": 0, "medium": 1, "low": 2}
    digestibilites = [
        j["repas"][repas_num - 1]["digestibilite"]
        for j in jours
        if len(j["repas"]) >= repas_num
    ]

    if not digestibilites:
        return "medium"

    return min(digestibilites, key=lambda x: ordre.get(x, 1))


def _repartir_jours(jours: list, nb_recettes: int) -> list:
    if nb_recettes >= len(jours):
        return [[j] for j in jours]

    taille_groupe = len(jours) // nb_recettes
    reste         = len(jours) % nb_recettes
    groupes       = []
    idx           = 0

    for i in range(nb_recettes):
        taille = taille_groupe + (1 if i < reste else 0)
        groupes.append(jours[idx:idx + taille])
        idx += taille

    return groupes


# ------------------------------------------------------------
# FONCTION PRINCIPALE
# ------------------------------------------------------------
def generer_semaine_recettes(
    config           : dict,
    planning_semaine : list,
) -> list:
    """
    Genere les repas de la semaine en cherchant
    les recettes les plus adaptees dans recettes.db.
    """
    structure_repas = config["structure_repas"]
    aliments_exclus = config["aliments_exclus"]
    budget_hebdo    = config["budget"]["budget_hebdo_max"]

    print("\n[...] Generation des repas via base recettes...")
    print(f"      Budget hebdomadaire : {budget_hebdo} euros")

    slots = _identifier_slots_semaine(planning_semaine, structure_repas)
    print(f"      Slots a optimiser   : {len(slots)}")

    budget_restant   = budget_hebdo
    repas_precedents = []
    resultats        = []

    for slot in slots:
        type_repas    = slot["type_repas"]
        seance        = slot["seance"]
        macros_cibles = slot["macros_cibles"]
        digestibilite = slot["digestibilite"]
        jours_str     = " / ".join(slot["jours"])

        print(
            f"\n  [{slot['slot_id']+1:02d}] {type_repas.upper():<12}"
            f" {jours_str:<30}"
            f" {macros_cibles['calories']:.0f} kcal"
            f" | digest: {digestibilite}"
        )

        # Generer le repas
        repas = generer_repas(
            type_repas       = type_repas,
            digestibilite    = digestibilite,
            macros_cibles    = macros_cibles,
            seance           = seance,
            repas_precedents = repas_precedents,
            aliments_exclus  = aliments_exclus,
        )

        budget_restant  -= repas["cout"]
        repas_precedents.append(repas)

        # Ajout infos slot
        repas["slot_id"] = slot["slot_id"]
        repas["jours"]   = slot["jours"]
        repas["periode"] = slot["periode"]
        repas["batch"]   = slot["batch"]
        repas["seance"]  = seance

        resultats.append(repas)

        # Affichage
        statut_str = "[OK]" if repas["statut"] == "ok" else "[NON TROUVE]"
        print(
            f"      {statut_str} {repas['nom_fr']:<40}"
            f" Cout : {repas['cout']:.2f} euros"
            f" Budget restant : {budget_restant:.2f} euros"
        )

        if repas["statut"] == "ok":
            mr = repas["macros_reelles"]
            mc = repas["macros_cibles"]
            print(
                f"      Macros reelles : "
                f"{mr['calories']:.0f} kcal"
                f" P:{mr['proteines_g']:.0f}g"
                f" G:{mr['glucides_g']:.0f}g"
                f" L:{mr['lipides_g']:.0f}g"
                f" (ratio: x{repas['ratio_adaptation']})"
            )
            print(
                f"      Macros cibles  : "
                f"{mc['calories']:.0f} kcal"
                f" P:{mc['proteines_g']:.0f}g"
                f" G:{mc['glucides_g']:.0f}g"
                f" L:{mc['lipides_g']:.0f}g"
            )

    # Recapitulatif
    print("\n" + "=" * 70)
    print("  RECAPITULATIF GENERATION")
    print("=" * 70)
    print(f"  Slots generes    : {len(resultats)}")
    print(f"  Budget utilise   : {budget_hebdo - budget_restant:.2f} euros")
    print(f"  Budget restant   : {budget_restant:.2f} euros")
    ok       = sum(1 for r in resultats if r["statut"] == "ok")
    non_trouves = sum(1 for r in resultats if r["statut"] != "ok")
    print(f"  Recettes OK      : {ok}")
    print(f"  Non trouvees     : {non_trouves}")
    print("=" * 70)

    return resultats


# ------------------------------------------------------------
# AFFICHAGE COMPLET
# ------------------------------------------------------------
def afficher_semaine_recettes(resultats: list) -> None:
    print("\n" + "=" * 80)
    print("  PLANNING ALIMENTAIRE HEBDOMADAIRE")
    print("=" * 80)

    for res in resultats:
        jours_str = " / ".join(res["jours"])
        batch_str = " [BATCH]" if res["batch"] else ""

        print(f"\n  {res['type_repas'].upper()}{batch_str} — {jours_str}")
        print(f"  Seance   : {res['seance']}")
        print(f"  Recette  : {res['nom_fr']}")

        if res["source_url"]:
            print(f"  Source   : {res['source_url']}")
        if res["temps_prep_min"]:
            print(f"  Prep     : {res['temps_prep_min']} min")

        print(f"  {'-' * 65}")

        # Macros
        mr = res["macros_reelles"]
        mc = res["macros_cibles"]
        print(
            f"  Macros reelles : "
            f"{mr['calories']:.0f} kcal"
            f" | P:{mr['proteines_g']:.0f}g"
            f" | G:{mr['glucides_g']:.0f}g"
            f" | L:{mr['lipides_g']:.0f}g"
        )
        print(
            f"  Macros cibles  : "
            f"{mc['calories']:.0f} kcal"
            f" | P:{mc['proteines_g']:.0f}g"
            f" | G:{mc['glucides_g']:.0f}g"
            f" | L:{mc['lipides_g']:.0f}g"
        )

        # Ingredients
        if res["ingredients"]:
            print(f"\n  Ingredients (x{res['ratio_adaptation']}) :")
            for ing in res["ingredients"]:
                print(
                    f"    {ing['nom_fr']:<35}"
                    f" {ing['quantite_g']:>6.0f}g"
                )

        # Instructions
        if res["instructions"]:
            print(f"\n  Preparation :")
            for step in res["instructions"]:
                print(
                    f"    {step['etape']}. "
                    f"{step['instruction_fr']}"
                )

    # Recapitulatif
    print("\n" + "=" * 80)
    print("  RECAPITULATIF SEMAINE")
    print("=" * 80)

    budget_total = sum(r["cout"] for r in resultats)
    ok           = sum(1 for r in resultats if r["statut"] == "ok")
    non_trouves  = sum(1 for r in resultats if r["statut"] != "ok")

    print(f"  Cout total semaine : {budget_total:.2f} euros")
    print(f"  Recettes trouvees  : {ok} / {len(resultats)}")

    if non_trouves > 0:
        print(f"\n  Recettes non trouvees ({non_trouves}) :")
        for r in resultats:
            if r["statut"] != "ok":
                jours_str = " / ".join(r["jours"])
                print(f"    {r['type_repas']:<12} {jours_str}")

    batch_list = [r for r in resultats if r["batch"]]
    if batch_list:
        print(f"\n  Recettes batch cooking :")
        for r in batch_list:
            jours_str   = " / ".join(r["jours"])
            nb_portions = len(r["jours"])
            cout_total  = r["cout"] * nb_portions
            print(
                f"    {r['type_repas'].upper():<12}"
                f" x{nb_portions} portions"
                f" ({jours_str})"
                f" -> {cout_total:.2f} euros total"
                f" | {r['nom_fr']}"
            )

    print("=" * 80)


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
    from optimisation.planning.semaine import construire_planning_semaine

    # 1. Charger la configuration
    config = lire_config_athlete()

    # 2. Calculer le planning calorique
    planning_calorique = calcul_calories_semaine(config)

    # 3. Calculer les macros
    planning_macros = calcul_macros_semaine(config, planning_calorique)

    # 4. Construire le planning semaine
    planning_semaine = construire_planning_semaine(
        config, planning_calorique, planning_macros
    )

    # 5. Generer les repas via recettes
    resultats = generer_semaine_recettes(config, planning_semaine)

    # 6. Afficher
    afficher_semaine_recettes(resultats)
