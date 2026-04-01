import tkinter as tk
from tkinter import ttk
import markdown

try:
    from tkhtmlview import HTMLLabel
except ImportError:
    HTMLLabel = None

class AutocompleteCombobox(ttk.Combobox):
    """
    Okos Combobox, amely gépelés közben szűri a listát a beírt karakterek alapján.
    """
    def set_completion_list(self, completion_list):
        """Beállítja a forráslistát az autokompletáláshoz."""
        self._hits = sorted(list(set(completion_list)))
        self._hit_index = 0
        self.position = 0
        self.bind('<KeyRelease>', self.handle_keyrelease)
        self['values'] = self._hits

    def handle_keyrelease(self, event):
        """Szűri a listát gépelés közben."""
        if event.keysym in ('BackSpace', 'Left', 'Right', 'Up', 'Down', 'Return', 'Tab'):
            if event.keysym == 'BackSpace':
                pass
            else:
                return

        value = self.get()
        if value == '':
            self['values'] = self._hits
        else:
            data = [item for item in self._hits if value.lower() in item.lower()]
            self['values'] = data

        if self['values']:
            self.event_generate('<Down>')


class UIFactory:
    """
    Központosított felületépítő osztály, amivel egyetlen sorral létrehozhatunk
    és grid-be helyezhetünk form elemeket címkével együtt.
    """
    @staticmethod
    def create_label_entry(parent, label, row, column=0, width=30, default=""):
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=5, pady=5)
        ent = ttk.Entry(parent, width=width)
        if default: 
            ent.insert(0, default)
        ent.grid(row=row, column=column + 1, sticky="w", padx=5, pady=5)
        return ent

    @staticmethod
    def create_label_combo(parent, label, values, row, column=0, width=28, readonly=True):
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", padx=5, pady=5)
        cb = ttk.Combobox(parent, values=values, width=width, state="readonly" if readonly else "normal")
        cb.grid(row=row, column=column + 1, sticky="w", padx=5, pady=5)
        if values: 
            cb.current(0)
        return cb

    @staticmethod
    def create_scrolled_text(parent, label, row, column=0, width=40, height=4):
        """Létrehoz egy többsoros szövegmezőt címkével."""
        ttk.Label(parent, text=label).grid(row=row, column=column, sticky="nw", padx=5, pady=5)
        txt = tk.Text(parent, width=width, height=height, font=("Courier", 10))
        txt.grid(row=row, column=column + 1, sticky="w", padx=5, pady=5)
        return txt


def safe_toplevel(parent, title, geometry="600x400"):
    """
    Létrehoz egy felugró ablakot (Toplevel), amely garantáltan a szülő (parent)
    ablak közepén jelenik meg, és kizárólagos fókuszt kér magának,
    kiküszöbölve az "ablak mögé nyíló" hibákat.
    """
    top = tk.Toplevel(parent)
    top.title(title)
    
    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_width = parent.winfo_width()
    parent_height = parent.winfo_height()

    try:
        w, h = map(int, geometry.split('x'))
        x = parent_x + (parent_width // 2) - (w // 2)
        y = parent_y + (parent_height // 2) - (h // 2)
        top.geometry(f"{w}x{h}+{x}+{y}")
    except:
        top.geometry(geometry)

    top.transient(parent)
    top.update_idletasks()
    try:
        top.grab_set()
    except tk.TclError:
        pass
        
    top.focus_force()
    return top


# add this to the END of core/ui_components.py

class EditableTreeview(ttk.Treeview):
    """
    Kiterjesztett Treeview, amely lehetővé teszi a cellák duplakattintással
    történő helyben szerkesztését (In-place editing).
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.bind("<Double-1>", self.on_double_click)
        self._edit_entry = None

    def on_double_click(self, event):
        # Ha már van nyitott szerkesztő, zárjuk be
        if self._edit_entry:
            self._edit_entry.destroy()

        region = self.identify_region(event.x, event.y)
        if region != "cell":
            return

        column = self.identify_column(event.x)
        col_idx = int(column[1:]) - 1  # #1 -> 0, #2 -> 1
        item = self.identify_row(event.y)

        # Oszlop azonosító lekérése (hogy tudjuk, nem egy read-only oszlopot szerkeszt-e)
        col_id = self["columns"][col_idx]
        if col_id == "Hibák":  # Ezt az oszlopot ne lehessen szerkeszteni
            return

        x, y, width, height = self.bbox(item, column)
        current_value = self.item(item, 'values')[col_idx]

        self._edit_entry = ttk.Entry(self)
        self._edit_entry.place(x=x, y=y, width=width, height=height)
        self._edit_entry.insert(0, current_value)
        self._edit_entry.focus_set()

        def save_edit(e):
            new_val = self._edit_entry.get()
            values = list(self.item(item, 'values'))
            values[col_idx] = new_val
            self.item(item, values=values)
            self._edit_entry.destroy()
            self._edit_entry = None
            # Egyedi event generálása, ha a szülő ablak újra akarja validálni
            self.event_generate("<<TreeviewEditEnd>>")

        self._edit_entry.bind("<Return>", save_edit)
        self._edit_entry.bind("<FocusOut>", lambda e: self._edit_entry.destroy() if self._edit_entry else None)

class LiveMarkdownEditor(ttk.Frame):
    """
    An embedded split-pane document editor providing real-time visual 
    feedback for headers, tables, and lists.
    Requires: pip install markdown tkhtmlview
    """
    def __init__(self, parent, initial_text="", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        if HTMLLabel is None:
            raise ImportError("Please install the required library: pip install tkhtmlview")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # Left Pane: The raw text editor
        self.editor_frame = ttk.LabelFrame(self, text="Editor")
        self.editor_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.text_input = tk.Text(self.editor_frame, wrap="word", undo=True)
        self.text_input.pack(fill="both", expand=True, padx=5, pady=5)
        self.text_input.insert("1.0", initial_text)
        
        # Right Pane: The live visual preview
        self.preview_frame = ttk.LabelFrame(self, text="Live Preview")
        self.preview_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self.html_preview = HTMLLabel(self.preview_frame, html="")
        self.html_preview.pack(fill="both", expand=True, padx=5, pady=5)

        # Bind the key release event to update the preview in real-time
        self.text_input.bind("<KeyRelease>", self._update_preview)
        
        # Initial render
        self._update_preview()

    def _update_preview(self, event=None):
        """Fetches text, converts markdown (with tables) to HTML, and updates the preview."""
        raw_text = self.text_input.get("1.0", tk.END).strip()
        
        # Convert markdown to HTML. Using 'tables' extension for table support.
        html_content = markdown.markdown(raw_text, extensions=['tables', 'fenced_code'])
        
        # Add basic CSS styling for the tables and headers so they look clean
        styled_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 10px;">
            <style>
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; }}
                th {{ background-color: #f2f2f2; text-align: left; }}
                h1, h2, h3 {{ color: #333; }}
            </style>
            {html_content}
        </div>
        """
        self.html_preview.set_html(styled_html)

    def get_content(self):
        """Returns the raw document content for saving to the database."""
        return self.text_input.get("1.0", tk.END).strip()

    def set_content(self, text):
        """Sets the editor content and refreshes the preview."""
        self.text_input.delete("1.0", tk.END)
        self.text_input.insert("1.0", text)
        self._update_preview()
