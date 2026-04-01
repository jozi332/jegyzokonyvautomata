import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os

from core.ui_components import UIFactory, safe_toplevel, AutocompleteCombobox
from core.style_manager import StyleAdminFrame


class AdminTab(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.db = self.app.db
        self.fm = self.app.fm
        self._build_ui()

    def _build_ui(self):
        f = ttk.LabelFrame(self, text="Rendszer", padding=30)
        f.pack(fill="both", expand=True, padx=30, pady=30)

        ttk.Button(f, text="Fájlok rendezése (INBOX -> PROJECTS)",
                   command=lambda: messagebox.showinfo("Info", self.fm.organize_inbox(), parent=self)).pack(pady=10,
                                                                                                            fill='x')

        ttk.Button(f, text="BIZTONSÁGI MENTÉS (Csak másolás)", command=self.action_backup).pack(pady=10, fill='x')
        ttk.Button(f, text="ARCHIVÁLÁS ÉS TÖRLÉS", command=self.action_archive).pack(pady=10, fill='x')

        ttk.Button(f, text="Cég és dolgozói adatok", command=self.open_company_settings).pack(pady=10, fill='x')
        ttk.Button(f, text="Iroda utazás", command=self.open_travel_settings).pack(pady=10, fill='x')
        ttk.Button(f, text="Dokumentum Stílusok", command=self.open_style_settings).pack(pady=10, fill='x')

        csv_frame = ttk.LabelFrame(f, text="Adatbázis CSV Import / Export", padding=15)
        csv_frame.pack(fill="x", pady=20)

        row1 = ttk.Frame(csv_frame)
        row1.pack(fill="x", pady=5)
        ttk.Label(row1, text="Céltábla / Sablon: ").pack(side="left")

        tables = self.db.get_all_table_names()
        self.combo_tables = AutocompleteCombobox(row1, values=tables, state="readonly")
        if tables: self.combo_tables.current(0)
        self.combo_tables.pack(side="left", padx=10, fill="x", expand=True)

        row2 = ttk.Frame(csv_frame)
        row2.pack(fill="x", pady=5)
        ttk.Button(row2, text="1. Sablon letöltése", command=self.action_generate_template).pack(side="left", padx=5,
                                                                                                 expand=True, fill="x")
        ttk.Button(row2, text="2. Tábla exportálása (CSV)", command=self.action_export_csv).pack(side="left", padx=5,
                                                                                                 expand=True, fill="x")

        row3 = ttk.Frame(csv_frame)
        row3.pack(fill="x", pady=10)
        ttk.Button(row3, text="3. Adatok importálása (Auto-felismerés)", command=self.action_import_csv).pack(fill="x",
                                                                                                              padx=5)

    def action_archive(self):
        if messagebox.askyesno("Archiválás",
                               "Figyelem!\nEz archiválja és TÖRLI az összes aktív projektet és bejegyzést az adatbázisból!\nBiztosan folytatod?",
                               parent=self):
            s, m = self.db.archive_database()
            if s:
                messagebox.showinfo("Eredmény", m, parent=self)
                self.app.notify_project_updated()
            else:
                messagebox.showerror("Hiba", m, parent=self)

    def action_backup(self):
        s, m = self.db.backup_database()
        if s:
            messagebox.showinfo("Siker", m, parent=self)
        else:
            messagebox.showerror("Hiba", m, parent=self)

    def open_company_settings(self):
        """Expanded settings to cover multiple phones and EUR bank account."""
        top = safe_toplevel(self, "Cég és dolgozói adatok", "550x550")

        n = UIFactory.create_label_entry(top, "Név (Cég):", 0,
                                         default=self.db.get_setting('company_name') or "Minta Kft.")
        a = UIFactory.create_label_entry(top, "Cím:", 1, default=self.db.get_setting(
            'company_address') or "1234 Budapest, Minta utca 1.")
        t = UIFactory.create_label_entry(top, "Adószám:", 2,
                                         default=self.db.get_setting('company_tax') or "12345678-1-12")
        e = UIFactory.create_label_entry(top, "Email:", 3,
                                         default=self.db.get_setting('company_email') or "info@minta.hu")

        p1 = UIFactory.create_label_entry(top, "Telefon (1):", 4,
                                          default=self.db.get_setting('company_phone') or "+36 30 123 4567")
        p2 = UIFactory.create_label_entry(top, "Telefon (2 - Opcionális):", 5,
                                          default=self.db.get_setting('company_phone2') or "")
        p3 = UIFactory.create_label_entry(top, "Telefon (3 - Opcionális):", 6,
                                          default=self.db.get_setting('company_phone3') or "")

        b_huf = UIFactory.create_label_entry(top, "Bankszámla (HUF):", 7, default=self.db.get_setting(
            'company_bank') or "00000000-00000000-00000000")
        b_eur = UIFactory.create_label_entry(top, "Bankszámla (EUR - Opcionális):", 8,
                                             default=self.db.get_setting('company_bank_eur') or "")

        r = UIFactory.create_label_entry(top, "Nyilvántartási szám:", 9,
                                         default=self.db.get_setting('company_reg') or "00000000")
        w = UIFactory.create_label_entry(top, "Dolgozó / Mérnök neve:", 10,
                                         default=self.db.get_setting('worker_name') or "Minta Dolgozó")

        def save():
            self.db.update_setting('company_name', n.get())
            self.db.update_setting('company_address', a.get())
            self.db.update_setting('company_tax', t.get())
            self.db.update_setting('company_email', e.get())
            self.db.update_setting('company_phone', p1.get())
            self.db.update_setting('company_phone2', p2.get())
            self.db.update_setting('company_phone3', p3.get())
            self.db.update_setting('company_bank', b_huf.get())
            self.db.update_setting('company_bank_eur', b_eur.get())
            self.db.update_setting('company_reg', r.get())
            self.db.update_setting('worker_name', w.get())

            # Pass all 11 parameters to the PDF engine dynamically
            self.app.rg.pdf_gen.set_company_data(
                n.get(), a.get(), t.get(), e.get(),
                p1.get(), p2.get(), p3.get(),
                b_huf.get(), b_eur.get(),
                r.get(), w.get()
            )
            top.destroy()
            messagebox.showinfo("Siker", "Cég és dolgozói adatok frissítve!", parent=self)

        ttk.Button(top, text="Mentés", command=save).grid(row=11, column=1, pady=20)

    def open_travel_settings(self):
        top = safe_toplevel(self, "Utazás", "450x450")
        s = UIFactory.create_label_entry(top, "Indulás:", 0, default=self.db.get_setting('office_start'))
        e = UIFactory.create_label_entry(top, "Érkezés:", 1, default=self.db.get_setting('office_end'))
        d = UIFactory.create_label_entry(top, "Táv:", 2, default=self.db.get_setting('office_dist'))
        r = UIFactory.create_label_entry(top, "Díj:", 3, default=self.db.get_setting('office_rate'))
        t = UIFactory.create_label_entry(top, "Idő:", 4, default=self.db.get_setting('office_time'))
        c = UIFactory.create_label_entry(top, "Fix Ft:", 5, default=self.db.get_setting('office_cost'))

        def save():
            self.db.update_setting('office_start', s.get())
            self.db.update_setting('office_end', e.get())
            self.db.update_setting('office_dist', d.get())
            self.db.update_setting('office_rate', r.get())
            self.db.update_setting('office_time', t.get())
            self.db.update_setting('office_cost', c.get())
            top.destroy()
            messagebox.showinfo("Siker", "Utazási adatok frissítve!", parent=self)

        ttk.Button(top, text="Mentés", command=save).grid(row=6, column=1, pady=20)

    def open_style_settings(self):
        top = safe_toplevel(self, "Dokumentum Stílusok Szerkesztése", "650x450")
        style_editor = StyleAdminFrame(top)
        style_editor.pack(fill="both", expand=True, padx=10, pady=10)

    # --- v8.1 CSV IMPORT / EXPORT LOGIKA ---
    def action_generate_template(self):
        table_name = self.combo_tables.get()
        if not table_name: return
        schema = self.db.get_table_schema(table_name)
        filepath = filedialog.asksaveasfilename(parent=self, initialfile=f"{table_name}_template.csv",
                                                title="Sablon mentése", defaultextension=".csv",
                                                filetypes=[("CSV fájlok", "*.csv")])
        if not filepath: return
        try:
            with open(filepath, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(schema.keys())
            messagebox.showinfo("Siker", f"A sablon sikeresen létrehozva:\n{filepath}", parent=self)
        except Exception as e:
            messagebox.showerror("Hiba", f"Nem sikerült menteni: {e}", parent=self)

    def action_export_csv(self):
        table_name = self.combo_tables.get()
        if not table_name: return
        filepath = filedialog.asksaveasfilename(parent=self, initialfile=f"{table_name}_export.csv",
                                                title="Tábla exportálása", defaultextension=".csv",
                                                filetypes=[("CSV fájlok", "*.csv")])
        if not filepath: return
        try:
            self.db.c.execute(f"SELECT * FROM {table_name}")
            rows = self.db.c.fetchall()
            col_names = [description[0] for description in self.db.c.description]
            with open(filepath, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(col_names)
                writer.writerows(rows)
            messagebox.showinfo("Siker", f"A tábla adatai sikeresen exportálva:\n{filepath}", parent=self)
        except Exception as e:
            messagebox.showerror("Hiba", f"Nem sikerült exportálni: {e}", parent=self)

    def action_import_csv(self):
        filepath = filedialog.askopenfilename(parent=self, title="Adatok importálása (Auto-felismerés)",
                                              filetypes=[("CSV fájlok", "*.csv")])
        if not filepath: return
        try:
            with open(filepath, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                data_rows = list(reader)
            if not data_rows:
                messagebox.showwarning("Üres", "A kiválasztott fájl nem tartalmaz adatot.", parent=self)
                return
            csv_headers = set(data_rows[0].keys())
            tables = self.db.get_all_table_names()
            best_table = None
            for t in tables:
                schema = self.db.get_table_schema(t)
                if set(schema.keys()) == csv_headers:
                    best_table = t
                    break
            if not best_table:
                for t in tables:
                    schema = self.db.get_table_schema(t)
                    if csv_headers.issubset(set(schema.keys())):
                        best_table = t
                        break
            if best_table:
                self.combo_tables.set(best_table)
                table_name = best_table
                messagebox.showinfo("Auto-felismerés", f"A rendszer automatikusan felismerte a táblát:\n{best_table}",
                                    parent=self)
            else:
                table_name = self.combo_tables.get()
                messagebox.showwarning("Figyelem",
                                       f"Nem sikerült azonosítani a táblát a fejlécek alapján.\nA kiválasztott '{table_name}' tábla sémája lesz alkalmazva.",
                                       parent=self)
            if not table_name: return
            self.open_import_validator(table_name, data_rows)
        except Exception as e:
            messagebox.showerror("Hiba", f"A fájl olvasása sikertelen:\n{e}", parent=self)

    def open_import_validator(self, table_name, data_rows):
        top = safe_toplevel(self, f"Adat Ellenőrzés - {table_name} ({len(data_rows)} sor)", "1100x700")
        master_frame = ttk.Frame(top)
        master_frame.pack(fill="x", padx=20, pady=5)
        ttk.Label(master_frame, text="Alapértelmezett importálási mód:").pack(side="left")
        saved_mode = self.db.get_setting('import_mode')
        default_mode = saved_mode if saved_mode else "Új bejegyzés (Auto-ID)"
        master_mode_var = tk.StringVar(value=default_mode)
        master_cb = ttk.Combobox(master_frame, textvariable=master_mode_var,
                                 values=["Új bejegyzés (Auto-ID)", "Felülírás (Abszolút pozíció)"], state="readonly",
                                 width=30)
        master_cb.pack(side="left", padx=10)

        def apply_master_mode():
            mode = master_mode_var.get()
            self.db.update_setting('import_mode', mode)
            for r in data_rows: r['_import_mode'] = mode
            load_and_validate()

        ttk.Button(master_frame, text="Alkalmazás összes sorra", command=apply_master_mode).pack(side="left")
        lbl = ttk.Label(top,
                        text="Dupla kattintással szerkesztheted a cellákat! (FK és Művelet oszlopoknál legördülő menü jelenik meg)\nMentés csak ha 0 hiba van.",
                        font=("Helvetica", 10, "bold"))
        lbl.pack(pady=5)
        original_columns = list(data_rows[0].keys())
        if '_import_mode' in original_columns: original_columns.remove('_import_mode')
        display_columns = ["Művelet"] + original_columns + ["Hibák"]
        tree_frame = ttk.Frame(top)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=10)
        scrollbar_y = ttk.Scrollbar(tree_frame)
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal")
        scrollbar_x.pack(side="bottom", fill="x")
        tree = ttk.Treeview(tree_frame, columns=display_columns, show='headings', yscrollcommand=scrollbar_y.set,
                            xscrollcommand=scrollbar_x.set)
        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)
        for col in display_columns:
            tree.heading(col, text=col)
            width = 150 if col == "Művelet" else (250 if col == "Hibák" else 120)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        tree.tag_configure('error', background='#ffcccc')

        def load_and_validate():
            for item in tree.get_children(): tree.delete(item)
            error_count = 0
            for row in data_rows:
                if '_import_mode' not in row: row['_import_mode'] = master_mode_var.get()
                is_valid, errors = self.db.validate_import_row(table_name, row)
                row_values = [row.get('_import_mode')] + [row.get(c, "") for c in original_columns] + [errors]
                tag = 'error' if not is_valid else ''
                if not is_valid: error_count += 1
                tree.insert('', tk.END, values=row_values, tags=(tag,))
            btn_save.config(state="normal" if error_count == 0 else "disabled")
            lbl.config(text=f"Talált hibák: {error_count} (Dupla kattintással javítsd a cellát, majd nyomj Entert!)")

        tree.active_editor = None
        tree.active_editor_save = None

        def on_tree_click(event):
            if tree.active_editor and tree.active_editor.winfo_exists():
                x, y = event.x, event.y
                ex, ey = tree.active_editor.winfo_x(), tree.active_editor.winfo_y()
                ew, eh = tree.active_editor.winfo_width(), tree.active_editor.winfo_height()
                if ex <= x <= ex + ew and ey <= y <= ey + eh: return
                if tree.active_editor_save: tree.active_editor_save()

        tree.bind("<Button-1>", on_tree_click)

        def on_double_click(event):
            if tree.active_editor and tree.active_editor.winfo_exists():
                if tree.active_editor_save: tree.active_editor_save()
            region = tree.identify("region", event.x, event.y)
            if region != "cell": return
            col_id = tree.identify_column(event.x)
            item_id = tree.identify_row(event.y)
            col_idx = int(col_id.replace('#', '')) - 1
            col_name = display_columns[col_idx]
            if col_name == "Hibák": return
            x, y, w, h = tree.bbox(item_id, col_id)
            current_val = tree.item(item_id, 'values')[col_idx]
            fk_options = []
            if col_name == "Művelet":
                fk_options = ["Új bejegyzés (Auto-ID)", "Felülírás (Abszolút pozíció)"]
            elif col_name in ['client_id', 'end_client_id']:
                self.db.c.execute("SELECT id, name FROM clients")
                fk_options = [f"{r[0]} - {r[1]}" for r in self.db.c.fetchall()]
            elif col_name == 'contract_code':
                self.db.c.execute("SELECT contract_code FROM contracts")
                fk_options = [r[0] for r in self.db.c.fetchall()]
            elif col_name == 'project_code':
                self.db.c.execute("SELECT project_code FROM projects")
                fk_options = [r[0] for r in self.db.c.fetchall()]
            elif col_name == 'log_id':
                self.db.c.execute("SELECT log_id FROM daily_logs")
                fk_options = [str(r[0]) for r in self.db.c.fetchall()]
            if fk_options:
                editor = ttk.Combobox(tree, values=fk_options, state="readonly")
                match = next((opt for opt in fk_options if opt.startswith(str(current_val))), None)
                if match: editor.set(match)
            else:
                editor = ttk.Entry(tree)
                editor.insert(0, current_val)
            editor.place(x=x, y=y, width=w, height=h)
            editor.focus()
            tree.active_editor = editor

            def save_edit(e=None):
                if not editor.winfo_exists(): return
                new_val = editor.get()
                if col_name == "Művelet":
                    data_rows[tree.index(item_id)]['_import_mode'] = new_val
                else:
                    if col_name in ['client_id', 'end_client_id'] and " - " in new_val: new_val = new_val.split(" - ")[
                        0]
                    data_rows[tree.index(item_id)][col_name] = new_val
                editor.destroy()
                tree.active_editor = None
                tree.active_editor_save = None
                load_and_validate()

            tree.active_editor_save = save_edit

            def handle_focus_out(e):
                def check_focus():
                    if not editor.winfo_exists(): return
                    focused_path = editor.tk.eval('focus')
                    if "popdown" in focused_path.lower(): return
                    save_edit()

                editor.after(100, check_focus)

            editor.bind("<Return>", save_edit)
            editor.bind("<FocusOut>", handle_focus_out)
            if isinstance(editor, ttk.Combobox): editor.bind("<<ComboboxSelected>>", save_edit)

        tree.bind("<Double-1>", on_double_click)

        btn_frame = ttk.Frame(top)
        btn_frame.pack(fill="x", padx=20, pady=10)
        ttk.Button(btn_frame, text="Újraellenőrzés", command=load_and_validate).pack(side="left")

        def perform_save():
            self.db.c.execute(f"PRAGMA table_info({table_name})")
            pk_info = next((r for r in self.db.c.fetchall() if r[5] > 0), None)
            pk_col = pk_info[1] if pk_info else None
            pk_type = pk_info[2].upper() if pk_info else ""
            import_list = []
            for r in data_rows:
                row_copy = dict(r)
                mode = row_copy.pop('_import_mode', "Új bejegyzés (Auto-ID)")
                if mode == "Új bejegyzés (Auto-ID)" and pk_col and pk_col in row_copy and 'INT' in pk_type:
                    row_copy[pk_col] = None
                import_list.append(row_copy)
            success, msg = self.db.bulk_import_data(table_name, import_list)
            if success:
                messagebox.showinfo("Siker", msg, parent=top)
                self.app.notify_project_updated()
                top.destroy()
            else:
                messagebox.showerror("Hiba", msg, parent=top)

        btn_save = ttk.Button(btn_frame, text="Importálás Adatbázisba", command=perform_save, state="disabled")
        btn_save.pack(side="right")
        load_and_validate()