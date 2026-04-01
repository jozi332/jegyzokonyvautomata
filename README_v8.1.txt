Technical State Summary - Engineering Admin (Jegyzőkönyv Automata) v8.1
Project Goal & Tech Stack

A Python-based desktop application utilizing Tkinter (GUI), SQLite3 (RDBMS), and ReportLab (PDF generation) to automate engineering administration, financial calculations, and the generation of standardized PDF documents (Worksheets, Protocols, Contract Settlements, and Certificates of Performance).
File Structure
Plaintext

JegyzokonyvAutomata/
├── v8.1.py                        # Main entry point, initializes App and UI Tabs
├── assets/
│   ├── CourierNew.ttf             # Core font (Normal/Italic)
│   └── CourierNew-Bold.ttf        # Core font (Bold/BoldItalic) for Hungarian char support
├── core/                          # Backend & Business Logic
│   ├── database.py                # SQLite3 DB Manager, regex validations, CRUD ops
│   ├── file_manager.py            # Directory creation and filename sanitization
│   ├── pdf_engine.py              # PDFEngineBase: fonts, styles, headers, NumberedCanvas
│   ├── pdf_templates.py           # PDFGenerator: visual layouts (Worksheet, Protocol, EOJ, TIG)
│   ├── report_manager.py          # ReportGenerator: Financial Engine and PDF orchestration
│   └── ui_components.py           # Reusable Tkinter widgets (Autocomplete, UIFactory)
├── data/
│   └── engineering_admin_v8.1.db  # SQLite database file
├── tabs/                          # Frontend GUI Modules
│   ├── admin_tab.py               # Application settings and DB management
│   ├── contract_tab.py            # Contracts, Quotes, and financial multipliers
│   ├── docs_tab.py                # Markdown document editor
│   ├── logs_tab.py                # Daily logs and events input (Work/Travel times)
│   ├── project_tab.py             # Project management and "Smart Close" actions
│   └── report_tab.py              # EOJ and TIG generation interface
└── PROJECTS/                      # --- GENERATED FILES STRUCTURE ---
    ├── WJP26001_AAAAAAAAAAAAAA/   # Project specific directory
    │   ├── Munkalap_WJP26001.pdf
    │   ├── JegyzoKonyv_J26001_1.pdf
    │   ├── Teljes_Projekt_WJP26001.pdf
    │   └── D26001_1_mellekletek/  # Document attachments subfolder
    │       └── Dokumentum_D26001_1_Cim.pdf
    └── SZ24002_Control_Pro/       # Contract specific directory
        └── 98_Elszamolas_osszesitok/
            ├── Elszamolasi_Jegyzkonyv_SZ24002_20260101.pdf (EOJ)
            └── Teljesites_Igazolas_SZ24002_20260101.pdf    (TIG)

Data Contracts & IO

1. Database Schema (engineering_admin_v8.1.db)
    clients: id (PK), name (UNIQUE), address, tax_number, email, phone, bank_account. (Used dually as Contracting Party and End-User).
    contracts: contract_code (PK), client_id (FK), contract_type, fee_type, fee_amount, currency, mult_overtime, mult_overtime_threshold, mult_weekend, mult_holiday, mult_night, standby_fee, travel_bp, travel_km, start_date, end_date, contact_name, contact_role, contact_phone, tech_content, warranty_terms, penalty_terms, billing_terms.
    projects: project_code (PK), end_client_id (FK), description, contract_code (FK), start_date, status (Active/Completed), project_type, client_ref.
    daily_logs: log_id (PK), project_code (FK), date, is_holiday (INT 0/1), activity, result, attachment_id, engineer_hours, material_cost, material_invoice_number.
    daily_events: event_id (PK), log_id (FK), event_type (Munka/Utazás), is_night (INT 0/1), start_time, end_time, event_description, travel_type, tr_start_loc, tr_end_loc, tr_dist, tr_time.
    quotes & documents & settings: Standard data persistence tables.
    
2. Financial Engine IO (report_manager.py -> _calculate_log_financials)
INPUT:
    log (dict): A complete row from daily_logs JOINED with a list of daily_events dicts.
    contract (dict): A complete row from contracts defining the financial rules.

OUTPUT (Dictionary passed to PDF Templates):
    work_fee (float): Total calculated work fee including all multipliers.
    travel_fee (float): Total calculated travel fee (Fixed BP or KM-based).
    mat_cost (float), total_cost (float).
    time_summary (list): Formatted [[start, end, description], ...] for PDF tables.
    travel_calc_str (str), travel_type_str (str), total_tr_dist (float), total_tr_time (float).
    TIG Specific Breakdown: base_fee_total, overtime_fee_total, night_fee_total, weekend_fee_total, holiday_fee_total (all floats).
    Hours Breakdown: w_hours, overtime_hours, night_hours, weekend_hours, holiday_hours (all floats).

Key Constraints

1. Library & Environment Restrictions
    Built-in only: Rely exclusively on standard Python libraries (os, datetime, re, sqlite3, subprocess) where possible.
    External Dependencies: reportlab (Strictly used for all PDF generation).
    No SQLAlchemy/ORMs: Direct parameterized SQL queries via sqlite3 are strictly enforced.

2. Architectural & Business Rules
    DRY PDF Generation: core.pdf_templates.PDFGenerator MUST inherit from core.pdf_engine.PDFEngineBase. Redundant SimpleDocTemplate setups are abstracted into _get_doc and _build_doc helpers.
    Dual-Client Architecture: projects utilize end_client_id (Location of work/End-user printed on Worksheets/Protocols), while contracts utilize client_id (Contracting/Paying party printed on EOJ/TIG).
    Financial Multipliers Calculation:
        Overtime triggers automatically when total engineer_hours > mult_overtime_threshold.
        Night shifts are calculated on a per-event basis via the is_night boolean flag.
        Weekends (Saturday = +50%) are calculated automatically via datetime.weekday().
        Holidays/Sundays (+100%) are driven by the is_holiday boolean flag on the daily log level.
    Smart Date Formatting: All dates input as YYYYMMDD or YYYY-M-D MUST be formatted to strict YYYY.MM.DD. before DB insertion via _format_date_input.

3. Typography & Formatting Rules
    ReportLab Font Family: To support Hungarian glyphs (ő, ű) alongside HTML tags (<b>, <i>), CourierNew.ttf and CourierNew-Bold.ttf MUST be explicitly mapped using reportlab.pdfbase.pdfmetrics.registerFontFamily. Fallbacks to default fonts will break character encoding.
    Currency Formatting: All financial outputs in the PDF must be formatted with thousand separators and the "Ft" suffix using: f"{int(value):,} Ft".replace(',', ' ') (e.g., 1 500 000 Ft).

4. File Naming Conventions & Output Paths
    Prefixes: WJP (Project), S (Contract), A (Quote), M (Munkalap, swapped from WJP), J (Protocol).
    Directories: Generated via file_manager.py._sanitize().
    Filenames:
        Worksheet: Munkalap_{project_code}.pdf
        Protocol: JegyzoKonyv_{protocol_id}.pdf
        Full Project: Teljes_Projekt_{project_code}.pdf
        EOJ: Elszamolasi_Jegyzkonyv_{contract_code}_{YYYYMMDD}.pdf
        TIG: Teljesites_Igazolas_{contract_code}_{YYYYMMDD}.pdf
