"""
audit.py — Module de gestion de la table d'audit
Lecture de audit_virement remplie automatiquement par les triggers PostgreSQL
"""

from db.config import get_connection


# ─────────────────────────────────────────────────────
#  LECTURE
# ─────────────────────────────────────────────────────

def get_all_audits(filtre_action: str = "", filtre_compte: str = "") -> list[dict]:
    """
    Retourne toutes les entrées d'audit.
    filtres optionnels : type d'action et/ou numéro de compte.
    """
    conn = get_connection()
    cursor = conn.cursor()

    conditions = []
    params = []

    if filtre_action and filtre_action != "Tous":
        conditions.append("type_action = %s")
        params.append(filtre_action)

    if filtre_compte.strip():
        conditions.append("n_compte ILIKE %s")
        params.append(f"%{filtre_compte.strip()}%")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    cursor.execute(f"""
        SELECT id_audit, type_action, date_operation, n_compte,
               n_virement, montant_ancien, montant_nouv, utilisateur
        FROM audit_virement
        {where}
        ORDER BY id_audit DESC
    """, params)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "id_audit":       r[0],
            "type_action":    r[1],
            "date_operation": str(r[2]),
            "n_compte":       r[3] or "—",
            "n_virement":     r[4] or "—",
            "montant_ancien": float(r[5]) if r[5] is not None else 0.0,
            "montant_nouv":   float(r[6]) if r[6] is not None else 0.0,
            "utilisateur":    r[7] or "ADMIN",
        }
        for r in rows
    ]


def get_stats_audit() -> dict:
    """
    Retourne les compteurs d'opérations dans la table d'audit.
    Utilisé pour afficher les indicateurs dans le tableau de bord.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*)                                            AS total,
            COUNT(*) FILTER (WHERE type_action = 'ajout')      AS insertions,
            COUNT(*) FILTER (WHERE type_action = 'modification') AS modifications,
            COUNT(*) FILTER (WHERE type_action = 'suppression') AS suppressions
        FROM audit_virement
    """)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return {
        "total":         int(row[0]),
        "insertions":    int(row[1]),
        "modifications": int(row[2]),
        "suppressions":  int(row[3]),
    }


def get_audit_by_compte(n_compte: str) -> list[dict]:
    """Retourne toutes les entrées d'audit pour un compte donné."""
    return get_all_audits(filtre_compte=n_compte)


# ─────────────────────────────────────────────────────
#  GESTION
# ─────────────────────────────────────────────────────

def vider_audit() -> int:
    """
    Supprime toutes les entrées d'audit.
    Retourne le nombre de lignes supprimées.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM audit_virement")
        count = cursor.rowcount
        conn.commit()
        return count
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erreur lors du vidage de l'audit : {e}")
    finally:
        cursor.close()
        conn.close()


def export_audit_csv(filepath: str) -> int:
    """
    Exporte la table d'audit dans un fichier CSV.
    Retourne le nombre de lignes exportées.
    """
    import csv
    rows = get_all_audits()
    if not rows:
        return 0

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)
