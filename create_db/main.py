# ============================================================
# POINT D ENTREE — CREATION BASE DE DONNEES
# create_db/main.py
# ============================================================

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True

from database.connection     import get_connection
from database.create_tables  import create_tables
from database.categories     import insert_categories
from importers.ciqual_parser import parse_ciqual
from importers.inserter      import insert_aliments, print_repartition
from engine.scoring          import update_scores
from config                  import CIQUAL_LOCAL


def main():
    print("=" * 50)
    print("  CREATION BASE DE DONNEES ALIMENTAIRE")
    print("=" * 50)

    # Verification presence du fichier CIQUAL
    if not os.path.exists(CIQUAL_LOCAL):
        print(f"[ERREUR] Fichier CIQUAL introuvable : {CIQUAL_LOCAL}")
        print(f"[INFO]   Placez le fichier dans create_db/data/")
        return

    print(f"[OK] Fichier CIQUAL detecte : {CIQUAL_LOCAL}")

    # Connexion
    conn = get_connection()

    # Tables
    create_tables(conn)

    # Categories
    insert_categories(conn)

    # Parser CIQUAL
    df = parse_ciqual()

    # Inserer
    insert_aliments(conn, df)

    # Scores
    update_scores(conn)

    # Rapport
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM aliments")
    total = cursor.fetchone()["total"]
    print(f"\n[OK] Base creee : {total} aliments dans nutrition.db")
    print_repartition(conn)

    conn.close()
    print("\n[OK] Creation base de donnees terminee.")


if __name__ == "__main__":
    main()