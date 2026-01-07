# 📑 מפת הפרויקט - PDF Processor Pro v2.0

## 📁 מבנה התיקייה

```
pyton pdf/
├── 📄 קבצים ראשיים
│   ├── pdf_processor_gui.py        # אפליקציה ראשית עם GUI
│   ├── pdf_analysis.py             # ⭐ מודול הניתוח המקצועי (עודכן!)
│   ├── config.py                   # ⭐ הגדרות מערכת (עודכן!)
│   ├── automation.py               # מודול אוטומציה
│   ├── manual_processing.py        # עיבוד ידני
│   ├── ui_components.py            # רכיבי UI
│   ├── pdf_utils.py                # פונקציות עזר
│   └── add_holes_and_cutcontour.py # הוספת חורים וקו חיתוך
│
├── 📚 תיעוד
│   ├── README.md                   # ⭐ תיעוד ראשי מלא (עודכן!)
│   ├── SUMMARY.md                  # 🆕 סיכום השינויים
│   ├── QUICK_START.md              # 🆕 מדריך התחלה מהירה
│   ├── INSTALL.md                  # 🆕 הוראות התקנה
│   ├── CHANGES_LOG.md              # 🆕 יומן שינויים מפורט
│   └── requirements.txt            # 🆕 דרישות מערכת
│
├── 🔧 כלי עזר
│   ├── example_usage.py            # 🆕 דוגמאות שימוש מקיפות
│   ├── check_tools.py              # 🆕 בדיקת זמינות כלים
│   ├── changes_log.py              # מעקב אחר שינויים
│   ├── approval_sketch.py          # סקיצות אישור
│   └── sketches_gallery.py         # גלריית סקיצות
│
├── 📂 תיקיות
│   ├── autofiles/                  # קבצים לאוטומציה
│   ├── __pycache__/               # קבצי cache של Python
│   └── .venv/                     # סביבה וירטואלית
│
└── ⚙️ קבצי מערכת
    ├── .git/                       # Git repository
    └── .gitignore                  # Git ignore rules
```

---

## 🎯 מפתח מהיר

### מתחילים? התחל כאן:
1. [INSTALL.md](INSTALL.md) - התקן את המערכת
2. [check_tools.py](check_tools.py) - בדוק שהכל עובד
3. [QUICK_START.md](QUICK_START.md) - למד את הבסיס
4. [example_usage.py](example_usage.py) - ראה דוגמאות

### רוצה לדעת יותר?
- [README.md](README.md) - תיעוד מלא ומקיף
- [SUMMARY.md](SUMMARY.md) - סיכום מה השתנה
- [CHANGES_LOG.md](CHANGES_LOG.md) - פירוט מלא של השינויים

### רוצה לפתח?
- [pdf_analysis.py](pdf_analysis.py) - המודול המרכזי
- [config.py](config.py) - הגדרות מערכת
- [pdf_processor_gui.py](pdf_processor_gui.py) - הממשק הגרפי

---

## 📋 קבצים לפי קטגוריה

### 🔴 חובה לקרוא
- `INSTALL.md` - התקנה
- `README.md` - תיעוד
- `QUICK_START.md` - התחלה מהירה

### 🟡 מומלץ
- `example_usage.py` - דוגמאות
- `check_tools.py` - בדיקה
- `SUMMARY.md` - סיכום

### 🟢 מתקדמים
- `pdf_analysis.py` - קוד ליבה
- `config.py` - הגדרות
- `CHANGES_LOG.md` - שינויים מפורטים

### 🔵 משתמשים
- `pdf_processor_gui.py` - אפליקציה ראשית
- `automation.py` - אוטומציה
- `manual_processing.py` - עיבוד ידני

---

## 🗂 תיאור קבצים מפורט

### pdf_analysis.py - ⭐ המודול המרכזי
**מה יש בפנים:**
- `PDFAnalyzer` - ניתוח ומניפולציות (PyMuPDF)
- `PDFValidator` - בדיקות ותיקון (PDFToolbox)
- `PDFConverter` - המרות ואופטימיזציה (Ghostscript)

**שימוש:**
```python
from pdf_analysis import PDFAnalyzer, PDFValidator, PDFConverter
```

**גודל:** ~800 שורות  
**סטטוס:** עודכן ב-v2.0  
**תלות:** PyMuPDF (חובה), Ghostscript (מומלץ), PDFToolbox (אופציונלי)

---

### config.py - ⭐ הגדרות מערכת
**מה יש בפנים:**
- `COLORS` - סכמת צבעים
- `FONTS` - הגדרות גופנים
- `DEFAULT_VALUES` - ערכי ברירת מחדל
- `PDF_TOOLS_CONFIG` - הגדרות כלים מקצועיים
- `OPTIMIZATION_CONFIG` - הגדרות אופטימיזציה
- `CONVERSION_CONFIG` - הגדרות המרות
- `VALIDATION_CONFIG` - הגדרות בדיקות
- `LOGGING_CONFIG` - הגדרות לוגים

**שימוש:**
```python
from config import PDF_TOOLS_CONFIG, OPTIMIZATION_CONFIG
```

**גודל:** ~200 שורות  
**סטטוס:** עודכן ב-v2.0

---

### example_usage.py - 🆕 דוגמאות שימוש
**מה יש בפנים:**
- `example_pymupdf()` - דוגמאות PyMuPDF
- `example_pdftoolbox()` - דוגמאות PDFToolbox
- `example_ghostscript()` - דוגמאות Ghostscript
- `example_combined_workflow()` - תהליך עבודה משולב

**איך להריץ:**
```bash
python example_usage.py
```

**גודל:** ~400 שורות  
**סטטוס:** חדש ב-v2.0

---

### check_tools.py - 🆕 בדיקת כלים
**מה זה עושה:**
- בודק את PyMuPDF
- בודק את Ghostscript
- בודק את PDFToolbox
- בודק את קובץ ההגדרות
- בודק פונקציונליות בסיסית

**איך להריץ:**
```bash
python check_tools.py
```

**גודל:** ~250 שורות  
**סטטוס:** חדש ב-v2.0

---

### pdf_processor_gui.py - אפליקציה ראשית
**מה זה עושה:**
- ממשק גרפי מלא
- עיבוד אוטומטי וידני
- תצוגת קבצים
- הגדרות מפורטות

**איך להריץ:**
```bash
python pdf_processor_gui.py
```

**תלות:** tkinter, pdf_analysis, config

---

## 🎓 מסלולי למידה מומלצים

### למתחילים (30 דקות):
1. קרא [INSTALL.md](INSTALL.md)
2. הרץ `python check_tools.py`
3. קרא [QUICK_START.md](QUICK_START.md)
4. הרץ `python example_usage.py`

### למשתמשים (1 שעה):
1. קרא [README.md](README.md) - סעיפים 1-5
2. נסה את הדוגמאות מ-[QUICK_START.md](QUICK_START.md)
3. התנסה עם [pdf_processor_gui.py](pdf_processor_gui.py)

### למפתחים (2-3 שעות):
1. קרא [README.md](README.md) - תיעוד מלא
2. למד את [pdf_analysis.py](pdf_analysis.py)
3. התאם את [config.py](config.py)
4. קרא [CHANGES_LOG.md](CHANGES_LOG.md)

---

## 📊 סטטיסטיקות פרויקט

- **קבצי Python:** 13
- **קבצי תיעוד:** 6
- **סה"כ שורות קוד:** ~5,000+
- **מחלקות ראשיות:** 3 (PDFAnalyzer, PDFValidator, PDFConverter)
- **פונקציות:** 40+
- **כלים משולבים:** 3 (PyMuPDF, Ghostscript, PDFToolbox)

---

## 🔄 עדכונים אחרונים (v2.0)

**תאריך:** ינואר 2026

**קבצים חדשים:**
- ✅ example_usage.py
- ✅ check_tools.py
- ✅ SUMMARY.md
- ✅ QUICK_START.md
- ✅ INSTALL.md
- ✅ CHANGES_LOG.md
- ✅ requirements.txt

**קבצים עודכנו:**
- ✅ pdf_analysis.py - הוספו מחלקות PDFValidator ו-PDFConverter
- ✅ config.py - נוספו הגדרות מתקדמות
- ✅ README.md - תיעוד מלא וחדש

---

## 🎯 לסיכום

זהו מדריך מלא למבנה הפרויקט.  
מוצאים משהו? חפשו כאן!

**צריך עזרה?** התחילו מ-[QUICK_START.md](QUICK_START.md) 🚀
