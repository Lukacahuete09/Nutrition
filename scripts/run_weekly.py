# ============================================================
# SCRIPT HEBDOMADAIRE AUTOMATIQUE
# scripts/run_weekly.py
#
# Lance tous les dimanches a 15h par le scheduler Windows
# Lit la config depuis athlete_config.xlsx
# Ecrit les resultats dans les memes feuilles Excel
# ============================================================

import sys
import os
import logging
from datetime import datetime
sys.dont_write_bytecode = True

# Logging
LOG_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        logging.FileHandler(
            os.path.join(LOG_DIR, f"run_{datetime.now().strftime('%Y%m%d')}.log"),
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)


def main():
    log.info("=" * 60)
    log.info("  LANCEMENT HEBDOMADAIRE AUTOMATIQUE")
    log.info(f"  {datetime.now().strftime('%A %d/%m/%Y %H:%M')}")
    log.info("=" * 60)

    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    ))

    try:
        # 1. Lire la configuration athlete
        log.info("[1/6] Lecture configuration athlete...")
        from optimisation.excel.reader import lire_config_athlete
        config = lire_config_athlete()
        log.info(f"      Athlete : {config['profil']['nom']}")
        log.info(f"      Poids   : {config['profil']['poids_actuel_kg']} kg")

        # 2. Calculer le planning calorique
        log.info("[2/6] Calcul calories...")
        from optimisation.engine.calories import calcul_calories_semaine
        planning_calorique = calcul_calories_semaine(config)

        # 3. Calculer les macros
        log.info("[3/6] Calcul macros...")
        from optimisation.engine.macros import calcul_macros_semaine
        planning_macros = calcul_macros_semaine(config, planning_calorique)

        # 4. Construire le planning semaine
        log.info("[4/6] Construction planning semaine...")
        from optimisation.planning.semaine import construire_planning_semaine
        planning_semaine = construire_planning_semaine(
            config, planning_calorique, planning_macros
        )

        # 5. Generer les repas via recettes
        log.info("[5/6] Generation des repas...")
        from optimisation.engine.recipe_optimizer import generer_semaine_recettes
        resultats = generer_semaine_recettes(config, planning_semaine)

        ok          = sum(1 for r in resultats if r["statut"] == "ok")
        non_trouves = sum(1 for r in resultats if r["statut"] != "ok")
        log.info(f"      Recettes trouvees : {ok}/{len(resultats)}")
        if non_trouves > 0:
            log.warning(f"      Recettes non trouvees : {non_trouves}")

        # 6. Ecrire les resultats dans Excel
        log.info("[6/6] Export vers Excel...")
        from optimisation.excel.writer import ecrire_resultats_excel
        ecrire_resultats_excel(resultats, config, planning_semaine)

        log.info("=" * 60)
        log.info("  EXECUTION TERMINEE AVEC SUCCES")
        log.info("=" * 60)

    except Exception as e:
        log.error(f"ERREUR : {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()