# ============================================================
# REGENERATION D UNE RECETTE SPECIFIQUE
# scripts/regenerer_repas.py
#
# Lance par la macro VBA quand l utilisateur clique
# sur le bouton Changer dans la feuille PLANNING_SEMAINE
#
# Arguments :
#   argv[1] : nom de la recette a remplacer
#   argv[2] : type de repas (petit_dej / dejeuner / diner)
#   argv[3] : jours concernes (ex: "Lundi / Mardi")
#
# Usage :
#   python scripts/regenerer_repas.py "Chicken Rice" "diner" "Lundi"
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
            os.path.join(LOG_DIR, f"regeneration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Ajouter la racine du projet au path
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
))


def main():
    # ----------------------------------------------------------
    # Lecture des arguments passes par la macro VBA
    # ----------------------------------------------------------
    if len(sys.argv) < 4:
        log.error(
            "Arguments manquants.\n"
            "Usage : python regenerer_repas.py "
            "<nom_recette> <type_repas> <jours>"
        )
        sys.exit(1)

    nom_recette_exclue = sys.argv[1]
    type_repas         = sys.argv[2]
    jours_str          = sys.argv[3]
    jours              = [j.strip() for j in jours_str.split("/")]

    log.info("=" * 60)
    log.info("  REGENERATION D UNE RECETTE")
    log.info("=" * 60)
    log.info(f"  Recette exclue : {nom_recette_exclue}")
    log.info(f"  Type repas     : {type_repas}")
    log.info(f"  Jours          : {jours}")

    try:
        # ----------------------------------------------------------
        # 1. Lire la configuration athlete
        # ----------------------------------------------------------
        log.info("[1/5] Lecture configuration athlete...")
        from optimisation.excel.reader import lire_config_athlete
        config = lire_config_athlete()

        # ----------------------------------------------------------
        # 2. Calculer les macros cibles pour ce repas
        # ----------------------------------------------------------
        log.info("[2/5] Calcul des macros cibles...")
        from optimisation.engine.calories  import calcul_calories_semaine
        from optimisation.engine.macros    import calcul_macros_semaine
        from optimisation.planning.semaine import construire_planning_semaine

        planning_calorique = calcul_calories_semaine(config)
        planning_macros    = calcul_macros_semaine(config, planning_calorique)
        planning_semaine   = construire_planning_semaine(
            config, planning_calorique, planning_macros
        )

        # Trouver les macros du repas concerne
        macros_cibles  = None
        digestibilite  = "medium"
        seance         = "Repos"

        for jour in planning_semaine:
            if jour["jour"] in jours:
                repas_num = {
                    "petit_dej" : 0,
                    "dejeuner"  : 1,
                    "diner"     : 2,
                }.get(type_repas, 2)

                if len(jour["repas"]) > repas_num:
                    repas        = jour["repas"][repas_num]
                    macros_cibles = {
                        "calories"   : repas["calories"],
                        "proteines_g": repas["proteines_g"],
                        "glucides_g" : repas["glucides_g"],
                        "lipides_g"  : repas["lipides_g"],
                    }
                    digestibilite = repas["digestibilite"]
                    seance        = jour["seance"]
                    break

        if macros_cibles is None:
            log.error(f"Impossible de trouver les macros pour {jours} / {type_repas}")
            sys.exit(1)

        log.info(
            f"     Macros cibles : "
            f"{macros_cibles['calories']:.0f} kcal "
            f"P:{macros_cibles['proteines_g']:.0f}g "
            f"G:{macros_cibles['glucides_g']:.0f}g "
            f"L:{macros_cibles['lipides_g']:.0f}g"
        )

        # ----------------------------------------------------------
        # 3. Lire les recettes deja utilisees cette semaine
        #    + ajouter la recette exclue
        # ----------------------------------------------------------
        log.info("[3/5] Preparation des exclusions...")
        from optimisation.excel.reader import lire_config_athlete

        # Re-lire pour avoir les recettes exclues a jour
        config = lire_config_athlete()
        recettes_exclues_utilisateur = config.get("recettes_exclues", [])

        # Ajouter la recette qu on veut remplacer
        recettes_exclues_utilisateur.append({
            "nom"    : nom_recette_exclue,
            "raison" : "N aime pas",
        })

        # Simuler les repas precedents pour la diversite
        repas_precedents = [
            {"nom_fr": r["nom"]}
            for r in recettes_exclues_utilisateur
        ]

        # ----------------------------------------------------------
        # 4. Generer une nouvelle recette
        # ----------------------------------------------------------
        log.info("[4/5] Generation nouvelle recette...")
        from optimisation.engine.recipe_optimizer import generer_repas

        nouveau_repas = generer_repas(
            type_repas          = type_repas,
            digestibilite       = digestibilite,
            macros_cibles       = macros_cibles,
            seance              = seance,
            repas_precedents    = repas_precedents,
            aliments_exclus     = config.get("aliments_exclus", []),
        )

        if nouveau_repas["statut"] != "ok":
            log.error(f"Aucune recette alternative trouvee pour {type_repas}")
            sys.exit(1)

        log.info(f"     Nouvelle recette : {nouveau_repas['nom_fr']}")
        log.info(
            f"     Macros reelles  : "
            f"{nouveau_repas['macros_reelles']['calories']:.0f} kcal "
            f"P:{nouveau_repas['macros_reelles']['proteines_g']:.0f}g"
        )

        # ----------------------------------------------------------
        # 5. Mettre a jour Excel
        # ----------------------------------------------------------
        log.info("[5/5] Mise a jour du fichier Excel...")
        from optimisation.excel.writer import _mettre_a_jour_repas_excel

        _mettre_a_jour_repas_excel(
            nom_recette_exclue = nom_recette_exclue,
            nouveau_repas      = nouveau_repas,
            type_repas         = type_repas,
            jours              = jours,
        )

        log.info("=" * 60)
        log.info("  REGENERATION TERMINEE AVEC SUCCES")
        log.info(f"  Ancienne recette : {nom_recette_exclue}")
        log.info(f"  Nouvelle recette : {nouveau_repas['nom_fr']}")
        log.info("=" * 60)

    except Exception as e:
        log.error(f"ERREUR : {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
