# תרשים ארכיטקטורה - PDF Processor Pro

## סקירה כללית
PDF Processor Pro הוא מערכת מקצועית לעיבוד קבצי PDF עם ארכיטקטורה מודולרית מבוססת Python.

---

## 📐 ארכיטקטורה ברמה גבוהה

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          PDF Processor Pro                              │
│                         Application Layer                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌──────────────────────────────────────────────────┐
        │         Entry Points (Root Directory)            │
        ├──────────────────────────────────────────────────┤
        │  • run_gui.py          → הפעלת GUI              │
        │  • check_tools.py      → בדיקת תלויות           │
        └──────────────────────────────────────────────────┘
                                    │
                                    ▼
        ┌──────────────────────────────────────────────────┐
        │            pdf_processor Package                 │
        │              (Core Application)                  │
        └──────────────────────────────────────────────────┘
                    │               │              │
         ┌──────────┘               │              └──────────┐
         ▼                          ▼                         ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   UI Layer      │      │  Business Logic │      │  Data Layer     │
│   (Presentation)│      │     Layer       │      │   (Processing)  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

---

## 🏗️ מבנה תיקיות מפורט

```
pdf_processor/
│
├── 📁 Root Level (Entry & Documentation)
│   ├── run_gui.py              🎯 נקודת כניסה - הפעלת GUI
│   ├── check_tools.py          🔧 בדיקת תלויות ותקינות
│   ├── requirements.txt        📦 תלויות חיצוניות
│   └── *.md                    📚 תיעוד
│
└── 📁 pdf_processor/           🎁 חבילת Python ראשית
    │
    ├── __init__.py             🔌 אתחול חבילה
    │
    ├── 🎨 UI Components Layer
    │   ├── pdf_processor_gui.py        # GUI ראשי
    │   ├── ui_components.py            # רכיבי UI משותפים
    │   ├── manual_processing.py        # ממשק עיבוד ידני
    │   ├── automation.py               # ממשק אוטומציה
    │   ├── changes_log.py              # ממשק לוג שינויים
    │   ├── sketches_gallery.py         # גלריית סקיצות
    │   └── approval_sketch.py          # יצירת סקיצות אישור
    │
    ├── 🧠 Business Logic Layer
    │   ├── pdf_analysis.py             # ניתוח PDF מתקדם
    │   │   ├── PDFAnalyzer             → ניתוח ומניפולציות
    │   │   ├── PDFValidator            → בדיקות ותיקון
    │   │   └── PDFConverter            → המרות ואופטימיזציה
    │   ├── pdf_utils.py                # כלי עזר PDF
    │   ├── add_holes_and_cutcontour.py # לוגיקת הוספת חורים
    │   └── check_tools.py              # בדיקת כלים חיצוניים
    │
    ├── ⚙️ Configuration Layer
    │   ├── config.py                   # הגדרות מערכת
    │   │   ├── COLORS                  → ערכת צבעים
    │   │   ├── FONTS                   → הגדרות גופנים
    │   │   ├── DEFAULT_VALUES          → ערכי ברירת מחדל
    │   │   └── WINDOW_CONFIG           → הגדרות חלון
    │   └── example_usage.py            # דוגמאות שימוש
    │
    ├── 📁 gui/                         # מודולי GUI נוספים
    │   ├── __init__.py
    │   └── pdf_processor_gui.py        # גרסת GUI חלופית
    │
    └── 📁 processing/                  # מודולי עיבוד מתקדמים
        ├── __init__.py
        └── crop_marks_remover.py       # הסרת סימני חיתוך
```

---

## 🔄 זרימת נתונים (Data Flow)

```
┌─────────────┐
│   משתמש     │
│   (User)    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────┐
│              GUI Layer (Tkinter)                        │
│  ┌───────────────────────────────────────────────────┐  │
│  │  pdf_processor_gui.py (PDFProcessorApp)          │  │
│  │  • manual_processing.py (עיבוד ידני)            │  │
│  │  • automation.py (אוטומציה)                     │  │
│  │  • changes_log.py (לוג)                         │  │
│  │  • sketches_gallery.py (גלריה)                  │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│           Business Logic Layer                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  pdf_analysis.py                                 │  │
│  │  ├─ PDFAnalyzer (PyMuPDF/fitz)                   │  │
│  │  │   • חילוץ טקסט                               │  │
│  │  │   • ניתוח מטא-דאטה                           │  │
│  │  │   • זיהוי Spot Colors                        │  │
│  │  │   • חילוץ תמונות                             │  │
│  │  │                                               │  │
│  │  ├─ PDFValidator (PDFToolbox)                    │  │
│  │  │   • Preflight validation                     │  │
│  │  │   • תיקון PDF פגום                           │  │
│  │  │                                               │  │
│  │  └─ PDFConverter (Ghostscript)                   │  │
│  │      • המרה לתמונות                             │  │
│  │      • אופטימיזציה ודחיסה                       │  │
│  │      • המרה ל-PDF/A, PDF/X                      │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  add_holes_and_cutcontour.py                     │  │
│  │  • הוספת חורים                                   │  │
│  │  • הוספת CutContour                             │  │
│  │  • קווי קיפול (Crease)                          │  │
│  └───────────────────────────────────────────────────┘  │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │  approval_sketch.py                              │  │
│  │  • יצירת PDF לאישור לקוח                        │  │
│  │  • תצוגה מקדימה + פרטים טכניים                  │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│          Processing & Output Layer                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │  processing/crop_marks_remover.py                │  │
│  │  • זיהוי והסרת סימני חיתוך                      │  │
│  │  • ניתוח תמונה עם OpenCV                        │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  קבצי PDF      │
              │  מעובדים       │
              └────────────────┘
```

---

## 🔌 תלויות חיצוניות (External Dependencies)

```
┌─────────────────────────────────────────────────────────────┐
│                   External Tools & Libraries                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  🔧 PDF Processing:                                         │
│  ├─ PyMuPDF (fitz)      → חובה - ניתוח וחילוץ             │
│  ├─ pypdf               → חובה - מניפולציות PDF            │
│  ├─ reportlab           → חובה - יצירת PDF                 │
│  ├─ Ghostscript         → מומלץ - המרות ואופטימיזציה      │
│  └─ PDFToolbox          → אופציונלי - validation מתקדם    │
│                                                              │
│  🎨 Image Processing:                                       │
│  ├─ Pillow (PIL)        → עיבוד תמונות                     │
│  ├─ OpenCV (cv2)        → ניתוח תמונה                      │
│  ├─ numpy               → חישובים מתמטיים                  │
│  ├─ scikit-image        → שיפור תמונות                     │
│  └─ RealESRGAN          → אופציונלי - AI upscaling        │
│                                                              │
│  💻 UI Framework:                                           │
│  └─ tkinter             → ממשק משתמש גרפי                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 רכיבים עיקריים (Core Components)

### 1. PDFProcessorApp (GUI ראשי)
```python
Class: PDFProcessorApp
Location: pdf_processor/pdf_processor_gui.py

תפקידים:
├─ ניהול ממשק המשתמש הגרפי
├─ תיאום בין מודולים שונים
├─ ניהול תהליכי עיבוד
└─ אינטראקציה עם משתמש

Dependencies:
├─ ui_components.ToggleSwitch
├─ pdf_analysis.PDFAnalyzer
├─ approval_sketch
├─ changes_log.ChangesLogTab
└─ sketches_gallery.SketchesGalleryTab
```

### 2. PDFAnalyzer (ניתוח PDF)
```python
Class: PDFAnalyzer
Location: pdf_processor/pdf_analysis.py

תפקידים:
├─ extract_text()          → חילוץ טקסט
├─ extract_metadata()      → מטא-דאטה
├─ extract_images()        → חילוץ תמונות
├─ get_pdf_info()          → מידע כללי (DPI, צבעים)
├─ detect_spot_layer()     → זיהוי Spot Colors
├─ split_pdf()             → פיצול PDF
├─ merge_pdfs()            → מיזוג PDFs
└─ rotate_pages()          → סיבוב עמודים

External Tool: PyMuPDF (fitz)
```

### 3. PDFConverter (המרות)
```python
Class: PDFConverter
Location: pdf_processor/pdf_analysis.py

תפקידים:
├─ convert_to_images()     → המרה לתמונות
├─ optimize_pdf()          → אופטימיזציה
├─ compress_pdf()          → דחיסה
└─ convert_to_pdfa()       → המרה ל-PDF/A

External Tool: Ghostscript
```

### 4. Configuration (הגדרות)
```python
Module: config.py
Location: pdf_processor/config.py

מספק:
├─ COLORS                  → ערכת צבעים
├─ FONTS                   → הגדרות גופנים
├─ DEFAULT_VALUES          → ערכי ברירת מחדל
├─ WINDOW_CONFIG           → הגדרות חלון
└─ PDF_TOOLS_CONFIG        → הגדרות כלים חיצוניים
```

---

## 🔀 Imports Flow (זרימת Imports)

```
Root Scripts
├─ run_gui.py
│  └─→ from pdf_processor.pdf_processor_gui import PDFProcessorApp
│
└─ check_tools.py
   └─→ from pdf_processor import check_tools

pdf_processor/ (Package)
├─ pdf_processor_gui.py
│  ├─→ from .ui_components import ToggleSwitch
│  ├─→ from .pdf_analysis import PDFAnalyzer
│  ├─→ from .approval_sketch import create_approval_sketch
│  ├─→ from .changes_log import ChangesLogTab
│  └─→ from .sketches_gallery import SketchesGalleryTab
│
├─ automation.py
│  └─→ from .config import COLORS, FONTS
│
├─ manual_processing.py
│  └─→ from .config import COLORS, FONTS
│
├─ check_tools.py
│  ├─→ from .pdf_analysis import PDFAnalyzer, PDFConverter
│  └─→ from .config import PDF_TOOLS_CONFIG
│
└─ gui/pdf_processor_gui.py
   ├─→ from ..ui_components import ToggleSwitch
   ├─→ from ..pdf_analysis import PDFAnalyzer
   └─→ from ..processing.crop_marks_remover import CropMarksRemover
```

---

## 🚀 תהליך עיבוד טיפוסי (Typical Processing Flow)

```
1. משתמש בוחר קובץ PDF
   │
   ▼
2. PDFAnalyzer מנתח את הקובץ
   ├─ גודל, רזולוציה, צבעים
   ├─ זיהוי תמונות מפוקסלות
   └─ חילוץ מידע טכני
   │
   ▼
3. משתמש בוחר פעולות עיבוד
   ├─ הוספת CutContour
   ├─ הוספת חורים
   ├─ קווי קיפול
   ├─ המרה ל-CMYK
   └─ שיפור תמונות
   │
   ▼
4. add_holes_and_cutcontour מעבד את הקובץ
   ├─ קריאת PDF המקורי
   ├─ יצירת שכבות נוספות
   ├─ הוספת אלמנטים גרפיים
   └─ שמירת PDF חדש
   │
   ▼
5. approval_sketch יוצר סקיצה לאישור (אופציונלי)
   ├─ תמונה ממוזערת
   ├─ פרטים טכניים
   └─ רשימת עיבודים
   │
   ▼
6. שמירת תוצאות
   ├─ PDF מעובד
   ├─ סקיצה לאישור
   └─ רישום בלוג השינויים
```

---

## 📊 מודל נתונים (Data Model)

```
┌─────────────────────────────────────────────────┐
│              PDF Document Model                 │
├─────────────────────────────────────────────────┤
│                                                  │
│  File Info:                                     │
│  ├─ path: str                                   │
│  ├─ size: int                                   │
│  └─ name: str                                   │
│                                                  │
│  Page Info:                                     │
│  ├─ width_mm: float                             │
│  ├─ height_mm: float                            │
│  ├─ page_count: int                             │
│  └─ rotation: int                               │
│                                                  │
│  Quality Info:                                  │
│  ├─ dpi: float                                  │
│  ├─ resolution: str                             │
│  ├─ colormode: str (RGB/CMYK/Gray)              │
│  ├─ is_pixelated: bool                          │
│  └─ has_vector: bool                            │
│                                                  │
│  Metadata:                                      │
│  ├─ title: str                                  │
│  ├─ author: str                                 │
│  ├─ creator: str                                │
│  ├─ producer: str                               │
│  └─ creation_date: str                          │
│                                                  │
│  Spot Layers:                                   │
│  ├─ has_cutcontour: bool                        │
│  ├─ has_crease: bool                            │
│  └─ custom_spots: list[str]                     │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 🔒 עקרונות עיצוב (Design Principles)

1. **Separation of Concerns**
   - שכבת UI מופרדת מלוגיקה עסקית
   - כל מודול ממלא תפקיד ספציפי

2. **Modularity**
   - רכיבים עצמאיים וניתנים לשימוש חוזר
   - ממשקים ברורים בין מודולים

3. **Configuration-Driven**
   - הגדרות מרוכזות ב-config.py
   - קל לשינוי והתאמה אישית

4. **External Tool Integration**
   - תמיכה במספר כלים חיצוניים
   - חיבור גמיש דרך wrappers

5. **User-Friendly**
   - GUI אינטואיטיבי
   - משוב ברור למשתמש
   - טיפול בשגיאות מקיף

---

## 🎨 UI Architecture (ארכיטקטורת ממשק משתמש)

```
PDFProcessorApp (Main Window)
├─ Header (כותרת)
│  └─ AI Summary Label
│
├─ Tabs (טאבים)
│  ├─ Tab 1: עיבוד ידני (Manual Processing)
│  │  ├─ File Selection
│  │  ├─ Settings Panel
│  │  │  ├─ Holes Settings
│  │  │  ├─ CutContour Settings
│  │  │  ├─ Crease Settings
│  │  │  └─ Processing Options
│  │  ├─ Preview Area
│  │  └─ Action Buttons
│  │
│  ├─ Tab 2: אוטומציה (Automation)
│  │  ├─ Folder Monitoring
│  │  ├─ Batch Processing
│  │  └─ Auto Settings
│  │
│  ├─ Tab 3: לוג שינויים (Changes Log)
│  │  ├─ Treeview (רשימת שינויים)
│  │  └─ Filter Options
│  │
│  └─ Tab 4: גלריית סקיצות (Sketches Gallery)
│     ├─ Thumbnails Grid
│     └─ Preview Panel
│
└─ Status Bar (סטטוס)
   └─ Progress Indicator
```

---

## 📝 סיכום

**PDF Processor Pro** בנוי עם ארכיטקטורה מודולרית ברורה:

✅ **שכבת Presentation** - GUI עם Tkinter  
✅ **שכבת Business Logic** - עיבוד וניתוח PDF  
✅ **שכבת Data** - אינטגרציה עם כלים חיצוניים  
✅ **שכבת Configuration** - הגדרות מרוכזות  

המבנה מאפשר:
- תחזוקה קלה
- הרחבה עתידית
- בדיקות יעילות
- שימוש חוזר בקוד
