"""
tab_virement.py — Onglet pour effectuer les virements bancaires
"""

import tkinter as tk
from tkinter import ttk, messagebox

from modules.styles import *
from modules.widgets import GreenButton, DangerButton, SecondaryButton, card_frame
import modules.virement as vir_mod
import modules.client   as cli_mod


class TabVirement(tk.Frame):
    """Onglet '💸 Effectuer un Virement'."""

    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, bg=BG_ROOT, **kwargs)
        self.app = app
        self._build()

    def _build(self):
        # Titre
        tk.Label(self, text="💸  Effectuer un Virement Bancaire",
                 bg=BG_ROOT, fg=FG_PRIMARY, font=FONT_SUBTITLE).pack(
            anchor="w", padx=PAD_X, pady=(PAD_Y, 0))

        tk.Label(self,
                 text="Formule :  Nouveau solde = Ancien solde − Montant  (géré automatiquement par trigger PostgreSQL)",
                 bg=BG_ROOT, fg=FG_SECONDARY, font=("Segoe UI", 9, "italic")).pack(
            anchor="w", padx=PAD_X, pady=(0, PAD_Y))

        # Corps centré
        center = tk.Frame(self, bg=BG_ROOT)
        center.pack(fill="both", expand=True)

        # Carte formulaire
        card_outer = card_frame(center, bg=BG_CARD)
        card_outer.place(relx=0.5, rely=0.48, anchor="center", width=560, height=520)
        card = card_outer.inner

        # ── En-tête de la carte ───────────────────────────
        hdr = tk.Frame(card, bg=BG_HEADER)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🔄  Nouveau Virement",
                 bg=BG_HEADER, fg=FG_HEADER, font=FONT_LABEL_B).pack(
            side="left", padx=14, pady=10)

        # ── Champs ───────────────────────────────────────
        body = tk.Frame(card, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=30, pady=15)

        def field(parent, label, var, row):
            tk.Label(parent, text=label, bg=BG_CARD,
                     fg=FG_SECONDARY, font=FONT_LABEL).grid(
                row=row, column=0, sticky="w", pady=(0, 2))
            e = ttk.Entry(parent, textvariable=var, width=32, font=FONT_MONO)
            e.grid(row=row+1, column=0, columnspan=2, sticky="ew",
                   pady=(0, 12), ipady=5)
            return e

        self.v_src  = tk.StringVar()
        self.v_dest = tk.StringVar()
        self.v_mont = tk.StringVar()

        body.columnconfigure(0, weight=1)

        field(body, "📤  Compte Source (débiteur)", self.v_src, 0)
        field(body, "📥  Compte Destination (créditeur)", self.v_dest, 2)
        field(body, "💵  Montant (Ar)", self.v_mont, 4)

        # Aperçu solde
        self.lbl_preview = tk.Label(body, text="",
                                     bg=BG_CARD, fg=ACCENT_GREEN,
                                     font=("Consolas", 10, "italic"))
        self.lbl_preview.grid(row=6, column=0, sticky="w", pady=(0, 6))

        # Trace pour mise à jour en temps réel
        self.v_src.trace("w", self._on_src_change)

        # Boutons
        btn_frame = tk.Frame(body, bg=BG_CARD)
        btn_frame.grid(row=7, column=0, sticky="ew", pady=(10, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        GreenButton(btn_frame, text="✔  VALIDER LE VIREMENT",
                    command=self._valider).grid(
            row=0, column=0, sticky="ew", padx=(0, 4), ipady=6)

        SecondaryButton(btn_frame, text="🔄  Réinitialiser",
                        command=self._reset).grid(
            row=0, column=1, sticky="ew", padx=(4, 0))

        # ── Résumé de confirmation ────────────────────────
        self.lbl_confirm = tk.Label(card, text="",
                                     bg=BG_CARD, fg=ACCENT_GREEN,
                                     font=("Segoe UI", 9, "bold"),
                                     wraplength=480)
        self.lbl_confirm.pack(pady=(0, 10))

    # ─────────────────────────────────────────────────────
    #  LOGIQUE
    # ─────────────────────────────────────────────────────

    def _on_src_change(self, *_):
        nc = self.v_src.get().strip()
        if nc:
            c = cli_mod.get_client_by_compte(nc)
            if c:
                self.lbl_preview.config(
                    text=f"✅  {c['nomclient']}  —  Solde : {c['solde']:,.2f} Ar",
                    fg=ACCENT_GREEN)
            else:
                self.lbl_preview.config(text="⚠  Compte introuvable", fg=ACCENT_RED)
        else:
            self.lbl_preview.config(text="")

    def _valider(self):
        src  = self.v_src.get().strip()
        dest = self.v_dest.get().strip()
        mont = self.v_mont.get().strip()

        if not src or not dest or not mont:
            messagebox.showwarning("Champs manquants",
                                   "Tous les champs sont obligatoires.", parent=self)
            return
        try:
            montant = float(mont)
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide (nombre attendu).", parent=self)
            return

        # Récupérer infos avant confirmation
        c_src  = cli_mod.get_client_by_compte(src)
        c_dest = cli_mod.get_client_by_compte(dest)

        if not c_src:
            messagebox.showerror("Erreur", f"Compte source '{src}' introuvable.", parent=self)
            return
        if not c_dest:
            messagebox.showerror("Erreur", f"Compte destination '{dest}' introuvable.", parent=self)
            return

        confirm = messagebox.askyesno(
            "Confirmer le virement",
            f"Voulez-vous confirmer ce virement ?\n\n"
            f"  De    : {src}  ({c_src['nomclient']})\n"
            f"  Vers  : {dest}  ({c_dest['nomclient']})\n"
            f"  Montant : {montant:,.2f} Ar\n\n"
            f"  Solde actuel source : {c_src['solde']:,.2f} Ar",
            parent=self
        )
        if not confirm:
            return

        try:
            nv = vir_mod.effectuer_virement(src, dest, montant)
            msg = (f"✅ Virement n°{nv} effectué avec succès !\n\n"
                   f"  Montant transféré : {montant:,.2f} Ar\n"
                   f"  Nouveau solde source ≈ {c_src['solde'] - montant:,.2f} Ar\n\n"
                   f"  Les triggers PostgreSQL ont été déclenchés :\n"
                   f"  • trg_audit_insert  → audit enregistré\n"
                   f"  • trg_update_solde  → soldes mis à jour")
            messagebox.showinfo("Succès", msg, parent=self)
            self.lbl_confirm.config(
                text=f"✅  Virement n°{nv}  |  {montant:,.2f} Ar  |  {src} → {dest}",
                fg=ACCENT_GREEN)
            self.app.set_status(
                f"✅ Virement n°{nv} — {montant:,.2f} Ar  |  {src} → {dest}")
            self._reset()
            self.app.refresh_all()
        except (ValueError, RuntimeError) as e:
            messagebox.showerror("Virement refusé", str(e), parent=self)
            self.lbl_confirm.config(text=f"❌  {e}", fg=ACCENT_RED)

    def _reset(self):
        self.v_src.set("")
        self.v_dest.set("")
        self.v_mont.set("")
        self.lbl_preview.config(text="")

    def refresh(self):
        """Rien à recharger dans cet onglet."""
        pass
