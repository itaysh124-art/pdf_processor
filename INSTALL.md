# התקנה מהירה - PDF Processor Pro

## שלב 1: התקנת Python (אם אין)
הורד מ: https://www.python.org/downloads/
גרסה מינימלית: Python 3.8+

## שלב 2: התקנת PyMuPDF (חובה)
```bash
pip install PyMuPDF
```

## שלב 3: התקנת Ghostscript (מומלץ מאוד)

### Windows:
1. הורד מ: https://github.com/ArtifexSoftware/ghostpdl-downloads/releases
2. בחר את הקובץ המתאים:
   - `gs10.04.0-win64.exe` (64-bit)
   - `gs10.04.0-win32.exe` (32-bit)
3. הרץ את המתקין
4. במהלך ההתקנה, סמן "Add to PATH"

### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install ghostscript
```

### macOS:
```bash
brew install ghostscript
```

## שלב 4: בדיקת ההתקנה
```bash
cd "c:\Users\itay\OneDrive\Visual Studio Code\scripts\pyton pdf"
python check_tools.py
```

## שלב 5: הרצת דוגמאות
```bash
python example_usage.py
```

## פתרון בעיות

### Python לא נמצא
- וודא ש-Python מותקן ונמצא ב-PATH
- הרץ: `python --version`

### PyMuPDF לא מותקן
```bash
pip install --upgrade PyMuPDF
```

### Ghostscript לא נמצא
#### Windows:
1. מצא את נתיב ההתקנה (בדרך כלל):
   `C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe`
2. הוסף את התיקייה ל-PATH במשתני סביבה

#### בדיקה ידנית:
```bash
# Windows
gswin64c --version

# Linux/Mac
gs --version
```

### הגדרה ידנית של נתיבים
ערוך את `config.py`:
```python
PDF_TOOLS_CONFIG = {
    'ghostscript': {
        'path': r'C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe'
    }
}
```

## מוכן! 🎉
אם כל הבדיקות עברו בהצלחה, המערכת מוכנה לשימוש.

הרץ את האפליקציה הראשית:
```bash
python pdf_processor_gui.py
```
