"""
config.py — Configuration de la connexion PostgreSQL
"""

import psycopg2
from psycopg2 import OperationalError

# ─────────────────────────────────────────────
#  Paramètres de connexion PostgreSQL
#  Modifiez ces valeurs selon votre installation
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "banque_db",
    "user":     "postgres",
    "password": "123456",   # ← changer selon votre mot de passe
}


def get_connection():
    """Retourne une connexion PostgreSQL active."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except OperationalError as e:
        raise ConnectionError(
            f"Impossible de se connecter à PostgreSQL.\n"
            f"Vérifiez que le serveur est démarré et que les paramètres dans config.py sont corrects.\n\n"
            f"Détail : {e}"
        )


def test_connection() -> bool:
    """Teste la connexion et retourne True si OK."""
    try:
        conn = get_connection()
        conn.close()
        return True
    except ConnectionError:
        return False
