"""
קובץ הגדרות עיצוב וצבעים עבור PDF Processor
"""

# סכמת צבעים מקצועית - עיצוב כהה מודרני
COLORS = {
    'primary': '#00BCD4',      # ציאן בהיר - כפתורים ראשיים
    'success': '#4CAF50',      # ירוק בהיר - הצלחה
    'warning': '#FF9800',      # כתום בהיר - אזהרה
    'danger': '#F44336',       # אדום בהיר - שגיאה
    'light_bg': '#2C2C2C',     # רקע אפור כהה ראשי
    'dark_bg': '#1E1E1E',      # רקע אפור כהה יותר
    'card_bg': '#353535',      # רקע כרטיסים/frames
    'dark_text': '#E0E0E0',    # טקסט בהיר על רקע כהה
    'light_text': '#B0B0B0',   # טקסט משני
    'border': '#4A4A4A',       # גבול
    'accent': '#7C4DFF',       # סגול - הדגשות
    'header_bg': '#1A1A1A'     # רקע כותרת כהה במיוחד
}

# הגדרות גופן
FONTS = {
    'title': ('Segoe UI', 24, 'bold'),
    'heading': ('Segoe UI', 11, 'bold'),
    'button': ('Segoe UI', 14, 'bold'),
    'label': ('Segoe UI', 10),
    'small': ('Segoe UI', 9),
    'treeview': ('Segoe UI', 9),
    'treeview_heading': ('Segoe UI', 10, 'bold'),
    'log': ('Consolas', 9),
    'summary': ('Segoe UI', 12, 'bold')
}

# הגדרות ברירת מחדל לעיבוד PDF
DEFAULT_VALUES = {
    'hole_diameter': 7.0,       # מ"מ
    'hole_margin': 20.0,        # מ"מ
    'artboard_margin': 2.0,     # מ"מ
    'stroke_width': 0.25,       # מ"מ
    'additional_margin': 0.0,   # מ"מ
    'enhance_images': False,
    'convert_to_cmyk': False,
    'add_cutcontour': True,
    'add_holes': True,
    'replace_crease': True,
    'add_margins': False
}

# הגדרות חלון ראשי
WINDOW_CONFIG = {
    'title': 'PDF Processor - Professional Edition',
    'width': 1200,
    'height': 900,
    'resizable': True
}

# הגדרות Treeview
TREEVIEW_CONFIG = {
    'theme': 'clam',
    'rowheight': 25,
    'columns': {
        'check': {'width': 50, 'text': '✓'},
        'name': {'width': 200, 'text': 'שם קובץ'},
        'resolution': {'width': 100, 'text': 'רזולוציה'},
        'dpi': {'width': 80, 'text': 'DPI'},
        'colormode': {'width': 100, 'text': 'מצב צבעים'},
        'pixelated': {'width': 100, 'text': 'פיקסול'},
        'cutcontour': {'width': 120, 'text': 'CutContour'},
        'crease': {'width': 100, 'text': 'Crease'},
        'holes': {'width': 100, 'text': 'Holes'}
    }
}

# הגדרות UI נוספות
UI_CONFIG = {
    'header_padding': 20,
    'frame_padding': 15,
    'button_padding': (30, 15),
    'border_width': 1,
    'relief': 'flat'
}
