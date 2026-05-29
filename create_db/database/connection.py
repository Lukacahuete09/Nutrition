# ============================================================
# GESTION DE LA CONNEXION SQLITE
# ============================================================
import sys
import sqlite3

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """
    Retourne une connexion SQLite a la base de donnees.
    Cree le fichier si inexistant.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
