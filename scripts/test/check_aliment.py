# check_aliments.py
# A lancer depuis la racine du projet

import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "create_db", "data", "nutrition.db"
)
conn    = sqlite3.connect(DB_PATH)
cursor  = conn.cursor()

recherches = [
    # VIANDES
    "poulet",
    "steak",
    "dinde",
    "lardon",
    "porc",

    # POISSONS
    "saumon",
    "thon",
    "truite",

    # LEGUMES
    "courgette",
    "brocoli",
    "epinard",
    "aubergine",
    "concombre",
    "tomate",
    "avocat",
    "haricot vert",
    "carotte",
    "chou-fleur",
    "champignon",

    # FECULENTS
    "riz blanc",
    "pates",
    "pain",
    "semoule",

    # PRODUITS LAITIERS
    "comte",
    "emmental",
    "cheddar",

    # OEUFS
    "oeuf",

    # LEGUMINEUSES
    "lentille",
    "pois chiche",

    # FRUITS
    "fraise",
    "melon",
    "ananas",
    "clementine",
    "kiwi",

    # MATIERES GRASSES
    "huile d olive",
    "beurre",
]

for mot in recherches:
    cursor.execute("""
        SELECT id, nom, categorie_id, digestibilite, calories_100g,
               proteines_g, glucides_g, lipides_g
        FROM aliments
        WHERE LOWER(nom) LIKE ?
        ORDER BY nom
        LIMIT 5
    """, (f"%{mot.lower()}%",))

    resultats = cursor.fetchall()
    print(f"\n--- {mot.upper()} ---")
    for r in resultats:
        print(f"  [{r[0]:4d}] {r[1]:<55} cat:{r[2]} digest:{r[3]} {r[4]:.0f}kcal P:{r[5]:.1f} G:{r[6]:.1f} L:{r[7]:.1f}")

conn.close()
