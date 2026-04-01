import tkinter as tk
from tkinter import ttk, messagebox
import datetime

# Helyi importok a core mappából
from core.ui_components import AutocompleteCombobox, UIFactory, safe_toplevel

class LogsTab(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context       # Fő alkalmazás hivatkozása
        self.db = self.app.db        # Adatbázis manager
        self.rg = self.app.rg        # Riport generátor
        
        self._build_ui()

    def _build_ui(self):
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        form_frame = ttk.Frame(paned, padding=10)
        paned.add(form_frame, weight=3)

        # --- ALAPADATOK KERET ---
        info_f = ttk.LabelFrame(form_frame, text="Alapadatok", padding=10)
        info_f.pack(fill="x", pady=5)
        ttk.Label(info_f, text="Projekt:").grid(row=0, column=0, sticky="w")
        self.ent_l_proj = AutocompleteCombobox(info_f, width=40)
        self.ent_l_proj.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.ent_l_date = UIFactory.create_label_entry(info_f, "Dátum:", 1,
                                                       default=datetime.date.today().strftime("%Y.%m.%d."))
        self.var_holiday = tk.BooleanVar()
        ttk.Checkbutton(info_f, text="Vasárnap / Ünnepnap (+100%)", variable=self.var_holiday).grid(row=1, column=2,
                                                                                                    sticky="w", padx=10)

        def check_sunday(event):
            d_str = self._format_date_input(self.ent_l_date.get())
            if d_str:
                try:
                    d_obj = datetime.datetime.strptime(d_str, "%Y.%m.%d.")
                    if d_obj.weekday() == 6:  # 6 = Vasárnap
                        self.var_holiday.set(True)
                    else:
                        self.var_holiday.set(False)  # Hétköznapnál kivesszük
                except:
                    pass

        self.ent_l_date.bind("<FocusOut>", check_sunday)
        check_sunday(None)
        self.txt_l_act = UIFactory.create_label_entry(info_f, "Tevékenység:", 2, width=40)
        self.ent_l_hours = UIFactory.create_label_entry(info_f, "Mérnökóra:", 3, default="0")
        self.ent_l_mat = UIFactory.create_label_entry(info_f, "Anyagköltség:", 4, default="0")
        self.ent_l_mat_inv = UIFactory.create_label_entry(info_f, "Anyag számlaszám:", 5, width=40)
        self.ent_l_att = UIFactory.create_label_entry(info_f, "Melléklet ID:", 6)

        # --- EREDMÉNY KERET ---
        text_f = ttk.LabelFrame(form_frame, text="Leírás", padding=10)
        text_f.pack(fill="x", pady=5)
        self.txt_l_res = UIFactory.create_scrolled_text(text_f, "", 0, width=80)

        # --- DINAMIKUS ESEMÉNYEK KERET (UTAZÁSSAL) ---
        ev_f = ttk.LabelFrame(form_frame, text="Napi Események (Munka és Utazás)", padding=10)
        ev_f.pack(fill="x", pady=5)

        ev_in = ttk.Frame(ev_f)
        ev_in.pack(fill="x")
        self.ent_ev_start = UIFactory.create_label_entry(ev_in, "Kezdés:", 0, 0, width=8)
        self.ent_ev_end = UIFactory.create_label_entry(ev_in, "Vége:", 0, 2, width=8)

        self.var_is_night = tk.BooleanVar()
        self.chk_night = ttk.Checkbutton(ev_in, text="Éjszakai", variable=self.var_is_night)
        self.chk_night.grid(row=0, column=4, padx=5)

        self.var_is_travel = tk.BooleanVar()
        ttk.Checkbutton(ev_in, text="Utazás", variable=self.var_is_travel, command=self._toggle_travel_frame).grid(
            row=0, column=5, padx=10)

        self.ent_ev_desc = UIFactory.create_label_entry(ev_in, "Leírás:", 0, 6, width=20)
        ttk.Button(ev_in, text="Hozzáad", command=self._add_event_to_list).grid(row=0, column=8, padx=10)


        # Rejtett Utazás panel
        self.f_tr_details = ttk.Frame(ev_f)
        ttk.Label(self.f_tr_details, text="Típus:").grid(row=0, column=0, padx=2)
        self.cb_t_type = ttk.Combobox(self.f_tr_details,
                                      values=['Magán autó Céges használat', 'Céges autó Magán használat', 'Iroda'],
                                      state="readonly", width=22)
        self.cb_t_type.grid(row=0, column=1, padx=2)
        self.cb_t_type.bind("<<ComboboxSelected>>", self._on_travel_type_change)

        self.ent_t_start = UIFactory.create_label_entry(self.f_tr_details, "Honnan:", 0, 2, width=15)
        self.ent_t_end = UIFactory.create_label_entry(self.f_tr_details, "Hova:", 0, 4, width=15)
        self.ent_t_dist = UIFactory.create_label_entry(self.f_tr_details, "Táv (km):", 0, 6, width=8)

        # Fa struktúra
        tree_f = ttk.Frame(ev_f)
        tree_f.pack(fill="x", pady=5)
        self.tree_events = ttk.Treeview(tree_f, columns=("T", "S", "E", "D"), show='headings', height=4)
        self.tree_events.heading("T", text="Típus")
        self.tree_events.heading("S", text="Kezd")
        self.tree_events.heading("E", text="Vége")
        self.tree_events.heading("D", text="Leírás / Részletek")
        self.tree_events.column("T", width=60)
        self.tree_events.column("S", width=60)
        self.tree_events.column("E", width=60)
        self.tree_events.pack(side="left", fill="x", expand=True)

        ttk.Button(tree_f, text="Törlés", command=self._delete_event).pack(side="right", padx=5)
        # ÚJ CÍMKE:
        self.lbl_ev_summary = ttk.Label(tree_f, text="Számított idő: 0 óra munka | 0 óra utazás",
                                        font=("Segoe UI", 9, "bold"))
        self.lbl_ev_summary.pack(side="left", padx=10)
        self.current_events = []

        self.btn_save_log = ttk.Button(form_frame, text="BEJEGYZÉS MENTÉSE (Enter)", command=self.action_save_log)
        self.btn_save_log.pack(pady=15, fill='x', padx=50)

        # --- LEGUTÓBBI NAPLÓK KERET ---
        right_frame = ttk.LabelFrame(paned, text="Legutóbbiak (Dupla kattintás)", padding=10)
        paned.add(right_frame, weight=1)
        self.tree_recent = ttk.Treeview(right_frame, columns=("ID", "D", "P", "A"), show='headings',
                                        displaycolumns=("D", "P", "A"))
        self.tree_recent.heading("D", text="Dátum")
        self.tree_recent.heading("P", text="Projekt")
        self.tree_recent.heading("A", text="Tevékenység")
        self.tree_recent.column("P", width=200)
        self.tree_recent.pack(fill="both", expand=True)
        self.tree_recent.bind("<Double-1>", self._on_log_double_click)

        self.refresh_log_project_list()
        self.refresh_recent_logs()

    def _toggle_travel_frame(self):
        if self.var_is_travel.get():
            self.f_tr_details.pack(fill="x", pady=5)
            self.ent_ev_desc.delete(0, tk.END)
            self.ent_ev_desc.insert(0, "Utazás")
            self.ent_ev_desc.config(state="readonly")
        else:
            self.f_tr_details.pack_forget()
            self.ent_ev_desc.config(state="normal")
            self.ent_ev_desc.delete(0, tk.END)

    def _on_travel_type_change(self, event=None):
        if self.cb_t_type.get() == 'Iroda':
            self.ent_t_start.delete(0, tk.END)
            self.ent_t_start.insert(0, self.db.get_setting('office_start'))
            self.ent_t_end.delete(0, tk.END)
            self.ent_t_end.insert(0, self.db.get_setting('office_end'))
            # Iroda oda-vissza távolság összesen
            dist = float(self.db.get_setting('office_dist') or 0) * 2
            self.ent_t_dist.delete(0, tk.END)
            self.ent_t_dist.insert(0, str(dist))

    def _add_event_to_list(self):
        s_raw, e_raw = self.ent_ev_start.get(), self.ent_ev_end.get()
        is_travel = self.var_is_travel.get()
        desc = self.ent_ev_desc.get()

        if not (s_raw and e_raw and desc):
            messagebox.showwarning("Hiány", "Kérlek töltsd ki az összes esemény mezőt!")
            return

        s = self._format_time_input(s_raw)
        e = self._format_time_input(e_raw)
        if not s or not e:
            messagebox.showerror("Hiba", "Az időt ÓRA:PERC formátumban add meg!")
            return

        ev = {'type': 'Utazás' if self.var_is_travel.get() else 'Munka', 'start': s, 'end': e, 'desc': desc}

        if self.var_is_travel.get():
            ev.update({
                't_type': self.cb_t_type.get(), 't_start': self.ent_t_start.get(),
                't_end': self.ent_t_end.get(), 't_dist': float(self.ent_t_dist.get() or 0),
                't_time': 0, 'is_night': 0  # t_time-ot a recalculate majd kitölti!
            })
            tree_desc = f"Utazás: {ev['t_start']} -> {ev['t_end']} ({ev['t_dist']}km)"
        else:
            ev.update({
                't_type': '', 't_start': '', 't_end': '', 't_dist': 0, 't_time': 0,
                'is_night': 1 if self.var_is_night.get() else 0  # ÉJSZAKAI MUNKA MENTÉSE
            })
            night_flag = "[Éjjel] " if ev['is_night'] else ""
            tree_desc = f"{night_flag}{desc}"

        self.current_events.append(ev)
        self.tree_events.insert("", "end", values=(ev['type'], ev['start'], ev['end'], tree_desc))

        self._recalculate_times(self.current_events, self.ent_l_hours, self.lbl_ev_summary)

        # Alaphelyzet:
        self.ent_ev_start.delete(0, tk.END);
        self.ent_ev_start.insert(0, e)
        self.ent_ev_end.delete(0, tk.END);
        self.ent_ev_desc.delete(0, tk.END)
        self.var_is_night.set(False)  # Éjszaka pipa törlése a következőhöz
        self.ent_ev_end.focus()

    def _delete_event(self):
        sel = self.tree_events.selection()
        if not sel: return
        idx = self.tree_events.index(sel[0])
        self.current_events.pop(idx)
        self.tree_events.delete(sel[0])

        # --- ÚJ: AZONNAL ÚJRASZÁMOL ---
        self._recalculate_times(self.current_events, self.ent_l_hours, self.lbl_ev_summary)

    def _reset_log_fields(self):
        self.txt_l_act.delete(0, tk.END)
        self.txt_l_res.delete("1.0", tk.END)
        self.ent_l_hours.delete(0, tk.END)
        self.ent_l_hours.insert(0, "0")
        self.ent_l_mat.delete(0, tk.END)
        self.ent_l_mat.insert(0, "0")
        self.ent_l_mat_inv.delete(0, tk.END)
        self.ent_l_att.delete(0, tk.END)
        self.current_events = []
        for item in self.tree_events.get_children():
            self.tree_events.delete(item)

        # --- ÚJ: ALAPHELYZETBE ÁLLÍTJA A CÍMKÉT ---
        self.lbl_ev_summary.config(text="Számított idő: 0 óra munka | 0 óra utazás")

    def action_save_log(self):
        raw_date = self.ent_l_date.get()
        formatted_date = self._format_date_input(raw_date)
        if not formatted_date:
            messagebox.showerror("Hiba", "Érvénytelen dátum formátum!")
            return
        self.ent_l_date.delete(0, tk.END)
        self.ent_l_date.insert(0, formatted_date)

        data = {
            'project_code': self.ent_l_proj.get().split(' - ')[
                0] if ' - ' in self.ent_l_proj.get() else self.ent_l_proj.get(),
            'date': formatted_date, 'activity': self.txt_l_act.get().strip(),
            'is_holiday': 1 if self.var_holiday.get() else 0,
            'result': self.txt_l_res.get("1.0", tk.END).strip(),
            'attach_id': self.ent_l_att.get(), 'eng_hours': float(self.ent_l_hours.get() or 0),
            'mat_cost': float(self.ent_l_mat.get() or 0), 'mat_inv': self.ent_l_mat_inv.get().strip()
        }

        success, msg = self.db.insert_log(data, self.current_events)
        if success:
            messagebox.showinfo("Siker", msg)
            self.refresh_recent_logs()
            self._reset_log_fields()
            self.app.notify_project_updated()
        else:
            messagebox.showerror("Hiba", msg)

    # --- FELUGRÓ SZERKESZTŐ (TELJES ESEMÉNY KEZELÉSSEL) ---
    def open_log_details_window(self, log_id, parent_win=None):
        data = self.db.get_log_details(log_id)
        if not data: return

        top = safe_toplevel(parent_win if parent_win else self, f"Napló Szerkesztése - {log_id}", "750x950")

        # Alapadatok frame...
        info_f = ttk.LabelFrame(top, text="Alapadatok", padding=10)
        info_f.pack(fill="x", padx=10, pady=5)
        ent_d = UIFactory.create_label_entry(info_f, "Dátum:", 0, 0, default=data['date'])
        ent_act = UIFactory.create_label_entry(info_f, "Tevékenység:", 1, 0, width=45, default=data['activity'])
        ent_hours = UIFactory.create_label_entry(info_f, "Mérnökóra:", 2, 0, default=str(data['engineer_hours']))
        ent_att = UIFactory.create_label_entry(info_f, "Melléklet ID:", 3, 0, default=data.get('attachment_id') or "")
        var_holiday_edit = tk.BooleanVar(value=bool(data.get('is_holiday', 0)))
        ttk.Checkbutton(info_f, text="Vasárnap / Ünnepnap (+100%)", variable=var_holiday_edit).grid(row=4, column=0,
                                                                                                    sticky="w", padx=5)

        res_f = ttk.LabelFrame(top, text="Eredmény", padding=10)
        res_f.pack(fill="x", padx=10, pady=5)
        txt_r = tk.Text(res_f, width=60, height=5, font=("Courier", 10))
        txt_r.pack(fill="both", expand=True)
        if data.get('result'): txt_r.insert("1.0", data['result'])

        # --- ESEMÉNYEK KEZELÉSE A POPUPBAN ---
        ev_f = ttk.LabelFrame(top, text="Események", padding=10)
        ev_f.pack(fill="both", expand=True, padx=10, pady=5)

        edit_events = data.get('events', [])

        t_frame = ttk.Frame(ev_f)
        t_frame.pack(fill="x", pady=5)
        tree = ttk.Treeview(t_frame, columns=("T", "S", "E", "D"), show='headings', height=4)
        for col, txt in zip(("T", "S", "E", "D"), ("Típus", "Kezd", "Vége", "Részletek")):
            tree.heading(col, text=txt)
        tree.column("T", width=60)
        tree.column("S", width=60)
        tree.column("E", width=60)
        tree.pack(side="left", fill="x", expand=True)
        lbl_edit_sum = ttk.Label(t_frame, text="", font=("Segoe UI", 9, "bold"))
        lbl_edit_sum.pack(side="left", padx=10)

        def redraw_edit_tree():
            for i in tree.get_children(): tree.delete(i)
            for ev in edit_events:
                desc = f"Utazás: {ev['t_start']}->{ev['t_end']} ({ev['t_dist']}km)" if ev['type'] == 'Utazás' else ev[
                    'desc']
                tree.insert("", "end", values=(ev['type'], ev['start'], ev['end'], desc))

            # --- ÚJ: Újraszámol mindent, ha bármi változik az edit_events listában ---
            self._recalculate_times(edit_events, ent_hours, lbl_edit_sum)

        redraw_edit_tree()

        def del_edit_ev():
            sel = tree.selection()
            if sel:
                edit_events.pop(tree.index(sel[0]))
                redraw_edit_tree()

        ttk.Button(t_frame, text="Törlés", command=del_edit_ev).pack(side="right", padx=5)

        # Hozzáadó sáv a popupban
        add_f = ttk.Frame(ev_f)
        add_f.pack(fill="x", pady=5)
        e_st = UIFactory.create_label_entry(add_f, "Kezd:", 0, 0, width=6)
        e_en = UIFactory.create_label_entry(add_f, "Vége:", 0, 2, width=6)
        var_night_edit = tk.BooleanVar()
        ttk.Checkbutton(add_f, text="Éjszakai", variable=var_night_edit).grid(row=0, column=4, padx=5)

        var_tr = tk.BooleanVar()
        tr_box = ttk.Frame(ev_f)

        def tgl_tr():
            if var_tr.get():
                tr_box.pack(fill="x")
                e_ds.delete(0, tk.END)
                e_ds.insert(0, "Utazás")
                e_ds.config(state="readonly")
            else:
                tr_box.pack_forget()
                e_ds.config(state="normal")
                e_ds.delete(0, tk.END)

        ttk.Checkbutton(add_f, text="Utazás", variable=var_tr, command=tgl_tr).grid(row=0, column=5, padx=5)
        e_ds = UIFactory.create_label_entry(add_f, "Leírás:", 0, 6, width=20)

        ttk.Label(tr_box, text="Típus:").grid(row=0, column=0, padx=2)
        cb_tt = ttk.Combobox(tr_box, values=['Magán autó Céges használat', 'Céges autó Magán használat', 'Iroda'],
                             width=20, state="readonly")
        cb_tt.grid(row=0, column=1, padx=2)
        e_ts = UIFactory.create_label_entry(tr_box, "Honnan:", 0, 2, width=12)
        e_te = UIFactory.create_label_entry(tr_box, "Hova:", 0, 4, width=12)
        e_td = UIFactory.create_label_entry(tr_box, "Km:", 0, 6, width=5)

        def auto_iroda(e):
            if cb_tt.get() == 'Iroda':
                e_ts.delete(0, tk.END)
                e_ts.insert(0, self.db.get_setting('office_start'))
                e_te.delete(0, tk.END)
                e_te.insert(0, self.db.get_setting('office_end'))
                e_td.delete(0, tk.END)
                e_td.insert(0, str(float(self.db.get_setting('office_dist') or 0) * 2))

        cb_tt.bind("<<ComboboxSelected>>", auto_iroda)

        def add_edit_ev():
            s = self._format_time_input(e_st.get())
            e = self._format_time_input(e_en.get())
            if not (s and e): return messagebox.showerror("Hiba", "Rossz időformátum!", parent=top)

            ev = {'type': 'Utazás' if var_tr.get() else 'Munka', 'start': s, 'end': e, 'desc': e_ds.get()}
            if var_tr.get():
                ev.update({'t_type': cb_tt.get(), 't_start': e_ts.get(), 't_end': e_te.get(),
                           't_dist': float(e_td.get() or 0)})
            else:
                ev.update({'t_type': '', 't_start': '', 't_end': '', 't_dist': 0, 't_time': 0,
                           'is_night': 1 if var_night_edit.get() else 0})

            edit_events.append(ev)
            redraw_edit_tree()
            e_st.delete(0, tk.END)
            e_st.insert(0, e)
            e_en.delete(0, tk.END)

        ttk.Button(add_f, text="+", command=add_edit_ev).grid(row=0, column=8, padx=5)

        # MENTÉS
        def save_edit():
            fd = self._format_date_input(ent_d.get())
            if not fd: return messagebox.showerror("Hiba", "Érvénytelen dátum!", parent=top)
            data['date'] = fd
            data['engineer_hours'] = float(ent_hours.get() or 0)
            data['attachment_id'] = ent_att.get()
            data['activity'] = ent_act.get().strip()
            data['result'] = txt_r.get("1.0", tk.END).strip()
            data['is_holiday'] = 1 if var_holiday_edit.get() else 0

            # Mat cost is missing from UI but we keep original data dict values or add them later if needed.

            success, msg = self.db.update_log(log_id, data, edit_events)
            if success:
                messagebox.showinfo("Siker", "Mentve!", parent=top)
                self.refresh_recent_logs()
                self.app.notify_project_updated()
                top.destroy()
            else:
                messagebox.showerror("Hiba", msg, parent=top)

        btn_box = ttk.Frame(top)
        btn_box.pack(fill="x", padx=10, pady=20)
        ttk.Button(btn_box, text="Mentés", command=save_edit).pack(side="right")
        top.shortcut_ctrl_s = save_edit

    def refresh_log_project_list(self):
        """Kívülről is hívható lista frissítő. Szép formátum: Kód - Végfelhasználó"""
        projs = [f"{r[0]} - {r[3]}" for r in self.db.get_project_stats()]  # R[0]=Code, R[3]=Description
        self.ent_l_proj.set_completion_list(projs)

    # ==========================================
    # LOGIKA ÉS FUNKCIÓK
    # ==========================================
    def _format_date_input(self, date_str):
        """Okos dátumformázó: 20260101 -> 2026.01.01., 2026-1-5 -> 2026.01.05."""
        date_str = date_str.strip()
        if not date_str: return None

        # Lezáró pont eltávolítása a darabolás előtt
        if date_str.endswith('.'): date_str = date_str[:-1]

        # Kötőjelek és perjelek pontra cserélése
        date_str = date_str.replace('-', '.').replace('/', '.')
        parts = date_str.split('.')

        try:
            if len(parts) == 1 and len(parts[0]) == 8:
                # 20260101 formátum
                y, m, d = parts[0][:4], parts[0][4:6], parts[0][6:]
            elif len(parts) == 3:
                # 2026.1.5 formátum
                y, m, d = parts[0], parts[1], parts[2]
                if len(y) == 2: y = "20" + y  # Ha csak 26-ot írt be
            else:
                return None

            # Vezető nullák hozzáadása
            m = m.zfill(2)
            d = d.zfill(2)

            formatted_date = f"{y}.{m}.{d}."

            # Ellenőrzés, hogy a dátum fizikailag létezik-e (pl. nem február 30.)
            datetime.datetime.strptime(formatted_date, "%Y.%m.%d.")
            return formatted_date
        except ValueError:
            return None

    def _format_time_input(self, time_str):
        time_str = time_str.strip().replace('.', ':').replace('-', ':')
        if not time_str: return None
        try:
            if time_str.isdigit():
                if len(time_str) <= 2: time_str = f"{time_str}:00"
                elif len(time_str) == 3: time_str = f"0{time_str[0]}:{time_str[1:]}"
                elif len(time_str) == 4: time_str = f"{time_str[:2]}:{time_str[2:]}"
            valid_time = datetime.datetime.strptime(time_str, "%H:%M")
            return valid_time.strftime("%H:%M")
        except ValueError:
            return None

    def _recalculate_times(self, events_list, target_entry, summary_label=None):
        w_hours = 0.0
        t_hours = 0.0

        for ev in events_list:
            try:
                s = datetime.datetime.strptime(ev['start'], "%H:%M")
                e = datetime.datetime.strptime(ev['end'], "%H:%M")
                diff = (e - s).total_seconds() / 3600.0
                if diff < 0: diff += 24.0

                if ev['type'] == 'Munka':
                    w_hours += diff
                elif ev['type'] == 'Utazás':
                    t_hours += diff
                    ev['t_time'] = diff  # AZONNAL ELMENTJÜK AZ UTAZÁSI IDŐT A DB SZÁMÁRA!
            except:
                pass

        target_entry.delete(0, tk.END)
        target_entry.insert(0, f"{w_hours:g}")
        if summary_label:
            summary_label.config(text=f"Számított idő: {w_hours:g} óra munka | {t_hours:g} óra utazás")

    def refresh_recent_logs(self):
        """Kívülről is hívható lista frissítő."""
        [self.tree_recent.delete(i) for i in self.tree_recent.get_children()]
        for r in self.db.get_recent_logs(): 
            self.tree_recent.insert("", "end", values=r)

    def _on_log_double_click(self, event):
        sel = self.tree_recent.selection()
        if sel: 
            self.open_log_details_window(self.tree_recent.item(sel[0], "values")[0])

    def shortcut_ctrl_s(self):
        """Ctrl+S hatására elmenti a naplót (hívd meg az itteni mentés gombhoz tartozó függvényt)."""
        self.action_save_log()  # Cseréld ki a pontos függvénynévre, ha nem ez!

    def shortcut_ctrl_n(self):
        """Ctrl+N hatására hozzáad egy új eseményt a listához."""
        self._add_event_to_list()