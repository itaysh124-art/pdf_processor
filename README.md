# PDF Processor Pro - מבנה הפרויקט

## סקירה כללית
מערכת מקצועית לעיבוד קבצי PDF עם אוטומציה מלאה. המערכת מאפשרת הוספת שכבות Spot Color, חורים, קווי חיתוך וקיפול, והמרה ל-CMYK.

## מבנה הקבצים

### 📄 `pdf_processor_gui.py`
**הקובץ הראשי** - מכיל את האפליקציה המלאה ומשמש כנקודת כניסה למערכת.

### 🎨 `config.py`
**הגדרות עיצוב וקונפיגורציה**
- סכמת צבעים (COLORS)
- הגדרות גופנים (FONTS)
- ערכי ברירת מחדל (DEFAULT_VALUES)
- הגדרות חלון (WINDOW_CONFIG)
- הגדרות Treeview (TREEVIEW_CONFIG)

```python
from config import COLORS, FONTS, DEFAULT_VALUES
```

### 🤖 `automation.py`
**מודול אוטומציה**
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
