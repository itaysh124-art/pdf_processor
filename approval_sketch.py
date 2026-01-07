# -*- coding: utf-8 -*-
"""
מודול הפקת סקיצה לאישור לקוח
====================================

מטרה:
------
יצירת PDF מקצועי עם תצוגה מקדימה ופרטים טכניים לאישור לקוח לפני עיבוד סופי.

תכונות:
--------
- תצוגה מקדימה (thumbnail) של הקובץ המקורי
- מידות מדויקות (רוחב וגובה במ"מ)
- רשימה צבעונית של כל העיבודים המתוכננים
- פרטי תחנה ושם קובץ
- הוראות אישור ברורות
- חותמת זמן

שימוש:
-------
from approval_sketch import create_approval_sketch, get_sketch_settings

# דרך 1: עם GUI instance
settings = get_sketch_settings(gui_instance)
sketch_file = create_approval_sketch(input_pdf, settings)

# דרך 2: עם settings ידניים
settings = {
    'station_name': 'תחנה 5',
    'add_cutcontour': True,
    'add_holes': True,
    'hole_diameter': 7.0,
    'replace_crease': False,
    'convert_to_cmyk': True,
    'enhance_images': False
}
sketch_file = create_approval_sketch('input.pdf', settings)

תלויות:
--------
- reportlab: יצירת PDF
- pypdf: קריאת PDF מקורי
- pdf2image: המרת PDF לתמונה (אופציונלי)
- PIL/Pillow: עיבוד תמונות

פורמט פלט:
-----------
שם קובץ: {original_name}_APPROVAL_SKETCH.pdf
גודל עמוד: A4
קידוד: UTF-8 (תומך בעברית)

"""

import os
from pypdf import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from datetime import datetime
import tempfile


def create_approval_sketch(input_pdf, settings):
    """
    יצירת סקיצה לאישור לקוח עם תמונה ממוזערת ופרטים טכניים
    
    Args:
        input_pdf: נתיב לקובץ PDF המקורי
        settings: dictionary עם ההגדרות:
            - station_name: שם התחנה
            - add_cutcontour: האם להוסיף CutContour
            - add_holes: האם להוסיף חורים
            - replace_crease: האם להחליף Crease
            - convert_to_cmyk: האם להמיר ל-CMYK
            - hole_diameter: קוטר החורים במ"מ
            - enhance_images: האם לשפר תמונות
    
    Returns:
        נתיב לקובץ הסקיצה שנוצר, או None אם נכשל
    """
    try:
        # קריאת PDF המקורי
        reader = PdfReader(input_pdf)
        page = reader.pages[0]
        
        # זיהוי גבולות
        if hasattr(page, 'trimbox') and page.trimbox:
            bbox = page.trimbox
        elif hasattr(page, 'bleedbox') and page.bleedbox:
            bbox = page.bleedbox
        else:
            bbox = page.mediabox
        
        left = float(bbox.left)
        right = float(bbox.right)
        bottom = float(bbox.bottom)
        top = float(bbox.top)
        
        # חישוב מידות (ב-מ"מ)
        width_mm = round((right - left) / mm, 2)
        height_mm = round((top - bottom) / mm, 2)
        
        # קבלת כמות מההגדרות
        quantity = settings.get('quantity', 1)
        order_number = settings.get('order_number', '')
        
        # יצירת שם קובץ סקיצה - skiza_{מספר_הזמנה}.pdf
        # שימוש בתיקיית יעד אם צוינה, אחרת תיקיית הקובץ המקורי
        output_dir = settings.get('output_folder', os.path.dirname(input_pdf))
        if order_number:
            sketch_pdf = os.path.join(output_dir, f"skiza_{order_number}.pdf")
        else:
            # אם אין מספר הזמנה, שימוש בשם המקורי
            original_filename = settings.get('original_filename', os.path.basename(input_pdf))
            original_base = os.path.splitext(original_filename)[0]
            sketch_pdf = os.path.join(output_dir, f"skiza_{original_base}.pdf")
        
        # אם הקובץ קיים, הוא יידרס
        if os.path.exists(sketch_pdf):
            print(f"[SKETCH] Overwriting existing sketch: {sketch_pdf}")
        
        c = canvas.Canvas(sketch_pdf, pagesize=A4)
        
        # כותרת ראשית
        c.setFont("Arial-Bold", 24)
        c.setFillColorRGB(0, 0.74, 0.83)  # ציאן
        c.drawString(50, 800, "סקיצה לאישור לקוח")
        
        # קו הפרדה
        c.setStrokeColorRGB(0, 0.74, 0.83)
        c.setLineWidth(2)
        c.line(50, 790, 550, 790)
        
        # פרטי קובץ
        c.setFont("Arial-Bold", 14)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(50, 760, f"שם קובץ: {os.path.basename(input_pdf)}")
        
        station_name = settings.get('station_name', '')
        if station_name:
            c.setFillColorRGB(0.2, 0.2, 0.8)
            c.drawString(50, 740, f"🏭 תחנה: {station_name}")
        
        # מסגרת מידות
        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        c.setLineWidth(1)
        c.rect(45, 650, 250, 70, stroke=1, fill=0)
        
        c.setFont("Arial-Bold", 16)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(55, 700, "📏 מידות:")
        c.setFont("Arial", 14)
        c.drawString(75, 680, f"רוחב: {width_mm} מ\"מ")
        c.drawString(75, 660, f"גובה: {height_mm} מ\"מ")        
        # הצגת כמות אם גדולה מ-1
        if quantity > 1:
            c.setFont("Arial-Bold", 16)
            c.setFillColorRGB(0.8, 0.2, 0.2)
            c.drawString(310, 760, f"📊 כמות: {quantity}")        
        # פרטי עיבוד
        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        c.rect(45, 400, 250, 240, stroke=1, fill=0)
        
        c.setFont("Arial-Bold", 16)
        c.setFillColorRGB(0.2, 0.2, 0.2)
        c.drawString(55, 620, "⚙️ עיבודים מתוכננים:")
        
        c.setFont("Arial", 12)
        y_pos = 595
        
        if settings.get('add_cutcontour', False):
            c.setFillColorRGB(1, 0, 1)  # מג'נטה
            c.drawString(75, y_pos, "✓ CutContour - קו חיתוך ורוד")
            y_pos -= 25
        
        if settings.get('add_holes', False):
            c.setFillColorRGB(0.5, 0.8, 0)  # ירוק
            hole_diameter = settings.get('hole_diameter', 7.0)
            c.drawString(75, y_pos, f"✓ Holes - חורים ירוקים")
            c.setFont("Arial", 10)
            c.setFillColorRGB(0.3, 0.5, 0)
            c.drawString(95, y_pos - 12, f"(קוטר: {hole_diameter} מ\"מ)")
            c.setFont("Arial", 12)
            y_pos -= 35
        
        if settings.get('replace_crease', False):
            c.setFillColorRGB(0, 1, 1)  # ציאן
            c.drawString(75, y_pos, "✓ Crease - קווי קיפול כחולים")
            y_pos -= 25
        
        if settings.get('convert_to_cmyk', False):
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.drawString(75, y_pos, "✓ המרה ל-CMYK")
            y_pos -= 25
        
        if settings.get('enhance_images', False):
            c.setFillColorRGB(0.3, 0.3, 0.3)
            c.drawString(75, y_pos, "✓ שיפור תמונות ל-300 DPI")
            y_pos -= 25
        
        # תמונה ממוזערת
        try:
            from pdf2image import convert_from_path
            
            c.setStrokeColorRGB(0.2, 0.2, 0.2)
            c.rect(315, 400, 240, 320, stroke=1, fill=0)
            
            c.setFont("Arial-Bold", 16)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            c.drawString(325, 710, "🖼️ תצוגה מקדימה:")
            
            with tempfile.TemporaryDirectory() as temp_dir:
                images = convert_from_path(input_pdf, first_page=1, last_page=1, dpi=150)
                if images:
                    temp_image = os.path.join(temp_dir, "preview.png")
                    images[0].save(temp_image, "PNG")
                    
                    img = ImageReader(temp_image)
                    # שמירת יחס גובה-רוחב
                    max_width = 220
                    max_height = 280
                    img_width, img_height = images[0].size
                    scale = min(max_width / img_width, max_height / img_height)
                    
                    img_display_width = img_width * scale
                    img_display_height = img_height * scale
                    
                    # מרכוז התמונה
                    x_offset = 325 + (220 - img_display_width) / 2
                    y_offset = 410 + (280 - img_display_height) / 2
                    
                    c.drawImage(img, x_offset, y_offset, 
                              width=img_display_width, 
                              height=img_display_height,
                              preserveAspectRatio=True)
        except ImportError:
            # אם pdf2image לא מותקן
            c.setFont("Arial", 10)
            c.setFillColorRGB(0.6, 0.6, 0.6)
            c.drawString(325, 550, "תצוגה מקדימה לא זמינה")
            c.drawString(325, 535, "(נדרש להתקין pdf2image)")
        except Exception as e:
            c.setFont("Arial", 10)
            c.setFillColorRGB(0.8, 0, 0)
            c.drawString(325, 550, "לא ניתן להציג תצוגה מקדימה")
            error_msg = str(e)[:40]
            c.drawString(325, 535, f"שגיאה: {error_msg}")
        
        # הוראות אישור
        c.setStrokeColorRGB(1, 0.6, 0)
        c.setLineWidth(2)
        c.rect(45, 80, 510, 100, stroke=1, fill=0)
        
        c.setFont("Arial-Bold", 18)
        c.setFillColorRGB(1, 0.6, 0)  # כתום
        c.drawString(55, 155, "📋 הוראות אישור:")
        
        c.setFont("Arial", 13)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(75, 135, "1. בדוק את הפרטים, המידות והתצוגה המקדימה")
        c.drawString(75, 115, "2. אשר את הקובץ במערכת או שלח אישור")
        c.drawString(75, 95, "3. לאחר אישור - הקובץ יעבור אוטומטית לעיבוד סופי")
        
        # פוטר - תאריך ושעה
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        c.line(50, 60, 550, 60)
        
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        c.setFont("Arial", 10)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(50, 45, f"נוצר בתאריך: {now}")
        c.drawString(450, 45, "PDF Processor Pro")
        
        # שמירת הקובץ PDF
        c.save()
        
        print(f"[SKETCH] Created approval sketch PDF: {sketch_pdf}")
        
        # יצירת גרסת תמונה (JPG) מה-PDF
        try:
            # פתיחת ה-PDF שנוצר
            doc = fitz.open(sketch_pdf)
            page = doc[0]
            
            # רנדור לתמונה ברזולוציה גבוהה (300 DPI)
            zoom = 300 / 72  # המרה ל-300 DPI
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # שמירת התמונה
            image_path = sketch_pdf.replace('.pdf', '.jpg')
            pix.save(image_path)
            
            doc.close()
            
            print(f"[SKETCH] Created approval sketch image: {image_path}")
            
            # החזרת שני הנתיבים (PDF ותמונה)
            return {
                'pdf': sketch_pdf,
                'image': image_path
            }
            
        except Exception as e:
            print(f"[SKETCH] Warning: Failed to create image version: {e}")
            # אם נכשל ביצירת התמונה, להחזיר רק את ה-PDF
            return {
                'pdf': sketch_pdf,
                'image': None
            }
        
    except Exception as e:
        print(f"[ERROR] Failed to create approval sketch: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_sketch_settings(gui_instance):
    """
    מחלץ את ההגדרות הנחוצות מאובייקט ה-GUI
    
    Args:
        gui_instance: instance של PDFProcessorGUI
    
    Returns:
        dictionary עם ההגדרות
    """
    return {
        'station_name': gui_instance.station_name.get(),
        'add_cutcontour': gui_instance.add_cutcontour.get(),
        'add_holes': gui_instance.add_holes.get(),
        'replace_crease': gui_instance.replace_crease.get(),
        'convert_to_cmyk': gui_instance.convert_to_cmyk.get(),
        'hole_diameter': gui_instance.hole_diameter.get(),
        'enhance_images': gui_instance.enhance_images.get()
    }
