# ============================================================
# POINT D ENTREE — PHASE 3 SUIVI DYNAMIQUE
# suivi/main.py
#
# Orchestre :
#   1. Mise a jour des prix
#   2. Detection des promotions
#   3. Analyse du suivi poids
#   4. Adaptation automatique des parametres nutritionnels
# ============================================================

import sys
import os
import logging
from datetime import datetime
sys.dont_write_bytecode = True

# Logging
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        logging.FileHandler(
            os.path.join(LOG_DIR, f"suivi_{datetime.now().strftime('%Y%m%d')}.log"),
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
))


def main(appliquer_adaptation: bool = True) -> dict:
    """
    Fonction principale du suivi dynamique.

    Parametre appliquer_adaptation :
      True  -> ecrit les ajustements dans Excel (production)
      False -> calcule sans ecrire (simulation)

    Retourne un rapport complet du suivi.
    """
    log.info("=" * 60)
    log.info("  SUIVI DYNAMIQUE HEBDOMADAIRE")
    log.info(f"  {datetime.now().strftime('%A %d/%m/%Y %H:%M')}")
    log.info("=" * 60)

    rapport = {
        "date"             : datetime.now().strftime("%d/%m/%Y %H:%M"),
        "prix"             : {},
        "promotions"       : [],
        "analyse_poids"    : {},
        "adaptation"       : {},
        "statut_global"    : "ok",
    }

    try:
        # ----------------------------------------------------------
        # 1. Lire la configuration athlete
        # ----------------------------------------------------------
        log.info("[1/4] Lecture configuration athlete...")
        from optimisation.excel.reader import lire_config_athlete
        config = lire_config_athlete()
        log.info(f"      Athlete  : {config['profil']['nom']}")
        log.info(f"      Objectif : {config['profil']['objectif']}")

        # ----------------------------------------------------------
        # 2. Mise a jour des prix
        # ----------------------------------------------------------
        log.info("[2/4] Mise a jour des prix alimentaires...")
        from suivi.prix.updater import mettre_a_jour_prix

        resultats_prix = mettre_a_jour_prix()
        rapport["prix"] = {
            "nb_mis_a_jour" : len(resultats_prix),
            "nb_en_promo"   : sum(1 for r in resultats_prix if r.get("en_promo")),
        }

        if rapport["prix"]["nb_mis_a_jour"] == 0:
            log.warning(
                "Aucun prix mis a jour. "
                "Verifiez le fichier suivi/data/prix.xlsx"
            )
        else:
            log.info(f"      Prix mis a jour : {rapport['prix']['nb_mis_a_jour']}")
            log.info(f"      En promotion    : {rapport['prix']['nb_en_promo']}")

        # ----------------------------------------------------------
        # 3. Detection des promotions
        # ----------------------------------------------------------
        # log.info("[3/4] Detection des promotions...")
        # # from suivi.prix.promo_detector import (
        # #     get_promotions_semaine,
        # #     afficher_resume_promotions,
        # # )

        # promotions = get_promotions_semaine()
        # rapport["promotions"] = promotions

        # if promotions:
        #     log.info(f"      {len(promotions)} promotion(s) detectee(s) :")
        #     for p in promotions[:5]:
        #         log.info(
        #             f"        {p['nom']:<35} "
        #             f"-{p['reduction_pct']:.0f}% "
        #             f"({p['magasin']})"
        #         )
        #     afficher_resume_promotions()
        # else:
        #     log.info("      Aucune promotion cette semaine.")

        # ----------------------------------------------------------
        # 4. Analyse du suivi poids
        # ----------------------------------------------------------
        log.info("[4/4] Analyse du suivi poids et adaptation...")
        from suivi.tracking.poids       import analyser_poids, afficher_analyse_poids
        from suivi.tracking.adaptation  import adapter_parametres

        analyse = analyser_poids(config)
        rapport["analyse_poids"] = {
            "statut"    : analyse["statut"],
            "message"   : analyse["message"],
            "tendances" : analyse.get("tendances", {}),
            "projection": analyse.get("projection", {}),
        }

        afficher_analyse_poids(analyse)

        # Adapter les parametres selon le suivi poids
        adaptation = adapter_parametres(
            analyse_poids = analyse,
            config        = config,
            appliquer     = appliquer_adaptation,
        )
        rapport["adaptation"] = {
            "statut"               : adaptation["statut"],
            "ajustements"          : adaptation["ajustements_appliques"],
            "aucun_ajustement"     : adaptation["aucun_ajustement"],
            "applique"             : adaptation.get("applique", False),
        }

        # ----------------------------------------------------------
        # Rapport final
        # ----------------------------------------------------------
        log.info("\n" + "=" * 60)
        log.info("  RAPPORT SUIVI DYNAMIQUE")
        log.info("=" * 60)
        log.info(f"  Prix mis a jour  : {rapport['prix'].get('nb_mis_a_jour', 0)}")
        log.info(f"  Promotions       : {len(rapport['promotions'])}")
        log.info(f"  Statut poids     : {rapport['analyse_poids']['statut'].upper()}")
        log.info(f"  Ajustements      : {len(rapport['adaptation']['ajustements'])}")
        log.info(f"  Appliques        : {'Oui' if rapport['adaptation']['applique'] else 'Non'}")

        if rapport["adaptation"]["ajustements"]:
            log.info("\n  Ajustements effectues :")
            for ajust in rapport["adaptation"]["ajustements"]:
                log.info(f"    -> {ajust}")

        log.info("=" * 60)

    except Exception as e:
        log.error(f"ERREUR : {e}", exc_info=True)
        rapport["statut_global"] = "erreur"
        rapport["erreur"]        = str(e)

    return rapport


# ------------------------------------------------------------
# TEST AUTONOME
# ------------------------------------------------------------
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Suivi dynamique hebdomadaire"
    )
    parser.add_argument(
        "--simulation",
        action  = "store_true",
        default = False,
        help    = "Calcule sans ecrire dans Excel"
    )
    args = parser.parse_args()

    rapport = main(appliquer_adaptation=not args.simulation)

    print(f"\n[OK] Suivi termine.")
    print(f"     Statut global : {rapport['statut_global']}")

    if args.simulation:
        print(f"     Mode simulation : ajustements non appliques")
