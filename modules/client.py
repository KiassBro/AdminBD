"""
client.py — CRUD clients + génération automatique du numéro de compte
"""
from db.config import get_connection


def get_next_numero() -> str:
    """Génère automatiquement le prochain numéro de compte.
    Ex : si le dernier est C005, retourne C006.
    """
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT n_compte FROM client
        WHERE n_compte ~ '^C[0-9]+$'
        ORDER BY CAST(SUBSTRING(n_compte FROM 2) AS INTEGER) DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        num = int(row[0][1:]) + 1
    else:
        num = 1
    return f"C{num:03d}"


def get_all_clients() -> list[dict]:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT n_compte, nomclient, solde FROM client ORDER BY n_compte")
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [{"n_compte": r[0], "nomclient": r[1], "solde": float(r[2])} for r in rows]


def get_client(n_compte: str) -> dict | None:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT n_compte,nomclient,solde FROM client WHERE n_compte=%s", (n_compte,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return {"n_compte": row[0], "nomclient": row[1], "solde": float(row[2])} if row else None


def ajouter_client(n_compte: str, nomclient: str, solde: float = 0.0) -> None:
    if not n_compte.strip() or not nomclient.strip():
        raise ValueError("N° compte et nom sont obligatoires.")
    if solde < 0:
        raise ValueError("Le solde initial ne peut pas être négatif.")
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("INSERT INTO client VALUES(%s,%s,%s)",
                    (n_compte.strip(), nomclient.strip(), solde))
        conn.commit()
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise ValueError(f"Le compte '{n_compte}' existe déjà.")
        raise RuntimeError(str(e))
    finally:
        cur.close(); conn.close()


def modifier_client(n_compte: str, nomclient: str, solde: float) -> None:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("UPDATE client SET nomclient=%s, solde=%s WHERE n_compte=%s",
                    (nomclient.strip(), solde, n_compte))
        if cur.rowcount == 0:
            raise ValueError(f"Client '{n_compte}' introuvable.")
        conn.commit()
    except Exception as e:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def supprimer_client(n_compte: str) -> None:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM virement WHERE n_compte=%s OR n_compte_dest=%s",
                    (n_compte, n_compte))
        if cur.fetchone()[0] > 0:
            raise ValueError("Ce client a des virements liés. Suppression impossible.")
        cur.execute("DELETE FROM client WHERE n_compte=%s", (n_compte,))
        if cur.rowcount == 0:
            raise ValueError(f"Client '{n_compte}' introuvable.")
        conn.commit()
    except Exception as e:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()


def get_stats_clients() -> dict:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT COUNT(*), COALESCE(SUM(solde),0),
               COALESCE(AVG(solde),0), COALESCE(MAX(solde),0), COALESCE(MIN(solde),0)
        FROM client
    """)
    r = cur.fetchone()
    cur.close(); conn.close()
    return {"nb": int(r[0]), "total": float(r[1]), "moyen": float(r[2]),
            "max": float(r[3]), "min": float(r[4])}
