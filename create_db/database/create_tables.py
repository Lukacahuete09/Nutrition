# ============================================================
# CREATION DES TABLES DE LA BASE DE DONNEES
# ============================================================

import sqlite3


def create_tables(conn: sqlite3.Connection) -> None:
    """
    Cree toutes les tables necessaires si elles n existent pas.
    """
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nom         TEXT NOT NULL UNIQUE,
            description TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aliments (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            nom                 TEXT NOT NULL,
            categorie_id        INTEGER,
            calories_100g       REAL,
            proteines_g         REAL,
            glucides_g          REAL,
            lipides_g           REAL,
            fibres_g            REAL,
            eau_g               REAL,
            sodium_mg           REAL,
            potassium_mg        REAL,
            calcium_mg          REAL,
            magnesium_mg        REAL,
            fer_mg              REAL,
            zinc_mg             REAL,
            vitamine_c_mg       REAL,
            vitamine_d_ug       REAL,
            vitamine_b12_ug     REAL,
            omega3_g            REAL,
            digestibilite       TEXT CHECK(digestibilite IN ('low','medium','high')),
            cout_kg             REAL DEFAULT 0.0,
            densite_proteique   REAL DEFAULT 0.0,
            score_nutritionnel  REAL DEFAULT 0.0,
            source              TEXT DEFAULT 'CIQUAL 2020',
            FOREIGN KEY (categorie_id) REFERENCES categories(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prix_dynamique (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            aliment_id   INTEGER NOT NULL,
            magasin      TEXT,
            prix_actuel  REAL,
            prix_moyen   REAL,
            promo_bool   INTEGER DEFAULT 0,
            promo_score  REAL DEFAULT 0.0,
            date_maj     TEXT,
            FOREIGN KEY (aliment_id) REFERENCES aliments(id)
        )
    """)

    conn.commit()
    print("[OK] Tables creees.")
