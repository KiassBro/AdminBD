"""
virement.py — Module de gestion des virements bancaires
Formule : Nouveau solde = Ancien solde - Montant  (géré par trigger PostgreSQL)
"""

import datetime
from db.config import get_connection


# ─────────────────────────────────────────────────────
#  LECTURE
# ─────────────────────────────────────────────────────

def get_all_virements(filtre_compte: str = "") -> list[dict]:
    """Retourne tous les virements, avec filtre optionnel par compte."""
    conn = get_connection()
    cursor = conn.cursor()

    if filtre_compte.strip():
        pattern = f"%{filtre_compte.strip()}%"
        cursor.execute("""
            SELECT v.n_virement, v.type_action, v.date_virement,
                   v.n_compte, v.n_compte_dest, v.montant_ancien, v.montant_nouv,
                   c.nomclient
            FROM virement v
            LEFT JOIN client c ON c.n_compte = v.n_compte
            WHERE v.n_compte ILIKE %s OR v.n_compte_dest ILIKE %s
            ORDER BY v.n_virement DESC
        """, (pattern, pattern))
    else:
        cursor.execute("""
            SELECT v.n_virement, v.type_action, v.date_virement,
                   v.n_compte, v.n_compte_dest, v.montant_ancien, v.montant_nouv,
                   c.nomclient
            FROM virement v
            LEFT JOIN client c ON c.n_compte = v.n_compte
            ORDER BY v.n_virement DESC
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "n_virement":     r[0],
            "type_action":    r[1],
            "date_virement":  str(r[2]),
            "n_compte":       r[3],
            "n_compte_dest":  r[4] or "—",
            "montant_ancien": float(r[5]) if r[5] else 0.0,
            "montant_nouv":   float(r[6]) if r[6] else 0.0,
            "nomclient":      r[7] or "",
        })
    return result


def get_virement_by_id(n_virement: int) -> dict | None:
    """Retourne un virement par son identifiant."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT n_virement, type_action, date_virement, n_compte, n_compte_dest, "
        "montant_ancien, montant_nouv FROM virement WHERE n_virement = %s",
        (n_virement,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {
            "n_virement":     row[0],
            "type_action":    row[1],
            "date_virement":  str(row[2]),
            "n_compte":       row[3],
            "n_compte_dest":  row[4],
            "montant_ancien": float(row[5]) if row[5] else 0.0,
            "montant_nouv":   float(row[6]) if row[6] else 0.0,
        }
    return None


# ─────────────────────────────────────────────────────
#  OPÉRATIONS MÉTIER
# ─────────────────────────────────────────────────────

def effectuer_virement(n_compte_src: str, n_compte_dest: str, montant: float) -> int:
    """
    Effectue un virement bancaire entre deux comptes.
    - Vérifie le solde suffisant sur le compte source
    - Insère dans la table virement
    - Le trigger trg_update_solde met à jour les soldes automatiquement
    - Le trigger trg_audit_insert enregistre l'opération dans audit_virement

    Retourne le n_virement créé.
    """
    if montant <= 0:
        raise ValueError("Le montant doit être supérieur à zéro.")
    if n_compte_src == n_compte_dest:
        raise ValueError("Les comptes source et destination doivent être différents.")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Vérifier compte source
        cursor.execute("SELECT solde FROM client WHERE n_compte = %s FOR UPDATE", (n_compte_src,))
        row_src = cursor.fetchone()
        if not row_src:
            raise ValueError(f"Compte source '{n_compte_src}' introuvable.")
        solde_actuel = float(row_src[0])

        if solde_actuel < montant:
            raise ValueError(
                f"Solde insuffisant : {solde_actuel:,.2f} Ar disponibles, "
                f"{montant:,.2f} Ar demandés."
            )

        # Vérifier compte destination
        cursor.execute("SELECT n_compte FROM client WHERE n_compte = %s", (n_compte_dest,))
        if not cursor.fetchone():
            raise ValueError(f"Compte destination '{n_compte_dest}' introuvable.")

        # Insérer le virement (les triggers s'occupent du reste)
        date_now = datetime.datetime.now()
        cursor.execute("""
            INSERT INTO virement (type_action, date_virement, n_compte, n_compte_dest, montant_ancien, montant_nouv)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING n_virement
        """, ('ajout', date_now, n_compte_src, n_compte_dest, solde_actuel, montant))

        n_virement = cursor.fetchone()[0]
        conn.commit()
        return n_virement

    except (ValueError, RuntimeError):
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erreur lors du virement : {e}")
    finally:
        cursor.close()
        conn.close()


def modifier_virement(n_virement: int, nouveau_montant: float) -> None:
    """
    Modifie le montant d'un virement existant.
    Le trigger trg_audit_update enregistre la modification automatiquement.
    """
    if nouveau_montant <= 0:
        raise ValueError("Le montant doit être supérieur à zéro.")

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE virement SET montant_nouv = %s WHERE n_virement = %s",
            (nouveau_montant, n_virement)
        )
        if cursor.rowcount == 0:
            raise ValueError(f"Virement n°{n_virement} introuvable.")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erreur modification virement : {e}")
    finally:
        cursor.close()
        conn.close()


def supprimer_virement(n_virement: int) -> None:
    """
    Supprime un virement.
    Le trigger trg_audit_delete enregistre la suppression automatiquement.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM virement WHERE n_virement = %s", (n_virement,))
        if cursor.rowcount == 0:
            raise ValueError(f"Virement n°{n_virement} introuvable.")
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erreur suppression virement : {e}")
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────
#  STATISTIQUES
# ─────────────────────────────────────────────────────

def get_stats_virements() -> dict:
    """Retourne des statistiques sur les virements."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*)                                          AS total,
            COUNT(*) FILTER (WHERE type_action = 'ajout')    AS nb_ajouts,
            COUNT(*) FILTER (WHERE type_action = 'modification') AS nb_modifs,
            COUNT(*) FILTER (WHERE type_action = 'suppression')  AS nb_supprs,
            COALESCE(SUM(montant_nouv) FILTER (WHERE type_action = 'ajout'), 0) AS montant_total
        FROM virement
    """)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return {
        "total":         int(row[0]),
        "nb_ajouts":     int(row[1]),
        "nb_modifs":     int(row[2]),
        "nb_supprs":     int(row[3]),
        "montant_total": float(row[4]),
    }
