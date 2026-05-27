# ============================================================
# REGLES DE DIGESTIBILITE AUTOMATIQUE
# ============================================================
#
# Priorite : low > high > medium (par defaut)
#
# Sources :
#   - Classification FODMAP (Monash University)
#   - Jeukendrup — Nutrition for endurance sports
#   - IOC Consensus Statement on Sports Nutrition
# ============================================================

KEYWORDS_LOW = [
    "ail", "oignon cru", "echalote",
    "chou blanc cru", "chou rouge cru",
    "chou de bruxelles", "chou-fleur cru",
    "kale cru", "artichaut",
    "topinambour",
    "saucisson", "salami", "bacon", "rillettes",
    "pate de campagne", "merguez", "chipolata",
    "fume", "pane",
    "haricots secs", "pois chiches secs",
    "lentilles crues", "feves crues",
    "soja cru", "lupins crus",
    "datte", "pruneau", "raisin sec",
    "abricot sec", "figue seche",
    "creme fraiche", "mascarpone",
    "lait concentre", "glace",
    "son de ble", "son d avoine",
    "pain integral", "germe de ble",
    "riz sauvage",
]

KEYWORDS_HIGH = [
    "vapeur", "mollet",
    "blanc de poulet", "filet de dinde",
    "escalope de veau", "lapin",
    "cabillaud", "lieu noir", "merlan",
    "sole", "carrelet", "tilapia", "colin",
    "concombre", "courgette", "laitue",
    "mache", "roquette", "tomate",
    "patate douce", "potiron", "courge",
    "riz blanc cuit", "riz basmati cuit",
    "pates blanches cuites",
    "pomme de terre cuite",
    "semoule cuite", "couscous cuit",
    "yaourt grec", "skyr", "kefir",
    "fromage blanc", "cottage",
    "blanc d oeuf",
    "huile d olive", "huile de colza",
    "huile de lin", "huile de noix",
    "lentilles corail", "edamame",
    "haricots conserve",
    "pois chiches conserve",
    "banane mure", "melon", "pasteque",
    "orange", "kiwi", "mangue", "papaye",
]


def get_digestibilite(nom: str) -> str:
    """
    Retourne 'low', 'medium' ou 'high'
    selon les mots-cles presents dans le nom de l aliment.
    Priorite : low > high > medium.
    """
    nom_lower = nom.lower()

    for keyword in KEYWORDS_LOW:
        if keyword in nom_lower:
            return "low"

    for keyword in KEYWORDS_HIGH:
        if keyword in nom_lower:
            return "high"

    return "medium"
