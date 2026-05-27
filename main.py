# ============================================================
# POINT D ENTREE GLOBAL
# ============================================================

import sys
import os

sys.path.append(os.path.dirname(__file__))


def main():
    print("=" * 55)
    print("  SYSTEME DE NUTRITION SPORTIVE")
    print("=" * 55)
    print()

    # PHASE 1 — Base de donnees
    db_path = os.path.join("create_db", "data", "nutrition.db")
    if not os.path.exists(db_path):
        print("[CREATE_DB] Base absente — initialisation...")
        from create_db.main import main as run_create_db
        run_create_db()
    else:
        print("[CREATE_DB] Base presente — initialisation ignoree.")

    print()

    # PHASE 2 — Optimisation
    print("[OPTIMISATION] Lancement du moteur...")
    from optimisation.main import main as run_optimisation
    run_optimisation()

    print()

    # PHASE 3 — Suivi
    print("[SUIVI] Lancement du suivi dynamique...")
    from suivi.main import main as run_suivi
    run_suivi()

    print()
    print("=" * 55)
    print("  CYCLE HEBDOMADAIRE TERMINE")
    print("=" * 55)


if __name__ == "__main__":
    main()
