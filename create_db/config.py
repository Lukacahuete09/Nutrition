# ============================================================
# CONFIGURATION — CREATE DB
# ============================================================

import os

BASE_DIR     = os.path.dirname(__file__)
DATA_DIR     = os.path.join(BASE_DIR, "data")
CIQUAL_LOCAL = os.path.join(DATA_DIR, "ciqual_2020.xls")
DB_PATH      = os.path.join(DATA_DIR, "nutrition.db")

