"""
tab_liste_vir.py — Onglet Historique des Virements (INSERT / UPDATE / DELETE)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from modules.styles import *
from modules.widgets import (
    GreenButton, DangerButton, SecondaryButton, make_treeview
)
import modules.virement as vir_mod


class TabListeVirements(tk.Frame):
    """Onglet '📋 Historique des Virements' avec filtrage et CRUD."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=BG_ROOT, **kwargs)
        self.app = app
        self._build()

    # ─────────────────────────────────────────────────────
    #  UI
    # ─────────────────────────────────────────────────────

    def _build(self):
        # ── Barre d'outils ───────────────────────────────
        toolbar = tk.Frame(self, bg=BG_SIDEBAR, height=46)
        toolbar.pack(fill="x", padx=PAD_X, pady=(PAD_Y, 0))

        tk.Label(toolbar, text="Filtrer par compte :",
                 bg=BG_SIDEBAR, fg=FG_SECONDARY, font=FONT_LABEL).pack(
            side="left", padx=(10, 4), pady=10)

        self.v_filtre = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.v_filtre, width=16).pack(
            side="left", pady=10, ipady=3)

        GreenButton(toolbar, text="🔍", command=self.refresh,
                    padx=8, pady=3).pack(side="left", padx=4, pady=10)

        SecondaryButton(toolbar, text="🔄  Tout afficher",
                        command=lambda: [self.v_filtre.set(""), self.refresh()]).pack(
            side="left", padx=4, pady=10)

        tk.Frame(toolbar, bg=BORDER, width=1).pack(side="left", fill="y",
                                                    padx=8, pady=6)

        tk.Button(toolbar, text="✏  Modifier montant",
                  bg=ACCENT_ORANGE, fg="white",
                  font=FONT_BTN_SM, relief="flat", cursor="hand2",
                  command=self._modifier).pack(side="left", padx=4, pady=10)

        DangerButton(toolbar, text="🗑  Supprimer",
                     command=self._supprimer).pack(side="left", padx=4, pady=10)

        SecondaryButton(toolbar, text="🔄  Actualiser",
                        command=self.refresh).pack(side="right", padx=10, pady=10)

        # ── Légende couleurs ─────────────────────────────
        leg = tk.Frame(self, bg=BG_ROOT)
        leg.pack(fill="x", padx=PAD_X, pady=2)
        for label, bg, fg in [("  Ajout  ", COLOR_INSERT, FG_INSERT),
                               ("  Modification  ", COLOR_UPDATE, FG_UPDATE),
                               ("  Suppression  ", COLOR_DELETE, FG_DELETE)]:
            tk.Label(leg, text=label, bg=bg, fg=fg,
                     font=("Segoe UI", 8, "bold"),
                     relief="flat", padx=6, pady=2).pack(side="left", padx=4)

        # ── Tableau ───────────────────────────────────────
        cols = ("n_virement", "type_action", "date_virement",
                "n_compte", "nomclient", "n_compte_dest",
                "montant_ancien", "montant_nouv")
        hdrs = {
            "n_virement":    "N° Vir",
            "type_action":   "Action",
            "date_virement": "Date / Heure",
            "n_compte":      "Cpte Src",
            "nomclient":     "Nom Client",
            "n_compte_dest": "Cpte Dest",
            "montant_ancien":"Anc. Solde (Ar)",
            "montant_nouv":  "Nouv. Solde (Ar)",
        }
        widths = {
            "n_virement": 65, "type_action": 110, "date_virement": 160,
            "n_compte": 90, "nomclient": 160, "n_compte_dest": 90,
            "montant_ancien": 130, "montant_nouv": 130,
        }

        self.tv, tv_frame = make_treeview(self, cols, hdrs, widths, height=18)
        tv_frame.pack(fill="both", expand=True, padx=PAD_X, pady=(4, PAD_Y))

    # ─────────────────────────────────────────────────────
    #  ACTIONS
    # ─────────────────────────────────────────────────────

    def _supprimer(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Sélection",
                                   "Veuillez sélectionner un virement.", parent=self)
            return
        nv = self.tv.item(sel[0])["values"][0]
        if not messagebox.askyesno(
                "Confirmer la suppression",
                f"Supprimer le virement n°{nv} ?\n\n"
                f"⚠ Le trigger PostgreSQL trg_audit_delete enregistrera\n"
                f"   automatiquement cette suppression dans la table audit.",
                parent=self):
            return
        try:
            vir_mod.supprimer_virement(int(nv))
            self.app.set_status(
                f"🗑 Virement n°{nv} supprimé — trigger audit déclenché.")
            self.refresh()
            self.app.refresh_all()
        except (ValueError, RuntimeError) as e:
            messagebox.showerror("Erreur", str(e), parent=self)

    def _modifier(self):
        sel = self.tv.selection()
        if not sel:
            messagebox.showwarning("Sélection",
                                   "Veuillez sélectionner un virement.", parent=self)
            return
        vals = self.tv.item(sel[0])["values"]
        nv = vals[0]

        win = tk.Toplevel(self)
        win.title(f"Modifier Virement n°{nv}")
        win.geometry("380x220")
        win.configure(bg=BG_CARD)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text=f"Modifier le montant du virement n°{nv}",
                 bg=BG_CARD, fg=FG_PRIMARY, font=FONT_LABEL_B).pack(pady=(20, 4))
        tk.Label(win,
                 text="ℹ  Le trigger trg_audit_update sera déclenché automatiquement.",
                 bg=BG_CARD, fg=FG_SECONDARY,
                 font=("Segoe UI", 8, "italic"), wraplength=340).pack(pady=(0, 14))

        tk.Label(win, text="Nouveau montant (Ar) :",
                 bg=BG_CARD, fg=FG_SECONDARY, font=FONT_LABEL).pack()
        v_m = tk.StringVar(value=str(vals[7]))
        ttk.Entry(win, textvariable=v_m, width=22, font=FONT_MONO).pack(ipady=4)

        def save():
            try:
                nm = float(v_m.get())
            except ValueError:
                messagebox.showerror("Erreur", "Montant invalide.", parent=win)
                return
            try:
                vir_mod.modifier_virement(int(nv), nm)
                self.app.set_status(
                    f"✏ Virement n°{nv} modifié — trigger audit déclenché.")
                win.destroy()
                self.refresh()
                self.app.refresh_all()
            except (ValueError, RuntimeError) as e:
                messagebox.showerror("Erreur", str(e), parent=win)

        GreenButton(win, text="✔  Sauvegarder",
                    command=save).pack(pady=14, ipadx=10)

    # ─────────────────────────────────────────────────────
    #  RAFRAÎCHISSEMENT
    # ─────────────────────────────────────────────────────

    def refresh(self):
        for row in self.tv.get_children():
            self.tv.delete(row)

        filtre = self.v_filtre.get() if hasattr(self, "v_filtre") else ""
        virements = vir_mod.get_all_virements(filtre)

        tag_map = {"ajout": "insert", "modification": "update", "suppression": "delete"}

        for v in virements:
            tag = tag_map.get(v["type_action"], "")
            self.tv.insert("", "end", tags=(tag,), values=(
                v["n_virement"],
                v["type_action"],
                v["date_virement"],
                v["n_compte"],
                v["nomclient"],
                v["n_compte_dest"],
                f"{v['montant_ancien']:,.2f}",
                f"{v['montant_nouv']:,.2f}",
            ))
