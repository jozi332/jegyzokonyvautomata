import os
import re
import shutil


class FileManager:
    def __init__(self, db_manager):
        # Az adatbázis hivatkozása szükséges a szülő-gyermek kapcsolatok lekérdezéséhez
        self.db = db_manager

        self.base_dir = 'PROJECTS'
        self.inbox_dir = 'INBOX'
        self.archive_dir = 'ARCHIVE'

        # Alapkönyvtárak létrehozása
        for d in [self.base_dir, self.inbox_dir, self.archive_dir]:
            if not os.path.exists(d):
                os.makedirs(d)

    def _sanitize(self, text):
        """Biztonságos mappanév generálása a partnernevekből (illegális karakterek cseréje)."""
        if not text:
            return "Ismeretlen_Partner"
        # Tiltott OS karakterek cseréje alulvonásra
        return re.sub(r'[<>:"/\\|?*]', '_', text).strip()

    def get_project_base_dir(self, code):
        """Kiszámolja a gyökérmappát az Ajánlat -> Szerződés -> Projekt hierarchia alapján."""
        # 1. ESET: Ajánlat (A)
        if code.startswith('A'):
            try:
                self.db.c.execute("SELECT client FROM quotes WHERE quote_code=?", (code,))
                row = self.db.c.fetchone()
                client_name = self._sanitize(row[0] if row else 'Ismeretlen_Partner')
            except:
                client_name = 'Ismeretlen_Partner'
            final_path = os.path.join(self.base_dir, f"{code}_{client_name}")

        # 2. ESET: Szerződés (S)
        elif code.startswith('S'):
            c_data = self.db.get_contract_data(code)
            client_name = self._sanitize(c_data.get('client', 'Ismeretlen_Partner') if c_data else 'Ismeretlen_Partner')
            final_path = os.path.join(self.base_dir, f"{code}_{client_name}")

        # 3. ESET: Projekt (WJP)
        else:
            p_data = self.db.get_project_data(code)
            if not p_data:
                final_path = os.path.join(self.base_dir, code)
            else:
                client_name = self._sanitize(p_data.get('client', 'Ismeretlen_Partner'))
                contract_code = p_data.get('contract', '')

                # Ha van Szerződés szülője, akkor a Szerződés mappájába (almappaként) kerül
                if contract_code:
                    parent_dir = self.get_project_base_dir(contract_code)
                    final_path = os.path.join(parent_dir, f"{code}_{client_name}")
                else:
                    # Ha önálló projekt (nincs szerződéshez kötve)
                    final_path = os.path.join(self.base_dir, f"{code}_{client_name}")

        # BIZTOSÍTÉK: Ha lekérjük a projekt mappát, garantáljuk, hogy fizikailag létezik is!
        os.makedirs(final_path, exist_ok=True)
        return final_path

    def ensure_project_dirs(self, code):
        """Létrehozza a kód típusának megfelelő almappákat, ha még nem léteznek."""
        base_dir = self.get_project_base_dir(code)
        subdirs = []

        if code.startswith('A'):
            subdirs = ["01_A_Ajanlatok"]
        elif code.startswith('S'):
            subdirs = ["01_S_Szerzodesek", "98_Elszamolas_osszesitok"]
        else:
            subdirs = ["02_J_Napi_JegyzoKonyvek", "03_M_Munkalapok", "04_D_Dokumentumok"]

        # Mappák fizikai létrehozása
        for d in subdirs:
            path = os.path.join(base_dir, d)
            os.makedirs(path, exist_ok=True)

        return base_dir

    def get_export_dir(self, code, doc_type):
        """
        Visszaadja a megfelelő almappát a fájlok PDF generálásához / csatolásához.
        """
        # Biztosítjuk, hogy létezzenek a mappák
        self.ensure_project_dirs(code)
        base_dir = self.get_project_base_dir(code)
        target_dir = base_dir

        if doc_type == 'Munkalap':
            target_dir = os.path.join(base_dir, "03_M_Munkalapok")
        elif doc_type == 'JegyzoKonyv':
            target_dir = os.path.join(base_dir, "02_J_Napi_JegyzoKonyvek")
        elif doc_type == 'Dokumentum':
            target_dir = os.path.join(base_dir, "04_D_Dokumentumok")
        elif doc_type == 'Osszesito':
            target_dir = os.path.join(base_dir, "98_Elszamolas_osszesitok")
        elif doc_type == 'Ajanlat':
            target_dir = os.path.join(base_dir, "01_A_Ajanlatok")
        elif doc_type == 'Szerzodes':
            target_dir = os.path.join(base_dir, "01_S_Szerzodesek")

        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    def organize_inbox(self):
        """Az INBOX mappa automatikus rendezése a megfelelő projekt/szerződés mappákba."""
        count = 0
        for filename in os.listdir(self.inbox_dir):
            # Kiszedjük a fájlnévből a kódot pl: WJP26001_valami.pdf -> WJP26001
            match = re.search(r'([A-Za-z]{1,4})(\d{4,5})', filename)
            if match:
                prefix = match.group(1).upper()
                num = match.group(2)
                code = f"{prefix}{num}"

                # Ellenőrizzük, hogy létezik-e az adatbázisban
                exists = False
                if prefix == 'A':
                    try:
                        self.db.c.execute("SELECT 1 FROM quotes WHERE quote_code=?", (code,))
                        exists = self.db.c.fetchone() is not None
                    except:
                        pass
                elif prefix == 'S':
                    exists = self.db.get_contract_data(code) is not None
                elif prefix == 'WJP':
                    exists = self.db.get_project_data(code) is not None

                if exists:
                    # Intelligens almappa választás a fájlnév alapján
                    doc_type = 'Dokumentum'
                    lower_name = filename.lower()
                    if 'munkalap' in lower_name: doc_type = 'Munkalap'
                    elif 'jegyzo' in lower_name or 'jegyző' in lower_name: doc_type = 'JegyzoKonyv'
                    elif 'osszesito' in lower_name or 'összesítő' in lower_name: doc_type = 'Osszesito'
                    elif 'ajanlat' in lower_name or 'ajánlat' in lower_name: doc_type = 'Ajanlat'
                    elif 'szerzodes' in lower_name or 'szerződés' in lower_name: doc_type = 'Szerzodes'

                    target_dir = self.get_export_dir(code, doc_type)

                    try:
                        shutil.move(os.path.join(self.inbox_dir, filename), os.path.join(target_dir, filename))
                        count += 1
                    except Exception as e:
                        print(f"Hiba a fájl mozgatásakor ({filename}): {e}")

        return f"{count} fájl áthelyezve az INBOX-ból a megfelelő mappákba."