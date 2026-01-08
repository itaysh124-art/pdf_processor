# מדריך שימוש במבנה החדש

## מה השתנה?

כל קוד המקור הועבר לתיקייה `pdf_processor/` למען ארגון טוב יותר ומבנה פרויקט תקני.

## איך להריץ את התוכנה?

### הרצת הממשק הגרפי
```bash
python run_gui.py
```

### בדיקת כלים זמינים
```bash
python check_tools.py
```

### שימוש בקוד (imports)

**לפני:**
```python
from pdf_analysis import PDFAnalyzer
from config import COLORS
```

**עכשיו:**
```python
from pdf_processor.pdf_analysis import PDFAnalyzer
from pdf_processor.config import COLORS
```

## מבנה התיקיות

```
pdf_processor/
├── run_gui.py              # הרצת GUI
├── check_tools.py          # בדיקת כלים
├── requirements.txt        # תלויות
├── *.md                    # תיעוד
└── pdf_processor/          # קוד המקור
    ├── *.py               # מודולים
    ├── gui/               # GUI נוסף
    └── processing/        # עיבוד
```

## שאלות נפוצות

**ש: איפה הקבצים שלי?**
ת: כל קבצי ה-Python עברו לתיקייה `pdf_processor/`. הם לא נמחקו!

**ש: איך אני מריץ את התוכנה?**
ת: השתמש ב-`python run_gui.py` או `python check_tools.py`

**ש: מה עם הקוד שלי שמשתמש בספרייה הזו?**
ת: עדכן את ה-imports שלך מ-`from pdf_analysis` ל-`from pdf_processor.pdf_analysis`

**ש: התיעוד עדכני?**
ת: כן! כל קבצי ה-MD עודכנו עם דוגמאות נכונות.
