"""
tab_audit.py — Onglet Audit (table audit_virement remplie par les triggers PostgreSQL)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from modules.styles import *
from modules.widgets import (
    GreenButton, DangerButton, SecondaryButton, StatCard, make_treeview
)
import modules.audit as audit_mod


class TabAudit(tk.Frame):
    """Onglet '🔍 Audit (Triggers)' — lecture seule + export CSV."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=BG_ROOT, **kwargs)
        self.app = app
        self._build()

    # ─────────────────────────────────────────────────────
    #  UI
    # ─────────────────────────────────────────────────────

    def _build(self):
        # ── Titre ────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_ROOT)
        hdr.pack(fill="x", padx=PAD_X, pady=(PAD_Y, 0))
        tk.Label(hdr, text="🔍  Journal d'Audit — Triggers PostgreSQL",
                 bg=BG_ROOT, fg=FG_PRIMARY, font=FONT_SUBTITLE).pack(side="left")

        tk.Label(hdr,
                 text="Chaque opération INSERT / UPDATE / DELETE déclenche automatiquement un trigger",
                 bg=BG_ROOT, fg=FG_SECONDARY,
                 font=("Segoe UI", 8, "italic")).pack(side="right", padx=4)

        # ── Cartes de stats ───────────────────────────────
        stats_row = tk.Frame(self, bg=BG_ROOT)
        stats_row.pack(fill="x", padx=PAD_X, pady=PAD_Y)

        self.sc_insert = StatCard(stats_row, "Insertions",    icon="➕", color=ACCENT_GREEN)
        self.sc_update = StatCard(stats_row, "Modifications", icon="✏", color=ACCENT_ORANGE)
        self.sc_delete = StatCard(stats_row, "Suppressions",  icon="🗑", color=ACCENT_RED)
        self.sc_total  = StatCard(stats_row, "Total Audit",   icon="📋", color=ACCENT_BLUE)

        for sc in (self.sc_insert, self.sc_update, self.sc_delete, self.sc_total):
            sc.pack(side="left", fill="y", expand=True, padx=4, pady=2, ipadx=4)

        # ── Barre filtres ─────────────────────────────────
        fbar = tk.Frame(self, bg=BG_SIDEBAR)
        fbar.pack(fill="x", padx=PAD_X, pady=(0, 4))

        tk.Label(fbar, text="Action :", bg=BG_SIDEBAR,
                 fg=FG_SECONDARY, font=FONT_LABEL).pack(side="left", padx=(10, 4), pady=8)

        self.v_action = tk.StringVar(value="Tous")
        cb = ttk.Combobox(fbar, textvariable=self.v_action, width=14,
                          values=["Tous", "ajout", "modification", "suppression"],
                          state="readonly", font=FONT_LABEL)
        cb.pack(side="left", pady=8)
        cb.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        tk.Label(fbar, text="  Compte :", bg=BG_SIDEBAR,
                 fg=FG_SECONDARY, font=FONT_LABEL).pack(side="left", padx=(14, 4))
        self.v_cpte = tk.StringVar()
        ttk.Entry(fbar, textvariable=self.v_cpte, width=14).pack(side="left", ipady=3, pady=8)

        GreenButton(fbar, text="🔍", command=self.refresh,
                    padx=8, pady=2).pack(side="left", padx=6)

        # Boutons droite
        DangerButton(fbar, text="🧹  Vider l'audit",
                     command=self._vider).pack(side="right", padx=10, pady=8)

        tk.Button(fbar, text="📤  Exporter CSV",
                  bg=ACCENT_BLUE, fg="white",
                  font=FONT_BTN_SM, relief="flat", cursor="hand2",
                  command=self._export_csv).pack(side="right", padx=4, pady=8)

        SecondaryButton(fbar, text="🔄  Actualiser",
                        command=self.refresh).pack(side="right", padx=4, pady=8)

        # ── Légende ───────────────────────────────────────
        leg = tk.Frame(self, bg=BG_ROOT)
        leg.pack(fill="x", padx=PAD_X, pady=2)
        for label, bg, fg in [("  ajout  ", COLOR_INSERT, FG_INSERT),
                               ("  modification  ", COLOR_UPDATE, FG_UPDATE),
                               ("  suppression  ", COLOR_DELETE, FG_DELETE)]:
            tk.Label(leg, text=label, bg=bg, fg=fg,
                     font=("Segoe UI", 8, "bold"),
                     padx=6, pady=2).pack(side="left", padx=4)

        # ── Tableau audit ─────────────────────────────────
        cols = ("id_audit", "type_action", "date_operation",
                "n_compte", "n_virement",
                "montant_ancien", "montant_nouv", "utilisateur")
        hdrs = {
            "id_audit":       "ID",
            "type_action":    "Action Trigger",
            "date_operation": "Date / Heure",
            "n_compte":       "N° Compte",
            "n_virement":     "N° Virement",
            "montant_ancien": "Anc. Montant (Ar)",
            "montant_nouv":   "Nouv. Montant (Ar)",
            "utilisateur":    "Utilisateur",
        }
        widths = {
            "id_audit": 55, "type_action": 130, "date_operation": 165,
            "n_compte": 100, "n_virement": 90,
            "montant_ancien": 140, "montant_nouv": 140, "utilisateur": 90,
        }

        self.tv, tv_frame = make_treeview(self, cols, hdrs, widths, height=16)
        tv_frame.pack(fill="both", expand=True, padx=PAD_X, pady=(0, PAD_Y))

    # ─────────────────────────────────────────────────────
    #  ACTIONS
    # ─────────────────────────────────────────────────────

    def _vider(self):
        if not messagebox.askyesno("Confirmer",
                                   "Vider complètement la table d'audit ?\n"
                                   "Cette opération est irréversible.", parent=self):
            return
        count = audit_mod.vider_audit()
        self.app.set_status(f"🧹 Audit vidé — {count} entrées supprimées.")
        self.refresh()

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Tous", "*.*")],
            initialfile="audit_virement.csv",
            title="Exporter l'audit",
            parent=self
        )
        if not path:
            return
        try:
            count = audit_mod.export_audit_csv(path)
            messagebox.showinfo("Export réussi",
                                f"✅ {count} lignes exportées vers :\n{path}", parent=self)
            self.app.set_status(f"📤 Audit exporté ({count} lignes) → {path}")
        except Exception as e:
            messagebox.showerror("Erreur export", str(e), parent=self)

    # ─────────────────────────────────────────────────────
    #  RAFRAÎCHISSEMENT
    # ─────────────────────────────────────────────────────

    def refresh(self):
        for row in self.tv.get_children():
            self.tv.delete(row)

        action = self.v_action.get() if hasattr(self, "v_action") else "Tous"
        cpte   = self.v_cpte.get()   if hasattr(self, "v_cpte")   else ""

        audits = audit_mod.get_all_audits(
            filtre_action=action,
            filtre_compte=cpte
        )

        tag_map = {"ajout": "insert", "modification": "update", "suppression": "delete"}

        for a in audits:
            tag = tag_map.get(a["type_action"], "")
            self.tv.insert("", "end", tags=(tag,), values=(
                a["id_audit"],
                a["type_action"],
                a["date_operation"],
                a["n_compte"],
                a["n_virement"],
                f"{a['montant_ancien']:,.2f}",
                f"{a['montant_nouv']:,.2f}",
                a["utilisateur"],
            ))

        # Stats
        stats = audit_mod.get_stats_audit()
        self.sc_insert.update_value(str(stats["insertions"]))
        self.sc_update.update_value(str(stats["modifications"]))
        self.sc_delete.update_value(str(stats["suppressions"]))
        self.sc_total.update_value(str(stats["total"]))
