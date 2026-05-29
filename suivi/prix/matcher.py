# ============================================================
# MATCHING INGRÉDIENTS → PRODUITS MAGASIN
# suivi/prix/matcher.py
# ============================================================

import sys
import re
import sqlite3
from pathlib import Path
sys.dont_write_bytecode = True

# ------------------------------------------------------------
# RACINE DU PROJET
# suivi/prix/matcher.py → suivi/prix/ → suivi/ → NUTRITION/
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from config import (
    RECETTES_DB,
    NUTRITION_DB,
    MAGASIN_FALLBACK,       
    CACHE_PRIX_JOURS,
)
from suivi.prix.api.cache_manager    import CacheManager
from suivi.prix.api.piloterr_client  import PiloterrClient 


# ------------------------------------------------------------
# MOTS PARASITES — Anglais ET Français
# ------------------------------------------------------------
MOTS_PARASITES = {
    "g", "kg", "ml", "cl", "l",
    "fresh", "frozen", "cooked", "raw", "whole",
    "large", "small", "medium", "extra",
    "of", "the", "with", "and", "or",
    "frais", "fraiche", "cuit", "cuite", "cru", "crue",
    "entier", "entiere", "nature",
    "de", "du", "des", "le", "la", "les", "en", "au",
}

# ------------------------------------------------------------
# TRADUCTIONS — Anglais → Query française magasin
# ------------------------------------------------------------
TRADUCTIONS_EN_FR = {
    # ── VIANDES
    "chicken breast"       : "filet poulet",
    "chicken thigh"        : "cuisse poulet",
    "ground beef"          : "viande hachee boeuf",
    "beef"                 : "boeuf",
    "turkey breast"        : "filet dinde",
    "turkey"               : "dinde",
    "pork tenderloin"      : "filet mignon porc",
    "pork"                 : "porc",
    "bacon"                : "lardons",
    # ── POISSONS
    "salmon"               : "saumon atlantique",
    "tuna"                 : "thon naturel boite",
    "cod"                  : "cabillaud",
    "shrimp"               : "crevettes",
    # ── OEUFS & LAITIERS
    "egg"                  : "oeufs frais",
    "eggs"                 : "oeufs frais",
    "egg white"            : "blancs oeufs",
    "milk"                 : "lait demi ecreme",
    "greek yogurt"         : "yaourt grec",
    "yogurt"               : "yaourt nature",
    "cottage cheese"       : "fromage blanc",
    "cream cheese"         : "fromage frais",
    "butter"               : "beurre doux",
    "parmesan"             : "parmesan rape",
    "mozzarella"           : "mozzarella",
    "whey protein"         : "proteine whey",
    # ── FÉCULENTS & CÉRÉALES
    "white rice"           : "riz long grain",
    "brown rice"           : "riz complet",
    "oats"                 : "flocons avoine",
    "rolled oats"          : "flocons avoine",
    "quinoa"               : "quinoa blanc",
    "pasta"                : "pates",
    "spaghetti"            : "spaghetti",
    "bread"                : "pain complet",
    "whole wheat bread"    : "pain complet",
    "couscous"             : "couscous",
    "sweet potato"         : "patate douce",
    "potato"               : "pomme de terre",
    # ── LÉGUMINEUSES
    "lentils"              : "lentilles vertes",
    "chickpeas"            : "pois chiches",
    "black beans"          : "haricots noirs",
    "kidney beans"         : "haricots rouges",
    "white beans"          : "haricots blancs",
    # ── LÉGUMES
    "spinach"              : "epinards frais",
    "broccoli"             : "brocoli",
    "zucchini"             : "courgette",
    "carrot"               : "carotte",
    "onion"                : "oignon",
    "garlic"               : "ail",
    "tomato"               : "tomate",
    "bell pepper"          : "poivron",
    "cucumber"             : "concombre",
    "green beans"          : "haricots verts",
    "asparagus"            : "asperges",
    "mushroom"             : "champignons",
    "lettuce"              : "salade verte",
    "avocado"              : "avocat",
    # ── FRUITS
    "banana"               : "banane",
    "apple"                : "pomme",
    "orange"               : "orange",
    "strawberry"           : "fraises",
    "blueberry"            : "myrtilles",
    "mango"                : "mangue",
    # ── MATIÈRES GRASSES
    "olive oil"            : "huile olive",
    "coconut oil"          : "huile coco",
    "peanut butter"        : "beurre cacahuete",
    "almond butter"        : "puree amande",
    # ── FRUITS SECS & GRAINES
    "almonds"              : "amandes",
    "walnuts"              : "noix",
    "cashews"              : "noix cajou",
    "chia seeds"           : "graines chia",
    "flaxseed"             : "graines lin",
    "pumpkin seeds"        : "graines courge",
    # ── CONDIMENTS & AUTRES
    "honey"                : "miel",
    "granola"              : "granola",
    "dark chocolate"       : "chocolat noir",
    "soy sauce"            : "sauce soja",
}


# ============================================================
# CLASSE PRINCIPALE
# ============================================================
class Matcher:

    def __init__(self, magasin: str = MAGASIN_FALLBACK):  
        self.magasin = magasin
        self.cache   = CacheManager()
        self.client  = PiloterrClient(magasin=magasin)    

    # ----------------------------------------------------------
    # MÉTHODE PRINCIPALE
    # ----------------------------------------------------------
    def matcher_ingredient(self, nom_en: str, nom_fr: str = "") -> dict:
        """
        Trouve le meilleur produit en magasin.
        Retourne None si aucun produit trouvé.
        """
        query = self._construire_query(nom_en, nom_fr)
        if not query:
            print(f"[WARN] Query vide pour : {nom_en}")
            return None

        print(f"[MATCH] '{nom_en}' → query: '{query}'")

        # 1. Cache
        cached = self.cache.get(query, self.magasin)
        if cached:
            return {**cached, "depuis_cache": True}

        # 2. API Piloterr
        produits = self.client.rechercher_produit(query)
        if not produits:
            print(f"[WARN] Aucun produit trouvé pour : '{query}'")
            return None

        # 3. Sélection meilleur produit
        meilleur = self._selectionner_meilleur(produits, query)
        if not meilleur:
            return None

        # 4. Sauvegarde cache
        self.cache.set(query, self.magasin, meilleur)

        print(
            f"[OK]    '{query}' → {meilleur['nom'][:40]}"
            f" | {meilleur['prix_kg']:.2f} €/kg"
        )

        return {**meilleur, "query": query, "depuis_cache": False}

    # ----------------------------------------------------------
    # CONSTRUCTION QUERY
    # ----------------------------------------------------------
    def _construire_query(self, nom_en: str, nom_fr: str = "") -> str:
        nom_en_clean = nom_en.strip().lower() if nom_en else ""
        nom_fr_clean = nom_fr.strip().lower() if nom_fr else ""

        # 1. Traduction directe EN → FR
        if nom_en_clean in TRADUCTIONS_EN_FR:
            return TRADUCTIONS_EN_FR[nom_en_clean]

        # 2. Recherche partielle
        for key, val in TRADUCTIONS_EN_FR.items():
            if key in nom_en_clean:
                return val

        # 3. nom_fr nettoyé
        if nom_fr_clean:
            query = self._nettoyer_nom(nom_fr_clean)
            if query:
                return query

        # 4. Fallback nom_en nettoyé
        if nom_en_clean:
            query = self._nettoyer_nom(nom_en_clean)
            if query:
                return query

        return ""

    def _nettoyer_nom(self, nom: str) -> str:
        nom  = re.sub(r'\d+[\.,]?\d*\s*(g|kg|ml|cl|l|cup|cups|oz|lb)?', '', nom)
        nom  = re.sub(r"[^\w\s]", " ", nom)
        mots = [
            m for m in nom.split()
            if m.lower() not in MOTS_PARASITES and len(m) > 1
        ]
        return " ".join(mots).strip()

    # ----------------------------------------------------------
    # SÉLECTION DU MEILLEUR PRODUIT
    # ----------------------------------------------------------
    def _selectionner_meilleur(self, produits: list, query: str) -> dict:
        scores     = []
        mots_query = set(query.lower().split())

        for produit in produits:
            prix_kg = produit.get("prix_kg", 0)
            nom     = produit.get("nom", "").lower()

            if not prix_kg or prix_kg <= 0:
                continue
            if prix_kg > 150:
                continue

            mots_nom         = set(nom.split())
            mots_communs     = mots_query & mots_nom
            score_pertinence = len(mots_communs) / max(len(mots_query), 1)
            score_prix       = 1 / (1 + prix_kg / 20)
            score_final      = (score_pertinence * 0.7) + (score_prix * 0.3)

            scores.append((score_final, produit))

        if not scores:
            return None

        scores.sort(key=lambda x: x[0], reverse=True)
        meilleur_score, meilleur_produit = scores[0]

        return {**meilleur_produit, "score": round(meilleur_score, 4)}

    # ----------------------------------------------------------
    # MATCHING RECETTE COMPLÈTE
    # ----------------------------------------------------------
    def matcher_ingredients_recette(self, recette_id: int) -> list:
        conn             = sqlite3.connect(RECETTES_DB)
        conn.row_factory = sqlite3.Row
        cursor           = conn.cursor()

        cursor.execute("""
            SELECT id, nom_fr, nom_en, quantite_g
            FROM recette_ingredients
            WHERE recette_id = ?
        """, (recette_id,))

        ingredients = cursor.fetchall()
        conn.close()

        resultats = []
        for ing in ingredients:
            resultat = self.matcher_ingredient(
                nom_en = ing["nom_en"] or "",
                nom_fr = ing["nom_fr"] or "",
            )
            resultats.append({
                "ingredient_id" : ing["id"],
                "nom_en"        : ing["nom_en"],
                "nom_fr"        : ing["nom_fr"],
                "quantite_g"    : ing["quantite_g"],
                "produit"       : resultat,
            })

        return resultats

    def close(self):
        self.cache.close()


# ============================================================
# TEST AUTONOME
# ============================================================
if __name__ == "__main__":
    print("\n[TEST] Matcher ingrédients\n")

    matcher = Matcher(magasin=MAGASIN_FALLBACK) 

    tests = [
        ("chicken breast",  "blanc de poulet"),
        ("white rice",      "riz blanc"),
        ("oats",            "flocons d'avoine"),
        ("eggs",            "oeufs"),
        ("salmon",          "saumon"),
        ("greek yogurt",    "yaourt grec"),
        ("olive oil",       "huile d'olive"),
        ("sweet potato",    "patate douce"),
    ]

    for nom_en, nom_fr in tests:
        resultat = matcher.matcher_ingredient(nom_en, nom_fr)
        if resultat:
            print(
                f"{nom_en:<20}"
                f" → {resultat.get('nom', '')[:35]:<35}"
                f" | {resultat['prix_kg']:.2f} €/kg"
                f" | score: {resultat['score']:.2f}"
                f" | {'cache' if resultat['depuis_cache'] else 'API'}"
            )
        else:
            print(f"{nom_en:<20} → aucun produit trouvé")

    matcher.close()
