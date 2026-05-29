# ============================================================
#  SYSTÈME NUTRITION SPORTIVE
# NUTRITION/main.py
# ============================================================

import sys
import logging
import argparse
from datetime import datetime
sys.dont_write_bytecode = True

# ------------------------------------------------------------
# IMPORT CONFIG 
# ------------------------------------------------------------
from config import (
    # Répertoires
    ROOT_DIR,
    LOGS_DIR,
    DATA_DIR,
    SUIVI_DIR,
    OUTPUT_DIR,
    OPTIM_DIR,

    # Bases de données
    NUTRITION_DB,
    RECETTES_DB,

    # Fichiers source
    CIQUAL_LOCAL,
    PRIX_XLSX,
    SUIVI_POIDS_XLSX,

    # Excel athlète
    EXCEL_CONFIG_PATH,

    # APIs
    SPOONACULAR_KEY,
    PILOTERR_API_KEY,

    # Magasin
    MAGASIN_DEFAUT,
    CACHE_PRIX_JOURS,

    # Nutrition
    NB_REPAS_SEMAINE,
    NB_REPAS_PAR_JOUR,
    NB_JOURS_SEMAINE,
    PROTEINES_MIN_PAR_KG,
    PROTEINES_MAX_PAR_KG,
    LIPIDES_MIN_PAR_KG,
    BUDGET_JOURNALIER_MAX,

    # Prix
    NB_SEMAINES_HISTORIQUE_PRIX,

    # Recettes
    NB_RECETTES_PETIT_DEJ,
    NB_RECETTES_DEJEUNER,
    NB_RECETTES_DINER,
    LANGUE_CIBLE,
)

# ------------------------------------------------------------
# LOGGING GLOBAL — Utilise LOGS_DIR du config
# ------------------------------------------------------------
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        logging.FileHandler(
            LOGS_DIR / f"nutrition_{datetime.now().strftime('%Y%m%d')}.log",
            encoding = "utf-8"
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


# ============================================================
# COMMANDES
# ============================================================

# ------------------------------------------------------------
# 1. INIT-DB — Création base alimentaire (CIQUAL)
# ------------------------------------------------------------
def cmd_init_db():
    """
    Crée et peuple nutrition.db depuis le fichier CIQUAL.
    DB cible     : NUTRITION_DB
    Fichier src  : CIQUAL_LOCAL
    Anciennement : create_db/main.py
    """
    log.info("=" * 60)
    log.info("  CRÉATION BASE DE DONNÉES ALIMENTAIRE")
    log.info(f"  Source  : {CIQUAL_LOCAL}")
    log.info(f"  Cible   : {NUTRITION_DB}")
    log.info("=" * 60)

    if not CIQUAL_LOCAL.exists():
        log.error(f"Fichier CIQUAL introuvable : {CIQUAL_LOCAL}")
        log.info(f"Placez le fichier dans : {DATA_DIR}")
        return

    from create_db.database.connection     import get_connection
    from create_db.database.create_tables  import create_tables
    from create_db.database.categories     import insert_categories
    from create_db.importers.ciqual_parser import parse_ciqual
    from create_db.importers.inserter      import insert_aliments, print_repartition
    from create_db.engine.scoring          import update_scores

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

    log.info("Création base de données terminée.")


# ------------------------------------------------------------
# 2. IMPORT-RECETTES — Import depuis Spoonacular
# ------------------------------------------------------------
def cmd_import_recettes():
    """
    Crée et peuple recettes.db depuis l'API Spoonacular.
    DB cible      : RECETTES_DB
    API Key       : SPOONACULAR_KEY
    Langue        : LANGUE_CIBLE
    Nb recettes   : NB_RECETTES_PETIT_DEJ / DEJEUNER / DINER
    Anciennement  : create_db/recettes/main.py
    """
    import sqlite3

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

    from create_db.recettes.create_recettes_db   import create_recettes_tables
    from create_db.recettes.spoonacular_importer import importer_toutes_recettes

    create_recettes_tables(conn)
    importer_toutes_recettes(conn)
    conn.close()

    log.info("Base recettes terminée.")


# ------------------------------------------------------------
# 3. OPTIMISE — Génération du planning hebdomadaire
# ------------------------------------------------------------
def cmd_optimise():
    """
    Lance le moteur PuLP et génère le planning de
    NB_REPAS_SEMAINE repas (NB_REPAS_PAR_JOUR x NB_JOURS_SEMAINE).
    Config athlète : EXCEL_CONFIG_PATH
    Output         : OUTPUT_DIR
    Contraintes    : PROTEINES_MIN/MAX_PAR_KG, LIPIDES_MIN_PAR_KG
                     BUDGET_JOURNALIER_MAX
    """
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
        log.error(f"Base nutrition introuvable : {NUTRITION_DB}")
        log.info("Lancez d'abord : python main.py init-db")
        return

    if not RECETTES_DB.exists():
        log.error(f"Base recettes introuvable : {RECETTES_DB}")
        log.info("Lancez d'abord : python main.py import-recettes")
        return

    from engine.recipe_optimizer import optimiser
    optimiser()

    log.info(f"Planning généré dans {OUTPUT_DIR}")


# ------------------------------------------------------------
# 4. PRIX — Mise à jour des prix depuis le magasin
# ------------------------------------------------------------
def cmd_prix(magasin: str = MAGASIN_DEFAUT):
    """
    Récupère les prix via Piloterr API.
    Magasin défaut  : MAGASIN_DEFAUT
    Cache           : CACHE_PRIX_JOURS jours
    Historique      : NB_SEMAINES_HISTORIQUE_PRIX semaines
    """
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
        log.error(f"Base nutrition introuvable : {NUTRITION_DB}")
        log.info("Lancez d'abord : python main.py init-db")
        return

    from suivi.prix.pipeline_prix import lancer_pipeline_prix
    lancer_pipeline_prix(magasin=magasin)

    log.info(f"Prix mis à jour pour {magasin}.")


# ------------------------------------------------------------
# 5. SUIVI — Suivi poids + adaptation nutritionnelle
# ------------------------------------------------------------
def cmd_suivi(simulation: bool = False):
    """
    Analyse le suivi poids et adapte les paramètres.
    Config athlète   : EXCEL_CONFIG_PATH
    Suivi poids      : SUIVI_POIDS_XLSX
    Historique prix  : NB_SEMAINES_HISTORIQUE_PRIX semaines
    Anciennement     : suivi/main.py
    """
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
        # Vérifications préalables
        if not EXCEL_CONFIG_PATH.exists():
            log.error(f"Config athlète introuvable : {EXCEL_CONFIG_PATH}")
            return rapport

        if not NUTRITION_DB.exists():
            log.error(f"Base nutrition introuvable : {NUTRITION_DB}")
            return rapport

        # Lecture configuration athlète
        log.info("[1/2] Lecture configuration athlète...")
        from excel.reader import lire_config_athlete
        config = lire_config_athlete()
        log.info(f"      Athlète  : {config['profil']['nom']}")
        log.info(f"      Objectif : {config['profil']['objectif']}")

        # Analyse poids + adaptation
        log.info("[2/2] Analyse poids et adaptation...")
        from suivi.tracking.poids      import analyser_poids, afficher_analyse_poids
        from suivi.tracking.adaptation import adapter_parametres

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

        # Rapport final
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
def cmd_run(magasin: str = MAGASIN_DEFAUT, simulation: bool = False):
    """
    Pipeline hebdomadaire complet :
      1. Suivi poids + adaptation   (EXCEL_CONFIG_PATH)
      2. Mise à jour prix           (MAGASIN_DEFAUT / Piloterr)
      3. Optimisation planning      (NB_REPAS_SEMAINE repas)
      4. Export rapport Excel       (OUTPUT_DIR)
    """
    log.info("=" * 60)
    log.info("  🚀 PIPELINE COMPLET HEBDOMADAIRE")
    log.info(f"  {datetime.now().strftime('%A %d/%m/%Y %H:%M')}")
    log.info(f"  Magasin  : {magasin.upper()}")
    log.info(f"  Mode     : {'SIMULATION' if simulation else 'PRODUCTION'}")
    log.info(f"  Output   : {OUTPUT_DIR}")
    log.info("=" * 60)

    log.info("\n[ÉTAPE 1/4] Suivi poids & adaptation...")
    cmd_suivi(simulation=simulation)

    log.info("\n[ÉTAPE 2/4] Récupération des prix...")
    cmd_prix(magasin=magasin)

    log.info("\n[ÉTAPE 3/4] Optimisation du planning...")
    cmd_optimise()

    log.info("\n[ÉTAPE 4/4] Export rapport Excel...")
    from excel.writer import exporter_rapport
    exporter_rapport()

    log.info(f"\n Pipeline terminé — Rapport dans {OUTPUT_DIR}")


# ============================================================
# POINT D'ENTRÉE PRINCIPAL
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description     = " Système de Nutrition Sportive Optimisée",
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
    subparsers.add_parser(
        "init-db",
        help=f"Crée nutrition.db depuis CIQUAL ({DATA_DIR.name}/)"
    )

    # --- import-recettes ---
    subparsers.add_parser(
        "import-recettes",
        help=f"Importe {NB_RECETTES_PETIT_DEJ + NB_RECETTES_DEJEUNER + NB_RECETTES_DINER} recettes Spoonacular → recettes.db"
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
        default = MAGASIN_DEFAUT,
        help    = f"Magasin cible (défaut: {MAGASIN_DEFAUT})"
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
        help="Pipeline complet : suivi → prix → optimise → export"
    )
    p_run.add_argument(
        "--magasin",
        choices = ["leclerc", "auchan"],
        default = MAGASIN_DEFAUT,
        help    = f"Magasin cible (défaut: {MAGASIN_DEFAUT})"
    )
    p_run.add_argument(
        "--simulation",
        action  = "store_true",
        default = False,
        help    = "Mode simulation (sans écriture Excel)"
    )

    args = parser.parse_args()

    if   args.commande == "init-db":
        cmd_init_db()

    elif args.commande == "import-recettes":
        cmd_import_recettes()

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
