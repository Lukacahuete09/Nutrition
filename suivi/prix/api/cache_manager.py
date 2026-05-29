import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))
from config import NUTRITION_DB, CACHE_PRIX_JOURS


class CacheManager:
    """
    Cache local SQLite des prix récupérés via API.
    Évite de reconsommer des crédits pour les mêmes
    ingrédients récemment recherchés.
    """

    def __init__(self):
        self.conn = sqlite3.connect(NUTRITION_DB)
        self.conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_prix_api (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                query           TEXT NOT NULL,
                magasin         TEXT NOT NULL,
                produit_id      TEXT,
                nom_produit     TEXT,
                prix_kg         REAL,
                prix_unite      REAL,
                unite           TEXT,
                url             TEXT,
                date_cache      TEXT NOT NULL,
                UNIQUE(query, magasin)
            )
        """)
        self.conn.commit()

    # ----------------------------------------------------------
    # LECTURE CACHE
    # ----------------------------------------------------------
    def get(self, query: str, magasin: str) -> dict | None:
        """
        Retourne le résultat caché si encore valide.
        None si absent ou expiré.
        """
        expiration = (
            datetime.now() - timedelta(days=CACHE_PRIX_JOURS)
        ).strftime("%Y-%m-%d %H:%M:%S")

        row = self.conn.execute("""
            SELECT * FROM cache_prix_api
            WHERE query   = ?
              AND magasin = ?
              AND date_cache > ?
        """, (query.lower(), magasin, expiration)).fetchone()

        if row:
            print(f"[CACHE] {query} ({magasin}) → prix_kg={row['prix_kg']} €")
            return dict(row)

        return None

    # ----------------------------------------------------------
    # ÉCRITURE CACHE
    # ----------------------------------------------------------
    def set(self, query: str, magasin: str, produit: dict) -> None:
        """
        Sauvegarde un résultat API en cache.
        """
        self.conn.execute("""
            INSERT INTO cache_prix_api
                (query, magasin, produit_id, nom_produit,
                 prix_kg, prix_unite, unite, url, date_cache)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(query, magasin) DO UPDATE SET
                produit_id  = excluded.produit_id,
                nom_produit = excluded.nom_produit,
                prix_kg     = excluded.prix_kg,
                prix_unite  = excluded.prix_unite,
                unite       = excluded.unite,
                url         = excluded.url,
                date_cache  = excluded.date_cache
        """, (
            query.lower(), magasin,
            produit.get("produit_id", ""),
            produit.get("nom", ""),
            produit.get("prix_kg", 0),
            produit.get("prix_unite", 0),
            produit.get("unite", ""),
            produit.get("url", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ))
        self.conn.commit()

    def close(self):
        self.conn.close()