import tkinter as tk
from tkinter import ttk, messagebox
import datetime

# Helyi importok a core mappából
from core.ui_components import AutocompleteCombobox, UIFactory, safe_toplevel


class ContractTab(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.db = self.app.db

        self._build_ui()
        # Frissítjük a partnereket, ha átkattintanak erre a fülre
        self.bind("<Visibility>", lambda e: self.refresh_data())

    def _build_ui(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True, padx=10, pady=10)

        # --- BAL OSZLOP: ŰRLAP ---
        form_frame = ttk.Frame(paned)
        paned.add(form_frame, weight=1)

        canvas = tk.Canvas(form_frame)
        scrollbar = ttk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- ALAPADATOK ---
        f_alap = ttk.LabelFrame(scrollable_frame, text="Alapadatok (Szerződés / Ajánlat)", padding=15)
        f_alap.pack(fill="x", pady=5, padx=5)

        ttk.Label(f_alap, text="Típus:").grid(row=0, column=0, sticky="w", pady=2)
        self.cb_doc_type = ttk.Combobox(f_alap, values=['Szerződés', 'Ajánlat'], state="readonly", width=20)
        self.cb_doc_type.current(0)
        self.cb_doc_type.grid(row=0, column=1, sticky="w", pady=2)
        self.cb_doc_type.bind("<<ComboboxSelected>>", self._on_doc_type_change)

        self.ent_code = UIFactory.create_label_entry(f_alap, "Azonosító:", 1)
        self.ent_code.delete(0, tk.END)
        self.ent_code.insert(0, self.db.generate_next_code("S"))

        ttk.Label(f_alap, text="Megrendelő:").grid(row=2, column=0, sticky="w", pady=2)
        self.cb_client = AutocompleteCombobox(f_alap, width=20)
        self.cb_client.grid(row=2, column=1, sticky="w", pady=2)

        self.cb_c_type = UIFactory.create_label_combo(f_alap, "Szerződés jellege:",
                                                      ['Keretszerződés', 'Projekt szerződés'], 3)
        self.ent_start = UIFactory.create_label_entry(f_alap, "Kezdés:", 4,
                                                      default=datetime.date.today().strftime("%Y.%m.%d."))
        self.ent_end = UIFactory.create_label_entry(f_alap, "Befejezés:", 5, default="Határozatlan")

        # --- PÉNZÜGYEK ---
        f_penz = ttk.LabelFrame(scrollable_frame, text="Díjazás és Szorzók", padding=15)
        f_penz.pack(fill="x", pady=5, padx=5)

        self.cb_fee_type = UIFactory.create_label_combo(f_penz, "Díjazás alapja:",
                                                        ['Óradíj', 'Napidíj', 'Projekt ár', 'Havi átalány',
                                                         'Keretösszeg'], 0)
        self.ent_amount = UIFactory.create_label_entry(f_penz, "Összeg:", 1, default="0")
        self.cb_curr = UIFactory.create_label_combo(f_penz, "Pénznem:", ['HUF', 'EUR', 'USD'], 2)

        ttk.Separator(f_penz, orient='horizontal').grid(row=3, column=0, columnspan=2, sticky="ew", pady=10)

        self.ent_m_over = UIFactory.create_label_entry(f_penz, "Túlóra szorzó (+%):", 4, default="50")
        self.ent_m_over_limit = UIFactory.create_label_entry(f_penz, "Túlóra limit (óra):", 5, default="8")
        self.ent_m_week = UIFactory.create_label_entry(f_penz, "Szombat/Hétvége (+%):", 6, default="50")
        self.ent_m_holi = UIFactory.create_label_entry(f_penz, "Vasárnap/Ünnep (+%):", 7, default="100")
        self.ent_m_night = UIFactory.create_label_entry(f_penz, "Éjszakai munka (+%):", 8, default="25")

        ttk.Separator(f_penz, orient='horizontal').grid(row=9, column=0, columnspan=2, sticky="ew", pady=10)

        self.ent_standby = UIFactory.create_label_entry(f_penz, "Állásidő (Napi):", 10, default="0")
        self.ent_tr_bp = UIFactory.create_label_entry(f_penz, "Kiszállás BP (Ft/alk):", 11, default="7000")
        self.ent_tr_km = UIFactory.create_label_entry(f_penz, "Kiszállás Vidék (Ft/km):", 12, default="250")

        # --- KAPCSOLATTARTÓ ---
        f_kapcs = ttk.LabelFrame(scrollable_frame, text="Kapcsolattartó", padding=15)
        f_kapcs.pack(fill="x", pady=5, padx=5)

        self.ent_c_name = UIFactory.create_label_entry(f_kapcs, "Név:", 0)
        self.ent_c_role = UIFactory.create_label_entry(f_kapcs, "Beosztás:", 1)
        self.ent_c_phone = UIFactory.create_label_entry(f_kapcs, "Telefon:", 2)

        # --- FELTÉTELEK ÉS TARTALOM ---
        f_szov = ttk.LabelFrame(scrollable_frame, text="Szerződéses Feltételek", padding=15)
        f_szov.pack(fill="x", pady=5, padx=5)

        self.ent_tech = UIFactory.create_label_entry(f_szov, "Műszaki tartalom:", 0)
        self.ent_warr = UIFactory.create_label_entry(f_szov, "Garancia feltételek:", 1, default="Átadástól 1 év")
        self.ent_penal = UIFactory.create_label_entry(f_szov, "Kötbér max:", 2, default="Díj 5-10%-ig")
        self.ent_bill = UIFactory.create_label_entry(f_szov, "Számlázás:", 3, default="30 nap")

        ttk.Button(scrollable_frame, text="Szerződés/Ajánlat Mentése", command=self.action_save).pack(pady=20)

        # --- JOBB OSZLOP: LISTA + PARTNEREK ---
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)

        list_frame = ttk.LabelFrame(right_frame, text="Rögzített Szerződések (Dupla katt: Szerkesztés)", padding=10)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("Kód", "Megrendelő", "Jelleg")
        self.tree = ttk.Treeview(list_frame, columns=cols, show='headings', height=10)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)

        scrollbar_t = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_t.set)
        scrollbar_t.pack(side='right', fill='y')
        self.tree.pack(side='left', fill='both', expand=True)

        # Dupla kattintás esemény a szerkesztéshez
        self.tree.bind("<Double-1>", self._on_contract_double_click)

        # Partnerek kezelése a jobb alsó sarokban (szinkronizálva a Project füllel)
        partner_frame = ttk.LabelFrame(right_frame, text="Megrendelők Kezelése (Dupla katt: Adatlap)", padding=10)
        partner_frame.pack(fill="both", expand=True)

        self.list_clients = tk.Listbox(partner_frame, height=6)
        self.list_clients.pack(fill="both", expand=True, pady=(0, 10))
        self.list_clients.bind('<Double-1>', self._on_client_double_click)

        btn_frame_client = ttk.Frame(partner_frame)
        btn_frame_client.pack(fill="x")
        ttk.Button(btn_frame_client, text="Új Hozzáadása", command=lambda: self.open_client_details_window()).pack(
            side="left", expand=True, fill="x", padx=2)
        ttk.Button(btn_frame_client, text="Módosítás", command=self._on_client_edit_click).pack(side="left",
                                                                                                expand=True, fill="x",
                                                                                                padx=2)

        self.refresh_data()

    def _on_doc_type_change(self, event=None):
        dtype = self.cb_doc_type.get()
        self.ent_code.delete(0, tk.END)
        self.ent_code.insert(0, self.db.generate_next_code("S" if dtype == 'Szerződés' else "A"))

    def _on_contract_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        code = self.tree.item(sel[0], "values")[0]
        self.open_contract_details_window(code)

    def open_contract_details_window(self, code):
        is_quote = code.startswith('A')

        # 1. Adatok betöltése ID alapú lekérésekkel
        if is_quote:
            c_data = self.db.get_quote_data(code)
            if not c_data: return
            c_data['contract_type'] = 'Ajánlat'
            c_data['start_date'] = c_data.get('issue_date', '')
            c_data['end_date'] = c_data.get('valid_until', '')
            c_data['tech_content'] = c_data.get('description', '')
            c_data['fee_amount'] = c_data.get('total_amount', 0)
        else:
            c_data = self.db.get_contract_data(code)
            if not c_data: return

        # 2. Felugró ablak létrehozása
        top = safe_toplevel(self, f"Szerkesztés: {code}", "850x950")

        canvas = tk.Canvas(top)
        scrollbar = ttk.Scrollbar(top, orient="vertical", command=canvas.yview)
        sf = ttk.Frame(canvas)
        sf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=sf, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- ALAPADATOK ---
        f_alap = ttk.LabelFrame(sf, text="Alapadatok", padding=15)
        f_alap.pack(fill="x", pady=5, padx=15)

        ttk.Label(f_alap, text="Megrendelő:").grid(row=0, column=0, sticky="w", pady=2)
        cb_client = AutocompleteCombobox(f_alap, width=28)
        cb_client.grid(row=0, column=1, sticky="w", pady=2)
        cb_client.set_completion_list(self.db.get_all_clients())
        cb_client.set(c_data.get('client_name', ''))

        cb_c_type = UIFactory.create_label_combo(f_alap, "Jelleg:", ['Keretszerződés', 'Projekt szerződés', 'Ajánlat'],
                                                 1, 0)
        cb_c_type.set(c_data.get('contract_type', ''))

        ent_start = UIFactory.create_label_entry(f_alap, "Kezdés:", 2, 0, default=c_data.get('start_date', ''))
        ent_end = UIFactory.create_label_entry(f_alap, "Befejezés:", 3, 0, default=c_data.get('end_date', ''))

        # ÚJ: Státusz lenyíló csak ajánlatoknak
        cb_status = None
        if is_quote:
            cb_status = UIFactory.create_label_combo(f_alap, "Státusz:", ['Nyitott', 'Elfogadva', 'Elutasítva'], 4, 0)
            cb_status.set(c_data.get('status', 'Nyitott'))

        # --- PÉNZÜGYEK ---
        f_penz = ttk.LabelFrame(sf, text="Díjazás", padding=15)
        f_penz.pack(fill="x", pady=5, padx=15)

        cb_fee_type = UIFactory.create_label_combo(f_penz, "Alap:",
                                                   ['Óradíj', 'Napidíj', 'Projekt ár', 'Havi átalány', 'Keretösszeg'],
                                                   0, 0)
        cb_fee_type.set(c_data.get('fee_type', 'Óradíj'))
        ent_amount = UIFactory.create_label_entry(f_penz, "Összeg:", 0, 2,
                                                  default=str(c_data.get('fee_amount', 0)).replace('.0', ''))
        cb_curr = UIFactory.create_label_combo(f_penz, "Pénznem:", ['HUF', 'EUR', 'USD'], 1, 0)
        cb_curr.set(c_data.get('currency', 'HUF'))

        ttk.Separator(f_penz, orient='horizontal').grid(row=2, column=0, columnspan=4, sticky="ew", pady=10)

        ent_m_over = UIFactory.create_label_entry(f_penz, "Túlóra (+%):", 3, 0,
                                                  default=str(c_data.get('mult_overtime', 50)).replace('.0', ''))
        ent_m_over_limit = UIFactory.create_label_entry(f_penz, "Túlóra limit (óra):", 3, 2, default="8")
        ent_m_week = UIFactory.create_label_entry(f_penz, "Szombat (+%):", 4, 0,
                                                  default=str(c_data.get('mult_weekend', 50)).replace('.0', ''))
        ent_m_holi = UIFactory.create_label_entry(f_penz, "Ünnep (+%):", 4, 2,
                                                  default=str(c_data.get('mult_holiday', 100)).replace('.0', ''))
        ent_m_night = UIFactory.create_label_entry(f_penz, "Éjszaka (+%):", 5, 0,
                                                   default=str(c_data.get('mult_night', 25)).replace('.0', ''))

        ttk.Separator(f_penz, orient='horizontal').grid(row=6, column=0, columnspan=4, sticky="ew", pady=10)

        ent_standby = UIFactory.create_label_entry(f_penz, "Állásidő:", 7, 0,
                                                   default=str(c_data.get('standby_fee', 0)).replace('.0', ''))
        ent_tr_bp = UIFactory.create_label_entry(f_penz, "Kisz. BP:", 7, 2,
                                                 default=str(c_data.get('travel_bp', 7000)).replace('.0', ''))
        ent_tr_km = UIFactory.create_label_entry(f_penz, "Kisz. Vidék:", 8, 0,
                                                 default=str(c_data.get('travel_km', 250)).replace('.0', ''))

        # ÚJ: Ha ajánlat, a felesleges (ghost) mezőket letiltjuk a UI-n
        state = 'disabled' if is_quote else 'normal'
        if is_quote:
            for w in [cb_fee_type, ent_m_over, ent_m_over_limit, ent_m_week, ent_m_holi, ent_m_night, ent_standby,
                      ent_tr_bp, ent_tr_km]:
                w.config(state=state)

        # --- KAPCSOLATTARTÓ ---
        f_kapcs = ttk.LabelFrame(sf, text="Kapcsolattartó", padding=15)
        f_kapcs.pack(fill="x", pady=5, padx=15)
        ent_c_name = UIFactory.create_label_entry(f_kapcs, "Név:", 0, 0, default=c_data.get('contact_name', ''))
        ent_c_role = UIFactory.create_label_entry(f_kapcs, "Beosztás:", 0, 2, default=c_data.get('contact_role', ''))
        ent_c_phone = UIFactory.create_label_entry(f_kapcs, "Telefon:", 1, 0, default=c_data.get('contact_phone', ''))
        if is_quote:
            for w in [ent_c_name, ent_c_role, ent_c_phone]: w.config(state=state)

        # --- FELTÉTELEK ---
        f_szov = ttk.LabelFrame(sf, text="Feltételek", padding=15)
        f_szov.pack(fill="x", pady=5, padx=15)
        ent_tech = UIFactory.create_label_entry(f_szov, "Műszaki tartalom:", 0, 0, width=50,
                                                default=c_data.get('tech_content', ''))
        ent_warr = UIFactory.create_label_entry(f_szov, "Garancia:", 1, 0, width=50,
                                                default=c_data.get('warranty_terms', ''))
        ent_penal = UIFactory.create_label_entry(f_szov, "Kötbér:", 2, 0, width=50,
                                                 default=c_data.get('penalty_terms', ''))
        ent_bill = UIFactory.create_label_entry(f_szov, "Számlázás:", 3, 0, width=50,
                                                default=c_data.get('billing_terms', ''))
        if is_quote:
            for w in [ent_warr, ent_penal, ent_bill]: w.config(state=state)

        def save():
            client_name = cb_client.get()
            client_data = self.db.get_client(client_name)
            if not client_data:
                messagebox.showwarning("Hiba", "A megadott Partner nem létezik az adatbázisban!", parent=top)
                return
            client_id = client_data['id']

            try:
                amt = float(ent_amount.get().replace(' ', '').replace(',', '.') or 0)
                m_o = float(ent_m_over.get().replace(',', '.') or 0) if not is_quote else 0
                m_w = float(ent_m_week.get().replace(',', '.') or 0) if not is_quote else 0
                m_h = float(ent_m_holi.get().replace(',', '.') or 0) if not is_quote else 0
                m_n = float(ent_m_night.get().replace(',', '.') or 0) if not is_quote else 0
                stb = float(ent_standby.get().replace(',', '.') or 0) if not is_quote else 0
                t_bp = float(ent_tr_bp.get().replace(',', '.') or 0) if not is_quote else 0
                t_km = float(ent_tr_km.get().replace(',', '.') or 0) if not is_quote else 0
            except ValueError:
                messagebox.showwarning("Hiba", "A díjak és szorzók csak számok lehetnek!", parent=top)
                return

            if is_quote:
                quote_data = {
                    'quote_code': code, 'client_id': client_id, 'issue_date': ent_start.get(),
                    'valid_until': ent_end.get(), 'description': ent_tech.get(),
                    'total_amount': amt, 'currency': cb_curr.get(), 'status': cb_status.get()
                }
                succ, msg = self.db.update_quote(quote_data)
            else:
                new_data = {
                    'contract_code': code, 'client_id': client_id, 'contract_type': cb_c_type.get(),
                    'fee_type': cb_fee_type.get(), 'fee_amount': amt, 'currency': cb_curr.get(),
                    'mult_overtime': m_o, 'mult_weekend': m_w, 'mult_holiday': m_h, 'mult_night': m_n,
                    'standby_fee': stb, 'travel_bp': t_bp, 'travel_km': t_km, 'start_date': ent_start.get(),
                    'end_date': ent_end.get(), 'contact_name': ent_c_name.get(), 'contact_role': ent_c_role.get(),
                    'contact_phone': ent_c_phone.get(), 'tech_content': ent_tech.get(),
                    'warranty_terms': ent_warr.get(),
                    'penalty_terms': ent_penal.get(), 'billing_terms': ent_bill.get(), 'other_terms': "",
                    'mult_overtime_threshold': float(ent_m_over_limit.get() or 8)
                }
                succ, msg = self.db.update_contract(new_data)

            if succ:
                self.refresh_data()
                self.app.notify_project_updated()
                top.destroy()
            else:
                messagebox.showerror("Hiba", msg, parent=top)

        btn_box = ttk.Frame(sf)
        btn_box.pack(pady=20)

        # ÚJ: Ajánlat esetén Konvertáló gomb
        if is_quote:
            def convert_to_contract():
                # 1. Adatok kimentése a UI-ból, MIELŐTT a save() bezárná és megsemmisítené az ablakot!
                c_name = cb_client.get()
                amt_str = ent_amount.get()
                curr_str = cb_curr.get()
                start_str = ent_start.get()
                end_str = ent_end.get()
                tech_str = ent_tech.get()

                # 2. Ajánlat státuszának beállítása és mentés/frissítés
                cb_status.set('Elfogadva')
                save()

                # 3. Ha a mentés sikeres volt, a save() megsemmisítette a 'top' ablakot.
                if not top.winfo_exists():
                    new_s_code = self.db.generate_next_code("S")
                    client_id = self.db.get_client(c_name)['id']
                    amt = float(amt_str.replace(' ', '').replace(',', '.') or 0)

                    contract_data = {
                        'contract_code': new_s_code, 'client_id': client_id, 'contract_type': 'Projekt szerződés',
                        'fee_type': 'Projekt ár', 'fee_amount': amt, 'currency': curr_str,
                        'mult_overtime': 50, 'mult_weekend': 50, 'mult_holiday': 100, 'mult_night': 25,
                        'standby_fee': 0, 'travel_bp': 7000, 'travel_km': 250, 'start_date': start_str,
                        'end_date': end_str, 'contact_name': '', 'contact_role': '',
                        'contact_phone': '', 'tech_content': tech_str,
                        'warranty_terms': 'Átadástól 1 év',
                        'penalty_terms': 'Díj 5-10%-ig', 'billing_terms': '30 nap', 'other_terms': "",
                        'mult_overtime_threshold': 8
                    }

                    s, m = self.db.insert_contract(contract_data)
                    if s:
                        messagebox.showinfo("Konvertálva", f"Ajánlat elfogadva! Új szerződés generálva: {new_s_code}")
                        self.refresh_data()
                        self.app.notify_project_updated()
                    else:
                        messagebox.showerror("Hiba generáláskor", m)

            ttk.Button(btn_box, text="Ajánlat elfogadása (Szerződés generálása)", command=convert_to_contract).pack(
                side="left", padx=10)

        ttk.Button(btn_box, text="Mentés / Frissítés", command=save).pack(side="left", padx=10)

        top.shortcut_ctrl_s = save

    # ------------------
    # FŐ ŰRLAP MENTÉSE:
    # ------------------
    def action_save(self):
        client_name = self.cb_client.get()
        client_data = self.db.get_client(client_name)
        if not client_data:
            messagebox.showwarning("Hiba",
                                   "A megadott Partner nem létezik! Kérlek válassz a listából vagy rögzíts újat.")
            return
        client_id = client_data['id']

        try:
            amt = float(self.ent_amount.get().replace(' ', '').replace(',', '.') or 0)
            m_o = float(self.ent_m_over.get().replace(',', '.') or 0)
            m_w = float(self.ent_m_week.get().replace(',', '.') or 0)
            m_h = float(self.ent_m_holi.get().replace(',', '.') or 0)
            m_n = float(self.ent_m_night.get().replace(',', '.') or 0)
            stb = float(self.ent_standby.get().replace(',', '.') or 0)
            t_bp = float(self.ent_tr_bp.get().replace(',', '.') or 0)
            t_km = float(self.ent_tr_km.get().replace(',', '.') or 0)
        except ValueError:
            messagebox.showwarning("Hiba", "A díjak és szorzók csak számok lehetnek!")
            return

        code = self.ent_code.get()

        data = {
            'contract_code': code, 'client_id': client_id, 'contract_type': self.cb_c_type.get(),
            'fee_type': self.cb_fee_type.get(), 'fee_amount': amt, 'currency': self.cb_curr.get(),
            'mult_overtime': m_o, 'mult_weekend': m_w, 'mult_holiday': m_h, 'mult_night': m_n,
            'standby_fee': stb, 'travel_bp': t_bp, 'travel_km': t_km, 'start_date': self.ent_start.get(),
            'end_date': self.ent_end.get(), 'contact_name': self.ent_c_name.get(),
            'contact_role': self.ent_c_role.get(),
            'contact_phone': self.ent_c_phone.get(), 'tech_content': self.ent_tech.get(),
            'warranty_terms': self.ent_warr.get(),
            'penalty_terms': self.ent_penal.get(), 'billing_terms': self.ent_bill.get(), 'other_terms': "",
            'mult_overtime_threshold': float(self.ent_m_over_limit.get() or 8)
        }

        if self.cb_doc_type.get() == 'Ajánlat':
            quote_data = {
                'quote_code': code, 'client_id': client_id, 'issue_date': self.ent_start.get(),
                'valid_until': self.ent_end.get(), 'description': self.ent_tech.get(), 'total_amount': amt,
                'currency': self.cb_curr.get(), 'status': 'Nyitott'
            }
            if self.db.get_quote_data(code):
                succ, msg = self.db.update_quote(quote_data)
            else:
                succ, msg = self.db.insert_quote(quote_data)
        else:
            if self.db.get_contract_data(code):
                succ, msg = self.db.update_contract(data)
            else:
                succ, msg = self.db.insert_contract(data)

        if succ:
            messagebox.showinfo("Siker", msg)
            self.refresh_data()
            self._on_doc_type_change()
            self.app.notify_project_updated()
        else:
            messagebox.showerror("Hiba", msg)

    def refresh_data(self):
        clients = self.db.get_all_clients()
        self.cb_client.set_completion_list(clients)

        self.list_clients.delete(0, tk.END)
        for c in clients: self.list_clients.insert(tk.END, c)

        for i in self.tree.get_children(): self.tree.delete(i)
        for r in self.db.get_all_contracts(): self.tree.insert("", "end", values=r)

    # --- Partnerek metódusai ---
    def _on_client_double_click(self, event):
        sel = self.list_clients.curselection()
        if sel: self.open_client_details_window(self.list_clients.get(sel[0]))

    def _on_client_edit_click(self):
        sel = self.list_clients.curselection()
        if sel:
            self.open_client_details_window(self.list_clients.get(sel[0]))
        else:
            messagebox.showwarning("Figyelmeztetés", "Jelölj ki egy partnert!")

    def open_client_details_window(self, client_name=None):
        is_new = client_name is None
        # Bővült a data szótár a bank_account-tal
        data = {'name': '', 'address': '', 'tax_number': '', 'email': '', 'phone': '', 'bank_account': ''}

        if not is_new:
            db_data = self.db.get_client(client_name)
            if db_data: data.update(db_data)

        # Magasság növelése 420-ra, hogy kiférjen az új mező
        top = safe_toplevel(self, "Új Partner rögzítése" if is_new else f"Partner Szerkesztése: {client_name}",
                            "500x420")
        f = ttk.Frame(top, padding=20)
        f.pack(fill="both", expand=True)

        # Vizuális mankók a címkékben a Regex formátumokhoz
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
                # Értesítjük a UI-t, hogy töltse újra a listákat
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
        """Ctrl+S hatására lenyomja a Szerződés mentése gombot."""
        self.action_save()

    def shortcut_ctrl_n(self):
        """Ctrl+N hatására megnyitja az Új Partner ablakot."""
        self.open_client_details_window()