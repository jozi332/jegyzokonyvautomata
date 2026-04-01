import os
import re
import shutil
import datetime
import sqlite3


def regexp_match(pattern, text):
    """Python funkció az SQLite REGEXP kényszeréhez (adószám ellenőrzéshez)."""
    if text is None:
        return 0
    return 1 if re.search(pattern, text) else 0


class DatabaseManager:
    def __init__(self):
        self.db_dir = 'data'
        if not os.path.exists(self.db_dir):
            os.makedirs(self.db_dir)

        self.db_path = os.path.join(self.db_dir, 'engineering_admin_v8.1.db')
        self.conn = sqlite3.connect(self.db_path)

        # Betanítjuk az SQLite-ot a REGEXP használatára
        self.conn.create_function("REGEXP", 2, regexp_match)

        # Idegen kulcsok bekapcsolása (CASCADE nélkül, szigorú kapcsolatok)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.c = self.conn.cursor()

        self.create_tables()

    def create_tables(self):
        # 1. Clients (Partnerek) - Adószám, Email és Bankszámla ellenőrzés
        # Using r'''...''' (raw strings) to prevent Python escape sequence warnings
        self.c.execute(r'''CREATE TABLE IF NOT EXISTS clients (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            name TEXT UNIQUE,
                            address TEXT DEFAULT '', 
                            tax_number TEXT DEFAULT '' CHECK(tax_number = '' OR tax_number REGEXP '^[0-9]{8}-[0-9]-[0-9]{2}$'), 
                            email TEXT DEFAULT '' CHECK(email = '' OR email REGEXP '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'), 
                            phone TEXT DEFAULT '',
                            bank_account TEXT DEFAULT '' CHECK(bank_account = '' OR bank_account REGEXP '^[0-9]{8}-[0-9]{8}(-[0-9]{8})?$')
                          )''')

        # 2. Contracts tábla frissítése (Túlóra küszöbérték hozzáadva)
        self.c.execute(r'''CREATE TABLE IF NOT EXISTS contracts (
                            contract_code TEXT PRIMARY KEY,
                            client_id INTEGER NOT NULL,
                            contract_type TEXT DEFAULT 'Keretszerződés',
                            fee_type TEXT DEFAULT 'Óradíj',
                            fee_amount REAL DEFAULT 0,
                            currency TEXT DEFAULT 'HUF',
                            mult_overtime REAL DEFAULT 50,
                            mult_overtime_threshold REAL DEFAULT 8,
                            mult_overtime_check_interval_amount REAL DEFAULT 1,
                            mult_overtime_check_interval_type TEXT DEFAULT 'Napi',
                            mult_over_border_eu REAL DEFAULT 40,
                            mult_over_border_3rd REAL DEFAULT 60,
                            mult_weekend REAL DEFAULT 50,
                            mult_holiday REAL DEFAULT 100,
                            mult_night REAL DEFAULT 25,
                            standby_fee REAL DEFAULT 0,
                            travel_bp REAL DEFAULT 7000,
                            travel_km REAL DEFAULT 250,
                            start_date TEXT CHECK(start_date IS NULL OR start_date = '' OR start_date REGEXP '^[0-9]{4}[.-][0-9]{2}[.-][0-9]{2}\.?$'),
                            end_date TEXT DEFAULT 'Határozatlan' CHECK(end_date = 'Határozatlan' OR end_date = '' OR end_date REGEXP '^[0-9]{4}[.-][0-9]{2}[.-][0-9]{2}\.?$'),
                            contact_name TEXT,
                            contact_role TEXT,
                            contact_phone TEXT,
                            tech_content TEXT,
                            warranty_terms TEXT,
                            penalty_terms TEXT,
                            billing_terms TEXT,
                            other_terms TEXT,
                            FOREIGN KEY(client_id) REFERENCES clients(id)
                          )''')

        # 3. Projects (Projektek) - Dátum ellenőrzés
        self.c.execute(r'''CREATE TABLE IF NOT EXISTS projects (
                            project_code TEXT PRIMARY KEY, 
                            end_client_id INTEGER NOT NULL, 
                            description TEXT, 
                            contract_code TEXT NOT NULL,
                            start_date TEXT CHECK(start_date IS NULL OR start_date = '' OR start_date REGEXP '^[0-9]{4}[.-][0-9]{2}[.-][0-9]{2}\.?$'), 
                            status TEXT DEFAULT 'Active', 
                            completion_date TEXT CHECK(completion_date IS NULL OR completion_date = '' OR completion_date REGEXP '^[0-9]{4}[.-][0-9]{2}[.-][0-9]{2}\.?$'),
                            project_type TEXT DEFAULT 'Normál',
                            client_ref TEXT DEFAULT '',
                            FOREIGN KEY(end_client_id) REFERENCES clients(id),
                            FOREIGN KEY(contract_code) REFERENCES contracts(contract_code)
                          )''')

        # 4. Daily Logs tábla frissítése (Ünnepnap flag)
        self.c.execute(r'''CREATE TABLE IF NOT EXISTS daily_logs (
                            log_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            project_code TEXT NOT NULL, 
                            date TEXT CHECK(date IS NULL OR date = '' OR date REGEXP '^[0-9]{4}[.-][0-9]{2}[.-][0-9]{2}\.?$'), 
                            is_holiday INTEGER DEFAULT 0,
                            activity TEXT,
                            result TEXT, 
                            attachment_id TEXT, 
                            engineer_hours REAL, 
                            material_cost REAL, 
                            material_invoice_number TEXT,
                            FOREIGN KEY(project_code) REFERENCES projects(project_code)
                          )''')

        # 5. Daily Events tábla frissítése (Éjszaka flag és Utazási idő)
        self.c.execute(r'''CREATE TABLE IF NOT EXISTS daily_events (
                            event_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            log_id INTEGER NOT NULL, 
                            event_type TEXT,
                            is_night INTEGER DEFAULT 0,
                            start_time TEXT CHECK(start_time IS NULL OR start_time = '' OR start_time REGEXP '^([01][0-9]|2[0-3]):[0-5][0-9]$'), 
                            end_time TEXT CHECK(end_time IS NULL OR end_time = '' OR end_time REGEXP '^([01][0-9]|2[0-3]):[0-5][0-9]$'), 
                            event_description TEXT,
                            travel_type TEXT,
                            tr_start_loc TEXT,
                            tr_end_loc TEXT,
                            tr_dist REAL,
                            tr_time REAL DEFAULT 0,
                            FOREIGN KEY(log_id) REFERENCES daily_logs(log_id)
                          )''')

        # 6. Quotes (Ajánlatok) - Dátum ellenőrzés
        self.c.execute(r'''CREATE TABLE IF NOT EXISTS quotes (
                            quote_code TEXT PRIMARY KEY,
                            client_id INTEGER NOT NULL,
                            issue_date TEXT CHECK(issue_date IS NULL OR issue_date = '' OR issue_date REGEXP '^[0-9]{4}[.-][0-9]{2}[.-][0-9]{2}\.?$'),
                            valid_until TEXT CHECK(valid_until IS NULL OR valid_until = '' OR valid_until REGEXP '^[0-9]{4}[.-][0-9]{2}[.-][0-9]{2}\.?$'),
                            description TEXT,
                            total_amount REAL,
                            currency TEXT DEFAULT 'HUF',
                            status TEXT DEFAULT 'Nyitott',
                            FOREIGN KEY(client_id) REFERENCES clients(id)
                          )''')

        # 7. Documents (Dokumentumok) - Dátum ellenőrzés
        self.c.execute(r'''CREATE TABLE IF NOT EXISTS documents (
                            doc_id TEXT PRIMARY KEY, 
                            project_code TEXT, 
                            title TEXT, 
                            content TEXT, 
                            created_date TEXT CHECK(created_date IS NULL OR created_date = '' OR created_date REGEXP '^[0-9]{4}[.-][0-9]{2}[.-][0-9]{2}\.?$'),
                            FOREIGN KEY(project_code) REFERENCES projects(project_code)
                          )''')

        # 8. Settings (Beállítások)
        self.c.execute(r'''CREATE TABLE IF NOT EXISTS settings (
                            key TEXT PRIMARY KEY, 
                            value TEXT
                          )''')

        self.conn.commit()
        self._init_defaults()

    def _init_defaults(self):
        defaults = {
            'company_name': 'Wéber József EV', 'company_address': '1163 Budapest, Vámosgyörk utca 9.',
            'company_tax': '69917882-1-42', 'office_start': 'Ecser', 'office_end': 'Budapest',
            'office_dist': '30', 'office_rate': '250', 'office_time': '1', 'office_cost': '7000'
        }
        for k, v in defaults.items():
            self.c.execute("INSERT OR IGNORE INTO settings VALUES (?, ?)", (k, v))
        self.conn.commit()

    def get_setting(self, key):
        self.c.execute("SELECT value FROM settings WHERE key=?", (key,))
        res = self.c.fetchone()
        return res[0] if res else ""

    def update_setting(self, key, value):
        self.c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_all_clients(self):
        self.c.execute("SELECT name FROM clients ORDER BY name")
        return [row[0] for row in self.c.fetchall()]

    def get_client(self, name):
        self.c.execute("SELECT * FROM clients WHERE name=?", (name,))
        row = self.c.fetchone()
        if not row: return None
        cols = [desc[0] for desc in self.c.description]
        return dict(zip(cols, row))

    def add_client_full(self, data):
        try:
            self.c.execute('''INSERT INTO clients (name, address, tax_number, email, phone, bank_account) 
                              VALUES (?, ?, ?, ?, ?, ?)''',
                           (data['name'], data.get('address', ''), data.get('tax_number', ''),
                            data.get('email', ''), data.get('phone', ''), data.get('bank_account', '')))
            self.conn.commit()
            return True, "Partner hozzáadva."
        except sqlite3.IntegrityError as e:
            # Ha a regex elkap egy hibát, vagy a név már létezik
            return False, f"Nem sikerült menteni!\nOka: Létező név, vagy hibás formátum (Adószám/Email/Bankszámla).\n\nRendszerüzenet: {e}"

    def update_client_full(self, old_name, data):
        try:
            self.c.execute('''UPDATE clients SET name=?, address=?, tax_number=?, email=?, phone=?, bank_account=? 
                              WHERE name=?''',
                           (data['name'], data.get('address', ''), data.get('tax_number', ''),
                            data.get('email', ''), data.get('phone', ''), data.get('bank_account', ''), old_name))
            self.conn.commit()
            return True, "Partner frissítve."
        except sqlite3.IntegrityError as e:
            return False, f"Nem sikerült menteni!\nOka: Létező név, vagy hibás formátum (Adószám/Email/Bankszámla).\n\nRendszerüzenet: {e}"

    def delete_client(self, name):
        self.c.execute("DELETE FROM clients WHERE name=?", (name,))
        self.conn.commit()

    def generate_next_code(self, prefix_type):
        """
        Univerzális kód generátor.
        prefix_type lehet: 'A' (Ajánlat), 'S' (Szerződés), 'WJP' (Projekt)
        Várt kimenet: A26001, S26001, WJP26001
        """

        current_year = datetime.date.today().strftime("%y")
        full_prefix = f"{prefix_type}{current_year}"

        table = "projects"
        column = "project_code"

        if prefix_type == 'A':
            table = "quotes"
            column = "quote_code"
        elif prefix_type == 'S':
            table = "contracts"
            column = "contract_code"

        try:
            self.c.execute(f"SELECT {column} FROM {table} WHERE {column} LIKE ? ORDER BY {column} DESC LIMIT 1",
                       (f"{full_prefix}%",))
            result = self.c.fetchone()
            new_seq = 1
            if result:
                # Az utolsó 3 karaktert számmá alakítjuk
                new_seq = int(result[0][-3:]) + 1
            return f"{full_prefix}{new_seq:03d}"
        except Exception as e:
            print(f"Hiba a kód generálásakor: {e}")
            return f"{full_prefix}000"

    def get_framework_contracts(self):
        self.c.execute(
            "SELECT project_code, client, description FROM projects WHERE project_type='Keretszerződés' ORDER BY project_code DESC")
        return self.c.fetchall()

    # ==========================================
    # PROJEKTEK (PROJECTS) KEZELÉSE (v8.1)
    # ==========================================
    def get_project_stats(self):
        """Visszaadja a projektek listáját a Treeview számára. (Kód, Típus, Megr.Hiv., Leírás, Óra)"""
        self.c.execute('''
            SELECT p.project_code, p.project_type, p.client_ref, p.description, COALESCE(SUM(l.engineer_hours), 0)
            FROM projects p
            LEFT JOIN daily_logs l ON p.project_code = l.project_code
            GROUP BY p.project_code
            ORDER BY p.project_code DESC
        ''')
        return self.c.fetchall()

    def get_project_data(self, project_code):
        """Lekéri egy projekt minden adatát, és hozzácsapja a Végfelhasználó (end_client) nevét is."""
        self.c.execute('''
            SELECT p.*, cl.name as end_client_name 
            FROM projects p
            JOIN clients cl ON p.end_client_id = cl.id
            WHERE p.project_code=?
        ''', (project_code,))
        row = self.c.fetchone()
        if not row: return None
        cols = [desc[0] for desc in self.c.description]
        return dict(zip(cols, row))

    def insert_project(self, data):
        try:
            self.c.execute('''INSERT INTO projects 
                              (project_code, end_client_id, description, contract_code, start_date, status, completion_date, project_type, client_ref)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (data['code'], data['end_client_id'], data['desc'], data['contract_code'], data['start'],
                            data['status'], "", data.get('type', 'Normál'), data.get('client_ref', '')))
            self.conn.commit()
            return True, "Projekt létrehozva."
        except sqlite3.IntegrityError as e:
            return False, f"Hiba a mentéskor (Hiányzó kötelező adat vagy létező kód):\n{e}"

    def update_project(self, data):
        self.c.execute("SELECT status FROM projects WHERE project_code=?", (data['code'],))
        row = self.c.fetchone()
        old_status = row[0] if row else ""
        comp_date = ""

        if data['status'] == 'Completed' and old_status != 'Completed':
            comp_date = datetime.date.today().strftime("%Y.%m.%d.")
        elif data['status'] == 'Active':
            comp_date = ""
        else:
            self.c.execute("SELECT completion_date FROM projects WHERE project_code=?", (data['code'],))
            r = self.c.fetchone()
            comp_date = r[0] if r else ""

        try:
            self.c.execute('''UPDATE projects 
                              SET end_client_id=?, description=?, contract_code=?, start_date=?, status=?, completion_date=?, 
                                  project_type=?, client_ref=?
                              WHERE project_code=?''',
                           (data['end_client_id'], data['desc'], data['contract_code'], data['start'],
                            data['status'], comp_date,
                            data.get('type', 'Normál'), data.get('client_ref', ''), data['code']))
            self.conn.commit()
            return True, "Projekt frissítve."
        except sqlite3.IntegrityError as e:
            return False, f"Hiba a frissítéskor:\n{e}"

    def get_recent_logs(self, limit=20):
        """Visszaadja a legutóbbi naplókat Projekt Kód + Név formázással."""
        self.c.execute('''
            SELECT l.log_id, l.date, p.project_code || ' - ' || cl.name, l.activity 
            FROM daily_logs l
            JOIN projects p ON l.project_code = p.project_code
            JOIN clients cl ON p.end_client_id = cl.id
            ORDER BY l.log_id DESC LIMIT ?
        ''', (limit,))
        return self.c.fetchall()

    def get_log_details(self, log_id):
        self.c.execute("SELECT * FROM daily_logs WHERE log_id=?", (log_id,))
        log_row = self.c.fetchone()
        if not log_row: return None
        columns = [desc[0] for desc in self.c.description]
        log_dict = dict(zip(columns, log_row))

        # Lekérjük az összes eseményt időrendben, szótárak listájaként
        self.c.execute('''SELECT event_type as type, start_time as start, end_time as end, event_description as desc, 
                                 travel_type as t_type, tr_start_loc as t_start, tr_end_loc as t_end, tr_dist as t_dist 
                          FROM daily_events WHERE log_id=? ORDER BY start_time''', (log_id,))
        ev_cols = [desc[0] for desc in self.c.description]
        log_dict['events'] = [dict(zip(ev_cols, row)) for row in self.c.fetchall()]
        return log_dict

    def insert_log(self, data, events=None):
        try:
            self.c.execute("SELECT project_code FROM projects WHERE project_code=?", (data['project_code'],))
            if not self.c.fetchone(): return False, "A megadott projekt nem létezik!"

            attach_id = data.get('attach_id', '').strip()
            if not attach_id:
                self.c.execute("SELECT COUNT(*) FROM daily_logs WHERE project_code=?", (data['project_code'],))
                count = self.c.fetchone()[0]
                attach_id = f"J{re.sub(r'\D', '', data['project_code'])}/{count + 1}"

            # ÚJ: is_holiday mentése
            self.c.execute('''INSERT INTO daily_logs 
                              (project_code, date, is_holiday, activity, result, attachment_id, engineer_hours, material_cost, material_invoice_number) 
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (data['project_code'], data['date'], data.get('is_holiday', 0), data['activity'], data['result'], attach_id,
                            data['eng_hours'], data['mat_cost'], data.get('mat_inv', '')))
            log_id = self.c.lastrowid

            if events:
                for ev in events:
                    # ÚJ: is_night és tr_time mentése
                    self.c.execute('''INSERT INTO daily_events 
                                      (log_id, event_type, is_night, start_time, end_time, event_description, travel_type, tr_start_loc, tr_end_loc, tr_dist, tr_time) 
                                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                   (log_id, ev['type'], ev.get('is_night', 0), ev['start'], ev['end'], ev['desc'],
                                    ev.get('t_type', ''), ev.get('t_start', ''), ev.get('t_end', ''),
                                    ev.get('t_dist', 0), ev.get('t_time', 0)))
            self.conn.commit()
            return True, "Bejegyzés mentve."
        except Exception as e:
            return False, f"Adatbázis hiba: {e}"

    def update_log(self, log_id, data, events=None):
        try:
            # ÚJ: is_holiday frissítése
            self.c.execute('''UPDATE daily_logs 
                              SET date=?, is_holiday=?, activity=?, result=?, attachment_id=?, engineer_hours=?, material_cost=?, material_invoice_number=? 
                              WHERE log_id=?''',
                           (data['date'], data.get('is_holiday', 0), data['activity'], data['result'], data['attachment_id'],
                            data['engineer_hours'], data['material_cost'], data.get('mat_inv', ''), log_id))

            self.c.execute("DELETE FROM daily_events WHERE log_id=?", (log_id,))
            if events:
                for ev in events:
                    # ÚJ: is_night és tr_time mentése
                    self.c.execute('''INSERT INTO daily_events 
                                      (log_id, event_type, is_night, start_time, end_time, event_description, travel_type, tr_start_loc, tr_end_loc, tr_dist, tr_time) 
                                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                   (log_id, ev['type'], ev.get('is_night', 0), ev['start'], ev['end'], ev['desc'],
                                    ev.get('t_type', ''), ev.get('t_start', ''), ev.get('t_end', ''),
                                    ev.get('t_dist', 0), ev.get('t_time', 0)))
            self.conn.commit()
            return True, "Bejegyzés frissítve."
        except Exception as e:
            return False, f"Adatbázis hiba: {e}"

    def get_daily_logs(self, project_code):
        self.c.execute("SELECT * FROM daily_logs WHERE project_code=? ORDER BY date DESC", (project_code,))
        columns = [desc[0] for desc in self.c.description]
        return [dict(zip(columns, row)) for row in self.c.fetchall()]

    def get_monthly_logs(self, year, month):
        pattern = f"{year}.{month:02d}.%"
        self.c.execute("SELECT * FROM daily_logs WHERE date LIKE ? ORDER BY date ASC", (pattern,))
        columns = [desc[0] for desc in self.c.description]
        return [dict(zip(columns, row)) for row in self.c.fetchall()]

    def get_framework_settlement_data(self, framework_code):
        fw_data = self.get_project_data(framework_code)
        if not fw_data: return None, []

        self.c.execute('''
            SELECT p.project_code, p.description, l.date, l.activity, l.engineer_hours, l.material_cost, l.travel_cost
            FROM daily_logs l
            JOIN projects p ON l.project_code = p.project_code
            WHERE p.project_code = ? OR p.parent_code = ?
            ORDER BY l.date ASC
        ''', (framework_code, framework_code))

        columns = [desc[0] for desc in self.c.description]
        logs = [dict(zip(columns, row)) for row in self.c.fetchall()]
        return fw_data, logs

    def get_documents(self, project_code):
        self.c.execute(
            "SELECT doc_id, title, created_date FROM documents WHERE project_code=? ORDER BY created_date DESC",
            (project_code,))
        return self.c.fetchall()

    def get_document_content(self, doc_id):
        self.c.execute("SELECT * FROM documents WHERE doc_id=?", (doc_id,))
        row = self.c.fetchone()
        if not row: return None
        cols = [desc[0] for desc in self.c.description]
        return dict(zip(cols, row))

    def save_document(self, data):
        try:
            self.c.execute(
                "INSERT OR REPLACE INTO documents (doc_id, project_code, title, content, created_date) VALUES (?, ?, ?, ?, ?)",
                (data['doc_id'], data['project_code'], data['title'], data['content'], data['created_date']))
            self.conn.commit()
            return True, "Dokumentum mentve."
        except Exception as e:
            return False, str(e)

    def delete_document(self, doc_id):
        self.c.execute("DELETE FROM documents WHERE doc_id=?", (doc_id,))
        self.conn.commit()

    def archive_database(self):
        archive_dir = 'ARCHIVE'
        if not os.path.exists(archive_dir): os.makedirs(archive_dir)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        backup_db = os.path.join(archive_dir, f'engineering_admin_backup_{timestamp}.db')
        try:
            shutil.copyfile(self.db_path, backup_db)
            self.c.execute('DELETE FROM projects')
            self.c.execute('DELETE FROM clients')
            self.conn.commit()
            return True, f"Teljes adatbázis archiválva ide:\n{backup_db}\n\nAz aktív rendszer kiürítve."
        except Exception as e:
            return False, str(e)

    def backup_database(self):
        archive_dir = 'ARCHIVE'
        if not os.path.exists(archive_dir): os.makedirs(archive_dir)
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        backup_db = os.path.join(archive_dir, f'engineering_admin_backup_ONLY_{timestamp}.db')
        try:
            shutil.copyfile(self.db_path, backup_db)
            return True, f"Biztonsági mentés elkészült ide:\n{backup_db}"
        except Exception as e:
            return False, str(e)

    # ==========================================
    # SZERZŐDÉSEK ÉS AJÁNLATOK KEZELÉSE (v8.1 Client_ID logikával)
    # ==========================================
    def get_all_contracts(self):
        """Visszaadja a szerződéseket és ajánlatokat is, 'Cégnév (Kapcsolattartó)' formátumban!"""
        self.c.execute('''
            SELECT c.contract_code, cl.name, c.contact_name, c.contract_type 
            FROM contracts c
            JOIN clients cl ON c.client_id = cl.id
            UNION ALL
            SELECT q.quote_code, cl.name, '', 'Ajánlat'
            FROM quotes q
            JOIN clients cl ON q.client_id = cl.id
            ORDER BY 1 DESC
        ''')
        results = []
        for row in self.c.fetchall():
            code, c_name, contact, c_type = row
            # Ha van beállítva kapcsolattartó ember, zárójelben hozzáfűzzük a céghez
            display_name = f"{c_name} ({contact})" if contact and contact.strip() else c_name
            results.append((code, display_name, c_type))
        return results

    def get_contract_data(self, contract_code):
        self.c.execute('''
            SELECT c.*, cl.name as client_name 
            FROM contracts c
            JOIN clients cl ON c.client_id = cl.id
            WHERE c.contract_code=?
        ''', (contract_code,))
        row = self.c.fetchone()
        if not row: return None
        cols = [desc[0] for desc in self.c.description]
        return dict(zip(cols, row))

    def get_quote_data(self, quote_code):
        self.c.execute('''
            SELECT q.*, cl.name as client_name 
            FROM quotes q
            JOIN clients cl ON q.client_id = cl.id
            WHERE q.quote_code=?
        ''', (quote_code,))
        row = self.c.fetchone()
        if not row: return None
        cols = [desc[0] for desc in self.c.description]
        return dict(zip(cols, row))

    def insert_contract(self, data):
        try:
            cols = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            sql = f"INSERT INTO contracts ({cols}) VALUES ({placeholders})"
            self.c.execute(sql, tuple(data.values()))
            self.conn.commit()
            return True, "Szerződés elmentve."
        except sqlite3.IntegrityError as e:
            return False, f"Adatbázis hiba mentéskor: {e}"

    def update_contract(self, data):
        try:
            set_clause = ', '.join([f"{k}=?" for k in data.keys() if k != 'contract_code'])
            values = [v for k, v in data.items() if k != 'contract_code']
            values.append(data['contract_code'])
            sql = f"UPDATE contracts SET {set_clause} WHERE contract_code=?"
            self.c.execute(sql, tuple(values))
            self.conn.commit()
            return True, "Szerződés sikeresen frissítve."
        except sqlite3.IntegrityError as e:
            return False, f"Adatbázis hiba frissítéskor: {e}"

    def insert_quote(self, data):
        try:
            cols = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            sql = f"INSERT INTO quotes ({cols}) VALUES ({placeholders})"
            self.c.execute(sql, tuple(data.values()))
            self.conn.commit()
            return True, "Ajánlat elmentve."
        except sqlite3.IntegrityError as e:
            return False, f"Adatbázis hiba mentéskor: {e}"

    def update_quote(self, data):
        try:
            set_clause = ', '.join([f"{k}=?" for k in data.keys() if k != 'quote_code'])
            values = [v for k, v in data.items() if k != 'quote_code']
            values.append(data['quote_code'])
            sql = f"UPDATE quotes SET {set_clause} WHERE quote_code=?"
            self.c.execute(sql, tuple(values))
            self.conn.commit()
            return True, "Ajánlat sikeresen frissítve."
        except sqlite3.IntegrityError as e:
            return False, f"Adatbázis hiba frissítéskor: {e}"

    # ==========================================
    # v8.1 CSV IMPORT / EXPORT ÉS ADATELLENŐRZÉS
    # ==========================================

    def get_all_table_names(self):
        """Visszaadja az összes létező tábla nevét (rendszertáblák kivételével)."""
        self.c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in self.c.fetchall() if r[0] != 'sqlite_sequence']
        return sorted(tables)

    def get_table_schema(self, table_name):
        """Visszaadja a tábla oszlopainak nevét és típusát szótárként."""
        self.c.execute(f"PRAGMA table_info({table_name})")
        return {row[1]: row[2] for row in self.c.fetchall()}

    def validate_import_row(self, table_name, row_dict):
        """
        Ellenőriz egyetlen adatsort a séma és speciális szabályok alapján.
        Visszatér: (is_valid, error_list)
        """
        schema = self.get_table_schema(table_name)
        errors = []

        for col, val in row_dict.items():
            if col not in schema:
                continue

            val_str = str(val).strip()
            if not val_str:
                continue  # Üres értéket átengedünk, kivéve ha PK lenne, de azt az SQLite lekezeli

            db_type = schema[col].upper()

            # 1. Szám ellenőrzés (REAL, INTEGER)
            if 'REAL' in db_type or 'INT' in db_type:
                try:
                    # Tisztítás: szóközök (ezres elválasztó) és magyar tizedesvessző eltávolítása
                    clean_val = val_str.replace(',', '.').replace(' ', '')
                    float(clean_val)
                except ValueError:
                    errors.append(f"{col}: Nem érvényes szám")

            # 2. Idő formátum ellenőrzés (CSAK a tényleges óra/perc oszlopoknál)
            if col in ['start_time', 'end_time'] and val_str:
                if not re.match(r'^\d{1,2}:\d{2}$', val_str):
                    errors.append(f"{col}: Hibás időformátum (ÓÓ:PP)")

            # 3. Dátum formátum ellenőrzés (ha a mező nevében benne van a 'date')
            if 'date' in col.lower() and val_str:
                # Elfogadunk YYYY.MM.DD. vagy YYYY-MM-DD formátumot
                if not re.match(r'^\d{4}[\.\-]\d{2}[\.\-]\d{2}\.?$', val_str):
                    errors.append(f"{col}: Hibás dátum (YYYY.MM.DD. vagy YYYY-MM-DD)")

        return len(errors) == 0, ", ".join(errors)

    def bulk_import_data(self, table_name, data_list):
        """A megtisztított és validált adatok dinamikus feltöltése az adatbázisba."""
        if not data_list:
            return False, "Nincs importálható adat."

        schema = self.get_table_schema(table_name)
        # Csak azokat az oszlopokat vesszük figyelembe, amik léteznek a táblában
        valid_cols = [c for c in data_list[0].keys() if c in schema]

        if not valid_cols:
            return False, "A CSV nem tartalmaz egyező oszlopokat a táblához."

        placeholders = ", ".join(["?"] * len(valid_cols))
        col_names = ", ".join(valid_cols)

        # REPLACE, hogy ha létező azonosító van, felülírja, ha új, létrehozza
        sql = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"

        try:
            for row in data_list:
                values = []
                for c in valid_cols:
                    val = row.get(c, "")
                    # Kicseréljük a magyar tizedesvesszőket és a szóközös ezres elválasztókat
                    if isinstance(val, str):
                        if 'REAL' in schema[c].upper():
                            val = val.replace(',', '.').replace(' ', '')
                        elif 'INT' in schema[c].upper():
                            val = val.replace(' ', '')
                    values.append(val)
                self.c.execute(sql, tuple(values))

            self.conn.commit()
            return True, f"Sikeresen importálva: {len(data_list)} sor a(z) '{table_name}' táblába."
        except Exception as e:
            return False, f"SQL Hiba az importálás során: {str(e)}"