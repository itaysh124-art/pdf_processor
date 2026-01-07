import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import sys

# הוספת תיקיית השורש ל-path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading
import time
import shutil
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import CMYKColorSep
import fitz  # PyMuPDF - לקריאת מידע ואנליזה
from pypdf import PdfReader, PdfWriter  # למניפולציה של PDF
from pypdf.generic import ContentStream, NameObject, DictionaryObject, RectangleObject
import re
import glob
import io
import cv2
import numpy as np
from skimage import restoration, filters

# ייבוא מודולים מותאמים אישית
from gui.ui_components import ToggleSwitch
from core.pdf_analysis import PDFAnalyzer
from gui.approval_sketch import create_approval_sketch, get_sketch_settings
from gui.changes_log import ChangesLogTab
from gui.sketches_gallery import SketchesGalleryTab
from processing.crop_marks_remover import CropMarksRemover

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
try:
    from realesrgan import RealESRGAN
    REALESRGAN_AVAILABLE = True
    import torch
except ImportError:
    REALESRGAN_AVAILABLE = False

class PDFProcessorApp:
    def detect_spot_layer(self, pdf_path, spot_name):
        """זיהוי שכבת Spot Color ב-PDF - משתמש ב-PDFAnalyzer"""
        return PDFAnalyzer.detect_spot_layer(pdf_path, spot_name)
    
    def detect_cropmarks_status(self, pdf_path):
        """ביטול זיהוי cropmarks - מחזיר ערך ריק"""
        return ""
    
    def update_ai_summary(self, total_files, pixelated_count, low_quality_count, duplicate_count, error_count):
        """Show AI summary of file stats at the top of the GUI."""
        if not hasattr(self, 'ai_summary_label'):
            self.ai_summary_label = tk.Label(self.root, text='', font=("Arial", 12, "bold"), fg=self.colors['primary'], bg=self.colors['light_bg'], anchor='w', justify='left')
            self.ai_summary_label.pack(fill="x", pady=(5, 0))
        summary = f"סך קבצים: {total_files} | כפולים: {duplicate_count} | מפוקסלים: {pixelated_count} | איכות ירודה: {low_quality_count} | שגיאות: {error_count}"
        self.ai_summary_label.config(text=summary)
    
    def show_mixed_folders_warning(self, folders):
        """הצגת התראה על קבצים מתיקיות שונות"""
        if not hasattr(self, 'mixed_folders_warning'):
            self.mixed_folders_warning = tk.Frame(self.root, bg=self.colors['warning'], pady=10, padx=15)
            
            warning_text = tk.Label(
                self.mixed_folders_warning,
                text="⚠️ אזהרה: הקבצים נטענו מתיקיות שונות!",
                font=("Arial", 12, "bold"),
                fg="white",
                bg=self.colors['warning']
            )
            warning_text.pack(side="left", padx=(0, 10))
            
            self.folders_detail_label = tk.Label(
                self.mixed_folders_warning,
                text="",
                font=("Arial", 10),
                fg="white",
                bg=self.colors['warning'],
                anchor="w"
            )
            self.folders_detail_label.pack(side="left", fill="x", expand=True)
            
        # עדכון רשימת התיקיות
        folders_text = "תיקיות: " + " | ".join(folders)
        self.folders_detail_label.config(text=folders_text)
        
        # הצגת ההתראה
        if not self.mixed_folders_warning.winfo_ismapped():
            self.mixed_folders_warning.pack(fill="x", after=self.ai_summary_label if hasattr(self, 'ai_summary_label') else None)
    
    def hide_mixed_folders_warning(self):
        """הסתרת התראת תיקיות מעורבות"""
        if hasattr(self, 'mixed_folders_warning'):
            self.mixed_folders_warning.pack_forget()
    def get_smart_recommendations(self, pdf_info):
        """Return automatic recommendations for file quality and print optimization."""
        recs = []
        dpi = pdf_info.get('dpi', None)
        colormode = pdf_info.get('colormode', None)
        pixelated = pdf_info.get('pixelated', '')
        # DPI recommendation
        if dpi and dpi != "N/A":
            try:
                dpi_val = int(dpi)
                if dpi_val < 150:
                    recs.append("🔴 מומלץ להגדיל רזולוציה (DPI נמוך)")
                elif dpi_val < 300:
                    recs.append("🟠 כדאי לשפר רזולוציה ל-300 DPI להדפסה מקצועית")
                else:
                    recs.append("🟢 רזולוציה טובה להדפסה")
            except:
                pass
        # Color mode recommendation
        if colormode == "RGB":
            recs.append("🟠 מומלץ להמיר ל-CMYK להדפסה")
        elif colormode == "CMYK":
            recs.append("🟢 מצב צבעים תקין להדפסה")
        elif colormode == "N/A":
            recs.append("⚠ לא זוהה מצב צבעים - בדוק את הקובץ")
        # Pixelation
        if "✗ מפוקסל" in pixelated:
            recs.append("🔴 יש תמונות מפוקסלות - מומלץ לשפר איכות")
        elif "⚠ בינוני" in pixelated:
            recs.append("🟠 איכות תמונה בינונית - אפשר לשפר")
        elif "✓ איכותי" in pixelated:
            recs.append("🟢 איכות תמונה טובה")
        return recs
    def analyze_image_quality(self, pil_image):
        """Analyze image quality using AI: sharpness, noise, resolution."""
        img = np.array(pil_image.convert('L'))
        # Sharpness: variance of Laplacian
        sharpness = cv2.Laplacian(img, cv2.CV_64F).var()
        # Noise: estimate using wavelet
        noise = restoration.estimate_sigma(img, multichannel=False)
        # Resolution: pixels per inch
        dpi = pil_image.info.get('dpi', (72, 72))[0]
        return {
            'sharpness': sharpness,
            'noise': noise,
            'dpi': dpi
        }

    def enhance_image_ai(self, pil_image):
        """Enhance image using AI: upscaling and denoising."""
        img = np.array(pil_image)
        # Denoise
        img_denoised = restoration.denoise_wavelet(img, multichannel=True, convert2ycbcr=True, mode='soft')
        img_denoised = (img_denoised * 255).astype(np.uint8)
        pil_denoised = Image.fromarray(img_denoised)
        # Upscale (if realesrgan available)
        if REALESRGAN_AVAILABLE:
            try:
                model = RealESRGAN('cuda' if torch.cuda.is_available() else 'cpu', scale=2)
                model.load_weights('RealESRGAN_x2.pth', download=True)
                upscaled = model.predict(pil_denoised)
                return upscaled
            except Exception as e:
                print(f"[AI] RealESRGAN failed: {e}")
        # Fallback: resize with PIL
        upscaled = pil_denoised.resize((pil_denoised.width*2, pil_denoised.height*2), Image.LANCZOS)
        return upscaled
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Processor - Professional Edition")
        self.root.geometry("1400x820")
        self.root.resizable(True, True)
        
        # הגדרת encoding לעברית
        try:
            if sys.platform == 'win32':
                import locale
                try:
                    locale.setlocale(locale.LC_ALL, 'he_IL.UTF-8')
                except:
                    try:
                        locale.setlocale(locale.LC_ALL, 'Hebrew_Israel.1255')
                    except:
                        pass
        except:
            pass
        
        # סכמת צבעים מקצועית - עיצוב כהה מודרני
        self.colors = {
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
        # הגדרת רקע
        self.root.configure(bg=self.colors['light_bg'])
        
        # הגדרת סגנון Treeview
        style = ttk.Style()
        style.theme_use('clam')  # נושא שמספק שליטה טובה יותר
        style.configure('Treeview.Heading', 
                       font=('Arial', 10, 'bold'),
                       background=self.colors['dark_bg'],
                       foreground=self.colors['dark_text'],
                       relief='flat',
                       borderwidth=1)
        style.configure('Treeview',
                       font=('Arial', 9),
                       rowheight=25,
                       background=self.colors['card_bg'],
                       foreground=self.colors['dark_text'],
                       fieldbackground=self.colors['card_bg'])
        style.map('Treeview.Heading',
                 background=[('active', self.colors['primary'])])
        style.map('Treeview',
                 background=[('selected', self.colors['primary'])],
                 foreground=[('selected', 'white')])
        
        # משתנים
        self.input_files = []
        self.all_tree_items = []  # שמירת כל השורות המקוריות לצורך מסננים
        self.all_tree_items_dict = {}  # מילון של כל הפריטים לפי ID
        
        # משתני אוטומציה
        self.automation_active = False
        self.automation_thread = None
        self.watch_folder = tk.StringVar(value="")
        self.automation_output_folder = tk.StringVar(value="")
        self.automation_error_folder = tk.StringVar(value="")
        self.processed_files = set()  # קבצים שכבר עובדו
        
        self.station_name = tk.StringVar(value="")  # שם התחנה
        self.order_number = tk.StringVar(value="")  # מספר הזמנה
        self.output_folder = tk.StringVar(value="")  # ריק = תיקיית המקור
        self.production_folder = tk.StringVar(value="")  # תיקיית ייצור לקבצים מאושרים
        self.hole_diameter = tk.DoubleVar(value=7.0)
        self.hole_margin = tk.DoubleVar(value=20.0)
        self.holes_position = tk.StringVar(value="page")  # "page" או "graphic"
        self.artboard_margin = tk.DoubleVar(value=2.0)
        self.stroke_width = tk.DoubleVar(value=0.25)
        self.additional_margin = tk.DoubleVar(value=0.0)  # שוליים נוספים
        self.enhance_images = tk.BooleanVar(value=False)
        self.convert_to_cmyk = tk.BooleanVar(value=False)
        # אפשרויות שכבות
        self.add_cutcontour = tk.BooleanVar(value=True)
        self.add_holes = tk.BooleanVar(value=True)
        self.replace_crease = tk.BooleanVar(value=True)
        self.add_margins = tk.BooleanVar(value=False)  # הוספת שוליים לבנים
        self.sketch_mode = tk.BooleanVar(value=False)  # מצב סקיצה לאישור לקוח
        self.remove_crop_marks = tk.BooleanVar(value=True)  # הסרת crop marks - מופעל כברירת מחדל
        self.create_widgets()

    def create_widgets(self):
        # Header Frame - קומפקטי יותר
        header_frame = tk.Frame(self.root, bg=self.colors['header_bg'], pady=4)
        header_frame.pack(fill="x")
        
        # לוגו קטן בפינה
        logo_frame = tk.Frame(header_frame, bg=self.colors['header_bg'])
        logo_frame.pack(side="left", padx=8)
        title_label = tk.Label(
            logo_frame, 
            text="⚡ PDF Pro | CutContour & Layers", 
            font=("Arial", 13, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['header_bg']
        )
        title_label.pack()
        
        # שדות שם התחנה ומספר הזמנה - בצד ימין של ההדר
        station_order_frame = tk.Frame(header_frame, bg=self.colors['header_bg'])
        station_order_frame.pack(side="right", padx=10)
        
        # שם התחנה
        tk.Label(
            station_order_frame,
            text="🏭 תחנה:",
            font=("Arial", 9, "bold"),
            fg=self.colors['dark_text'],
            bg=self.colors['header_bg']
        ).pack(side="right", padx=(0, 3))
        
        station_entry = tk.Entry(
            station_order_frame,
            textvariable=self.station_name,
            font=("Arial", 9),
            width=12,
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            insertbackground=self.colors['primary'],
            relief="flat",
            bd=2
        )
        station_entry.pack(side="right", padx=(0, 10))
        
        # מספר הזמנה
        tk.Label(
            station_order_frame,
            text="📋 הזמנה:",
            font=("Arial", 9, "bold"),
            fg=self.colors['dark_text'],
            bg=self.colors['header_bg']
        ).pack(side="right", padx=(0, 3))
        
        order_entry = tk.Entry(
            station_order_frame,
            textvariable=self.order_number,
            font=("Arial", 9),
            width=12,
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            insertbackground=self.colors['primary'],
            relief="flat",
            bd=2
        )
        order_entry.pack(side="right")
        
        # Notebook for tabs
        notebook = ttk.Notebook(self.root)
        
        # סגנון Notebook
        style = ttk.Style()
        style.configure('TNotebook', background=self.colors['light_bg'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=self.colors['dark_bg'],
                       foreground=self.colors['light_text'],
                       padding=[12, 4],
                       font=('Arial', 9, 'bold'))
        style.map('TNotebook.Tab',
                 background=[('selected', self.colors['card_bg'])],
                 foreground=[('selected', self.colors['primary'])])
        
        notebook.pack(fill="both", expand=True, padx=4, pady=2)
        
        # Tab 1: Manual Processing
        manual_tab = tk.Frame(notebook, bg=self.colors['light_bg'])
        notebook.add(manual_tab, text="✅ עיבוד ידני")
        
        # Tab 2: Automation
        automation_tab = tk.Frame(notebook, bg=self.colors['light_bg'])
        notebook.add(automation_tab, text="🤖 אוטומציה")
        
        # Tab 3: Changes Log
        changes_log_tab = tk.Frame(notebook, bg=self.colors['light_bg'])
        notebook.add(changes_log_tab, text="📋 יומן שינויים")
        
        # יצירת אובייקט יומן שינויים
        self.changes_log_ui = ChangesLogTab(changes_log_tab, self.colors)
        
        # Tab 4: Sketches Gallery
        sketches_tab = tk.Frame(notebook, bg=self.colors['light_bg'])
        notebook.add(sketches_tab, text="📸 סקיצות")
        
        # יצירת אובייקט גלריית סקיצות
        self.sketches_gallery_ui = SketchesGalleryTab(sketches_tab, self.colors, self)
        
        # Main Container - ללא גלילה, הכל במסך אחד
        main_container = tk.Frame(manual_tab, bg=self.colors['light_bg'])
        main_container.pack(fill="both", expand=True, padx=4, pady=2)
        # פאנל שמאלי - קבצים ותיקיות
        left_panel = tk.Frame(main_container, bg=self.colors['light_bg'])
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 2))
        
        # בחירת קבצים
        file_frame = tk.LabelFrame(
            left_panel, 
            text=" 📁 קבצי PDF ",
            font=("Arial", 9, "bold"),
            padx=4,
            pady=2,
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="flat",
            borderwidth=1
        )
        file_frame.pack(fill="both", expand=True, pady=(0, 2))
        # כפתורי בחירה
        buttons_frame = tk.Frame(file_frame, bg=self.colors['card_bg'])
        buttons_frame.pack(fill="x", pady=(0, 2))
        browse_files_btn = tk.Button(
            buttons_frame, 
            text="📄 קבצים", 
            command=self.browse_files,
            bg=self.colors['success'],
            fg="white",
            font=("Arial", 9, "bold"),
            padx=6,
            pady=2,
            relief="flat",
            cursor="hand2",
            activebackground="#2E7D32"
        )
        browse_files_btn.pack(side="left", padx=2)
        browse_folder_btn = tk.Button(
            buttons_frame, 
            text="📁 תיקייה", 
            command=self.browse_folder,
            bg=self.colors['primary'],
            fg="white",
            font=("Arial", 9, "bold"),
            padx=6,
            pady=2,
            relief="flat",
            cursor="hand2",
            activebackground="#1565C0"
        )
        browse_folder_btn.pack(side="left", padx=2)
        clear_btn = tk.Button(
            buttons_frame, 
            text="🗑️ נקה", 
            command=self.clear_files,
            bg=self.colors['danger'],
            fg="white",
            font=("Arial", 9, "bold"),
            padx=6,
            pady=2,
            relief="flat",
            cursor="hand2",
            activebackground="#C62828"
        )
        clear_btn.pack(side="left", padx=2)
        
        # רשימת קבצים - שימוש ב-Treeview במקום Listbox
        list_frame = tk.Frame(file_frame, bg=self.colors['card_bg'])
        list_frame.pack(fill="both", expand=True, pady=(0, 6))
        # יצירת Treeview עם עמודות (עם checkbox)
        columns = ('selected', 'name', 'quantity', 'resolution', 'dpi', 'colormode', 'vector', 'pixelated', 'cutcontour', 'crease', 'holes')
        self.files_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=12,
            selectmode='extended'
        )
        # משתנים למסננים
        self.column_filters = {}
        
        # הגדרת כותרות עם מסננים
        self.files_tree.heading('selected', text='☑', command=self.toggle_all_checkboxes)
        self.files_tree.heading('name', text='שם הקובץ ▼', command=lambda: self.show_column_filter('name'))
        self.files_tree.heading('quantity', text='כמות')
        self.files_tree.heading('resolution', text='מידה (מ"מ) ▼', command=lambda: self.show_column_filter('resolution'))
        self.files_tree.heading('dpi', text='DPI ▼', command=lambda: self.show_column_filter('dpi'))
        self.files_tree.heading('colormode', text='מצב צבעים ▼', command=lambda: self.show_column_filter('colormode'))
        self.files_tree.heading('vector', text='Vector ▼', command=lambda: self.show_column_filter('vector'))
        self.files_tree.heading('pixelated', text='איכות ▼', command=lambda: self.show_column_filter('pixelated'))
        self.files_tree.heading('cutcontour', text='קו חיתוך ▼', command=lambda: self.show_column_filter('cutcontour'))
        self.files_tree.heading('crease', text='קו קיפול ▼', command=lambda: self.show_column_filter('crease'))
        self.files_tree.heading('holes', text='חורים ▼', command=lambda: self.show_column_filter('holes'))
        # הגדרת רוחב עמודות - רוחב מינימלי בלבד, דינאמי לפי תוכן
        self.files_tree.column('selected', minwidth=30, width=30, anchor='center', stretch=False)
        self.files_tree.column('name', minwidth=100, width=100, anchor='w', stretch=True)
        self.files_tree.column('quantity', minwidth=50, width=50, anchor='center', stretch=False)
        self.files_tree.column('resolution', minwidth=70, width=70, anchor='center', stretch=True)
        self.files_tree.column('dpi', minwidth=50, width=50, anchor='center', stretch=True)
        self.files_tree.column('colormode', minwidth=70, width=70, anchor='center', stretch=True)
        self.files_tree.column('vector', minwidth=60, width=60, anchor='center', stretch=True)
        self.files_tree.column('pixelated', minwidth=80, width=80, anchor='center', stretch=True)
        self.files_tree.column('cutcontour', minwidth=80, width=80, anchor='center', stretch=True)
        self.files_tree.column('crease', minwidth=80, width=80, anchor='center', stretch=True)
        self.files_tree.column('holes', minwidth=80, width=80, anchor='center', stretch=True)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        self.files_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # קישור גלילת עכבר ל-Treeview - עם עצירת event propagation
        def tree_mousewheel(event):
            self.files_tree.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"  # עצירת העברת האירוע ל-Canvas הראשי
        self.files_tree.bind("<MouseWheel>", tree_mousewheel)
        
        # קישור לחיצה לשינוי checkbox
        self.files_tree.bind('<Button-1>', self.on_tree_click)
        # קישור דאבל קליק לפתיחת תצוגה מקדימה
        self.files_tree.bind('<Double-Button-1>', self.on_tree_double_click)
        # תווית מספר קבצים - Frame עם תוויות מרובות
        count_frame = tk.Frame(file_frame, bg=self.colors['card_bg'])
        count_frame.pack(pady=5)
        
        self.files_total_label = tk.Label(
            count_frame,
            text="0 קבצים ברשימה",
            font=("Arial", 10, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['card_bg']
        )
        self.files_total_label.pack(side="left")
        
        # כפתור ביטול מסננים
        self.clear_filters_btn = tk.Button(
            count_frame,
            text="✗ בטל מסננים",
            command=self.clear_all_filters,
            bg=self.colors['dark_bg'],
            fg=self.colors['dark_text'],
            font=("Arial", 8),
            padx=8,
            pady=2,
            relief="flat",
            borderwidth=1,
            cursor="hand2"
        )
        self.clear_filters_btn.pack(side="left", padx=10)
        
        self.files_separator_label = tk.Label(
            count_frame,
            text=" | ",
            font=("Arial", 10),
            fg=self.colors['light_text'],
            bg=self.colors['card_bg']
        )
        
        self.files_pixelated_label = tk.Label(
            count_frame,
            text="",
            font=("Arial", 10, "bold"),
            fg=self.colors['warning'],
            bg=self.colors['card_bg']
        )
        
        self.files_duplicate_separator_label = tk.Label(
            count_frame,
            text=" | ",
            font=("Arial", 10),
            fg=self.colors['light_text'],
            bg=self.colors['card_bg']
        )
        
        self.files_duplicate_label = tk.Label(
            count_frame,
            text="",
            font=("Arial", 10, "bold"),
            fg=self.colors['accent'],
            bg=self.colors['card_bg']
        )
        
        self.files_error_separator_label = tk.Label(
            count_frame,
            text=" | ",
            font=("Arial", 10),
            fg=self.colors['dark_text'], bg=self.colors['card_bg']
        )
        self.files_error_label = tk.Label(
            count_frame,
            text="",
            font=("Arial", 10, "bold"),
            fg=self.colors['danger'], bg=self.colors['card_bg']
        )
        # תיקיית יעד
        output_frame = tk.LabelFrame(
            left_panel,
            text=" 💾 תיקיית יעד ",
            font=("Arial", 9, "bold"),
            padx=4,
            pady=2, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        output_frame.pack(fill="x", pady=(0, 2))
        output_entry_frame = tk.Frame(output_frame, bg=self.colors['card_bg'])
        output_entry_frame.pack(fill="x")
        output_entry = tk.Entry(
            output_entry_frame,
            textvariable=self.output_folder,
            font=("Arial", 9),
            relief="solid",
            borderwidth=1
        )
        output_entry.pack(side="left", padx=(0, 2), fill="x", expand=True)
        browse_output_btn = tk.Button(
            output_entry_frame, 
            text="📁", 
            command=self.browse_output_folder,
            bg=self.colors['warning'],
            fg="white",
            font=("Arial", 9, "bold"),
            padx=6,
            pady=2,
            relief="flat",
            cursor="hand2",
            activebackground="#E64A19"
        )
        browse_output_btn.pack(side="left", padx=(0, 2))
        clear_output_btn = tk.Button(
            output_entry_frame, 
            text="✖", 
            command=self.clear_output_folder,
            bg=self.colors['danger'],
            fg="white",
            font=("Arial", 9, "bold"),
            width=3,
            pady=2,
            relief="flat",
            cursor="hand2",
            activebackground="#C62828"
        )
        clear_output_btn.pack(side="left")
        
        # תיקיית ייצור (לקבצים מאושרים)
        production_frame = tk.LabelFrame(
            left_panel, 
            text=" 🏭 ייצור ",
            font=("Arial", 9, "bold"),
            fg=self.colors['success'],
            bg=self.colors['card_bg'],
            relief="solid",
            borderwidth=1,
            padx=4,
            pady=2
        )
        production_frame.pack(fill="x", pady=(0, 2))
        production_entry_frame = tk.Frame(production_frame, bg=self.colors['card_bg'])
        production_entry_frame.pack(fill="x")
        production_entry = tk.Entry(
            production_entry_frame,
            textvariable=self.production_folder,
            font=("Arial", 9),
            relief="solid",
            borderwidth=1
        )
        production_entry.pack(side="left", padx=(0, 2), fill="x", expand=True)
        browse_production_btn = tk.Button(
            production_entry_frame,
            text="📁",
            command=self.browse_production_folder,
            bg=self.colors['success'],
            fg="white",
            font=("Arial", 9, "bold"),
            padx=6,
            pady=2,
            relief="flat",
            cursor="hand2"
        )
        browse_production_btn.pack(side="left", padx=(0, 2))
        clear_production_btn = tk.Button(
            production_entry_frame,
            text="✖",
            command=self.clear_production_folder,
            bg=self.colors['danger'],
            fg="white",
            font=("Arial", 9, "bold"),
            width=3,
            pady=2,
            relief="flat",
            cursor="hand2"
        )
        clear_production_btn.pack(side="left")
        
        # פאנל ימני - הגדרות
        right_panel = tk.Frame(main_container, bg=self.colors['light_bg'])
        right_panel.pack(side="right", fill="both", expand=True, padx=(2, 0))
        
        # Grid להגדרות
        settings_container = tk.Frame(right_panel, bg=self.colors['light_bg'])
        settings_container.pack(fill="both", expand=True)
        # הגדרות חורים
        holes_frame = tk.LabelFrame(
            settings_container,
            text=" 🕳️ חורים ",
            font=("Arial", 9, "bold"),
            padx=4,
            pady=2, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        holes_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=(0, 2))
        
        # הפעלה/כיבוי יצירת חורים
        holes_enable_frame = tk.Frame(holes_frame, bg=self.colors['card_bg'])
        holes_enable_frame.grid(row=0, column=0, columnspan=2, sticky="w", padx=2, pady=(0, 4))
        
        holes_enable_toggle = ToggleSwitch(
            holes_enable_frame,
            variable=self.add_holes,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        )
        holes_enable_toggle.pack(side="left", padx=(0, 5))
        
        tk.Label(
            holes_enable_frame,
            text="הפעל",
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            font=("Arial", 9, "bold")
        ).pack(side="left")
        
        # מיקום חורים - בפינות העמוד או הגרפיקה
        tk.Label(holes_frame, text="מיקום:", bg=self.colors['card_bg'], fg=self.colors['dark_text'], font=("Arial", 9)).grid(row=1, column=0, sticky="e", padx=2, pady=2)
        position_frame = tk.Frame(holes_frame, bg=self.colors['card_bg'])
        position_frame.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        
        tk.Radiobutton(
            position_frame,
            text="עמוד",
            variable=self.holes_position,
            value="page",
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            selectcolor=self.colors['card_bg'],
            font=("Arial", 9)
        ).pack(side="left", padx=(0, 5))
        
        tk.Radiobutton(
            position_frame,
            text="גרפיקה",
            variable=self.holes_position,
            value="graphic",
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            selectcolor=self.colors['card_bg'],
            font=("Arial", 9)
        ).pack(side="left")
        
        # קוטר חור
        tk.Label(holes_frame, text="קוטר (מ\"מ):", bg=self.colors['card_bg'], fg=self.colors['dark_text'], font=("Arial", 9)).grid(row=2, column=0, sticky="e", padx=2, pady=2)
        diameter_spinbox = tk.Spinbox(
            holes_frame, 
            from_=1.0, 
            to=50.0, 
            increment=0.5,
            textvariable=self.hole_diameter,
            width=8,
            font=("Arial", 9)
        )
        diameter_spinbox.grid(row=2, column=1, sticky="w", padx=2, pady=2)
        
        # מרחק מגבול
        tk.Label(holes_frame, text="מרחק (מ\"מ):", bg=self.colors['card_bg'], fg=self.colors['dark_text'], font=("Arial", 9)).grid(row=3, column=0, sticky="e", padx=2, pady=2)
        margin_spinbox = tk.Spinbox(
            holes_frame, 
            from_=5.0, 
            to=100.0, 
            increment=1.0,
            textvariable=self.hole_margin,
            width=8,
            font=("Arial", 9)
        )
        margin_spinbox.grid(row=3, column=1, sticky="w", padx=2, pady=2)
        # הגדרות נוספות
        settings_frame = tk.LabelFrame(
            settings_container,
            text=" ⚙️ נוספות ",
            font=("Arial", 9, "bold"),
            padx=4,
            pady=2, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        settings_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=(0, 2))
        # מרווח Artboard
        tk.Label(settings_frame, text="Artboard:", bg=self.colors['card_bg'], font=("Arial", 9)).grid(row=0, column=0, sticky="e", padx=2, pady=2)
        artboard_spinbox = tk.Spinbox(
            settings_frame, 
            from_=0.0, 
            to=20.0, 
            increment=0.5,
            textvariable=self.artboard_margin,
            width=6,
            font=("Arial", 9)
        )
        artboard_spinbox.grid(row=0, column=1, sticky="w", padx=2, pady=2)
        # עובי Stroke
        tk.Label(settings_frame, text="Stroke:", bg=self.colors['card_bg'], font=("Arial", 9)).grid(row=1, column=0, sticky="e", padx=2, pady=2)
        stroke_spinbox = tk.Spinbox(
            settings_frame, 
            from_=0.1, 
            to=2.0, 
            increment=0.05,
            textvariable=self.stroke_width,
            width=6,
            font=("Arial", 9)
        )
        stroke_spinbox.grid(row=1, column=1, sticky="w", padx=2, pady=2)
        
        # שיפור איכות תמונות
        enhance_frame = tk.Frame(settings_frame, bg=self.colors['card_bg'])
        enhance_frame.grid(row=2, column=0, columnspan=2, sticky="w", padx=2, pady=3)
        
        enhance_toggle = ToggleSwitch(
            enhance_frame,
            variable=self.enhance_images,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        )
        enhance_toggle.pack(side="left", padx=(0, 4))
        
        tk.Label(
            enhance_frame,
            text="🎯 DPI+CMYK",
            bg=self.colors['card_bg'],
            font=("Arial", 9, "bold"),
            fg=self.colors['dark_text']
        ).pack(side="left")
        
        # המרה ל-CMYK
        cmyk_frame = tk.Frame(settings_frame, bg=self.colors['card_bg'])
        cmyk_frame.grid(row=3, column=0, columnspan=2, sticky="w", padx=2, pady=3)
        
        cmyk_toggle = ToggleSwitch(
            cmyk_frame,
            variable=self.convert_to_cmyk,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        )
        cmyk_toggle.pack(side="left", padx=(0, 4))
        
        tk.Label(
            cmyk_frame,
            text="🎨 RGB>CMYK",
            bg=self.colors['card_bg'],
            font=("Arial", 9, "bold"),
            fg=self.colors['dark_text']
        ).pack(side="left")
        
        # סקיצה לאישור לקוח
        sketch_frame = tk.Frame(settings_frame, bg=self.colors['card_bg'])
        sketch_frame.grid(row=4, column=0, columnspan=2, sticky="w", padx=2, pady=3)
        
        sketch_toggle = ToggleSwitch(
            sketch_frame,
            variable=self.sketch_mode,
            on_color=self.colors['warning'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        )
        sketch_toggle.pack(side="left", padx=(0, 4))
        
        tk.Label(
            sketch_frame,
            text="📋 סקיצה",
            bg=self.colors['card_bg'],
            font=("Arial", 9, "bold"),
            fg=self.colors['warning']
        ).pack(side="left")
        
        # הגדרות שוליים
        margins_frame = tk.LabelFrame(
            settings_container,
            text=" 📏 שוליים ",
            font=("Arial", 9, "bold"),
            padx=4,
            pady=2, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        margins_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 2))
        
        # Toggle להפעלת שוליים
        margins_toggle_frame = tk.Frame(margins_frame, bg=self.colors['card_bg'])
        margins_toggle_frame.pack(fill="x", padx=2, pady=2)
        
        margins_toggle = ToggleSwitch(
            margins_toggle_frame,
            variable=self.add_margins,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        )
        margins_toggle.pack(side="left", padx=(0, 4))
        
        tk.Label(
            margins_toggle_frame,
            text="הפעל",
            bg=self.colors['card_bg'],
            font=("Arial", 9, "bold"),
            fg=self.colors['dark_text']
        ).pack(side="left", padx=(0, 8))
        
        tk.Label(
            margins_toggle_frame, 
            text="רוחב:", bg=self.colors['card_bg'],
            font=("Arial", 9)
        ).pack(side="left", padx=(0, 2))
        additional_margin_spinbox = tk.Spinbox(
            margins_toggle_frame, 
            from_=0.0, 
            to=150.0, 
            increment=5.0,
            textvariable=self.additional_margin,
            width=6,
            font=("Arial", 9)
        )
        additional_margin_spinbox.pack(side="left", padx=(0, 2))
        tk.Label(
            margins_toggle_frame,
            text="מ\"מ", bg=self.colors['card_bg'],
            font=("Arial", 9)
        ).pack(side="left")
        # תיאור הצבעים ובחירת שכבות
        colors_frame = tk.LabelFrame(
            settings_container,
            text=" 🎨 שכבות Spot ",
            font=("Arial", 9, "bold"),
            padx=4,
            pady=2, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        colors_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(2, 2))
        # CutContour
        cutcontour_frame = tk.Frame(colors_frame, bg=self.colors['card_bg'])
        cutcontour_frame.pack(fill="x", pady=2)
        
        cutcontour_toggle = ToggleSwitch(
            cutcontour_frame,
            variable=self.add_cutcontour,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        )
        cutcontour_toggle.pack(side="left", padx=(0, 4))
        
        tk.Label(
            cutcontour_frame, 
            text="✂️ CutContour (מג'נטה)", 
            fg="#FF00FF", 
            bg=self.colors['card_bg'], 
            font=("Arial", 9, "bold")
        ).pack(side="left")
        # Holes
        holes_frame = tk.Frame(colors_frame, bg=self.colors['card_bg'])
        holes_frame.pack(fill="x", pady=2)
        
        holes_toggle = ToggleSwitch(
            holes_frame,
            variable=self.add_holes,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        )
        holes_toggle.pack(side="left", padx=(0, 4))
        
        tk.Label(
            holes_frame, 
            text="🕳️ Holes (ירוק)", 
            fg="#80FF00", 
            bg=self.colors['card_bg'], 
            font=("Arial", 9, "bold")
        ).pack(side="left")
        # Crease
        crease_frame = tk.Frame(colors_frame, bg=self.colors['card_bg'])
        crease_frame.pack(fill="x", pady=2)
        
        crease_toggle = ToggleSwitch(
            crease_frame,
            variable=self.replace_crease,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        )
        crease_toggle.pack(side="left", padx=(0, 4))
        
        tk.Label(
            crease_frame, 
            text="📐 Crease (ציאן)", 
            fg="#00FFFF", 
            bg=self.colors['card_bg'], 
            font=("Arial", 9, "bold")
        ).pack(side="left")
        
        # Crop Marks Control
        crop_marks_frame = tk.LabelFrame(
            settings_container,
            text=" ✂️ Crop Marks ",
            font=("Arial", 9, "bold"),
            padx=4,
            pady=2, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        crop_marks_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(2, 2))
        
        # הסרת crop marks
        remove_frame = tk.Frame(crop_marks_frame, bg=self.colors['card_bg'])
        remove_frame.pack(fill="x", pady=2)
        
        remove_toggle = ToggleSwitch(
            remove_frame,
            variable=self.remove_crop_marks,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        )
        remove_toggle.pack(side="left", padx=(0, 4))
        
        tk.Label(
            remove_frame, 
            text="🗑️ הסר Crop Marks אוטומטית", 
            fg=self.colors['success'], 
            bg=self.colors['card_bg'], 
            font=("Arial", 9, "bold")
        ).pack(side="left")
        
        # הגדרת גריד להתפשטות
        settings_container.grid_columnconfigure(0, weight=1)
        settings_container.grid_columnconfigure(1, weight=1)
        # כפתור עיבוד
        process_btn = tk.Button(
            right_panel,
            text="▶  עבד את כל הקבצים",
            command=self.process_all_files,
            bg=self.colors['primary'],
            fg="white",
            font=("Arial", 11, "bold"),
            pady=6,
            relief="flat",
            cursor="hand2",
            activebackground="#1565C0"
        )
        process_btn.pack(fill="x", pady=(4, 0))
        
        # יצירת ממשק האוטומציה
        self.create_automation_tab(automation_tab)
        
        # שורת סטטוס
        self.status_label = tk.Label(
            self.root, 
            text="⚡ מוכן לעיבוד",
            font=("Arial", 9, "bold"),
            bg=self.colors['header_bg'],
            fg=self.colors['primary'],
            anchor="w",
            padx=10,
            pady=4
        )
        self.status_label.pack(side="bottom", fill="x")
    
    def browse_files(self):
        filenames = filedialog.askopenfilenames(
            title="בחר קבצי PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filenames:
            # עדכון מספר הזמנה לפי התיקייה של הקובץ הראשון
            if len(filenames) > 0:
                first_file = filenames[0]
                folder_name = os.path.basename(os.path.dirname(first_file))
                self.order_number.set(folder_name)
            
            for filename in filenames:
                if filename not in self.input_files:
                    self.input_files.append(filename)
            self.update_files_list()
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="בחר תיקייה")
        if folder:
            # עדכון מספר הזמנה לפי שם התיקייה
            folder_name = os.path.basename(folder)
            self.order_number.set(folder_name)
            
            pdf_files = glob.glob(os.path.join(folder, "*.pdf"))
            for pdf_file in pdf_files:
                if pdf_file not in self.input_files:
                    self.input_files.append(pdf_file)
            self.update_files_list()
    
    def clear_files(self):
        self.input_files = []
        self.update_files_list()
    
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="בחר תיקיית יעד")
        if folder:
            self.output_folder.set(folder)
    
    def clear_output_folder(self):
        self.output_folder.set("")
    
    def browse_production_folder(self):
        folder = filedialog.askdirectory(title="בחר תיקיית ייצור")
        if folder:
            self.production_folder.set(folder)
    
    def clear_production_folder(self):
        self.production_folder.set("")
    
    def update_files_list(self):
        # ניקוי הטבלה
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # איפוס מסננים
        self.column_filters = {}
        self.all_tree_items_dict = {}  # שמירת כל הפריטים לצורך מסננים

        # בדיקת תיקיות מקור - זיהוי קבצים מתיקיות שונות
        source_folders = set()
        for file_path in self.input_files:
            folder = os.path.dirname(file_path)
            source_folders.add(folder)
        
        # הצגת/הסתרת אזהרה על תיקיות מעורבות
        if len(source_folders) > 1:
            folder_names = [os.path.basename(f) for f in source_folders]
            self.show_mixed_folders_warning(folder_names)
        else:
            self.hide_mixed_folders_warning()

        # ספירת כפולים
        seen = set()
        duplicate_count = 0
        for file_path in self.input_files:
            if file_path in seen:
                duplicate_count += 1
            else:
                seen.add(file_path)

        pixelated_count = 0
        low_quality_count = 0
        error_count = 0
        item_counter = 0
        for file_path in self.input_files:
            filename = os.path.basename(file_path)
            resolution, dpi, colormode, pixelated, vector_status = self.get_pdf_info(file_path)
            cutcontour = self.detect_spot_layer(file_path, 'CutContour')
            crease = self.detect_spot_layer(file_path, 'Crease')
            holes = self.detect_spot_layer(file_path, 'Holes')
            
            print(f"[FILE] {filename}: colormode={colormode}, vector={vector_status}, cutcontour={cutcontour}, crease={crease}, holes={holes}")
            
            # יצירת ID ייחודי לפריט
            item_id = f"item_{item_counter}"
            item_values = ('⬜', filename, '1', resolution, dpi, colormode, vector_status, pixelated, cutcontour, crease, holes)
            
            print(f"[FILE] Inserting values: {item_values}")
            
            # שמירה במילון
            self.all_tree_items_dict[item_id] = item_values
            
            # הוספה לטבלה
            self.files_tree.insert('', 'end', iid=item_id, values=item_values)
            item_counter += 1
            
            if "✗ מפוקסל" in pixelated:
                pixelated_count += 1
            if "⚠ בינוני" in pixelated:
                low_quality_count += 1
            if "שגיאה" in resolution or "שגיאה" in dpi or "שגיאה" in pixelated:
                error_count += 1

        # התאמת רוחב עמודות לתוכן
        self.adjust_column_widths()

        total_files = len(self.input_files)
        self.files_total_label.config(text=f"{total_files} קבצים ברשימה")
        self.update_ai_summary(total_files, pixelated_count, low_quality_count, duplicate_count, error_count)
        
        # הצגת כפולים
        if duplicate_count > 0:
            self.files_duplicate_separator_label.pack(side="left")
            self.files_duplicate_label.config(text=f"{duplicate_count} כפולים")
            self.files_duplicate_label.pack(side="left")
        else:
            self.files_duplicate_separator_label.pack_forget()
            self.files_duplicate_label.pack_forget()

        # תווית כתומה - מפוקסלים
        if pixelated_count > 0:
            self.files_separator_label.pack(side="left")
            self.files_pixelated_label.config(text=f"{pixelated_count} מפוקסלים")
            self.files_pixelated_label.pack(side="left")
        else:
            self.files_separator_label.pack_forget()
            self.files_pixelated_label.pack_forget()

        # תווית אדומה - שגיאות
        if error_count > 0:
            self.files_error_separator_label.pack(side="left")
            self.files_error_label.config(text=f"{error_count} שגיאות")
            self.files_error_label.pack(side="left")
        else:
            self.files_error_separator_label.pack_forget()
            self.files_error_label.pack_forget()
    
    def get_pdf_info(self, pdf_path):
        """מחזיר מידע על PDF - משתמש ב-PDFAnalyzer"""
        return PDFAnalyzer.get_pdf_info(pdf_path)
    
    def find_cutcontour_bounds(self, page):
        """מחפש גבולות CutContour - משתמש ב-PDFAnalyzer"""
        return PDFAnalyzer.find_cutcontour_bounds(page)
    
    def get_actual_dpi(self, page):
        """מחזיר את ה-DPI האמיתי הנמוך ביותר מבין כל התמונות בעמוד"""
        try:
            # קבלת מידות העמוד
            if hasattr(page, 'trimbox') and page.trimbox:
                bbox = page.trimbox
            elif hasattr(page, 'bleedbox') and page.bleedbox:
                bbox = page.bleedbox
            else:
                bbox = page.mediabox
            
            page_width_pt = float(bbox.right) - float(bbox.left)
            page_height_pt = float(bbox.top) - float(bbox.bottom)
            
            if '/Resources' not in page or '/XObject' not in page['/Resources']:
                print("[DPI] No /XObject in /Resources - might be vector-only PDF")
                # עבור PDF וקטורי, נחשיב שה-DPI הוא מצוין (לא רלוונטי)
                return 300  # ערך ברירת מחדל טוב עבור PDF וקטורי
            
            xobjects = page['/Resources']['/XObject'].get_object()
            all_dpis = []

            for obj_name in xobjects:
                obj = xobjects[obj_name]
                if obj.get('/Subtype') == '/Image':
                    width_px = obj.get('/Width', 0)
                    height_px = obj.get('/Height', 0)
                    print(f"[DPI] Found image {obj_name}: {width_px}x{height_px} px")
                    if width_px and height_px:
                        actual_dpi = self.calculate_image_dpi(page, obj_name, width_px, height_px, page_width_pt, page_height_pt)
                        print(f"[DPI]   Calculated DPI for {obj_name}: {actual_dpi}")
                        if actual_dpi and actual_dpi > 0:
                            all_dpis.append(actual_dpi)

            if all_dpis:
                print(f"[DPI] All calculated DPIs: {all_dpis}")
                min_dpi = min(all_dpis)
                return min_dpi

            print("[DPI] No images with valid DPI found - might be vector graphics")
            return 300  # ערך ברירת מחדל עבור גרפיקה וקטורית
        except Exception as e:
            print(f"[DPI] Exception: {e}")
            import traceback
            traceback.print_exc()
            return 300  # ערך ברירת מחדל במקרה של שגיאה
    
    def get_actual_dpi_fitz(self, page):
        """מחזיר DPI - משתמש ב-PDFAnalyzer"""
        return PDFAnalyzer.get_actual_dpi_fitz(page)
    
    def detect_color_mode(self, page):
        """מזהה מצב צבעים - משתמש ב-PDFAnalyzer"""
        return PDFAnalyzer.detect_color_mode(page)
    
    def check_images_quality(self, page, page_width_mm, page_height_mm):
        """בודק איכות תמונות - משתמש ב-PDFAnalyzer"""
        return PDFAnalyzer.check_images_quality(page, page_width_mm, page_height_mm)
    
    def get_content_bounding_box(self, page):
        """פונקציה זו לא בשימוש יותר - הפונקציונליות במודול PDFAnalyzer"""
        pass
    
    def calculate_image_dpi(self, page, image_name, width_px, height_px, page_width_pt=None, page_height_pt=None):
        """מחשב את ה-DPI האמיתי של תמונה על סמך מיקומה בעמוד"""
        try:
            # אם לא סופקו מידות העמוד, נחשב אותן
            if page_width_pt is None or page_height_pt is None:
                if hasattr(page, 'trimbox') and page.trimbox:
                    bbox = page.trimbox
                elif hasattr(page, 'bleedbox') and page.bleedbox:
                    bbox = page.bleedbox
                else:
                    bbox = page.mediabox
                page_width_pt = float(bbox.right) - float(bbox.left)
                page_height_pt = float(bbox.top) - float(bbox.bottom)
            
            content = page.get_contents()
            if content is None:
                print(f"[DPI] No content stream for image {image_name}")
                # חישוב DPI על סמך מידות העמוד
                page_width_inches = page_width_pt / 72
                page_height_inches = page_height_pt / 72
                dpi_w = width_px / page_width_inches if page_width_inches > 0 else 72
                dpi_h = height_px / page_height_inches if page_height_inches > 0 else 72
                return (dpi_w + dpi_h) / 2

            content_data = content.get_data()
            if isinstance(content_data, bytes):
                content_str = content_data.decode('latin-1', errors='ignore')
            else:
                content_str = str(content_data)

            # חיפוש מטריצת טרנספורמציה של התמונה
            pattern = rf'q\s+([\d\.\-\s]+)\s+cm\s+{image_name}\s+Do'
            matches = re.findall(pattern, content_str)
            print(f"[DPI] Searching for matrix for {image_name}: found {len(matches)} matches")

            if matches:
                matrix_values = matches[0].split()
                print(f"[DPI]   Matrix values for {image_name}: {matrix_values}")
                if len(matrix_values) >= 4:
                    width_pt = abs(float(matrix_values[0]))
                    height_pt = abs(float(matrix_values[3]))
                    
                    # אם המטריצה מכילה ערכים קטנים מאוד, ייתכן שזו טרנספורמציה מוזרה
                    if width_pt < 1 or height_pt < 1:
                        print(f"[DPI]   Matrix values too small, using page dimensions")
                        width_pt = page_width_pt
                        height_pt = page_height_pt
                    
                    width_inches = width_pt / 72
                    height_inches = height_pt / 72
                    dpi_w = width_px / width_inches if width_inches > 0 else 0
                    dpi_h = height_px / height_inches if height_inches > 0 else 0
                    print(f"[DPI]   width_pt={width_pt}, height_pt={height_pt}, width_inches={width_inches}, height_inches={height_inches}, dpi_w={dpi_w}, dpi_h={dpi_h}")
                    
                    avg_dpi = (dpi_w + dpi_h) / 2
                    # בדיקת סבירות - אם ה-DPI גבוה מדי או נמוך מדי, משהו שגוי
                    if avg_dpi > 10000 or avg_dpi < 10:
                        print(f"[DPI]   DPI out of range ({avg_dpi}), recalculating with page size")
                        page_width_inches = page_width_pt / 72
                        page_height_inches = page_height_pt / 72
                        dpi_w = width_px / page_width_inches if page_width_inches > 0 else 72
                        dpi_h = height_px / page_height_inches if page_height_inches > 0 else 72
                        return (dpi_w + dpi_h) / 2
                    
                    return avg_dpi

            print(f"[DPI] No matrix found for {image_name}, calculating from page dimensions")
            page_width_inches = page_width_pt / 72
            page_height_inches = page_height_pt / 72
            dpi_w = width_px / page_width_inches if page_width_inches > 0 else 72
            dpi_h = height_px / page_height_inches if page_height_inches > 0 else 72
            print(f"[DPI]   page_width_inches={page_width_inches}, page_height_inches={page_height_inches}, dpi_w={dpi_w}, dpi_h={dpi_h}")
            return (dpi_w + dpi_h) / 2
        except Exception as e:
            print(f"[DPI] Exception in calculate_image_dpi for {image_name}: {e}")
            import traceback
            traceback.print_exc()
            try:
                # ניסיון אחרון - שימוש במידות העמוד
                page_width_inches = page_width_pt / 72 if page_width_pt else (page.mediabox.width / 72)
                dpi = width_px / page_width_inches if page_width_inches > 0 else 72
                print(f"[DPI]   Fallback DPI: {dpi}")
                return dpi
            except Exception as e2:
                print(f"[DPI]   Fallback exception: {e2}")
                return 72
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update()
    
    def show_column_filter(self, column):
        """הצגת תפריט מסנן לעמודה"""
        # איסוף כל הערכים הייחודיים בעמודה - מכל הפריטים (גם מוסתרים)
        col_index = list(self.files_tree['columns']).index(column)
        unique_values = set()
        
        # שימוש ברשימת הפריטים המלאה ששמרנו
        if hasattr(self, 'all_tree_items_dict') and self.all_tree_items_dict:
            for item_id, values in self.all_tree_items_dict.items():
                if col_index < len(values):
                    unique_values.add(str(values[col_index]))
        else:
            # אם לא שמור, נשתמש בפריטים הנוכחיים
            for item in self.files_tree.get_children():
                values = self.files_tree.item(item)['values']
                if col_index < len(values):
                    unique_values.add(str(values[col_index]))
        
        # יצירת חלון מסנן
        filter_window = tk.Toplevel(self.root)
        filter_window.title(f"סינון: {self.files_tree.heading(column)['text'].replace(' ▼', '')}")
        filter_window.geometry("300x400")
        filter_window.transient(self.root)
        
        # כפתור הכל
        tk.Button(
            filter_window,
            text="✓ הצג הכל",
            command=lambda: self.apply_filter(column, None, filter_window),
            bg=self.colors['success'],
            fg='white',
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5
        ).pack(fill="x", padx=10, pady=(10, 5))
        
        # רשימת ערכים
        tk.Label(
            filter_window,
            text="בחר ערכים לסינון:",
            font=("Arial", 9, "bold")
        ).pack(pady=(5, 5))
        
        list_frame = tk.Frame(filter_window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        value_listbox = tk.Listbox(
            list_frame,
            selectmode="multiple",
            yscrollcommand=scrollbar.set,
            font=("Arial", 9)
        )
        value_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=value_listbox.yview)
        
        # הוספת ערכים
        for value in sorted(unique_values):
            value_listbox.insert(tk.END, value)
        
        # כפתור החלה
        def apply_selected():
            selected_indices = value_listbox.curselection()
            if selected_indices:
                selected_values = [value_listbox.get(i) for i in selected_indices]
                self.apply_filter(column, selected_values, filter_window)
            else:
                messagebox.showwarning("אזהרה", "נא לבחור לפחות ערך אחד")
        
        tk.Button(
            filter_window,
            text="החל סינון",
            command=apply_selected,
            bg=self.colors['primary'],
            fg='white',
            font=("Arial", 9, "bold"),
            padx=10,
            pady=5
        ).pack(fill="x", padx=10, pady=(5, 10))
    
    def apply_filter(self, column, filter_values, window):
        """החלת מסנן על עמודה"""
        if filter_values is None:
            # ביטול מסנן - הצג הכל
            if column in self.column_filters:
                del self.column_filters[column]
        else:
            # שמירת מסנן
            self.column_filters[column] = filter_values
        
        # סגירת חלון המסנן
        window.destroy()
        
        # החלת המסנן
        self.filter_tree_items()
    
    def clear_all_filters(self):
        """ביטול כל המסננים והצגת כל השורות (עם שמירת סימונים)"""
        self.column_filters = {}
        
        # אם יש פריטים מוסתרים, נשחזר אותם
        if hasattr(self, 'all_tree_items_dict') and self.all_tree_items_dict:
            # שמירת הסימונים הנוכחיים לפני הניקוי
            current_checkboxes = {}
            for item in self.files_tree.get_children():
                values = self.files_tree.item(item)['values']
                if values:
                    current_checkboxes[item] = values[0]
            
            # נקי את הטבלה ונוסיף מחדש את כל הפריטים
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)
            
            for item_id, values in self.all_tree_items_dict.items():
                self.files_tree.insert('', 'end', iid=item_id, values=values)
        else:
            # אם לא שמור, פשוט נוודא שכל הפריטים הנוכחיים גלויים
            # (זה לא אמור לקרות אם אנחנו שומרים נכון)
            pass
    
    def filter_tree_items(self):
        """סינון שורות בטבלה לפי הסננים"""
        if not hasattr(self, 'all_tree_items_dict') or not self.all_tree_items_dict:
            return
        
        # נקי את הטבלה
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # הוסף רק את הפריטים שעוברים את כל המסננים
        for item_id, values in self.all_tree_items_dict.items():
            show_item = True
            
            # בדיקה לפי כל המסננים
            for column, filter_values in self.column_filters.items():
                col_index = list(self.files_tree['columns']).index(column)
                if col_index < len(values):
                    cell_value = str(values[col_index])
                    if cell_value not in filter_values:
                        show_item = False
                        break
            
            # הוספה של השורה אם היא עוברת את המסננים
            if show_item:
                self.files_tree.insert('', 'end', iid=item_id, values=values)
    
    def adjust_column_widths(self):
        """התאמת רוחב עמודות באופן דינאמי לפי התוכן"""
        import tkinter.font as tkfont
        
        # יצירת פונט למדידה
        font = tkfont.Font()
        
        # עבור כל עמודה
        for col in self.files_tree['columns']:
            # מדידת רוחב הכותרת
            heading_text = self.files_tree.heading(col)['text']
            max_width = font.measure(str(heading_text)) + 20  # ריווח נוסף
            
            # מדידת רוחב כל ערך בעמודה
            for item in self.files_tree.get_children():
                values = self.files_tree.item(item)['values']
                col_index = list(self.files_tree['columns']).index(col)
                if col_index < len(values):
                    cell_value = str(values[col_index])
                    cell_width = font.measure(cell_value) + 20
                    max_width = max(max_width, cell_width)
            
            # עמודת checkbox - רוחב קבוע
            if col == 'selected':
                self.files_tree.column(col, width=30, stretch=False)
            else:
                # הגבלת רוחב מקסימלי
                max_width = min(max_width, 300)
                self.files_tree.column(col, width=max_width)
    
    def on_tree_click(self, event):
        """טיפול בלחיצה על הטבלה - שינוי checkbox או עריכת כמות"""
        region = self.files_tree.identify_region(event.x, event.y)
        if region == 'heading':
            return
        
        column = self.files_tree.identify_column(event.x)
        item = self.files_tree.identify_row(event.y)
        
        if not item:
            return
        
        if column == '#1':  # עמודת checkbox
            values = list(self.files_tree.item(item)['values'])
            if values:
                # שינוי מצב checkbox
                values[0] = '✅' if values[0] == '⬜' else '⬜'
                self.files_tree.item(item, values=values)
                
                # עדכון במילון המקורי
                if item in self.all_tree_items_dict:
                    updated_values = list(self.all_tree_items_dict[item])
                    updated_values[0] = values[0]
                    self.all_tree_items_dict[item] = tuple(updated_values)
        
        elif column == '#3':  # עמודת כמות (quantity)
            # וידוא שהשורה נבחרת לפני עריכה
            self.files_tree.selection_set(item)
            # השהיה קטנה כדי לוודא שהבחירה התעדכנה
            self.root.after(10, lambda: self.edit_quantity(item))
    
    def edit_quantity(self, clicked_item):
        """עריכת כמות בשורה - כל הקבצים המסומנים בcheckbox יתעדכנו"""
        # קבלת כל השורות שמסומנות בcheckbox (✅)
        checked_items = []
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item)['values']
            if values and values[0] == '✅':
                checked_items.append(item)
        
        # אם אין שורות מסומנות, עדכן רק את השורה שלחצו עליה
        if not checked_items:
            checked_items = [clicked_item]
        
        # ודא שה-bbox תקין
        try:
            bbox_result = self.files_tree.bbox(clicked_item, '#3')
            if not bbox_result or len(bbox_result) != 4:
                print(f"[ERROR] Invalid bbox for item {clicked_item}")
                return
            x, y, width, height = bbox_result
        except Exception as e:
            print(f"[ERROR] Failed to get bbox: {e}")
            return
        
        # קבלת הערך הנוכחי
        values = self.files_tree.item(clicked_item)['values']
        current_quantity = str(values[2]) if len(values) > 2 and values[2] else '1'
        
        # יצירת Entry לעריכה
        entry = tk.Entry(self.files_tree, justify='center', font=("Arial", 9))
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_quantity)
        entry.select_range(0, tk.END)
        entry.focus()
        
        def save_quantity(event=None):
            new_quantity = entry.get().strip()
            # בדיקה שהכמות היא מספר חיובי
            try:
                qty = int(new_quantity)
                if qty < 1:
                    qty = 1
                new_quantity = str(qty)
            except ValueError:
                new_quantity = '1'
            
            # עדכון כל השורות המסומנות בcheckbox
            for item in checked_items:
                try:
                    # עדכון הערך בטבלה
                    values = list(self.files_tree.item(item)['values'])
                    if len(values) > 2:
                        values[2] = new_quantity
                        self.files_tree.item(item, values=values)
                    
                    # עדכון במילון המקורי
                    if item in self.all_tree_items_dict:
                        updated_values = list(self.all_tree_items_dict[item])
                        if len(updated_values) > 2:
                            updated_values[2] = new_quantity
                            self.all_tree_items_dict[item] = tuple(updated_values)
                except Exception as e:
                    print(f"[ERROR] Failed to update item {item}: {e}")
            
            entry.destroy()
            # הצגת הודעה
            if len(checked_items) > 1:
                self.update_status(f"עודכנו {len(checked_items)} קבצים מסומנים לכמות: {new_quantity}")
            else:
                self.update_status(f"עודכנה כמות ל: {new_quantity}")
        
        def cancel_edit(event=None):
            entry.destroy()
        
        entry.bind('<Return>', save_quantity)
        entry.bind('<FocusOut>', save_quantity)
        entry.bind('<Escape>', cancel_edit)
        entry.bind('<Tab>', save_quantity)
    
    def on_tree_double_click(self, event):
        """טיפול בדאבל קליק - פתיחת תצוגה מקדימה של PDF"""
        item = self.files_tree.identify_row(event.y)
        column = self.files_tree.identify_column(event.x)
        
        # אם לחצו על עמודת checkbox, אל תפתח תצוגה מקדימה
        if column == '#1':
            return
        
        if item:
            values = self.files_tree.item(item)['values']
            if values and len(values) > 1:
                filename = values[1]  # שם הקובץ
                
                # מצא את הנתיב המלא של הקובץ
                file_path = None
                for path in self.input_files:
                    if os.path.basename(path) == filename:
                        file_path = path
                        break
                
                if file_path and os.path.exists(file_path):
                    self.show_pdf_preview(file_path)
    
    def show_pdf_preview(self, pdf_path):
        """הצגת חלון תצוגה מקדימה של PDF"""
        try:
            # פתיחת PDF לבדיקת מידות
            doc = fitz.open(pdf_path)
            page = doc[0]
            
            # חישוב גודל המסך הזמין
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # מידות העמוד בפיקסלים (72 DPI)
            page_width_pt = page.rect.width
            page_height_pt = page.rect.height
            
            # המרה לפיקסלים - zoom=1 נותן 72 DPI
            # נרצה להתאים לגודל המסך עם מרווח של 10%
            max_preview_width = int(screen_width * 0.8)
            max_preview_height = int(screen_height * 0.85)
            
            # חישוב zoom כך שהתמונה תתאים למסך
            zoom_x = max_preview_width / page_width_pt
            zoom_y = max_preview_height / page_height_pt
            zoom = min(zoom_x, zoom_y, 2.0)  # מקסימום פי 2
            
            # המרה לתמונה
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # המרה ל-PIL Image
            img_data = pix.tobytes("png")
            from PIL import Image, ImageTk
            img = Image.open(io.BytesIO(img_data))
            
            # גודל החלון מותאם לתמונה + מרווח
            window_width = min(img.width + 40, max_preview_width)
            window_height = min(img.height + 200, max_preview_height)  # +200 למידע ולכפתור
            
            # פתיחת חלון חדש
            preview_window = tk.Toplevel(self.root)
            preview_window.title(f"תצוגה מקדימה - {os.path.basename(pdf_path)}")
            preview_window.geometry(f"{window_width}x{window_height}")
            preview_window.configure(bg=self.colors['dark_bg'])
            
            # מרכוז החלון במסך
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            preview_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            # יצירת frame עם scrollbar (למקרה שהתמונה עדיין גדולה)
            canvas_frame = tk.Frame(preview_window, bg=self.colors['dark_bg'])
            canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            canvas = tk.Canvas(canvas_frame, bg=self.colors['dark_bg'], highlightthickness=0)
            scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=self.colors['dark_bg'])
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            
            photo = ImageTk.PhotoImage(img)
            
            # הצגת התמונה
            img_label = tk.Label(scrollable_frame, image=photo, bg=self.colors['dark_bg'])
            img_label.image = photo  # שמירת reference
            img_label.pack(pady=10)
            
            # מידע על הקובץ
            info_frame = tk.Frame(scrollable_frame, bg=self.colors['card_bg'], padx=20, pady=15)
            info_frame.pack(fill="x", padx=10, pady=(0, 10))
            
            tk.Label(
                info_frame,
                text=f"📄 {os.path.basename(pdf_path)}",
                font=("Arial", 12, "bold"),
                fg=self.colors['primary'],
                bg=self.colors['card_bg']
            ).pack(anchor="w", pady=5)
            
            # מידות העמוד
            width_mm = int(page_width_pt / 72 * 25.4)
            height_mm = int(page_height_pt / 72 * 25.4)
            
            tk.Label(
                info_frame,
                text=f"📏 מידות: {width_mm}x{height_mm} מ\"מ",
                font=("Arial", 10),
                fg=self.colors['dark_text'],
                bg=self.colors['card_bg']
            ).pack(anchor="w", pady=2)
            
            # נתיב מלא
            tk.Label(
                info_frame,
                text=f"📁 נתיב: {pdf_path}",
                font=("Arial", 9),
                fg=self.colors['light_text'],
                bg=self.colors['card_bg']
            ).pack(anchor="w", pady=2)
            
            doc.close()
            
            # כפתור סגירה
            close_btn = tk.Button(
                preview_window,
                text="✖ סגור",
                command=preview_window.destroy,
                bg=self.colors['danger'],
                fg="white",
                font=("Arial", 10, "bold"),
                padx=20,
                pady=8,
                relief="flat",
                cursor="hand2"
            )
            close_btn.pack(pady=10)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[PREVIEW ERROR] Failed to show preview for {pdf_path}")
            print(f"[PREVIEW ERROR] {error_details}")
            messagebox.showerror("שגיאה", f"לא ניתן להציג תצוגה מקדימה:\n{str(e)}\n\nפרטים נוספים נמצאים בטרמינל.")
    
    def toggle_all_checkboxes(self):
        """סימון/ביטול סימון של כל ה-checkboxes המוצגים"""
        # בדיקה אם כולם מסומנים (רק מה שמוצג)
        all_checked = True
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item)['values']
            if values and values[0] == '⬜':
                all_checked = False
                break
        
        # שינוי מצב רק למוצגים
        new_state = '⬜' if all_checked else '✅'
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item)['values'])
            if values:
                values[0] = new_state
                self.files_tree.item(item, values=values)
                # עדכון במילון המקורי
                if item in self.all_tree_items_dict:
                    updated_values = list(self.all_tree_items_dict[item])
                    updated_values[0] = new_state
                    self.all_tree_items_dict[item] = tuple(updated_values)
    
    def select_all_files(self):
        """סמן checkbox עבור כל הקבצים"""
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item)['values'])
            if values:
                values[0] = '✅'
                self.files_tree.item(item, values=values)
    
    def select_none_files(self):
        """בטל סימון כל ה-checkboxes"""
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item)['values'])
            if values:
                values[0] = '⬜'
                self.files_tree.item(item, values=values)
    
    def select_pixelated_files(self):
        """סמן checkbox רק עבור קבצים מפוקסלים או באיכות ירודה"""
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item)['values'])
            if len(values) > 5:
                pixelated = str(values[5])
                if "מפוקסל" in pixelated or "בינוני" in pixelated:
                    values[0] = '✅'
                else:
                    values[0] = '⬜'
                self.files_tree.item(item, values=values)
    
    def select_rgb_files(self):
        """סמן checkbox רק עבור קבצים במצב RGB"""
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item)['values'])
            if len(values) > 4:
                colormode = str(values[4])
                if "RGB" in colormode:
                    values[0] = '✅'
                else:
                    values[0] = '⬜'
                self.files_tree.item(item, values=values)
    
    def select_low_dpi_files(self):
        """סמן checkbox רק עבור קבצים עם DPI נמוך מ-300"""
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item)['values'])
            if len(values) > 3:
                dpi = str(values[3])
                try:
                    if dpi != "N/A" and int(dpi) < 300:
                        values[0] = '✅'
                    else:
                        values[0] = '⬜'
                    self.files_tree.item(item, values=values)
                except:
                    values[0] = '⬜'
                    self.files_tree.item(item, values=values)
    
    def process_all_files(self):
        # בדיקה אם יש קבצים מסומנים
        has_selected = False
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item)['values']
            if values and values[0] == '✅':
                has_selected = True
                break
        
        if not has_selected:
            messagebox.showerror("שגיאה", "נא לסמן לפחות קובץ אחד עם ה-checkbox")
            return
        
        # הפעלת העיבוד בחוט נפרד
        thread = threading.Thread(target=self.process_multiple_files)
        thread.start()
    
    def process_multiple_files(self):
        # קבלת הקבצים המסומנים (עם checkbox) והכמות שלהם
        selected_files = []
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item)['values']
            if values and values[0] == '✅':
                filename = values[1]  # שם הקובץ בעמודה השנייה
                quantity = int(values[2]) if len(values) > 2 and values[2] else 1  # כמות
                # חיפוש הקובץ המלא לפי שם
                for file_path in self.input_files:
                    if os.path.basename(file_path) == filename:
                        selected_files.append((file_path, quantity))
                        break
        
        # חישוב סך כל הקבצים לעיבוד (כל קובץ מעובד רק פעם אחת)
        total_files = len(selected_files)
        success_count = 0
        failed_files = []
        current_file_index = 0
        
        for file_path, quantity in selected_files:
            current_file_index += 1
            try:
                qty_suffix = f" (כמות: {quantity})" if quantity > 1 else ""
                self.update_status(f"מעבד קובץ {current_file_index}/{total_files}: {os.path.basename(file_path)}{qty_suffix}...")
                self.process_single_pdf(file_path, quantity)
                success_count += 1
            except Exception as e:
                failed_files.append((os.path.basename(file_path) + qty_suffix, str(e)))
                print(f"שגיאה בעיבוד {file_path}: {e}")
                # רישום השגיאה ליומן
                if hasattr(self, 'changes_log_ui'):
                    order_number = self.order_number.get() if hasattr(self, 'order_number') else ""
                    self.changes_log_ui.add_change(
                        file_path,
                        None,
                        [],
                        success=False,
                        error_message=str(e),
                        order_number=order_number
                    )
        
        # סיכום
        summary = f"הסתיים!\n\nעובדו בהצלחה: {success_count}/{total_files}"
        if failed_files:
            summary += "\n\nנכשלו:\n"
            for fname, error in failed_files:
                summary += f"• {fname}\n"
        
        self.update_status(f"הושלם! {success_count}/{total_files} קבצים")
        messagebox.showinfo("סיכום עיבוד", summary)
    
    def process_file(self):
        input_pdf = self.input_file.get()
        
        if not input_pdf or not os.path.exists(input_pdf):
            messagebox.showerror("שגיאה", "נא לבחור קובץ PDF תקין")
            return
        
        # הפעלת העיבוד בחוט נפרד
        thread = threading.Thread(target=self.process_pdf_file, args=(input_pdf,))
        thread.start()
    
    def process_pdf_file(self, input_pdf):
        try:
            self.process_single_pdf(input_pdf)
            
            base, ext = os.path.splitext(input_pdf)
            reader = PdfReader(input_pdf)
            page = reader.pages[0]
            
            if hasattr(page, 'trimbox') and page.trimbox:
                bbox = page.trimbox
            elif hasattr(page, 'bleedbox') and page.bleedbox:
                bbox = page.bleedbox
            else:
                bbox = page.mediabox
            
            left = float(bbox.left)
            right = float(bbox.right)
            bottom = float(bbox.bottom)
            top = float(bbox.top)
            
            cutcontour_width_mm = int(round((right - left) / mm))
            cutcontour_height_mm = int(round((top - bottom) / mm))
            output_pdf = f"{base}_{cutcontour_width_mm}x{cutcontour_height_mm}mm{ext}"
            
            self.update_status(f"הושלם! נשמר: {os.path.basename(output_pdf)}")
            messagebox.showinfo(
                "הצלחה", 
                f"הקובץ עובד בהצלחה!\n\nנשמר בשם:\n{os.path.basename(output_pdf)}\n\n"
                f"מידות CutContour: {cutcontour_width_mm}x{cutcontour_height_mm}mm"
            )
            
        except Exception as e:
            self.update_status(f"שגיאה: {str(e)}")
            messagebox.showerror("שגיאה", f"אירעה שגיאה בעיבוד:\n{str(e)}")
    
    def process_single_pdf(self, input_pdf, quantity=1):
        # שמירת שם הקובץ המקורי לפני העיבודים
        original_input_pdf = input_pdf
        
        # הסרת crop marks אם נדרש
        if self.remove_crop_marks.get():
            input_pdf = self.remove_crop_marks_from_pdf(input_pdf)
        
        # שיפור איכות תמונות אם נדרש
        if self.enhance_images.get():
            input_pdf = self.enhance_pdf_images(input_pdf)
        
        # המרה ל-CMYK אם נדרש
        if self.convert_to_cmyk.get():
            input_pdf = self.convert_pdf_to_cmyk(input_pdf)
        
        # פרמטרים
        hole_diameter_val = self.hole_diameter.get() * mm
        hole_radius = hole_diameter_val / 2
        margin = self.hole_margin.get() * mm
        artboard_margin = self.artboard_margin.get() * mm
        stroke_width = self.stroke_width.get()
        stroke_width = self.stroke_width.get()
        
        # צבעי Spot
        cutcontour_color = CMYKColorSep(0, 1, 0, 0, spotName="CutContour")
        crease_color = CMYKColorSep(1, 0, 0, 0, spotName="Crease")
        holes_color = CMYKColorSep(0.5, 0, 1, 0, spotName="Holes")
        
        # יצירת שם קובץ פלט
        base, ext = os.path.splitext(input_pdf)
        
        # קריאת PDF
        reader = PdfReader(input_pdf)
        page = reader.pages[0]
        
        # זיהוי גבולות הגרפיקה מ-Artboard (TrimBox/BleedBox/MediaBox)
        if hasattr(page, 'trimbox') and page.trimbox:
            bbox = page.trimbox
        elif hasattr(page, 'bleedbox') and page.bleedbox:
            bbox = page.bleedbox
        else:
            bbox = page.mediabox
        
        left = float(bbox.left)
        right = float(bbox.right)
        bottom = float(bbox.bottom)
        top = float(bbox.top)
        
        # שוליים נוספים - רק אם נבחר
        additional_margin_val = 0
        if self.add_margins.get():
            additional_margin_val = self.additional_margin.get() * mm
        
        # חישוב גדלים
        new_page_width = (right - left) + (artboard_margin * 2) + (additional_margin_val * 2)
        new_page_height = (top - bottom) + (artboard_margin * 2) + (additional_margin_val * 2)
        
        cutcontour_width_mm = int(round((right - left) / mm))
        cutcontour_height_mm = int(round((top - bottom) / mm))
        
        # קביעת תיקיית יעד
        output_folder = self.output_folder.get()
        quantity_suffix = f"_qty{quantity}"  # הכמות תמיד מופיעה בשם הקובץ
        if output_folder and os.path.isdir(output_folder):
            # שמירה בתיקיית יעד
            output_pdf = os.path.join(
                output_folder,
                f"{os.path.basename(base)}_{cutcontour_width_mm}x{cutcontour_height_mm}mm{quantity_suffix}{ext}"
            )
        else:
            # שמירה בתיקיית המקור
            output_pdf = f"{base}_{cutcontour_width_mm}x{cutcontour_height_mm}mm{quantity_suffix}{ext}"
        
        # אם הקובץ קיים, הוא יידרס
        if os.path.exists(output_pdf):
            print(f"[INFO] Overwriting existing file: {output_pdf}")
        
        x_offset = artboard_margin + additional_margin_val - left
        y_offset = artboard_margin + additional_margin_val - bottom
        
        # החלפת שכבות קיימות
        if self.add_cutcontour.get():
            self.replace_cut_with_cutcontour(page)
        
        if self.replace_crease.get():
            self.replace_crease_layers(page)
        
        # יצירת overlay
        overlay_path = os.path.join(os.path.dirname(input_pdf), "overlay_temp.pdf")
        c = canvas.Canvas(overlay_path, pagesize=(new_page_width, new_page_height))
        
        # קו אפור - מסמן את הגבול המקורי לפני הוספת השוליים
        if additional_margin_val > 0:
            c.setStrokeColorRGB(0.7, 0.7, 0.7)  # אפור בהיר
            c.setLineWidth(1 * mm)  # קו בעובי 1 מ"מ
            c.rect(
                artboard_margin + additional_margin_val,
                artboard_margin + additional_margin_val,
                (right - left),
                (top - bottom),
                stroke=1,
                fill=0
            )
        
        # CutContour - סביב הגרפיקה + השוליים הלבנים
        if self.add_cutcontour.get():
            c.setStrokeColor(cutcontour_color)
            c.setLineWidth(stroke_width)
            c.rect(
                artboard_margin,
                artboard_margin,
                (right - left) + (additional_margin_val * 2),
                (top - bottom) + (additional_margin_val * 2),
                stroke=1,
                fill=0
            )
        
        # Holes - ממוקמים לפי הבחירה: פינות העמוד או פינות הגרפיקה
        if self.add_holes.get():
            c.setStrokeColor(holes_color)
            c.setLineWidth(stroke_width)
            
            if self.holes_position.get() == "graphic":
                # חורים בפינות הגרפיקה (CutContour)
                graphic_left = artboard_margin + (additional_margin_val if self.add_margins.get() else 0)
                graphic_right = artboard_margin + (right - left) + (additional_margin_val if self.add_margins.get() else 0)
                graphic_bottom = artboard_margin + (additional_margin_val if self.add_margins.get() else 0)
                graphic_top = artboard_margin + (top - bottom) + (additional_margin_val if self.add_margins.get() else 0)
                
                holes = [
                    (graphic_left + margin, graphic_top - margin),      # שמאל עליון
                    (graphic_right - margin, graphic_top - margin),     # ימין עליון
                    (graphic_left + margin, graphic_bottom + margin),   # שמאל תחתון
                    (graphic_right - margin, graphic_bottom + margin)   # ימין תחתון
                ]
            else:
                # חורים בפינות העמוד (ברירת מחדל)
                holes = [
                    (margin, new_page_height - margin),                 # שמאל עליון
                    (new_page_width - margin, new_page_height - margin),# ימין עליון
                    (margin, margin),                                   # שמאל תחתון
                    (new_page_width - margin, margin)                   # ימין תחתון
                ]
            
            for x, y in holes:
                c.circle(x, y, hole_radius, stroke=1, fill=0)
        
        c.save()
        
        # מיזוג
        writer = PdfWriter()
        overlay_reader = PdfReader(overlay_path)
        
        page.mediabox = RectangleObject([0, 0, new_page_width, new_page_height])
        page.cropbox = RectangleObject([0, 0, new_page_width, new_page_height])
        page.add_transformation([1, 0, 0, 1, x_offset, y_offset])
        page.merge_page(overlay_reader.pages[0])
        writer.add_page(page)
        
        # שמירה
        with open(output_pdf, "wb") as f:
            writer.write(f)
        
        # מחיקת קובץ זמני
        if os.path.exists(overlay_path):
            os.remove(overlay_path)
        
        # רישום השינויים ליומן - עם השם המקורי
        self.log_changes(original_input_pdf, output_pdf)
        
        # יצירת סקיצה לאישור לקוח אם המצב מופעל
        print(f"[DEBUG] sketch_mode is: {self.sketch_mode.get()}")
        if self.sketch_mode.get():
            try:
                print(f"[SKETCH] Creating approval sketch for: {output_pdf}")
                settings = get_sketch_settings(self)
                settings['quantity'] = quantity  # הוספת הכמות להגדרות הסקיצה
                settings['original_filename'] = os.path.basename(original_input_pdf)  # שם הקובץ המקורי
                settings['order_number'] = self.order_number.get() if hasattr(self, 'order_number') else ""  # מספר הזמנה
                # תיקיית יעד לסקיצות: אם הוגדרה תיקיית יעד - שימוש בה, אחרת תיקיית הקובץ המקורי
                settings['output_folder'] = output_folder if output_folder and os.path.isdir(output_folder) else os.path.dirname(original_input_pdf)
                print(f"[SKETCH] Settings: {settings}")
                sketch_result = create_approval_sketch(output_pdf, settings)
                if sketch_result:
                    if isinstance(sketch_result, dict):
                        print(f"[SKETCH] Created approval sketch PDF: {sketch_result.get('pdf')}")
                        if sketch_result.get('image'):
                            print(f"[SKETCH] Created approval sketch image: {sketch_result.get('image')}")
                    else:
                        # תאימות לאחור - אם מוחזר רק מחרוזת
                        print(f"[SKETCH] Created approval sketch: {sketch_result}")
                else:
                    print(f"[SKETCH] Sketch file is None!")
            except Exception as e:
                print(f"[SKETCH] Failed to create approval sketch: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[SKETCH] Sketch mode is OFF - skipping sketch creation")
        
        return output_pdf
    
    def replace_cut_with_cutcontour(self, page):
        try:
            content = ContentStream(page.get_contents(), page.pdf)
            content_str = content.get_data().decode('latin-1') if isinstance(content.get_data(), bytes) else str(content.get_data())
            
            pattern1 = r'/Cut\s+(cs|CS)'
            replacements_made = False
            
            if re.search(pattern1, content_str):
                content_str = re.sub(r'/Cut(\s+)', r'/CutContour\1', content_str)
                replacements_made = True
            
            if '/ColorSpace' in page.get('/Resources', {}):
                resources = page['/Resources']
                colorspaces = resources.get('/ColorSpace', {})
                
                if isinstance(colorspaces, DictionaryObject):
                    if '/Cut' in colorspaces:
                        cut_def = colorspaces['/Cut']
                        colorspaces[NameObject('/CutContour')] = cut_def
                        del colorspaces[NameObject('/Cut')]
                        replacements_made = True
            
            if replacements_made:
                page.replace_contents(content_str.encode('latin-1'))
        except Exception as e:
            print(f"Note: Could not process existing Cut layers: {e}")
    
    def replace_crease_layers(self, page):
        try:
            content = ContentStream(page.get_contents(), page.pdf)
            content_str = content.get_data().decode('latin-1') if isinstance(content.get_data(), bytes) else str(content.get_data())
            
            replacements_made = False
            crease_names = ['Crease', 'Fold', 'Score', 'Creasing']
            
            if '/ColorSpace' in page.get('/Resources', {}):
                resources = page['/Resources']
                colorspaces = resources.get('/ColorSpace', {})
                
                if isinstance(colorspaces, DictionaryObject):
                    for crease_name in crease_names:
                        name_key = f'/{crease_name}'
                        if name_key in colorspaces:
                            crease_def = colorspaces[name_key]
                            colorspaces[NameObject('/Crease')] = crease_def
                            if crease_name != 'Crease':
                                del colorspaces[NameObject(name_key)]
                            replacements_made = True
                        
                        pattern = rf'/{crease_name}(\s+)'
                        if re.search(pattern, content_str):
                            content_str = re.sub(pattern, r'/Crease\1', content_str)
                            replacements_made = True
            
            if replacements_made:
                page.replace_contents(content_str.encode('latin-1'))
        except Exception as e:
            print(f"Note: Could not process existing Crease/Fold layers: {e}")
    
    def convert_pdf_to_cmyk(self, input_pdf):
        """ממיר את כל התמונות ב-PDF מ-RGB ל-CMYK"""
        if not PIL_AVAILABLE:
            messagebox.showwarning(
                "התראה",
                "ספריית PIL/Pillow לא מותקנת.\nלא ניתן להמיר ל-CMYK.\n\nהתקן באמצעות: pip install Pillow"
            )
            return input_pdf
        
        try:
            # יצירת קובץ זמני מומר
            base, ext = os.path.splitext(input_pdf)
            cmyk_pdf = f"{base}_cmyk_temp{ext}"
            
            reader = PdfReader(input_pdf)
            writer = PdfWriter()
            
            for page_num, page in enumerate(reader.pages):
                # עיבוד תמונות בעמוד
                if '/Resources' in page and '/XObject' in page['/Resources']:
                    xobjects = page['/Resources']['/XObject'].get_object()
                    
                    for obj_name in xobjects:
                        obj = xobjects[obj_name]
                        
                        if obj.get('/Subtype') == '/Image':
                            try:
                                # בדיקת מצב הצבע הנוכחי
                                colorspace = obj.get('/ColorSpace')
                                is_rgb = False
                                
                                if isinstance(colorspace, str):
                                    if 'RGB' in colorspace or 'DeviceRGB' in colorspace:
                                        is_rgb = True
                                elif isinstance(colorspace, list) and len(colorspace) > 0:
                                    cs_name = str(colorspace[0])
                                    if 'RGB' in cs_name or 'DeviceRGB' in cs_name:
                                        is_rgb = True
                                
                                # המרה רק אם זה RGB
                                if is_rgb:
                                    # שליפת נתוני התמונה
                                    data = obj.get_data()
                                    
                                    # המרה לתמונת PIL
                                    image = Image.open(io.BytesIO(data))
                                    
                                    # המרה ל-CMYK
                                    if image.mode != 'CMYK':
                                        image = image.convert('CMYK')
                                    
                                    # שמירה חזרה
                                    img_buffer = io.BytesIO()
                                    image.save(img_buffer, format='JPEG', quality=95)
                                    
                                    # עדכון האובייקט ב-PDF
                                    obj[NameObject('/ColorSpace')] = NameObject('/DeviceCMYK')
                                    obj._data = img_buffer.getvalue()
                                    
                            except Exception as e:
                                print(f"לא ניתן להמיר תמונה {obj_name} ל-CMYK: {e}")
                
                writer.add_page(page)
            
            # שמירת הקובץ המומר
            with open(cmyk_pdf, 'wb') as output_file:
                writer.write(output_file)
            
            return cmyk_pdf
            
        except Exception as e:
            print(f"שגיאה בהמרה ל-CMYK: {e}")
            return input_pdf
    
    def detect_and_display_crop_marks(self, pdf_path):
        """זיהוי והצגת מידע על crop marks"""
        try:
            remover = CropMarksRemover(verbose=True)
            info = remover.detect_crop_marks(pdf_path)
            
            # הצגת מידע למשתמש
            if info.has_crop_marks:
                msg = f"נמצאו Crop Marks!\n\n"
                msg += f"סך כל סימנים: {info.total_marks}\n\n"
                msg += "סימנים לפי סוג:\n"
                for mark_type, count in info.marks_by_type.items():
                    if count > 0:
                        msg += f"  • {mark_type}: {count}\n"
                
                msg += f"\n\nסך עמודים עם סימנים: {len(info.marks_by_page)}"
                
                messagebox.showinfo("Crop Marks Detection", msg)
                
                # רישום ליומן
                if hasattr(self, 'changes_log_ui'):
                    changes = [f"זוהו {info.total_marks} crop marks"]
                    self.changes_log_ui.add_change(
                        pdf_path,
                        None,
                        changes,
                        success=True,
                        order_number=self.order_number.get() if hasattr(self, 'order_number') else ""
                    )
            else:
                messagebox.showinfo("Crop Marks Detection", "לא נמצאו Crop Marks בקובץ")
                
        except Exception as e:
            messagebox.showerror("שגיאה בזיהוי Crop Marks", str(e))
            print(f"שגיאה בזיהוי crop marks: {e}")
    
    def remove_crop_marks_from_pdf(self, input_pdf):
        """הסרת crop marks מהקובץ - גישה מבוססת TrimBox"""
        try:
            print(f"[CROP] מסיר crop marks מ: {input_pdf}")
            
            # יצירת שם קובץ פלט
            base, ext = os.path.splitext(input_pdf)
            output_pdf = f"{base}_no_crops{ext}"
            
            # פתיחת המסמך
            doc = fitz.open(input_pdf)
            
            removed_pages = 0
            for page_num, page in enumerate(doc, 1):
                try:
                    # קבלת TrimBox או CropBox
                    mediabox = page.mediabox
                    trimbox = page.trimbox if hasattr(page, 'trimbox') and page.trimbox else None
                    cropbox = page.cropbox if hasattr(page, 'cropbox') and page.cropbox else None
                    
                    # בחירת ה-box הנכון
                    target_box = trimbox or cropbox
                    
                    if target_box and target_box != mediabox:
                        print(f"[CROP] עמוד {page_num}: קיים TrimBox/CropBox שונה מ-MediaBox")
                        print(f"[CROP]   MediaBox: {mediabox}")
                        print(f"[CROP]   Target: {target_box}")
                        
                        # ולידציה: וודא שה-target_box בתוך ה-MediaBox
                        target_rect = fitz.Rect(target_box)
                        media_rect = fitz.Rect(mediabox)
                        
                        # בדיקה שה-target box תקין
                        if (target_rect.x0 >= media_rect.x0 and 
                            target_rect.y0 >= media_rect.y0 and
                            target_rect.x1 <= media_rect.x1 and 
                            target_rect.y1 <= media_rect.y1 and
                            target_rect.width > 0 and 
                            target_rect.height > 0):
                            
                            # הגדרת MediaBox ו-CropBox ל-TrimBox
                            page.set_mediabox(target_rect)
                            page.set_cropbox(target_rect)
                            removed_pages += 1
                            print(f"[CROP] ✓ הוגדר box חדש")
                        else:
                            print(f"[CROP] ⚠ TrimBox לא תקין - מדלג")
                    else:
                        print(f"[CROP] עמוד {page_num}: אין TrimBox/CropBox שונה - מדלג")
                        
                except Exception as e:
                    print(f"[CROP] שגיאה בעמוד {page_num}: {e}")
                    continue
            
            # שמירה
            doc.save(output_pdf, garbage=4, deflate=True, clean=True)
            doc.close()
            
            if removed_pages > 0:
                print(f"[CROP] ✓ הוסרו crop marks מ-{removed_pages} עמודים")
                self.update_status(f"Crop marks הוסרו מ-{removed_pages} עמודים: {os.path.basename(output_pdf)}")
                
                # רישום ליומן
                if hasattr(self, 'changes_log_ui'):
                    changes = [f"הוסרו crop marks מ-{removed_pages} עמודים"]
                    self.changes_log_ui.add_change(
                        input_pdf,
                        output_pdf,
                        changes,
                        success=True,
                        order_number=self.order_number.get() if hasattr(self, 'order_number') else ""
                    )
                
                return output_pdf
            else:
                print(f"[CROP] ✗ לא נמצאו crop marks להסרה - מחזיר קובץ מקורי")
                # אם אין crop marks, פשוט החזר את הקובץ המקורי
                return input_pdf
                
        except Exception as e:
            print(f"[CROP ERROR] שגיאה כללית: {e}")
            import traceback
            traceback.print_exc()
            # במקרה של שגיאה, החזר את הקובץ המקורי
            return input_pdf
            return input_pdf
    
    def enhance_pdf_images(self, input_pdf):
        """משפר את איכות התמונות ב-PDF - upscaling ל-300 DPI והמרה ל-CMYK"""
        if not PIL_AVAILABLE:
            messagebox.showwarning(
                "התראה",
                "ספריית PIL/Pillow לא מותקנת.\nלא ניתן לשפר תמונות.\n\nהתקן באמצעות: pip install Pillow"
            )
            return input_pdf
        
        try:
            base, ext = os.path.splitext(input_pdf)
            enhanced_pdf = f"{base}_enhanced_temp{ext}"
            reader = PdfReader(input_pdf)
            writer = PdfWriter()
            for page_num, page in enumerate(reader.pages):
                if '/Resources' in page and '/XObject' in page['/Resources']:
                    xobjects = page['/Resources']['/XObject'].get_object()
                    for obj_name in xobjects:
                        obj = xobjects[obj_name]
                        if obj.get('/Subtype') == '/Image':
                            width_px = obj.get('/Width', 0)
                            height_px = obj.get('/Height', 0)
                            if width_px and height_px:
                                current_dpi = self.calculate_image_dpi(page, obj_name, width_px, height_px)
                                try:
                                    data = obj.get_data()
                                    image = Image.open(io.BytesIO(data))
                                    # AI quality analysis
                                    quality = self.analyze_image_quality(image)
                                    print(f"[AI] Image {obj_name} quality: {quality}")
                                    # AI enhancement if needed
                                    if current_dpi and current_dpi < 300:
                                        image = self.enhance_image_ai(image)
                                        print(f"[AI] Enhanced image {obj_name} with AI")
                                    # Convert to CMYK if needed
                                    if image.mode != 'CMYK':
                                        image = image.convert('CMYK')
                                    # Update size
                                    new_width, new_height = image.size
                                    img_buffer = io.BytesIO()
                                    image.save(img_buffer, format='JPEG', quality=95)
                                    obj[NameObject('/Width')] = new_width
                                    obj[NameObject('/Height')] = new_height
                                    obj[NameObject('/ColorSpace')] = NameObject('/DeviceCMYK')
                                    obj._data = img_buffer.getvalue()
                                except Exception as e:
                                    print(f"[AI] Failed to enhance image {obj_name}: {e}")
                writer.add_page(page)
            with open(enhanced_pdf, 'wb') as output_file:
                writer.write(output_file)
            return enhanced_pdf
        except Exception as e:
            print(f"[AI] Error enhancing images: {e}")
            return input_pdf
    
    # ===== AUTOMATION FUNCTIONS =====
    
    def create_automation_tab(self, parent):
        """יצירת ממשק אוטומציה"""
        # Main container with scroll
        main_container = tk.Frame(parent, bg=self.colors['light_bg'])
        main_container.pack(fill="both", expand=True)
        
        # יצירת Canvas ו-Scrollbar
        canvas = tk.Canvas(main_container, bg=self.colors['light_bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['light_bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # הוספת גלילה עם גלגלת העכבר
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        # קישור הגלילה ל-canvas ולכל האלמנטים בתוכו
        canvas.bind("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        # קישור גם כשנכנסים לאזור
        def bind_to_mousewheel(event):
            canvas.bind("<MouseWheel>", _on_mousewheel)
            scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Enter>", bind_to_mousewheel)
        scrollable_frame.bind("<Enter>", bind_to_mousewheel)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Container לתוכן
        container = tk.Frame(scrollable_frame, bg=self.colors['light_bg'])
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # תיקיית ניטור
        watch_frame = tk.LabelFrame(
            container,
            text=" 📁 תיקיית ניטור ",
            font=("Arial", 10, "bold"),
            padx=8,
            pady=6, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        watch_frame.pack(fill="x", pady=(0, 6))
        
        tk.Label(
            watch_frame,
            text="בחר תיקיה לניטור - כל קובץ PDF חדש יטופל אוטומטית",
            font=("Arial", 9),
            fg=self.colors['light_text'], bg=self.colors['card_bg']
        ).pack(anchor="w", pady=(0, 8))
        
        watch_entry_frame = tk.Frame(watch_frame, bg=self.colors['card_bg'])
        watch_entry_frame.pack(fill="x")
        
        watch_entry = tk.Entry(
            watch_entry_frame,
            textvariable=self.watch_folder,
            font=("Arial", 10),
            relief="solid",
            borderwidth=1
        )
        watch_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(
            watch_entry_frame,
            text="📁 בחר תיקיה",
            command=self.browse_watch_folder,
            bg=self.colors['primary'],
            fg="white",
            font=("Arial", 9, "bold"),
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        ).pack(side="right")
        
        # תיקיות יעד
        dest_frame = tk.LabelFrame(
            container,
            text=" 📂 תיקיות יעד ",
            font=("Arial", 10, "bold"),
            padx=8,
            pady=6, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        dest_frame.pack(fill="x", pady=(0, 6))
        
        # תיקיית הצלחה
        tk.Label(
            dest_frame,
            text="תיקיית קבצים מעובדים:",
            font=("Arial", 9, "bold"), bg=self.colors['card_bg']
        ).pack(anchor="w", pady=(0, 5))
        
        success_entry_frame = tk.Frame(dest_frame, bg=self.colors['card_bg'])
        success_entry_frame.pack(fill="x", pady=(0, 10))
        
        tk.Entry(
            success_entry_frame,
            textvariable=self.automation_output_folder,
            font=("Arial", 10),
            relief="solid",
            borderwidth=1
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(
            success_entry_frame,
            text="📁 בחר",
            command=self.browse_automation_output,
            bg=self.colors['success'],
            fg="white",
            font=("Arial", 9, "bold"),
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        ).pack(side="right")
        
        # תיקיית שגיאות
        tk.Label(
            dest_frame,
            text="תיקיית קבצים עם שגיאות (UnDone):",
            font=("Arial", 9, "bold"), bg=self.colors['card_bg']
        ).pack(anchor="w", pady=(0, 5))
        
        error_entry_frame = tk.Frame(dest_frame, bg=self.colors['card_bg'])
        error_entry_frame.pack(fill="x")
        
        tk.Entry(
            error_entry_frame,
            textvariable=self.automation_error_folder,
            font=("Arial", 10),
            relief="solid",
            borderwidth=1
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(
            error_entry_frame,
            text="📁 בחר",
            command=self.browse_automation_error,
            bg=self.colors['danger'],
            fg="white",
            font=("Arial", 9, "bold"),
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        ).pack(side="right")
        
        # הגדרות עיבוד
        settings_frame = tk.LabelFrame(
            container,
            text=" ⚙️ הגדרות עיבוד אוטומטי ",
            font=("Arial", 10, "bold"),
            padx=8,
            pady=6, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        settings_frame.pack(fill="x", pady=(0, 6))
        
        tk.Label(
            settings_frame,
            text="התכונות שיופעלו באופן אוטומטי על כל קובץ:",
            font=("Arial", 9),
            fg=self.colors['light_text'], bg=self.colors['card_bg']
        ).pack(anchor="w", pady=(0, 10))
        
        # Toggle Switches לתכונות
        features_container = tk.Frame(settings_frame, bg=self.colors['card_bg'])
        features_container.pack(fill="x", padx=5)
        
        # CutContour
        cutcontour_auto_frame = tk.Frame(features_container, bg=self.colors['card_bg'])
        cutcontour_auto_frame.pack(fill="x", pady=6)
        ToggleSwitch(
            cutcontour_auto_frame,
            variable=self.add_cutcontour,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        ).pack(side="left", padx=(0, 10))
        tk.Label(
            cutcontour_auto_frame,
            text="✂️ הוסף CutContour",
            font=("Arial", 10, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text']
        ).pack(side="left")
        
        # Holes
        holes_auto_frame = tk.Frame(features_container, bg=self.colors['card_bg'])
        holes_auto_frame.pack(fill="x", pady=6)
        ToggleSwitch(
            holes_auto_frame,
            variable=self.add_holes,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        ).pack(side="left", padx=(0, 10))
        tk.Label(
            holes_auto_frame,
            text="🕳️ הוסף חורים",
            font=("Arial", 10, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text']
        ).pack(side="left")
        
        # Crease
        crease_auto_frame = tk.Frame(features_container, bg=self.colors['card_bg'])
        crease_auto_frame.pack(fill="x", pady=6)
        ToggleSwitch(
            crease_auto_frame,
            variable=self.replace_crease,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        ).pack(side="left", padx=(0, 10))
        tk.Label(
            crease_auto_frame,
            text="📐 החלף Crease",
            font=("Arial", 10, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text']
        ).pack(side="left")
        
        # CMYK
        cmyk_auto_frame = tk.Frame(features_container, bg=self.colors['card_bg'])
        cmyk_auto_frame.pack(fill="x", pady=6)
        ToggleSwitch(
            cmyk_auto_frame,
            variable=self.convert_to_cmyk,
            on_color=self.colors['success'],
            off_color=self.colors['border'],
            bg=self.colors['card_bg']
        ).pack(side="left", padx=(0, 10))
        tk.Label(
            cmyk_auto_frame,
            text="🎨 המר ל-CMYK",
            font=("Arial", 10, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text']
        ).pack(side="left")
        
        # הגדרות חורים
        holes_settings_frame = tk.LabelFrame(
            container,
            text=" 🕳️ הגדרות חורים ",
            font=("Arial", 10, "bold"),
            padx=8,
            pady=6, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        holes_settings_frame.pack(fill="x", pady=(0, 6))
        
        # מיקום חורים
        hole_position_frame = tk.Frame(holes_settings_frame, bg=self.colors['card_bg'])
        hole_position_frame.pack(fill="x", pady=5)
        
        tk.Label(
            hole_position_frame,
            text="מיקום חורים:",
            font=("Arial", 10, "bold"), bg=self.colors['card_bg']
        ).pack(side="left", padx=(0, 10))
        
        tk.Radiobutton(
            hole_position_frame,
            text="פינות העמוד",
            variable=self.holes_position,
            value="page",
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            selectcolor=self.colors['card_bg'],
            font=("Arial", 9)
        ).pack(side="left", padx=(0, 10))
        
        tk.Radiobutton(
            hole_position_frame,
            text="פינות הגרפיקה (CutContour)",
            variable=self.holes_position,
            value="graphic",
            bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            selectcolor=self.colors['card_bg'],
            font=("Arial", 9)
        ).pack(side="left")
        
        # קוטר חור
        hole_diameter_frame = tk.Frame(holes_settings_frame, bg=self.colors['card_bg'])
        hole_diameter_frame.pack(fill="x", pady=5)
        
        tk.Label(
            hole_diameter_frame,
            text="קוטר חור (מ\"מ):",
            font=("Arial", 10), bg=self.colors['card_bg']
        ).pack(side="left", padx=(0, 10))
        
        tk.Spinbox(
            hole_diameter_frame,
            from_=1.0,
            to=50.0,
            increment=0.5,
            textvariable=self.hole_diameter,
            width=10,
            font=("Arial", 10)
        ).pack(side="left")
        
        # מרחק ממרכז החור לגבול
        hole_margin_frame = tk.Frame(holes_settings_frame, bg=self.colors['card_bg'])
        hole_margin_frame.pack(fill="x", pady=5)
        
        tk.Label(
            hole_margin_frame,
            text="מרחק ממרכז חור לגבול (מ\"מ):",
            font=("Arial", 10), bg=self.colors['card_bg']
        ).pack(side="left", padx=(0, 10))
        
        tk.Spinbox(
            hole_margin_frame,
            from_=5.0,
            to=100.0,
            increment=1.0,
            textvariable=self.hole_margin,
            width=10,
            font=("Arial", 10)
        ).pack(side="left")
        
        # סטטוס ולוג
        status_frame = tk.LabelFrame(
            container,
            text=" 📊 סטטוס ",
            font=("Arial", 10, "bold"),
            padx=8,
            pady=6, bg=self.colors['card_bg'],
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        status_frame.pack(fill="both", expand=True, pady=(0, 6))
        
        self.automation_status_label = tk.Label(
            status_frame,
            text="⚪ האוטומציה כבויה",
            font=("Arial", 12, "bold"), bg=self.colors['card_bg'],
            fg=self.colors['light_text']
        )
        self.automation_status_label.pack(pady=(0, 10))
        
        # לוג
        log_scroll = tk.Scrollbar(status_frame)
        log_scroll.pack(side="right", fill="y")
        
        self.automation_log = tk.Text(
            status_frame,
            height=8,
            font=("Consolas", 8),
            yscrollcommand=log_scroll.set,
            relief="solid",
            borderwidth=1
        )
        self.automation_log.pack(fill="both", expand=True)
        log_scroll.config(command=self.automation_log.yview)
        
        # כפתורי בקרה
        control_frame = tk.Frame(container, bg=self.colors['light_bg'])
        control_frame.pack(fill="x")
        
        self.start_automation_btn = tk.Button(
            control_frame,
            text="▶️ הפעל אוטומציה",
            command=self.start_automation,
            bg=self.colors['success'],
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2"
        )
        self.start_automation_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        
        self.stop_automation_btn = tk.Button(
            control_frame,
            text="⏹️ עצור אוטומציה",
            command=self.stop_automation,
            bg=self.colors['danger'],
            fg="white",
            font=("Arial", 11, "bold"),
            padx=20,
            pady=8,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.stop_automation_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))
    
    def browse_watch_folder(self):
        """בחירת תיקיית ניטור"""
        folder = filedialog.askdirectory(title="בחר תיקיה לניטור")
        if folder:
            self.watch_folder.set(folder)
            self.log_automation(f"נבחרה תיקיית ניטור: {folder}")
    
    def browse_automation_output(self):
        """בחירת תיקיית פלט"""
        folder = filedialog.askdirectory(title="בחר תיקיית פלט לקבצים מעובדים")
        if folder:
            self.automation_output_folder.set(folder)
            self.log_automation(f"נבחרה תיקיית פלט: {folder}")
    
    def browse_automation_error(self):
        """בחירת תיקיית שגיאות"""
        folder = filedialog.askdirectory(title="בחר תיקיית שגיאות (UnDone)")
        if folder:
            self.automation_error_folder.set(folder)
            self.log_automation(f"נבחרה תיקיית שגיאות: {folder}")
    
    def log_automation(self, message):
        """הוספת הודעה ללוג אוטומציה"""
        timestamp = time.strftime("%H:%M:%S")
        self.automation_log.insert("end", f"[{timestamp}] {message}\\n")
        self.automation_log.see("end")
        self.root.update()
    
    def start_automation(self):
        """הפעלת אוטומציה"""
        # בדיקת תקינות
        if not self.watch_folder.get():
            messagebox.showerror("שגיאה", "נא לבחור תיקיית ניטור")
            return
        
        if not self.automation_output_folder.get():
            messagebox.showerror("שגיאה", "נא לבחור תיקיית פלט")
            return
        
        if not self.automation_error_folder.get():
            messagebox.showerror("שגיאה", "נא לבחור תיקיית שגיאות")
            return
        
        # יצירת תיקיות אם לא קיימות
        os.makedirs(self.automation_output_folder.get(), exist_ok=True)
        os.makedirs(self.automation_error_folder.get(), exist_ok=True)
        
        # הפעלת אוטומציה
        self.automation_active = True
        self.processed_files = set()
        
        # עדכון UI
        self.start_automation_btn.config(state="disabled")
        self.stop_automation_btn.config(state="normal")
        self.automation_status_label.config(
            text="🟢 האוטומציה פעילה",
            fg=self.colors['success']
        )
        
        self.log_automation("=== האוטומציה הופעלה ===")
        self.log_automation(f"מנטר תיקיה: {self.watch_folder.get()}")
        self.log_automation(f"פלט: {self.automation_output_folder.get()}")
        self.log_automation(f"שגיאות: {self.automation_error_folder.get()}")
        
        # הרצת Thread לניטור
        self.automation_thread = threading.Thread(target=self.automation_worker, daemon=True)
        self.automation_thread.start()
    
    def stop_automation(self):
        """עצירת אוטומציה"""
        self.automation_active = False
        
        # עדכון UI
        self.start_automation_btn.config(state="normal")
        self.stop_automation_btn.config(state="disabled")
        self.automation_status_label.config(
            text="⚪ האוטומציה כבויה",
            fg=self.colors['light_text']
        )
        
        self.log_automation("=== האוטומציה הופסקה ===")
    
    def automation_worker(self):
        """Thread עיקרי לניטור תיקיה"""
        self.log_automation("מתחיל ניטור קבצים...")
        
        while self.automation_active:
            try:
                # סריקת קבצי PDF בתיקיה
                watch_path = self.watch_folder.get()
                pdf_files = glob.glob(os.path.join(watch_path, "*.pdf"))
                
                for pdf_file in pdf_files:
                    if not self.automation_active:
                        break
                    
                    # בדיקה אם הקובץ כבר עובד
                    if pdf_file in self.processed_files:
                        continue
                    
                    # סימון שהקובץ בעיבוד
                    self.processed_files.add(pdf_file)
                    
                    filename = os.path.basename(pdf_file)
                    self.log_automation(f"⚙️ מעבד: {filename}")
                    
                    # עיבוד הקובץ
                    success = self.process_file_automation(pdf_file)
                    
                    if success:
                        # העברה לתיקיית הצלחה
                        dest = os.path.join(self.automation_output_folder.get(), filename)
                        try:
                            shutil.move(pdf_file, dest)
                            self.log_automation(f"✅ הושלם: {filename} → {self.automation_output_folder.get()}")
                        except Exception as e:
                            self.log_automation(f"⚠️ שגיאה בהעברת קובץ {filename}: {e}")
                    else:
                        # העברה לתיקיית שגיאות
                        dest = os.path.join(self.automation_error_folder.get(), filename)
                        try:
                            shutil.move(pdf_file, dest)
                            self.log_automation(f"❌ שגיאה: {filename} → UnDone")
                        except Exception as e:
                            self.log_automation(f"⚠️ שגיאה בהעברת קובץ שגוי {filename}: {e}")
                
                # המתנה קצרה לפני הסריקה הבאה
                time.sleep(2)
                
            except Exception as e:
                self.log_automation(f"❌ שגיאה בניטור: {e}")
                time.sleep(5)
    
    def process_file_automation(self, pdf_path):
        """עיבוד קובץ בודד באוטומציה"""
        try:
            # קריאה לפונקציית העיבוד הקיימת
            output_path = os.path.join(
                self.automation_output_folder.get(),
                os.path.basename(pdf_path)
            )
            
            # שימוש בפונקציה הקיימת
            self.process_single_file_internal(pdf_path, output_path)
            return True
            
        except Exception as e:
            self.log_automation(f"❌ שגיאה בעיבוד {os.path.basename(pdf_path)}: {e}")
            return False
    
    def process_single_file_internal(self, input_path, output_path):
        """עיבוד קובץ בודד - לוגיקה פנימית"""
        # קריאה לפונקציות העיבוד הקיימות
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        for page_num, page in enumerate(reader.pages):
            # העתקת העמוד
            writer.add_page(page)
            
            # הוספת CutContour אם צריך
            if self.add_cutcontour.get():
                self.add_cutcontour_layer(writer, page_num, page)
            
            # הוספת חורים אם צריך
            if self.add_holes.get():
                self.add_holes_layer(writer, page_num, page)
            
            # החלפת Crease אם צריך
            if self.replace_crease.get():
                self.replace_crease_layer(writer, page_num, page)
        
        # שמירה
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
    
    def log_changes(self, input_pdf, output_pdf):
        """רישום שינויים ליומן"""
        try:
            print(f"[DEBUG] log_changes called: {input_pdf} -> {output_pdf}")
            changes_made = []
            
            # בדיקת השינויים שבוצעו
            if self.add_cutcontour.get():
                changes_made.append("הוספת/עדכון שכבת CutContour")
            
            if self.replace_crease.get():
                changes_made.append("החלפת שכבת Crease (קיפול)")
            
            if self.add_holes.get():
                changes_made.append("הוספת חורים")
            
            if self.add_margins.get():
                margin = self.additional_margin.get()
                changes_made.append(f"הוספת שוליים: {margin} מ\"מ")
            
            if self.enhance_images.get():
                changes_made.append("שיפור איכות תמונות")
            
            if self.convert_to_cmyk.get():
                changes_made.append("המרה ל-CMYK")
            
            if self.sketch_mode.get():
                changes_made.append("יצירת סקיצת אישור")
            
            # קבלת מספר הזמנה
            order_number = self.order_number.get() if hasattr(self, 'order_number') else ""
            
            print(f"[DEBUG] Changes made: {changes_made}")
            print(f"[DEBUG] Order number: {order_number}")
            print(f"[DEBUG] Has changes_log_ui: {hasattr(self, 'changes_log_ui')}")
            
            # הוספה ליומן
            if hasattr(self, 'changes_log_ui'):
                print(f"[DEBUG] Adding to changes log...")
                self.changes_log_ui.add_change(
                    input_pdf, 
                    output_pdf, 
                    changes_made,
                    success=True,
                    order_number=order_number
                )
                print(f"[DEBUG] Successfully added to changes log")
            else:
                print(f"[DEBUG] changes_log_ui NOT FOUND!")
        except Exception as e:
            print(f"[LOG] Error logging changes: {e}")
            import traceback
            traceback.print_exc()

def main():
    """הפעלת GUI ראשי"""
    root = tk.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
