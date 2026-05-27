# ============================================================
# CONFIGURATION — MODULE OPTIMISATION
# ============================================================

import os

BASE_DIR          = os.path.dirname(os.path.abspath(__file__))
DATA_DIR          = os.path.join(BASE_DIR, "data")
EXCEL_CONFIG_PATH = os.path.join(DATA_DIR, "athlete_config.xlsm")
OUTPUT_DIR        = os.path.join(BASE_DIR, "output")

# Chemin vers la base de donnees generee par create_db
DB_PATH = os.path.join(
    BASE_DIR, "..", "create_db", "data", "nutrition.db"
)
