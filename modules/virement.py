"""
virement.py — Logique métier des virements bancaires
"""
import datetime
from db.config import get_connection


def get_all_virements(filtre: str = "") -> list[dict]:
    conn = get_connection()
    cur  = conn.cursor()
    if filtre.strip():
        p = f"%{filtre.strip()}%"
        cur.execute("""
            SELECT v.n_virement,v.type_action,v.date_virement,
                   v.n_compte,v.n_compte_dest,v.montant_ancien,v.montant_nouv,
                   c.nomclient
            FROM virement v LEFT JOIN client c ON c.n_compte=v.n_compte
            WHERE v.n_compte ILIKE %s OR v.n_compte_dest ILIKE %s
            ORDER BY v.n_virement DESC
        """, (p, p))
    else:
        cur.execute("""
            SELECT v.n_virement,v.type_action,v.date_virement,
                   v.n_compte,v.n_compte_dest,v.montant_ancien,v.montant_nouv,
                   c.nomclient
            FROM virement v LEFT JOIN client c ON c.n_compte=v.n_compte
            ORDER BY v.n_virement DESC
        """)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"n_virement": r[0], "type_action": r[1], "date_virement": str(r[2]),
             "n_compte": r[3], "n_compte_dest": r[4] or "—",
             "montant_ancien": float(r[5] or 0), "montant_nouv": float(r[6] or 0),
             "nomclient": r[7] or ""} for r in rows]


def effectuer_virement(src: str, dest: str, montant: float) -> int:
    if montant <= 0:
        raise ValueError("Le montant doit être supérieur à zéro.")
    if src == dest:
        raise ValueError("Les comptes source et destination doivent être différents.")
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT solde FROM client WHERE n_compte=%s FOR UPDATE", (src,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Compte source '{src}' introuvable.")
        solde = float(row[0])
        if solde < montant:
            raise ValueError(f"Solde insuffisant : {solde:,.2f} Ar disponibles, {montant:,.2f} Ar demandés.")
        cur.execute("SELECT n_compte FROM client WHERE n_compte=%s", (dest,))
        if not cur.fetchone():
            raise ValueError(f"Compte destination '{dest}' introuvable.")
        cur.execute("""
            INSERT INTO virement(type_action,date_virement,n_compte,n_compte_dest,montant_ancien,montant_nouv)
            VALUES(%s,%s,%s,%s,%s,%s) RETURNING n_virement
        """, ('ajout', datetime.datetime.now(), src, dest, solde, montant))
        nv = cur.fetchone()[0]
        conn.commit()
        return nv
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def modifier_virement(n_virement: int, nouveau_montant: float) -> None:
    if nouveau_montant <= 0:
        raise ValueError("Le montant doit être supérieur à zéro.")
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("UPDATE virement SET montant_nouv=%s WHERE n_virement=%s",
                    (nouveau_montant, n_virement))
        if cur.rowcount == 0:
            raise ValueError(f"Virement n°{n_virement} introuvable.")
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def supprimer_virement(n_virement: int) -> None:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM virement WHERE n_virement=%s", (n_virement,))
        if cur.rowcount == 0:
            raise ValueError(f"Virement n°{n_virement} introuvable.")
        conn.commit()
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def get_stats_virements() -> dict:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT COUNT(*),
               COUNT(*) FILTER(WHERE type_action='ajout'),
               COUNT(*) FILTER(WHERE type_action='modification'),
               COUNT(*) FILTER(WHERE type_action='suppression'),
               COALESCE(SUM(montant_nouv) FILTER(WHERE type_action='ajout'),0)
        FROM virement
    """)
    r = cur.fetchone()
    cur.close(); conn.close()
    return {"total": int(r[0]), "ajouts": int(r[1]), "modifs": int(r[2]),
            "supprs": int(r[3]), "montant_total": float(r[4])}
