"""
Locres CSV Tools — Icarus UE4  v3
Tabs: Importar · Comparar · Editor CSV
Definicoes: Idioma + Tema
"""
import csv, os, sys, tkinter as tk
try:
    from pypresence import Presence
    HAS_PRESENCE = True
except ImportError:
    HAS_PRESENCE = False
from tkinter import filedialog, messagebox, scrolledtext, ttk
from configparser import ConfigParser

try:
    from pylocres import LocresFile, Namespace, Entry, entry_hash
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pylocres"])
    from pylocres import LocresFile, Namespace, Entry, entry_hash

# ─── Caminhos ────────────────────────────────────────────────────────────────
# BASE compatível com execução normal e PyInstaller onedir
if getattr(sys, "frozen", False):
    BASE   = os.path.dirname(sys.executable)
    ASSETS = sys._MEIPASS          # ficheiros embutidos no .exe
else:
    BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ASSETS = BASE                  # em desenvolvimento usa BASE normalmente
SETTINGS    = os.path.join(BASE, "Settings.ini")
VERSION     = "v1.1"  # fallback — sobrescrito por load_lang()
DISCORD_ID  = "1500142270131863683"
THEMES_DIR  = os.path.join(BASE, "Themes")
LANG_DIR    = os.path.join(BASE, "Lang")

LANGS  = {"Português (PT)": "pt", "English (EN)": "en"}
THEMES = {
    "Catppuccin Mocha": "catppuccin",
    "Dracula":          "dracula",
    "Nord":             "nord",
    "Tokyo Night":      "tokyo_night",
    "Gruvbox Dark":     "gruvbox",
    "One Dark":         "one_dark",
    "Monokai":          "monokai",
}

# ─── Tema (paleta global) ────────────────────────────────────────────────────
C = {}

def load_theme(tid):
    global C
    path = os.path.join(THEMES_DIR, f"theme_{tid}.ini")
    cfg  = ConfigParser(interpolation=None)
    if os.path.isfile(path):
        cfg.read(path, encoding="utf-8")
    def g(k, fb): return cfg.get("colors", k, fallback=fb)
    C.update({
        "bg":     g("bg",     "#1e1e2e"),
        "bg2":    g("bg2",    "#181825"),
        "bg3":    g("bg3",    "#313244"),
        "bg4":    g("bg4",    "#45475a"),
        "fg":     g("fg",     "#cdd6f4"),
        "fg2":    g("fg2",    "#a6adc8"),
        "fg3":    g("fg3",    "#6c7086"),
        "accent": g("accent", "#cba6f7"),
        "green":  g("green",  "#a6e3a1"),
        "red":    g("red",    "#f38ba8"),
        "yellow": g("yellow", "#f9e2af"),
        "blue":   g("blue",   "#89b4fa"),
        "cyan":   g("cyan",   "#89dceb"),
        "orange": g("orange", "#fab387"),
        "bg_row": g("bg_row", "#202030"),
    })

# ─── Tradução ────────────────────────────────────────────────────────────────
_TR = {}

def load_lang(code):
    global _TR, VERSION; _TR = {}
    path = os.path.join(LANG_DIR, f"lang_{code}.ini")
    if not os.path.isfile(path): return
    cfg = ConfigParser(interpolation=None)
    cfg.read(path, encoding="utf-8")
    for sec in cfg.sections():
        for k, v in cfg.items(sec):
            _TR[f"{sec}.{k}"] = v
    # Versão centralizada no ficheiro de tradução
    VERSION = _TR.get("app.version", VERSION)

def T(key, **kw):
    v = _TR.get(key, key)
    try:   return v.format(**kw) if kw else v
    except: return v

# ─── Settings ────────────────────────────────────────────────────────────────
def load_settings():
    cfg = ConfigParser()
    cfg.read(SETTINGS, encoding="utf-8")
    return {
        "lang":  cfg.get("app", "lang",  fallback="pt"),
        "theme": cfg.get("app", "theme", fallback="catppuccin"),
    }

def save_settings(d):
    cfg = ConfigParser(); cfg["app"] = d
    with open(SETTINGS, "w", encoding="utf-8") as f: cfg.write(f)


# ─── Discord Rich Presence ───────────────────────────────────────────────────
class RichPresence:
    """Gere o Discord Rich Presence de forma segura (ignora erros se Discord fechado)."""
    def __init__(self):
        self._rpc  = None
        self._active = False
        self._connect()

    def _connect(self):
        if not HAS_PRESENCE: return
        try:
            self._rpc = Presence(DISCORD_ID)
            self._rpc.connect()
            self._active = True
        except Exception:
            self._active = False

    def update(self, state, details="LocresTools", tab=None):
        if not self._active: return
        try:
            self._rpc.update(
                state   = state,
                details = details,
                large_image = "logo",
                large_text  = f"LocresTools {VERSION}",
                small_image = None,
            )
        except Exception:
            self._active = False

    def clear(self):
        if not self._active: return
        try:   self._rpc.clear()
        except: pass

    def close(self):
        if not self._active: return
        try:   self._rpc.close()
        except: pass

# ─── Widget helpers ──────────────────────────────────────────────────────────
def mkbtn(parent, text, cmd, bg=None, fg=None, px=8):
    b = tk.Button(parent, text=text, command=cmd,
                  font=("Segoe UI", 10),
                  bg=bg or C["bg3"], fg=fg or C["fg"],
                  relief="flat", padx=px, cursor="hand2", bd=0,
                  activebackground=C["bg4"],
                  activeforeground=fg or C["fg"])
    b.bind("<Enter>", lambda _: b.config(bg=C["bg4"]))
    b.bind("<Leave>", lambda _: b.config(bg=bg or C["bg3"]))
    return b

def mklbl(parent, text, bold=False, fg=None, size=10):
    f = ("Segoe UI", size, "bold") if bold else ("Segoe UI", size)
    return tk.Label(parent, text=text, font=f, bg=C["bg"],
                    fg=fg or (C["accent"] if bold else C["fg"]))

def mkent(parent, var):
    return tk.Entry(parent, textvariable=var,
                    font=("Segoe UI", 10), bg=C["bg3"], fg=C["fg"],
                    insertbackground=C["fg"], relief="flat", bd=4)

def mklog(parent, height=12):
    return scrolledtext.ScrolledText(parent,
        font=("Consolas", 9), bg=C["bg2"], fg=C["green"],
        insertbackground=C["fg"], relief="flat", bd=0, height=height)

# ─── Lógica: Importar ────────────────────────────────────────────────────────
def import_csv_into_locres(locres_path, csv_path, out_path, log):
    log(f"A ler: {locres_path}")
    lf = LocresFile(); lf.read(locres_path)
    log(f"  Versão: {lf.version.name} | Namespaces: {len(lf.namespaces)}")
    idx = {}; nsi = {}; total = 0
    for ns in lf:
        nsi[ns.name.lower()] = ns
        for e in ns:
            total += 1
            idx[f"{ns.name}/{e.key}".lower()] = e
            idx[e.key.lower()] = e
    log(f"  {total} entradas indexadas")
    if total == 0: log("ERRO: 0 entradas"); return False
    log(f"\nA ler CSV: {csv_path}")
    rows = []
    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with open(csv_path, encoding=enc, newline="") as f:
                rows = list(csv.DictReader(f))
            log(f"  {enc} | {len(rows)} linhas"); break
        except UnicodeDecodeError: continue
    if not rows: log("ERRO: não foi possível ler"); return False
    cm = {c.lower().strip(): c for c in rows[0].keys()}
    col_key = cm.get("key") or cm.get("chave")
    if not col_key: log("ERRO: coluna 'key' não encontrada"); return False
    ct = cm.get("target", ""); cs = cm.get("source", "")
    nt = sum(1 for r in rows if str(r.get(ct, "") or "").strip()) if ct else 0
    ns2= sum(1 for r in rows if str(r.get(cs, "") or "").strip()) if cs else 0
    col_trans = ct if nt >= ns2 and nt > 0 else cs
    log(f"  Tradução: '{'target' if col_trans==ct else 'source'}' ({max(nt,ns2)} preench.)")
    upd = ins = skip = 0
    for row in rows:
        k = str(row.get(col_key, "") or "").strip()
        v = str(row.get(col_trans, "") or "").strip()
        if not k or not v: skip += 1; continue
        e = idx.get(k.lower())
        if e: e.translation = v; upd += 1
        else:
            nn = k.split("/")[0] if "/" in k else ""; ek = k[len(nn)+1:] if "/" in k else k
            no = nsi.get(nn.lower())
            if not no: no = Namespace(nn); lf.add(no); nsi[nn.lower()] = no
            ne = Entry(ek, v, 0, is_hash=True); no.add(ne)
            idx[k.lower()] = ne; idx[ek.lower()] = ne; ins += 1
    log(f"\n  ✔ Actualizadas:{upd}  ✚ Inseridas:{ins}  – Ignoradas:{skip}")
    if upd + ins == 0: log("AVISO: nenhuma entrada processada"); return False
    log(f"\nA escrever: {out_path}")
    lf.write(out_path)
    log(f"  ✔ {upd+ins} entradas | {os.path.getsize(out_path)//1024} KB")
    return True

# ─── Lógica: Comparar ────────────────────────────────────────────────────────
def _read_dict(path):
    for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
        try:
            with open(path, encoding=enc, newline="") as f:
                return {r["key"].strip(): r for r in csv.DictReader(f)}, enc
        except: continue
    return {}, ""

def _tcol(rows):
    if not rows: return "", ""
    s = next(iter(rows.values()))
    cm = {c.lower().strip(): c for c in s.keys()}
    ct = cm.get("target", ""); cs = cm.get("source", "")
    nt = sum(1 for r in rows.values() if str(r.get(ct,"") or "").strip()) if ct else 0
    ns = sum(1 for r in rows.values() if str(r.get(cs,"") or "").strip()) if cs else 0
    return (ct, "target") if nt >= ns and nt > 0 else (cs, "source")

def compare_csvs(pa, pb, mode):
    a, _ = _read_dict(pa); b, _ = _read_dict(pb)
    ca, _ = _tcol(a); cb, _ = _tcol(b)
    oa = sorted(k for k in a if k not in b)
    ob = sorted(k for k in b if k not in a)
    df = sorted(k for k in (a.keys() & b.keys())
                if str(a[k].get(ca,"") or "").strip() != str(b[k].get(cb,"") or "").strip())
    ta = T("compare.tag_only_a"); tb2 = T("compare.tag_only_b"); td = T("compare.tag_diff")
    res = []
    if mode in ("missing_in_b", "all"):
        for k in oa: res.append((ta, k, str(a[k].get(ca,"") or "").strip(), ""))
    if mode in ("missing_in_a", "all"):
        for k in ob: res.append((tb2, k, "", str(b[k].get(cb,"") or "").strip()))
    if mode in ("different", "all"):
        for k in df: res.append((td, k, str(a[k].get(ca,"") or "").strip(), str(b[k].get(cb,"") or "").strip()))
    return res, {"only_a": len(oa), "only_b": len(ob), "different": len(df)}


# ════════════════════════════════════════════════════════════════════════════
# APLICAÇÃO
# ════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self, settings, rpc=None):
        super().__init__()
        self._s = settings
        self._rpc = rpc
        self.title(f"{T('app.title')} {VERSION}")
        self.resizable(True, True)
        self.minsize(960, 700)
        # Ícone da aplicação
        _icon = os.path.join(ASSETS, "Data", "LocresToolsIcon.ico")
        if os.path.isfile(_icon):
            try: self.iconbitmap(_icon)
            except: pass
        self._rebuild()

    def _rebuild(self):
        """Reconstrói toda a UI (chamado ao mudar tema ou idioma)."""
        self.configure(bg=C["bg"])
        for w in self.winfo_children(): w.destroy()
        self._apply_ttk_style()

        # ── Header ────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["bg2"])
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=C["accent"], height=3).pack(fill="x")
        hrow = tk.Frame(hdr, bg=C["bg2"], padx=14, pady=8)
        hrow.pack(fill="x")
        # Logo — ícone real do .ico
        try:
            from PIL import Image, ImageTk
            _ico = os.path.join(ASSETS, "Data", "LocresToolsIcon.ico")
            _pil = Image.open(_ico).resize((48, 48), Image.LANCZOS)
            self._hdr_img = ImageTk.PhotoImage(_pil)
            tk.Label(hrow, image=self._hdr_img, bg=C["bg2"]).pack(side="left", padx=(0, 8))
        except:
            tk.Label(hrow, text="⬡", font=("Segoe UI", 16),
                     bg=C["bg2"], fg=C["accent"]).pack(side="left", padx=(0, 8))
        self._hdr_var = tk.StringVar(value=f"LocresTools {VERSION}")
        tk.Label(hrow, textvariable=self._hdr_var, font=("Segoe UI", 11, "bold"),
                 bg=C["bg2"], fg=C["fg"]).pack(side="left")
        # Botão definições
        mkbtn(hrow, f"⚙  {T('app.settings_btn')}",
              self._open_settings, bg=C["bg3"], px=12).pack(side="right", padx=(4, 0))
        mkbtn(hrow, "ℹ  Info",
              self._open_info, bg=C["bg3"], px=12).pack(side="right")
        tk.Frame(hdr, bg=C["bg3"], height=1).pack(fill="x")

        # ── Notebook ──────────────────────────────────────────────────────
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=6, pady=6)
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

        t1 = ttk.Frame(self.nb); self.nb.add(t1, text=f"  {T('tabs.import')}  ")
        t2 = ttk.Frame(self.nb); self.nb.add(t2, text=f"  {T('tabs.compare')}  ")
        t3 = ttk.Frame(self.nb); self.nb.add(t3, text=f"  {T('tabs.editor')}  ")

        self._build_import(t1)
        self._build_compare(t2)
        self._build_editor(t3)

        # Ctrl+S
        self.bind_all("<Control-s>", lambda _: self._ed_save())
        self.bind_all("<Control-S>", lambda _: self._ed_save())

    def _apply_ttk_style(self):
        s = ttk.Style(self); s.theme_use("default")
        s.configure("TNotebook",     background=C["bg2"], borderwidth=0)
        s.configure("TNotebook.Tab", background=C["bg3"], foreground=C["fg2"],
                    font=("Segoe UI", 10, "bold"), padding=[16, 8])
        s.map("TNotebook.Tab",
              background=[("selected", C["bg4"])],
              foreground=[("selected", C["accent"])])
        s.configure("TFrame", background=C["bg"])
        for n in ("LT", "ED"):
            s.configure(f"{n}.Treeview",
                        background=C["bg2"], foreground=C["fg"],
                        fieldbackground=C["bg2"], rowheight=28,
                        font=("Consolas", 9), borderwidth=0)
            s.configure(f"{n}.Treeview.Heading",
                        background=C["bg3"], foreground=C["accent"],
                        font=("Segoe UI", 10, "bold"), relief="flat", padding=8)
            s.map(f"{n}.Treeview",
                  background=[("selected", C["bg4"])],
                  foreground=[("selected", C["fg"])])
        s.configure("TScrollbar", background=C["bg3"], troughcolor=C["bg2"],
                    borderwidth=0, arrowcolor=C["fg3"], relief="flat")
        s.map("TScrollbar", background=[("active", C["bg4"])])
        s.configure("TCombobox",
                    fieldbackground=C["bg3"], background=C["bg3"],
                    foreground=C["fg"], selectbackground=C["bg4"],
                    selectforeground=C["fg"], borderwidth=0)
        s.map("TCombobox", fieldbackground=[("readonly", C["bg3"])])

    # ── Definições ────────────────────────────────────────────────────────
    def _on_tab_change(self, _):
        if not self._rpc: return
        try:
            tab_idx = self.nb.index(self.nb.select())
            tab_names = [
                T("tabs.import"),
                T("tabs.compare"),
                T("tabs.editor"),
            ]
            tab = tab_names[tab_idx] if tab_idx < len(tab_names) else "?"
            self._rpc.update(
                state   = tab,
                details = "LocresTools",
                large_image = "logo",
                large_text  = f"LocresTools {VERSION}",
            )
        except Exception:
            pass

    def _open_info(self):
        win = tk.Toplevel(self)
        win.title("Info")
        win.configure(bg=C["bg"])
        win.resizable(False, False)
        win.grab_set()
        _ico = os.path.join(ASSETS, "Data", "LocresToolsIcon.ico")
        if os.path.isfile(_ico):
            try: win.iconbitmap(_ico)
            except: pass
        self.update_idletasks()
        x = self.winfo_x() + self.winfo_width()  // 2 - 210
        y = self.winfo_y() + self.winfo_height() // 2 - 150
        win.geometry(f"480x430+{x}+{y}")

        tk.Frame(win, bg=C["accent"], height=3).pack(fill="x")
        tk.Label(win, text=f"ℹ  {T('info.info_title')}", font=("Segoe UI", 11, "bold"),
                 bg=C["bg"], fg=C["accent"], anchor="w",
                 padx=16, pady=10).pack(fill="x")
        tk.Frame(win, bg=C["bg3"], height=1).pack(fill="x")

        inner = tk.Frame(win, bg=C["bg"], padx=12, pady=8)
        inner.pack(fill="both", expand=True)

        # Banner da app
        try:
            from PIL import Image, ImageTk
            _banner_path = os.path.join(ASSETS, "Data", "banner.png")
            _new_w = 430
            _new_h = int(576 * _new_w / 1024)
            _banner_img = Image.open(_banner_path).resize((_new_w, _new_h), Image.LANCZOS)
            _banner_tk = ImageTk.PhotoImage(_banner_img)
            _lbl_banner = tk.Label(inner, image=_banner_tk, bg=C["bg"])
            _lbl_banner.image = _banner_tk
            _lbl_banner.pack(fill="x", pady=(0, 14))
        except:
            top = tk.Frame(inner, bg=C["bg"]); top.pack(fill="x", pady=(0, 16))
            tk.Label(top, text="⬡", font=("Segoe UI", 28),
                     bg=C["bg"], fg=C["accent"]).pack(side="left", padx=(0, 12))
            txt = tk.Frame(top, bg=C["bg"]); txt.pack(side="left", anchor="w")
            tk.Label(txt, text="LocresTools", font=("Segoe UI", 14, "bold"),
                     bg=C["bg"], fg=C["fg"]).pack(anchor="w")
            tk.Label(txt, text=T("info.info_subtitle"),
                     font=("Segoe UI", 9), bg=C["bg"], fg=C["fg3"]).pack(anchor="w")

        tk.Frame(inner, bg=C["bg3"], height=1).pack(fill="x", pady=(0, 14))

        def info_row(label, value, val_color=None):
            r = tk.Frame(inner, bg=C["bg"]); r.pack(fill="x", pady=3)
            tk.Label(r, text=label, font=("Segoe UI", 9, "bold"),
                     bg=C["bg"], fg=C["fg3"], width=14, anchor="w").pack(side="left")
            tk.Label(r, text=value, font=("Segoe UI", 10),
                     bg=C["bg"], fg=val_color or C["fg"]).pack(side="left")

        info_row(T("info.info_version"),  VERSION)
        info_row(T("info.info_dev"),       "DarkEsteves", C["accent"])
        info_row(T("info.info_contact"),   "JetDrugas@hotmail.com", C["cyan"])
        info_row(T("info.info_platform"),  "Icarus UE4")

        tk.Frame(inner, bg=C["bg3"], height=1).pack(fill="x", pady=(14, 10))
        mkbtn(inner, T("info.info_close"), win.destroy,
              bg=C["bg3"], px=14).pack(anchor="e")

    def _open_settings(self):
        win = tk.Toplevel(self)
        win.title(T("settings.window_title"))
        win.configure(bg=C["bg"])
        win.resizable(False, False)
        win.grab_set()
        _ico = os.path.join(ASSETS, "Data", "LocresToolsIcon.ico")
        if os.path.isfile(_ico):
            try: win.iconbitmap(_ico)
            except: pass
        self.update_idletasks()
        x = self.winfo_x() + self.winfo_width()  // 2 - 240
        y = self.winfo_y() + self.winfo_height() // 2 - 120
        win.geometry(f"480x215+{x}+{y}")

        tk.Frame(win, bg=C["accent"], height=3).pack(fill="x")
        tk.Label(win, text=T("settings.window_title"),
                 font=("Segoe UI", 11, "bold"),
                 bg=C["bg"], fg=C["accent"], anchor="w",
                 padx=16, pady=10).pack(fill="x")
        tk.Frame(win, bg=C["bg3"], height=1).pack(fill="x")

        inner = tk.Frame(win, bg=C["bg"], padx=20, pady=14)
        inner.pack(fill="both", expand=True)
        inner.columnconfigure(1, weight=1)

        def row_widget(r, label, var, choices):
            tk.Label(inner, text=label, font=("Segoe UI", 10, "bold"),
                     bg=C["bg"], fg=C["fg2"]).grid(
                         row=r, column=0, sticky="w", pady=(0, 10))
            cb = ttk.Combobox(inner, textvariable=var, values=choices,
                              state="readonly", width=26,
                              font=("Segoe UI", 10))
            cb.grid(row=r, column=1, sticky="w", padx=(12, 0), pady=(0, 10))

        lang_var  = tk.StringVar()
        theme_var = tk.StringVar()

        cur_lang  = next((n for n, c in LANGS.items()
                          if c == self._s.get("lang", "pt")), list(LANGS)[0])
        cur_theme = next((n for n, c in THEMES.items()
                          if c == self._s.get("theme", "catppuccin")), list(THEMES)[0])
        lang_var.set(cur_lang); theme_var.set(cur_theme)

        row_widget(0, T("settings.lang_label"),  lang_var,  list(LANGS.keys()))
        row_widget(1, "Tema:",                    theme_var, list(THEMES.keys()))

        tk.Label(inner, text=T("settings.restart_info"),
                 font=("Segoe UI", 9), bg=C["bg"], fg=C["fg3"]).grid(
                     row=2, column=0, columnspan=2, sticky="w", pady=(0, 14))

        bf = tk.Frame(inner, bg=C["bg"])
        bf.grid(row=3, column=0, columnspan=2, sticky="w")

        def _save():
            self._s["lang"]  = LANGS.get(lang_var.get(),  "pt")
            self._s["theme"] = THEMES.get(theme_var.get(), "catppuccin")
            save_settings(self._s)
            load_lang(self._s["lang"])
            load_theme(self._s["theme"])
            win.destroy()
            self._rebuild()
            messagebox.showinfo(T("settings.window_title"), T("settings.saved_msg"))

        mkbtn(bf, T("settings.save_btn"),   _save,
              bg="#2a4a2a", fg=C["green"], px=14).pack(side="left", padx=(0, 8))
        mkbtn(bf, T("settings.cancel_btn"), win.destroy,
              bg="#4a2a2a", fg=C["red"],   px=12).pack(side="left")

    # ════════════════════════════════════════════════════════════════════
    # TAB 1 — IMPORTAR
    # ════════════════════════════════════════════════════════════════════
    def _build_import(self, p):
        p.configure(style="TFrame")
        self.vi_locres = tk.StringVar()
        self.vi_csv    = tk.StringVar()
        self.vi_out    = tk.StringVar()

        wrap = tk.Frame(p, bg=C["bg"])
        wrap.pack(fill="both", expand=True, padx=14, pady=10)
        wrap.columnconfigure(0, weight=1)

        def file_card(row_num, icon, label_key, var, browse_cmd):
            fr = tk.Frame(wrap, bg=C["bg2"], relief="flat")
            fr.grid(row=row_num, column=0, sticky="ew", pady=(0, 6))
            fr.columnconfigure(1, weight=1)
            tk.Frame(fr, bg=C["accent"], width=4).grid(
                row=0, column=0, rowspan=2, sticky="ns")
            tk.Label(fr, text=icon, font=("Segoe UI", 13),
                     bg=C["bg2"], fg=C["accent"]).grid(
                         row=0, column=1, padx=(10, 6), pady=(8, 0), sticky="w")
            tk.Label(fr, text=T(label_key),
                     font=("Segoe UI", 9, "bold"),
                     bg=C["bg2"], fg=C["fg3"], anchor="w").grid(
                         row=0, column=2, columnspan=2, sticky="w", pady=(8, 0))
            tk.Entry(fr, textvariable=var, font=("Consolas", 9),
                     bg=C["bg3"], fg=C["fg"], insertbackground=C["fg"],
                     relief="flat", bd=3).grid(
                         row=1, column=1, columnspan=2, sticky="ew",
                         padx=(10, 4), pady=(2, 8))
            mkbtn(fr, T("import.browse"), browse_cmd, px=8).grid(
                row=1, column=3, padx=(0, 8), pady=(2, 8))
            fr.columnconfigure(2, weight=1)

        file_card(0, "📄", "import.section1", self.vi_locres, self._i_bl)
        file_card(1, "📊", "import.section2", self.vi_csv,    self._i_bc)
        file_card(2, "💾", "import.section3", self.vi_out,    self._i_bo)

        mkbtn(wrap, T("import.run_btn"), self._i_run,
              bg=C["accent"], fg=C["bg"], px=16).grid(
                  row=3, column=0, sticky="ew", pady=10, ipady=5)

        # Log header
        lhdr = tk.Frame(wrap, bg=C["bg3"])
        lhdr.grid(row=4, column=0, sticky="ew")
        tk.Label(lhdr, text="●", font=("Segoe UI", 9),
                 bg=C["bg3"], fg=C["green"]).pack(side="left", padx=(10, 4), pady=3)
        tk.Label(lhdr, text=T("import.log_label"),
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg3"], fg=C["fg2"]).pack(side="left", pady=3)

        self.ilog = scrolledtext.ScrolledText(
            wrap, font=("Consolas", 9), bg=C["bg2"], fg=C["green"],
            insertbackground=C["fg"], relief="flat", bd=0, height=11)
        self.ilog.grid(row=5, column=0, sticky="nsew")
        wrap.rowconfigure(5, weight=1)

    def _i_bl(self):
        p = filedialog.askopenfilename(
            filetypes=[("Locres", "*.locres"), ("Todos", "*.*")])
        if p:
            self.vi_locres.set(p)
            if not self.vi_out.get():
                b, e = os.path.splitext(p); self.vi_out.set(b + "_PT" + e)
            self._hdr_var.set(f"LocresTools {VERSION}  —  {p}")

    def _i_bc(self):
        p = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if p: self.vi_csv.set(p)

    def _i_bo(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".locres",
            filetypes=[("Locres", "*.locres"), ("Todos", "*.*")])
        if p: self.vi_out.set(p)

    def _ilog(self, m):
        self.ilog.insert(tk.END, m + "\n")
        self.ilog.see(tk.END); self.update_idletasks()

    def _i_run(self):
        l = self.vi_locres.get().strip()
        c = self.vi_csv.get().strip()
        o = self.vi_out.get().strip()
        self.ilog.delete("1.0", tk.END)
        if not os.path.isfile(l):
            messagebox.showerror("", T("import.err_locres")); return
        if not os.path.isfile(c):
            messagebox.showerror("", T("import.err_csv")); return
        if not o:
            messagebox.showerror("", T("import.err_out")); return
        try:
            ok = import_csv_into_locres(l, c, o, self._ilog)
            if ok: messagebox.showinfo(T("import.done_title"),
                                       T("import.done_msg") + f"\n\n{o}")
        except Exception as ex:
            self._ilog(f"\nERRO: {ex}")
            import traceback; self._ilog(traceback.format_exc())
            messagebox.showerror("", str(ex))

    # ════════════════════════════════════════════════════════════════════
    # TAB 2 — COMPARAR
    # ════════════════════════════════════════════════════════════════════
    def _build_compare(self, parent):
        parent.configure(style="TFrame")
        top = tk.Frame(parent, bg=C["bg"])
        top.pack(fill="x", padx=10, pady=(10, 0))

        # Frames CSV A / B
        self.vc_a = tk.StringVar(); self.vc_b = tk.StringVar()
        for var, lkey, color in [
            (self.vc_a, "compare.csv_a_label", C["red"]),
            (self.vc_b, "compare.csv_b_label", C["blue"]),
        ]:
            fr = tk.Frame(top, bg=C["bg2"])
            fr.pack(fill="x", pady=(0, 4))
            tk.Frame(fr, bg=color, width=4).pack(side="left", fill="y")
            inn = tk.Frame(fr, bg=C["bg2"], padx=10, pady=7)
            inn.pack(side="left", fill="x", expand=True)
            tk.Label(inn, text=T(lkey), font=("Segoe UI", 9, "bold"),
                     bg=C["bg2"], fg=color).pack(anchor="w")
            r2 = tk.Frame(inn, bg=C["bg2"]); r2.pack(fill="x", pady=(4, 0))
            tk.Entry(r2, textvariable=var, font=("Consolas", 9),
                     bg=C["bg3"], fg=C["fg"], insertbackground=C["fg"],
                     relief="flat", bd=3).pack(side="left", fill="x", expand=True)
            # capturar var corretamente na closure
            _v = var
            mkbtn(r2, T("compare.browse"),
                  lambda v=_v: self._c_browse(v),
                  px=8).pack(side="left", padx=(6, 0))

        # Controles
        ctrl = tk.Frame(top, bg=C["bg"]); ctrl.pack(fill="x", pady=(6, 4))
        mklbl(ctrl, T("compare.show_label"), bold=True).pack(side="left", padx=(0, 8))
        self.vc_mode = tk.StringVar(value="all")
        for label, val, col in [
            (T("compare.filter_only_a"), "missing_in_b", C["red"]),
            (T("compare.filter_only_b"), "missing_in_a", C["blue"]),
            (T("compare.filter_diff"),   "different",    C["yellow"]),
            (T("compare.filter_all"),    "all",          C["accent"]),
        ]:
            tk.Radiobutton(ctrl, text=label, variable=self.vc_mode, value=val,
                           font=("Segoe UI", 9), bg=C["bg"], fg=col,
                           selectcolor=C["bg3"], activebackground=C["bg"],
                           indicatoron=0, relief="flat",
                           padx=8, pady=4, cursor="hand2", bd=1).pack(side="left", padx=3)

        tk.Label(ctrl, text="  🔍", bg=C["bg"], fg=C["fg3"]).pack(side="left", padx=(12, 2))
        self.vc_search = tk.StringVar()
        self.vc_search.trace_add("write", lambda *_: self._c_filter())
        tk.Entry(ctrl, textvariable=self.vc_search,
                 font=("Segoe UI", 10), bg=C["bg3"], fg=C["fg"],
                 insertbackground=C["fg"], relief="flat", bd=3,
                 width=22).pack(side="left", padx=(0, 8))
        mkbtn(ctrl, T("compare.run_btn"), self._c_run,
              bg=C["accent"], fg=C["bg"], px=12).pack(side="left", padx=(0, 4))
        mkbtn(ctrl, T("compare.export_btn"),
              self._c_export, px=10).pack(side="left")

        # Status bar
        self.vc_status = tk.StringVar(value=T("compare.status_init"))
        sb = tk.Frame(top, bg=C["bg3"]); sb.pack(fill="x", pady=(4, 6))
        tk.Label(sb, textvariable=self.vc_status,
                 font=("Segoe UI", 9), bg=C["bg3"], fg=C["fg2"],
                 anchor="w", padx=8, pady=3).pack(fill="x")

        # Treeview
        tf = tk.Frame(parent, bg=C["bg"])
        tf.pack(fill="both", expand=True, padx=10, pady=(0, 4))
        self.ctree = ttk.Treeview(
            tf, columns=("sit", "key", "ta", "tb"),
            show="headings", style="LT.Treeview", selectmode="browse")
        for col, tkey, w, stretch in [
            ("sit", "compare.col_status", 110, False),
            ("key", "compare.col_key",   330, True),
            ("ta",  "compare.col_text_a",245, True),
            ("tb",  "compare.col_text_b",245, True),
        ]:
            self.ctree.heading(col, text=T(tkey), anchor="w")
            self.ctree.column(col, width=w, minwidth=60, stretch=stretch)
        self.ctree.tag_configure("only_a",    foreground=C["red"])
        self.ctree.tag_configure("only_b",    foreground=C["blue"])
        self.ctree.tag_configure("different", foreground=C["yellow"])
        self.ctree.tag_configure("even",      background=C["bg_row"])
        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self.ctree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal",  command=self.ctree.xview)
        self.ctree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.ctree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tf.columnconfigure(0, weight=1); tf.rowconfigure(0, weight=1)

        # Painel detalhes
        prev = tk.Frame(parent, bg=C["bg2"])
        prev.pack(fill="x", padx=10, pady=(0, 8))
        tk.Frame(prev, bg=C["accent"], height=2).pack(fill="x")
        ph = tk.Frame(prev, bg=C["bg2"], padx=8, pady=5); ph.pack(fill="x")
        tk.Label(ph, text=T("compare.details_label"),
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg2"], fg=C["accent"]).pack(side="left")
        mkbtn(ph, T("compare.copy_key_btn"), self._c_copy_key,
              px=8).pack(side="right")
        self.cprev_key = tk.Text(prev, height=1, font=("Consolas", 9),
                                  bg=C["bg3"], fg=C["accent"],
                                  relief="flat", bd=4)
        self.cprev_key.pack(fill="x", padx=8, pady=(0, 4))
        pf = tk.Frame(prev, bg=C["bg2"]); pf.pack(fill="x", padx=8, pady=(0, 8))
        self.cprev_a = scrolledtext.ScrolledText(
            pf, height=2, font=("Consolas", 9),
            bg=C["bg3"], fg=C["red"], relief="flat", bd=4)
        self.cprev_a.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.cprev_b = scrolledtext.ScrolledText(
            pf, height=2, font=("Consolas", 9),
            bg=C["bg3"], fg=C["blue"], relief="flat", bd=4)
        self.cprev_b.pack(side="left", fill="both", expand=True)
        self.ctree.bind("<<TreeviewSelect>>", self._c_on_select)
        self._cmp_data = []

    def _c_browse(self, var):
        p = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if p: var.set(p)

    def _c_run(self):
        a = self.vc_a.get().strip(); b = self.vc_b.get().strip()
        if not os.path.isfile(a):
            messagebox.showerror("", T("compare.err_csv_a")); return
        if not os.path.isfile(b):
            messagebox.showerror("", T("compare.err_csv_b")); return
        self.vc_status.set(T("compare.status_compare")); self.update_idletasks()
        data, st = compare_csvs(a, b, self.vc_mode.get())
        self._cmp_data = data; self.vc_search.set(""); self._c_populate(data)
        self.vc_status.set(T("compare.status_result",
            a=st["only_a"], b=st["only_b"], d=st["different"], t=len(data)))

    def _c_populate(self, data):
        for i in self.ctree.get_children(): self.ctree.delete(i)
        ta  = T("compare.tag_only_a")
        tb2 = T("compare.tag_only_b")
        td  = T("compare.tag_diff")
        tm  = {ta: "only_a", tb2: "only_b", td: "different"}
        for i, (sit, key, a, b) in enumerate(data):
            tags = (tm.get(sit, "different"),) + (("even",) if i % 2 == 0 else ())
            self.ctree.insert("", "end", values=(sit, key, a, b), tags=tags)

    def _c_filter(self):
        q = self.vc_search.get().lower().strip()
        f = [(s, k, a, b) for s, k, a, b in self._cmp_data
             if not q or any(q in x.lower() for x in (s, k, a, b))]
        self._c_populate(f)
        self.vc_status.set(T("compare.status_filter",
            q=q, v=len(f), t=len(self._cmp_data)))

    def _c_on_select(self, _):
        sel = self.ctree.selection()
        if not sel: return
        _, key, ta, tb = self.ctree.item(sel[0], "values")
        self.cprev_key.config(state="normal")
        self.cprev_key.delete("1.0", "end")
        self.cprev_key.insert("end", key)
        self.cprev_key.config(state="disabled")
        self.cprev_a.delete("1.0", "end"); self.cprev_a.insert("end", ta)
        self.cprev_b.delete("1.0", "end"); self.cprev_b.insert("end", tb)

    def _c_copy_key(self):
        sel = self.ctree.selection()
        if not sel: return
        self.clipboard_clear()
        self.clipboard_append(self.ctree.item(sel[0], "values")[1])

    def _c_export(self):
        if not self._cmp_data:
            messagebox.showwarning("", T("compare.export_warn")); return
        out = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if not out: return
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow([T("compare.col_status"), T("compare.col_key"),
                        T("compare.col_text_a"), T("compare.col_text_b")])
            w.writerows(self._cmp_data)
        messagebox.showinfo("", T("compare.export_done", n=len(self._cmp_data)))

    # ════════════════════════════════════════════════════════════════════
    # TAB 3 — EDITOR CSV
    # ════════════════════════════════════════════════════════════════════
    def _build_editor(self, parent):
        parent.configure(style="TFrame")
        self._ed_path      = None
        self._ed_rows      = []
        self._ed_modified  = {}
        self._ed_col_key   = "key"
        self._ed_col_src   = "source"
        self._ed_col_tgt   = "target"
        self._ed_all_iids  = []
        self._ed_sel_iid   = None

        # Toolbar
        tb = tk.Frame(parent, bg=C["bg2"]); tb.pack(fill="x")
        tk.Frame(tb, bg=C["bg3"], height=1).pack(fill="x")
        tbr = tk.Frame(tb, bg=C["bg2"], pady=6); tbr.pack(fill="x", padx=6)

        mkbtn(tbr, T("editor.open_btn"),    self._ed_open,            px=10).pack(side="left", padx=(0, 3))
        mkbtn(tbr, T("editor.save_btn"),    self._ed_save,            px=10).pack(side="left", padx=3)
        mkbtn(tbr, T("editor.save_as_btn"), self._ed_save_as,         px=10).pack(side="left", padx=3)
        tk.Frame(tbr, bg=C["bg4"], width=1).pack(side="left", fill="y", padx=8, pady=2)
        mkbtn(tbr, T("editor.reset_all_btn"),  self._ed_reset_all,
              fg=C["orange"], px=10).pack(side="left", padx=3)
        mkbtn(tbr, T("editor.export_mod_btn"), self._ed_export_modified,
              fg=C["yellow"], px=10).pack(side="left", padx=3)
        tk.Frame(tbr, bg=C["bg4"], width=1).pack(side="left", fill="y", padx=8, pady=2)
        tk.Label(tbr, text=T("editor.edit_col_label"),
                 font=("Segoe UI", 9), bg=C["bg2"],
                 fg=C["fg3"]).pack(side="left", padx=(0, 6))
        self._ed_edit_col = tk.StringVar(value="source")
        for txt, val, col in [("source", "source", C["cyan"]),
                               ("target", "target", C["green"])]:
            tk.Radiobutton(tbr, text=txt, variable=self._ed_edit_col, value=val,
                           font=("Segoe UI", 9), bg=C["bg2"], fg=col,
                           selectcolor=C["bg3"], activebackground=C["bg2"],
                           indicatoron=0, relief="flat",
                           padx=8, pady=3, cursor="hand2", bd=1).pack(side="left", padx=2)

        # Search bar
        sb = tk.Frame(parent, bg=C["bg3"]); sb.pack(fill="x")
        tk.Label(sb, text="🔍", bg=C["bg3"],
                 fg=C["fg3"]).pack(side="left", padx=(10, 4), pady=4)
        self._ed_search = tk.StringVar()
        self._ed_search.trace_add("write", lambda *_: self._ed_filter())
        tk.Entry(sb, textvariable=self._ed_search,
                 font=("Segoe UI", 10), bg=C["bg2"], fg=C["fg"],
                 insertbackground=C["fg"], relief="flat", bd=0,
                 width=30).pack(side="left", pady=4)
        tk.Frame(sb, bg=C["bg4"], width=1).pack(side="left", fill="y", padx=8, pady=3)
        self._ed_fmode = tk.StringVar(value="all")
        for txt, val, col in [
            (T("editor.filter_all"),      "all",      C["fg"]),
            (T("editor.filter_modified"), "modified", C["yellow"]),
            (T("editor.filter_empty"),    "empty",    C["red"]),
        ]:
            tk.Radiobutton(sb, text=txt, variable=self._ed_fmode, value=val,
                           font=("Segoe UI", 9), bg=C["bg3"], fg=col,
                           selectcolor=C["bg2"], activebackground=C["bg3"],
                           indicatoron=0, relief="flat",
                           padx=7, pady=3, cursor="hand2", bd=1,
                           command=self._ed_filter).pack(side="left", padx=2, pady=3)
        self._ed_status = tk.StringVar(value=T("editor.status_init"))
        tk.Label(sb, textvariable=self._ed_status,
                 font=("Segoe UI", 9), bg=C["bg3"],
                 fg=C["fg3"], anchor="e", padx=10).pack(side="right")

        # Treeview
        tf = tk.Frame(parent, bg=C["bg"]); tf.pack(fill="both", expand=True)
        self.etree = ttk.Treeview(
            tf, columns=("i", "key", "src", "tgt"),
            show="headings", style="ED.Treeview", selectmode="browse")
        for col, tkey, w, anc, stretch in [
            ("i",   "editor.col_num",    52,  "center", False),
            ("key", "editor.col_key",   300,  "w",      True),
            ("src", "editor.col_source",310,  "w",      True),
            ("tgt", "editor.col_target",310,  "w",      True),
        ]:
            self.etree.heading(col, text=T(tkey), anchor=anc)
            self.etree.column(col, width=w,
                              minwidth=40 if col == "i" else 80,
                              stretch=stretch, anchor=anc)
        self.etree.tag_configure("modified", foreground=C["yellow"], background="#2a2a18")
        self.etree.tag_configure("empty",    foreground=C["red"],    background="#2a1818")
        self.etree.tag_configure("even",     background=C["bg_row"])
        self.etree.tag_configure("normal",   foreground=C["fg"])
        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self.etree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal",  command=self.etree.xview)
        self.etree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.etree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tf.columnconfigure(0, weight=1); tf.rowconfigure(0, weight=1)

        # Edit panel
        ep = tk.Frame(parent, bg=C["bg2"]); ep.pack(fill="x")
        tk.Frame(ep, bg=C["accent"], height=2).pack(fill="x")

        # Key row
        kr = tk.Frame(ep, bg=C["bg2"], padx=10, pady=5); kr.pack(fill="x")
        tk.Label(kr, text=T("editor.key_label"),
                 font=("Segoe UI", 9, "bold"),
                 bg=C["bg2"], fg=C["fg3"]).pack(side="left")
        self._ed_key_var = tk.StringVar()
        tk.Entry(kr, textvariable=self._ed_key_var,
                 font=("Consolas", 9), bg=C["bg2"], fg=C["accent"],
                 relief="flat", bd=0, state="readonly",
                 readonlybackground=C["bg2"]).pack(
                     side="left", fill="x", expand=True, padx=(6, 0))
        mkbtn(kr, T("editor.copy_key_btn"),
              self._ed_copy_key, px=8).pack(side="right")

        # Source + Target
        er = tk.Frame(ep, bg=C["bg2"]); er.pack(fill="x", padx=10, pady=(0, 4))
        for label, color, attr in [
            (T("editor.source_label"), C["cyan"],  "_ed_src_box"),
            (T("editor.target_label"), C["green"], "_ed_tgt_box"),
        ]:
            pad = (0, 4) if attr == "_ed_src_box" else (0, 0)
            f = tk.Frame(er, bg=C["bg2"])
            f.pack(side="left", fill="both", expand=True, padx=pad)
            hd = tk.Frame(f, bg=C["bg2"]); hd.pack(fill="x")
            tk.Label(hd, text="▌", font=("Segoe UI", 9),
                     bg=C["bg2"], fg=color).pack(side="left")
            tk.Label(hd, text=label, font=("Segoe UI", 9, "bold"),
                     bg=C["bg2"], fg=color).pack(side="left")
            box = tk.Text(f, height=3, font=("Consolas", 9),
                          bg=C["bg3"], fg=color, insertbackground=color,
                          relief="flat", bd=4, wrap="word", undo=True)
            box.pack(fill="both", expand=True, pady=(2, 0))
            setattr(self, attr, box)

        # Action row
        ar = tk.Frame(ep, bg=C["bg2"], padx=10, pady=6); ar.pack(fill="x")
        mkbtn(ar, T("editor.apply_btn"),  self._ed_apply,
              bg="#1e3a1e", fg=C["green"], px=12).pack(side="left", padx=(0, 4))
        mkbtn(ar, T("editor.cancel_btn"), self._ed_cancel,
              bg="#3a1e1e", fg=C["red"],   px=10).pack(side="left", padx=(0, 4))
        mkbtn(ar, T("editor.reset_row_btn"), self._ed_reset_row,
              fg=C["orange"], px=8).pack(side="left", padx=(0, 4))
        tk.Label(ar, text=T("editor.hint"),
                 font=("Segoe UI", 8), bg=C["bg2"],
                 fg=C["fg3"]).pack(side="right")

        # Bindings
        self.etree.bind("<Double-1>",         self._ed_on_double)
        self.etree.bind("<<TreeviewSelect>>",  self._ed_on_select)
        self.etree.bind("<Return>",            lambda _: self._ed_apply())
        self.etree.bind("<Escape>",            lambda _: self._ed_cancel())
        self.etree.bind("<Up>",                self._ed_nav_up)
        self.etree.bind("<Down>",              self._ed_nav_down)
        self.etree.bind("<Button-3>",          self._ed_ctx)

        # Context menu
        self._ctx = tk.Menu(self, tearoff=0,
                            bg=C["bg3"], fg=C["fg"],
                            activebackground=C["bg4"],
                            activeforeground=C["accent"],
                            font=("Segoe UI", 10), bd=0, relief="flat")
        self._ctx.add_command(label=T("editor.ctx_copy_key"),  command=self._ed_copy_key)
        self._ctx.add_command(label=T("editor.ctx_copy_src"),  command=lambda: self._ed_copy_col("source"))
        self._ctx.add_command(label=T("editor.ctx_copy_tgt"),  command=lambda: self._ed_copy_col("target"))
        self._ctx.add_separator()
        self._ctx.add_command(label=T("editor.ctx_reset_row"), command=self._ed_reset_row)
        self._ctx.add_command(label=T("editor.ctx_clear_src"), command=lambda: self._ed_clear_col("source"))
        self._ctx.add_command(label=T("editor.ctx_clear_tgt"), command=lambda: self._ed_clear_col("target"))

    # ── Editor helpers ─────────────────────────────────────────────────
    def _ed_open(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if not path: return
        rows = []
        for enc in ["utf-8-sig", "utf-8", "cp1252", "latin-1"]:
            try:
                with open(path, encoding=enc, newline="") as f:
                    rows = list(csv.DictReader(f)); break
            except UnicodeDecodeError: continue
        if not rows:
            messagebox.showerror("", T("editor.err_open")); return
        cm = {c.lower().strip(): c for c in rows[0].keys()}
        self._ed_col_key = cm.get("key",    "key")
        self._ed_col_src = cm.get("source", "source")
        self._ed_col_tgt = cm.get("target", "target")
        self._ed_path = path; self._ed_rows = rows; self._ed_modified = {}
        self.title(f"{T('app.title')} {VERSION}")
        self._ed_pop_all()

    def _ed_pop_all(self):
        for i in self.etree.get_children(): self.etree.delete(i)
        self._ed_all_iids = []
        for idx, row in enumerate(self._ed_rows, 1):
            src = str(row.get(self._ed_col_src, "") or "")
            tgt = str(row.get(self._ed_col_tgt, "") or "")
            key = str(row.get(self._ed_col_key, "") or "")
            iid = self.etree.insert("", "end",
                values=(idx, key, src, tgt),
                tags=self._ed_tags(idx - 1, src, tgt, False))
            self._ed_all_iids.append(iid)
        self._ed_upd()

    def _ed_tags(self, idx, src, tgt, mod):
        t = ["modified" if mod else ("empty" if not src and not tgt else "normal")]
        if idx % 2 == 0: t.append("even")
        return tuple(t)

    def _ed_upd(self):
        tot = len(self._ed_rows)
        mod = len(self._ed_modified)
        emp = sum(1 for r in self._ed_rows
                  if not str(r.get(self._ed_col_src, "") or "").strip()
                  and not str(r.get(self._ed_col_tgt, "") or "").strip())
        self._ed_status.set(T("editor.status_info",
            t=tot, m=mod, e=emp,
            f=os.path.basename(self._ed_path or "—")))

    def _ed_save(self):
        if not self._ed_path: self._ed_save_as(); return
        self._ed_write(self._ed_path)

    def _ed_save_as(self):
        if not self._ed_rows:
            messagebox.showwarning("", T("editor.err_no_file")); return
        p = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if p: self._ed_path = p; self._ed_write(p)

    def _ed_write(self, path):
        cols = list(self._ed_rows[0].keys())
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader(); w.writerows(self._ed_rows)
        messagebox.showinfo("", T("editor.save_done") + f"\n{path}")
        self.title(f"{T('app.title')} {VERSION}")

    def _ed_export_modified(self):
        if not self._ed_modified:
            messagebox.showwarning("", T("editor.export_mod_warn")); return
        p = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")])
        if not p: return
        cols = list(self._ed_rows[0].keys())
        mod_rows = [self._ed_rows[int(self.etree.item(iid, "values")[0]) - 1]
                    for iid in self._ed_modified]
        with open(p, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader(); w.writerows(mod_rows)
        messagebox.showinfo("", T("editor.export_mod_done", n=len(mod_rows)))

    def _ed_filter(self):
        q    = self._ed_search.get().lower().strip()
        mode = self._ed_fmode.get()
        for iid in self.etree.get_children(): self.etree.detach(iid)
        v = 0
        for iid in self._ed_all_iids:
            _, key, src, tgt = self.etree.item(iid, "values")
            im = iid in self._ed_modified
            ie = not src.strip() and not tgt.strip()
            if mode == "modified" and not im: continue
            if mode == "empty"    and not ie: continue
            if q and not any(q in x.lower() for x in (key, src, tgt)): continue
            self.etree.reattach(iid, "", "end"); v += 1
        self._ed_status.set(T("editor.status_filter",
            v=v, t=len(self._ed_rows),
            m=len(self._ed_modified), q=q))

    def _ed_on_select(self, _):
        sel = self.etree.selection()
        if not sel: return
        self._ed_sel_iid = sel[0]
        _, key, src, tgt = self.etree.item(sel[0], "values")
        self._ed_key_var.set(key)
        self._ed_src_box.delete("1.0", "end"); self._ed_src_box.insert("end", src)
        self._ed_tgt_box.delete("1.0", "end"); self._ed_tgt_box.insert("end", tgt)

    def _ed_on_double(self, _):
        if not self.etree.selection(): return
        box = (self._ed_src_box if self._ed_edit_col.get() == "source"
               else self._ed_tgt_box)
        box.focus_set(); box.mark_set("insert", "end")

    def _ed_apply(self):
        if not self._ed_sel_iid: return
        iid  = self._ed_sel_iid
        vals = self.etree.item(iid, "values")
        idx  = int(vals[0]) - 1
        ns   = self._ed_src_box.get("1.0", "end-1c").strip()
        nt   = self._ed_tgt_box.get("1.0", "end-1c").strip()
        self._ed_rows[idx][self._ed_col_src] = ns
        self._ed_rows[idx][self._ed_col_tgt] = nt
        self._ed_modified[iid] = True
        self.etree.item(iid, values=(vals[0], vals[1], ns, nt),
                         tags=self._ed_tags(idx, ns, nt, True))
        self._ed_upd(); self._ed_nav_down(None)

    def _ed_cancel(self):
        if not self._ed_sel_iid: return
        vals = self.etree.item(self._ed_sel_iid, "values")
        self._ed_src_box.delete("1.0", "end"); self._ed_src_box.insert("end", vals[2])
        self._ed_tgt_box.delete("1.0", "end"); self._ed_tgt_box.insert("end", vals[3])
        self.etree.focus_set()

    def _ed_reset_row(self):
        if not self._ed_sel_iid: return
        iid  = self._ed_sel_iid
        vals = self.etree.item(iid, "values")
        idx  = int(vals[0]) - 1
        src  = str(self._ed_rows[idx].get(self._ed_col_src, "") or "")
        tgt  = str(self._ed_rows[idx].get(self._ed_col_tgt, "") or "")
        self._ed_src_box.delete("1.0", "end"); self._ed_src_box.insert("end", src)
        self._ed_tgt_box.delete("1.0", "end"); self._ed_tgt_box.insert("end", tgt)
        self._ed_modified.pop(iid, None)
        self.etree.item(iid, tags=self._ed_tags(idx, src, tgt, False))
        self._ed_upd()

    def _ed_reset_all(self):
        if not self._ed_modified: return
        if not messagebox.askyesno("", T("editor.reset_confirm")): return
        self._ed_modified.clear()
        for iid in self._ed_all_iids:
            vals = self.etree.item(iid, "values")
            idx  = int(vals[0]) - 1
            src  = str(self._ed_rows[idx].get(self._ed_col_src, "") or "")
            tgt  = str(self._ed_rows[idx].get(self._ed_col_tgt, "") or "")
            self.etree.item(iid, tags=self._ed_tags(idx, src, tgt, False))
        self._ed_upd()

    def _ed_nav_up(self, _):
        sel = self.etree.selection()
        if not sel: return
        prev = self.etree.prev(sel[0])
        if prev:
            self.etree.selection_set(prev)
            self.etree.focus(prev)
            self.etree.see(prev)

    def _ed_nav_down(self, _):
        sel = self.etree.selection()
        if not sel: return
        nxt = self.etree.next(sel[0])
        if nxt:
            self.etree.selection_set(nxt)
            self.etree.focus(nxt)
            self.etree.see(nxt)

    def _ed_copy_key(self):
        if not self._ed_sel_iid: return
        self.clipboard_clear()
        self.clipboard_append(self.etree.item(self._ed_sel_iid, "values")[1])

    def _ed_copy_col(self, col):
        if not self._ed_sel_iid: return
        idx = {"source": 2, "target": 3}.get(col, 2)
        self.clipboard_clear()
        self.clipboard_append(self.etree.item(self._ed_sel_iid, "values")[idx])

    def _ed_clear_col(self, col):
        if not self._ed_sel_iid: return
        (self._ed_src_box if col == "source" else self._ed_tgt_box).delete("1.0", "end")
        self._ed_apply()

    def _ed_ctx(self, event):
        iid = self.etree.identify_row(event.y)
        if iid:
            self.etree.selection_set(iid)
            self._ctx.tk_popup(event.x_root, event.y_root)


# ── Arranque ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    s = load_settings()
    load_lang(s.get("lang", "pt"))
    load_theme(s.get("theme", "catppuccin"))
    rpc = RichPresence()
    app = App(s, rpc)
    app.mainloop()
    rpc.close()
