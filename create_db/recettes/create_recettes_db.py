# ============================================================
# CREATION DE LA BASE DE DONNEES RECETTES
# create_db/recettes/create_recettes_db.py
# ============================================================

import sqlite3
import sys
sys.dont_write_bytecode = True


def create_recettes_tables(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recettes (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            spoonacular_id      INTEGER UNIQUE,
            nom_fr              TEXT NOT NULL,
            nom_en              TEXT,
            type_repas          TEXT,
            type_seance         TEXT DEFAULT 'all',
            nb_personnes        INTEGER DEFAULT 1,
            temps_prep_min      INTEGER DEFAULT 0,
            source_url          TEXT,
            image_url           TEXT,
            digestibilite       TEXT DEFAULT 'medium',
            calories_portion    REAL DEFAULT 0,
            proteines_g         REAL DEFAULT 0,
            glucides_g          REAL DEFAULT 0,
            lipides_g           REAL DEFAULT 0,
            fibres_g            REAL DEFAULT 0,
            cout_portion        REAL DEFAULT 0,
            score_nutritionnel  REAL DEFAULT 0,
            valide              INTEGER DEFAULT 1,
            date_import         TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recette_ingredients (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            recette_id      INTEGER NOT NULL,
            nom_fr          TEXT,
            nom_en          TEXT,
            quantite_g      REAL DEFAULT 0,
            unite           TEXT,
            calories        REAL DEFAULT 0,
            proteines_g     REAL DEFAULT 0,
            glucides_g      REAL DEFAULT 0,
            lipides_g       REAL DEFAULT 0,
            FOREIGN KEY (recette_id) REFERENCES recettes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recette_instructions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            recette_id  INTEGER NOT NULL,
            etape       INTEGER NOT NULL,
            instruction_fr TEXT,
            instruction_en TEXT,
            FOREIGN KEY (recette_id) REFERENCES recettes(id)
        )
    """)

    conn.commit()
    print("[OK] Tables recettes creees.")
