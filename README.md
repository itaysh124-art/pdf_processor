# PDF Processor Pro - Professional Edition

## סקירה כללית
מערכת מקצועית לעיבוד קבצי PDF עם שילוב שלושה כלים מקצועיים:
- **PyMuPDF (fitz)** - ניתוח, חילוץ טקסט ומניפולציות בסיסיות
- **PDFToolbox** - validations, preflight ותיקון PDFs
- **Ghostscript** - המרות מורכבות, דחיסה ו-rendering

המערכת מאפשרת הוספת שכבות Spot Color, חורים, קווי חיתוך וקיפול, והמרה ל-CMYK.

## 🔧 התקנה

### דרישות מקדימות
```bash
pip install PyMuPDF
```

### כלים אופציונליים
1. **Ghostscript** (מומלץ מאוד)
   - הורד מ: https://www.ghostscript.com/download/gsdnld.html
   - התקן ב-Windows: הרץ את המתקין והוסף ל-PATH
   
2. **PDFToolbox** (אופציונלי)
   - דורש רישיון מסחרי
   - מתקין מ: https://www.callassoftware.com/

## 📦 מבנה הפרויקט

### תיקיות עיקריות

```
pdf_processor/              # כל קוד המקור
├── __init__.py
├── pdf_analysis.py        # מודול ניתוח PDF
├── pdf_processor_gui.py   # ממשק המשתמש הראשי
├── config.py              # הגדרות ותצורה
├── automation.py          # מודול אוטומציה
├── manual_processing.py   # עיבוד ידני
├── approval_sketch.py     # סקיצות לאישור
├── changes_log.py         # לוג שינויים
├── sketches_gallery.py    # גלריית סקיצות
├── ui_components.py       # רכיבי UI
├── pdf_utils.py           # כלי עזר PDF
├── add_holes_and_cutcontour.py  # הוספת חורים וקווי חיתוך
├── check_tools.py         # בדיקת כלים
├── example_usage.py       # דוגמאות שימוש
├── gui/                   # קבצי GUI נוספים
│   ├── __init__.py
│   └── pdf_processor_gui.py
└── processing/            # מודולי עיבוד
    ├── __init__.py
    └── crop_marks_remover.py

run_gui.py                 # הרצת הממשק הגרפי
check_tools.py             # בדיקת כלים זמינים
requirements.txt           # תלויות
README.md                  # תיעוד ראשי
```

### קבצים עיקריים

#### 📄 `pdf_processor/pdf_analysis.py` - **מודול הניתוח המקצועי**
מכיל שלוש מחלקות עיקריות:

##### 1. `PDFAnalyzer` - ניתוח ומניפולציות בסיסיות (PyMuPDF)
```python
from pdf_processor.pdf_analysis import PDFAnalyzer

# חילוץ מידע בסיסי
resolution, dpi, colormode, pixelated, vector = PDFAnalyzer.get_pdf_info("file.pdf")

# חילוץ טקסט
text = PDFAnalyzer.extract_text("file.pdf", page_num=0)

# חילוץ מטא-דאטה
metadata = PDFAnalyzer.extract_metadata("file.pdf")

# חילוץ תמונות
images = PDFAnalyzer.extract_images("file.pdf", output_folder="images")

# פיצול PDF
files = PDFAnalyzer.split_pdf("file.pdf", pages_per_file=1)

# סיבוב עמודים
PDFAnalyzer.rotate_pages("file.pdf", output_path="rotated.pdf", rotation=90)

# מיזוג PDFs
PDFAnalyzer.merge_pdfs(["file1.pdf", "file2.pdf"], "merged.pdf")

# זיהוי שכבות Spot
cutcontour = PDFAnalyzer.detect_spot_layer("file.pdf", "CutContour")
```

##### 2. `PDFValidator` - בדיקות ותיקון (PDFToolbox)
```python
from pdf_processor.pdf_analysis import PDFValidator

validator = PDFValidator()

# Preflight validation
result = validator.validate_pdf("file.pdf", profile='PDF/X-4')

# תיקון PDF פגום
validator.fix_corrupted_pdf("corrupted.pdf", "fixed.pdf")

# המרה ל-PDF/A
validator.convert_to_pdfa("file.pdf", "output.pdf", standard='PDF/A-2b')

# המרה ל-PDF/X
validator.convert_to_pdfx("file.pdf", "output.pdf", standard='PDF/X-4')

# בדיקת עמידה בתקן
compliance = validator.check_compliance("file.pdf", standard='PDF/X-4')
```

##### 3. `PDFConverter` - המרות ואופטימיזציה (Ghostscript)
```python
from pdf_processor.pdf_analysis import PDFConverter

converter = PDFConverter()

# אופטימיזציה ודחיסה
converter.optimize_pdf("file.pdf", "optimized.pdf", quality='printer')
# רמות איכות: screen (72 DPI), ebook (150 DPI), printer (300 DPI), 
#              prepress (300 DPI + colors)

# המרה לתמונות
images = converter.convert_to_images("file.pdf", "output", dpi=300, format='png')
# פורמטים זמינים: png, jpg, tiff

# המרה ל-PDF/A
converter.convert_to_pdfa_gs("file.pdf", "output.pdf", pdfa_version='2')

# מיזוג PDFs
converter.merge_pdfs(["file1.pdf", "file2.pdf"], "merged.pdf")
```

#### 🎨 `config.py` - **הגדרות וקונפיגורציה**
```python
from config import (
    COLORS,                    # סכמת צבעים
    FONTS,                     # הגדרות גופנים
    DEFAULT_VALUES,            # ערכי ברירת מחדל לעיבוד
    PDF_TOOLS_CONFIG,          # הגדרות הכלים המקצועיים
    OPTIMIZATION_CONFIG,       # הגדרות אופטימיזציה
    CONVERSION_CONFIG,         # הגדרות המרות
    VALIDATION_CONFIG,         # הגדרות בדיקות
    LOGGING_CONFIG            # הגדרות לוגים
)
```

**הגדרות הכלים:**
- `PDF_TOOLS_CONFIG['pymupdf']` - הגדרות PyMuPDF
- `PDF_TOOLS_CONFIG['pdftoolbox']` - הגדרות PDFToolbox
- `PDF_TOOLS_CONFIG['ghostscript']` - הגדרות Ghostscript

#### 📄 `pdf_processor_gui.py` - **הקובץ הראשי**
האפליקציה המלאה עם ממשק גרפי

#### 🤖 `automation.py` - **מודול אוטומציה**
- ניטור תיקיות אוטומטי
- עיבוד קבצים בזמן אמת
- ניהול תיקיות הצלחה/שגיאות
- לוג ומעקב אחר פעולות

#### ✋ `manual_processing.py` - **עיבוד ידני**
- ממשק בחירת קבצים
- טבלת קבצים עם מסננים
- הגדרות עיבוד מפורטות

#### 📊 `example_usage.py` - **דוגמאות שימוש**
קובץ עם דוגמאות מלאות לשימוש בכל הכלים

## 🚀 שימוש מהיר

### דוגמה 1: ניתוח PDF בסיסי
```python
from pdf_processor.pdf_analysis import PDFAnalyzer

# קבלת מידע מלא על PDF
resolution, dpi, colormode, pixelated, vector = PDFAnalyzer.get_pdf_info("myfile.pdf")

print(f"רזולוציה: {resolution}")
print(f"DPI: {dpi}")
print(f"מצב צבעים: {colormode}")
print(f"וקטורי: {'כן' if vector else 'לא'}")

# חילוץ מטא-דאטה
metadata = PDFAnalyzer.extract_metadata("myfile.pdf")
print(f"כותרת: {metadata['title']}")
print(f"מספר עמודים: {metadata['page_count']}")
print(f"גודל קובץ: {metadata['file_size']} bytes")
```

### דוגמה 2: אופטימיזציה ודחיסה
```python
from pdf_processor.pdf_analysis import PDFConverter

converter = PDFConverter()

# דחיסה לאיכות הדפסה (300 DPI)
converter.optimize_pdf(
    "large_file.pdf", 
    "compressed.pdf", 
    quality='printer'
)

# המרה לתמונות PNG ברזולוציה גבוהה
images = converter.convert_to_images(
    "document.pdf",
    output_folder="output_images",
    dpi=300,
    format='png'
)

print(f"נוצרו {len(images)} תמונות")
```

### דוגמה 3: תהליך עבודה מלא
```python
from pdf_processor.pdf_analysis import PDFAnalyzer, PDFValidator, PDFConverter

pdf_file = "input.pdf"

# שלב 1: ניתוח
print("מנתח קובץ...")
metadata = PDFAnalyzer.extract_metadata(pdf_file)
print(f"עמודים: {metadata['page_count']}")

# שלב 2: בדיקת תקינות
print("בודק תקינות...")
validator = PDFValidator()
validation = validator.validate_pdf(pdf_file, profile='PDF/X-4')

if not validation['success']:
    print("מתקן שגיאות...")
    validator.fix_corrupted_pdf(pdf_file, "fixed.pdf")
    pdf_file = "fixed.pdf"

# שלב 3: אופטימיזציה
print("מבצע אופטימיזציה...")
converter = PDFConverter()
converter.optimize_pdf(pdf_file, "optimized.pdf", quality='printer')

# שלב 4: המרה לתקן
print("ממיר ל-PDF/X-4...")
validator.convert_to_pdfx("optimized.pdf", "final.pdf", standard='PDF/X-4')

print("✓ הושלם!")
```

## 🎯 תכונות מתקדמות

### עבודה עם שכבות Spot Color
```python
from pdf_processor.pdf_analysis import PDFAnalyzer

# זיהוי שכבת CutContour
cutcontour = PDFAnalyzer.detect_spot_layer("file.pdf", "CutContour")
print(f"CutContour: {cutcontour}")

# זיהוי שכבת Crease
crease = PDFAnalyzer.detect_spot_layer("file.pdf", "Crease")
print(f"Crease: {crease}")
```

### חילוץ והמרת תמונות
```python
from pdf_processor.pdf_analysis import PDFAnalyzer, PDFConverter

# חילוץ כל התמונות מ-PDF
images = PDFAnalyzer.extract_images("document.pdf", "extracted_images")

# המרת PDF לתמונות ברזולוציות שונות
converter = PDFConverter()

# Preview ברזולוציה נמוכה
converter.convert_to_images("doc.pdf", "previews", dpi=150, format='jpg')

# Print ברזולוציה גבוהה
converter.convert_to_images("doc.pdf", "print_ready", dpi=300, format='png')
```

### פיצול ומיזוג PDFs
```python
from pdf_processor.pdf_analysis import PDFAnalyzer

# פיצול ל-1 עמוד לקובץ
PDFAnalyzer.split_pdf("multi_page.pdf", "split", pages_per_file=1)

# פיצול ל-5 עמודים לקובץ
PDFAnalyzer.split_pdf("multi_page.pdf", "split", pages_per_file=5)

# מיזוג קבצים
PDFAnalyzer.merge_pdfs(
    ["page1.pdf", "page2.pdf", "page3.pdf"],
    "merged_document.pdf"
)
```

## ⚙️ הגדרות מתקדמות

### התאמת הגדרות Ghostscript
ערוך את `config.py`:
```python
PDF_TOOLS_CONFIG = {
    'ghostscript': {
        'enabled': True,
        'path': r'C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe',
        'quality_settings': {
            'custom': {'dpi': 450, 'description': 'Custom high quality'}
        },
        'default_quality': 'custom'
    }
}
```

### התאמת הגדרות אופטימיזציה
```python
OPTIMIZATION_CONFIG = {
    'auto_optimize': True,
    'compress_images': True,
    'image_quality': 90,
    'target_dpi': 300,
    'remove_unused_resources': True,
    'linearize': True  # Fast Web View
}
```

### התאמת הגדרות Validation
```python
VALIDATION_CONFIG = {
    'check_on_load': True,
    'auto_fix': True,
    'validation_rules': {
        'check_fonts': True,
        'check_images': True,
        'check_colors': True,
        'check_transparency': True,
        'check_bleed': True,
        'check_trim_box': True
    }
}
```

## 🔍 פתרון בעיות

### Ghostscript לא נמצא
```python
from pdf_processor.pdf_analysis import PDFConverter

converter = PDFConverter()

if not converter.gs_path:
    print("Ghostscript לא נמצא!")
    print("הורד מ: https://www.ghostscript.com/download/gsdnld.html")
    
    # הגדרה ידנית של נתיב
    converter.gs_path = r"C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe"
```

### בדיקת זמינות כלים
```python
from pdf_processor.pdf_analysis import PDFAnalyzer, PDFValidator, PDFConverter

# PyMuPDF - תמיד זמין (חובה)
print("✓ PyMuPDF זמין")

# PDFToolbox - אופציונלי
validator = PDFValidator()
if validator.pdftoolbox_path:
    print(f"✓ PDFToolbox נמצא: {validator.pdftoolbox_path}")
else:
    print("✗ PDFToolbox לא נמצא (אופציונלי)")

# Ghostscript - מומלץ
converter = PDFConverter()
if converter.gs_path:
    print(f"✓ Ghostscript נמצא: {converter.gs_path}")
else:
    print("✗ Ghostscript לא נמצא (מומלץ להתקין)")
```

## 📚 משאבים נוספים

- [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
- [Ghostscript Documentation](https://www.ghostscript.com/doc/current/Use.htm)
- [PDF/X Standards](https://www.iso.org/standard/42872.html)
- [PDF/A Standards](https://www.iso.org/standard/57229.html)

## 🎓 קבצי דוגמה

הרץ את `example_usage.py` לדוגמאות מלאות:
```bash
python example_usage.py
```

הקובץ מכיל דוגמאות ל:
- ✓ כל הפונקציות של PyMuPDF
- ✓ Validation ותיקון עם PDFToolbox
- ✓ המרות ואופטימיזציה עם Ghostscript
- ✓ תהליכי עבודה משולבים

## 📝 רישיונות

- **PyMuPDF** - AGPL / Commercial
- **Ghostscript** - AGPL / Commercial
- **PDFToolbox** - Commercial (רישיון נדרש)

---

**גרסה:** Professional Edition 2.0  
**עדכון אחרון:** ינואר 2026
- ניטור תיקיות אוטומטי
- עיבוד קבצים בזמן אמת
- ניהול תיקיות הצלחה/שגיאות
- לוג ומעקב אחר פעולות

**שימוש:**
```python
from automation import AutomationModule

automation = AutomationModule(parent_app)
automation.create_automation_tab(automation_tab)
```

### ✋ `manual_processing.py`
**מודול עיבוד ידני**
- ממשק בחירת קבצים
- טבלת קבצים עם מסננים
- הגדרות עיבוד מפורטות
- פונקציות עזר ל-UI

**שימוש:**
```python
from manual_processing import (
    create_manual_tab_ui,
    create_file_selection_ui,
    create_treeview_ui,
    create_settings_ui
)
```

### 🔧 `pdf_utils.py`
**פונקציות עזר ל-PDF**
- `detect_spot_layer()` - זיהוי שכבות Spot Color
- `analyze_image_quality()` - ניתוח איכות תמונה
- `enhance_image_ai()` - שיפור תמונות באמצעות AI
- `get_smart_recommendations()` - המלצות חכמות

**שימוש:**
```python
from pdf_utils import detect_spot_layer, analyze_image_quality

layer = detect_spot_layer(pdf_path, "CutContour")
quality = analyze_image_quality(pil_image)
```

## תהליך העבודה

### עיבוד ידני
1. בחירת קבצי PDF (קבצים בודדים או תיקייה שלמה)
2. סקירת המידע בטבלה (DPI, צבעים, שכבות קיימות)
3. בחירת קבצים ספציפיים באמצעות checkbox
4. הגדרת פרמטרים (חורים, שוליים, שכבות)
5. עיבוד הקבצים

### אוטומציה
1. הגדרת תיקיית ניטור
2. הגדרת תיקיות יעד (הצלחה/שגיאות)
3. בחירת תכונות לעיבוד אוטומטי
4. הפעלת המערכת
5. מעקב בלוג בזמן אמת

## תכונות עיקריות

### שכבות Spot Color
- **CutContour** - מגנטה 100% (קו חיתוך)
- **Crease** - ציאן 100% (קו קיפול)
- **Holes** - ציאן 50% + צהוב 100% (חורים)

### אופציות עיבוד
- ✂️ הוספת CutContour
- 🕳️ הוספת חורים (קוטר ומרחק מתכווננים)
- 📐 החלפת Crease
- 📏 הוספת שוליים לבנים
- 🎨 המרה ל-CMYK
- 🎯 שיפור איכות תמונות

### מסננים חכמים
- סינון לפי שם קובץ
- סינון לפי DPI
- סינון לפי מצב צבעים
- סינון לפי איכות
- סינון לפי שכבות קיימות

## דרישות מערכת

### ספריות Python נדרשות
```bash
pip install pypdf reportlab pillow opencv-python scikit-image
```

### ספריות אופציונליות (לשיפור AI)
```bash
pip install torch torchvision realesrgan
```

## הרצת המערכת

```bash
python pdf_processor_gui.py
```

## עדכונים עתידיים אפשריים

### מודולריזציה נוספת
הפרוייקט מוכן להרחבה:
- ניתן להוסיף מודולים נוספים בקלות
- כל מודול עצמאי ובעל אחריות ברורה
- שימוש חוזר בקוד דרך ייבוא פשוט

### שיפורים מוצעים
1. **הפרדת לוגיקת עיבוד** - העברת פונקציות עיבוד PDF למודול נפרד
2. **מנהל הגדרות** - שמירה וטעינה של הגדרות משתמש
3. **מערכת תבניות** - שמירת תצורות עיבוד שונות
4. **ייצוא דוחות** - יצירת דוחות PDF/Excel על קבצים מעובדים
5. **עיבוד מקבילי** - שיפור ביצועים עבור קבצים רבים

## תמיכה ותיעוד
- כל הקבצים מתועדים עם docstrings בעברית
- קוד ממוין לפי תחומי אחריות
- שמות משתנים וקבועים ברורים

---

**גרסה:** 2.0  
**תאריך:** 2026  
**רישיון:** שימוש פנימי
