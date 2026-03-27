"""
audit.py — Lecture et gestion de la table audit_virement
"""
from db.config import get_connection


def get_all_audits(filtre_action: str = "", filtre_compte: str = "") -> list[dict]:
    conn = get_connection()
    cur  = conn.cursor()
    conds, params = [], []
    if filtre_action and filtre_action != "Tous":
        conds.append("type_action=%s"); params.append(filtre_action)
    if filtre_compte.strip():
        conds.append("n_compte ILIKE %s"); params.append(f"%{filtre_compte.strip()}%")
    where = ("WHERE " + " AND ".join(conds)) if conds else ""
    cur.execute(f"""
        SELECT id_audit,type_action,date_operation,n_compte,
               n_virement,montant_ancien,montant_nouv,utilisateur
        FROM audit_virement {where} ORDER BY id_audit DESC
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"id_audit": r[0], "type_action": r[1], "date_operation": str(r[2]),
             "n_compte": r[3] or "—", "n_virement": r[4] or "—",
             "montant_ancien": float(r[5] or 0), "montant_nouv": float(r[6] or 0),
             "utilisateur": r[7] or "ADMIN"} for r in rows]


def get_stats_audit() -> dict:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT COUNT(*),
               COUNT(*) FILTER(WHERE type_action='ajout'),
               COUNT(*) FILTER(WHERE type_action='modification'),
               COUNT(*) FILTER(WHERE type_action='suppression')
        FROM audit_virement
    """)
    r = cur.fetchone()
    cur.close(); conn.close()
    return {"total": int(r[0]), "insertions": int(r[1]),
            "modifications": int(r[2]), "suppressions": int(r[3])}


def vider_audit() -> int:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM audit_virement")
        count = cur.rowcount
        conn.commit()
        return count
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def export_audit_csv(filepath: str) -> int:
    import csv
    rows = get_all_audits()
    if not rows:
        return 0
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    return len(rows)
