"""
client.py — Module de gestion des clients
CRUD complet sur la table `client`
"""

from db.config import get_connection


# ─────────────────────────────────────────────────────
#  LECTURE
# ─────────────────────────────────────────────────────

def get_all_clients() -> list[dict]:
    """Retourne tous les clients triés par n_compte."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT n_compte, nomclient, solde FROM client ORDER BY n_compte")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"n_compte": r[0], "nomclient": r[1], "solde": float(r[2])} for r in rows]


def get_client_by_compte(n_compte: str) -> dict | None:
    """Retourne un client par son numéro de compte, ou None."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT n_compte, nomclient, solde FROM client WHERE n_compte = %s", (n_compte,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {"n_compte": row[0], "nomclient": row[1], "solde": float(row[2])}
    return None


def search_clients(keyword: str) -> list[dict]:
    """Recherche des clients par nom ou numéro de compte (ILIKE)."""
    conn = get_connection()
    cursor = conn.cursor()
    pattern = f"%{keyword}%"
    cursor.execute(
        "SELECT n_compte, nomclient, solde FROM client "
        "WHERE nomclient ILIKE %s OR n_compte ILIKE %s ORDER BY n_compte",
        (pattern, pattern)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [{"n_compte": r[0], "nomclient": r[1], "solde": float(r[2])} for r in rows]


# ─────────────────────────────────────────────────────
#  ÉCRITURE
# ─────────────────────────────────────────────────────

def ajouter_client(n_compte: str, nomclient: str, solde: float = 0.0) -> None:
    """Insère un nouveau client."""
    if not n_compte.strip() or not nomclient.strip():
        raise ValueError("N° compte et nom client sont obligatoires.")
    if solde < 0:
        raise ValueError("Le solde initial ne peut pas être négatif.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO client (n_compte, nomclient, solde) VALUES (%s, %s, %s)",
            (n_compte.strip(), nomclient.strip(), solde)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise ValueError(f"Le compte '{n_compte}' existe déjà.")
        raise RuntimeError(f"Erreur lors de l'ajout du client : {e}")
    finally:
        cursor.close()
        conn.close()


def modifier_client(n_compte: str, nomclient: str, solde: float) -> None:
    """Met à jour le nom et le solde d'un client existant."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE client SET nomclient = %s, solde = %s WHERE n_compte = %s",
            (nomclient.strip(), solde, n_compte)
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Client '{n_compte}' introuvable.")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erreur modification client : {e}")
    finally:
        cursor.close()
        conn.close()


def supprimer_client(n_compte: str) -> None:
    """Supprime un client (vérifie l'absence de virements liés)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Vérifier les virements associés
        cursor.execute(
            "SELECT COUNT(*) FROM virement WHERE n_compte = %s OR n_compte_dest = %s",
            (n_compte, n_compte)
        )
        count = cursor.fetchone()[0]
        if count > 0:
            raise ValueError(
                f"Impossible de supprimer : {count} virement(s) lié(s) à ce compte."
            )

        cursor.execute("DELETE FROM client WHERE n_compte = %s", (n_compte,))
        if cursor.rowcount == 0:
            raise ValueError(f"Client '{n_compte}' introuvable.")
        conn.commit()
    except ValueError:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erreur suppression client : {e}")
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────
#  STATISTIQUES
# ─────────────────────────────────────────────────────

def get_stats_clients() -> dict:
    """Retourne des statistiques sur les clients."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*)           AS nb_clients,
            SUM(solde)         AS solde_total,
            AVG(solde)         AS solde_moyen,
            MAX(solde)         AS solde_max,
            MIN(solde)         AS solde_min
        FROM client
    """)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return {
        "nb_clients":   int(row[0]) if row[0] else 0,
        "solde_total":  float(row[1]) if row[1] else 0.0,
        "solde_moyen":  float(row[2]) if row[2] else 0.0,
        "solde_max":    float(row[3]) if row[3] else 0.0,
        "solde_min":    float(row[4]) if row[4] else 0.0,
    }
