# check_aliments3.py
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "create_db", "data", "nutrition.db"
)

conn   = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

recherches = [
    "pâte",
    "pasta",
    "clém",
    "clem",
    "huile",
    "saumon",
    "oeuf entier",
    "oeuf, entier",
    "poulet, filet",
    "poulet, blanc",
    "poulet rôti",
    "sein",
    "fraise",
    "ananas",
    "kiwi",
    "melon",
    "carotte, bouillie",
    "haricot vert, bouilli",
    "riz, blanc, cuit",
    "couscous",
    "pain, blanc",
    "pain baguette",
]

for mot in recherches:
    cursor.execute("""
        SELECT a.id, a.nom, a.categorie_id, c.nom,
               a.calories_100g, a.proteines_g,
               a.glucides_g, a.lipides_g, a.digestibilite
        FROM aliments a
        LEFT JOIN categories c ON a.categorie_id = c.id
        WHERE LOWER(a.nom) LIKE ?
        AND a.calories_100g > 0
        ORDER BY a.calories_100g ASC
        LIMIT 3
    """, (f"%{mot.lower()}%",))

    resultats = cursor.fetchall()
    if resultats:
        print(f"\n--- {mot.upper()} ---")
        for r in resultats:
            print(
                f"  [{r[0]:4d}] {r[1]:<55}"
                f" {r[4]:.0f}kcal"
                f" P:{r[5]:.1f} G:{r[6]:.1f} L:{r[7]:.1f}"
                f" digest:{r[8]}"
            )
    else:
        print(f"\n--- {mot.upper()} --- AUCUN RESULTAT")

conn.close()
