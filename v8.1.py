import tkinter as tk
from tkinter import ttk

# Helyi modulok importálása a 'core' mappából
from core.database import DatabaseManager
from core.file_manager import FileManager
from core.report_manager import ReportGenerator

# Fülek importálása a 'tabs' mappából
from tabs.project_tab import ProjectTab
from tabs.logs_tab import LogsTab
from tabs.docs_tab import DocsTab
from tabs.report_tab import ReportTab
from tabs.admin_tab import AdminTab
from tabs.contract_tab import ContractTab

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MAR v8.1 - Mérnöki Adminisztrációs Rendszer")
        self.geometry("1500x1080")
        self.eval('tk::PlaceWindow . center')

        # --- Modulok inicializálása és összekötése ---
        self.db = DatabaseManager()
        self.fm = FileManager(self.db)
        self.rg = ReportGenerator(self.db, self.fm)

        self._setup_ui()
        self._setup_bindings()

    def _setup_bindings(self):
        # 1. Escape bezárja a felugró (Toplevel) ablakokat
        self.bind_all("<Escape>", self._on_escape)

        # 2. Globális intelligens egérgörgő (bárhol van az egér, azt görgeti)
        self.bind_all("<MouseWheel>", self._on_mousewheel)  # Windows / OSX
        self.bind_all("<Button-4>", self._on_mousewheel)  # Linux fel
        self.bind_all("<Button-5>", self._on_mousewheel)  # Linux le

        # 3. Globális Ctrl+S és Ctrl+N továbbító
        self.bind_all("<Control-s>", self._on_ctrl_s)
        self.bind_all("<Control-S>", self._on_ctrl_s)
        self.bind_all("<Control-n>", self._on_ctrl_n)
        self.bind_all("<Control-N>", self._on_ctrl_n)

    def _on_escape(self, event):
        widget = event.widget
        if isinstance(widget, tk.Tk): return  # A főalkalmazást ne zárja be
        try:
            toplevel = widget.winfo_toplevel()
            if toplevel != self:
                toplevel.destroy()
        except:
            pass

    def _on_mousewheel(self, event):
        try:
            widget = self.winfo_containing(event.x_root, event.y_root)
            if not widget: return

            # Megkeressük a legközelebbi görgethető Canvas-t a kurzor alatt
            parent = widget
            while parent:
                if isinstance(parent, tk.Canvas):
                    if event.num == 5 or event.delta < 0:
                        parent.yview_scroll(1, "units")
                    elif event.num == 4 or event.delta > 0:
                        parent.yview_scroll(-1, "units")
                    break
                parent = self.nametowidget(parent.winfo_parent()) if parent.winfo_parent() else None
        except Exception:
            pass

    def _on_ctrl_s(self, event):
        focus_widget = self.focus_get()
        if not focus_widget: return

        # Megnézzük, hogy melyik ablakban van a kurzor/fókusz
        toplevel = focus_widget.winfo_toplevel()

        if toplevel != self:
            # Ha egy felugró ablakban vagyunk, és van mentés funkciója, futtatjuk!
            if hasattr(toplevel, 'shortcut_ctrl_s'):
                toplevel.shortcut_ctrl_s()
            return "break"  # Megállítjuk a parancs továbbterjedését!

        # Ha a főablakban vagyunk, a nyitott fül mentését futtatjuk
        current_tab_id = self.notebook.select()
        if current_tab_id:
            current_tab = self.nametowidget(current_tab_id)
            if hasattr(current_tab, 'shortcut_ctrl_s'):
                current_tab.shortcut_ctrl_s()
        return "break"

    def _on_ctrl_n(self, event):
        focus_widget = self.focus_get()
        if not focus_widget: return

        toplevel = focus_widget.winfo_toplevel()
        if toplevel != self:
            if hasattr(toplevel, 'shortcut_ctrl_n'):
                toplevel.shortcut_ctrl_n()
            return "break"

        current_tab_id = self.notebook.select()
        if current_tab_id:
            current_tab = self.nametowidget(current_tab_id)
            if hasattr(current_tab, 'shortcut_ctrl_n'):
                current_tab.shortcut_ctrl_n()
        return "break"

    def _setup_ui(self):
        """A fő füles felület (Notebook) felépítése."""
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Fülek példányosítása (átadjuk magát a fő App-ot 'self'-ként)
        self.tab_contract = ContractTab(self.notebook, self)
        self.tab_project = ProjectTab(self.notebook, self)
        self.tab_logs = LogsTab(self.notebook, self)
        self.tab_report = ReportTab(self.notebook, self)
        self.tab_admin = AdminTab(self.notebook, self)
        self.tab_docs = DocsTab(self.notebook, self)

        # Fülek hozzáadása a notebookhoz
        self.notebook.add(self.tab_logs, text="Napi Jegyzőkönyv")
        self.notebook.add(self.tab_docs, text="Dokumentum Kezelő")
        self.notebook.add(self.tab_project, text="Projekt Kezelés")
        self.notebook.add(self.tab_report, text="Elszámolási Jegyzőkönyv")
        self.notebook.add(self.tab_contract, text="Szerződések és Ajánlatok")
        self.notebook.add(self.tab_admin, text="Rendszer")

    # ==========================================
    # KÖZÖS KOMMUNIKÁCIÓS METÓDUSOK A FÜLEK KÖZÖTT
    # ==========================================
    
    def notify_project_updated(self):
        """
        Ezt hívják a fülek, ha frissíteni kell a projekt listákat mindenhol.
        """
        self.tab_project.refresh_project_list()
        self.tab_logs.refresh_log_project_list()
        self.tab_docs.refresh_doc_project_list()
        self.tab_contract.refresh_data()

    def open_log_editor(self, log_id, parent_win=None):
        """
        A napló szerkesztő megnyitása (pl. a Projekt fülről is elérhető).
        Delegálja a hívást a LogsTab felé.
        """
        self.tab_logs.open_log_details_window(log_id, parent_win)

if __name__ == "__main__":
    app = App()
    app.mainloop()
