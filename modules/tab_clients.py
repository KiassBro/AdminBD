"""
tab_clients.py — Onglet de gestion des clients (interface graphique)
"""

import tkinter as tk
from tkinter import ttk, messagebox

from modules.styles import *
from modules.widgets import (
    GreenButton, DangerButton, SecondaryButton,
    StatCard, LabelEntry, make_treeview, card_frame
)
import modules.client as client_mod


class TabClients(tk.Frame):
    """Onglet 'Clients' : liste, ajout, modification, suppression."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=BG_ROOT, **kwargs)
        self.app = app
        self._build()

    # ─────────────────────────────────────────────────────
    #  CONSTRUCTION UI
    # ─────────────────────────────────────────────────────

    def _build(self):
        # ── En-tête ───────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_ROOT)
        hdr.pack(fill="x", padx=PAD_X, pady=(PAD_Y, 0))

        tk.Label(hdr, text="👤  Gestion des Clients",
                 bg=BG_ROOT, fg=FG_PRIMARY, font=FONT_SUBTITLE).pack(side="left")

        SecondaryButton(hdr, text="🔄  Actualiser",
                        command=self.refresh).pack(side="right")

        # ── Stats ─────────────────────────────────────────
        stats_row = tk.Frame(self, bg=BG_ROOT)
        stats_row.pack(fill="x", padx=PAD_X, pady=PAD_Y)

        self.sc_total  = StatCard(stats_row, "Clients",   icon="👥", color=ACCENT_GREEN)
        self.sc_solde  = StatCard(stats_row, "Solde total (Ar)", icon="💰", color=ACCENT_BLUE)
        self.sc_moyen  = StatCard(stats_row, "Solde moyen",   icon="📊", color=ACCENT_ORANGE)

        for sc in (self.sc_total, self.sc_solde, self.sc_moyen):
            sc.pack(side="left", fill="y", expand=True,
                    padx=4, pady=2, ipadx=4)

        # ── Corps principal ───────────────────────────────
        body = tk.Frame(self, bg=BG_ROOT)
        body.pack(fill="both", expand=True, padx=PAD_X, pady=PAD_Y)

        # Tableau gauche
        tv_cols = ("n_compte", "nomclient", "solde")
        tv_hdrs = {"n_compte": "N° Compte", "nomclient": "Nom Client", "solde": "Solde (Ar)"}
        tv_wids = {"n_compte": 130, "nomclient": 300, "solde": 160}

        self.tv, tv_frame = make_treeview(body, tv_cols, tv_hdrs, tv_wids, height=16)
        self.tv.bind("<<TreeviewSelect>>", self._on_select)
        tv_frame.pack(side="left", fill="both", expand=True)

        # Panneau droit — formulaire
        pnl = tk.Frame(body, bg=BG_CARD, width=280)
        pnl.pack(side="right", fill="y", padx=(10, 0))
        pnl.pack_propagate(False)

        tk.Label(pnl, text="➕  Nouveau Client",
                 bg=BG_CARD, fg=FG_PRIMARY, font=FONT_SUBTITLE).pack(
            pady=(18, 8), padx=14, anchor="w")

        # Séparateur
        tk.Frame(pnl, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(0, 10))

        self.v_nc  = tk.StringVar()
        self.v_nom = tk.StringVar()
        self.v_sol = tk.StringVar(value="0")

        for lbl, var in [("N° Compte :", self.v_nc),
                         ("Nom Client :", self.v_nom),
                         ("Solde initial (Ar) :", self.v_sol)]:
            le = LabelEntry(pnl, lbl, var, width=26, bg=BG_CARD)
            le.pack(fill="x", padx=14)

        GreenButton(pnl, text="✔  Enregistrer",
                    command=self._ajouter).pack(
            pady=(4, 2), padx=14, fill="x")

        # ── Modification ──────────────────────────────────
        tk.Frame(pnl, bg=BORDER, height=1).pack(fill="x", padx=14, pady=10)

        tk.Label(pnl, text="✏  Modifier Sélectionné",
                 bg=BG_CARD, fg=FG_PRIMARY, font=FONT_LABEL_B).pack(
            padx=14, anchor="w")

        self.v_nom_m = tk.StringVar()
        self.v_sol_m = tk.StringVar()

        LabelEntry(pnl, "Nouveau nom :", self.v_nom_m, width=26, bg=BG_CARD).pack(
            fill="x", padx=14)
        LabelEntry(pnl, "Nouveau solde (Ar) :", self.v_sol_m, width=26, bg=BG_CARD).pack(
            fill="x", padx=14)

        tk.Button(pnl, text="💾  Mettre à jour",
                  bg=ACCENT_ORANGE, fg="white",
                  font=FONT_BTN, relief="flat", cursor="hand2",
                  command=self._modifier).pack(pady=(4, 2), padx=14, fill="x")

        DangerButton(pnl, text="🗑  Supprimer",
                     command=self._supprimer).pack(
            pady=2, padx=14, fill="x")

    # ─────────────────────────────────────────────────────
    #  ACTIONS
    # ─────────────────────────────────────────────────────

    def _on_select(self, _event=None):
        """Rempli les champs de modification quand on sélectionne un client."""
        sel = self.tv.selection()
        if sel:
            vals = self.tv.item(sel[0])["values"]
            # vals = (n_compte, nomclient, solde_str)
            self.v_nom_m.set(vals[1])
            solde_str = str(vals[2]).replace(" ", "").replace(",", "")
            self.v_sol_m.set(solde_str)

    def _ajouter(self):
        nc  = self.v_nc.get().strip()
        nom = self.v_nom.get().strip()
        try:
            sol = float(self.v_sol.get().strip() or "0")
        except ValueError:
            messagebox.showerror("Erreur", "Solde invalide (nombre attendu).", parent=self)
            return

        try:
            client_mod.ajouter_client(nc, nom, sol)
            self.app.set_status(f"✅ Client '{nom}' ajouté.")
            self.v_nc.set(""); self.v_nom.set(""); self.v_sol.set("0")
            self.refresh()
        except (ValueError, RuntimeError) as e:
            messagebox.showerror("Erreur", str(e), parent=self)

    def _modifier(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un client.", parent=self)
            return
        nc = self.tv.item(sel[0])["values"][0]
        nom = self.v_nom_m.get().strip()
        try:
            sol = float(self.v_sol_m.get().strip())
        except ValueError:
            messagebox.showerror("Erreur", "Solde invalide.", parent=self)
            return

        try:
            client_mod.modifier_client(nc, nom, sol)
            self.app.set_status(f"✏ Client '{nc}' modifié.")
            self.refresh()
        except (ValueError, RuntimeError) as e:
            messagebox.showerror("Erreur", str(e), parent=self)

    def _supprimer(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Sélection", "Veuillez sélectionner un client.", parent=self)
            return
        nc, nom = self.tv.item(sel[0])["values"][0], self.tv.item(sel[0])["values"][1]
        if not messagebox.askyesno("Confirmer",
                                   f"Supprimer le client '{nom}' ({nc}) ?", parent=self):
            return
        try:
            client_mod.supprimer_client(nc)
            self.app.set_status(f"🗑 Client '{nc}' supprimé.")
            self.refresh()
        except (ValueError, RuntimeError) as e:
            messagebox.showerror("Erreur", str(e), parent=self)

    # ─────────────────────────────────────────────────────
    #  RAFRAÎCHISSEMENT
    # ─────────────────────────────────────────────────────

    def refresh(self):
        """Recharge le tableau et les statistiques."""
        for row in self.tv.get_children():
            self.tv.delete(row)

        clients = client_mod.get_all_clients()
        for i, c in enumerate(clients):
            tag = "alt" if i % 2 else ""
            fg_tag = "neg" if c["solde"] < 0 else tag
            self.tv.insert("", "end",
                           values=(c["n_compte"], c["nomclient"],
                                   f"{c['solde']:,.2f}"),
                           tags=(fg_tag,))

        self.tv.tag_configure("neg", foreground=ACCENT_RED)

        stats = client_mod.get_stats_clients()
        self.sc_total.update_value(str(stats["nb_clients"]))
        self.sc_solde.update_value(f"{stats['solde_total']:,.0f}")
        self.sc_moyen.update_value(f"{stats['solde_moyen']:,.0f}")
