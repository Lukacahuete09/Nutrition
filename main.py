# ============================================================
# APP — SYSTÈME NUTRITION SPORTIVE
# ============================================================

import sys
import sqlite3
import logging
import argparse
from datetime import datetime
sys.dont_write_bytecode = True

# ------------------------------------------------------------
# IMPORT CONFIG 
# ------------------------------------------------------------
from config import (
    ROOT_DIR, DATA_DIR, SUIVI_DIR, OUTPUT_DIR, OPTIM_DIR,
    NUTRITION_DB, RECETTES_DB,
    CIQUAL_LOCAL, SUIVI_POIDS_XLSX, EXCEL_CONFIG_PATH,
    SPOONACULAR_KEY, PILOTERR_API_KEY,
    MAGASIN_FALLBACK, CACHE_PRIX_JOURS,
    NB_REPAS_SEMAINE, NB_REPAS_PAR_JOUR, NB_JOURS_SEMAINE,
    PROTEINES_MIN_PAR_KG, PROTEINES_MAX_PAR_KG,
    LIPIDES_MIN_PAR_KG, BUDGET_JOURNALIER_MAX,
    NB_SEMAINES_HISTORIQUE_PRIX,
    NB_RECETTES_PETIT_DEJ, NB_RECETTES_DEJEUNER,
    NB_RECETTES_DINER, LANGUE_CIBLE,
)

# ------------------------------------------------------------
# IMPORTS MODULES 
# ------------------------------------------------------------
from optimisation.excel.reader            import lire_config_athlete
from optimisation.engine.calories         import calcul_calories_semaine
from optimisation.engine.macros           import calcul_macros_semaine
from optimisation.planning.semaine        import construire_planning_semaine
from optimisation.engine.recipe_optimizer import (
    generer_semaine_recettes,
    afficher_semaine_recettes,
)
from optimisation.excel.writer            import ecrire_resultats_excel
from suivi.prix.pipeline_prix             import lancer_pipeline_prix
from suivi.tracking.poids                 import analyser_poids, afficher_analyse_poids
from suivi.tracking.adaptation            import adapter_parametres
from create_db.database.connection        import get_connection
from create_db.database.create_tables     import create_tables
from create_db.database.categories        import insert_categories
from create_db.importers.ciqual_parser    import parse_ciqual
from create_db.importers.inserter         import insert_aliments, print_repartition
from create_db.engine.scoring             import update_scores
from create_db.recettes.create_recettes_db   import create_recettes_tables
from create_db.recettes.spoonacular_importer import importer_toutes_recettes

# ------------------------------------------------------------
# LOGGING GLOBAL
# ------------------------------------------------------------
logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [logging.StreamHandler()]
)
log = logging.getLogger(__name__)


# ============================================================
# COMMANDES
# ============================================================

# ------------------------------------------------------------
# 1. INIT-DB
# ------------------------------------------------------------
def cmd_init_db(force: bool = False):
    if NUTRITION_DB.exists() and not force:
        log.info(f"[SKIP] {NUTRITION_DB.name} déjà existante.")
        log.info("       Utilisez --force pour recréer.")
        return

    log.info("=" * 60)
    log.info("  CRÉATION BASE DE DONNÉES ALIMENTAIRE")
    log.info(f"  Source : {CIQUAL_LOCAL}")
    log.info(f"  Cible  : {NUTRITION_DB}")
    log.info("=" * 60)

    if not CIQUAL_LOCAL.exists():
        log.error(f"Fichier CIQUAL introuvable : {CIQUAL_LOCAL}")
        log.info(f"Placez le fichier dans : {DATA_DIR}")
        return

    conn = get_connection()
    create_tables(conn)
    insert_categories(conn)

    log.info("Parsing CIQUAL en cours...")
    df = parse_ciqual()
    insert_aliments(conn, df)
    update_scores(conn)

    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM aliments")
    total = cursor.fetchone()["total"]
    log.info(f"Base créée : {total} aliments dans {NUTRITION_DB.name}")
    print_repartition(conn)
    conn.close()

    log.info("Base alimentaire créée.")


# ------------------------------------------------------------
# 2. IMPORT-RECETTES
# ------------------------------------------------------------
def cmd_import_recettes(force: bool = False):
    if RECETTES_DB.exists() and not force:
        conn_check = sqlite3.connect(RECETTES_DB)
        cursor     = conn_check.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM recettes")
            nb = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            nb = 0
        finally:
            conn_check.close()

        if nb > 0:
            log.info(f"[SKIP] {RECETTES_DB.name} déjà peuplée ({nb} recettes).")
            log.info("       Utilisez --force pour réimporter.")
            return

    log.info("=" * 60)
    log.info("  CRÉATION BASE DE DONNÉES RECETTES")
    log.info(f"  Cible       : {RECETTES_DB}")
    log.info(f"  Langue      : {LANGUE_CIBLE}")
    log.info(f"  Petit-déj   : {NB_RECETTES_PETIT_DEJ} recettes")
    log.info(f"  Déjeuner    : {NB_RECETTES_DEJEUNER} recettes")
    log.info(f"  Dîner       : {NB_RECETTES_DINER} recettes")
    log.info(f"  Total cible : {NB_RECETTES_PETIT_DEJ + NB_RECETTES_DEJEUNER + NB_RECETTES_DINER} recettes")
    log.info("=" * 60)

    if not SPOONACULAR_KEY:
        log.error("Clé API Spoonacular manquante.")
        log.info("Définissez SPOONACULAR_KEY dans votre environnement.")
        return

    RECETTES_DB.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(RECETTES_DB)
    conn.row_factory = sqlite3.Row
    create_recettes_tables(conn)
    importer_toutes_recettes(conn)
    conn.close()

    log.info("Base recettes créée.")


# ------------------------------------------------------------
# 3. OPTIMISE
# ------------------------------------------------------------
def cmd_optimise():
    log.info("=" * 60)
    log.info("  OPTIMISATION PLANNING HEBDOMADAIRE")
    log.info(f"  Config athlète  : {EXCEL_CONFIG_PATH.name}")
    log.info(f"  Repas / semaine : {NB_REPAS_SEMAINE} ({NB_REPAS_PAR_JOUR}/j × {NB_JOURS_SEMAINE}j)")
    log.info(f"  Protéines       : {PROTEINES_MIN_PAR_KG}–{PROTEINES_MAX_PAR_KG} g/kg/j")
    log.info(f"  Lipides min     : {LIPIDES_MIN_PAR_KG} g/kg/j")
    log.info(f"  Budget max/j    : {BUDGET_JOURNALIER_MAX} €")
    log.info(f"  Output          : {OUTPUT_DIR}")
    log.info("=" * 60)

    if not EXCEL_CONFIG_PATH.exists():
        log.error(f"Config athlète introuvable : {EXCEL_CONFIG_PATH}")
        log.info(f"Placez le fichier dans : {OPTIM_DIR}")
        return

    if not NUTRITION_DB.exists():
        log.error(f"{NUTRITION_DB.name} introuvable.")
        log.info("Lancez d'abord : python main.py init-db")
        return

    if not RECETTES_DB.exists():
        log.error(f"{RECETTES_DB.name} introuvable.")
        log.info("Lancez d'abord : python main.py import-recettes")
        return

    log.info("[1/5] Lecture configuration athlète...")
    config = lire_config_athlete()

    log.info("[2/5] Calcul calories...")
    planning_calorique = calcul_calories_semaine(config)

    log.info("[3/5] Calcul macros...")
    planning_macros = calcul_macros_semaine(config, planning_calorique)

    log.info("[4/5] Construction planning semaine...")
    planning_semaine = construire_planning_semaine(
        config, planning_calorique, planning_macros
    )

    log.info("[5/5] Génération des repas...")
    resultats = generer_semaine_recettes(config, planning_semaine)

    afficher_semaine_recettes(resultats)

    log.info("Export Excel...")
    ecrire_resultats_excel(resultats, config, planning_semaine)

    ok          = sum(1 for r in resultats if r["statut"] == "ok")
    non_trouves = sum(1 for r in resultats if r["statut"] != "ok")
    log.info(f"Planning généré — {ok}/{len(resultats)} recettes trouvées")
    if non_trouves > 0:
        log.warning(f"   {non_trouves} recettes non trouvées")
    log.info(f"Export dans {OUTPUT_DIR}")


# ------------------------------------------------------------
# 4. PRIX
# ------------------------------------------------------------
def cmd_prix(magasin: str = None):
    if magasin is None:
        try:
            config  = lire_config_athlete()
            magasin = config["budget"]["magasin"]
            log.info(f"  Magasin lu depuis Excel : {magasin.upper()}")
        except Exception as e:
            log.warning(f"Impossible de lire le magasin depuis Excel : {e}")
            magasin = MAGASIN_FALLBACK

    log.info("=" * 60)
    log.info(f"  MISE À JOUR PRIX — {magasin.upper()}")
    log.info(f"  Cache      : {CACHE_PRIX_JOURS} jours")
    log.info(f"  Historique : {NB_SEMAINES_HISTORIQUE_PRIX} semaines")
    log.info("=" * 60)

    if not PILOTERR_API_KEY:
        log.error("Clé API Piloterr manquante.")
        log.info("Définissez PILOTERR_API_KEY dans votre environnement.")
        return

    if not NUTRITION_DB.exists():
        log.error(f"{NUTRITION_DB.name} introuvable.")
        log.info("Lancez d'abord : python main.py init-db")
        return

    if not EXCEL_CONFIG_PATH.exists():
        log.error(f"Config athlète introuvable : {EXCEL_CONFIG_PATH}")
        log.info(f"Placez le fichier dans : {OPTIM_DIR}")
        return

    lancer_pipeline_prix(magasin=magasin)
    log.info(f"Prix mis à jour pour {magasin.upper()}.")


# ------------------------------------------------------------
# 5. SUIVI
# ------------------------------------------------------------
def cmd_suivi(simulation: bool = False):
    log.info("=" * 60)
    log.info("  SUIVI DYNAMIQUE HEBDOMADAIRE")
    log.info(f"  {datetime.now().strftime('%A %d/%m/%Y %H:%M')}")
    log.info(f"  Config athlète : {EXCEL_CONFIG_PATH.name}")
    log.info(f"  Suivi poids    : {SUIVI_POIDS_XLSX.name}")
    log.info(f"  Mode           : {'SIMULATION' if simulation else 'PRODUCTION'}")
    log.info("=" * 60)

    rapport = {
        "date"          : datetime.now().strftime("%d/%m/%Y %H:%M"),
        "analyse_poids" : {},
        "adaptation"    : {},
        "statut_global" : "ok",
    }

    try:
        if not EXCEL_CONFIG_PATH.exists():
            log.error(f"Config athlète introuvable : {EXCEL_CONFIG_PATH}")
            return rapport

        if not NUTRITION_DB.exists():
            log.error(f"{NUTRITION_DB.name} introuvable.")
            return rapport

        log.info("[1/2] Lecture configuration athlète...")
        config = lire_config_athlete()
        log.info(f"      Athlète  : {config['profil']['nom']}")
        log.info(f"      Objectif : {config['profil']['objectif']}")

        log.info("[2/2] Analyse poids et adaptation...")
        analyse = analyser_poids(config)
        rapport["analyse_poids"] = {
            "statut"    : analyse["statut"],
            "message"   : analyse["message"],
            "tendances" : analyse.get("tendances", {}),
            "projection": analyse.get("projection", {}),
        }
        afficher_analyse_poids(analyse)

        adaptation = adapter_parametres(
            analyse_poids = analyse,
            config        = config,
            appliquer     = not simulation,
        )
        rapport["adaptation"] = {
            "statut"           : adaptation["statut"],
            "ajustements"      : adaptation["ajustements_appliques"],
            "aucun_ajustement" : adaptation["aucun_ajustement"],
            "applique"         : adaptation.get("applique", False),
        }

        log.info("=" * 60)
        log.info("  RAPPORT SUIVI")
        log.info("=" * 60)
        log.info(f"  Statut poids : {rapport['analyse_poids']['statut'].upper()}")
        log.info(f"  Ajustements  : {len(rapport['adaptation']['ajustements'])}")
        log.info(f"  Appliqués    : {'Oui' if rapport['adaptation']['applique'] else 'Non'}")

        if rapport["adaptation"]["ajustements"]:
            log.info("\n  Ajustements effectués :")
            for ajust in rapport["adaptation"]["ajustements"]:
                log.info(f"    -> {ajust}")

        log.info("=" * 60)

    except Exception as e:
        log.error(f"ERREUR suivi : {e}", exc_info=True)
        rapport["statut_global"] = "erreur"
        rapport["erreur"]        = str(e)

    return rapport


# ------------------------------------------------------------
# 6. RUN — Pipeline complet hebdomadaire
# ------------------------------------------------------------
def cmd_run(magasin: str = None, simulation: bool = False):
    try:
        config  = lire_config_athlete()
        magasin = magasin or config["budget"]["magasin"]
    except Exception as e:
        log.warning(f"Impossible de lire Excel : {e}")
        magasin = magasin or MAGASIN_FALLBACK

    log.info("=" * 60)
    log.info("  PIPELINE COMPLET HEBDOMADAIRE")
    log.info(f"  {datetime.now().strftime('%A %d/%m/%Y %H:%M')}")
    log.info(f"  Magasin  : {magasin.upper()}")
    log.info(f"  Mode     : {'SIMULATION' if simulation else 'PRODUCTION'}")
    log.info(f"  Output   : {OUTPUT_DIR}")
    log.info("=" * 60)

    if not NUTRITION_DB.exists():
        log.error(f"{NUTRITION_DB.name} introuvable.")
        log.info("Lancez d'abord : python main.py init-db")
        return

    if not RECETTES_DB.exists():
        log.error(f"{RECETTES_DB.name} introuvable.")
        log.info("Lancez d'abord : python main.py import-recettes")
        return

    if not EXCEL_CONFIG_PATH.exists():
        log.error(f"Config athlète introuvable : {EXCEL_CONFIG_PATH.name}")
        log.info(f"Placez le fichier dans : {OPTIM_DIR}")
        return

    log.info("\n[ÉTAPE 1/3] Suivi poids & adaptation...")
    cmd_suivi(simulation=simulation)

    log.info("\n[ÉTAPE 2/3] Récupération des prix...")
    cmd_prix(magasin=magasin)

    log.info("\n[ÉTAPE 3/3] Optimisation + export Excel...")
    cmd_optimise()

    log.info(f"\nPipeline terminé — Rapport dans {OUTPUT_DIR}")


# ============================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description     = "Système de Nutrition Sportive Optimisée",
        formatter_class = argparse.RawTextHelpFormatter,
        epilog          = f"""
Chemins actifs (config.py) :
  nutrition.db   : {NUTRITION_DB}
  recettes.db    : {RECETTES_DB}
  athlete_config : {EXCEL_CONFIG_PATH}
  output         : {OUTPUT_DIR}
        """
    )

    subparsers = parser.add_subparsers(
        dest  = "commande",
        title = "Commandes disponibles",
    )

    # --- init-db ---
    p_init = subparsers.add_parser(
        "init-db",
        help="Crée nutrition.db depuis CIQUAL (skip si existe)"
    )
    p_init.add_argument(
        "--force",
        action  = "store_true",
        default = False,
        help    = "Force la recréation de nutrition.db"
    )

    # --- import-recettes ---
    p_recettes = subparsers.add_parser(
        "import-recettes",
        help="Importe les recettes Spoonacular (skip si peuplée)"
    )
    p_recettes.add_argument(
        "--force",
        action  = "store_true",
        default = False,
        help    = "Force la réimportation de recettes.db"
    )

    # --- optimise ---
    subparsers.add_parser(
        "optimise",
        help=f"Génère {NB_REPAS_SEMAINE} repas via PuLP ({NB_REPAS_PAR_JOUR}/j × {NB_JOURS_SEMAINE}j)"
    )

    # --- prix ---
    p_prix = subparsers.add_parser(
        "prix",
        help=f"Récupère les prix via Piloterr (cache {CACHE_PRIX_JOURS}j)"
    )
    p_prix.add_argument(
        "--magasin",
        choices = ["leclerc", "auchan"],
        default = None,
        help    = "Override magasin Excel"
    )

    # --- suivi ---
    p_suivi = subparsers.add_parser(
        "suivi",
        help=f"Analyse poids + adaptation (historique {NB_SEMAINES_HISTORIQUE_PRIX} semaines)"
    )
    p_suivi.add_argument(
        "--simulation",
        action  = "store_true",
        default = False,
        help    = "Calcule sans écrire dans Excel"
    )

    # --- run ---
    p_run = subparsers.add_parser(
        "run",
        help="Pipeline complet hebdomadaire (suivi → prix → optimise)"
    )
    p_run.add_argument(
        "--magasin",
        choices = ["leclerc", "auchan"],
        default = None,
        help    = "Override magasin Excel"
    )
    p_run.add_argument(
        "--simulation",
        action  = "store_true",
        default = False,
        help    = "Mode simulation (sans écriture Excel)"
    )

    args = parser.parse_args()

    if   args.commande == "init-db":
        cmd_init_db(force=args.force)

    elif args.commande == "import-recettes":
        cmd_import_recettes(force=args.force)

    elif args.commande == "optimise":
        cmd_optimise()

    elif args.commande == "prix":
        cmd_prix(magasin=args.magasin)

    elif args.commande == "suivi":
        cmd_suivi(simulation=args.simulation)

    elif args.commande == "run":
        cmd_run(magasin=args.magasin, simulation=args.simulation)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()