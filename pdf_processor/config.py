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

# הגדרות כלים מקצועיים
PDF_TOOLS_CONFIG = {
    'pymupdf': {
        'enabled': True,
        'description': 'PyMuPDF (fitz) - חילוץ טקסט, ניתוח ומניפולציות בסיסיות'
    },
    'pdftoolbox': {
        'enabled': False,  # יופעל כאשר PDFToolbox מותקן
        'path': None,  # נתיב ל-PDFToolbox (יאותר אוטומטית)
        'description': 'PDFToolbox - validations, preflight ותיקון PDFs',
        'default_profile': 'PDF/X-4',
        'profiles': ['PDF/A-1b', 'PDF/A-2b', 'PDF/X-1a', 'PDF/X-3', 'PDF/X-4']
    },
    'ghostscript': {
        'enabled': True,  # ינסה לאתר אוטומטית
        'path': None,  # נתיב ל-Ghostscript (יאותר אוטומטית)
        'description': 'Ghostscript - המרות מורכבות, דחיסה ו-rendering',
        'quality_settings': {
            'screen': {'dpi': 72, 'description': 'איכות מסך (קובץ קטן)'},
            'ebook': {'dpi': 150, 'description': 'איכות ספר אלקטרוני'},
            'printer': {'dpi': 300, 'description': 'איכות הדפסה (מומלץ)'},
            'prepress': {'dpi': 300, 'description': 'איכות דפוס (שמירת צבעים)'},
            'default': {'dpi': 300, 'description': 'ברירת מחדל'}
        },
        'default_quality': 'printer'
    }
}

# הגדרות אופטימיזציה ודחיסה
OPTIMIZATION_CONFIG = {
    'auto_optimize': False,
    'compress_images': True,
    'image_quality': 85,  # 1-100
    'downsample_images': False,
    'target_dpi': 300,
    'remove_unused_resources': True,
    'linearize': False  # Fast Web View
}

# הגדרות המרות
CONVERSION_CONFIG = {
    'pdfa': {
        'enabled': True,
        'default_version': '2b',  # 1b, 2b, 3b
        'embed_fonts': True,
        'compress': True
    },
    'pdfx': {
        'enabled': True,
        'default_version': 'X-4',  # X-1a, X-3, X-4
        'output_intent': 'Coated FOGRA39'
    },
    'image_export': {
        'formats': ['png', 'jpg', 'tiff'],
        'default_format': 'png',
        'default_dpi': 300,
        'default_quality': 95  # עבור JPEG
    }
}

# הגדרות Validation
VALIDATION_CONFIG = {
    'check_on_load': False,
    'auto_fix': False,
    'validation_rules': {
        'check_fonts': True,
        'check_images': True,
        'check_colors': True,
        'check_transparency': True,
        'check_bleed': False,
        'check_trim_box': False
    },
    'max_file_size_mb': 500,  # גודל מקסימלי לבדיקה
    'timeout_seconds': 60
}

# הגדרות לוגים ודיווחים
LOGGING_CONFIG = {
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'log_to_file': True,
    'log_directory': 'logs',
    'max_log_size_mb': 10,
    'backup_count': 5,
    'report_format': 'html',  # html, txt, json
    'save_reports': True,
    'reports_directory': 'reports'
}
