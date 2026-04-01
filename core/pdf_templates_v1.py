import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from core.pdf_engine import PDFEngineBase, NumberedCanvas, MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM, BG_TITLE, BG_H1, BG_H2, BG_H3


class PDFGenerator(PDFEngineBase):
    """
    Ez az osztály felel a konkrét dokumentumok (Munkalap, Jegyzőkönyv, Összesítő)
    összeállításáért az alapmotor stílusait felhasználva.
    """
    def __init__(self, output_dir="output"):
        super().__init__() # <--- Ez hívja meg a pdf_engine.py _register_font() metódusát!
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def set_company_data(self, name, address, tax):
        """Allows the main app to override hardcoded company info."""
        self.company_header[0] = f"{name}; {address}; Adószám: {tax}"

    def _create_styles(self):
        s = StyleSheet1()
        s.add(ParagraphStyle(name='Normal', fontName=self.font_main, fontSize=11, leading=12, textColor=colors.black,
                             spaceAfter=4))
        s.add(ParagraphStyle(name='Table_H', parent=s['Normal'], fontSize=10, alignment=TA_CENTER))
        s.add(ParagraphStyle(name='Table_C', parent=s['Normal'], fontSize=10, alignment=TA_LEFT))
        s.add(ParagraphStyle(name='Table_C_Center', parent=s['Normal'], fontSize=10, alignment=TA_CENTER))

        # --- HEADER STYLES ---
        s.add(ParagraphStyle(name='HT_Title', parent=s['Normal'], fontSize=20, leading=24, spaceBefore=0, spaceAfter=6,
                             keepWithNext=True))
        s.add(ParagraphStyle(name='HT_Subtitle', parent=s['Normal'], fontSize=11, leading=13, spaceBefore=0,
                             spaceAfter=12))
        s.add(ParagraphStyle(name='HT_H1', parent=s['Normal'], fontSize=16, leading=20, spaceBefore=12, spaceAfter=6,
                             keepWithNext=True))
        s.add(ParagraphStyle(name='HT_H2', parent=s['Normal'], fontSize=15, leading=18, spaceBefore=0, spaceAfter=6))
        s.add(ParagraphStyle(name='HT_H3', parent=s['Normal'], fontSize=14, leading=17,
                             textColor=colors.HexColor('#434343'), spaceBefore=10, spaceAfter=4, keepWithNext=True))
        # Dokumentum stílusok
        s.add(ParagraphStyle(name='HT_Bullet', parent=s['Normal'], leftIndent=20, bulletIndent=10, spaceAfter=2))
        s.add(ParagraphStyle(
            name='HT_Code',
            fontName='Courier',  # Direkt a csúnyább alap Courier a kódhoz
            fontSize=9,
            leading=10,
            textColor=colors.HexColor('#202020'),
            backColor=colors.HexColor('#FDFDFD'),
            borderPadding=5,
            spaceBefore=5,
            spaceAfter=5
        ))
        s.add(ParagraphStyle(name='HT_DocTitle', parent=s['HT_Title'], alignment=TA_CENTER, spaceAfter=20))

        return s

    def _header_footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(self.font_main, 9)

        # HEADER
        y = A4[1] - 1.5 * cm
        canvas.drawString(2 * cm, y, self.company_header[0])
        y -= 0.5 * cm
        canvas.drawString(2 * cm, y, self.company_header[1])
        y -= 0.2 * cm
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, y, A4[0] - 2 * cm, y)

        # FOOTER
        y_foot = 1.5 * cm
        canvas.drawString(2 * cm, y_foot,
                          "Bankszámlaszám: 11600006-00000000-84606132       Nyilvántartási szám: 53873051")
        canvas.restoreState()

    def _fmt(self, text, color=None, bold=False):
        res = str(text)
        if bold: res = f"<b>{res}</b>"
        if color: res = f'<font backColor="{color}">{res}</font>'
        return res

    # --- Építőelem Helper Metódusok ---

    def _build_munkalap_elements(self, data, rows):
        elems = []
        title_text = self._fmt("Munkalap", color=BG_TITLE)
        elems.append(Paragraph(title_text, self.styles['HT_Title']))

        subtitle_text = self._fmt(f"Munkalap sorszáma: M{data.get('iW_num', '')}", color=BG_TITLE)
        elems.append(Paragraph(subtitle_text, self.styles['HT_Subtitle']))

        elems.append(Paragraph("Projekt megrendelői hivatkozás:", self.styles['Normal']))
        elems.append(Paragraph(data.get('sOrder_link', ''), self.styles['Normal']))
        elems.append(Paragraph(f"Szerződés sorszáma: S{data.get('iContract_num', '')}", self.styles['Normal']))
        elems.append(Paragraph(f"Munka leírása (dokumentum azonosítója): D{data.get('iW_num', '')}", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph(f"Munkalap nyitás:          {data.get('dStart_date', '')}", self.styles['Normal']))
        elems.append(Paragraph(f"Munkalap zárás:           {data.get('dClose_date', '')}", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph("Mérnökóra:", self.styles['Normal']))
        elems.append(Paragraph(self._fmt(f"{data.get('iOW_time', '')}", bold=True), self.styles['Normal']))

        elems.append(Paragraph("Utazási idő:", self.styles['Normal']))
        elems.append(Paragraph(self._fmt(f"{data.get('iOT_time', '')}", bold=True), self.styles['Normal']))

        elems.append(Paragraph("Költség:", self.styles['Normal']))
        elems.append(Paragraph(self._fmt(f"{data.get('iOO_Fee', '')}", bold=True), self.styles['Normal']))

        elems.append(Paragraph("Munkát elvégezte: Wéber József", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        h1_text = self._fmt("Jegyzőkönyv és tevékenység lista", color=BG_H1)
        elems.append(Paragraph(h1_text, self.styles['HT_H1']))
        elems.append(Spacer(1, 0.2 * cm))

        headers = ["Dátum", "Tevékenység", "M. idő\n(ó)", "U. idő\n(ó)", "Költség", "Melléklet"]
        t_data = [[Paragraph(self._fmt(h, bold=True), self.styles['Table_H']) for h in headers]]

        for r in rows:
            row_cells = [
                Paragraph(str(r[0]), self.styles['Table_C_Center']),
                Paragraph(str(r[1]), self.styles['Table_C_Center']),
                Paragraph(str(r[3]), self.styles['Table_C_Center']),
                Paragraph(str(r[4]), self.styles['Table_C_Center']),
                Paragraph(str(r[5]), self.styles['Table_C_Center']),
                Paragraph(str(r[6]), self.styles['Table_C_Center']),
            ]
            t_data.append(row_cells)

        t = Table(t_data, colWidths=[3.0 * cm, 6.0 * cm, 1.5 * cm, 1.5 * cm, 2.5 * cm, 2.6 * cm], repeatRows=1)
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 2.0, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elems.append(t)

        elems.append(Spacer(1, 1 * cm))
        elems.append(Paragraph("Munkát átvette:", self.styles['Normal']))
        elems.append(Spacer(1, 1 * cm))
        elems.append(Paragraph("Aláírása: .......................................", self.styles['Normal']))

        return elems

    def _build_jegyzokonyv_elements(self, data):
        elems = []
        s_indent1 = ParagraphStyle('Indent1', parent=self.styles['Normal'], leftIndent=1.5 * cm)
        s_indent2 = ParagraphStyle('Indent2', parent=self.styles['Normal'], leftIndent=3.0 * cm)
        s_right = ParagraphStyle('Right', parent=self.styles['Normal'], alignment=TA_RIGHT)

        id_text = self._fmt(data.get('iW_num', ''), color=BG_H2)
        elems.append(Paragraph(id_text, self.styles['HT_H2']))

        elems.append(Paragraph(data.get('sW_type', ''), self.styles['Normal']))
        elems.append(Paragraph(f"Helyszín: {data.get('aW_address', '')}", self.styles['Normal']))
        elems.append(Paragraph(f"Megrendelői hivatkozás: {data.get('sOrder_link', '')}", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        h3_text = self._fmt("Idő összefoglaló", color=BG_H3)
        elems.append(Paragraph(h3_text, self.styles['HT_H3']))
        elems.append(Paragraph(
            f"Dátum: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {data.get('dDate', '')}",
            self.styles['Normal']))

        events = data.get('ssTime_summary', [])
        if isinstance(events, list) and len(events) > 0:
            time_table_data = []
            for ev in events:
                if len(ev) == 3:
                    time_table_data.append([
                        Paragraph(str(ev[0]), self.styles['Normal']),
                        Paragraph("-", self.styles['Normal']),
                        Paragraph(str(ev[1]), self.styles['Normal']),
                        Paragraph(str(ev[2]), self.styles['Normal'])
                    ])
                else:
                    time_table_data.append([Paragraph(str(ev[0]), self.styles['Normal']), "", "", ""])

            t_time = Table(time_table_data, colWidths=[1.5 * cm, 0.5 * cm, 1.5 * cm, 12 * cm], hAlign='LEFT')
            t_time.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            elems.append(t_time)

        travel_type = data.get('sNat_of_usage', '')
        t_fee = str(data.get('iTravel_fee', '0')).replace(" ", "")

        is_ho = travel_type in ['Nincs utazás (HO)', 'Nincs (HO)', 'Nincs']
        has_travel_fee = t_fee not in ["", "0", "0Ft", "0 Ft"]

        if not is_ho:
            elems.append(
                Paragraph(f"Kiszállási díj: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{data.get('sLicense_plate', '')}",
                          s_indent1))
            elems.append(Paragraph(f"{travel_type}:", s_indent1))

            if travel_type != 'Iroda':
                elems.append(Paragraph(
                    f"{data.get('iDepart_dist', '')} km ({data.get('sDepart_towns', '')} - {data.get('sArriv_towns', '')})",
                    s_indent2))
                elems.append(Paragraph(
                    f"{data.get('iArriv_dist', '')} km ({data.get('sArriv_towns', '')} - {data.get('sDepart_towns', '')})",
                    s_indent2))

                elems.append(Paragraph("Forintosított:", s_indent1))
                elems.append(Paragraph(f"{data.get('sCalc_of_fee', '')}", s_indent2))
            else:
                elems.append(Paragraph(f"Fix költség: {data.get('sCalc_of_fee', '')}", s_indent2))

        elems.append(Spacer(1, 0.5 * cm))

        mini_data = []
        mini_data.append([Paragraph("Utazási idő:", self.styles['Normal']), "",
                          Paragraph(f"{data.get('iT_time', '')} óra", s_right)])

        if not is_ho and has_travel_fee:
            mini_data.append(
                [Paragraph("Kiszállási díj:", s_indent1), Paragraph(f"{data.get('iTravel_fee', '')}", s_right), ""])

        mini_data.append(
            [Paragraph("Munkaidő:", self.styles['Normal']), "", Paragraph(f"{data.get('iW_time', '')} óra", s_right)])
        mini_data.append([
            Paragraph(self._fmt("Összesen:", bold=True), self.styles['Normal']),
            Paragraph(self._fmt(f"{data.get('iO_fee', '')}", bold=True) if not is_ho else "", s_right),
            Paragraph(self._fmt(f"{data.get('iO_time', '')}", bold=True), s_right)
        ])

        t_mini = Table(mini_data, colWidths=[5 * cm, 3 * cm, 3 * cm], hAlign='LEFT')
        t_mini.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        elems.append(t_mini)
        elems.append(Spacer(1, 0.5 * cm))

        desc_h_text = self._fmt("Elvégzett tevékenységek", color=BG_H3)
        elems.append(Paragraph(desc_h_text, self.styles['HT_H3']))
        desc = data.get('ssW_desc', '').replace('\n', '<br/>')
        elems.append(Paragraph(desc, self.styles['Normal']))

        return elems

    # --- Publikus Fájl Generáló Metódusok ---

    def create_work(self, filename, data, rows):
        doc = SimpleDocTemplate(os.path.join(self.output_dir, filename), pagesize=A4, topMargin=MARGIN_TOP,
                                bottomMargin=MARGIN_BOTTOM, leftMargin=MARGIN_X, rightMargin=MARGIN_X)
        elems = self._build_munkalap_elements(data, rows)
        doc.build(elems, onFirstPage=self._header_footer, onLaterPages=self._header_footer, canvasmaker=NumberedCanvas)
        return os.path.join(self.output_dir, filename)

    def create_merge(self, filename, data):
        doc = SimpleDocTemplate(os.path.join(self.output_dir, filename), pagesize=A4,
                                topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
                                leftMargin=MARGIN_X, rightMargin=MARGIN_X)
        elems = self._build_jegyzokonyv_elements(data)
        doc.build(elems, onFirstPage=self._header_footer, onLaterPages=self._header_footer, canvasmaker=NumberedCanvas)
        return os.path.join(self.output_dir, filename)

    def create_full_report(self, filename, data, rows, logs_data):
        doc = SimpleDocTemplate(os.path.join(self.output_dir, filename), pagesize=A4,
                                topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
                                leftMargin=MARGIN_X, rightMargin=MARGIN_X)
        elems = self._build_munkalap_elements(data, rows)
        elems.append(PageBreak())
        s_center = ParagraphStyle(name='CenterTitle', parent=self.styles['HT_Title'], alignment=TA_LEFT)
        elems.append(Paragraph(self._fmt("Mellékletek", color=BG_TITLE), s_center))

        for j_data in logs_data:
            elems.append(PageBreak())
            elems.extend(self._build_jegyzokonyv_elements(j_data))

        doc.build(elems, onFirstPage=self._header_footer, onLaterPages=self._header_footer, canvasmaker=NumberedCanvas)
        return os.path.join(self.output_dir, filename)

    def create_monthly_report(self, filename, year, month, rows):
        doc = SimpleDocTemplate(os.path.join(self.output_dir, filename), pagesize=A4, topMargin=MARGIN_TOP,
                                bottomMargin=MARGIN_BOTTOM, leftMargin=MARGIN_X, rightMargin=MARGIN_X)
        elems = []
        title_text = self._fmt(f"Havi Összesítő - {year}.{month:02d}", color=BG_TITLE)
        elems.append(Paragraph(title_text, self.styles['HT_Title']))
        elems.append(Spacer(1, 0.5 * cm))

        headers = ["Dátum", "Projekt", "Tevékenység", "Óra"]
        t_data = [[Paragraph(self._fmt(h, bold=True), self.styles['Table_H']) for h in headers]]

        total_hours = 0
        for r in rows:
            total_hours += float(r[3])
            t_data.append([
                Paragraph(str(r[0]), self.styles['Table_C_Center']),
                Paragraph(str(r[1]), self.styles['Table_C_Center']),
                Paragraph(str(r[2]), self.styles['Table_C']),
                Paragraph(str(r[3]), self.styles['Table_C_Center']),
            ])

        t_data.append([
            Paragraph(self._fmt("ÖSSZESEN", bold=True), self.styles['Table_H']), "", "",
            Paragraph(self._fmt(f"{total_hours:g}", bold=True), self.styles['Table_C_Center'])
        ])

        t = Table(t_data, colWidths=[3 * cm, 3 * cm, 8.5 * cm, 2.5 * cm], repeatRows=1)
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('SPAN', (0, -1), (2, -1)),
        ]))
        elems.append(t)

        doc.build(elems, onFirstPage=self._header_footer, onLaterPages=self._header_footer, canvasmaker=NumberedCanvas)
        return os.path.join(self.output_dir, filename)

    def create_contract_report(self, filename, c_data, rows):
        """Szerződés Elszámolási Jegyzőkönyv vizuális felépítése (EOJ Formátum)."""
        doc = SimpleDocTemplate(os.path.join(self.output_dir, filename), pagesize=A4, topMargin=MARGIN_TOP,
                                bottomMargin=MARGIN_BOTTOM, leftMargin=MARGIN_X, rightMargin=MARGIN_X)
        elems = []

        # --- OLDAL 1: FEDŐLAP ---
        title_text = self._fmt("Elszámolási összesített jegyzőkönyv", color=BG_TITLE)
        elems.append(Paragraph(title_text, self.styles['HT_Title']))

        elems.append(Paragraph(f"Sorszáma: {c_data.get('sEOJ_num', '')}", self.styles['Normal']))
        elems.append(Paragraph(f"Szerződés sorszáma: {c_data.get('contract_code', '')}", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph(f"Elszámolás nyitás: {c_data.get('dStart', '')}", self.styles['Normal']))
        elems.append(Paragraph(f"Elszámolás zárás: {c_data.get('dEnd', '')}", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph("Elszámolni kívánt összeg összesen az elszámolási időszakban:", self.styles['Normal']))
        elems.append(Paragraph(self._fmt(c_data.get('iTotal_fee', ''), bold=True), self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph("Ebből:", self.styles['Normal']))
        elems.append(Spacer(1, 0.2 * cm))

        s_indent = ParagraphStyle('Indent', parent=self.styles['Normal'], leftIndent=1.0 * cm)
        elems.append(Paragraph(f"Korábbi elszámolás záró összege: 0 Ft", s_indent))
        elems.append(Paragraph(f"Elvégzett mérnökóra: {self._fmt(c_data.get('iW_time_sum', ''), bold=True)}", s_indent))
        elems.append(Paragraph(f"Utazási idő: {self._fmt(c_data.get('iT_time_sum', ''), bold=True)}", s_indent))
        elems.append(
            Paragraph(f"Költség (Utazás + Anyag): {self._fmt(c_data.get('iCost_sum', ''), bold=True)}", s_indent))
        elems.append(Spacer(1, 1.5 * cm))

        elems.append(Paragraph("Munkát elvégezte: Wéber József", self.styles['Normal']))
        elems.append(Spacer(1, 1.5 * cm))
        elems.append(Paragraph("Aláírás: .......................................", self.styles['Normal']))

        # --- OLDAL 2: TEVÉKENYSÉG LISTA ---
        elems.append(PageBreak())

        h1_text = self._fmt("Tevékenység lista", color=BG_H1)
        elems.append(Paragraph(h1_text, self.styles['HT_H1']))
        elems.append(Spacer(1, 0.5 * cm))

        # 8 Oszlopos fejléc
        headers = ["Dátum", "Munkalap", "Hivatkozás", "M. idő", "U. idő", "Költség", "Melléklet", "Túlóra"]
        t_data = [[Paragraph(self._fmt(h, bold=True), self.styles['Table_H']) for h in headers]]

        s_small = ParagraphStyle('Small', parent=self.styles['Table_C_Center'], fontSize=8, leading=9)
        s_small_left = ParagraphStyle('SmallL', parent=self.styles['Table_C'], fontSize=8, leading=9)

        # Sorok dinamikus feltöltése
        for r in rows:
            t_data.append([
                Paragraph(str(r[0]), s_small),  # Dátum
                Paragraph(str(r[1]), s_small),  # Munkalap
                Paragraph(str(r[2]), s_small_left),  # Hivatkozás (balra zárt, mert hosszú lehet)
                Paragraph(str(r[3]), s_small),  # M.idő
                Paragraph(str(r[4]), s_small),  # U.idő
                Paragraph(str(r[5]), s_small),  # Költség
                Paragraph(str(r[6]), s_small),  # Melléklet
                Paragraph(str(r[7]), s_small),  # Túlóra
            ])

        # Dinamikus táblázat rajzolása
        t = Table(t_data, colWidths=[2.2 * cm, 1.8 * cm, 3.8 * cm, 1.2 * cm, 1.2 * cm, 2.3 * cm, 3.0 * cm, 1.5 * cm],
                  repeatRows=1)
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        elems.append(t)

        doc.build(elems, onFirstPage=self._header_footer, onLaterPages=self._header_footer, canvasmaker=NumberedCanvas)
        return os.path.join(self.output_dir, filename)

    # --- Publikus Fájl Generáló Metódusok ---

    def create_document(self, filename, doc_data, project_data):
        """Rich Text (Markdown) dokumentum generálása PDF-be."""
        doc = SimpleDocTemplate(os.path.join(self.output_dir, filename), pagesize=A4,
                                topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
                                leftMargin=MARGIN_X, rightMargin=MARGIN_X)
        elems = []

        # 1. Fejléc adatok
        elems.append(Paragraph(self._fmt(doc_data['doc_id'], color=BG_H2), self.styles['HT_H2']))

        # JAVÍTVA: A v8.1-ben a project_data már egy szótár (dict)!
        p_code = project_data.get('project_code', '')
        c_name = project_data.get('end_client_name', 'Ismeretlen Megrendelő')
        elems.append(Paragraph(f"Projekt: {p_code} - {c_name}", self.styles['Normal']))

        elems.append(Paragraph(f"Létrehozva: {doc_data['created_date']}", self.styles['Normal']))
        elems.append(Spacer(1, 1 * cm))

        # Fő Cím
        elems.append(Paragraph(self._fmt(doc_data['title'], color=BG_TITLE), self.styles['HT_DocTitle']))

        # 2. Markdown Parser (Marad a régi, jól működő logika)
        content = doc_data['content'].split('\n')

        in_code_block = False
        code_lines = []
        in_table = False
        table_rows = []

        for line in content:
            raw_line = line.strip()

            # --- Kód blokk kezelése ( ``` ) ---
            if raw_line.startswith('```'):
                if in_code_block:
                    code_text = "<br/>".join(code_lines).replace(' ', '&nbsp;')
                    elems.append(Paragraph(code_text, self.styles['HT_Code']))
                    in_code_block = False
                    code_lines = []
                else:
                    in_code_block = True
                continue

            if in_code_block:
                code_lines.append(line)
                continue

            # --- Táblázat kezelése ( | Oszlop | ) ---
            if raw_line.startswith('|') and raw_line.endswith('|'):
                in_table = True
                cells = [cell.strip() for cell in raw_line.split('|') if cell.strip()]
                row_data = [Paragraph(self._fmt(c), self.styles['Table_C']) for c in cells]
                if row_data:
                    table_rows.append(row_data)
                continue
            elif in_table:
                if table_rows:
                    col_width = (A4[0] - MARGIN_X * 2) / len(table_rows[0])
                    t = Table(table_rows, colWidths=[col_width] * len(table_rows[0]))
                    t.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BG_H3)),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    elems.append(t)
                    elems.append(Spacer(1, 0.3 * cm))
                in_table = False
                table_rows = []

            # --- Egyéb Markdown Elemek ---
            if not raw_line:
                elems.append(Spacer(1, 0.2 * cm))
            elif raw_line.startswith('# '):
                elems.append(Paragraph(self._fmt(raw_line[2:], color=BG_H1), self.styles['HT_H1']))
            elif raw_line.startswith('## '):
                elems.append(Paragraph(self._fmt(raw_line[3:], color=BG_H2), self.styles['HT_H2']))
            elif raw_line.startswith('* ') or raw_line.startswith('- '):
                elems.append(Paragraph(raw_line[2:], self.styles['HT_Bullet'], bulletText='•'))
            else:
                if "(Kép/File:" in raw_line:
                    raw_line = raw_line.replace("(Kép/File:", "<b><i>(Csatolmány:").replace(")", ")</i></b>")
                elems.append(Paragraph(raw_line, self.styles['Normal']))

        # Failsafe: Ha a fájl végén maradt nyitva táblázat vagy kód
        if in_code_block and code_lines:
            elems.append(Paragraph("<br/>".join(code_lines).replace(' ', '&nbsp;'), self.styles['HT_Code']))
        if in_table and table_rows:
            col_width = (A4[0] - MARGIN_X * 2) / len(table_rows[0])
            t = Table(table_rows, colWidths=[col_width] * len(table_rows[0]))
            t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                   ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BG_H3))]))
            elems.append(t)

        doc.build(elems, onFirstPage=self._header_footer, onLaterPages=self._header_footer, canvasmaker=NumberedCanvas)
        return os.path.join(self.output_dir, filename)