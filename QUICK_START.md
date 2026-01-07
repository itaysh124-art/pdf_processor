# Quick Start Guide - PDF Processor Pro

## התחלה מהירה ב-3 דקות

### 1️⃣ בדוק את המערכת
```bash
python check_tools.py
```

אמור להציג:
```
✓ PyMuPDF מותקן
✓ Ghostscript נמצא (אופציונלי)
```

---

### 2️⃣ דוגמאות מהירות

#### חילוץ מידע על PDF
```python
from pdf_analysis import PDFAnalyzer

# קבל מידע מלא
resolution, dpi, colormode, pixelated, vector = PDFAnalyzer.get_pdf_info("myfile.pdf")

print(f"רזולוציה: {resolution}")
print(f"DPI: {dpi}")
print(f"צבעים: {colormode}")
```

#### חילוץ טקסט
```python
text = PDFAnalyzer.extract_text("myfile.pdf")
print(text)
```

#### דחיסה ואופטימיזציה
```python
from pdf_analysis import PDFConverter

converter = PDFConverter()
converter.optimize_pdf("large_file.pdf", "compressed.pdf", quality='printer')
```

#### המרה לתמונות
```python
images = converter.convert_to_images("document.pdf", "output", dpi=300, format='png')
print(f"נוצרו {len(images)} תמונות")
```

---

### 3️⃣ תרחישים נפוצים

#### תרחיש 1: בדיקת איכות PDF
```python
from pdf_analysis import PDFAnalyzer

# בדוק מידע בסיסי
resolution, dpi, colormode, pixelated, vector = PDFAnalyzer.get_pdf_info("design.pdf")

if int(dpi) < 300:
    print("⚠ איכות נמוכה - DPI מתחת ל-300")

if colormode != "CMYK":
    print("⚠ לא מתאים לדפוס - צריך CMYK")

if vector:
    print("✓ קובץ וקטורי - מעולה!")
```

#### תרחיש 2: הכנת קובץ לדפוס
```python
from pdf_analysis import PDFValidator

validator = PDFValidator()

# המר ל-PDF/X (תקן דפוס)
validator.convert_to_pdfx("design.pdf", "print_ready.pdf", standard='PDF/X-4')
```

#### תרחיש 3: דחיסת קובץ גדול
```python
from pdf_analysis import PDFConverter

converter = PDFConverter()

# דחיסה לאיכות הדפסה
converter.optimize_pdf("big_file.pdf", "compressed.pdf", quality='printer')

# דחיסה לאיכות מסך (קובץ קטן מאוד)
converter.optimize_pdf("big_file.pdf", "web_version.pdf", quality='screen')
```

#### תרחיש 4: פיצול PDF גדול
```python
from pdf_analysis import PDFAnalyzer

# פצל ל-1 עמוד לקובץ
files = PDFAnalyzer.split_pdf("multi_page.pdf", "split_pages", pages_per_file=1)

print(f"נוצרו {len(files)} קבצים")
```

#### תרחיש 5: מיזוג מספר PDFs
```python
from pdf_analysis import PDFAnalyzer

pdfs = ["chapter1.pdf", "chapter2.pdf", "chapter3.pdf"]
PDFAnalyzer.merge_pdfs(pdfs, "complete_book.pdf")
```

#### תרחיש 6: יצירת תמונות Preview
```python
from pdf_analysis import PDFConverter

converter = PDFConverter()

# תמונות ברזולוציה נמוכה לאתר
converter.convert_to_images("catalog.pdf", "previews", dpi=150, format='jpg')

# תמונות ברזולוציה גבוהה להדפסה
converter.convert_to_images("catalog.pdf", "print", dpi=300, format='png')
```

---

### 4️⃣ תהליך עבודה מלא (All-in-One)

```python
from pdf_analysis import PDFAnalyzer, PDFValidator, PDFConverter

input_file = "original.pdf"

# שלב 1: ניתוח
print("📊 מנתח קובץ...")
metadata = PDFAnalyzer.extract_metadata(input_file)
resolution, dpi, colormode, _, _ = PDFAnalyzer.get_pdf_info(input_file)

print(f"  עמודים: {metadata['page_count']}")
print(f"  רזולוציה: {resolution}")
print(f"  DPI: {dpi}")
print(f"  צבעים: {colormode}")

# שלב 2: תיקון (אם נדרש)
print("\n🔧 בודק תקינות...")
validator = PDFValidator()
validation = validator.validate_pdf(input_file)

if not validation['success']:
    print("  מתקן שגיאות...")
    validator.fix_corrupted_pdf(input_file, "fixed.pdf")
    input_file = "fixed.pdf"

# שלב 3: אופטימיזציה
print("\n⚡ מבצע אופטימיזציה...")
converter = PDFConverter()

if metadata.get('file_size', 0) > 10 * 1024 * 1024:  # מעל 10MB
    converter.optimize_pdf(input_file, "optimized.pdf", quality='printer')
    input_file = "optimized.pdf"

# שלב 4: המרה לתקן
print("\n📄 ממיר לתקן מתאים...")
if colormode == "CMYK":
    validator.convert_to_pdfx(input_file, "final.pdf", standard='PDF/X-4')
    print("  ✓ הומר ל-PDF/X-4 (דפוס)")
else:
    validator.convert_to_pdfa(input_file, "final.pdf", standard='PDF/A-2b')
    print("  ✓ הומר ל-PDF/A-2b (ארכיון)")

# שלב 5: יצירת תמונות
print("\n🖼 יוצר תמונות preview...")
images = converter.convert_to_images(input_file, "previews", dpi=150, format='jpg')
print(f"  ✓ נוצרו {len(images)} תמונות")

print("\n✅ הושלם בהצלחה!")
```

---

### 5️⃣ פקודות CLI מהירות

#### בדיקת מערכת
```bash
python check_tools.py
```

#### הרצת דוגמאות
```bash
python example_usage.py
```

#### הרצת GUI (אם קיים)
```bash
python pdf_processor_gui.py
```

---

### 6️⃣ טיפים מהירים

✅ **Do's:**
- השתמש ב-PyMuPDF לפעולות מהירות (חילוץ, ניתוח)
- השתמש ב-Ghostscript לאופטימיזציה ודחיסה
- תמיד בדוק DPI לפני דפוס (צריך לפחות 300)
- שמור גיבוי לפני עריכה

❌ **Don'ts:**
- אל תדחוס קובץ כמה פעמים (איבוד איכות)
- אל תשתמש ב-quality='screen' לדפוס
- אל תשכח לבדוק מצב צבעים (CMYK לדפוס)

---

### 7️⃣ עזרה מהירה

**שאלה:** הקובץ שלי גדול מדי?
```python
from pdf_analysis import PDFConverter
converter = PDFConverter()
converter.optimize_pdf("big.pdf", "small.pdf", quality='printer')
```

**שאלה:** איך אדע אם הקובץ מתאים לדפוס?
```python
from pdf_analysis import PDFAnalyzer
_, dpi, colormode, _, _ = PDFAnalyzer.get_pdf_info("file.pdf")
if int(dpi) >= 300 and colormode == "CMYK":
    print("✓ מתאים לדפוס")
```

**שאלה:** איך אמיר RGB ל-CMYK?
```python
# עדיין בפיתוח - בינתיים השתמש באפליקציה הראשית
```

**שאלה:** איך אחלץ כל התמונות?
```python
from pdf_analysis import PDFAnalyzer
images = PDFAnalyzer.extract_images("doc.pdf", "extracted_images")
```

---

## מוכן להתחיל! 🚀

עכשיו אתה יודע את הבסיס.
לתיעוד מלא, ראה: [README.md](README.md)
