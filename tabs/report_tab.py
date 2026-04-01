import tkinter as tk
from tkinter import ttk, messagebox
import datetime

from core.ui_components import AutocompleteCombobox, UIFactory


class ReportTab(ttk.Frame):
    def __init__(self, parent, app_context):
        super().__init__(parent)
        self.app = app_context
        self.db = self.app.db
        self.rg = self.app.rg

        self._build_ui()
        # Frissítjük a szerződéseket, ha átkattintanak erre a fülre
        self.bind("<Visibility>", lambda e: self.refresh_data())

    def _build_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        # --- EOJ ÉS TIG KERET ---
        f_szerz = ttk.LabelFrame(main_frame, text="Szerződés Elszámolás (EOJ) és Teljesítés Igazolás (TIG)", padding=20)
        f_szerz.pack(fill="x", pady=10)

        ttk.Label(f_szerz, text="Szerződés:").grid(row=0, column=0, sticky="w", pady=5)
        self.cb_contract = AutocompleteCombobox(f_szerz, width=40)
        self.cb_contract.grid(row=0, column=1, sticky="w", pady=5, padx=10)

        self.ent_s_start = UIFactory.create_label_entry(f_szerz, "Kezdő dátum:", 1,
                                                        default=datetime.date.today().replace(day=1).strftime(
                                                            "%Y.%m.%d."))
        self.ent_s_end = UIFactory.create_label_entry(f_szerz, "Záró dátum:", 2,
                                                      default=datetime.date.today().strftime("%Y.%m.%d."))

        btn_frame = ttk.Frame(f_szerz)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

        # Két külön gomb a két dokumentumnak
        ttk.Button(btn_frame, text="EOJ Generálása és Megnyitása", command=lambda: self.generate_contract('EOJ')).pack(
            side="left", padx=10)
        ttk.Button(btn_frame, text="TIG Generálása és Megnyitása", command=lambda: self.generate_contract('TIG')).pack(
            side="left", padx=10)

        self.refresh_data()

    def refresh_data(self):
        contracts = [f"{c[0]} - {c[1]}" for c in self.db.get_all_contracts() if c[2] != 'Ajánlat']
        self.cb_contract.set_completion_list(contracts)

    def generate_contract(self, target):
        contract_str = self.cb_contract.get()
        if not contract_str:
            messagebox.showwarning("Hiba", "Kérlek válassz egy szerződést a listából!")
            return
        contract_code = contract_str.split(' - ')[0]
        start_d = self.ent_s_start.get().strip()
        end_d = self.ent_s_end.get().strip()

        if not start_d or not end_d:
            messagebox.showwarning("Hiba", "Kérlek add meg a kezdő és záró dátumokat!")
            return

        res = self.rg.generate_contract_settlement(contract_code, start_d, end_d)
        if res[0]:
            success, eoj_path, ti_path = res
            if target == 'EOJ':
                self.rg.open_pdf(eoj_path)
            else:
                self.rg.open_pdf(ti_path)
        else:
            messagebox.showerror("Hiba", res[1])