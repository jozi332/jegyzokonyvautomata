import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, StyleSheet1
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfgen import canvas

# --- 1. CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, 'assets', 'CourierNew.ttf')
FONT_BOLD_PATH = os.path.join(BASE_DIR, 'assets', 'CourierNew-Bold.ttf')

FONT_NAME = 'CourierNew'
FONT_BOLD_NAME = 'CourierNew-Bold'

# HTML Colors
BG_TITLE = '#64ff64'
BG_H1 = '#78ff78'
BG_H2 = '#96ff96'
BG_H3 = '#b4ffb4'
COL_TEXT = 'black'

# Layout Constants
MARGIN_X = 2.0 * cm
MARGIN_TOP = 2.5 * cm
MARGIN_BOTTOM = 2.0 * cm


class NumberedCanvas(canvas.Canvas):
    """Custom canvas for 'Page / Total Pages' rendering."""

    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        try:
            self.setFont(FONT_NAME, 9)
        except Exception:
            self.setFont('Courier', 9)
        self.drawCentredString(A4[0] / 2.0, 2 * cm, f"{self._pageNumber}/{page_count}")


class PDFEngineBase:
    """Base class for PDF generator: handles fonts, styles, and dynamic headers/footers."""

    def __init__(self):
        self._register_font()
        self.styles = self._create_styles()

        # Default placeholder values
        self.company_header = [
            "Minta Kft.; 1234 Budapest, Minta utca 1.; Adószám: 12345678-1-12",
            "E: info@minta.hu        T: +36 30 123 4567"
        ]
        self.bank_info = "Banksz.: 00000000-00000000-00000000       Nytsz.: 00000000"
        self.worker_name = "Minta Dolgozó"

    def set_company_data(self, name, address, tax, email, phone1, phone2, phone3, bank_huf, bank_eur, reg_num,
                         worker_name):
        """Dynamically sets all company and worker information from the DB."""
        self.company_header[0] = f"{name}; {address}; Adószám: {tax}"

        # Filter out empty phone numbers and join them gracefully
        phones = [p.strip() for p in [phone1, phone2, phone3] if p and p.strip()]
        phone_str = " | ".join(phones)
        self.company_header[1] = f"E: {email}        T: {phone_str}"

        # Format the bank accounts nicely (hide EUR if not provided)
        bank_str = f"HUF: {bank_huf}" if bank_huf else ""
        if bank_eur and bank_eur.strip():
            bank_str += f"   EUR: {bank_eur}"

        self.bank_info = f"Banksz.: {bank_str}       Nytsz.: {reg_num}"
        self.worker_name = worker_name

    def _register_font(self):
        try:
            has_normal = os.path.exists(FONT_PATH)
            has_bold = os.path.exists(FONT_BOLD_PATH)

            if has_normal:
                pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
                if has_bold:
                    pdfmetrics.registerFont(TTFont(FONT_BOLD_NAME, FONT_BOLD_PATH))
                    registerFontFamily(FONT_NAME, normal=FONT_NAME, bold=FONT_BOLD_NAME, italic=FONT_NAME,
                                       boldItalic=FONT_BOLD_NAME)
                else:
                    registerFontFamily(FONT_NAME, normal=FONT_NAME, bold=FONT_NAME, italic=FONT_NAME,
                                       boldItalic=FONT_NAME)
                self.font_main = FONT_NAME
            else:
                print(f"ERROR: Font file not found: {FONT_PATH}")
                self.font_main = 'Helvetica'
        except Exception as e:
            print(f"ERROR loading font: {e}")
            self.font_main = 'Helvetica'

    def _create_styles(self):
        s = StyleSheet1()
        s.add(ParagraphStyle(name='Normal', fontName=self.font_main, fontSize=11, leading=12, textColor=colors.black,
                             spaceAfter=4))
        s.add(ParagraphStyle(name='Table_H', parent=s['Normal'], fontSize=10, alignment=TA_CENTER))
        s.add(ParagraphStyle(name='Table_C', parent=s['Normal'], fontSize=10, alignment=TA_LEFT))
        s.add(ParagraphStyle(name='Table_C_Center', parent=s['Normal'], fontSize=10, alignment=TA_CENTER))

        s.add(ParagraphStyle(name='HT_Title', parent=s['Normal'], fontSize=20, leading=24, spaceBefore=0, spaceAfter=6,
                             keepWithNext=True))
        s.add(ParagraphStyle(name='HT_Subtitle', parent=s['Normal'], fontSize=11, leading=13, spaceBefore=0,
                             spaceAfter=12))
        s.add(ParagraphStyle(name='HT_H1', parent=s['Normal'], fontSize=16, leading=20, spaceBefore=12, spaceAfter=6,
                             keepWithNext=True))
        s.add(ParagraphStyle(name='HT_H2', parent=s['Normal'], fontSize=15, leading=18, spaceBefore=0, spaceAfter=6))
        s.add(ParagraphStyle(name='HT_H3', parent=s['Normal'], fontSize=14, leading=17,
                             textColor=colors.HexColor('#434343'), spaceBefore=10, spaceAfter=4, keepWithNext=True))

        s.add(ParagraphStyle(name='HT_Bullet', parent=s['Normal'], leftIndent=20, bulletIndent=10, spaceAfter=2))
        s.add(ParagraphStyle(
            name='HT_Code', fontName='Courier', fontSize=9, leading=10,
            textColor=colors.HexColor('#202020'), backColor=colors.HexColor('#FDFDFD'),
            borderPadding=5, spaceBefore=5, spaceAfter=5
        ))
        s.add(ParagraphStyle(name='HT_DocTitle', parent=s['HT_Title'], alignment=TA_CENTER, spaceAfter=20))
        return s

    def _header_footer(self, canvas, doc):
        """Draws the dynamic company header and footer onto the PDF."""
        canvas.saveState()
        canvas.setFont(self.font_main, 9)
        y = A4[1] - 1.5 * cm
        canvas.drawString(2 * cm, y, self.company_header[0])
        y -= 0.5 * cm
        canvas.drawString(2 * cm, y, self.company_header[1])
        y -= 0.2 * cm
        canvas.setLineWidth(0.5)
        canvas.line(2 * cm, y, A4[0] - 2 * cm, y)
        y_foot = 1.5 * cm

        # Uses the dynamic bank_info variable
        canvas.drawString(2 * cm, y_foot, self.bank_info)
        canvas.restoreState()

    def _fmt(self, text, color=None, bold=False):
        res = str(text)
        if bold: res = f"<b>{res}</b>"
        if color: res = f'<font backColor="{color}">{res}</font>'
        return res