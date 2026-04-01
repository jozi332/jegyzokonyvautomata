import os
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image

# Mindent a pdf_engine-ből importálunk!
from core.pdf_engine import PDFEngineBase, NumberedCanvas, MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM, BG_TITLE, BG_H1, BG_H2, \
    BG_H3


class PDFGenerator(PDFEngineBase):
    """
    Ez az osztály felel a konkrét dokumentumok (Munkalap, Jegyzőkönyv, EOJ, TI)
    összeállításáért az alapmotor stílusait felhasználva.
    """

    def __init__(self, output_dir="output"):
        super().__init__()
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_doc(self, filename):
        return SimpleDocTemplate(os.path.join(self.output_dir, filename), pagesize=A4,
                                 topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
                                 leftMargin=MARGIN_X, rightMargin=MARGIN_X)

    def _build_doc(self, doc, elems, filename):
        doc.build(elems, onFirstPage=self._header_footer, onLaterPages=self._header_footer, canvasmaker=NumberedCanvas)
        return os.path.join(self.output_dir, filename)

    # ==========================================
    # Építőelem Helper Metódusok
    # ==========================================
    def _build_munkalap_elements(self, data, rows):
        elems = []
        elems.append(Paragraph(self._fmt("Munkalap", color=BG_TITLE), self.styles['HT_Title']))
        elems.append(Paragraph(self._fmt(f"Munkalap sorszáma: M{data.get('iW_num', '')}", color=BG_TITLE),
                               self.styles['HT_Subtitle']))

        elems.append(Paragraph("Projekt megrendelői hivatkozás:", self.styles['Normal']))
        elems.append(Paragraph(data.get('sOrder_link', ''), self.styles['Normal']))
        elems.append(Paragraph(f"Szerződés sorszáma: S{data.get('iContract_num', '')}", self.styles['Normal']))
        elems.append(
            Paragraph(f"Munka leírása (dokumentum azonosítója): D{data.get('iW_num', '')}", self.styles['Normal']))
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

        # --- DINAMIKUS DOLGOZÓ NÉV HASZNÁLATA ---
        elems.append(Paragraph(f"Munkát elvégezte: {self.worker_name}", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph(self._fmt("Jegyzőkönyv és tevékenység lista", color=BG_H1), self.styles['HT_H1']))
        elems.append(Spacer(1, 0.2 * cm))

        headers = ["Dátum", "Tevékenység", "M. idő\n(ó)", "U. idő\n(ó)", "Költség", "Melléklet"]
        t_data = [[Paragraph(self._fmt(h, bold=True), self.styles['Table_H']) for h in headers]]

        for r in rows:
            t_data.append([
                Paragraph(str(r[0]), self.styles['Table_C_Center']),
                Paragraph(str(r[1]), self.styles['Table_C_Center']),
                Paragraph(str(r[3]), self.styles['Table_C_Center']),
                Paragraph(str(r[4]), self.styles['Table_C_Center']),
                Paragraph(str(r[5]), self.styles['Table_C_Center']),
                Paragraph(str(r[6]), self.styles['Table_C_Center']),
            ])

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

        elems.append(Paragraph(self._fmt(data.get('iW_num', ''), color=BG_H2), self.styles['HT_H2']))
        elems.append(Paragraph(data.get('sW_type', ''), self.styles['Normal']))
        elems.append(Paragraph(f"Helyszín: {data.get('aW_address', '')}", self.styles['Normal']))
        elems.append(Paragraph(f"Megrendelői hivatkozás: {data.get('sOrder_link', '')}", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph(self._fmt("Idő összefoglaló", color=BG_H3), self.styles['HT_H3']))
        elems.append(Paragraph(
            f"Dátum: &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {data.get('dDate', '')}",
            self.styles['Normal']))

        events = data.get('time_summary', [])
        if events:
            time_table_data = []
            for ev in events:
                if len(ev) == 3:
                    time_table_data.append(
                        [Paragraph(str(ev[0]), self.styles['Normal']), Paragraph("-", self.styles['Normal']),
                         Paragraph(str(ev[1]), self.styles['Normal']), Paragraph(str(ev[2]), self.styles['Normal'])])
                else:
                    time_table_data.append([Paragraph(str(ev[0]), self.styles['Normal']), "", "", ""])

            t_time = Table(time_table_data, colWidths=[1.6 * cm, 0.5 * cm, 1.6 * cm, 12 * cm], hAlign='LEFT')
            t_time.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('BOTTOMPADDING', (0, 0), (-1, -1), 2)]))
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

        mini_data = [[Paragraph("Utazási idő:", self.styles['Normal']), "",
                      Paragraph(f"{data.get('iT_time', '')} óra", s_right)]]
        if not is_ho and has_travel_fee:
            mini_data.append(
                [Paragraph("Kiszállási díj:", s_indent1), Paragraph(f"{data.get('iTravel_fee', '')}", s_right), ""])

        mini_data.append(
            [Paragraph("Munkaidő:", self.styles['Normal']), "", Paragraph(f"{data.get('iW_time', '')} óra", s_right)])
        mini_data.append([Paragraph(self._fmt("Összesen:", bold=True), self.styles['Normal']),
                          Paragraph(self._fmt(f"{data.get('iO_fee', '')}", bold=True) if not is_ho else "", s_right),
                          Paragraph(self._fmt(f"{data.get('iO_time', '')}", bold=True), s_right)])

        t_mini = Table(mini_data, colWidths=[5 * cm, 3 * cm, 3 * cm], hAlign='LEFT')
        t_mini.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('TOPPADDING', (0, 0), (-1, -1), 1),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 1)]))
        elems.append(t_mini)
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph(self._fmt("Elvégzett tevékenységek", color=BG_H3), self.styles['HT_H3']))
        elems.append(Paragraph(data.get('ssW_desc', '').replace('\n', '<br/>'), self.styles['Normal']))
        return elems

    # ==========================================
    # Public File Generator Methods
    # ==========================================
    def create_work(self, filename, data, rows):
        doc = self._get_doc(filename)
        elems = self._build_munkalap_elements(data, rows)
        return self._build_doc(doc, elems, filename)

    def create_merge(self, filename, data):
        doc = self._get_doc(filename)
        elems = self._build_jegyzokonyv_elements(data)
        return self._build_doc(doc, elems, filename)

    def create_full_report(self, filename, data, rows, logs_data):
        doc = self._get_doc(filename)
        elems = self._build_munkalap_elements(data, rows)
        elems.append(PageBreak())

        s_center = ParagraphStyle(name='CenterTitle', parent=self.styles['HT_Title'], alignment=TA_LEFT)
        elems.append(Paragraph(self._fmt("Mellékletek", color=BG_TITLE), s_center))

        for j_data in logs_data:
            elems.append(PageBreak())
            elems.extend(self._build_jegyzokonyv_elements(j_data))

        return self._build_doc(doc, elems, filename)

    def create_contract_report(self, filename, c_data, rows):
        doc = self._get_doc(filename)
        elems = []

        elems.append(
            Paragraph(self._fmt("Elszámolási összesített jegyzőkönyv", color=BG_TITLE), self.styles['HT_Title']))
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

        # --- DINAMIKUS DOLGOZÓ NÉV HASZNÁLATA ---
        elems.append(Paragraph(f"Munkát elvégezte: {self.worker_name}", self.styles['Normal']))
        elems.append(Spacer(1, 1.5 * cm))
        elems.append(Paragraph("Aláírás: .......................................", self.styles['Normal']))

        elems.append(PageBreak())
        elems.append(Paragraph(self._fmt("Tevékenység lista", color=BG_H1), self.styles['HT_H1']))
        elems.append(Spacer(1, 0.5 * cm))

        headers = ["Dátum", "Munkalap", "Hivatkozás", "M. idő", "U. idő", "Költség", "Melléklet", "Túlóra"]
        t_data = [[Paragraph(self._fmt(h, bold=True), self.styles['Table_H']) for h in headers]]

        s_small = ParagraphStyle('Small', parent=self.styles['Table_C_Center'], fontSize=8, leading=9)
        s_small_left = ParagraphStyle('SmallL', parent=self.styles['Table_C'], fontSize=8, leading=9)

        for r in rows:
            t_data.append([
                Paragraph(str(r[0]), s_small), Paragraph(str(r[1]), s_small), Paragraph(str(r[2]), s_small_left),
                Paragraph(str(r[3]), s_small), Paragraph(str(r[4]), s_small), Paragraph(str(r[5]), s_small),
                Paragraph(str(r[6]), s_small), Paragraph(str(r[7]), s_small)
            ])

        t = Table(t_data, colWidths=[2.2 * cm, 1.8 * cm, 3.8 * cm, 1.2 * cm, 1.2 * cm, 2.3 * cm, 3.0 * cm, 1.5 * cm],
                  repeatRows=1)
        t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
        elems.append(t)

        return self._build_doc(doc, elems, filename)

    def create_completion_certificate(self, filename, c_data, ti_data):
        doc = self._get_doc(filename)
        elems = []

        elems.append(Paragraph(self._fmt("Teljesítés igazolás", color=BG_TITLE), self.styles['HT_Title']))
        elems.append(Paragraph(f"sorszáma: {c_data.get('sTI_num', '')}", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph(self._fmt("Megbízó", bold=True), self.styles['Normal']))
        s_indent = ParagraphStyle('Indent', parent=self.styles['Normal'], leftIndent=1.0 * cm)
        elems.append(Paragraph(f"Neve: {c_data.get('client_name', '')}", s_indent))
        elems.append(Paragraph(f"Székhelye: {c_data.get('client_address', '')}", s_indent))
        elems.append(Paragraph(f"Adószáma: {c_data.get('client_tax', '')}", s_indent))
        elems.append(Spacer(1, 0.3 * cm))

        c_info = self.company_header[0].split(';')
        elems.append(Paragraph(self._fmt("Megbízott", bold=True), self.styles['Normal']))
        elems.append(Paragraph(f"Neve: {c_info[0].strip()}", s_indent))
        elems.append(Paragraph(f"Székhelye: {c_info[1].strip()}", s_indent))
        elems.append(Paragraph(f"{c_info[2].strip()}", s_indent))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(Paragraph(f"Szerződés sorszáma: {c_data.get('contract_code', '')}", self.styles['Normal']))
        elems.append(Spacer(1, 0.5 * cm))

        elems.append(
            Paragraph(self._fmt("Munkadíj, díjmódosító tényezők, végösszeg", color=BG_H2), self.styles['HT_H2']))

        headers = ["Megnevezés", "Mennyiség", "Költség (Ft)"]
        t_data = [[Paragraph(self._fmt(h, bold=True), self.styles['Table_H']) for h in headers]]

        def add_row(name, qty, cost):
            t_data.append([
                Paragraph(name, self.styles['Table_C']),
                Paragraph(qty, self.styles['Table_C_Center']),
                Paragraph(f"{int(cost):,} Ft".replace(',', ' '), self.styles['Table_C_Center'])
            ])

        add_row("Munkaóra alapdíj", f"{ti_data['w_hours']:g} óra", ti_data['base_fee_total'])

        if ti_data['overtime_fee_total'] > 0:
            add_row("Túlóra pótlék (+%)", f"{ti_data['overtime_hours']:g} óra", ti_data['overtime_fee_total'])
        if ti_data['night_fee_total'] > 0:
            add_row("Éjszakai pótlék (+%)", f"{ti_data['night_hours']:g} óra", ti_data['night_fee_total'])
        if ti_data['weekend_fee_total'] > 0:
            add_row("Szombati pótlék (+%)", f"{ti_data['weekend_hours']:g} óra", ti_data['weekend_fee_total'])
        if ti_data['holiday_fee_total'] > 0:
            add_row("Vasárnapi / Ünnep pótlék (+%)", f"{ti_data['holiday_hours']:g} óra", ti_data['holiday_fee_total'])
        if ti_data['travel_fee_total'] > 0:
            add_row("Utazási és kiszállási díj", "-", ti_data['travel_fee_total'])
        if ti_data['mat_cost_total'] > 0:
            add_row("Anyagköltség / Egyéb", "-", ti_data['mat_cost_total'])

        t_data.append([
            Paragraph(self._fmt("VÉGÖSSZEG (MINDÖSSZESEN)", bold=True), self.styles['Table_H']), "",
            Paragraph(self._fmt(f"{int(ti_data['total_cost']):,} Ft".replace(',', ' '), bold=True),
                      self.styles['Table_C_Center'])
        ])

        t = Table(t_data, colWidths=[9.0 * cm, 3.5 * cm, 4.5 * cm], repeatRows=1)
        t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                               ('SPAN', (0, -1), (1, -1))]))
        elems.append(t)
        elems.append(Spacer(1, 2.0 * cm))

        sig_data = [
            [Paragraph("Teljesítést igazolom (Megbízó):", self.styles['Normal']),
             Paragraph("Számla kiállítására jogosult (Megbízott):", self.styles['Normal'])],
            [Spacer(1, 1.5 * cm), Spacer(1, 1.5 * cm)],
            [Paragraph(".......................................", self.styles['Normal']),
             Paragraph(".......................................", self.styles['Normal'])],
            [Paragraph("Dátum: ................................", self.styles['Normal']),
             Paragraph("Dátum: ................................", self.styles['Normal'])]
        ]
        t_sig = Table(sig_data, colWidths=[8.5 * cm, 8.5 * cm])
        t_sig.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP')]))
        elems.append(t_sig)

        return self._build_doc(doc, elems, filename)

    # ==========================================
    # EXTENDED DOCUMENT GENERATOR (JSON + TABLES + IMAGES)
    # ==========================================
    def create_document(self, filename, doc_data, project_data):
        doc = self._get_doc(filename)
        elems = []

        elems.append(Paragraph(self._fmt(doc_data['doc_id'], color=BG_H2), self.styles['HT_H2']))
        p_code = project_data.get('project_code', '')
        c_name = project_data.get('end_client_name', 'Ismeretlen Megrendelő')
        elems.append(Paragraph(f"Projekt: {p_code} - {c_name}", self.styles['Normal']))
        elems.append(Paragraph(f"Létrehozva: {doc_data['created_date']}", self.styles['Normal']))
        elems.append(Spacer(1, 1 * cm))
        elems.append(Paragraph(self._fmt(doc_data['title'], color=BG_TITLE), self.styles['HT_DocTitle']))

        content_raw = doc_data['content']

        is_json = False
        if content_raw.strip().startswith("["):
            try:
                content_json = json.loads(content_raw)
                is_json = isinstance(content_json, list)
            except json.JSONDecodeError:
                is_json = False

        if is_json:
            # Load styles for the PDF Generator
            ui_styles = {}
            style_path = "document_styles.json"
            if os.path.exists(style_path):
                try:
                    with open(style_path, "r", encoding="utf-8") as f:
                        ui_styles = json.load(f)
                except Exception:
                    pass

            for block in content_json:
                b_type = block.get('type', 'paragraph')

                # HANDLE PAGE BREAKS
                if b_type == 'page_break':
                    elems.append(PageBreak())
                    continue

                # HANDLE EMBEDDED IMAGES
                elif b_type == 'image':
                    img_path = block.get('path', '')
                    if os.path.exists(img_path):
                        try:
                            # Read original dimensions to calculate aspect ratio
                            img_reader = ImageReader(img_path)
                            orig_w, orig_h = img_reader.getSize()

                            # Calculate the maximum allowed width on the A4 page
                            max_w = A4[0] - (MARGIN_X * 2)

                            if orig_w > max_w:
                                # Scale down while preserving aspect ratio
                                ratio = max_w / orig_w
                                draw_w = max_w
                                draw_h = orig_h * ratio
                            else:
                                draw_w = orig_w
                                draw_h = orig_h

                            # Append the ReportLab Image object
                            img_flowable = Image(img_path, width=draw_w, height=draw_h)
                            img_flowable.hAlign = 'CENTER'  # Center images by default
                            elems.append(img_flowable)
                            elems.append(Spacer(1, 0.3 * cm))
                        except Exception as e:
                            elems.append(Paragraph(f"[Kép renderelési hiba: {e}]", self.styles['Normal']))
                    else:
                        elems.append(Paragraph(f"[Hiányzó kép fájl: {img_path}]", self.styles['Normal']))
                    continue

                # HANDLE TABLES
                elif b_type == 'embedded_table':
                    table_data = block.get('data', [])
                    if not table_data or not table_data[0]: continue

                    num_cols = len(table_data[0])
                    # Calculate column width to fit exactly on A4 paper
                    col_width = (A4[0] - MARGIN_X * 2) / num_cols

                    formatted_rows = []
                    for r_idx, row in enumerate(table_data):
                        formatted_row = []
                        for cell_text in row:
                            # Safe HTML and line break conversion inside cells
                            escaped_text = cell_text.replace('&', '&amp;').replace('<', '&lt;').replace('>',
                                                                                                        '&gt;').replace(
                                '\n', '<br/>')
                            p = Paragraph(escaped_text, self.styles['Table_C'])
                            formatted_row.append(p)
                        formatted_rows.append(formatted_row)

                    t = Table(formatted_rows, colWidths=[col_width] * num_cols)
                    t.setStyle(TableStyle([
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BG_H3)),  # First row gets header background
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6)
                    ]))
                    elems.append(t)
                    elems.append(Spacer(1, 0.3 * cm))
                    continue

                # HANDLE NORMAL TEXT (PARAGRAPHS / HEADINGS / LISTS)
                elif b_type == 'paragraph':
                    style_name = block.get('style', 'Normal')
                    align_str = block.get('align', 'left')
                    is_list = block.get('list', False)
                    text = block.get('text', '')

                    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                    if not text.strip() and not is_list:
                        elems.append(Spacer(1, 0.2 * cm))
                        continue

                    if "(Kép/File:" in text:
                        text = text.replace("(Kép/File:", "<b><i>(Csatolmány:").replace(")", ")</i></b>")

                    fmt_text = text.strip()

                    # Read style attributes
                    cfg = ui_styles.get(style_name, {})
                    f_size = cfg.get("font_size", 11)
                    f_color = cfg.get("color", "#000000")
                    is_bold = cfg.get("bold", False)
                    is_italic = cfg.get("italic", False)
                    bg_color = cfg.get("bg_color", "")

                    if style_name == 'Címsor 1':
                        bg_color = BG_H1
                    elif style_name == 'Címsor 2':
                        bg_color = BG_H2
                    elif style_name == 'Címsor 3':
                        bg_color = BG_H3

                    align_enum = TA_LEFT
                    if align_str == "center":
                        align_enum = TA_CENTER
                    elif align_str == "right":
                        align_enum = TA_RIGHT

                    # Create a dynamic ReportLab style combining UI style and formatting
                    dyn_style_name = f"DYN_{style_name.replace(' ', '_')}_{align_str}_{is_list}"
                    if dyn_style_name not in self.styles:
                        dyn_style = ParagraphStyle(
                            name=dyn_style_name,
                            parent=self.styles['Normal'],
                            fontSize=f_size,
                            leading=f_size + 3,
                            textColor=colors.HexColor(f_color),
                            alignment=align_enum
                        )
                        if is_list:
                            dyn_style.leftIndent = 20
                            dyn_style.bulletIndent = 10
                        self.styles.add(dyn_style)

                    if is_bold: fmt_text = f"<b>{fmt_text}</b>"
                    if is_italic: fmt_text = f"<i>{fmt_text}</i>"
                    if bg_color: fmt_text = self._fmt(fmt_text, color=bg_color)

                    # Render as list item or standard paragraph
                    if is_list:
                        elems.append(Paragraph(fmt_text, self.styles[dyn_style_name], bulletText='•'))
                    else:
                        elems.append(Paragraph(fmt_text, self.styles[dyn_style_name]))

        else:
            # ==========================================
            # BACKWARD COMPATIBILITY (OLD MARKDOWN)
            # ==========================================
            content = content_raw.split('\n')
            in_code_block = False
            code_lines = []
            in_table = False
            table_rows = []

            for line in content:
                raw_line = line.strip()
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

                if raw_line.startswith('|') and raw_line.endswith('|'):
                    in_table = True
                    cells = [cell.strip() for cell in raw_line.split('|') if cell.strip()]
                    row_data = [Paragraph(self._fmt(c), self.styles['Table_C']) for c in cells]
                    if row_data: table_rows.append(row_data)
                    continue
                elif in_table:
                    if table_rows:
                        col_width = (A4[0] - MARGIN_X * 2) / len(table_rows[0])
                        t = Table(table_rows, colWidths=[col_width] * len(table_rows[0]))
                        t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                               ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BG_H3))]))
                        elems.append(t)
                        elems.append(Spacer(1, 0.3 * cm))
                    in_table = False
                    table_rows = []

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

            if in_code_block and code_lines:
                elems.append(Paragraph("<br/>".join(code_lines).replace(' ', '&nbsp;'), self.styles['HT_Code']))
            if in_table and table_rows:
                col_width = (A4[0] - MARGIN_X * 2) / len(table_rows[0])
                t = Table(table_rows, colWidths=[col_width] * len(table_rows[0]))
                t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                                       ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(BG_H3))]))
                elems.append(t)

        return self._build_doc(doc, elems, filename)