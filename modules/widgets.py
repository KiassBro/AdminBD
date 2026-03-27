"""
widgets.py — Composants UI réutilisables + boîtes de dialogue personnalisées
"""
import tkinter as tk
from tkinter import ttk
from modules.styles import *


# ════════════════════════════════════════════════════════
#  STYLES TTK
# ════════════════════════════════════════════════════════

def apply_styles(root):
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure("TNotebook", background=BG_ROOT, borderwidth=0)
    s.configure("TNotebook.Tab",
        background=BG_SIDEBAR, foreground=FG_SECONDARY,
        padding=[22, 10], font=F_LABEL_B, borderwidth=0)
    s.map("TNotebook.Tab",
        background=[("selected", GREEN_DARK), ("active", "#C8E6D5")],
        foreground=[("selected", FG_HEAD),    ("active", FG_PRIMARY)])

    s.configure("Treeview",
        background=BG_CARD, foreground=FG_TABLE,
        fieldbackground=BG_CARD, rowheight=30, font=F_TABLE, borderwidth=0)
    s.configure("Treeview.Heading",
        background=TBL_HDR_BG, foreground=FG_TABLE_H,
        font=F_TABLE_H, relief="flat", padding=[6,6])
    s.map("Treeview",
        background=[("selected", GREEN_MED)],
        foreground=[("selected", "#FFFFFF")])

    s.configure("TFrame",  background=BG_ROOT)
    s.configure("TLabel",  background=BG_ROOT, foreground=FG_PRIMARY, font=F_LABEL)
    s.configure("TEntry",  fieldbackground=BG_INPUT, foreground=FG_PRIMARY,
                           font=F_INPUT, padding=6)
    s.configure("TCombobox", fieldbackground=BG_INPUT, foreground=FG_PRIMARY,
                             font=F_INPUT, padding=6)
    s.map("TCombobox",
        fieldbackground=[("readonly", BG_INPUT)],
        foreground=[("readonly", FG_PRIMARY)])
    s.configure("TScrollbar",
        background=BORDER, troughcolor=BG_ROOT,
        arrowcolor=FG_SECONDARY, borderwidth=0, gripcount=0)


# ════════════════════════════════════════════════════════
#  BOUTONS
# ════════════════════════════════════════════════════════

class Btn(tk.Button):
    """Bouton stylé générique."""
    def __init__(self, parent, color=GREEN_DARK, hover=GREEN_MED, **kw):
        kw.setdefault("padx", 16)
        kw.setdefault("pady", 6)
        super().__init__(parent, bg=color, fg="#fff",
            font=F_BTN, relief="flat", cursor="hand2",
            activebackground=hover, activeforeground="#fff",
            bd=0, **kw)
        self._c = color; self._h = hover
        self.bind("<Enter>", lambda _: self.config(bg=self._h))
        self.bind("<Leave>", lambda _: self.config(bg=self._c))

class BtnDanger(Btn):
    def __init__(self, parent, **kw):
        super().__init__(parent, color=RED, hover=RED_DARK, **kw)

class BtnOrange(Btn):
    def __init__(self, parent, **kw):
        super().__init__(parent, color=ORANGE, hover=ORANGE_DARK, **kw)

class BtnGhost(tk.Button):
    def __init__(self, parent, **kw):
        kw.setdefault("padx", 12)
        kw.setdefault("pady", 5)
        super().__init__(parent, bg=BG_SIDEBAR, fg=FG_PRIMARY,
            font=F_BTN_SM, relief="flat", cursor="hand2",
            activebackground=BORDER, bd=0, **kw)


# ════════════════════════════════════════════════════════
#  STAT CARD
# ════════════════════════════════════════════════════════

class StatCard(tk.Frame):
    def __init__(self, parent, label, value="0", color=GREEN_DARK, icon="", **kw):
        super().__init__(parent, bg=BG_CARD, **kw)
        # Barre latérale colorée
        tk.Frame(self, bg=color, width=4).pack(side="left", fill="y")
        body = tk.Frame(self, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=14, pady=10)
        tk.Label(body, text=f"{icon}  {label}",
                 bg=BG_CARD, fg=FG_MUTED, font=F_STAT_L).pack(anchor="w")
        self._lbl = tk.Label(body, text=value,
                              bg=BG_CARD, fg=color, font=F_STAT_V)
        self._lbl.pack(anchor="w")

    def set(self, v): self._lbl.config(text=str(v))


# ════════════════════════════════════════════════════════
#  TREEVIEW HELPER
# ════════════════════════════════════════════════════════

def make_tree(parent, cols, hdrs, widths, height=16):
    frame = tk.Frame(parent, bg=BG_ROOT)
    tv = ttk.Treeview(frame, columns=cols, show="headings", height=height)
    tv.tag_configure("ins", background=INS_BG, foreground=INS_FG)
    tv.tag_configure("upd", background=UPD_BG, foreground=UPD_FG)
    tv.tag_configure("del", background=DEL_BG, foreground=DEL_FG)
    tv.tag_configure("alt", background=BG_ROW_ALT)
    tv.tag_configure("neg", foreground=RED)
    for c in cols:
        tv.heading(c, text=hdrs.get(c, c))
        tv.column(c, width=widths.get(c, 100), anchor="center", minwidth=50)
    sb = ttk.Scrollbar(frame, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    tv.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return tv, frame


# ════════════════════════════════════════════════════════
#  BOÎTES DE DIALOGUE PERSONNALISÉES
# ════════════════════════════════════════════════════════

class _BaseDialog(tk.Toplevel):
    """Base pour toutes les boîtes de dialogue."""
    ICONS = {"success": ("✅", GREEN_DARK), "error": ("❌", RED),
             "warning": ("⚠️", ORANGE),   "question": ("❓", BLUE),
             "info":    ("ℹ️", BLUE)}

    def __init__(self, parent, title, message, kind="info"):
        super().__init__(parent)
        self.result = False
        icon, color = self.ICONS.get(kind, ("ℹ️", BLUE))
        self.title(title)
        self.configure(bg=BG_CARD)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self._color = color
        self._icon  = icon
        self._msg   = message
        self._build(title, message, icon, color)
        # Centrer sur le parent
        self.update_idletasks()
        pw = parent.winfo_rootx(); ph = parent.winfo_rooty()
        pw2 = parent.winfo_width(); ph2 = parent.winfo_height()
        x = pw + (pw2 - self.winfo_width())  // 2
        y = ph + (ph2 - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self, title, message, icon, color):
        # Bande couleur en haut
        top = tk.Frame(self, bg=color, height=5)
        top.pack(fill="x")
        # Corps
        body = tk.Frame(self, bg=BG_CARD)
        body.pack(fill="both", expand=True, padx=28, pady=(20, 16))
        # Icône + titre
        row1 = tk.Frame(body, bg=BG_CARD)
        row1.pack(fill="x", pady=(0, 10))
        tk.Label(row1, text=icon, bg=BG_CARD, font=("Segoe UI", 22)).pack(side="left", padx=(0,12))
        tk.Label(row1, text=title, bg=BG_CARD, fg=FG_PRIMARY, font=F_SECTION,
                 wraplength=340, justify="left").pack(side="left", anchor="w")
        # Message
        tk.Label(body, text=message, bg=BG_CARD, fg=FG_SECONDARY,
                 font=F_LABEL, wraplength=380, justify="left").pack(anchor="w", pady=(0,18))
        # Séparateur
        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(0,14))
        # Boutons (à surcharger)
        self._build_buttons(body, color)

    def _build_buttons(self, body, color):
        Btn(body, text="  OK  ", color=color, hover=color,
            command=self._ok).pack(anchor="e")

    def _ok(self):
        self.result = True; self.destroy()


class MsgSuccess(_BaseDialog):
    def __init__(self, parent, message, title="Succès"):
        super().__init__(parent, title, message, kind="success")

class MsgError(_BaseDialog):
    def __init__(self, parent, message, title="Erreur"):
        super().__init__(parent, title, message, kind="error")

class MsgWarning(_BaseDialog):
    def __init__(self, parent, message, title="Avertissement"):
        super().__init__(parent, title, message, kind="warning")

class MsgInfo(_BaseDialog):
    def __init__(self, parent, message, title="Information"):
        super().__init__(parent, title, message, kind="info")


class MsgConfirm(_BaseDialog):
    """Boîte de confirmation Oui / Non."""
    def __init__(self, parent, message, title="Confirmer"):
        super().__init__(parent, title, message, kind="question")

    def _build_buttons(self, body, color):
        row = tk.Frame(body, bg=BG_CARD)
        row.pack(anchor="e")
        BtnGhost(row, text="  Annuler  ",
                 command=self.destroy).pack(side="left", padx=(0,8))
        Btn(row, text="  Oui, confirmer  ", color=color, hover=GREEN_MED,
            command=self._ok).pack(side="left")

    def ask(self) -> bool:
        self.wait_window()
        return self.result


class MsgInput(_BaseDialog):
    """Boîte de saisie personnalisée."""
    def __init__(self, parent, message, title="Saisie", default=""):
        self._default = default
        self._value   = None
        super().__init__(parent, title, message, kind="info")

    def _build_buttons(self, body, color):
        self._var = tk.StringVar(value=self._default)
        e = ttk.Entry(body, textvariable=self._var, width=28, font=F_MONO)
        e.pack(anchor="w", pady=(0, 14), ipady=4)
        e.focus_set()
        e.bind("<Return>", lambda _: self._ok())
        row = tk.Frame(body, bg=BG_CARD)
        row.pack(anchor="e")
        BtnGhost(row, text="  Annuler  ", command=self.destroy).pack(side="left", padx=(0,8))
        Btn(row, text="  Valider  ", color=color,
            command=self._ok).pack(side="left")

    def _ok(self):
        self._value = self._var.get()
        self.result = True
        self.destroy()

    def get_value(self):
        self.wait_window()
        return self._value if self.result else None


# ════════════════════════════════════════════════════════
#  FORMULAIRE LABEL + ENTRY / COMBOBOX
# ════════════════════════════════════════════════════════

def form_field(parent, label, var, bg=BG_CARD, width=30, readonly=False):
    """Label au-dessus + Entry en dessous."""
    tk.Label(parent, text=label, bg=bg, fg=FG_SECONDARY, font=F_LABEL).pack(anchor="w")
    state = "readonly" if readonly else "normal"
    e = ttk.Entry(parent, textvariable=var, width=width, state=state)
    e.pack(fill="x", pady=(2, 10), ipady=5)
    return e

def form_combo(parent, label, var, values, bg=BG_CARD, width=30, callback=None):
    """Label au-dessus + Combobox en dessous."""
    tk.Label(parent, text=label, bg=bg, fg=FG_SECONDARY, font=F_LABEL).pack(anchor="w")
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      width=width, state="readonly", font=F_INPUT)
    cb.pack(fill="x", pady=(2, 10), ipady=5)
    if callback:
        cb.bind("<<ComboboxSelected>>", lambda _: callback())
    return cb
