"""
tab_audit.py — Journal d'Audit (triggers PostgreSQL)
"""
import tkinter as tk
from tkinter import ttk, filedialog

from modules.styles  import *
from modules.widgets import (Btn, BtnDanger, BtnGhost, StatCard, make_tree,
                              MsgSuccess, MsgError, MsgConfirm)
import modules.audit as am


class TabAudit(tk.Frame):

    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg=BG_ROOT, **kw)
        self.app = app
        self._build()

    def _build(self):
        # En-tête
        hdr = tk.Frame(self, bg=BG_ROOT)
        hdr.pack(fill="x", padx=PX, pady=(PY,0))
        tk.Label(hdr, text="🔍  Journal d'Audit — Triggers PostgreSQL",
                 bg=BG_ROOT, fg=FG_PRIMARY, font=F_SECTION).pack(side="left")
        tk.Label(hdr,
                 text="Alimenté automatiquement par trg_audit_insert / update / delete",
                 bg=BG_ROOT, fg=FG_MUTED, font=("Segoe UI", 8, "italic")).pack(
            side="right", padx=4)

        # Stat cards
        sr = tk.Frame(self, bg=BG_ROOT)
        sr.pack(fill="x", padx=PX, pady=PY)
        self.sc_i = StatCard(sr, "Insertions",    icon="➕", color=GREEN_DARK)
        self.sc_u = StatCard(sr, "Modifications", icon="✏", color=ORANGE)
        self.sc_d = StatCard(sr, "Suppressions",  icon="🗑", color=RED)
        self.sc_t = StatCard(sr, "Total Audit",   icon="📋", color=BLUE)
        for sc in (self.sc_i, self.sc_u, self.sc_d, self.sc_t):
            sc.pack(side="left", expand=True, fill="both", padx=4, ipadx=4)

        # Toolbar filtres
        tb = tk.Frame(self, bg=BG_SIDEBAR)
        tb.pack(fill="x", padx=PX, pady=(0,4))

        tk.Label(tb, text="  Action :", bg=BG_SIDEBAR,
                 fg=FG_SECONDARY, font=F_LABEL).pack(side="left", pady=9)
        self.v_action = tk.StringVar(value="Tous")
        cb = ttk.Combobox(tb, textvariable=self.v_action, width=14,
                          values=["Tous","ajout","modification","suppression"],
                          state="readonly", font=F_LABEL)
        cb.pack(side="left", padx=6, pady=9, ipady=3)
        cb.bind("<<ComboboxSelected>>", lambda _: self.refresh())

        tk.Label(tb, text="  Compte :", bg=BG_SIDEBAR,
                 fg=FG_SECONDARY, font=F_LABEL).pack(side="left")
        self.v_cpte = tk.StringVar()
        ttk.Entry(tb, textvariable=self.v_cpte, width=14).pack(
            side="left", padx=6, pady=9, ipady=3)
        Btn(tb, text="🔍", command=self.refresh, padx=8, pady=3).pack(
            side="left", pady=9)

        # Droite
        tk.Button(tb, text="📤  Export CSV", bg=BLUE, fg="#fff",
                  font=F_BTN_SM, relief="flat", cursor="hand2",
                  activebackground="#1A5C8A",
                  command=self._export).pack(side="right", padx=10, pady=9)
        BtnDanger(tb, text="🧹  Vider l'audit",
                  command=self._vider).pack(side="right", pady=9)
        BtnGhost(tb, text="🔄", command=self.refresh).pack(side="right", padx=6, pady=9)

        # Légende
        leg = tk.Frame(self, bg=BG_ROOT)
        leg.pack(fill="x", padx=PX, pady=2)
        for txt, bg, fg in [(" ➕ ajout ", INS_BG, INS_FG),
                             (" ✏ modification ", UPD_BG, UPD_FG),
                             (" 🗑 suppression ", DEL_BG, DEL_FG)]:
            tk.Label(leg, text=txt, bg=bg, fg=fg,
                     font=("Segoe UI", 8, "bold"),
                     padx=8, pady=3).pack(side="left", padx=4)

        # Tableau
        cols = ("id_audit","type_action","date_operation","n_compte",
                "n_virement","montant_ancien","montant_nouv","utilisateur")
        hdrs = {"id_audit":"ID","type_action":"Action Trigger",
                "date_operation":"Date/Heure","n_compte":"N° Compte",
                "n_virement":"N° Vir","montant_ancien":"Anc. Montant (Ar)",
                "montant_nouv":"Nouv. Montant (Ar)","utilisateur":"Utilisateur"}
        wids = {"id_audit":55,"type_action":120,"date_operation":158,
                "n_compte":100,"n_virement":80,
                "montant_ancien":140,"montant_nouv":140,"utilisateur":90}
        self.tv, tvf = make_tree(self, cols, hdrs, wids, height=15)
        tvf.pack(fill="both", expand=True, padx=PX, pady=(0,PY))

    def _vider(self):
        if MsgConfirm(self,
                      "Vider complètement la table d'audit ?\n\n"
                      "⚠ Cette opération est irréversible.",
                      "Vider l'audit").ask():
            count = am.vider_audit()
            MsgSuccess(self, f"{count} entrées supprimées de la table audit.",
                       "Audit vidé")
            self.app.set_status(f"🧹 Audit vidé — {count} entrées supprimées.")
            self.refresh()

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV","*.csv"),("Tous","*.*")],
            initialfile="audit_virement.csv",
            title="Exporter l'audit",
            parent=self)
        if not path:
            return
        try:
            n = am.export_audit_csv(path)
            MsgSuccess(self, f"{n} lignes exportées vers :\n{path}", "Export réussi")
        except Exception as e:
            MsgError(self, str(e), "Erreur export")

    def refresh(self):
        for r in self.tv.get_children():
            self.tv.delete(r)
        a = self.v_action.get() if hasattr(self,"v_action") else "Tous"
        c = self.v_cpte.get()   if hasattr(self,"v_cpte")   else ""
        TAG = {"ajout":"ins","modification":"upd","suppression":"del"}
        for row in am.get_all_audits(a, c):
            self.tv.insert("","end",tags=(TAG.get(row["type_action"],""),),values=(
                row["id_audit"], row["type_action"], row["date_operation"],
                row["n_compte"], row["n_virement"],
                f"{row['montant_ancien']:,.2f}", f"{row['montant_nouv']:,.2f}",
                row["utilisateur"]))
        s = am.get_stats_audit()
        self.sc_i.set(s["insertions"])
        self.sc_u.set(s["modifications"])
        self.sc_d.set(s["suppressions"])
        self.sc_t.set(s["total"])
