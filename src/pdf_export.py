"""تصدير تقرير التداخلات الدوائية إلى PDF"""

from datetime import datetime
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER


# ===== تسجيل الخط العربي =====
FONT_NAME = "ArabicFont"
FONT_PATH = "C:/Windows/Fonts/arial.ttf"  # خط عربي متوفر في ويندوز

try:
    pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
except Exception as e:
    print(f"⚠️ مش قادر أحمّل الخط من {FONT_PATH}: {e}")
    FONT_NAME = "Helvetica"  # fallback


def ar(text):
    """تنسيق النص العربي للعرض في PDF"""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)


def create_pdf_report(ingredients, interactions, pairs_checked):
    """
    إنشاء تقرير PDF
    
    ingredients: قائمة بأسماء المواد اللي افحصت
    interactions: قائمة بالتداخلات المكتشفة
    pairs_checked: عدد الأزواج اللي افحصت
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="تقرير فحص التداخلات الدوائية",
    )

    # ===== الأنماط =====
    title_style = ParagraphStyle(
        "Title",
        fontName=FONT_NAME,
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor("#2c3e50"),
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontName=FONT_NAME,
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=15,
        textColor=colors.HexColor("#7f8c8d"),
    )

    heading_style = ParagraphStyle(
        "Heading",
        fontName=FONT_NAME,
        fontSize=14,
        alignment=TA_RIGHT,
        spaceAfter=10,
        spaceBefore=15,
        textColor=colors.HexColor("#2c3e50"),
    )

    body_style = ParagraphStyle(
        "Body",
        fontName=FONT_NAME,
        fontSize=11,
        alignment=TA_RIGHT,
        leading=16,
        textColor=colors.HexColor("#34495e"),
    )

    cell_style = ParagraphStyle(
        "Cell",
        fontName=FONT_NAME,
        fontSize=9,
        alignment=TA_RIGHT,
        leading=12,
        textColor=colors.black,
    )

    warning_style = ParagraphStyle(
        "Warning",
        fontName=FONT_NAME,
        fontSize=11,
        alignment=TA_RIGHT,
        leading=18,
        textColor=colors.HexColor("#c0392b"),
        backColor=colors.HexColor("#fadbd8"),
        borderPadding=10,
        spaceAfter=15,
    )

    # ===== الإطار =====
    story = []

    # العنوان
    story.append(Paragraph(ar("تقرير فحص التداخلات الدوائية"), title_style))
    story.append(Paragraph(
        ar(f"تاريخ الفحص: {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
        subtitle_style
    ))
    story.append(Spacer(1, 10))

    # المواد اللي افحصت
    story.append(Paragraph(ar("المواد اللي اتفحصت:"), heading_style))
    ingredients_text = " • ".join(ingredients)
    story.append(Paragraph(ar(ingredients_text), body_style))
    story.append(Spacer(1, 10))

    # عدد الأزواج
    story.append(Paragraph(
        ar(f"عدد الأزواج اللي افحصت: {pairs_checked}"),
        body_style
    ))
    story.append(Spacer(1, 15))

    # ===== لو مفيش تداخلات =====
    if not interactions:
        story.append(Paragraph(
            ar("✅ مفيش تداخلات مسجلة بين المواد دي في قاعدة البيانات."),
            body_style
        ))
        story.append(Spacer(1, 15))
        story.append(Paragraph(
            ar("ملاحظة: قاعدة البيانات مش شاملة كل التداخلات المحتملة. استشر الطبيب أو الصيدلي."),
            body_style
        ))
    else:
        # ===== عدادات =====
        major = sum(1 for i in interactions if i["severity"] == "major")
        moderate = sum(1 for i in interactions if i["severity"] == "moderate")
        minor = sum(1 for i in interactions if i["severity"] == "minor")

        story.append(Paragraph(ar("ملخص النتائج:"), heading_style))

        summary_data = [
            [ar("خطير"), ar("متوسط"), ar("بسيط"), ar("الإجمالي")],
            [str(major), str(moderate), str(minor), str(len(interactions))]
        ]
        summary_table = Table(summary_data, colWidths=[4 * cm] * 4)
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, 0), 12),
            ("FONTSIZE", (0, 1), (-1, 1), 16),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 1), (-1, 1), 10),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("BACKGROUND", (0, 1), (0, 1), colors.HexColor("#fadbd8")),
            ("BACKGROUND", (1, 1), (1, 1), colors.HexColor("#fdebd0")),
            ("BACKGROUND", (2, 1), (2, 1), colors.HexColor("#d5f4e6")),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 15))

        # ===== التنبيه =====
        if major > 0:
            story.append(Paragraph(
                ar(f"🚨 تحذير: فيه {major} تداخل خطير! استشر الطبيب فوراً."),
                warning_style
            ))
        elif moderate > 0:
            story.append(Paragraph(
                ar(f"⚠️ انتبه: فيه {moderate} تداخل متوسط. يُفضل استشارة الصيدلي."),
                warning_style
            ))

        # ===== جدول التداخلات =====
        story.append(Paragraph(ar("تفاصيل التداخلات:"), heading_style))

        severity_text = {
            "major": "🔴 خطير",
            "moderate": "🟡 متوسط",
            "minor": "🟢 بسيط",
            "unknown": "⚪ غير معروف"
        }

        table_data = [[
            ar("الخطورة"), ar("المادة 1"), ar("المادة 2"),
            ar("الوصف"), ar("التوصية")
        ]]

        for inter in interactions:
            table_data.append([
                Paragraph(ar(severity_text.get(inter["severity"], "غير معروف")), cell_style),
                Paragraph(ar(inter["a"]), cell_style),
                Paragraph(ar(inter["b"]), cell_style),
                Paragraph(ar(inter["description"]), cell_style),
                Paragraph(ar(inter["management"]), cell_style),
            ])

        detail_table = Table(
            table_data,
            colWidths=[2.2 * cm, 2.8 * cm, 2.8 * cm, 5 * cm, 5 * cm],
            repeatRows=1
        )
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, 0), FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#f8f9fa")]),
        ]))
        story.append(detail_table)

    # ===== إخلاء المسؤولية =====
    story.append(Spacer(1, 20))
    story.append(Paragraph(ar("إخلاء مسؤولية:"), heading_style))
    story.append(Paragraph(
        ar("هذا التقرير لأغراض تعليمية فقط ولا يُغني عن استشارة الطبيب أو الصيدلي. "
           "قاعدة البيانات المستخدمة ليست شاملة لكل التداخلات الدوائية المحتملة. "
           "لا تتخذ أي قرار علاجي بناءً على هذا التقرير فقط."),
        body_style
    ))

    # ===== بناء الـ PDF =====
    doc.build(story)
    buffer.seek(0)
    return buffer
