# ============================================================
# POINT D ENTREE — CREATION BASE RECETTES
# create_db/recettes/main_recettes.py
# ============================================================

import sys
import os
import sqlite3
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_recettes        import RECETTES_DB
from create_recettes_db     import create_recettes_tables
from spoonacular_importer   import importer_toutes_recettes


def main():
    print("=" * 60)
    print("  CREATION BASE DE DONNEES RECETTES")
    print("=" * 60)

    os.makedirs(os.path.dirname(RECETTES_DB), exist_ok=True)

    conn = sqlite3.connect(RECETTES_DB)
    conn.row_factory = sqlite3.Row

    # Creer les tables
    create_recettes_tables(conn)

    # Importer les recettes
    importer_toutes_recettes(conn)

    conn.close()
    print("\n[OK] Base recettes terminee.")


if __name__ == "__main__":
    main()