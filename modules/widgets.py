"""
widgets.py — Composants UI réutilisables (thème Blanc/Vert)
"""

import tkinter as tk
from tkinter import ttk
from modules.styles import *


def apply_ttk_styles(root: tk.Tk) -> None:
    """Configure les styles ttk globaux pour l'application."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # ── Notebook ──────────────────────────────────────────
    style.configure("TNotebook",
        background=BG_ROOT, borderwidth=0)
    style.configure("TNotebook.Tab",
        background=BG_SIDEBAR, foreground=FG_SECONDARY,
        padding=[20, 9], font=FONT_LABEL_B, borderwidth=0)
    style.map("TNotebook.Tab",
        background=[("selected", BG_HEADER), ("active", "#c8e6d4")],
        foreground=[("selected", FG_HEADER),  ("active", FG_PRIMARY)])

    # ── Treeview ──────────────────────────────────────────
    style.configure("Treeview",
        background=BG_TABLE_ROW, foreground=FG_TABLE,
        fieldbackground=BG_TABLE_ROW,
        rowheight=28, font=FONT_TABLE, borderwidth=0)
    style.configure("Treeview.Heading",
        background=BG_TABLE_HDR, foreground=FG_TABLE_HDR,
        font=FONT_TABLE_H, relief="flat")
    style.map("Treeview",
        background=[("selected", ACCENT_GREEN)],
        foreground=[("selected", "#ffffff")])

    # ── Frame / Label ────────────────────────────────────
    style.configure("TFrame", background=BG_ROOT)
    style.configure("Card.TFrame", background=BG_CARD,
        relief="flat", borderwidth=1)
    style.configure("TLabel",
        background=BG_ROOT, foreground=FG_PRIMARY, font=FONT_LABEL)
    style.configure("Card.TLabel",
        background=BG_CARD, foreground=FG_PRIMARY, font=FONT_LABEL)

    # ── Entry ─────────────────────────────────────────────
    style.configure("TEntry",
        fieldbackground=BG_INPUT, foreground=FG_PRIMARY,
        bordercolor=BORDER, font=FONT_INPUT, padding=5)
    style.map("TEntry",
        bordercolor=[("focus", BORDER_FOCUS)])

    # ── Combobox ──────────────────────────────────────────
    style.configure("TCombobox",
        fieldbackground=BG_INPUT, foreground=FG_PRIMARY,
        background=BG_CARD, font=FONT_INPUT)

    # ── Scrollbar ─────────────────────────────────────────
    style.configure("TScrollbar",
        background=BORDER, troughcolor=BG_ROOT,
        arrowcolor=FG_SECONDARY, borderwidth=0)


# ─────────────────────────────────────────────────────
#  COMPOSANTS RÉUTILISABLES
# ─────────────────────────────────────────────────────

class GreenButton(tk.Button):
    def __init__(self, parent, **kwargs):
        bg    = kwargs.pop("bg", ACCENT_GREEN)
        hover = kwargs.pop("hover_bg", ACCENT_HOVER)

        super().__init__(parent,
            bg=bg,
            fg="#ffffff",
            font=FONT_BTN,
            relief="flat",
            activebackground=hover,
            activeforeground="#ffffff",
            cursor="hand2",
            **kwargs)               # ← on laisse padx/pady venir de l'appelant

        self.bind("<Enter>", lambda _: self.config(bg=hover))
        self.bind("<Leave>", lambda _: self.config(bg=bg))

class DangerButton(tk.Button):
    """Bouton rouge (suppression)."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent,
            bg=ACCENT_RED, fg="#ffffff",
            font=FONT_BTN, relief="flat",
            activebackground="#922b21",
            activeforeground="#ffffff",
            cursor="hand2", padx=BTN_PAD_X, pady=BTN_PAD_Y,
            **kwargs)
        self.bind("<Enter>", lambda _: self.config(bg="#922b21"))
        self.bind("<Leave>", lambda _: self.config(bg=ACCENT_RED))


class SecondaryButton(tk.Button):
    """Bouton secondaire gris-vert."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent,
            bg=BG_SIDEBAR, fg=FG_PRIMARY,
            font=FONT_BTN_SM, relief="flat",
            activebackground=BORDER, cursor="hand2",
            padx=10, pady=4, **kwargs)


class StatCard(tk.Frame):
    """Carte de statistique (icône + valeur + label)."""
    def __init__(self, parent, label: str, value: str = "0",
                 color: str = ACCENT_GREEN, icon: str = "", **kwargs):
        super().__init__(parent, bg=BG_CARD,
            relief="flat", bd=0, **kwargs)

        # Barre colorée gauche
        bar = tk.Frame(self, bg=color, width=5)
        bar.pack(side="left", fill="y")

        inner = tk.Frame(self, bg=BG_CARD)
        inner.pack(fill="both", expand=True, padx=14, pady=10)

        tk.Label(inner, text=f"{icon}  {label}",
                 bg=BG_CARD, fg=FG_SECONDARY,
                 font=FONT_STAT_LBL).pack(anchor="w")

        self.val_lbl = tk.Label(inner, text=value,
                                 bg=BG_CARD, fg=color,
                                 font=FONT_STAT)
        self.val_lbl.pack(anchor="w")

    def update_value(self, value: str) -> None:
        self.val_lbl.config(text=value)


class LabelEntry(tk.Frame):
    """Label + Entry dans un Frame vertical."""
    def __init__(self, parent, label: str, var: tk.Variable,
                 width: int = 30, bg: str = BG_CARD, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        tk.Label(self, text=label, bg=bg,
                 fg=FG_SECONDARY, font=FONT_LABEL).pack(anchor="w")
        ttk.Entry(self, textvariable=var, width=width).pack(
            fill="x", pady=(2, 8), ipady=4)


def make_treeview(parent, columns: list, headings: dict,
                  widths: dict, height: int = 18):
    """
    Crée un Treeview avec scrollbar vertical.
    Retourne (treeview, scrollbar_frame).
    """
    frame = tk.Frame(parent, bg=BG_ROOT)

    tv = ttk.Treeview(frame, columns=columns, show="headings", height=height)
    tv.tag_configure("insert", background=COLOR_INSERT, foreground=FG_INSERT)
    tv.tag_configure("update", background=COLOR_UPDATE, foreground=FG_UPDATE)
    tv.tag_configure("delete", background=COLOR_DELETE, foreground=FG_DELETE)
    tv.tag_configure("alt",    background=BG_TABLE_ALT)

    for col in columns:
        tv.heading(col, text=headings.get(col, col))
        tv.column(col, width=widths.get(col, 100), anchor="center")

    sb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)

    tv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    return tv, frame


def card_frame(parent, title: str = "", bg: str = BG_CARD) -> tk.Frame:
    """Retourne un Frame 'carte' avec ombre simulée et titre optionnel."""
    outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
    inner = tk.Frame(outer, bg=bg)
    inner.pack(fill="both", expand=True)
    if title:
        tk.Label(inner, text=title, bg=bg,
                 fg=FG_SECONDARY, font=FONT_LABEL_B).pack(
            anchor="w", padx=14, pady=(10, 4))
    outer.inner = inner
    return outer
