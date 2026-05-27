# ============================================================
# DEFINITION DES TYPES DE SEANCES ET REGLES NUTRITIONNELLES
# optimisation/planning/seances.py
#
# Contexte : seances en fin d apres-midi
#            3 repas fixes : matin / midi / soir
#            pas de collation
#
# Sources scientifiques :
#   - Jeukendrup 2014 — nutrition periexercice
#     Sports Medicine, 44(S1), S25-S33
#   - Burke et al. 2011 — periodisation glucidique
#     Journal of Sports Sciences, 29(S1), S17-S27
#   - Areta et al. 2013 — timing proteique
#     Journal of Physiology, 591(9), 2319-2331
#   - Thomas et al. 2016 — IOC Consensus Statement
#     International Journal of Sport Nutrition
#   - Maughan & Burke 2012 — alimentation avant effort
#     IOC Medical Commission
#   - Gibala et al. 2006 — HIIT et nutrition
#   - ISSN Recovery Position Stand
# ============================================================

import sys
import os
import re
sys.dont_write_bytecode = True

# ------------------------------------------------------------
# REGLES NUTRITIONNELLES PAR TYPE DE SEANCE
#
# Structure des 3 repas :
#   repas_1 : Petit-dejeuner (matin)
#   repas_2 : Dejeuner (midi) — repas pre-seance indirect
#             (seance en fin apres-midi -> dejeuner = dernier
#              vrai repas avant effort)
#   repas_3 : Diner (soir) — repas post-seance
#             (30-60min apres la fin de seance)
#
# Les parts de macros sont relatives aux totaux journaliers
# calcules par macros.py
# Leur somme doit faire 1.0 par macro
#
# Source repartition :
#   Areta et al. 2013 — distribution proteique 3-4h
#   Thomas et al. 2016 — IOC nutrition periexercice
# ------------------------------------------------------------
REGLES_SEANCES = {

    # ----------------------------------------------------------
    # MUSCULATION
    # ----------------------------------------------------------
    "Musculation" : {
        "digestibilite_avant" : "medium",
        "priorite_macro"      : ["proteines", "glucides", "lipides"],
        "timing_repas" : {
            "repas_1" : {
                "nom"            : "Petit-dejeuner",
                "moment"         : "matin",
                "part_calories"  : 0.20,
                "part_proteines" : 0.25,
                "part_glucides"  : 0.25,
                "part_lipides"   : 0.30,
                "digestibilite"  : "medium",
            },
            "repas_2" : {
                "nom"            : "Dejeuner (pre-seance)",
                "moment"         : "midi",
                "part_calories"  : 0.42,
                "part_proteines" : 0.33,
                "part_glucides"  : 0.47,
                "part_lipides"   : 0.28,
                "digestibilite"  : "medium",
            },
            "repas_3" : {
                "nom"            : "Diner (post-seance)",
                "moment"         : "soir",
                "part_calories"  : 0.38,
                "part_proteines" : 0.42,
                "part_glucides"  : 0.28,
                "part_lipides"   : 0.42,
                "digestibilite"  : "medium",
            },
        },
        "notes" : (
            "Petit-dej leger (20% cal). "
            "Dejeuner = pre-seance : glucides eleves. "
            "Diner = fenetre anabolique : proteines maximales. "
            "Source : Areta et al. 2013 / ISSN Position Stand 2023."
        ),
    },

    # ----------------------------------------------------------
    # SPRINT
    # ----------------------------------------------------------
    "Sprint" : {
        "digestibilite_avant" : "high",
        "priorite_macro"      : ["glucides", "proteines", "lipides"],
        "timing_repas" : {
            "repas_1" : {
                "nom"            : "Petit-dejeuner charge",
                "moment"         : "matin",
                "part_calories"  : 0.20,
                "part_proteines" : 0.20,
                "part_glucides"  : 0.45,
                "part_lipides"   : 0.18,
                "digestibilite"  : "high",
            },
            "repas_2" : {
                "nom"            : "Dejeuner leger (pre-seance)",
                "moment"         : "midi",
                "part_calories"  : 0.42,
                "part_proteines" : 0.28,
                "part_glucides"  : 0.40,
                "part_lipides"   : 0.17,
                "digestibilite"  : "high",
            },
            "repas_3" : {
                "nom"            : "Diner (post-seance)",
                "moment"         : "soir",
                "part_calories"  : 0.38,
                "part_proteines" : 0.52,
                "part_glucides"  : 0.15,
                "part_lipides"   : 0.65,
                "digestibilite"  : "medium",
            },
        },
        "notes" : (
            "Petit-dej leger (20% cal). "
            "Digestion haute obligatoire avant sprint. "
            "Lipides tres reduits au dejeuner. "
            "Proteines elevees au diner pour recuperation nerveuse. "
            "Source : Maughan & Burke 2012 / Thomas et al. 2016."
        ),
    },

    # ----------------------------------------------------------
    # CHARIOT
    # ----------------------------------------------------------
    "Chariot" : {
        "digestibilite_avant" : "high",
        "priorite_macro"      : ["glucides", "proteines", "lipides"],
        "timing_repas" : {
            "repas_1" : {
                "nom"            : "Petit-dejeuner charge",
                "moment"         : "matin",
                "part_calories"  : 0.20,
                "part_proteines" : 0.25,
                "part_glucides"  : 0.42,
                "part_lipides"   : 0.18,
                "digestibilite"  : "high",
            },
            "repas_2" : {
                "nom"            : "Dejeuner leger (pre-seance)",
                "moment"         : "midi",
                "part_calories"  : 0.42,
                "part_proteines" : 0.28,
                "part_glucides"  : 0.38,
                "part_lipides"   : 0.17,
                "digestibilite"  : "high",
            },
            "repas_3" : {
                "nom"            : "Diner (post-seance)",
                "moment"         : "soir",
                "part_calories"  : 0.38,
                "part_proteines" : 0.47,
                "part_glucides"  : 0.20,
                "part_lipides"   : 0.65,
                "digestibilite"  : "medium",
            },
        },
        "notes" : (
            "Petit-dej leger (20% cal). "
            "Complex training force-vitesse. "
            "Memes contraintes digestives que sprint. "
            "Source : Cahill et al. 2019 / Morin & Samozino 2016."
        ),
    },

    # ----------------------------------------------------------
    # PLIOMETRIE
    # ----------------------------------------------------------
    "Pliometrie" : {
        "digestibilite_avant" : "high",
        "priorite_macro"      : ["glucides", "proteines", "lipides"],
        "timing_repas" : {
            "repas_1" : {
                "nom"            : "Petit-dejeuner",
                "moment"         : "matin",
                "part_calories"  : 0.18,
                "part_proteines" : 0.20,
                "part_glucides"  : 0.42,
                "part_lipides"   : 0.22,
                "digestibilite"  : "high",
            },
            "repas_2" : {
                "nom"            : "Dejeuner leger (pre-seance)",
                "moment"         : "midi",
                "part_calories"  : 0.42,
                "part_proteines" : 0.28,
                "part_glucides"  : 0.38,
                "part_lipides"   : 0.17,
                "digestibilite"  : "high",
            },
            "repas_3" : {
                "nom"            : "Diner (post-seance)",
                "moment"         : "soir",
                "part_calories"  : 0.40,
                "part_proteines" : 0.52,
                "part_glucides"  : 0.20,
                "part_lipides"   : 0.61,
                "digestibilite"  : "medium",
            },
        },
        "notes" : (
            "Petit-dej leger (18% cal). "
            "Effort explosif -> digestion haute avant. "
            "Proteines elevees post pour recuperation musculaire. "
            "Source : Thomas et al. 2016."
        ),
    },

    # ----------------------------------------------------------
    # TECHNIQUE
    # ----------------------------------------------------------
    "Technique" : {
        "digestibilite_avant" : "medium",
        "priorite_macro"      : ["proteines", "glucides", "lipides"],
        "timing_repas" : {
            "repas_1" : {
                "nom"            : "Petit-dejeuner equilibre",
                "moment"         : "matin",
                "part_calories"  : 0.20,
                "part_proteines" : 0.28,
                "part_glucides"  : 0.28,
                "part_lipides"   : 0.28,
                "digestibilite"  : "medium",
            },
            "repas_2" : {
                "nom"            : "Dejeuner equilibre",
                "moment"         : "midi",
                "part_calories"  : 0.42,
                "part_proteines" : 0.36,
                "part_glucides"  : 0.38,
                "part_lipides"   : 0.36,
                "digestibilite"  : "medium",
            },
            "repas_3" : {
                "nom"            : "Diner equilibre",
                "moment"         : "soir",
                "part_calories"  : 0.38,
                "part_proteines" : 0.36,
                "part_glucides"  : 0.34,
                "part_lipides"   : 0.36,
                "digestibilite"  : "medium",
            },
        },
        "notes" : (
            "Petit-dej leger (20% cal). "
            "Seance technique : alimentation reguliere et stable. "
            "Source : Jeukendrup 2014."
        ),
    },

    # ----------------------------------------------------------
    # RESISTANCE
    # ----------------------------------------------------------
    "Resistance" : {
        "digestibilite_avant" : "medium",
        "priorite_macro"      : ["glucides", "proteines", "lipides"],
        "timing_repas" : {
            "repas_1" : {
                "nom"            : "Petit-dejeuner charge glucides",
                "moment"         : "matin",
                "part_calories"  : 0.20,
                "part_proteines" : 0.18,
                "part_glucides"  : 0.38,
                "part_lipides"   : 0.18,
                "digestibilite"  : "medium",
            },
            "repas_2" : {
                "nom"            : "Dejeuner charge (pre-seance)",
                "moment"         : "midi",
                "part_calories"  : 0.45,
                "part_proteines" : 0.27,
                "part_glucides"  : 0.47,
                "part_lipides"   : 0.22,
                "digestibilite"  : "medium",
            },
            "repas_3" : {
                "nom"            : "Diner recharge (post-seance)",
                "moment"         : "soir",
                "part_calories"  : 0.35,
                "part_proteines" : 0.55,
                "part_glucides"  : 0.15,
                "part_lipides"   : 0.60,
                "digestibilite"  : "medium",
            },
        },
        "notes" : (
            "Petit-dej leger (20% cal). "
            "Endurance : charge glucidique maximale au dejeuner. "
            "Source : Burke et al. 2011."
        ),
    },

    # ----------------------------------------------------------
    # COMMANDO
    # ----------------------------------------------------------
    "Commando" : {
        "digestibilite_avant" : "high",
        "priorite_macro"      : ["proteines", "glucides", "lipides"],
        "timing_repas" : {
            "repas_1" : {
                "nom"            : "Petit-dejeuner pre-commando",
                "moment"         : "matin",
                "part_calories"  : 0.20,
                "part_proteines" : 0.25,
                "part_glucides"  : 0.47,
                "part_lipides"   : 0.13,
                "digestibilite"  : "high",
            },
            "repas_2" : {
                "nom"            : "Dejeuner leger (pre-seance)",
                "moment"         : "midi",
                "part_calories"  : 0.38,
                "part_proteines" : 0.25,
                "part_glucides"  : 0.33,
                "part_lipides"   : 0.12,
                "digestibilite"  : "high",
            },
            "repas_3" : {
                "nom"            : "Diner recuperation (post-commando)",
                "moment"         : "soir",
                "part_calories"  : 0.42,
                "part_proteines" : 0.50,
                "part_glucides"  : 0.20,
                "part_lipides"   : 0.75,
                "digestibilite"  : "medium",
            },
        },
        "notes" : (
            "Petit-dej leger (20% cal). "
            "Seance extreme : catabolisme musculaire tres eleve. "
            "Source : Gibala et al. 2006 / Scott et al. 2011."
        ),
    },

    # ----------------------------------------------------------
    # RECUPERATION
    # ----------------------------------------------------------
    "Recuperation" : {
        "digestibilite_avant" : "high",
        "priorite_macro"      : ["proteines", "lipides", "glucides"],
        "timing_repas" : {
            "repas_1" : {
                "nom"            : "Petit-dejeuner recuperation",
                "moment"         : "matin",
                "part_calories"  : 0.18,
                "part_proteines" : 0.30,
                "part_glucides"  : 0.28,
                "part_lipides"   : 0.38,
                "digestibilite"  : "high",
            },
            "repas_2" : {
                "nom"            : "Dejeuner recuperation",
                "moment"         : "midi",
                "part_calories"  : 0.42,
                "part_proteines" : 0.38,
                "part_glucides"  : 0.38,
                "part_lipides"   : 0.32,
                "digestibilite"  : "high",
            },
            "repas_3" : {
                "nom"            : "Diner leger",
                "moment"         : "soir",
                "part_calories"  : 0.40,
                "part_proteines" : 0.32,
                "part_glucides"  : 0.34,
                "part_lipides"   : 0.30,
                "digestibilite"  : "high",
            },
        },
        "notes" : (
            "Petit-dej leger (18% cal). "
            "Recuperation : omega-3 et antioxydants prioritaires. "
            "Source : ISSN Recovery Position Stand."
        ),
    },

    # ----------------------------------------------------------
    # REPOS
    # ----------------------------------------------------------
    "Repos" : {
        "digestibilite_avant" : "high",
        "priorite_macro"      : ["proteines", "glucides", "lipides"],
        "timing_repas" : {
            "repas_1" : {
                "nom"            : "Petit-dejeuner",
                "moment"         : "matin",
                "part_calories"  : 0.18,
                "part_proteines" : 0.30,
                "part_glucides"  : 0.30,
                "part_lipides"   : 0.30,
                "digestibilite"  : "high",
            },
            "repas_2" : {
                "nom"            : "Dejeuner",
                "moment"         : "midi",
                "part_calories"  : 0.42,
                "part_proteines" : 0.35,
                "part_glucides"  : 0.35,
                "part_lipides"   : 0.35,
                "digestibilite"  : "high",
            },
            "repas_3" : {
                "nom"            : "Diner",
                "moment"         : "soir",
                "part_calories"  : 0.40,
                "part_proteines" : 0.35,
                "part_glucides"  : 0.35,
                "part_lipides"   : 0.35,
                "digestibilite"  : "high",
            },
        },
        "notes" : (
            "Petit-dej leger (18% cal). "
            "Repos : distribution equilibree sur 3 repas. "
            "Source : Helms et al. 2014."
        ),
    },
}


# ------------------------------------------------------------
# FONCTIONS UTILITAIRES
# ------------------------------------------------------------
def _split_seance(seance: str) -> list:
    """
    Decoupe un nom de seance composite en sous-seances.
    Gere tous les cas d'espacement autour des separateurs.
    """
    parties = re.split(r'\s*[/+&-]\s*', seance.strip())
    return [p.strip() for p in parties if p.strip()]


def get_regles_seance(seance: str) -> dict:
    """
    Retourne les regles nutritionnelles pour une seance.
    Pour les seances composites, fusionne les regles
    en prenant les contraintes les plus strictes.
    """
    sous_seances = _split_seance(seance)
    regles_list  = []

    for ss in sous_seances:
        trouve = False
        for key, val in REGLES_SEANCES.items():
            if key.lower() in ss.lower():
                regles_list.append(val)
                trouve = True
                break
        if not trouve:
            regles_list.append(REGLES_SEANCES["Repos"])

    if len(regles_list) == 1:
        return regles_list[0]

    return _fusionner_regles(regles_list)


def _fusionner_regles(regles_list: list) -> dict:
    """
    Fusionne les regles de plusieurs seances.
    Prend les contraintes les plus strictes.
    """
    ordre_digestibilite = {"high": 0, "medium": 1, "low": 2}

    # Digestibilite avant -> la plus stricte
    digestibilite_avant = min(
        [r["digestibilite_avant"] for r in regles_list],
        key=lambda x: ordre_digestibilite[x]
    )

    # Priorite macro -> seance la plus intense (premiere)
    priorite_macro = regles_list[0]["priorite_macro"]

    # Timing -> moyenne ponderee des parts
    timing_fusionne = _fusionner_timing(regles_list)

    # Notes concatenees
    notes = " | ".join([r["notes"] for r in regles_list])

    return {
        "digestibilite_avant" : digestibilite_avant,
        "priorite_macro"      : priorite_macro,
        "timing_repas"        : timing_fusionne,
        "notes"               : notes,
    }

def valider_regles_seances() -> None:
    """
    Verifie que la somme des parts de chaque macro
    fait bien 1.0 pour chaque seance et chaque repas.
    Affiche les erreurs si des incoherences sont detectees.
    """
    print("\n" + "=" * 55)
    print("  VALIDATION DES PARTS DE MACROS")
    print("=" * 55)

    erreurs = []
    macros  = ["part_calories", "part_proteines", "part_glucides", "part_lipides"]

    for nom_seance, regles in REGLES_SEANCES.items():
        for macro in macros:
            total = sum(
                regles["timing_repas"][repas][macro]
                for repas in ["repas_1", "repas_2", "repas_3"]
                if repas in regles["timing_repas"]
            )
            total = round(total, 3)
            if abs(total - 1.0) > 0.01:
                erreurs.append(
                    f"  [ERREUR] {nom_seance:<30} "
                    f"{macro:<20} : somme = {total:.3f} (attendu 1.0)"
                )
            else:
                print(
                    f"  [OK]     {nom_seance:<30} "
                    f"{macro:<20} : {total:.3f}"
                )

    if erreurs:
        print("\n  ERREURS DETECTEES :")
        for e in erreurs:
            print(e)
    else:
        print("\n  Toutes les sommes sont correctes.")

    print("=" * 55)

def _fusionner_timing(regles_list: list) -> dict:
    """
    Fusionne les timings de repas par moyenne des parts.
    Les 3 repas restent fixes : matin / midi / soir.
    """
    nb = len(regles_list)

    timing_fusionne = {}

    for nom_repas in ["repas_1", "repas_2", "repas_3"]:
        repas_list = [
            r["timing_repas"][nom_repas]
            for r in regles_list
            if nom_repas in r["timing_repas"]
        ]

        if not repas_list:
            continue

        # Digestibilite -> la plus stricte
        ordre = {"high": 0, "medium": 1, "low": 2}
        digestibilite = min(
            [r["digestibilite"] for r in repas_list],
            key=lambda x: ordre[x]
        )

        timing_fusionne[nom_repas] = {
            "nom"            : repas_list[0]["nom"],
            "moment"         : repas_list[0]["moment"],
            "part_calories"  : round(
                sum(r["part_calories"]  for r in repas_list) / nb, 3
            ),
            "part_proteines" : round(
                sum(r["part_proteines"] for r in repas_list) / nb, 3
            ),
            "part_glucides"  : round(
                sum(r["part_glucides"]  for r in repas_list) / nb, 3
            ),
            "part_lipides"   : round(
                sum(r["part_lipides"]   for r in repas_list) / nb, 3
            ),
            "digestibilite"  : digestibilite,
        }

    return timing_fusionne


def get_digestibilite_avant(seance: str) -> str:
    return get_regles_seance(seance)["digestibilite_avant"]


def get_timing_repas(seance: str) -> dict:
    return get_regles_seance(seance)["timing_repas"]


def get_priorite_macro(seance: str) -> list:
    return get_regles_seance(seance)["priorite_macro"]


def afficher_regles_seance(seance: str) -> None:
    regles = get_regles_seance(seance)

    print(f"\n{'=' * 65}")
    print(f"  REGLES NUTRITIONNELLES : {seance.upper()}")
    print(f"{'=' * 65}")
    print(f"  Digestibilite avant effort : {regles['digestibilite_avant']}")
    print(f"  Priorite macros            : {' > '.join(regles['priorite_macro'])}")
    print(f"\n  Timing des 3 repas :")

    for nom_repas, repas in regles["timing_repas"].items():
        print(f"\n    {repas['nom'].upper()} ({repas['moment']})")
        print(f"      Calories  : {repas['part_calories']*100:.0f}%")
        print(f"      Proteines : {repas['part_proteines']*100:.0f}%")
        print(f"      Glucides  : {repas['part_glucides']*100:.0f}%")
        print(f"      Lipides   : {repas['part_lipides']*100:.0f}%")
        print(f"      Digest.   : {repas['digestibilite']}")

    print(f"\n  Notes scientifiques :")
    for note in regles["notes"].split(" | "):
        print(f"    - {note}")
    print(f"{'=' * 65}")


# ------------------------------------------------------------
# TEST AUTONOME
# ------------------------------------------------------------
if __name__ == "__main__":

    valider_regles_seances()

    seances_test = [
        "Musculation",
        "Sprint",
        "Technique",
        "Repos",
        "Musculation / Sprint",
        "Musculation / Chariot / Pliometrie",
        "Commando",
    ]

    for seance in seances_test:
        afficher_regles_seance(seance)