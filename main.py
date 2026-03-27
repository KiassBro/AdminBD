"""
main.py — Application Lourde : Supervision des Virements Bancaires
         PostgreSQL + Tkinter | Sujet 11 — Admin BD
"""
import sys
import tkinter as tk
from tkinter import ttk
import datetime

from db.config   import test_connection
from db.init_db  import init_database
from modules.styles  import *
from modules.widgets import apply_styles, Btn, BtnGhost, MsgError

from modules.tab_clients   import TabClients
from modules.tab_virement  import TabVirement
from modules.tab_liste_vir import TabListeVirements
from modules.tab_audit     import TabAudit


# ════════════════════════════════════════════════════════
#  SPLASH / CONNEXION
# ════════════════════════════════════════════════════════

class SplashConnect(tk.Toplevel):
    """Fenêtre de connexion au démarrage."""

    def __init__(self, parent):
        super().__init__(parent)
        self.result = False
        self.title("Connexion — Banque App")
        self.geometry("440x300")
        self.configure(bg=BG_CARD)
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self.after(400, self._connect)

    def _build(self):
        # Bande verte haut
        tk.Frame(self, bg=GREEN_DARK, height=6).pack(fill="x")

        body = tk.Frame(self, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=36, pady=28)

        # Logo + titre
        top = tk.Frame(body, bg=BG_CARD)
        top.pack(fill="x", pady=(0,20))
        tk.Label(top, text="🏦", bg=BG_CARD,
                 font=("Segoe UI", 32)).pack(side="left", padx=(0,14))
        info = tk.Frame(top, bg=BG_CARD)
        info.pack(side="left")
        tk.Label(info, text="Banque App",
                 bg=BG_CARD, fg=GREEN_DARK, font=F_TITLE).pack(anchor="w")
        tk.Label(info, text="Supervision des Virements Bancaires",
                 bg=BG_CARD, fg=FG_SECONDARY, font=F_LABEL).pack(anchor="w")

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0,16))

        self.lbl = tk.Label(body, text="⏳  Connexion à PostgreSQL en cours…",
                            bg=BG_CARD, fg=FG_SECONDARY, font=F_LABEL)
        self.lbl.pack(anchor="w")

        # Barre de progression simulée
        self.pb = ttk.Progressbar(body, mode="indeterminate", length=360)
        self.pb.pack(pady=(12,16))
        self.pb.start(12)

        self.btn_retry = Btn(body, text="🔄  Réessayer",
                             command=self._connect)
        self.btn_retry.pack(anchor="w")
        self.btn_retry.config(state="disabled")

    def _connect(self):
        self.btn_retry.config(state="disabled")
        self.lbl.config(text="⏳  Connexion à PostgreSQL en cours…", fg=FG_SECONDARY)
        self.update()
        try:
            if test_connection():
                init_database()
                self.pb.stop()
                self.lbl.config(text="✅  Connexion réussie ! Base initialisée.",
                                fg=GREEN_DARK)
                self.result = True
                self.after(900, self.destroy)
            else:
                raise ConnectionError("Échec de la connexion.")
        except Exception as e:
            self.pb.stop()
            self.lbl.config(text=f"❌  {str(e)[:80]}", fg=RED)
            self.btn_retry.config(state="normal")


# ════════════════════════════════════════════════════════
#  APPLICATION PRINCIPALE
# ════════════════════════════════════════════════════════

class BankApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("🏦  Banque App — Supervision des Virements")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.configure(bg=BG_ROOT)
        self.minsize(960, 640)

        apply_styles(self)
        self._build_header()
        self._build_notebook()
        self._build_statusbar()
        self.refresh_all()

    # ── Header ───────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self, bg=GREEN_DARK, height=66)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # Bande accent claire
        tk.Frame(hdr, bg=GREEN_LIGHT, width=5).pack(side="left", fill="y")

        left = tk.Frame(hdr, bg=GREEN_DARK)
        left.pack(side="left", padx=16, pady=10)
        tk.Label(left, text="🏦", bg=GREEN_DARK, fg="#fff",
                 font=("Segoe UI", 22)).pack(side="left", padx=(0,12))
        info = tk.Frame(left, bg=GREEN_DARK)
        info.pack(side="left")
        tk.Label(info, text="SUPERVISION DES VIREMENTS BANCAIRES",
                 bg=GREEN_DARK, fg=FG_HEAD, font=F_TITLE).pack(anchor="w")

        right = tk.Frame(hdr, bg=GREEN_DARK)
        right.pack(side="right", padx=20)
        self.lbl_clock = tk.Label(right, text="",
                                   bg=GREEN_DARK, fg=GREEN_PALE, font=F_CLOCK)
        self.lbl_clock.pack()
        tk.Label(right, text="Sujet 11 — Admin BD",
                 bg=GREEN_DARK, fg=GREEN_PALE,
                 font=("Segoe UI", 7)).pack()
        self._tick()

    def _tick(self):
        self.lbl_clock.config(
            text=datetime.datetime.now().strftime("%A %d/%m/%Y   %H:%M:%S"))
        self.after(1000, self._tick)

    # ── Notebook ─────────────────────────────────────────

    def _build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=(8,0))

        self.tab_cli  = TabClients(self.nb, self)
        self.tab_vir  = TabVirement(self.nb, self)
        self.tab_lst  = TabListeVirements(self.nb, self)
        self.tab_aud  = TabAudit(self.nb, self)

        self.nb.add(self.tab_cli,  text="   👤  Clients   ")
        self.nb.add(self.tab_vir,  text="   💸  Effectuer Virement   ")
        self.nb.add(self.tab_lst,  text="   📋  Historique   ")
        self.nb.add(self.tab_aud,  text="   🔍  Audit Triggers   ")

    # ── Status bar ───────────────────────────────────────

    def _build_statusbar(self):
        sb = tk.Frame(self, bg=GREEN_DARK, height=30)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        self.v_status = tk.StringVar(
            value="✅  Prêt — Connecté à PostgreSQL — 4 triggers actifs")
        tk.Label(sb, textvariable=self.v_status,
                 bg=GREEN_DARK, fg=GREEN_PALE, font=F_STATUS).pack(
            side="left", padx=14, pady=5)
        tk.Label(sb, text="🔒  PostgreSQL sécurisé",
                 bg=GREEN_DARK, fg=GREEN_PALE, font=F_STATUS).pack(
            side="right", padx=14)

    # ── API publique ─────────────────────────────────────

    def set_status(self, msg: str):
        self.v_status.set(msg)

    def refresh_all(self):
        self.tab_cli.refresh()
        self.tab_vir.refresh()
        self.tab_lst.refresh()
        self.tab_aud.refresh()


# ════════════════════════════════════════════════════════
#  LANCEMENT
# ════════════════════════════════════════════════════════

def main():
    root = tk.Tk()
    root.withdraw()
    apply_styles(root)

    splash = SplashConnect(root)
    root.wait_window(splash)

    if not splash.result:
        from tkinter import messagebox
        messagebox.showinfo(
            "Connexion requise",
            "L'application nécessite une connexion PostgreSQL.\n\n"
            "1. Vérifiez que PostgreSQL est démarré\n"
            "2. Créez la base : CREATE DATABASE banque_db;\n"
            "3. Modifiez db/config.py si nécessaire\n"
            "4. Relancez l'application",
            parent=root)
        root.destroy()
        sys.exit(0)

    root.destroy()
    BankApp().mainloop()


if __name__ == "__main__":
    main()
