# ============================================================
# CONFIGURATION — PHASE 3 SUIVI DYNAMIQUE
# suivi/config.py
# ============================================================

import os
import sys
sys.dont_write_bytecode = True

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# ------------------------------------------------------------
# CHEMINS DES FICHIERS
# ------------------------------------------------------------
NUTRITION_DB      = os.path.abspath(
    os.path.join(BASE_DIR, "..", "create_db", "data", "nutrition.db")
)
EXCEL_CONFIG_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "optimisation", "data", "athlete_config.xlsx")
)
PRIX_XLSX         = os.path.join(DATA_DIR,   "prix.xlsx")
SUIVI_POIDS_XLSX  = os.path.join(OUTPUT_DIR, "suivi_poids.xlsx")


# ============================================================
# PARAMETRES PAR OBJECTIF
#
# Structure de chaque objectif :
#
#   direction
#     "perte"    : objectif de reduction du poids
#     "gain"     : objectif d augmentation du poids
#     "maintien" : stabilisation du poids
#
#   perte_optimale_min_kg / perte_optimale_max_kg
#     Fourchette de variation de poids hebdomadaire
#     consideree comme optimale pour l objectif.
#     En gain de masse : represente le gain hebdomadaire cible.
#
#   seuil_stagnation_kg
#     En dessous de ce seuil de variation hebdomadaire,
#     le systeme considere qu il y a stagnation et
#     ajuste le deficit/surplus.
#
#   seuil_changement_rapide_kg
#     Au dessus de ce seuil, le changement est trop rapide
#     et risque de compromettre la masse musculaire (perte)
#     ou d accumuler trop de graisse (gain).
#
#   nb_semaines_stagnation
#     Nombre de semaines consecutives de stagnation
#     avant de declencher un ajustement automatique.
#
#   ajustement_deficit_stagnation
#     Nombre de kcal a ajouter au deficit (perte)
#     ou au surplus (gain) en cas de stagnation.
#
#   ajustement_deficit_rapide
#     Nombre de kcal a retirer au deficit (perte)
#     ou au surplus (gain) si changement trop rapide.
#
#   ajustement_glucides_stagnation
#     Ratio d ajustement des glucides en cas de stagnation.
#     Negatif = reduire, positif = augmenter.
#
#   ajustement_glucides_rapide
#     Ratio d ajustement des glucides si changement trop rapide.
#
#   deficit_min_absolu / deficit_max_absolu
#     Bornes absolues du deficit calorique.
#     Le systeme ne depassera jamais ces valeurs
#     meme si l ajustement le suggere.
#
#   surplus_min_absolu / surplus_max_absolu
#     Bornes absolues du surplus calorique (prise de masse).
# ============================================================

PARAMETRES_PAR_OBJECTIF = {

    # ----------------------------------------------------------
    # RECOMPOSITION
    #
    # Definition :
    #   Perdre de la graisse et maintenir ou gagner du muscle
    #   simultanement. Possible chez les athletes entraines
    #   et en retour apres blessure (sensibilite anabolique
    #   elevee).
    #
    # Taux de perte optimal : 0.3 - 0.7 kg/semaine
    #   Source : Barakat et al. 2020
    #   "Recomposition corporelle : les athletes entraines
    #    peuvent-ils construire du muscle et perdre de la
    #    graisse simultanement ?"
    #   Strength and Conditioning Journal
    #   "Un deficit de 200-500 kcal/jour permet une perte
    #    de graisse et une preservation musculaire simultanees
    #    a raison de 0.3-0.7 kg/semaine"
    #
    # Seuil changement trop rapide : 1.0 kg/semaine
    #   Source : Helms et al. 2014
    #   "Recommandations fondees sur les preuves pour la
    #    preparation a la competition en culturisme naturel"
    #   Journal of the International Society of Sports Nutrition
    #   "Une perte de poids depassant 1% du poids corporel
    #    par semaine augmente significativement le risque
    #    de perte de masse musculaire"
    #   -> 1% x 80kg = 0.8kg -> arrondi securise a 1.0kg
    #
    # Deficit maximum : 500 kcal
    #   Source : Hall et al. 2012
    #   "Quantification de l effet du desequilibre energetique
    #    sur le poids corporel" — The Lancet
    #   "Des deficits superieurs a 500 kcal/jour chez les
    #    athletes compromettent la performance a l entrainement
    #    et la synthese proteique musculaire"
    #
    # Ajustement glucides : 10%
    #   Source : Burke et al. 2011
    #   "Les glucides pour l entrainement et la competition"
    #   Journal of Sports Sciences
    #   "La periodisation glucidique permet des ajustements
    #    de 10-15% sans compromettre la qualite
    #    de l entrainement"
    # ----------------------------------------------------------
    "recomposition" : {
        "direction"                      : "perte",
        "perte_optimale_min_kg"          :  0.3,
        "perte_optimale_max_kg"          :  0.7,
        "seuil_stagnation_kg"            :  0.1,
        "seuil_changement_rapide_kg"     :  1.0,
        "nb_semaines_stagnation"         :  2,
        "ajustement_deficit_stagnation"  :  100,
        "ajustement_deficit_rapide"      :  100,
        "ajustement_glucides_stagnation" : -0.10,
        "ajustement_glucides_rapide"     :  0.10,
        "deficit_min_absolu"             :    0,
        "deficit_max_absolu"             :  500,
        "surplus_min_absolu"             :    0,
        "surplus_max_absolu"             :    0,
    },

    # ----------------------------------------------------------
    # PERTE DE POIDS
    #
    # Definition :
    #   Reduction prioritaire de la masse grasse.
    #   Deficit plus agressif que la recomposition.
    #
    # Taux de perte optimal : 0.5 - 1.0 kg/semaine
    #   Source : Garthe et al. 2011
    #   "Effet de deux vitesses de perte de poids differentes
    #    sur la composition corporelle et les performances
    #    de force et de puissance chez les athletes de haut
    #    niveau"
    #   International Journal of Sport Nutrition and
    #   Exercise Metabolism
    #   "Une perte de poids lente (0.5-1.0 kg/semaine) preserve
    #    mieux la masse maigre qu une perte rapide chez les
    #    athletes de competition"
    #
    # Seuil changement trop rapide : 1.5 kg/semaine
    #   Source : Mero et al. 2010
    #   "Apport en proteines et maintien de la masse musculaire
    #    lors d une restriction calorique chez les athletes"
    #   "Au dela de 1.5 kg/semaine, la perte de masse maigre
    #    devient significative independamment de l apport
    #    proteique"
    #
    # Deficit minimum : 200 kcal / Deficit maximum : 750 kcal
    #   Source : Helms et al. 2014
    #   "Un deficit minimum de 200 kcal garantit une perte
    #    de graisse constante sans adaptation metabolique"
    #   "Un maximum de 750 kcal preserve la capacite
    #    d entrainement et la masse musculaire"
    #
    # Ajustement glucides : 15%
    #   Source : Jeukendrup 2014
    #   "Vers une nutrition sportive personnalisee"
    #   Sports Medicine
    #   "Une modulation glucidique de 10-15% par semaine
    #    est la fourchette securisee pour les athletes
    #    de performance"
    # ----------------------------------------------------------
    "perte de poids" : {
        "direction"                      : "perte",
        "perte_optimale_min_kg"          :  0.5,
        "perte_optimale_max_kg"          :  1.0,
        "seuil_stagnation_kg"            :  0.2,
        "seuil_changement_rapide_kg"     :  1.5,
        "nb_semaines_stagnation"         :  2,
        "ajustement_deficit_stagnation"  :  150,
        "ajustement_deficit_rapide"      :  150,
        "ajustement_glucides_stagnation" : -0.15,
        "ajustement_glucides_rapide"     :  0.10,
        "deficit_min_absolu"             :  200,
        "deficit_max_absolu"             :  750,
        "surplus_min_absolu"             :    0,
        "surplus_max_absolu"             :    0,
    },

    # ----------------------------------------------------------
    # PRISE DE MASSE
    #
    # Definition :
    #   Gain musculaire maximal avec surplus calorique controle.
    #   Minimiser la prise de graisse associee.
    #
    # Gain optimal : 0.2 - 0.5 kg/semaine
    #   Source : Slater & Phillips 2011
    #   "Recommandations nutritionnelles pour les sports
    #    de force"
    #   Journal of Sports Sciences
    #   "Les athletes naturels peuvent synthetiser au maximum
    #    0.25-0.5 kg de masse maigre par semaine"
    #   "Gagner plus vite conduit a une accumulation excessive
    #    de graisse"
    #
    #   Source : Antonio et al. 2020
    #   Prise de position ISSN : Regimes et composition
    #   corporelle
    #   Journal of the International Society of Sports Nutrition
    #   "Un surplus calorique de 150-400 kcal/jour optimise
    #    le gain de masse maigre tout en minimisant la prise
    #    de graisse chez les individus entraines en resistance"
    #
    # Seuil gain trop rapide : 0.7 kg/semaine
    #   Source : Haff & Triplett 2016
    #   "Fondamentaux de l entrainement en force et du
    #    conditionnement physique" — NSCA
    #   "Un gain de poids depassant 0.7 kg/semaine chez les
    #    athletes suggere une accumulation excessive de graisse"
    #
    # Surplus minimum : 150 kcal / Surplus maximum : 400 kcal
    #   Source : Antonio et al. 2020 ISSN
    #   Confirme par : Slater & Phillips 2011
    # ----------------------------------------------------------
    "prise de masse" : {
        "direction"                      : "gain",
        "perte_optimale_min_kg"          :  0.2,
        "perte_optimale_max_kg"          :  0.5,
        "seuil_stagnation_kg"            :  0.1,
        "seuil_changement_rapide_kg"     :  0.7,
        "nb_semaines_stagnation"         :  2,
        "ajustement_deficit_stagnation"  :  100,
        "ajustement_deficit_rapide"      :  100,
        "ajustement_glucides_stagnation" :  0.10,
        "ajustement_glucides_rapide"     : -0.10,
        "deficit_min_absolu"             :    0,
        "deficit_max_absolu"             :    0,
        "surplus_min_absolu"             :  150,
        "surplus_max_absolu"             :  400,
    },

    # ----------------------------------------------------------
    # MAINTIEN
    #
    # Definition :
    #   Stabiliser le poids actuel tout en preservant
    #   la composition corporelle et les performances.
    #
    # Variation acceptable : -0.2 a +0.2 kg/semaine
    #   Source : Loucks et al. 2011
    #   "Disponibilite energetique chez les athletes"
    #   Journal of Sports Sciences
    #   "Une stabilite du poids dans une fourchette de
    #    +/-0.2 kg/semaine indique une disponibilite
    #    energetique adequate et un equilibre hormonal"
    #
    # Deficit maximum : 200 kcal
    #   Source : Loucks et al. 2011
    #   "Des deficits energetiques superieurs a 200 kcal/jour
    #    en phase de maintien perturbent la fonction hormonale
    #    et la recuperation"
    #
    # Nombre de semaines de stagnation : 4
    #   En maintien la stagnation est l objectif recherche.
    #   On n ajuste qu apres 4 semaines de derive significative.
    # ----------------------------------------------------------
    "maintien" : {
        "direction"                      : "maintien",
        "perte_optimale_min_kg"          : -0.2,
        "perte_optimale_max_kg"          :  0.2,
        "seuil_stagnation_kg"            :  0.0,
        "seuil_changement_rapide_kg"     :  0.5,
        "nb_semaines_stagnation"         :  4,
        "ajustement_deficit_stagnation"  :   50,
        "ajustement_deficit_rapide"      :   50,
        "ajustement_glucides_stagnation" :  0.05,
        "ajustement_glucides_rapide"     : -0.05,
        "deficit_min_absolu"             : -100,
        "deficit_max_absolu"             :  200,
        "surplus_min_absolu"             :    0,
        "surplus_max_absolu"             :  100,
    },

    # ----------------------------------------------------------
    # PERFORMANCE
    #
    # Definition :
    #   Optimiser la performance sportive sans contrainte
    #   stricte de poids. Energie maximale disponible.
    #   Le poids est secondaire par rapport aux resultats.
    #
    # Variation acceptable : -0.3 a +0.3 kg/semaine
    #   Source : Burke et al. 2011
    #   "Les glucides pour l entrainement et la competition"
    #   Journal of Sports Sciences
    #
    #   Source : Thomas et al. 2016
    #   Declaration de consensus du CIO sur la nutrition
    #   sportive — British Journal of Sports Medicine
    #   "Les athletes privilegiant la performance doivent
    #    maintenir une disponibilite energetique superieure
    #    a 40 kcal/kg de masse maigre par jour"
    #   "Des fluctuations de poids dans une fourchette de
    #    +/-0.3 kg/semaine sont acceptables en phase
    #    de performance"
    #
    # Deficit maximum : 100 kcal (quasi maintien)
    #   Source : Loucks et al. 2011
    #   "Des deficits minimaux preservent la fonction
    #    hormonale et l adaptation a l entrainement"
    #
    # Surplus maximum : 200 kcal
    #   En performance un leger surplus peut etre benefique
    #   pour la recuperation et l adaptation neuromusculaire.
    #   Source : Thomas et al. 2016 — Declaration CIO
    # ----------------------------------------------------------
    "performance" : {
        "direction"                      : "maintien",
        "perte_optimale_min_kg"          : -0.3,
        "perte_optimale_max_kg"          :  0.3,
        "seuil_stagnation_kg"            :  0.0,
        "seuil_changement_rapide_kg"     :  0.5,
        "nb_semaines_stagnation"         :  4,
        "ajustement_deficit_stagnation"  :   50,
        "ajustement_deficit_rapide"      :   50,
        "ajustement_glucides_stagnation" :  0.05,
        "ajustement_glucides_rapide"     : -0.05,
        "deficit_min_absolu"             : -200,
        "deficit_max_absolu"             :  100,
        "surplus_min_absolu"             :    0,
        "surplus_max_absolu"             :  200,
    },
}


# ------------------------------------------------------------
# FONCTION UTILITAIRE
# ------------------------------------------------------------
def get_parametres_objectif(objectif: str) -> dict:
    """
    Retourne les parametres correspondant a l objectif.
    Recherche partielle insensible a la casse.

    Exemples de correspondances :
      "Recomposition corporelle" -> "recomposition"
      "Perte de poids rapide"    -> "perte de poids"
      "Prise de masse seche"     -> "prise de masse"
      "Maintien du poids"        -> "maintien"
      "Optimisation performance" -> "performance"

    Retourne "recomposition" par defaut si objectif
    non reconnu.
    """
    objectif_lower = objectif.strip().lower()
    for key, val in PARAMETRES_PAR_OBJECTIF.items():
        if key in objectif_lower:
            return {**val, "objectif_detecte": key}

    return {
        **PARAMETRES_PAR_OBJECTIF["recomposition"],
        "objectif_detecte": "recomposition"
    }


# ------------------------------------------------------------
# PARAMETRES PRIX
# ------------------------------------------------------------

# Score minimum pour qualifier une promotion
# promo_score = (prix_moyen - prix_actuel) / prix_moyen
# Un score de 0.15 signifie une reduction de 15% par rapport
# au prix moyen historique
PROMO_SCORE_MIN = 0.15

# Nombre de semaines d historique prix a conserver en base
NB_SEMAINES_HISTORIQUE_PRIX = 12


# ------------------------------------------------------------
# CREATION DES DOSSIERS AU DEMARRAGE
# ------------------------------------------------------------
os.makedirs(DATA_DIR,   exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)