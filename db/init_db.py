"""
init_db.py — Création des tables, triggers PostgreSQL et données initiales
"""

from db.config import get_connection

# ─────────────────────────────────────────────────────────────────
#  DDL — Création des tables
# ─────────────────────────────────────────────────────────────────

SQL_CREATE_TABLES = """
-- Table CLIENT
CREATE TABLE IF NOT EXISTS client (
    n_compte    VARCHAR(20)  PRIMARY KEY,
    nomclient   VARCHAR(100) NOT NULL,
    solde       NUMERIC(15,2) NOT NULL DEFAULT 0.00
);

-- Table VIREMENT
CREATE TABLE IF NOT EXISTS virement (
    n_virement      SERIAL       PRIMARY KEY,
    type_action     VARCHAR(20)  NOT NULL CHECK (type_action IN ('ajout','suppression','modification')),
    date_virement   TIMESTAMP    NOT NULL DEFAULT NOW(),
    n_compte        VARCHAR(20)  NOT NULL REFERENCES client(n_compte),
    n_compte_dest   VARCHAR(20),
    montant_ancien  NUMERIC(15,2) DEFAULT 0,
    montant_nouv    NUMERIC(15,2) DEFAULT 0
);

-- Table AUDIT_VIREMENT
CREATE TABLE IF NOT EXISTS audit_virement (
    id_audit        SERIAL       PRIMARY KEY,
    type_action     VARCHAR(20)  NOT NULL,
    date_operation  TIMESTAMP    NOT NULL DEFAULT NOW(),
    n_compte        VARCHAR(20),
    n_virement      INTEGER,
    montant_ancien  NUMERIC(15,2),
    montant_nouv    NUMERIC(15,2),
    utilisateur     VARCHAR(50)  DEFAULT 'ADMIN'
);
"""

# ─────────────────────────────────────────────────────────────────
#  FONCTIONS et TRIGGERS PostgreSQL
# ─────────────────────────────────────────────────────────────────

SQL_TRIGGER_INSERT = """
-- Fonction trigger : AFTER INSERT sur virement
CREATE OR REPLACE FUNCTION fn_audit_insert_virement()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_virement (type_action, date_operation, n_compte, n_virement, montant_ancien, montant_nouv)
    VALUES ('ajout', NOW(), NEW.n_compte, NEW.n_virement, NEW.montant_ancien, NEW.montant_nouv);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_insert ON virement;
CREATE TRIGGER trg_audit_insert
    AFTER INSERT ON virement
    FOR EACH ROW EXECUTE FUNCTION fn_audit_insert_virement();
"""

SQL_TRIGGER_UPDATE = """
-- Fonction trigger : AFTER UPDATE sur virement
CREATE OR REPLACE FUNCTION fn_audit_update_virement()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_virement (type_action, date_operation, n_compte, n_virement, montant_ancien, montant_nouv)
    VALUES ('modification', NOW(), NEW.n_compte, NEW.n_virement, OLD.montant_nouv, NEW.montant_nouv);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_update ON virement;
CREATE TRIGGER trg_audit_update
    AFTER UPDATE ON virement
    FOR EACH ROW EXECUTE FUNCTION fn_audit_update_virement();
"""

SQL_TRIGGER_DELETE = """
-- Fonction trigger : AFTER DELETE sur virement
CREATE OR REPLACE FUNCTION fn_audit_delete_virement()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_virement (type_action, date_operation, n_compte, n_virement, montant_ancien, montant_nouv)
    VALUES ('suppression', NOW(), OLD.n_compte, OLD.n_virement, OLD.montant_ancien, OLD.montant_nouv);
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_delete ON virement;
CREATE TRIGGER trg_audit_delete
    AFTER DELETE ON virement
    FOR EACH ROW EXECUTE FUNCTION fn_audit_delete_virement();
"""

SQL_TRIGGER_SOLDE = """
-- Fonction trigger : mise à jour solde après INSERT virement (ajout)
-- Nouveau solde = Ancien solde - Montant (débit sur compte source)
CREATE OR REPLACE FUNCTION fn_update_solde_virement()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.type_action = 'ajout' THEN
        -- Débit compte source
        UPDATE client SET solde = solde - NEW.montant_nouv WHERE n_compte = NEW.n_compte;
        -- Crédit compte destination (si renseigné)
        IF NEW.n_compte_dest IS NOT NULL THEN
            UPDATE client SET solde = solde + NEW.montant_nouv WHERE n_compte = NEW.n_compte_dest;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_solde ON virement;
CREATE TRIGGER trg_update_solde
    AFTER INSERT ON virement
    FOR EACH ROW EXECUTE FUNCTION fn_update_solde_virement();
"""

# ─────────────────────────────────────────────────────────────────
#  Données initiales de démonstration
# ─────────────────────────────────────────────────────────────────

SQL_SAMPLE_DATA = """
INSERT INTO client (n_compte, nomclient, solde) VALUES
    ('C001', 'Jean Dupont',      5000.00),
    ('C002', 'Marie Martin',    12500.50),
    ('C003', 'Ahmed Benali',     3200.00),
    ('C004', 'Sofia Randria',    8750.75),
    ('C005', 'Paul Leblanc',      950.25)
ON CONFLICT (n_compte) DO NOTHING;
"""


def init_database():
    """
    Initialise la base de données :
    - Crée les tables
    - Crée les fonctions et triggers PostgreSQL
    - Insère les données de démonstration
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Tables
        cursor.execute(SQL_CREATE_TABLES)

        # Triggers (chacun dans son bloc séparé pour PostgreSQL)
        cursor.execute(SQL_TRIGGER_INSERT)
        cursor.execute(SQL_TRIGGER_UPDATE)
        cursor.execute(SQL_TRIGGER_DELETE)
        cursor.execute(SQL_TRIGGER_SOLDE)

        # Données de démo
        cursor.execute(SQL_SAMPLE_DATA)

        conn.commit()
        print("✅ Base de données initialisée avec succès.")
        print("   Tables     : client, virement, audit_virement")
        print("   Triggers   : trg_audit_insert, trg_audit_update, trg_audit_delete, trg_update_solde")

    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erreur lors de l'initialisation DB : {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    init_database()
