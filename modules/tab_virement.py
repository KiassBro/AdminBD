"""
tab_virement.py — Effectuer un virement bancaire
  - Sélection du compte source ET destination via liste déroulante
  - Aperçu solde en temps réel
  - Boîtes de dialogue personnalisées
"""
import tkinter as tk
from tkinter import ttk

from modules.styles  import *
from modules.widgets import (Btn, BtnGhost, form_combo,
                              MsgSuccess, MsgError, MsgWarning, MsgConfirm)
import modules.client   as cm
import modules.virement as vm


class TabVirement(tk.Frame):

    def __init__(self, parent, app, **kw):
        super().__init__(parent, bg=BG_ROOT, **kw)
        self.app = app
        self._clients = []  # cache liste clients
        self._build()

    # ── Construction ─────────────────────────────────────

    def _build(self):
        # Fond centré avec carte
        canvas = tk.Frame(self, bg=BG_ROOT)
        canvas.pack(fill="both", expand=True)

        # Carte formulaire centrée
        outer = tk.Frame(canvas, bg=BORDER, padx=1, pady=1)
        outer.place(relx=0.5, rely=0.5, anchor="center", width=580, height=560)
        card = tk.Frame(outer, bg=BG_CARD)
        card.pack(fill="both", expand=True)

        # En-tête de la carte
        hdr = tk.Frame(card, bg=GREEN_DARK)
        hdr.pack(fill="x")
        tk.Label(hdr, text="💸  Effectuer un Virement Bancaire",
                 bg=GREEN_DARK, fg=FG_HEAD, font=F_SECTION).pack(
            side="left", padx=16, pady=12)

        body = tk.Frame(card, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=28, pady=16)

        # Formule
        info_bar = tk.Frame(body, bg="#E8F5EE", pady=7)
        info_bar.pack(fill="x", pady=(0,16))
        tk.Label(info_bar,
                 text="  📐  Nouveau solde = Ancien solde − Montant  (trigger PostgreSQL)",
                 bg="#E8F5EE", fg=GREEN_DARK, font=("Segoe UI", 9, "italic")).pack(
            side="left", padx=10)

        # ── Sélection compte SOURCE ───────────────────────
        self.v_src_display = tk.StringVar()
        self.v_src_code    = tk.StringVar()
        self._cb_src = form_combo(
            body,
            "📤  Compte Source (débiteur) :",
            self.v_src_display,
            values=[],
            bg=BG_CARD, width=42,
            callback=self._on_src_change
        )

        # Aperçu solde source
        self.lbl_src = tk.Label(body, text="", bg=BG_CARD,
                                 fg=GREEN_MED, font=("Consolas", 10, "italic"))
        self.lbl_src.pack(anchor="w", pady=(0, 10))

        # ── Sélection compte DESTINATION ─────────────────
        self.v_dest_display = tk.StringVar()
        self.v_dest_code    = tk.StringVar()
        self._cb_dest = form_combo(
            body,
            "📥  Compte Destination (créditeur) :",
            self.v_dest_display,
            values=[],
            bg=BG_CARD, width=42,
            callback=self._on_dest_change
        )

        # Aperçu solde destination
        self.lbl_dest = tk.Label(body, text="", bg=BG_CARD,
                                  fg=TEAL, font=("Consolas", 10, "italic"))
        self.lbl_dest.pack(anchor="w", pady=(0, 10))

        # ── Montant ───────────────────────────────────────
        tk.Label(body, text="💵  Montant à virer (Ar) :",
                 bg=BG_CARD, fg=FG_SECONDARY, font=F_LABEL).pack(anchor="w")
        self.v_mont = tk.StringVar()
        e = ttk.Entry(body, textvariable=self.v_mont, width=28, font=F_MONO)
        e.pack(anchor="w", pady=(2,14), ipady=5)
        self.v_mont.trace("w", self._on_montant_change)

        # Résumé avant validation
        self.lbl_resume = tk.Label(body, text="", bg="#F0FAF4",
                                    fg=GREEN_DARK, font=("Segoe UI", 9),
                                    wraplength=480, justify="left",
                                    pady=6, padx=10)
        self.lbl_resume.pack(fill="x", pady=(0,14))

        # Boutons
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0,12))
        btn_row = tk.Frame(body, bg=BG_CARD)
        btn_row.pack(fill="x")
        BtnGhost(btn_row, text="  Réinitialiser  ",
                 command=self._reset).pack(side="left")
        Btn(btn_row, text="✔  VALIDER LE VIREMENT",
            command=self._valider).pack(side="right", ipadx=10, ipady=4)

    # ── Chargement des clients ────────────────────────────

    def refresh(self):
        """Recharge la liste des clients dans les comboboxes."""
        self._clients = cm.get_all_clients()
        options = [f"{c['n_compte']}  —  {c['nomclient']}  ({c['solde']:,.2f} Ar)"
                   for c in self._clients]
        self._cb_src["values"]  = options
        self._cb_dest["values"] = options
        self.v_src_display.set("")
        self.v_dest_display.set("")
        self.lbl_src.config(text="")
        self.lbl_dest.config(text="")
        self.lbl_resume.config(text="")

    # ── Callbacks ─────────────────────────────────────────

    def _get_client_from_display(self, display: str) -> dict | None:
        """Retrouve le client depuis la valeur affichée dans la combobox."""
        if not display:
            return None
        nc = display.split("—")[0].strip()
        return next((c for c in self._clients if c["n_compte"] == nc), None)

    def _on_src_change(self):
        c = self._get_client_from_display(self.v_src_display.get())
        if c:
            self.lbl_src.config(
                text=f"  ✅  {c['nomclient']}  —  Solde disponible : {c['solde']:,.2f} Ar",
                fg=GREEN_DARK)
        else:
            self.lbl_src.config(text="")
        self._update_resume()

    def _on_dest_change(self):
        c = self._get_client_from_display(self.v_dest_display.get())
        if c:
            self.lbl_dest.config(
                text=f"  ✅  {c['nomclient']}  —  Solde actuel : {c['solde']:,.2f} Ar",
                fg=TEAL)
        else:
            self.lbl_dest.config(text="")
        self._update_resume()

    def _on_montant_change(self, *_):
        self._update_resume()

    def _update_resume(self):
        src  = self._get_client_from_display(self.v_src_display.get())
        dest = self._get_client_from_display(self.v_dest_display.get())
        try:
            m = float(self.v_mont.get())
        except ValueError:
            self.lbl_resume.config(text="")
            return
        if src and dest and m > 0:
            nouveau = src["solde"] - m
            couleur = RED if nouveau < 0 else GREEN_DARK
            self.lbl_resume.config(
                text=(f"  Après virement :\n"
                      f"  {src['nomclient']} : {src['solde']:,.2f}  →  {nouveau:,.2f} Ar\n"
                      f"  {dest['nomclient']} : {dest['solde']:,.2f}  →  {dest['solde']+m:,.2f} Ar"),
                fg=couleur, bg="#F0FAF4")
        else:
            self.lbl_resume.config(text="")

    # ── Validation ────────────────────────────────────────

    def _valider(self):
        src  = self._get_client_from_display(self.v_src_display.get())
        dest = self._get_client_from_display(self.v_dest_display.get())

        if not src:
            MsgWarning(self, "Veuillez sélectionner le compte source.", "Sélection manquante")
            return
        if not dest:
            MsgWarning(self, "Veuillez sélectionner le compte destination.", "Sélection manquante")
            return
        if src["n_compte"] == dest["n_compte"]:
            MsgWarning(self, "Les comptes source et destination doivent être différents.",
                       "Sélection invalide")
            return
        try:
            montant = float(self.v_mont.get())
            if montant <= 0:
                raise ValueError
        except ValueError:
            MsgError(self, "Veuillez entrer un montant valide (nombre > 0).", "Montant invalide")
            return

        if not MsgConfirm(self,
                          f"Confirmer ce virement ?\n\n"
                          f"  De    :  {src['n_compte']}  ({src['nomclient']})\n"
                          f"  Vers  :  {dest['n_compte']}  ({dest['nomclient']})\n"
                          f"  Montant  :  {montant:,.2f} Ar\n\n"
                          f"  Nouveau solde source ≈  {src['solde'] - montant:,.2f} Ar",
                          "Confirmer le virement").ask():
            return

        try:
            nv = vm.effectuer_virement(src["n_compte"], dest["n_compte"], montant)
            MsgSuccess(self,
                       f"Virement n°{nv} effectué avec succès !\n\n"
                       f"  Montant  :  {montant:,.2f} Ar\n"
                       f"  De  :  {src['nomclient']}\n"
                       f"  Vers  :  {dest['nomclient']}\n\n"
                       f"  Les triggers PostgreSQL ont été déclenchés automatiquement.",
                       "Virement réussi")
            self.app.set_status(f"✅ Virement n°{nv} — {montant:,.2f} Ar | "
                                f"{src['n_compte']} → {dest['n_compte']}")
            self._reset()
            self.app.refresh_all()
        except (ValueError, RuntimeError) as e:
            MsgError(self, str(e), "Virement refusé")

    def _reset(self):
        self.v_src_display.set("")
        self.v_dest_display.set("")
        self.v_mont.set("")
        self.lbl_src.config(text="")
        self.lbl_dest.config(text="")
        self.lbl_resume.config(text="")
