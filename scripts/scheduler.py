# ============================================================
# CONFIGURATION DU PLANIFICATEUR WINDOWS
# scripts/scheduler.py
#
# Installe une tache planifiee Windows qui lance
# run_weekly.py tous les dimanches a 15h00
#
# Lancer UNE SEULE FOIS en tant qu administrateur :
#   python scripts/scheduler.py install
#
# Pour desinstaller :
#   python scripts/scheduler.py uninstall
#
# Pour tester immediatement :
#   python scripts/scheduler.py run
# ============================================================

import sys
import os
import subprocess
import argparse
sys.dont_write_bytecode = True

TASK_NAME    = "NutritionSportive_Weekly"
SCRIPT_PATH  = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "run_weekly.py")
)
PYTHON_PATH  = sys.executable
HEURE        = "15:00"
JOUR_SEMAINE = "DIM"   # Dimanche en francais Windows


def installer_tache():
    """
    Installe la tache planifiee Windows.
    Necessite les droits administrateur.
    """
    commande = [
        "schtasks", "/create",
        "/tn",  TASK_NAME,
        "/tr",  f'"{PYTHON_PATH}" "{SCRIPT_PATH}"',
        "/sc",  "WEEKLY",
        "/d",   JOUR_SEMAINE,
        "/st",  HEURE,
        "/f",                    # forcer si existe deja
        "/rl",  "HIGHEST",       # niveau le plus eleve
    ]

    print(f"[...] Installation tache planifiee : {TASK_NAME}")
    print(f"      Script  : {SCRIPT_PATH}")
    print(f"      Python  : {PYTHON_PATH}")
    print(f"      Horaire : Dimanche a {HEURE}")

    result = subprocess.run(commande, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] Tache installee avec succes.")
        print(f"     Prochain lancement : dimanche prochain a {HEURE}")
    else:
        print(f"[ERREUR] {result.stderr}")
        print(f"[INFO]   Relancez en tant qu administrateur.")


def desinstaller_tache():
    """
    Supprime la tache planifiee Windows.
    """
    commande = [
        "schtasks", "/delete",
        "/tn", TASK_NAME,
        "/f"
    ]

    print(f"[...] Suppression tache planifiee : {TASK_NAME}")
    result = subprocess.run(commande, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] Tache supprimee.")
    else:
        print(f"[ERREUR] {result.stderr}")


def verifier_tache():
    """
    Verifie si la tache est bien installee.
    """
    commande = ["schtasks", "/query", "/tn", TASK_NAME, "/fo", "LIST"]
    result   = subprocess.run(commande, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] Tache trouvee :")
        print(result.stdout)
    else:
        print(f"[INFO] Tache non trouvee. Lancez : python scheduler.py install")


def lancer_maintenant():
    """
    Lance le script immediatement pour tester.
    """
    print(f"[...] Lancement immediat du script...")
    result = subprocess.run(
        [PYTHON_PATH, SCRIPT_PATH],
        capture_output=False
    )
    if result.returncode == 0:
        print(f"[OK] Execution terminee.")
    else:
        print(f"[ERREUR] Code retour : {result.returncode}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gestionnaire de tache planifiee Nutrition Sportive"
    )
    parser.add_argument(
        "action",
        choices=["install", "uninstall", "check", "run"],
        help=(
            "install   : installe la tache planifiee\n"
            "uninstall : supprime la tache planifiee\n"
            "check     : verifie l installation\n"
            "run       : lance le script immediatement"
        )
    )
    args = parser.parse_args()

    if args.action == "install":
        installer_tache()
    elif args.action == "uninstall":
        desinstaller_tache()
    elif args.action == "check":
        verifier_tache()
    elif args.action == "run":
        lancer_maintenant()