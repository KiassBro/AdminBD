"""
main.py — Point d'entrée de l'application lourde Python/Tkinter
          Supervision des Virements Bancaires (PostgreSQL)
          Sujet 11 — Administration BD
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

# Modules internes
from db.config  import test_connection
from db.init_db import init_database
from modules.styles  import *
from modules.widgets import apply_ttk_styles

from modules.tab_clients    import TabClients
from modules.tab_virement   import TabVirement
from modules.tab_liste_vir  import TabListeVirements
from modules.tab_audit      import TabAudit


# ────────────────────────────────────────────────────────────────────
#  FENÊTRE DE CONNEXION
# ────────────────────────────────────────────────────────────────────

class ConnexionWindow(tk.Toplevel):
    """Dialogue de vérification de la connexion PostgreSQL au démarrage."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title("Connexion PostgreSQL")
        self.geometry("420x260")
        self.configure(bg=BG_CARD)
        self.resizable(False, False)
        self.grab_set()
        self.result = False
        self._build()

    def _build(self):
        # En-tête vert
        hdr = tk.Frame(self, bg=BG_HEADER)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🗄  Connexion à PostgreSQL",
                 bg=BG_HEADER, fg=FG_HEADER, font=FONT_LABEL_B).pack(
            side="left", padx=14, pady=10)

        body = tk.Frame(self, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        self.lbl_status = tk.Label(body,
            text="⏳  Test de la connexion en cours…",
            bg=BG_CARD, fg=FG_SECONDARY, font=FONT_LABEL)
        self.lbl_status.pack(pady=(10, 20))

        self.btn_retry = tk.Button(body, text="🔄  Réessayer",
            bg=ACCENT_GREEN, fg="white", font=FONT_BTN, relief="flat",
            cursor="hand2", command=self._try_connect, state="disabled")
        self.btn_retry.pack(pady=4)

        tk.Button(body, text="✖  Quitter",
            bg=ACCENT_RED, fg="white", font=FONT_BTN_SM, relief="flat",
            cursor="hand2", command=self._quit).pack(pady=4)

        self.after(300, self._try_connect)

    def _try_connect(self):
        self.lbl_status.config(text="⏳  Connexion en cours…", fg=FG_SECONDARY)
        self.btn_retry.config(state="disabled")
        self.update()
        try:
            if test_connection():
                init_database()
                self.lbl_status.config(
                    text="✅  Connexion réussie !\n   Base de données initialisée.",
                    fg=ACCENT_GREEN)
                self.result = True
                self.after(900, self.destroy)
            else:
                raise ConnectionError("Connexion échouée.")
        except Exception as e:
            self.lbl_status.config(
                text=f"❌  Erreur de connexion :\n{str(e)[:120]}",
                fg=ACCENT_RED)
            self.btn_retry.config(state="normal")

    def _quit(self):
        self.result = False
        self.destroy()


# ────────────────────────────────────────────────────────────────────
#  APPLICATION PRINCIPALE
# ────────────────────────────────────────────────────────────────────

class BankApp(tk.Tk):
    """Fenêtre principale — Supervision des Virements Bancaires."""

    def __init__(self):
        super().__init__()
        self.title("🏦  Supervision des Virements Bancaires — PostgreSQL")
        self.geometry(f"{WINDOW_W}x{WINDOW_H}")
        self.configure(bg=BG_ROOT)
        self.minsize(900, 600)

        apply_ttk_styles(self)

        self._build_header()
        self._build_notebook()
        self._build_status_bar()

        self.refresh_all()

    # ─────────────────────────────────────────────────────
    #  CONSTRUCTION UI
    # ─────────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=BG_HEADER, height=62)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Logo + titre
        left = tk.Frame(hdr, bg=BG_HEADER)
        left.pack(side="left", padx=16, pady=8)
        tk.Label(left, text="🏦",
                 bg=BG_HEADER, fg=FG_HEADER,
                 font=("Segoe UI", 20)).pack(side="left")
        tk.Frame(left, bg="#4ade80", width=3).pack(
            side="left", fill="y", padx=8)
        info = tk.Frame(left, bg=BG_HEADER)
        info.pack(side="left")
        tk.Label(info, text="SUPERVISION DES VIREMENTS BANCAIRES",
                 bg=BG_HEADER, fg=FG_HEADER, font=FONT_TITLE).pack(anchor="w")
        tk.Label(info, text="Application Lourde Python · PostgreSQL · Triggers",
                 bg=BG_HEADER, fg="#a7f3d0", font=("Segoe UI", 8)).pack(anchor="w")

        # Horloge
        self.lbl_clock = tk.Label(hdr, text="", bg=BG_HEADER,
                                   fg="#a7f3d0", font=FONT_CLOCK)
        self.lbl_clock.pack(side="right", padx=18)
        self._tick()

    def _tick(self):
        self.lbl_clock.config(
            text=datetime.datetime.now().strftime("%A %d/%m/%Y   %H:%M:%S"))
        self.after(1000, self._tick)

    def _build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        self.tab_clients   = TabClients(self.nb, self)
        self.tab_virement  = TabVirement(self.nb, self)
        self.tab_liste_vir = TabListeVirements(self.nb, self)
        self.tab_audit     = TabAudit(self.nb, self)

        self.nb.add(self.tab_clients,   text="  👤  Clients  ")
        self.nb.add(self.tab_virement,  text="  💸  Effectuer Virement  ")
        self.nb.add(self.tab_liste_vir, text="  📋  Historique  ")
        self.nb.add(self.tab_audit,     text="  🔍  Audit Triggers  ")

    def _build_status_bar(self):
        sb = tk.Frame(self, bg=BG_HEADER, height=28)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)

        self.v_status = tk.StringVar(value="✅  Application prête — Connecté à PostgreSQL — Triggers actifs")
        tk.Label(sb, textvariable=self.v_status,
                 bg=BG_HEADER, fg="#a7f3d0",
                 font=FONT_STATUS, anchor="w").pack(
            side="left", padx=12, pady=5)

        tk.Label(sb, text="Sujet 11 — Admin BD",
                 bg=BG_HEADER, fg="#4ade80",
                 font=FONT_STATUS).pack(side="right", padx=12)

    # ─────────────────────────────────────────────────────
    #  MÉTHODES PUBLIQUES
    # ─────────────────────────────────────────────────────

    def set_status(self, msg: str) -> None:
        self.v_status.set(msg)

    def refresh_all(self) -> None:
        """Rafraîchit tous les onglets."""
        self.tab_clients.refresh()
        self.tab_liste_vir.refresh()
        self.tab_audit.refresh()


# ────────────────────────────────────────────────────────────────────
#  LANCEMENT
# ────────────────────────────────────────────────────────────────────

def main():
    # Fenêtre racine invisible pour la boîte de dialogue de connexion
    root = tk.Tk()
    root.withdraw()

    apply_ttk_styles(root)

    dlg = ConnexionWindow(root)
    root.wait_window(dlg)

    if not dlg.result:
        messagebox.showinfo(
            "Information",
            "L'application ne peut pas démarrer sans connexion PostgreSQL.\n\n"
            "Vérifiez que le serveur PostgreSQL est démarré et\n"
            "modifiez les paramètres dans db/config.py si nécessaire.",
            parent=root
        )
        root.destroy()
        sys.exit(0)

    root.destroy()

    app = BankApp()
    app.mainloop()


if __name__ == "__main__":
    main()
