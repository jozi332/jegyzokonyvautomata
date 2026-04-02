import json
import os
import shutil
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox, filedialog
import tkinter.font as tkfont

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


class CustomColorPicker(tk.Toplevel):
    def __init__(self, parent, initialcolor="#ffffff", title="Színválasztó"):
        super().__init__(parent)
        self.title(title)
        self.geometry("320x280")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None
        self.updating = False

        if not initialcolor or not str(initialcolor).startswith('#') or len(initialcolor) != 7:
            initialcolor = "#ffffff"

        self.hex_var = tk.StringVar(value=initialcolor)

        def hex_to_rgb(hx):
            hx = hx.lstrip('#')
            try:
                return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))
            except:
                return 255, 255, 255

        r, g, b = hex_to_rgb(initialcolor)
        self.r_var = tk.StringVar(value=str(r))
        self.g_var = tk.StringVar(value=str(g))
        self.b_var = tk.StringVar(value=str(b))

        f = ttk.Frame(self, padding=15)
        f.pack(fill="both", expand=True)

        self.preview = tk.Label(f, bg=initialcolor, relief="sunken", height=2)
        self.preview.pack(fill="x", pady=(0, 15))

        grid_f = ttk.Frame(f)
        grid_f.pack(fill="x")

        ttk.Label(grid_f, text="HEX Kód:").grid(row=0, column=0, sticky="w", pady=5)
        self.hex_ent = ttk.Entry(grid_f, textvariable=self.hex_var, width=15)
        self.hex_ent.grid(row=0, column=1, sticky="w", pady=5)

        ttk.Label(grid_f, text="R (Piros 0-255):").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(grid_f, textvariable=self.r_var, width=15).grid(row=1, column=1, sticky="w", pady=5)

        ttk.Label(grid_f, text="G (Zöld 0-255):").grid(row=2, column=0, sticky="w", pady=5)
        ttk.Entry(grid_f, textvariable=self.g_var, width=15).grid(row=2, column=1, sticky="w", pady=5)

        ttk.Label(grid_f, text="B (Kék 0-255):").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(grid_f, textvariable=self.b_var, width=15).grid(row=3, column=1, sticky="w", pady=5)

        btn_f = ttk.Frame(f)
        btn_f.pack(fill="x", pady=(20, 0))
        ttk.Button(btn_f, text="Mentés", command=self.on_ok).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ttk.Button(btn_f, text="Mégse", command=self.destroy).pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.hex_var.trace_add("write", self.on_hex_change)
        self.r_var.trace_add("write", self.on_rgb_change)
        self.g_var.trace_add("write", self.on_rgb_change)
        self.b_var.trace_add("write", self.on_rgb_change)

    def on_hex_change(self, *args):
        if self.updating: return
        hx = self.hex_var.get().strip()
        if len(hx) == 7 and hx.startswith('#'):
            try:
                r, g, b = tuple(int(hx.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
                self.updating = True
                self.r_var.set(str(r))
                self.g_var.set(str(g))
                self.b_var.set(str(b))
                self.preview.config(bg=hx)
                self.updating = False
            except ValueError:
                pass

    def on_rgb_change(self, *args):
        if self.updating: return
        try:
            r = max(0, min(255, int(self.r_var.get().strip() or 0)))
            g = max(0, min(255, int(self.g_var.get().strip() or 0)))
            b = max(0, min(255, int(self.b_var.get().strip() or 0)))
            hx = f"#{r:02x}{g:02x}{b:02x}"
            self.updating = True
            self.hex_var.set(hx)
            self.preview.config(bg=hx)
            self.updating = False
        except ValueError:
            pass

    def on_ok(self):
        hx = self.hex_var.get().strip()
        if len(hx) == 7 and hx.startswith('#'):
            self.result = hx
        else:
            self.result = None
        self.destroy()


def ask_custom_color(parent, initialcolor, title="Színválasztó"):
    dlg = CustomColorPicker(parent, initialcolor, title)
    parent.wait_window(dlg)
    return dlg.result


class StyleManager:
    FILE_PATH = "document_styles.json"
    DEFAULT_STYLES = {
        "Normal": {"font_family": "Arial", "font_size": 12, "bold": False, "italic": False, "color": "#000000",
                   "bg_color": ""},
        "Címsor 1": {"font_family": "Arial", "font_size": 18, "bold": True, "italic": False, "color": "#000000",
                     "bg_color": "#78ff78"},
        "Címsor 2": {"font_family": "Arial", "font_size": 15, "bold": True, "italic": False, "color": "#333333",
                     "bg_color": "#96ff96"},
        "Címsor 3": {"font_family": "Arial", "font_size": 14, "bold": True, "italic": False, "color": "#434343",
                     "bg_color": "#b4ffb4"},
        "Dokumentum Cím": {"font_family": "Arial", "font_size": 20, "bold": True, "italic": False, "color": "#000000",
                           "bg_color": "#64ff64"},
        "Kód Blokk": {"font_family": "Courier New", "font_size": 10, "bold": False, "italic": False, "color": "#202020",
                      "bg_color": "#FDFDFD"},
        "Kiemelt": {"font_family": "Arial", "font_size": 12, "bold": True, "italic": False, "color": "#cc0000",
                    "bg_color": "#ffff99"}
    }

    @classmethod
    def load_styles(cls):
        if not os.path.exists(cls.FILE_PATH):
            cls.save_styles(cls.DEFAULT_STYLES)
            return cls.DEFAULT_STYLES.copy()
        try:
            with open(cls.FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return cls.DEFAULT_STYLES.copy()

    @classmethod
    def save_styles(cls, styles_dict):
        with open(cls.FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(styles_dict, f, indent=4)


class StyleAdminFrame(ttk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, text="Dokumentum Stílus Szerkesztő", padding=10, *args, **kwargs)
        self.styles = StyleManager.load_styles()
        self.current_selection = None
        self._build_ui()
        self._load_available_fonts()
        self._refresh_list()

    def _build_ui(self):
        list_frame = ttk.Frame(self)
        list_frame.pack(side="left", fill="y", padx=(0, 10))
        self.style_listbox = tk.Listbox(list_frame, width=25, exportselection=False)
        self.style_listbox.pack(side="top", fill="y", expand=True)
        self.style_listbox.bind("<<ListboxSelect>>", self._on_select)
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side="bottom", fill="x", pady=(5, 0))
        ttk.Button(btn_frame, text="Új Stílus", command=self._add_style).pack(side="left", expand=True, fill="x")
        ttk.Button(btn_frame, text="Törlés", command=self._delete_style).pack(side="left", expand=True, fill="x")
        self.edit_frame = ttk.Frame(self)
        self.edit_frame.pack(side="left", fill="both", expand=True)
        ttk.Label(self.edit_frame, text="Stílus Neve:").grid(row=0, column=0, sticky="w", pady=5)
        self.ent_name = ttk.Entry(self.edit_frame)
        self.ent_name.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        ttk.Label(self.edit_frame, text="Betűtípus:").grid(row=1, column=0, sticky="w", pady=5)
        self.ent_font = ttk.Combobox(self.edit_frame, state="readonly")
        self.ent_font.grid(row=1, column=1, sticky="ew", pady=5, padx=5)
        ttk.Button(self.edit_frame, text="TTF Import", command=self._import_ttf).grid(row=1, column=2, sticky="ew",
                                                                                      pady=5, padx=5)
        ttk.Label(self.edit_frame, text="Betűméret:").grid(row=2, column=0, sticky="w", pady=5)
        self.ent_size = ttk.Entry(self.edit_frame)
        self.ent_size.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        self.var_bold = tk.BooleanVar()
        self.chk_bold = ttk.Checkbutton(self.edit_frame, text="Félkövér (Bold)", variable=self.var_bold)
        self.chk_bold.grid(row=3, column=0, sticky="w", pady=5)
        self.var_italic = tk.BooleanVar()
        self.chk_italic = ttk.Checkbutton(self.edit_frame, text="Dőlt (Italic)", variable=self.var_italic)
        self.chk_italic.grid(row=3, column=1, sticky="w", pady=5)
        ttk.Label(self.edit_frame, text="Szöveg Színe:").grid(row=4, column=0, sticky="w", pady=5)
        self.btn_color = tk.Button(self.edit_frame, text="Választás", bg="#000000", fg="#ffffff",
                                   command=self._pick_color)
        self.btn_color.grid(row=4, column=1, sticky="ew", pady=5, padx=5)
        self.current_color = "#000000"
        ttk.Label(self.edit_frame, text="Háttérszín:").grid(row=5, column=0, sticky="w", pady=5)
        bg_frame = ttk.Frame(self.edit_frame)
        bg_frame.grid(row=5, column=1, columnspan=2, sticky="ew", pady=5, padx=5)
        self.btn_bg_color = tk.Button(bg_frame, text="Választás", bg="#ffffff", fg="#000000",
                                      command=self._pick_bg_color)
        self.btn_bg_color.pack(side="left", fill="x", expand=True)
        self.current_bg_color = ""
        ttk.Button(bg_frame, text="Törlés", command=self._clear_bg_color, width=8).pack(side="left", padx=(5, 0))
        ttk.Button(self.edit_frame, text="Mentés az Adatbázisba", command=self._save_all).grid(row=6, column=0,
                                                                                               columnspan=3, pady=15)
        self.edit_frame.columnconfigure(1, weight=1)
        self._clear_form()

    def _load_available_fonts(self):
        fonts = list(tkfont.families())
        if os.path.exists("assets"):
            for f in os.listdir("assets"):
                if f.lower().endswith(".ttf"): fonts.append(os.path.splitext(f)[0])
        self.ent_font['values'] = sorted(list(set(fonts)))

    def _import_ttf(self):
        parent_win = self.winfo_toplevel()
        filepath = filedialog.askopenfilename(title="Válassz TTF fájlt", filetypes=[("TrueType Font", "*.ttf")],
                                              parent=parent_win)
        if filepath:
            os.makedirs("assets", exist_ok=True)
            filename = os.path.basename(filepath)
            dest = os.path.join("assets", filename)
            try:
                shutil.copy2(filepath, dest)
                messagebox.showinfo("Siker",
                                    f"Betűtípus importálva: {filename}\n\nMegjegyzés: Az operációs rendszerre is telepíteni kell a vizuális Editorhoz!",
                                    parent=parent_win)
                self._load_available_fonts()
                font_name = os.path.splitext(filename)[0]
                if font_name in self.ent_font['values']: self.ent_font.set(font_name)
            except Exception as e:
                messagebox.showerror("Hiba", str(e), parent=parent_win)

    def _refresh_list(self):
        self.style_listbox.delete(0, tk.END)
        for style_name in self.styles.keys(): self.style_listbox.insert(tk.END, style_name)

    def _on_select(self, event):
        selection = self.style_listbox.curselection()
        if not selection: return
        style_name = self.style_listbox.get(selection[0])
        self.current_selection = style_name
        data = self.styles[style_name]
        self._clear_form()
        self.ent_name.insert(0, style_name)
        font_fam = data.get("font_family", "Arial")
        if font_fam in self.ent_font['values']:
            self.ent_font.set(font_fam)
        else:
            self.ent_font.set("Arial")
        self.ent_size.insert(0, str(data.get("font_size", 12)))
        self.var_bold.set(data.get("bold", False))
        self.var_italic.set(data.get("italic", False))
        self._set_color_btn(data.get("color", "#000000"))
        if data.get("bg_color"): self._set_bg_color_btn(data.get("bg_color"))

    def _clear_form(self):
        self.ent_name.delete(0, tk.END)
        self.ent_font.set("")
        self.ent_size.delete(0, tk.END)
        self.var_bold.set(False)
        self.var_italic.set(False)
        self._set_color_btn("#000000")
        self._clear_bg_color()

    def _set_color_btn(self, hex_color):
        self.current_color = hex_color
        fg_color = "#ffffff" if int(hex_color[1:3], 16) + int(hex_color[3:5], 16) + int(hex_color[5:7],
                                                                                        16) < 382 else "#000000"
        self.btn_color.config(bg=hex_color, fg=fg_color, text=hex_color)

    def _set_bg_color_btn(self, hex_color):
        self.current_bg_color = hex_color
        fg_color = "#ffffff" if int(hex_color[1:3], 16) + int(hex_color[3:5], 16) + int(hex_color[5:7],
                                                                                        16) < 382 else "#000000"
        self.btn_bg_color.config(bg=hex_color, fg=fg_color, text=hex_color)

    def _clear_bg_color(self):
        self.current_bg_color = ""
        self.btn_bg_color.config(bg="#ffffff", fg="#000000", text="Nincs (Átlátszó)")

    def _pick_color(self):
        color = ask_custom_color(self.winfo_toplevel(), initialcolor=self.current_color, title="Szöveg Színe")
        if color: self._set_color_btn(color)

    def _pick_bg_color(self):
        color = ask_custom_color(self.winfo_toplevel(), initialcolor=self.current_bg_color or "#ffffff",
                                 title="Háttérszín")
        if color: self._set_bg_color_btn(color)

    def _add_style(self):
        new_name = "Új Stílus"
        parent_win = self.winfo_toplevel()
        if new_name in self.styles:
            messagebox.showwarning("Figyelmeztetés", "Kérlek előbb nevezd át az 'Új Stílus' nevű elemet.",
                                   parent=parent_win)
            return
        self.styles[new_name] = StyleManager.DEFAULT_STYLES["Normal"].copy()
        self._refresh_list()
        self._clear_form()
        self.current_selection = None

    def _delete_style(self):
        parent_win = self.winfo_toplevel()
        if not self.current_selection: return
        if self.current_selection == "Normal":
            messagebox.showwarning("Tiltott", "A 'Normal' alapstílust nem lehet törölni.", parent=parent_win)
            return
        del self.styles[self.current_selection]
        self.current_selection = None
        self._clear_form()
        self._refresh_list()

    def _save_all(self):
        parent_win = self.winfo_toplevel()
        if not self.ent_name.get().strip(): return
        new_name = self.ent_name.get().strip()
        if self.current_selection and self.current_selection != new_name:
            if new_name in self.styles:
                messagebox.showwarning("Hiba", "Már létezik stílus ilyen névvel.", parent=parent_win)
                return
            del self.styles[self.current_selection]
        try:
            size = int(self.ent_size.get())
        except ValueError:
            messagebox.showerror("Hiba", "A betűméretnek számnak kell lennie.", parent=parent_win)
            return
        font_fam = self.ent_font.get().strip()
        if not font_fam: font_fam = "Arial"
        self.styles[new_name] = {
            "font_family": font_fam, "font_size": size, "bold": self.var_bold.get(),
            "italic": self.var_italic.get(), "color": self.current_color, "bg_color": self.current_bg_color
        }
        StyleManager.save_styles(self.styles)
        self.current_selection = new_name
        self._refresh_list()
        messagebox.showinfo("Siker", "A stílusok sikeresen elmentve.", parent=parent_win)


class EmbeddedTableWidget(tk.Frame):
    def __init__(self, parent, rows=3, cols=3, table_data=None):
        super().__init__(parent, bg="black", padx=1, pady=1)
        self.cells = {}
        if table_data:
            self.row_count = len(table_data)
            self.col_count = len(table_data[0]) if self.row_count > 0 else cols
        else:
            self.row_count = rows
            self.col_count = cols
        self._build_grid()
        if table_data: self.load_data(table_data)

    def _build_grid(self):
        for widget in self.winfo_children(): widget.destroy()
        self.cells.clear()
        for r in range(self.row_count):
            for c in range(self.col_count): self._create_cell(r, c)

    def _create_cell(self, r, c, text=""):
        cell_frame = tk.Frame(self, bg="white", padx=1, pady=1)
        cell_frame.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
        txt = tk.Text(cell_frame, width=15, height=2, wrap="word", font=("Arial", 10), relief="flat")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", text)
        txt.bind("<Button-3>", lambda e, row=r, col=c: self._show_context_menu(e, row, col))
        self.cells[(r, c)] = txt
        self.grid_rowconfigure(r, weight=1)
        self.grid_columnconfigure(c, weight=1)

    def _show_context_menu(self, event, row, col):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Sor beszúrása felé", command=lambda: self.insert_row(row))
        menu.add_command(label="Sor beszúrása alá", command=lambda: self.insert_row(row + 1))
        menu.add_separator()
        menu.add_command(label="Oszlop beszúrása balra", command=lambda: self.insert_col(col))
        menu.add_command(label="Oszlop beszúrása jobbra", command=lambda: self.insert_col(col + 1))
        menu.add_separator()
        menu.add_command(label="Sor törlése", command=lambda: self.delete_row(row))
        menu.add_command(label="Oszlop törlése", command=lambda: self.delete_col(col))
        menu.add_separator()
        menu.add_command(label="Cella Szélesítése", command=lambda: self.adjust_width(col, 5))
        menu.add_command(label="Cella Keskenyítése", command=lambda: self.adjust_width(col, -5))
        menu.tk_popup(event.x_root, event.y_root)

    def insert_row(self, index):
        data_matrix = self.get_data()['data']
        data_matrix.insert(index, ["" for _ in range(self.col_count)])
        self.row_count += 1
        self._build_grid()
        self.load_data(data_matrix)

    def delete_row(self, index):
        if self.row_count <= 1: return
        data_matrix = self.get_data()['data']
        data_matrix.pop(index)
        self.row_count -= 1
        self._build_grid()
        self.load_data(data_matrix)

    def insert_col(self, index):
        data_matrix = self.get_data()['data']
        for row in data_matrix: row.insert(index, "")
        self.col_count += 1
        self._build_grid()
        self.load_data(data_matrix)

    def delete_col(self, index):
        if self.col_count <= 1: return
        data_matrix = self.get_data()['data']
        for row in data_matrix: row.pop(index)
        self.col_count -= 1
        self._build_grid()
        self.load_data(data_matrix)

    def adjust_width(self, col, delta):
        for r in range(self.row_count):
            txt = self.cells.get((r, col))
            if txt: txt.config(width=max(5, txt.cget("width") + delta))

    def get_data(self):
        data = []
        for r in range(self.row_count):
            row_data = []
            for c in range(self.col_count):
                txt = self.cells.get((r, c))
                row_data.append(txt.get("1.0", "end-1c") if txt else "")
            data.append(row_data)
        return dict(type="embedded_table", rows=self.row_count, cols=self.col_count, data=data)

    def load_data(self, data_matrix):
        for r in range(min(self.row_count, len(data_matrix))):
            for c in range(min(self.col_count, len(data_matrix[r]))):
                txt = self.cells.get((r, c))
                if txt:
                    txt.delete("1.0", tk.END)
                    txt.insert("1.0", data_matrix[r][c])


class NativeRichTextEditor(ttk.Frame):
    def __init__(self, parent, initial_content="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.styles = StyleManager.load_styles()

        # Lists to keep images loaded in memory and referenced by Tkinter
        self.photo_references = []
        self.embedded_images = {}

        self._build_ui()
        self._configure_tags()
        if initial_content:
            self.set_content(initial_content)

    def _build_ui(self):
        self.toolbar = ttk.Frame(self)
        self.toolbar.pack(fill="x", pady=2)
        ttk.Label(self.toolbar, text="Stílus:").pack(side="left", padx=(5, 2))
        self.style_var = tk.StringVar()
        self.cb_styles = ttk.Combobox(self.toolbar, textvariable=self.style_var, state="readonly",
                                      values=list(self.styles.keys()), width=15)
        self.cb_styles.pack(side="left", padx=2)
        self.cb_styles.bind("<<ComboboxSelected>>", self._apply_style)
        if "Normal" in self.styles: self.cb_styles.set("Normal")

        align_f = ttk.Frame(self.toolbar)
        align_f.pack(side="left", padx=10)
        ttk.Button(align_f, text="Balra", width=6, command=lambda: self._set_align("align_left")).pack(side="left",
                                                                                                       padx=1)
        ttk.Button(align_f, text="Közép", width=6, command=lambda: self._set_align("align_center")).pack(side="left",
                                                                                                         padx=1)
        ttk.Button(align_f, text="Jobbra", width=6, command=lambda: self._set_align("align_right")).pack(side="left",
                                                                                                         padx=1)
        ttk.Button(align_f, text="• Lista", command=self._toggle_list).pack(side="left", padx=(10, 2))
        ttk.Button(align_f, text="Oldaltörés", command=self._insert_page_break).pack(side="left", padx=2)
        ttk.Button(align_f, text="Táblázat (+)", command=self._insert_table).pack(side="left", padx=2)

        self.editor_container = tk.Frame(self, bg="#d0d0d0")
        self.editor_container.pack(fill="both", expand=True)
        self.paper_shadow = tk.Frame(self.editor_container, bg="#999999", padx=1, pady=1)
        self.paper_shadow.pack(pady=20, fill="y", expand=False)
        self.text_editor = tk.Text(
            self.paper_shadow, wrap="word", undo=True,
            bg="white", fg="black", width=85,
            padx=45, pady=45, relief="flat"
        )
        self.text_editor.pack(fill="both", expand=True)
        self.text_editor.bind("<ButtonRelease-1>", self._update_toolbar)
        self.text_editor.bind("<KeyRelease>", self._update_toolbar)
        self.text_editor.bind("<Return>", self._on_enter)

    def _configure_tags(self):
        for name, cfg in self.styles.items():
            safe_name = name.replace(" ", "_")
            font_weight = "bold" if cfg.get("bold") else "normal"
            font_slant = "italic" if cfg.get("italic") else "roman"
            tag_cfg = {
                "font": (cfg.get("font_family", "Arial"), cfg.get("font_size", 12), font_weight, font_slant),
                "foreground": cfg.get("color", "#000000")
            }
            if cfg.get("bg_color"): tag_cfg["background"] = cfg.get("bg_color")
            self.text_editor.tag_configure(safe_name, **tag_cfg)

        self.text_editor.tag_configure("align_left", justify="left")
        self.text_editor.tag_configure("align_center", justify="center")
        self.text_editor.tag_configure("align_right", justify="right")
        self.text_editor.tag_configure("list_item", lmargin1=20, lmargin2=40)
        self.text_editor.tag_configure("page_break", background="#e0e0e0", foreground="#555555", justify="center",
                                       font=("Arial", 10, "bold"))

    def _apply_style(self, event=None):
        selected = self.style_var.get()
        if not selected: return
        start, end = "insert linestart", "insert lineend"
        for s in self.styles.keys(): self.text_editor.tag_remove(s.replace(" ", "_"), start, end)
        safe_name = selected.replace(" ", "_")
        self.text_editor.tag_add(safe_name, start, end)
        self.text_editor.focus()

    def _set_align(self, align_tag):
        start, end = "insert linestart", "insert lineend"
        for t in ["align_left", "align_center", "align_right"]:
            self.text_editor.tag_remove(t, start, end)
        self.text_editor.tag_add(align_tag, start, end)

    def _toggle_list(self):
        start, end = "insert linestart", "insert lineend"
        text = self.text_editor.get(start, end)
        if "list_item" in self.text_editor.tag_names(start):
            self.text_editor.tag_remove("list_item", start, end)
            if text.startswith("• "): self.text_editor.delete(start, f"{start}+2c")
        else:
            self.text_editor.tag_add("list_item", start, end)
            if not text.startswith("• "): self.text_editor.insert(start, "• ")

    def _insert_page_break(self):
        self.text_editor.insert("insert", "\n--- OLDALTÖRÉS ---\n", ("page_break", "align_center"))

    def _insert_table(self):
        self.text_editor.insert("insert", "\n")
        table_widget = EmbeddedTableWidget(self.text_editor, rows=3, cols=3)
        self.text_editor.window_create("insert", window=table_widget)
        self.text_editor.insert("insert", "\n", ("Normal", "align_left"))

    # --- NEW: Image Insertion Engine ---
    def insert_image(self, filepath):
        """Loads and visually renders an image directly onto the Tkinter canvas."""
        if Image is None:
            messagebox.showerror("Hiba",
                                 "A PIL (Pillow) könyvtár nincs telepítve!\nKérlek futtasd a parancssorban: pip install pillow")
            return

        try:
            img = Image.open(filepath)

            # Constrain image size so it fits inside the A4 editor width
            if img.width > 550:
                ratio = 550 / img.width
                img = img.resize((550, int(img.height * ratio)), Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(img)
            self.photo_references.append(photo)

            # Unique identifier for the JSON dump retrieval
            img_name = f"img_obj_{len(self.photo_references)}"
            self.embedded_images[img_name] = filepath

            self.text_editor.insert("insert", "\n")
            self.text_editor.image_create("insert", image=photo, name=img_name)
            self.text_editor.insert("insert", "\n", ("Normal", "align_center"))

        except Exception as e:
            messagebox.showerror("Hiba", f"Nem sikerült a képet beilleszteni:\n{e}")

    # -----------------------------------

    def _update_toolbar(self, event=None):
        tags = self.text_editor.tag_names("insert linestart")
        safe_to_real = {k.replace(" ", "_"): k for k in self.styles.keys()}
        for t in tags:
            if t in safe_to_real:
                self.cb_styles.set(safe_to_real[t])
                return
        self.cb_styles.set("Normal")

    def _on_enter(self, event):
        current_style = self.style_var.get()
        if "Címsor" in current_style or "Cím" in current_style:
            self.text_editor.insert("insert", "\n")
            self.cb_styles.set("Normal")
            self._apply_style()
            return "break"

    def get_content(self):
        elements = []
        dump_data = self.text_editor.dump("1.0", "end", text=True, window=True, image=True)  # Fetch images too
        safe_to_real = {k.replace(" ", "_"): k for k in self.styles.keys()}

        current_paragraph = []
        for key, value, index in dump_data:
            if key == "window" and value:
                try:
                    widget = self.nametowidget(value)
                    if isinstance(widget, EmbeddedTableWidget):
                        elements.append(widget.get_data())
                except KeyError:
                    pass

            elif key == "image":
                # Find the tracked image path based on Tkinter's internal photo name
                if value in self.embedded_images:
                    elements.append({
                        "type": "image",
                        "path": self.embedded_images[value]
                    })

            elif key == "text":
                if value == "\n":
                    line_start_index = f"{index} linestart"
                    tags = self.text_editor.tag_names(line_start_index)
                    full_text = "".join(current_paragraph)

                    if "--- OLDALTÖRÉS" in full_text:
                        elements.append({"type": "page_break"})
                    else:
                        style, align, is_list = "Normal", "left", False
                        for t in tags:
                            if t in safe_to_real: style = safe_to_real[t]
                            if t == "align_center": align = "center"
                            if t == "align_right": align = "right"
                            if t == "list_item": is_list = True

                        clean_text = full_text[2:] if is_list and full_text.startswith("• ") else full_text
                        elements.append(
                            {"type": "paragraph", "style": style, "align": align, "list": is_list, "text": clean_text})
                    current_paragraph = []
                else:
                    current_paragraph.append(value)

        if elements and elements[-1].get("type") == "paragraph" and not elements[-1].get("text"):
            elements.pop()

        return json.dumps(elements)

    def set_content(self, content):
        self.text_editor.delete("1.0", tk.END)
        self.photo_references.clear()
        self.embedded_images.clear()
        if not content: return

        try:
            if isinstance(content, str):
                if not content.strip().startswith("["):
                    self.text_editor.insert("end", content, ("Normal", "align_left"))
                    return
                data = json.loads(content)
            elif isinstance(content, list):
                data = content
            else:
                self.text_editor.insert("end", str(content), ("Normal", "align_left"))
                return

            for idx, block in enumerate(data):
                if idx > 0: self.text_editor.insert("end", "\n")
                b_type = block.get("type", "paragraph")

                if b_type == "page_break":
                    self.text_editor.insert("end", "--- OLDALTÖRÉS ---", ("page_break", "align_center"))

                elif b_type == "embedded_table":
                    r = block.get("rows", 3)
                    c = block.get("cols", 3)
                    t_data = block.get("data", [])
                    table_widget = EmbeddedTableWidget(self.text_editor, rows=r, cols=c, table_data=t_data)
                    self.text_editor.window_create("end", window=table_widget)

                elif b_type == "image":
                    filepath = block.get("path", "")
                    if os.path.exists(filepath) and Image is not None:
                        try:
                            img = Image.open(filepath)
                            if img.width > 550:
                                ratio = 550 / img.width
                                img = img.resize((550, int(img.height * ratio)), Image.Resampling.LANCZOS)

                            photo = ImageTk.PhotoImage(img)
                            self.photo_references.append(photo)

                            img_name = f"img_obj_{len(self.photo_references)}"
                            self.embedded_images[img_name] = filepath
                            self.text_editor.image_create("end", image=photo, name=img_name)
                        except Exception:
                            self.text_editor.insert("end", f"[KÉP HIBA: {filepath}]", ("Normal", "align_center"))
                    else:
                        self.text_editor.insert("end", f"[HIÁNYZÓ KÉP: {filepath}]", ("Normal", "align_center"))

                elif b_type == "paragraph":
                    style = block.get("style", "Normal")
                    align = block.get("align", "left")
                    is_list = block.get("list", False)
                    text = block.get("text", "")

                    if is_list: text = "• " + text
                    safe_style = style.replace(" ", "_")
                    tags = [safe_style, f"align_{align}"]
                    if is_list: tags.append("list_item")

                    self.text_editor.insert("end", text, tuple(tags))

        except Exception as e:
            self.text_editor.insert("end", f"[RENDSZERHIBA A BETÖLTÉSKOR: {e}]\n\n{content}")