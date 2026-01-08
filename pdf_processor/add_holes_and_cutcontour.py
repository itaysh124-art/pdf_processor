from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import CMYKColorSep
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject, ArrayObject, DictionaryObject

import sys
import os
import re

# קלט: נתיב לקובץ PDF
input_pdf = sys.argv[1]

# שמירת הבסיס והסיומת לשימוש מאוחר יותר
base, ext = os.path.splitext(input_pdf)

# צבע CMYK CutContour (100% מג'נטה)
cutcontour_color = CMYKColorSep(0, 1, 0, 0, spotName="CutContour")  # C=0, M=1, Y=0, K=0 (מג'נטה/ורוד)

# צבע CMYK Crease לכיפוף (100% ציאן)
crease_color = CMYKColorSep(1, 0, 0, 0, spotName="Crease")  # C=1, M=0, Y=0, K=0 (ציאן/כחול בהיר)

# צבע CMYK Holes לחורים (ירוק בהיר)
holes_color = CMYKColorSep(0.5, 0, 1, 0, spotName="Holes")  # C=0.5, M=0, Y=1, K=0 (ירוק בהיר)

def replace_cut_with_cutcontour(page):
    """
    מחפש ומחליף כל התייחסות לצבע ספוט 'Cut' ב-'CutContour'
    """
    try:
        # קבלת תוכן העמוד
        content = ContentStream(page.get_contents(), page.pdf)
        
        # המרה למחרוזת לעיבוד
        content_str = content.get_data().decode('latin-1') if isinstance(content.get_data(), bytes) else str(content.get_data())
        
        # דפוסי חיפוש לצבע ספוט Cut
        # Pattern 1: /Cut cs או /Cut CS (הגדרת צבע ספוט)
        pattern1 = r'/Cut\s+(cs|CS)'
        # Pattern 2: ערכי CMYK + /Cut setcolorspace
        pattern2 = r'(\d+\.?\d*\s+){0,4}/Cut\s+setcolorspace'
        
        replacements_made = False
        
        # החלפת שם הצבע הספוט
        if re.search(pattern1, content_str):
            content_str = re.sub(r'/Cut(\s+)', r'/CutContour\1', content_str)
            replacements_made = True
            print("Found and replaced 'Cut' spot color references")
        
        # עדכון ה-Resources של העמוד
        if '/ColorSpace' in page.get('/Resources', {}):
            resources = page['/Resources']
            colorspaces = resources.get('/ColorSpace', {})
            
            if isinstance(colorspaces, DictionaryObject):
                # חיפוש אחר /Cut בהגדרות הצבעים
                if '/Cut' in colorspaces:
                    # שמירת ההגדרה הישנה
                    cut_def = colorspaces['/Cut']
                    # הוספת CutContour עם אותן הגדרות
                    colorspaces[NameObject('/CutContour')] = cut_def
                    # הסרת Cut הישן
                    del colorspaces[NameObject('/Cut')]
                    replacements_made = True
                    print("Found and replaced 'Cut' in ColorSpace resources")
        
        if replacements_made:
            # עדכון התוכן בעמוד
            page.replace_contents(content_str.encode('latin-1'))
            
    except Exception as e:
        print(f"Note: Could not process existing Cut layers: {e}")

def replace_crease_layers(page):
    """
    מחפש ומחליף כל התייחסות לשכבות כיפוף (Crease, Fold, וכו') ב-'Crease' ספוט
    """
    try:
        # קבלת תוכן העמוד
        content = ContentStream(page.get_contents(), page.pdf)
        
        # המרה למחרוזת לעיבוד
        content_str = content.get_data().decode('latin-1') if isinstance(content.get_data(), bytes) else str(content.get_data())
        
        replacements_made = False
        crease_names = ['Crease', 'Fold', 'Score', 'Creasing']
        
        # עדכון ה-Resources של העמוד
        if '/ColorSpace' in page.get('/Resources', {}):
            resources = page['/Resources']
            colorspaces = resources.get('/ColorSpace', {})
            
            if isinstance(colorspaces, DictionaryObject):
                for crease_name in crease_names:
                    name_key = f'/{crease_name}'
                    if name_key in colorspaces:
                        # שמירת ההגדרה הישנה
                        crease_def = colorspaces[name_key]
                        # הוספת Crease עם אותן הגדרות
                        colorspaces[NameObject('/Crease')] = crease_def
                        # הסרת השם הישן אם זה לא Crease
                        if crease_name != 'Crease':
                            del colorspaces[NameObject(name_key)]
                        replacements_made = True
                        print(f"Found and replaced '{crease_name}' in ColorSpace resources with 'Crease'")
                    
                    # החלפה בתוכן
                    pattern = rf'/{crease_name}(\s+)'
                    if re.search(pattern, content_str):
                        content_str = re.sub(pattern, r'/Crease\1', content_str)
                        replacements_made = True
                        print(f"Found and replaced '{crease_name}' spot color references with 'Crease'")
        
        if replacements_made:
            # עדכון התוכן בעמוד
            page.replace_contents(content_str.encode('latin-1'))
            
    except Exception as e:
        print(f"Note: Could not process existing Crease/Fold layers: {e}")

# הגדרות חורים
hole_diameter = 7 * mm
hole_radius = hole_diameter / 2
margin = 20 * mm

# מרחק של קו CutContour מהגרפיקה
offset = 0

# מרווח סביב הגרפיקה לגודל העמוד החדש
artboard_margin = 2 * mm

# קריאת ה-PDF המקורי
reader = PdfReader(input_pdf)
page = reader.pages[0]

page_width = float(page.mediabox.width)
page_height = float(page.mediabox.height)

# זיהוי גבולות החיתוך האמיתיים
# קודם מנסים TrimBox (גבולות חיתוך), אז BleedBox (גבולות דימום), ואז MediaBox
if hasattr(page, 'trimbox') and page.trimbox:
    bbox = page.trimbox
    print("Found TrimBox - using trim marks boundaries")
elif hasattr(page, 'bleedbox') and page.bleedbox:
    bbox = page.bleedbox
    print("Found BleedBox - using bleed boundaries")
else:
    bbox = page.mediabox
    print("No trim marks found - using MediaBox")

left = float(bbox.left)
right = float(bbox.right)
bottom = float(bbox.bottom)
top = float(bbox.top)

# חישוב גודל העמוד החדש (תיבת חיתוך + 2 מ"מ מכל צד)
new_page_width = (right - left) + (artboard_margin * 2)
new_page_height = (top - bottom) + (artboard_margin * 2)

# יצירת שם קובץ חדש עם מידות ה-CutContour (ללא המרווח)
cutcontour_width_mm = int(round((right - left) / mm))
cutcontour_height_mm = int(round((top - bottom) / mm))
output_pdf = f"{base}_{cutcontour_width_mm}x{cutcontour_height_mm}mm{ext}"

# חישוב offset להזזת הגרפיקה למרכז העמוד החדש
x_offset = artboard_margin - left
y_offset = artboard_margin - bottom

print(f"CutContour size: {cutcontour_width_mm}mm x {cutcontour_height_mm}mm")
print(f"Artboard size: {int(round(new_page_width / mm))}mm x {int(round(new_page_height / mm))}mm")
print(f"Output file: {os.path.basename(output_pdf)}")

# זיהוי והחלפת שכבות Cut קיימות
replace_cut_with_cutcontour(page)

# זיהוי והחלפת שכבות כיפוף (Crease, Fold, וכו')
replace_crease_layers(page)

# יצירת שכבת חורים + CutContour
overlay_path = "overlay_temp.pdf"
c = canvas.Canvas(overlay_path, pagesize=(new_page_width, new_page_height))

c.setStrokeColor(cutcontour_color)
c.setLineWidth(0.25)

# --- ציור CutContour מסביב לגרפיקה ---
c.rect(
    artboard_margin,
    artboard_margin,
    (right - left),
    (top - bottom),
    stroke=1,
    fill=0
)

# --- ציור 4 חורים בשכבת Holes ---
c.setStrokeColor(holes_color)
c.setLineWidth(0.25)

holes = [
    (margin, new_page_height - margin),                     # שמאל עליון
    (new_page_width - margin, new_page_height - margin),    # ימין עליון
    (margin, margin),                                        # שמאל תחתון
    (new_page_width - margin, margin)                        # ימין תחתון
]

for x, y in holes:
    c.circle(x, y, hole_radius, stroke=1, fill=0)

c.save()

# מיזוג השכבה עם ה-PDF המקורי
writer = PdfWriter()
overlay_reader = PdfReader(overlay_path)

# עדכון גודל העמוד של ה-PDF המקורי
from pypdf.generic import RectangleObject
page.mediabox = RectangleObject([0, 0, new_page_width, new_page_height])
page.cropbox = RectangleObject([0, 0, new_page_width, new_page_height])

# הזזת התוכן המקורי למרכז העמוד החדש
page.add_transformation([1, 0, 0, 1, x_offset, y_offset])

page.merge_page(overlay_reader.pages[0])
writer.add_page(page)

# שמירה בשם חדש
with open(output_pdf, "wb") as f:
    writer.write(f)

print(f"Created: {output_pdf}")