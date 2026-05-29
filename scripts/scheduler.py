# ============================================================
# GESTIONNAIRE DE PLANIFICATION
# scripts/scheduler.py
# ============================================================

import sys
import os
import subprocess
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))
sys.dont_write_bytecode = True

from config import MAGASIN_DEFAUT, LOGS_DIR, ROOT_DIR

# ------------------------------------------------------------
# CONSTANTES
# ------------------------------------------------------------
TASK_NAME    = "NutritionSportive_Weekly"
SCRIPT_PATH  = ROOT_DIR / "scripts" / "run_weekly.py"
MAIN_PATH    = ROOT_DIR / "main.py"
PYTHON_PATH  = sys.executable
HEURE        = "15:00"
JOUR_SEMAINE = "DIM"


# ------------------------------------------------------------
# WINDOWS — Tâche planifiée
# ------------------------------------------------------------
def installer_tache():
    commande = [
        "schtasks", "/create",
        "/tn",  TASK_NAME,
        "/tr",  f'"{PYTHON_PATH}" "{SCRIPT_PATH}"',
        "/sc",  "WEEKLY",
        "/d",   JOUR_SEMAINE,
        "/st",  HEURE,
        "/f",
        "/rl",  "HIGHEST",
    ]

    print(f"[...] Installation tâche planifiée : {TASK_NAME}")
    print(f"      Script  : {SCRIPT_PATH}")
    print(f"      Python  : {PYTHON_PATH}")
    print(f"      Horaire : Dimanche à {HEURE}")
    print(f"      Magasin : {MAGASIN_DEFAUT.upper()}")

    result = subprocess.run(commande, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] Tâche installée avec succès.")
        print(f"     Prochain lancement : dimanche prochain à {HEURE}")
    else:
        print(f"[ERREUR] {result.stderr}")
        print(f"[INFO]   Relancez en tant qu'administrateur.")


def desinstaller_tache():
    commande = ["schtasks", "/delete", "/tn", TASK_NAME, "/f"]

    print(f"[...] Suppression tâche planifiée : {TASK_NAME}")
    result = subprocess.run(commande, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] Tâche supprimée.")
    else:
        print(f"[ERREUR] {result.stderr}")


def verifier_tache():
    commande = ["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"]
    result   = subprocess.run(commande, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] Tâche trouvée :")
        print(result.stdout)
    else:
        print(f"[INFO] Tâche non trouvée.")
        print(f"       Lancez : python scripts/scheduler.py install")


def lancer_maintenant():
    """
    Lance directement main.py run
    sans passer par run_weekly.py
    """
    print(f"[...] Lancement immédiat via main.py...")
    result = subprocess.run(
        [
            PYTHON_PATH,
            str(MAIN_PATH),
            "run",
            "--magasin", MAGASIN_DEFAUT,
        ],
        capture_output = False,
        cwd            = str(ROOT_DIR),
    )
    if result.returncode == 0:
        print(f"[OK] Exécution terminée.")
    else:
        print(f"[ERREUR] Code retour : {result.returncode}")


# ------------------------------------------------------------
# POINT D'ENTRÉE
# ------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gestionnaire de planification — Nutrition Sportive"
    )
    parser.add_argument(
        "action",
        choices = ["install", "uninstall", "check", "run"],
        help    = (
            "install   : installe la tâche planifiée Windows\n"
            "uninstall : supprime la tâche planifiée Windows\n"
            "check     : vérifie l'installation Windows\n"
            "run       : lance le pipeline immédiatement\n"
        )
    )
    args = parser.parse_args()

    if   args.action == "install":
        installer_tache()
    elif args.action == "uninstall":
        desinstaller_tache()
    elif args.action == "check":
        verifier_tache()
    elif args.action == "run":
        lancer_maintenant()