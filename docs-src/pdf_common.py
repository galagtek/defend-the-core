#!/usr/bin/env python3
"""
Module commun pour la génération des PDFs Defend-The-Core.
Fournit : enregistrement des polices, styles, palette, helpers.
"""
import os
import hashlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether, CondPageBreak, Image, ListFlowable, ListItem
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ============================================================
# PALETTE (générée par pdf.py palette.generate)
# Intent: neutral | Mode: minimal | Harmony: split_complementary
# ============================================================
ACCENT       = colors.HexColor('#4d28bc')
TEXT_PRIMARY  = colors.HexColor('#191a1c')
TEXT_MUTED    = colors.HexColor('#868a91')
BG_SURFACE   = colors.HexColor('#d6d9de')
BG_PAGE      = colors.HexColor('#f1f3f4')
TABLE_HEADER_COLOR = ACCENT
TABLE_HEADER_TEXT  = colors.white
TABLE_ROW_EVEN     = colors.white
TABLE_ROW_ODD      = BG_SURFACE

# Couleurs sémantiques dérivées
COLOR_BLOCK  = colors.HexColor('#c0392b')   # rouge pour "block/interdit"
COLOR_ALLOW  = colors.HexColor('#27ae60')   # vert pour "allow/autorisé"
COLOR_WARN   = colors.HexColor('#e67e22')   # orange pour avertissement

# ============================================================
# ENREGISTREMENT DES POLICES
# ============================================================
FONT_DIR_LIB = '/usr/share/fonts/truetype/liberation'
FONT_DIR_DJV = '/usr/share/fonts/truetype/dejavu'

def register_fonts():
    """Enregistre les polices utilisables."""
    # Liberation Serif = équivalent métrique de Times New Roman
    pdfmetrics.registerFont(TTFont('BodyFont', f'{FONT_DIR_LIB}/LiberationSerif-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('BodyFont-Bold', f'{FONT_DIR_LIB}/LiberationSerif-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('BodyFont-Italic', f'{FONT_DIR_LIB}/LiberationSerif-Italic.ttf'))
    pdfmetrics.registerFont(TTFont('BodyFont-BoldItalic', f'{FONT_DIR_LIB}/LiberationSerif-BoldItalic.ttf'))
    registerFontFamily('BodyFont',
                       normal='BodyFont', bold='BodyFont-Bold',
                       italic='BodyFont-Italic', boldItalic='BodyFont-BoldItalic')

    # Liberation Sans pour les titres
    pdfmetrics.registerFont(TTFont('HeadFont', f'{FONT_DIR_LIB}/LiberationSans-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('HeadFont-Bold', f'{FONT_DIR_LIB}/LiberationSans-Bold.ttf'))
    registerFontFamily('HeadFont', normal='HeadFont', bold='HeadFont-Bold')

    # DejaVu Sans Mono pour le code
    pdfmetrics.registerFont(TTFont('CodeFont', f'{FONT_DIR_DJV}/DejaVuSansMono.ttf'))
    pdfmetrics.registerFont(TTFont('CodeFont-Bold', f'{FONT_DIR_DJV}/DejaVuSansMono-Bold.ttf'))
    registerFontFamily('CodeFont', normal='CodeFont', bold='CodeFont-Bold')

# ============================================================
# STYLES
# ============================================================
def get_styles():
    """Retourne un dictionnaire de styles ParagraphStyle."""
    s = {}
    s['title'] = ParagraphStyle(
        name='Title', fontName='HeadFont-Bold', fontSize=26, leading=32,
        textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=6
    )
    s['subtitle'] = ParagraphStyle(
        name='Subtitle', fontName='HeadFont', fontSize=14, leading=18,
        textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=24
    )
    s['h1'] = ParagraphStyle(
        name='H1', fontName='HeadFont-Bold', fontSize=18, leading=24,
        textColor=ACCENT, spaceBefore=24, spaceAfter=12
    )
    s['h2'] = ParagraphStyle(
        name='H2', fontName='HeadFont-Bold', fontSize=14, leading=18,
        textColor=TEXT_PRIMARY, spaceBefore=16, spaceAfter=8
    )
    s['h3'] = ParagraphStyle(
        name='H3', fontName='BodyFont-Bold', fontSize=12, leading=16,
        textColor=TEXT_PRIMARY, spaceBefore=12, spaceAfter=6
    )
    s['body'] = ParagraphStyle(
        name='Body', fontName='BodyFont', fontSize=10.5, leading=16,
        textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, spaceAfter=8
    )
    s['body_left'] = ParagraphStyle(
        name='BodyLeft', fontName='BodyFont', fontSize=10.5, leading=16,
        textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=8
    )
    s['bullet'] = ParagraphStyle(
        name='Bullet', fontName='BodyFont', fontSize=10.5, leading=16,
        textColor=TEXT_PRIMARY, leftIndent=18, bulletIndent=6, spaceAfter=4
    )
    s['code'] = ParagraphStyle(
        name='Code', fontName='CodeFont', fontSize=8.5, leading=12,
        textColor=TEXT_PRIMARY, leftIndent=12, rightIndent=12,
        spaceBefore=6, spaceAfter=6, backColor=BG_PAGE,
        borderColor=BG_SURFACE, borderWidth=0.5, borderPadding=6
    )
    s['caption'] = ParagraphStyle(
        name='Caption', fontName='BodyFont-Italic', fontSize=9, leading=12,
        textColor=TEXT_MUTED, alignment=TA_CENTER, spaceBefore=4, spaceAfter=12
    )
    s['callout'] = ParagraphStyle(
        name='Callout', fontName='BodyFont', fontSize=10.5, leading=16,
        textColor=TEXT_PRIMARY, leftIndent=16, rightIndent=12,
        spaceBefore=8, spaceAfter=8, backColor=BG_PAGE,
        borderColor=ACCENT, borderWidth=0, borderPadding=8
    )
    # Styles pour les cellules de tableau
    s['th'] = ParagraphStyle(
        name='TH', fontName='HeadFont-Bold', fontSize=9.5, leading=12,
        textColor=colors.white, alignment=TA_CENTER
    )
    s['td'] = ParagraphStyle(
        name='TD', fontName='BodyFont', fontSize=9, leading=12,
        textColor=TEXT_PRIMARY, alignment=TA_LEFT
    )
    s['td_center'] = ParagraphStyle(
        name='TDC', fontName='BodyFont', fontSize=9, leading=12,
        textColor=TEXT_PRIMARY, alignment=TA_CENTER
    )
    s['toc_h1'] = ParagraphStyle(
        name='TOCH1', fontName='HeadFont-Bold', fontSize=12, leading=18, leftIndent=10
    )
    s['toc_h2'] = ParagraphStyle(
        name='TOCH2', fontName='BodyFont', fontSize=10.5, leading=16, leftIndent=30
    )
    return s

# ============================================================
# HELPERS
# ============================================================
PAGE_W, PAGE_H = A4
LEFT_M = 2.0 * cm
RIGHT_M = 2.0 * cm
TOP_M = 2.0 * cm
BOTTOM_M = 2.0 * cm
AVAIL_W = PAGE_W - LEFT_M - RIGHT_M

MAX_KEEP_HEIGHT = A4[1] * 0.4

def safe_keep_together(elements):
    """Wrap elements in KeepTogether only if total height is reasonable."""
    total_h = 0
    for el in elements:
        try:
            w, h = el.wrap(AVAIL_W, A4[1])
            total_h += h
        except Exception:
            pass
    if total_h <= MAX_KEEP_HEIGHT:
        return [KeepTogether(elements)]
    elif len(elements) >= 2:
        return [KeepTogether(elements[:2])] + list(elements[2:])
    else:
        return list(elements)

def make_table(data, col_ratios=None, header=True):
    """Crée un tableau stylé avec la palette DTC.
    data: liste de listes de Paragraph ou str.
    col_ratios: proportions des colonnes (somme = 1.0).
    """
    styles = get_styles()
    if col_ratios is None:
        n = len(data[0])
        col_ratios = [1.0 / n] * n
    col_widths = [r * AVAIL_W for r in col_ratios]

    # Convertir les strings en Paragraph
    processed = []
    for i, row in enumerate(data):
        new_row = []
        for j, cell in enumerate(row):
            if isinstance(cell, str):
                style = styles['th'] if (header and i == 0) else styles['td']
                cell = Paragraph(cell, style)
            new_row.append(cell)
        processed.append(new_row)

    t = Table(processed, colWidths=col_widths, hAlign='CENTER')
    style_cmds = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('GRID', (0, 0), (-1, -1), 0.5, TEXT_MUTED),
    ]
    if header:
        style_cmds.extend([
            ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ])
        for i in range(1, len(data)):
            bg = TABLE_ROW_ODD if i % 2 == 1 else TABLE_ROW_EVEN
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style_cmds))
    return t

def add_heading(text, styles, level=0):
    """Ajoute un titre avec bookmark pour le TOC."""
    style = styles['h1'] if level == 0 else styles['h2']
    key = 'h_%s' % hashlib.md5(text.encode()).hexdigest()[:8]
    p = Paragraph('<a name="%s"/>%s' % (key, text), style)
    p.bookmark_name = text
    p.bookmark_level = level
    p.bookmark_text = text
    p.bookmark_key = key
    return p

class TocDocTemplate(SimpleDocTemplate):
    """SimpleDocTemplate avec support TOC."""
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            key = getattr(flowable, 'bookmark_key', '')
            self.notify('TOCEntry', (level, text, self.page, key))

def header_footer(canvas, doc):
    """Header et footer de page."""
    canvas.saveState()
    # Footer : numéro de page + titre
    canvas.setFont('BodyFont', 8)
    canvas.setFillColor(TEXT_MUTED)
    page_num = canvas.getPageNumber()
    canvas.drawRightString(PAGE_W - RIGHT_M, 1.0 * cm, str(page_num))
    canvas.drawString(LEFT_M, 1.0 * cm, "Defend-The-Core")
    # Ligne de séparation footer
    canvas.setStrokeColor(BG_SURFACE)
    canvas.setLineWidth(0.5)
    canvas.line(LEFT_M, 1.4 * cm, PAGE_W - RIGHT_M, 1.4 * cm)
    canvas.restoreState()

def build_doc(filename, title, author="Defend-The-Core"):
    """Crée un TocDocTemplate configuré."""
    doc = TocDocTemplate(
        filename, pagesize=A4,
        leftMargin=LEFT_M, rightMargin=RIGHT_M,
        topMargin=TOP_M, bottomMargin=BOTTOM_M,
        title=title, author=author, creator=author,
        subject="Documentation technique Defend-The-Core"
    )
    return doc
