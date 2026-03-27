"""
tab_clients.py — Onglet Gestion des Clients
  - Numéro de compte généré automatiquement
  - Formulaire de modification clair dans une fenêtre dédiée
"""
import tkinter as tk
from tkinter import ttk

from modules.styles  import *
from modules.widgets import (Btn, BtnDanger, BtnGhost, BtnOrange,
                              StatCard, make_tree, form_field,
                              MsgSuccess, MsgError, MsgConfirm)
import modules.client as cm


class TabClients(tk.Frame):

    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg=BG_ROOT, **kw)
        self.app = app
        self._build()

    # ── Construction ─────────────────────────────────────

    def _build(self):
        # Titre
        hdr = tk.Frame(self, bg=BG_ROOT)
        hdr.pack(fill="x", padx=PX, pady=(PY, 0))
        tk.Label(hdr, text="👤  Gestion des Clients",
                 bg=BG_ROOT, fg=FG_PRIMARY, font=F_SECTION).pack(side="left")
        BtnGhost(hdr, text="🔄  Actualiser", command=self.refresh).pack(side="right")

        # Stats
        stats = tk.Frame(self, bg=BG_ROOT)
        stats.pack(fill="x", padx=PX, pady=PY)
        self.sc_n  = StatCard(stats, "Clients",          icon="👥", color=GREEN_DARK)
        self.sc_t  = StatCard(stats, "Solde total (Ar)", icon="💰", color=TEAL)
        self.sc_m  = StatCard(stats, "Solde moyen (Ar)", icon="📊", color=BLUE)
        for sc in (self.sc_n, self.sc_t, self.sc_m):
            sc.pack(side="left", expand=True, fill="both", padx=4, ipadx=4)

        # Corps
        body = tk.Frame(self, bg=BG_ROOT)
        body.pack(fill="both", expand=True, padx=PX, pady=PY)

        # Tableau
        cols = ("n_compte","nomclient","solde")
        hdrs = {"n_compte":"N° Compte","nomclient":"Nom Client","solde":"Solde (Ar)"}
        wids = {"n_compte":130,"nomclient":320,"solde":180}
        self.tv, tvf = make_tree(body, cols, hdrs, wids, height=16)
        self.tv.bind("<<TreeviewSelect>>", self._on_sel)
        tvf.pack(side="left", fill="both", expand=True)

        # Panneau droit — Ajout nouveau client
        pnl = tk.Frame(body, bg=BG_CARD, width=290)
        pnl.pack(side="right", fill="y", padx=(12,0))
        pnl.pack_propagate(False)

        # En-tête panneau
        ph = tk.Frame(pnl, bg=GREEN_DARK)
        ph.pack(fill="x")
        tk.Label(ph, text="➕  Nouveau Client",
                 bg=GREEN_DARK, fg=FG_HEAD, font=F_LABEL_B).pack(
            side="left", padx=14, pady=10)

        form = tk.Frame(pnl, bg=BG_CARD)
        form.pack(fill="both", expand=True, padx=16, pady=10)

        # Numéro auto (lecture seule)
        self.v_nc  = tk.StringVar()
        self.v_nom = tk.StringVar()
        self.v_sol = tk.StringVar(value="0")

        tk.Label(form, text="N° Compte :",
                 bg=BG_CARD, fg=FG_SECONDARY, font=F_LABEL).pack(anchor="w")
        nc_frame = tk.Frame(form, bg=BG_CARD)
        nc_frame.pack(fill="x", pady=(2,10))
        self.e_nc = ttk.Entry(nc_frame, textvariable=self.v_nc,
                              width=16, state="readonly", font=F_INPUT)
        self.e_nc.pack(side="left", ipady=5)
        BtnGhost(nc_frame, text="↺", command=self._refresh_num,
                 padx=6, pady=4).pack(side="left", padx=(6,0))

        form_field(form, "Nom complet :", self.v_nom, bg=BG_CARD)
        form_field(form, "Solde initial (Ar) :", self.v_sol, bg=BG_CARD)

        Btn(form, text="✔  Enregistrer", command=self._ajouter).pack(
            fill="x", pady=(4,2))

        # Séparateur
        tk.Frame(pnl, bg=BORDER, height=1).pack(fill="x", padx=16, pady=6)

        # Boutons actions sur sélection
        act = tk.Frame(pnl, bg=BG_CARD)
        act.pack(fill="x", padx=16, pady=4)
        tk.Label(act, text="Client sélectionné :", bg=BG_CARD,
                 fg=FG_MUTED, font=F_STAT_L).pack(anchor="w", pady=(0,6))
        BtnOrange(act, text="✏  Modifier", command=self._ouvrir_modif).pack(
            fill="x", pady=2)
        BtnDanger(act, text="🗑  Supprimer", command=self._supprimer).pack(
            fill="x", pady=2)

        # Rafraîchir le numéro auto
        self._refresh_num()

    # ── Numéro automatique ────────────────────────────────

    def _refresh_num(self):
        try:
            self.v_nc.set(cm.get_next_numero())
        except Exception:
            self.v_nc.set("C001")

    # ── Sélection dans le tableau ─────────────────────────

    def _on_sel(self, _=None):
        pass  # Juste pour réagir si besoin

    def _get_selected(self):
        sel = self.tv.selection()
        if not sel:
            return None
        return self.tv.item(sel[0])["values"]

    # ── Actions ───────────────────────────────────────────

    def _ajouter(self):
        nc  = self.v_nc.get().strip()
        nom = self.v_nom.get().strip()
        try:
            sol = float(self.v_sol.get().strip() or "0")
        except ValueError:
            MsgError(self, "Le solde doit être un nombre valide.", "Erreur de saisie")
            return
        try:
            cm.ajouter_client(nc, nom, sol)
            MsgSuccess(self, f"Le client « {nom} » a été ajouté avec succès.\nN° Compte : {nc}",
                       "Client ajouté")
            self.app.set_status(f"✅ Client '{nom}' ({nc}) ajouté.")
            self.v_nom.set(""); self.v_sol.set("0")
            self._refresh_num()
            self.refresh()
        except (ValueError, RuntimeError) as e:
            MsgError(self, str(e), "Erreur")

    def _ouvrir_modif(self):
        vals = self._get_selected()
        if not vals:
            MsgWarning = __import__("modules.widgets", fromlist=["MsgWarning"]).MsgWarning
            MsgWarning(self, "Veuillez d'abord sélectionner un client dans la liste.",
                       "Aucune sélection")
            return
        FenetreModifClient(self, self.app, vals[0], vals[1],
                           float(str(vals[2]).replace(",","")))

    def _supprimer(self):
        vals = self._get_selected()
        if not vals:
            from modules.widgets import MsgWarning
            MsgWarning(self, "Veuillez sélectionner un client.", "Aucune sélection")
            return
        nc, nom = vals[0], vals[1]
        if MsgConfirm(self,
                      f"Supprimer le client « {nom} » ({nc}) ?\n\n"
                      f"⚠ Cette action est irréversible.",
                      "Confirmer la suppression").ask():
            try:
                cm.supprimer_client(nc)
                self.app.set_status(f"🗑 Client '{nc}' supprimé.")
                self.refresh()
            except (ValueError, RuntimeError) as e:
                MsgError(self, str(e), "Erreur")

    # ── Refresh ───────────────────────────────────────────

    def refresh(self):
        for r in self.tv.get_children():
            self.tv.delete(r)
        for i, c in enumerate(cm.get_all_clients()):
            tag = ("neg",) if c["solde"] < 0 else (("alt",) if i % 2 else ())
            self.tv.insert("", "end",
                           values=(c["n_compte"], c["nomclient"],
                                   f"{c['solde']:,.2f}"),
                           tags=tag)
        s = cm.get_stats_clients()
        self.sc_n.set(s["nb"])
        self.sc_t.set(f"{s['total']:,.0f}")
        self.sc_m.set(f"{s['moyen']:,.0f}")


# ════════════════════════════════════════════════════════
#  FENÊTRE MODIFICATION CLIENT (claire et lisible)
# ════════════════════════════════════════════════════════

class FenetreModifClient(tk.Toplevel):
    """Fenêtre dédiée à la modification d'un client — formulaire clair."""

    def __init__(self, parent, app, n_compte, nomclient, solde):
        super().__init__(parent)
        self.app      = app
        self.parent   = parent
        self.n_compte = n_compte
        self.title(f"Modifier le client — {n_compte}")
        self.geometry("460x380")
        self.configure(bg=BG_CARD)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        # Centrer
        self.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width()  - 460) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - 380) // 2
        self.geometry(f"+{px}+{py}")

        self._build(n_compte, nomclient, solde)

    def _build(self, nc, nom, solde):
        # En-tête coloré
        hdr = tk.Frame(self, bg=ORANGE, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="✏  Modifier le Client",
                 bg=ORANGE, fg="#fff", font=F_SECTION).pack(
            side="left", padx=16, pady=12)
        tk.Label(hdr, text=nc, bg=ORANGE, fg="#fff4e0",
                 font=("Consolas", 11, "bold")).pack(side="right", padx=16)

        body = tk.Frame(self, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=28, pady=20)

        # N° compte (non modifiable — affiché en info)
        info = tk.Frame(body, bg=BG_SIDEBAR, pady=8)
        info.pack(fill="x", pady=(0,16))
        tk.Label(info, text=f"  N° Compte :  {nc}",
                 bg=BG_SIDEBAR, fg=GREEN_DARK, font=F_LABEL_B).pack(side="left", padx=10)
        tk.Label(info, text="(non modifiable)",
                 bg=BG_SIDEBAR, fg=FG_MUTED, font=("Segoe UI", 8, "italic")).pack(
            side="left")

        # Champs modifiables
        self.v_nom = tk.StringVar(value=nom)
        self.v_sol = tk.StringVar(value=str(solde))

        form_field(body, "Nom complet :", self.v_nom, bg=BG_CARD, width=36)
        form_field(body, "Solde (Ar) :", self.v_sol, bg=BG_CARD, width=36)

        # Boutons
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(8,14))
        row = tk.Frame(body, bg=BG_CARD)
        row.pack(anchor="e")
        BtnGhost(row, text="  Annuler  ", command=self.destroy).pack(
            side="left", padx=(0,10))
        BtnOrange(row, text="💾  Enregistrer les modifications",
                  command=self._sauvegarder).pack(side="left")

    def _sauvegarder(self):
        nom = self.v_nom.get().strip()
        try:
            sol = float(self.v_sol.get().strip())
        except ValueError:
            MsgError(self, "Le solde doit être un nombre valide.", "Erreur de saisie")
            return
        try:
            from modules.client import modifier_client
            modifier_client(self.n_compte, nom, sol)
            MsgSuccess(self,
                       f"Le client « {nom} » ({self.n_compte}) a été mis à jour avec succès.",
                       "Modification enregistrée")
            self.app.set_status(f"✏ Client '{self.n_compte}' modifié.")
            self.parent.refresh()
            self.destroy()
        except (ValueError, RuntimeError) as e:
            MsgError(self, str(e), "Erreur")
