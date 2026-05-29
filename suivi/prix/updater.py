# ============================================================
# MISE À JOUR DES PRIX EN BASE
# suivi/prix/updater.py
#
# Dans la nouvelle architecture, l'updater est appelé
# par pipeline_prix.py APRÈS le pricing Piloterr.
#
# Son rôle est de mettre à jour nutrition.db avec les
# prix récupérés via l'API magasin (plus via Excel).
#
# Il conserve l'historique des prix et calcule
# le promo_score pour chaque aliment.
# ============================================================

import sys
import sqlite3
from pathlib import Path
from datetime import datetime
sys.dont_write_bytecode = True

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from config import (
    NUTRITION_DB,
    NB_SEMAINES_HISTORIQUE_PRIX,
)

# Seuil promo défini localement car supprimé du config v1
PROMO_SCORE_MIN = 0.15


# ------------------------------------------------------------
# CONNEXION BASE DE DONNÉES
# ------------------------------------------------------------
def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(NUTRITION_DB)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------------------
# CRÉATION TABLE HISTORIQUE PRIX
# ------------------------------------------------------------
def _create_table_prix(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS historique_prix (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            aliment_id  INTEGER NOT NULL,
            nom_aliment TEXT,
            magasin     TEXT,
            prix_actuel REAL NOT NULL,
            prix_moyen  REAL,
            promo_score REAL DEFAULT 0.0,
            date_releve TEXT NOT NULL,
            semaine     INTEGER,
            annee       INTEGER,
            FOREIGN KEY (aliment_id) REFERENCES aliments(id)
        )
    """)
    conn.commit()


# ------------------------------------------------------------
# RECHERCHE D'UN ALIMENT EN BASE
# ------------------------------------------------------------
def _trouver_aliment(conn: sqlite3.Connection, nom: str):
    """
    Cherche un aliment dans nutrition.db par son nom.
    Recherche exacte d'abord, puis partielle.
    """
    cursor = conn.cursor()

    # Recherche exacte
    cursor.execute(
        "SELECT id, nom, cout_kg FROM aliments WHERE LOWER(nom) = LOWER(?)",
        (nom,)
    )
    row = cursor.fetchone()
    if row:
        return dict(row)

    # Recherche partielle
    cursor.execute(
        "SELECT id, nom, cout_kg FROM aliments WHERE LOWER(nom) LIKE LOWER(?)",
        (f"%{nom}%",)
    )
    row = cursor.fetchone()
    if row:
        return dict(row)

    return None


# ------------------------------------------------------------
# CALCUL DU PRIX MOYEN HISTORIQUE — Corrigé
# ------------------------------------------------------------
def _calculer_prix_moyen(
    conn        : sqlite3.Connection,
    aliment_id  : int,
    prix_actuel : float,
) -> float:
    """
    Calcule le prix moyen sur les NB_SEMAINES_HISTORIQUE_PRIX
    dernières semaines.

    ✅ Fix : sous-requête pour que LIMIT soit respecté avec AVG.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT AVG(prix_actuel) as moy
        FROM (
            SELECT prix_actuel
            FROM historique_prix
            WHERE aliment_id = ?
            ORDER BY date_releve DESC
            LIMIT ?
        )
    """, (aliment_id, NB_SEMAINES_HISTORIQUE_PRIX))

    row = cursor.fetchone()
    if row and row["moy"] is not None:
        # Moyenne pondérée : 70% historique + 30% prix actuel
        return round(row["moy"] * 0.7 + prix_actuel * 0.3, 3)

    return prix_actuel


# ------------------------------------------------------------
# CALCUL DU PROMO SCORE
# ------------------------------------------------------------
def _calculer_promo_score(prix_actuel: float, prix_moyen: float) -> float:
    """
    promo_score = (prix_moyen - prix_actuel) / prix_moyen

    > 0.15 : promotion intéressante
    0-0.15 : prix normal
    < 0    : prix plus élevé que d'habitude
    """
    if prix_moyen <= 0:
        return 0.0
    return round((prix_moyen - prix_actuel) / prix_moyen, 4)


# ------------------------------------------------------------
# MISE À JOUR D'UN ALIMENT
# ------------------------------------------------------------
def _mettre_a_jour_aliment(
    conn        : sqlite3.Connection,
    aliment_id  : int,
    nom_aliment : str,
    magasin     : str,
    prix_actuel : float,
) -> dict:
    """
    Met à jour cout_kg dans aliments et insère
    un enregistrement dans historique_prix.
    """
    cursor     = conn.cursor()
    maintenant = datetime.now()
    semaine    = maintenant.isocalendar()[1]
    annee      = maintenant.year

    # Vérifier si un relevé existe déjà cette semaine
    cursor.execute("""
        SELECT id FROM historique_prix
        WHERE aliment_id = ?
          AND semaine    = ?
          AND annee      = ?
    """, (aliment_id, semaine, annee))

    existe_deja = cursor.fetchone()

    # Calcul prix moyen et promo score
    prix_moyen  = _calculer_prix_moyen(conn, aliment_id, prix_actuel)
    promo_score = _calculer_promo_score(prix_actuel, prix_moyen)

    if existe_deja:
        cursor.execute("""
            UPDATE historique_prix
            SET prix_actuel = ?,
                prix_moyen  = ?,
                promo_score = ?,
                magasin     = ?,
                date_releve = ?
            WHERE id = ?
        """, (
            prix_actuel, prix_moyen, promo_score,
            magasin, maintenant.strftime("%Y-%m-%d %H:%M:%S"),
            existe_deja["id"]
        ))
    else:
        cursor.execute("""
            INSERT INTO historique_prix (
                aliment_id, nom_aliment, magasin,
                prix_actuel, prix_moyen, promo_score,
                date_releve, semaine, annee
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            aliment_id, nom_aliment, magasin,
            prix_actuel, prix_moyen, promo_score,
            maintenant.strftime("%Y-%m-%d %H:%M:%S"),
            semaine, annee
        ))

    # Mettre à jour cout_kg dans aliments
    cursor.execute("""
        UPDATE aliments
        SET cout_kg = ?
        WHERE id = ?
    """, (prix_actuel, aliment_id))

    conn.commit()

    return {
        "aliment_id"  : aliment_id,
        "nom"         : nom_aliment,
        "magasin"     : magasin,
        "prix_actuel" : prix_actuel,
        "prix_moyen"  : prix_moyen,
        "promo_score" : promo_score,
        "en_promo"    : promo_score >= PROMO_SCORE_MIN,
    }


# ------------------------------------------------------------
# NETTOYAGE HISTORIQUE ANCIEN — Corrigé
# ------------------------------------------------------------
def _nettoyer_historique(conn: sqlite3.Connection) -> None:
    """
    Supprime les relevés plus anciens que
    NB_SEMAINES_HISTORIQUE_PRIX semaines.

    ✅ Fix : syntaxe SQLite datetime() correcte.
    """
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM historique_prix
        WHERE date_releve < datetime('now', ?)
    """, (f"-{NB_SEMAINES_HISTORIQUE_PRIX} weeks",))

    nb_supprimes = cursor.rowcount
    conn.commit()

    if nb_supprimes > 0:
        print(f"[OK] {nb_supprimes} relevés anciens supprimés")


# ------------------------------------------------------------
# MISE À JOUR DEPUIS LES RÉSULTATS PRICER
# Nouvelle fonction — remplace l'ancienne lecture Excel
# ------------------------------------------------------------
def mettre_a_jour_depuis_pricer(resultats_pricer: list) -> list:
    """
    Met à jour nutrition.db depuis les résultats
    du Pricer (prix récupérés via Piloterr).

    Appelée par pipeline_prix.py après le pricing.

    resultats_pricer : liste de recettes avec leurs ingrédients
    [
        {
            "recette_id" : 42,
            "ingredients": [
                {
                    "nom_en"    : "chicken breast",
                    "nom_fr"    : "blanc de poulet",
                    "prix_kg"   : 9.50,
                    "magasin"   : "leclerc",
                    "trouve"    : True,
                },
                ...
            ]
        },
        ...
    ]
    """
    print("\n[...] Mise à jour des prix dans nutrition.db...")

    if not NUTRITION_DB.exists():
        print(f"[ERREUR] nutrition.db introuvable : {NUTRITION_DB}")
        return []

    conn = _get_connection()
    _create_table_prix(conn)
    _nettoyer_historique(conn)

    resultats   = []
    mis_a_jour  = 0
    non_trouves = []

    # Extraire tous les ingrédients uniques des recettes
    ingredients_vus = {}

    for recette in resultats_pricer:
        for ing in recette.get("ingredients", []):
            if not ing.get("trouve"):
                continue

            nom_en  = ing.get("nom_en", "")
            nom_fr  = ing.get("nom_fr", "")
            prix_kg = ing.get("prix_kg", 0)
            magasin = ing.get("magasin", "")

            # Dédoublonner par nom_en
            if nom_en in ingredients_vus:
                continue
            ingredients_vus[nom_en] = True

            # Chercher dans nutrition.db
            # Essai nom_fr d'abord, puis nom_en
            aliment = _trouver_aliment(conn, nom_fr) or \
                      _trouver_aliment(conn, nom_en)

            if aliment is None:
                non_trouves.append(nom_en)
                continue

            resultat = _mettre_a_jour_aliment(
                conn,
                aliment["id"],
                aliment["nom"],
                magasin,
                prix_kg,
            )
            resultats.append(resultat)
            mis_a_jour += 1

    conn.close()

    # Rapport
    print(f"[OK] Aliments mis à jour : {mis_a_jour}")

    if non_trouves:
        print(f"\n  Non trouvés en nutrition.db ({len(non_trouves)}) :")
        for nom in non_trouves:
            print(f"    → {nom}")

    return resultats


# ------------------------------------------------------------
# FONCTION PRINCIPALE — Conservée pour compatibilité
# Appelée depuis pipeline_prix.py
# ------------------------------------------------------------
def mettre_a_jour_prix() -> list:
    """
    Point d'entrée appelé par pipeline_prix.py.
    Sans argument car les prix viennent du Pricer.

    ⚠️ Sans résultats Pricer passés en argument,
    cette fonction ne fait que nettoyer l'historique.
    Utilisez mettre_a_jour_depuis_pricer() depuis
    pipeline_prix.py pour la mise à jour complète.
    """
    print("\n[...] Nettoyage historique prix...")

    if not NUTRITION_DB.exists():
        print(f"[ERREUR] nutrition.db introuvable : {NUTRITION_DB}")
        return []

    conn = _get_connection()
    _create_table_prix(conn)
    _nettoyer_historique(conn)
    conn.close()

    print("[OK] Historique nettoyé.")
    return []


# ------------------------------------------------------------
# TEST AUTONOME
# ------------------------------------------------------------
if __name__ == "__main__":
    print("[TEST] Updater — nettoyage historique")
    mettre_a_jour_prix()
    print("[OK] Test terminé.")
