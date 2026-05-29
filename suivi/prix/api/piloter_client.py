import requests
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.resolve()))

from config import PILOTERR_API_KEY
from suivi.prix.api.base_client import BaseMarketClient


class PiloterClient(BaseMarketClient):
    """
    Client Piloterr unifié pour Leclerc et Auchan.
    Documentation : https://piloterr.com/docs
    """

    BASE_URL   = "https://piloterr.com/api/v2"
    HEADERS    = {"x-api-key": None}  # Injecté à l'init

    # Endpoints disponibles
    ENDPOINTS = {
        "leclerc_search"  : "/leclerc/search",
        "leclerc_product" : "/leclerc/product",
        "auchan_search"   : "/auchan/search",
        "auchan_product"  : "/auchan/product",
    }

    def __init__(self, magasin: str = "leclerc"):
        """
        magasin : "leclerc" ou "auchan"
        """
        if magasin not in ("leclerc", "auchan"):
            raise ValueError(f"Magasin inconnu : {magasin}")

        self.magasin = magasin
        self.HEADERS = {"x-api-key": PILOTERR_API_KEY}

    # ----------------------------------------------------------
    # RECHERCHE PRODUIT PAR MOT-CLÉ
    # ----------------------------------------------------------
    def rechercher_produit(self, query: str) -> list[dict]:
        """
        Recherche un ingrédient dans le magasin choisi.

        Retourne :
        [
            {
                "nom"        : "Filet de poulet Label Rouge",
                "prix_kg"    : 9.50,
                "prix_unite" : 4.75,
                "unite"      : "500g",
                "url"        : "https://...",
                "image"      : "https://...",
                "magasin"    : "leclerc",
                "produit_id" : "abc123",
            },
            ...
        ]
        """
        endpoint = self.ENDPOINTS[f"{self.magasin}_search"]

        try:
            response = requests.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self.HEADERS,
                params={"query": query},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            return self._normaliser_recherche(data)

        except requests.exceptions.Timeout:
            print(f"[WARN] Timeout Piloterr pour : {query}")
            return []
        except requests.exceptions.HTTPError as e:
            print(f"[ERREUR] Piloterr HTTP {e.response.status_code} : {query}")
            return []

    # ----------------------------------------------------------
    # RÉCUPÉRATION PRODUIT PAR ID
    # ----------------------------------------------------------
    def get_produit_par_id(self, produit_id: str) -> dict:
        endpoint = self.ENDPOINTS[f"{self.magasin}_product"]

        try:
            response = requests.get(
                f"{self.BASE_URL}{endpoint}",
                headers=self.HEADERS,
                params={"id": produit_id},
                timeout=10,
            )
            response.raise_for_status()
            return self._normaliser_produit(response.json())

        except requests.exceptions.RequestException as e:
            print(f"[ERREUR] Piloterr produit {produit_id} : {e}")
            return {}

    # ----------------------------------------------------------
    # NORMALISATION — UNIFORMISE LA RÉPONSE JSON
    # ----------------------------------------------------------
    def _normaliser_recherche(self, data: dict) -> list[dict]:
        """
        Normalise la réponse JSON Piloterr en format uniforme.
        À adapter selon la vraie structure JSON Piloterr.
        """
        produits = []
        items    = data.get("data", data.get("results", []))

        for item in items:
            prix_kg = self._calculer_prix_kg(item)
            if prix_kg is None:
                continue

            produits.append({
                "nom"        : item.get("name", ""),
                "prix_kg"    : prix_kg,
                "prix_unite" : item.get("price", 0),
                "unite"      : item.get("unit", ""),
                "url"        : item.get("url", ""),
                "image"      : item.get("image", ""),
                "magasin"    : self.magasin,
                "produit_id" : str(item.get("id", "")),
            })

        return produits

    def _normaliser_produit(self, data: dict) -> dict:
        item    = data.get("data", data)
        prix_kg = self._calculer_prix_kg(item)

        return {
            "nom"        : item.get("name", ""),
            "prix_kg"    : prix_kg or 0,
            "prix_unite" : item.get("price", 0),
            "unite"      : item.get("unit", ""),
            "url"        : item.get("url", ""),
            "image"      : item.get("image", ""),
            "magasin"    : self.magasin,
            "produit_id" : str(item.get("id", "")),
        }

    def _calculer_prix_kg(self, item: dict) -> float | None:
        """
        Tente de ramener le prix à un prix/kg normalisé.
        """
        # Piloterr expose souvent price_per_kg directement
        if item.get("price_per_kg"):
            return round(float(item["price_per_kg"]), 3)

        prix  = item.get("price")
        poids = item.get("weight_g") or item.get("quantity_g")

        if prix and poids and float(poids) > 0:
            return round(float(prix) / (float(poids) / 1000), 3)

        return None