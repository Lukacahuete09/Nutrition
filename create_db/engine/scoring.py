# ============================================================
# CALCUL DES SCORES NUTRITIONNELS ET DE LA DENSITE PROTEIQUE
# ============================================================
#
# Formule score nutritionnel :
#   score = (proteines * 0.40)
#         + (vitamine_c * 0.01)
#         + (vitamine_d * 0.50)
#         + (omega3     * 1.00)
#         - (calories   * 0.001)
#
# Sources :
#   - ISSN Position Stand 2023
#   - Loucks et al. — energie disponible
#   - Vitamine D et performance (Dahlquist et al.)
# ============================================================

import sqlite3


def compute_densite_proteique(proteines: float, calories: float) -> float:
    """
    Densite proteique = proteines / calories.
    Retourne 0 si calories nulle.
    """
    if calories > 0:
        return round(proteines / calories, 4)
    return 0.0


def compute_score_nutritionnel(
    proteines  : float,
    vitamine_c : float,
    vitamine_d : float,
    omega3     : float,
    calories   : float,
) -> float:
    """
    Score nutritionnel composite oriente performance sportive.
    """
    score = (
        (proteines  * 0.40) +
        (vitamine_c * 0.01) +
        (vitamine_d * 0.50) +
        (omega3     * 1.00) -
        (calories   * 0.001)
    )
    return round(score, 4)


def update_scores(conn: sqlite3.Connection) -> None:
    """
    Calcule et met a jour densite_proteique et score_nutritionnel
    pour tous les aliments de la base.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, proteines_g, vitamine_c_mg,
               vitamine_d_ug, omega3_g, calories_100g
        FROM aliments
    """)
    rows = cursor.fetchall()

    for row in rows:
        id_, prot, vitC, vitD, omega3, kcal = (
            row["id"], row["proteines_g"], row["vitamine_c_mg"],
            row["vitamine_d_ug"], row["omega3_g"], row["calories_100g"]
        )

        densite = compute_densite_proteique(prot, kcal)
        score   = compute_score_nutritionnel(prot, vitC, vitD, omega3, kcal)

        cursor.execute("""
            UPDATE aliments
            SET densite_proteique  = ?,
                score_nutritionnel = ?
            WHERE id = ?
        """, (densite, score, id_))

    conn.commit()
    print(f"[OK] Scores calcules pour {len(rows)} aliments.")
