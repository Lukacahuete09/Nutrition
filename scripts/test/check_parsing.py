# check_parsing.py
import pandas as pd
import os

CIQUAL_LOCAL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "create_db", "data", "ciqual_2020.xls"
)

df = pd.read_excel(CIQUAL_LOCAL, sheet_name=0, dtype=str)

# Afficher les valeurs brutes de la colonne calories
# pour les 20 premiers aliments avec calories = 0
col_cal = "Energie, Règlement UE N° 1169/2011 (kcal/100 g)"

print(f"Colonne calories : {col_cal}")
print(f"\nExemples de valeurs brutes :")

masque_zero = df[col_cal].apply(
    lambda x: str(x).strip().replace(",", ".").replace("<", "")
              .replace("-", "0").replace(" ", "") == "0"
              or str(x).strip() in ["-", "", "nan", "0"]
)

print(f"Lignes avec valeur nulle ou zero : {masque_zero.sum()}")
print(f"\n20 premiers exemples :")
for _, row in df[masque_zero].head(20).iterrows():
    print(f"  {row['alim_nom_fr']:<50} -> brut : {repr(row[col_cal])}")
