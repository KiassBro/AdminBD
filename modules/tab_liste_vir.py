"""
tab_liste_vir.py — Historique des virements avec CRUD
"""
import tkinter as tk
from modules.styles  import *
from modules.widgets import (Btn, BtnDanger, BtnOrange, BtnGhost, make_tree,
                              MsgSuccess, MsgError, MsgWarning, MsgConfirm, MsgInput)
import modules.virement as vm


class TabListeVirements(tk.Frame):

    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg=BG_ROOT, **kw)
        self.app = app
        self._build()

    def _build(self):
        # Titre
        hdr = tk.Frame(self, bg=BG_ROOT)
        hdr.pack(fill="x", padx=PX, pady=(PY, 0))
        tk.Label(hdr, text="📋  Historique des Virements",
                 bg=BG_ROOT, fg=FG_PRIMARY, font=F_SECTION).pack(side="left")

        # Toolbar
        tb = tk.Frame(self, bg=BG_SIDEBAR)
        tb.pack(fill="x", padx=PX, pady=(PY, 0))

        tk.Label(tb, text="  Filtrer :", bg=BG_SIDEBAR,
                 fg=FG_SECONDARY, font=F_LABEL).pack(side="left", pady=10)
        self.v_f = tk.StringVar()
        import tkinter.ttk as ttk
        ttk.Entry(tb, textvariable=self.v_f, width=16).pack(
            side="left", padx=6, pady=10, ipady=3)
        Btn(tb, text="🔍", command=self.refresh, padx=8, pady=3).pack(
            side="left", pady=10)
        BtnGhost(tb, text="✖ Tout afficher",
                 command=lambda: [self.v_f.set(""), self.refresh()]).pack(
            side="left", padx=8, pady=10)

        tk.Frame(tb, bg=BORDER, width=1).pack(side="left", fill="y", padx=8, pady=6)

        BtnOrange(tb, text="✏  Modifier montant",
                  command=self._modifier).pack(side="left", pady=10)
        BtnDanger(tb, text="🗑  Supprimer",
                  command=self._supprimer).pack(side="left", padx=8, pady=10)
        BtnGhost(tb, text="🔄", command=self.refresh).pack(side="right", padx=10, pady=10)

        # Légende
        leg = tk.Frame(self, bg=BG_ROOT)
        leg.pack(fill="x", padx=PX, pady=4)
        for txt, bg, fg in [(" ➕ Ajout ", INS_BG, INS_FG),
                             (" ✏ Modification ", UPD_BG, UPD_FG),
                             (" 🗑 Suppression ", DEL_BG, DEL_FG)]:
            tk.Label(leg, text=txt, bg=bg, fg=fg,
                     font=("Segoe UI", 8, "bold"),
                     padx=8, pady=3).pack(side="left", padx=4)

        # Tableau
        cols = ("n_virement","type_action","date_virement","n_compte",
                "nomclient","n_compte_dest","montant_ancien","montant_nouv")
        hdrs = {"n_virement":"N° Vir","type_action":"Action","date_virement":"Date/Heure",
                "n_compte":"Cpte Src","nomclient":"Nom Client","n_compte_dest":"Cpte Dest",
                "montant_ancien":"Anc. Solde (Ar)","montant_nouv":"Montant (Ar)"}
        wids = {"n_virement":65,"type_action":110,"date_virement":155,
                "n_compte":85,"nomclient":150,"n_compte_dest":85,
                "montant_ancien":130,"montant_nouv":130}
        self.tv, tvf = make_tree(self, cols, hdrs, wids, height=18)
        tvf.pack(fill="both", expand=True, padx=PX, pady=(4,PY))

    def _get_selected(self):
        sel = self.tv.selection()
        return self.tv.item(sel[0])["values"] if sel else None

    def _supprimer(self):
        vals = self._get_selected()
        if not vals:
            MsgWarning(self, "Sélectionnez un virement dans la liste.", "Aucune sélection")
            return
        nv = vals[0]
        if MsgConfirm(self,
                      f"Supprimer le virement n°{nv} ?\n\n"
                      f"⚠ Le trigger PostgreSQL trg_audit_delete\n"
                      f"   enregistrera cette suppression automatiquement.",
                      "Confirmer la suppression").ask():
            try:
                vm.supprimer_virement(int(nv))
                MsgSuccess(self,
                           f"Le virement n°{nv} a été supprimé.\n"
                           f"L'audit a été mis à jour automatiquement par le trigger.",
                           "Virement supprimé")
                self.app.set_status(f"🗑 Virement n°{nv} supprimé — trigger audit déclenché.")
                self.refresh()
                self.app.refresh_all()
            except (ValueError, RuntimeError) as e:
                MsgError(self, str(e), "Erreur")

    def _modifier(self):
        vals = self._get_selected()
        if not vals:
            MsgWarning(self, "Sélectionnez un virement dans la liste.", "Aucune sélection")
            return
        nv = vals[0]
        val_actuel = str(vals[7]).replace(",","")
        inp = MsgInput(self,
                       f"Modifier le montant du virement n°{nv}\n\n"
                       f"⚠ Le trigger trg_audit_update sera déclenché automatiquement.",
                       title=f"Modifier Virement n°{nv}",
                       default=val_actuel)
        new_val = inp.get_value()
        if new_val is None:
            return
        try:
            nm = float(new_val)
            vm.modifier_virement(int(nv), nm)
            MsgSuccess(self,
                       f"Le virement n°{nv} a été modifié.\n"
                       f"Nouveau montant : {nm:,.2f} Ar",
                       "Modification enregistrée")
            self.app.set_status(f"✏ Virement n°{nv} modifié — trigger audit déclenché.")
            self.refresh()
            self.app.refresh_all()
        except (ValueError, RuntimeError) as e:
            MsgError(self, str(e), "Erreur")

    def refresh(self):
        for r in self.tv.get_children():
            self.tv.delete(r)
        f = self.v_f.get() if hasattr(self, "v_f") else ""
        TAG = {"ajout":"ins","modification":"upd","suppression":"del"}
        for v in vm.get_all_virements(f):
            self.tv.insert("", "end", tags=(TAG.get(v["type_action"],""),), values=(
                v["n_virement"], v["type_action"], v["date_virement"],
                v["n_compte"], v["nomclient"], v["n_compte_dest"],
                f"{v['montant_ancien']:,.2f}", f"{v['montant_nouv']:,.2f}"))
