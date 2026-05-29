from abc import ABC, abstractmethod

class BaseMarketClient(ABC):
    """
    Interface commune à tous les clients API magasin.
    Garantit que Leclerc et Auchan ont la même signature.
    """

    @abstractmethod
    def rechercher_produit(self, query: str) -> list[dict]:
        """
        Recherche un produit par mot-clé.
        Retourne une liste de produits avec prix.
        """
        pass

    @abstractmethod
    def get_produit_par_id(self, produit_id: str) -> dict:
        """
        Récupère un produit par son identifiant magasin.
        """
        pass
