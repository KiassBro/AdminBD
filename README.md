# 🏦 Supervision des Virements Bancaires
## Application Lourde Python · PostgreSQL · Tkinter
### Sujet 11 — Administration BD

---

## 📁 Structure du Projet

```
banque_app/
│
├── main.py                    # ← Point d'entrée (lancer ici)
│
├── db/
│   ├── config.py              # Paramètres de connexion PostgreSQL
│   └── init_db.py             # Création tables + triggers PostgreSQL
│
├── modules/
│   ├── client.py              # CRUD clients (get, add, update, delete)
│   ├── virement.py            # Logique virements (effectuer, modifier, supprimer)
│   ├── audit.py               # Lecture table audit + export CSV
│   ├── styles.py              # Palette couleurs Blanc/Vert + polices
│   ├── widgets.py             # Composants UI réutilisables
│   ├── tab_clients.py         # Onglet Clients (interface)
│   ├── tab_virement.py        # Onglet Effectuer Virement (interface)
│   ├── tab_liste_vir.py       # Onglet Historique Virements (interface)
│   └── tab_audit.py           # Onglet Audit Triggers (interface)
│
└── README.md
```

---

## ⚙️ Installation

### 1. Prérequis
- Python 3.10+
- PostgreSQL 13+
- pip

### 2. Installer les dépendances Python
```bash
pip install psycopg2-binary
```

### 3. Créer la base de données PostgreSQL
```sql
CREATE DATABASE banque_db;
```

### 4. Configurer la connexion
Modifier `db/config.py` selon votre installation :
```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "banque_db",
    "user":     "postgres",
    "password": "VOTRE_MOT_DE_PASSE",
}
```

### 5. Lancer l'application
```bash
cd banque_app
python main.py
```

---

## 🗄️ Schéma de la Base de Données

### Table `client`
| Colonne    | Type          | Description              |
|-----------|---------------|--------------------------|
| n_compte  | VARCHAR(20)   | Clé primaire             |
| nomclient | VARCHAR(100)  | Nom complet du client    |
| solde     | NUMERIC(15,2) | Solde du compte          |

### Table `virement`
| Colonne        | Type          | Description                        |
|---------------|---------------|------------------------------------|
| n_virement    | SERIAL        | Clé primaire auto-incrémentée      |
| type_action   | VARCHAR(20)   | 'ajout', 'modification', 'suppression' |
| date_virement | TIMESTAMP     | Date et heure de l'opération       |
| n_compte      | VARCHAR(20)   | Compte source (FK → client)        |
| n_compte_dest | VARCHAR(20)   | Compte destination                 |
| montant_ancien| NUMERIC(15,2) | Solde avant opération              |
| montant_nouv  | NUMERIC(15,2) | Montant du virement / nouveau solde|

### Table `audit_virement`
| Colonne        | Type          | Description                        |
|---------------|---------------|------------------------------------|
| id_audit      | SERIAL        | Clé primaire auto-incrémentée      |
| type_action   | VARCHAR(20)   | Action déclenchée                  |
| date_operation| TIMESTAMP     | Horodatage du trigger              |
| n_compte      | VARCHAR(20)   | Compte concerné                    |
| n_virement    | INTEGER       | N° du virement concerné            |
| montant_ancien| NUMERIC(15,2) | Ancien montant                     |
| montant_nouv  | NUMERIC(15,2) | Nouveau montant                    |
| utilisateur   | VARCHAR(50)   | Utilisateur (défaut : ADMIN)       |

---

## ⚡ Triggers PostgreSQL

| Trigger              | Table    | Événement | Fonction                      | Action                                              |
|---------------------|----------|-----------|-------------------------------|-----------------------------------------------------|
| `trg_audit_insert`  | virement | INSERT    | `fn_audit_insert_virement()`  | Enregistre l'ajout dans audit_virement              |
| `trg_audit_update`  | virement | UPDATE    | `fn_audit_update_virement()`  | Enregistre la modification dans audit_virement      |
| `trg_audit_delete`  | virement | DELETE    | `fn_audit_delete_virement()`  | Enregistre la suppression dans audit_virement       |
| `trg_update_solde`  | virement | INSERT    | `fn_update_solde_virement()`  | Met à jour les soldes (Nouveau = Ancien − Montant)  |

### Formule appliquée par le trigger `trg_update_solde` :
```
Nouveau solde (source)      = Ancien solde − Montant
Nouveau solde (destination) = Ancien solde + Montant
```

---

## 🖥️ Fonctionnalités de l'Interface

| Onglet | Fonctionnalités |
|--------|----------------|
| 👤 Clients | Lister, ajouter, modifier, supprimer des clients avec statistiques |
| 💸 Effectuer Virement | Formulaire de virement avec vérification solde et confirmation |
| 📋 Historique | Voir tous les virements, filtrer, modifier montant, supprimer |
| 🔍 Audit Triggers | Consulter les entrées générées par les triggers, filtres, export CSV |

---

## 🎨 Thème visuel
- Fond blanc avec accents **vert professionnel** (`#1a7a4a`)
- Tableau coloré par type d'action : vert (ajout) / orange (modification) / rouge (suppression)
- Interface moderne avec cartes de statistiques et horloge en temps réel
