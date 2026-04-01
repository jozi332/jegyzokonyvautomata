import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from core.ui_components import AutocompleteCombobox, UIFactory, safe_toplevel


class ProjectTab(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.db = self.app.db
        self.rg = self.app.rg

        self._build_ui()

    def _build_ui(self):
        top_container = ttk.Frame(self)
        top_container.pack(fill="x", padx=20, pady=10)

        # --- ÚJ PROJEKT KERET ---
        frame = ttk.LabelFrame(top_container, text="Új Projekt Létrehozása", padding=20)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ttk.Label(frame, text="--- Alapadatok ---", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, columnspan=2,
                                                                                       pady=(0, 5), sticky="w")

        self.ent_p_code = UIFactory.create_label_entry(frame, "Projekt Azonosító:", 1)
        self.ent_p_code.delete(0, tk.END)
        self.ent_p_code.insert(0, self.db.generate_next_code("WJP"))

        ttk.Label(frame, text="Kapcsolódó Szerződés:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.cb_p_contr = AutocompleteCombobox(frame, width=28)
        self.cb_p_contr.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self.cb_p_contr.bind("<<ComboboxSelected>>", self._on_contract_selected)

        ttk.Label(frame, text="Végfelhasználó:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.ent_p_client = AutocompleteCombobox(frame, width=28)
        self.ent_p_client.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        self.ent_p_client.set_completion_list(self.db.get_all_clients())

        self.ent_p_client_ref = UIFactory.create_label_entry(frame, "Megr. hivatkozás (PO stb):", 4)
        self.ent_p_desc = UIFactory.create_label_entry(frame, "Projekt Leírás / Név:", 5)
        self.ent_p_date = UIFactory.create_label_entry(frame, "Kezdés Dátuma:", 6,
                                                       default=datetime.date.today().strftime("%Y.%m.%d."))
        self.cb_p_status = UIFactory.create_label_combo(frame, "Státusz:", ['Active', 'Completed'], 7)

        btn_save = ttk.Button(frame, text="Mentés (Projekt)", command=self.action_save_project)
        btn_save.grid(row=8, column=1, pady=20)

        # --- PARTNEREK KERET ---
        partner_frame = ttk.LabelFrame(top_container, text="Végfelhasználók (Dupla kattintás: Adatlap)", padding=20)
        partner_frame.pack(side="left", fill="both", expand=True, padx=(10, 0))

        self.list_clients = tk.Listbox(partner_frame, height=8)
        self.list_clients.pack(fill="both", expand=True, pady=(0, 10))
        self.list_clients.bind('<Double-1>', self._on_client_double_click)

        btn_frame_client = ttk.Frame(partner_frame)
        btn_frame_client.pack(fill="x")
        ttk.Button(btn_frame_client, text="Új Hozzáadása", command=lambda: self.open_client_details_window()).pack(
            side="left", expand=True, fill="x", padx=2)
        ttk.Button(btn_frame_client, text="Módosítás", command=self._on_client_edit_click).pack(side="left",
                                                                                                expand=True, fill="x",
                                                                                                padx=2)
        ttk.Button(btn_frame_client, text="Törlés", command=self.action_delete_client).pack(side="left", expand=True,
                                                                                            fill="x", padx=2)

        self._refresh_client_list()

        # --- PROJEKT LISTA KERET ---
        bottom_container = ttk.Frame(self)
        bottom_container.pack(fill="both", expand=True, padx=20, pady=10)

        list_frame = ttk.LabelFrame(bottom_container, text="Létező Projektek (Dupla kattintás: Szerkesztés)",
                                    padding=10)
        list_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        cols = ("Kód", "Típus", "Megrendelői hiv.", "Leírás", "Össz. Óra")
        self.tree_projects = ttk.Treeview(list_frame, columns=cols, show='headings', height=10)
        for col in cols:
            self.tree_projects.heading(col, text=col)
            w = 300 if col == "Leírás" else 120
            self.tree_projects.column(col, width=w)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_projects.yview)
        self.tree_projects.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree_projects.pack(side='left', fill='both', expand=True)

        self.tree_projects.bind("<Double-1>", self._on_project_double_click)
        # ÚJ: Figyeli a kijelölést az okos gombhoz
        self.tree_projects.bind("<<TreeviewSelect>>", self._on_project_select)

        # --- PROJEKT MŰVELETEK KERET ---
        self.action_frame = ttk.LabelFrame(bottom_container, text="Kijelölt Elem Műveletek", padding=20)
        self.action_frame.pack(side="right", fill="y")

        ttk.Button(self.action_frame, text="Teljes Projekt PDF Generálása\n(Munkalap + Jegyzőkönyvek)",
                   command=self.action_generate_selected_pdf).pack(pady=20, fill="x")

        # ÚJ: Projekt lezáró és Full Generáló Gomb (Alapból rejtett)
        self.btn_close_project = ttk.Button(self.action_frame,
                                            text="Projekt Lezárása\nés Teljes Dokumentáció (EOJ+TIG)",
                                            command=self.action_close_standalone_project)
        self.btn_close_project.pack_forget()

        # --- IDE TEDD BE A FRISSÍTÉST: ---
        self.refresh_project_list()

    # ==========================================
    # PROJEKT FUNKCIÓK
    # ==========================================
    def _on_contract_selected(self, event=None):
        contract_str = self.cb_p_contr.get()
        if not contract_str: return
        contract_code = contract_str.split(' - ')[0]
        c_data = self.db.get_contract_data(contract_code)
        if c_data:
            self.ent_p_client.set(c_data.get('client_name', ''))

    def action_save_project(self):
        contract_val = self.cb_p_contr.get().split(' - ')[0] if self.cb_p_contr.get() else ""
        client_name = self.ent_p_client.get()
        client_data = self.db.get_client(client_name)
        if not client_data:
            messagebox.showwarning("Hiba", "A megadott Végfelhasználó nem létezik az adatbázisban!")
            return

        data = {
            'code': self.ent_p_code.get(),
            'end_client_id': client_data['id'],
            'desc': self.ent_p_desc.get(),
            'contract_code': contract_val,
            'start': self.ent_p_date.get(),
            'status': self.cb_p_status.get(),
            'type': 'Normál',
            'client_ref': self.ent_p_client_ref.get()
        }

        success, msg = self.db.insert_project(data)
        if success:
            messagebox.showinfo("Siker", msg)
            self.refresh_project_list()
            self.ent_p_desc.delete(0, tk.END)
            self.ent_p_client_ref.delete(0, tk.END)
            self.cb_p_contr.set('')
            self.ent_p_code.delete(0, tk.END)
            self.ent_p_code.insert(0, self.db.generate_next_code("WJP"))
            self.app.notify_project_updated()
        else:
            messagebox.showerror("Hiba", msg)

    def refresh_project_list(self):
        contracts = [f"{c[0]} - {c[1]}" for c in self.db.get_all_contracts() if c[2] != 'Ajánlat']
        self.cb_p_contr.set_completion_list(contracts)
        self._refresh_client_list()
        for i in self.tree_projects.get_children():
            self.tree_projects.delete(i)
        for r in self.db.get_project_stats():
            self.tree_projects.insert("", "end", values=(r[0], r[1], r[2], r[3], f"{r[4]:g}"))

        # Elrejtjük az okos gombot frissítéskor (mivel a kijelölés eltűnik)
        self.btn_close_project.pack_forget()

    def _on_project_select(self, event):
        """Kijelöléskor megnézi, hogy a projekt önálló-e, és nyitott-e még."""
        sel = self.tree_projects.selection()
        if not sel:
            self.btn_close_project.pack_forget()
            return

        project_code = self.tree_projects.item(sel[0], "values")[0]
        p_data = self.db.get_project_data(project_code)
        if not p_data:
            self.btn_close_project.pack_forget()
            return

        c_data = self.db.get_contract_data(p_data['contract_code'])
        # Ha a szerződés "Projekt szerződés" (önálló) ÉS a projekt még nincs lezárva
        if c_data and c_data.get('contract_type') == 'Projekt szerződés' and p_data.get('status') != 'Completed':
            self.btn_close_project.pack(pady=10, fill="x")
        else:
            self.btn_close_project.pack_forget()

    def action_close_standalone_project(self):
        """Önálló projekt automatikus lezárása és mind a 3 PDF legenerálása."""
        sel = self.tree_projects.selection()
        if not sel: return
        project_code = self.tree_projects.item(sel[0], "values")[0]

        if not messagebox.askyesno("Megerősítés",
                                   f"Biztosan lezáród a {project_code} projektet?\nEz átállítja a státuszt 'Completed'-re, és kigenerálja a Munkalapot, az EOJ-t és a TIG-et is!"):
            return

        p_data = self.db.get_project_data(project_code)
        today_str = datetime.date.today().strftime("%Y.%m.%d.")

        update_data = {
            'code': p_data['project_code'],
            'end_client_id': p_data['end_client_id'],
            'desc': p_data['description'],
            'contract_code': p_data['contract_code'],
            'start': p_data['start_date'],
            'status': 'Completed',
            'type': p_data.get('project_type', 'Normál'),
            'client_ref': p_data.get('client_ref', '')
        }

        succ, msg = self.db.update_project(update_data)
        if not succ:
            messagebox.showerror("Hiba", f"Nem sikerült lezárni a projektet:\n{msg}")
            return

        self.refresh_project_list()

        # 1. Generáljuk a Teljes Projekt PDF-et
        succ1, fp1 = self.rg.generate_full_project_report(project_code)

        # 2. Generáljuk az EOJ-t és TIG-et (A projekt kezdődátumától a mai napig)
        start_d = p_data.get('start_date', '')
        if not start_d: start_d = today_str
        res2 = self.rg.generate_contract_settlement(p_data['contract_code'], start_d, today_str)

        if succ1 and res2[0]:
            succ2, eoj_path, ti_path = res2
            # Mind a három fájlt megnyitjuk a felhasználónak
            self.rg.open_pdf(fp1)
            self.rg.open_pdf(eoj_path)
            self.rg.open_pdf(ti_path)
            messagebox.showinfo("Siker",
                                "Projekt sikeresen lezárva!\n\nA Teljes Projekt PDF, az EOJ és a TIG elkészült és megnyitásra került.")
        else:
            err_msg = ""
            if not succ1: err_msg += f"Hiba a projekt PDF generálásakor: {fp1}\n"
            if not res2[0]: err_msg += f"Hiba az EOJ/TIG generálásakor: {res2[1]}\n"
            messagebox.showerror("Hiba", err_msg)

    def open_project_details_window(self, code):
        p = self.db.get_project_data(code)
        if not p: return
        logs = self.db.get_daily_logs(code)

        top = safe_toplevel(self, f"Projekt: {code}", "1100x850")

        info = ttk.LabelFrame(top, text="Adatok Szerkesztése", padding=15)
        info.pack(fill='x', padx=15, pady=10)

        ttk.Label(info, text="Végfelhasználó:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        cb_client = AutocompleteCombobox(info, width=28)
        cb_client.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        cb_client.set_completion_list(self.db.get_all_clients())
        cb_client.set(p.get('end_client_name') or '')

        ent_st = UIFactory.create_label_entry(info, "Kezdés:", 0, 2, width=15, default=p.get('start_date') or '')
        ent_ds = UIFactory.create_label_entry(info, "Leírás:", 1, 0, width=40, default=p.get('description') or '')
        cb_s = UIFactory.create_label_combo(info, "Státusz:", ['Active', 'Completed'], 1, 2)
        cb_s.set(p.get('status') or 'Active')

        ent_contr = UIFactory.create_label_entry(info, "Szerződés (S-kód):", 2, 0, width=40,
                                                 default=p.get('contract_code') or '')
        ent_ref = UIFactory.create_label_entry(info, "Megrendelői hivatkozás:", 2, 2, width=28,
                                               default=p.get('client_ref') or '')

        btn_box = ttk.Frame(info)
        btn_box.grid(row=3, column=0, columnspan=4, pady=15)

        def save_proj():
            c_name = cb_client.get()
            c_data = self.db.get_client(c_name)
            if not c_data:
                messagebox.showwarning("Hiba", "A megadott Végfelhasználó nem létezik!", parent=top)
                return

            self.db.update_project({
                'code': code, 'end_client_id': c_data['id'], 'desc': ent_ds.get(),
                'contract_code': ent_contr.get(), 'start': ent_st.get(), 'status': cb_s.get(),
                'type': p.get('project_type') or 'Normál', 'client_ref': ent_ref.get()
            })
            self.refresh_project_list()
            self.app.notify_project_updated()
            top.destroy()

        ttk.Button(btn_box, text="Mentés", command=save_proj).pack(side="left", padx=10)
        ttk.Button(btn_box, text="PDF Munkalap",
                   command=lambda: self.rg.open_pdf(self.rg.generate_report(code, logs, p)[1])).pack(side="left",
                                                                                                     padx=10)
        ttk.Button(btn_box, text="Teljes Projekt PDF",
                   command=lambda: self.rg.open_pdf(self.rg.generate_full_project_report(code)[1])).pack(side="left",
                                                                                                         padx=10)

        l_f = ttk.LabelFrame(top, text="Naplók (Dupla kattintás a szerkesztéshez)", padding=10)
        l_f.pack(fill="both", expand=True, padx=15, pady=10)

        t = ttk.Treeview(l_f, columns=("ID", "D", "T", "O", "K"), show="headings", displaycolumns=("D", "T", "O", "K"))
        t.heading("D", text="Dátum");
        t.heading("T", text="Tevékenység")
        t.heading("O", text="Óra");
        t.heading("K", text="Költség")
        t.column("T", width=450)
        t.pack(fill="both", expand=True)

        for l in logs:
            cost = (l['material_cost'] or 0) + (l.get('travel_cost', 0) or 0)
            t.insert("", "end",
                     values=(l['log_id'], l['date'], l['activity'], f"{l['engineer_hours']:g}", f"{int(cost):,} Ft"))

        def on_proj_log_double_click(event):
            sel = t.selection()
            if sel:
                self.app.open_log_editor(t.item(sel[0], "values")[0], parent_win=top)

        t.bind("<Double-1>", on_proj_log_double_click)
        top.shortcut_ctrl_s = save_proj

    def _on_project_double_click(self, event):
        sel = self.tree_projects.selection()
        if sel:
            self.open_project_details_window(self.tree_projects.item(sel[0], "values")[0])

    def action_generate_selected_pdf(self):
        sel = self.tree_projects.selection()
        if not sel:
            messagebox.showwarning("Figyelmeztetés", "Kérlek jelölj ki egy projektet a listából!")
            return
        project_code = self.tree_projects.item(sel[0], "values")[0]
        success, filepath = self.rg.generate_full_project_report(project_code)
        if success:
            self.rg.open_pdf(filepath)
        else:
            messagebox.showerror("Hiba", filepath)

    # ==========================================
    # PARTNER FUNKCIÓK
    # ==========================================
    def _refresh_client_list(self):
        self.list_clients.delete(0, tk.END)
        for c in self.db.get_all_clients():
            self.list_clients.insert(tk.END, c)
        self.ent_p_client.set_completion_list(self.db.get_all_clients())

    def _on_client_double_click(self, event):
        sel = self.list_clients.curselection()
        if sel: self.open_client_details_window(self.list_clients.get(sel[0]))

    def _on_client_edit_click(self):
        sel = self.list_clients.curselection()
        if sel:
            self.open_client_details_window(self.list_clients.get(sel[0]))
        else:
            messagebox.showwarning("Figyelmeztetés", "Kérlek jelölj ki egy partnert a listából!")

    def action_delete_client(self):
        sel = self.list_clients.curselection()
        if not sel: return
        name = self.list_clients.get(sel[0])
        if messagebox.askyesno("Törlés", f"Biztosan törlöd a partnert: {name}?"):
            self.db.delete_client(name)
            self._refresh_client_list()

    def open_client_details_window(self, client_name=None):
        is_new = client_name is None
        data = {'name': '', 'address': '', 'tax_number': '', 'email': '', 'phone': '', 'bank_account': ''}

        if not is_new:
            db_data = self.db.get_client(client_name)
            if db_data: data.update(db_data)

        top = safe_toplevel(self, "Új Partner rögzítése" if is_new else f"Partner Szerkesztése: {client_name}",
                            "500x420")
        f = ttk.Frame(top, padding=20)
        f.pack(fill="both", expand=True)

        ent_name = UIFactory.create_label_entry(f, "Partner Neve *:", 0, width=40, default=data.get('name', ''))
        ent_address = UIFactory.create_label_entry(f, "Cím / Székhely:", 1, width=40, default=data.get('address', ''))
        ent_tax = UIFactory.create_label_entry(f, "Adószám (12345678-1-42):", 2, width=40,
                                               default=data.get('tax_number', ''))
        ent_email = UIFactory.create_label_entry(f, "E-mail cím:", 3, width=40, default=data.get('email', ''))
        ent_phone = UIFactory.create_label_entry(f, "Telefonszám:", 4, width=40, default=data.get('phone', ''))
        ent_bank = UIFactory.create_label_entry(f, "Bankszámla (8-8 vagy 8-8-8):", 5, width=40,
                                                default=data.get('bank_account', ''))

        def save():
            new_data = {
                'name': ent_name.get().strip(), 'address': ent_address.get().strip(),
                'tax_number': ent_tax.get().strip(), 'email': ent_email.get().strip(),
                'phone': ent_phone.get().strip(), 'bank_account': ent_bank.get().strip()
            }
            if not new_data['name']:
                messagebox.showwarning("Hiba", "A Partner nevének megadása kötelező!", parent=top)
                return

            if is_new:
                succ, msg = self.db.add_client_full(new_data)
            else:
                succ, msg = self.db.update_client_full(client_name, new_data)

            if succ:
                if hasattr(self, '_refresh_client_list'):
                    self._refresh_client_list()
                else:
                    self.refresh_data()
                self.app.notify_project_updated()
                top.destroy()
            else:
                messagebox.showerror("Hiba", msg, parent=top)

        btn_f = ttk.Frame(f)
        btn_f.grid(row=6, column=0, columnspan=2, pady=20, sticky="e")
        ttk.Button(btn_f, text="Mégse", command=top.destroy).pack(side="left", padx=5)
        ttk.Button(btn_f, text="Mentés", command=save).pack(side="left", padx=5)

        top.shortcut_ctrl_s = save

    def shortcut_ctrl_s(self):
        self.action_save_project()

    def shortcut_ctrl_n(self):
        self.open_client_details_window()