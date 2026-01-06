import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import os
import threading
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import CMYKColorSep
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, NameObject, DictionaryObject, RectangleObject
import re
import glob
import io
import cv2
import numpy as np
from skimage import restoration, filters
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
        """Detect if a layer exists in the PDF by name. Returns layer name with type (S=Spot/P=Process/L=Layer) or '-' if not found."""
        try:
            reader = PdfReader(pdf_path)
            page = reader.pages[0]
            found_layers = []
            
            # 1. בדיקת ColorSpace (Spot Colors)
            if '/Resources' in page and '/ColorSpace' in page['/Resources']:
                colorspaces = page['/Resources']['/ColorSpace']
                if isinstance(colorspaces, dict):
                    for key, val in colorspaces.items():
                        name = str(key).replace('/', '')
                        if spot_name.lower() in name.lower():
                            try:
                                resolved = val.get_object() if hasattr(val, 'get_object') else val
                                if isinstance(resolved, list) and len(resolved) > 0:
                                    if str(resolved[0]) == '/Separation':
                                        found_layers.append(f'{name} (S)')
                                    else:
                                        found_layers.append(f'{name} (P)')
                                elif isinstance(resolved, str) and 'Separation' in resolved:
                                    found_layers.append(f'{name} (S)')
                                else:
                                    found_layers.append(f'{name} (P)')
                            except Exception:
                                found_layers.append(f'{name} (S)')
            
            # 2. בדיקת Layers/OCG (Optional Content Groups)
            if '/OCProperties' in reader.trailer.get('/Root', {}):
                try:
                    oc_props = reader.trailer['/Root']['/OCProperties']
                    if '/OCGs' in oc_props:
                        ocgs = oc_props['/OCGs']
                        if hasattr(ocgs, 'get_object'):
                            ocgs = ocgs.get_object()
                        if isinstance(ocgs, list):
                            for ocg in ocgs:
                                if hasattr(ocg, 'get_object'):
                                    ocg = ocg.get_object()
                                if isinstance(ocg, dict) and '/Name' in ocg:
                                    layer_name = str(ocg['/Name']).replace('/', '')
                                    if spot_name.lower() in layer_name.lower():
                                        found_layers.append(f'{layer_name} (L)')
                except Exception:
                    pass
            
            # 3. חיפוש בתוך content stream
            try:
                content = page.get_contents()
                if content:
                    content_data = content.get_data()
                    if isinstance(content_data, bytes):
                        content_str = content_data.decode('latin-1', errors='ignore')
                    else:
                        content_str = str(content_data)
                    
                    # חיפוש שמות שכבות בתוך content stream
                    import re
                    pattern = rf'/{spot_name}\s*(cs|CS|scn|SCN|setcolor)'
                    if re.search(pattern, content_str, re.IGNORECASE):
                        # נמצא שימוש בשכבה
                        if not any(spot_name.lower() in layer.lower() for layer in found_layers):
                            found_layers.append(f'{spot_name} (P)')
            except Exception:
                pass
            
            # החזרת התוצאה
            if found_layers:
                return ', '.join(found_layers)
            return '-'
        except Exception as e:
            return '-'
    
    def update_ai_summary(self, total_files, pixelated_count, low_quality_count, duplicate_count, error_count):
        """Show AI summary of file stats at the top of the GUI."""
        if not hasattr(self, 'ai_summary_label'):
            self.ai_summary_label = tk.Label(self.root, text='', font=("Segoe UI", 12, "bold"), fg=self.colors['primary'], bg=self.colors['light_bg'], anchor='w', justify='left')
            self.ai_summary_label.pack(fill="x", pady=(5, 0))
        summary = f"סך קבצים: {total_files} | כפולים: {duplicate_count} | מפוקסלים: {pixelated_count} | איכות ירודה: {low_quality_count} | שגיאות: {error_count}"
        self.ai_summary_label.config(text=summary)
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
        self.root.geometry("1200x900")
        self.root.resizable(True, True)
        # סכמת צבעים מקצועית
        self.colors = {
            'primary': '#1976D2',      # כחול מקצועי
            'success': '#388E3C',      # ירוק
            'warning': '#F57C00',      # כתום
            'danger': '#D32F2F',       # אדום
            'light_bg': '#F5F5F5',     # רקע בהיר
            'dark_text': '#212121',    # טקסט כהה
            'light_text': '#757575',   # טקסט בהיר
            'border': '#E0E0E0'        # גבול
        }
        # הגדרת רקע
        self.root.configure(bg=self.colors['light_bg'])
        
        # הגדרת סגנון Treeview
        style = ttk.Style()
        style.theme_use('clam')  # נושא שמספק שליטה טובה יותר
        style.configure('Treeview.Heading', 
                       font=('Segoe UI', 10, 'bold'),
                       background=self.colors['primary'],
                       foreground='white',
                       relief='raised',
                       borderwidth=1)
        style.configure('Treeview',
                       font=('Segoe UI', 9),
                       rowheight=25,
                       background='white',
                       fieldbackground='white')
        style.map('Treeview.Heading',
                 background=[('active', '#1565C0')])
        
        # משתנים
        self.input_files = []
        self.all_tree_items = []  # שמירת כל השורות המקוריות לצורך מסננים
        self.all_tree_items_dict = {}  # מילון של כל הפריטים לפי ID
        self.output_folder = tk.StringVar(value="")  # ריק = תיקיית המקור
        self.hole_diameter = tk.DoubleVar(value=7.0)
        self.hole_margin = tk.DoubleVar(value=20.0)
        self.artboard_margin = tk.DoubleVar(value=2.0)
        self.stroke_width = tk.DoubleVar(value=0.25)
        self.additional_margin = tk.DoubleVar(value=0.0)  # שוליים נוספים
        self.enhance_images = tk.BooleanVar(value=False)
        self.convert_to_cmyk = tk.BooleanVar(value=False)
        # אפשרויות שכבות
        self.add_cutcontour = tk.BooleanVar(value=True)
        self.add_holes = tk.BooleanVar(value=True)
        self.replace_crease = tk.BooleanVar(value=True)
        self.create_widgets()

    def create_widgets(self):
        # Header Frame
        header_frame = tk.Frame(self.root, bg=self.colors['primary'], pady=20)
        header_frame.pack(fill="x")
        title_label = tk.Label(
            header_frame, 
            text="PDF Processor Pro", 
            font=("Segoe UI", 24, "bold"),
            fg="white",
            bg=self.colors['primary']
        )
        title_label.pack()
        subtitle_label = tk.Label(
            header_frame,
            text="CutContour, Crease & Holes Generator",
            font=("Segoe UI", 10),
            fg="white",
            bg=self.colors['primary']
        )
        subtitle_label.pack()
        # יצירת Frame עם Canvas ו-Scrollbar
        container_frame = tk.Frame(self.root, bg=self.colors['light_bg'])
        container_frame.pack(fill="both", expand=True)
        # Canvas לגלילה
        canvas = tk.Canvas(container_frame, bg=self.colors['light_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
        # Main Container בתוך Canvas
        main_container = tk.Frame(canvas, bg=self.colors['light_bg'])
        # יצירת חלון בתוך Canvas
        canvas_frame = canvas.create_window((0, 0), window=main_container, anchor="nw")
        # הגדרת Scrollbar
        canvas.configure(yscrollcommand=scrollbar.set)
        # Packing
        canvas.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        scrollbar.pack(side="right", fill="y")
        # עדכון אזור הגלילה כשהתוכן משתנה
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # התאמת רוחב ה-frame לרוחב ה-canvas
            canvas_width = canvas.winfo_width()
            canvas.itemconfig(canvas_frame, width=canvas_width)
        main_container.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_frame_configure)
        # גלילה עם גלגל העכבר
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        # בחירת קבצים
        file_frame = tk.LabelFrame(
            main_container, 
            text=" 📁 קבצי PDF למעבד ",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=15,
            bg="white",
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        file_frame.pack(fill="both", expand=True, pady=(0, 10))
        # כפתורי בחירה
        buttons_frame = tk.Frame(file_frame, bg="white")
        buttons_frame.pack(fill="x", pady=(0, 10))
        browse_files_btn = tk.Button(
            buttons_frame, 
            text="  📄 בחר קבצים  ", 
            command=self.browse_files,
            bg=self.colors['success'],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2",
            activebackground="#2E7D32"
        )
        browse_files_btn.pack(side="left", padx=5)
        browse_folder_btn = tk.Button(
            buttons_frame, 
            text="  📁 בחר תיקייה  ", 
            command=self.browse_folder,
            bg=self.colors['primary'],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2",
            activebackground="#1565C0"
        )
        browse_folder_btn.pack(side="left", padx=5)
        clear_btn = tk.Button(
            buttons_frame, 
            text="  🗑️ נקה  ", 
            command=self.clear_files,
            bg=self.colors['danger'],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
            cursor="hand2",
            activebackground="#C62828"
        )
        clear_btn.pack(side="left", padx=5)
        
        # רשימת קבצים - שימוש ב-Treeview במקום Listbox
        list_frame = tk.Frame(file_frame, bg="white")
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        # יצירת Treeview עם עמודות (עם checkbox)
        columns = ('selected', 'name', 'resolution', 'dpi', 'colormode', 'pixelated', 'cutcontour', 'crease', 'holes')
        self.files_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='headings',
            height=12,
            selectmode='browse'
        )
        # משתנים למסננים
        self.column_filters = {}
        
        # הגדרת כותרות עם מסננים
        self.files_tree.heading('selected', text='☑', command=self.toggle_all_checkboxes)
        self.files_tree.heading('name', text='שם הקובץ ▼', command=lambda: self.show_column_filter('name'))
        self.files_tree.heading('resolution', text='מידה (מ"מ) ▼', command=lambda: self.show_column_filter('resolution'))
        self.files_tree.heading('dpi', text='DPI ▼', command=lambda: self.show_column_filter('dpi'))
        self.files_tree.heading('colormode', text='מצב צבעים ▼', command=lambda: self.show_column_filter('colormode'))
        self.files_tree.heading('pixelated', text='איכות ▼', command=lambda: self.show_column_filter('pixelated'))
        self.files_tree.heading('cutcontour', text='קו חיתוך ▼', command=lambda: self.show_column_filter('cutcontour'))
        self.files_tree.heading('crease', text='קו קיפול ▼', command=lambda: self.show_column_filter('crease'))
        self.files_tree.heading('holes', text='חורים ▼', command=lambda: self.show_column_filter('holes'))
        # הגדרת רוחב עמודות - רוחב מינימלי בלבד, דינאמי לפי תוכן
        self.files_tree.column('selected', minwidth=30, width=30, anchor='center', stretch=False)
        self.files_tree.column('name', minwidth=100, width=100, anchor='w', stretch=True)
        self.files_tree.column('resolution', minwidth=70, width=70, anchor='center', stretch=True)
        self.files_tree.column('dpi', minwidth=50, width=50, anchor='center', stretch=True)
        self.files_tree.column('colormode', minwidth=70, width=70, anchor='center', stretch=True)
        self.files_tree.column('pixelated', minwidth=80, width=80, anchor='center', stretch=True)
        self.files_tree.column('cutcontour', minwidth=80, width=80, anchor='center', stretch=True)
        self.files_tree.column('crease', minwidth=80, width=80, anchor='center', stretch=True)
        self.files_tree.column('holes', minwidth=80, width=80, anchor='center', stretch=True)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        self.files_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # קישור לחיצה לשינוי checkbox
        self.files_tree.bind('<Button-1>', self.on_tree_click)
        # תווית מספר קבצים - Frame עם תוויות מרובות
        count_frame = tk.Frame(file_frame, bg="white")
        count_frame.pack(pady=5)
        
        self.files_total_label = tk.Label(
            count_frame,
            text="0 קבצים ברשימה",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors['primary'],
            bg="white"
        )
        self.files_total_label.pack(side="left")
        
        # כפתור ביטול מסננים
        self.clear_filters_btn = tk.Button(
            count_frame,
            text="✗ בטל מסננים",
            command=self.clear_all_filters,
            bg=self.colors['light_bg'],
            fg=self.colors['dark_text'],
            font=("Segoe UI", 8),
            padx=8,
            pady=2,
            relief="solid",
            borderwidth=1,
            cursor="hand2"
        )
        self.clear_filters_btn.pack(side="left", padx=10)
        
        self.files_separator_label = tk.Label(
            count_frame,
            text=" | ",
            font=("Segoe UI", 10),
            fg=self.colors['dark_text'],
            bg="white"
        )
        
        self.files_pixelated_label = tk.Label(
            count_frame,
            text="",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors['warning'],
            bg="white"
        )
        
        self.files_error_separator_label = tk.Label(
            count_frame,
            text=" | ",
            font=("Segoe UI", 10),
            fg=self.colors['dark_text'],
            bg="white"
        )
        self.files_error_label = tk.Label(
            count_frame,
            text="",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors['danger'],
            bg="white"
        )
        # תיקיית יעד
        output_frame = tk.LabelFrame(
            main_container,
            text=" 💾 תיקיית יעד (אופציונלי) ",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=15,
            bg="white",
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        output_frame.pack(fill="x", pady=(0, 10))
        output_info = tk.Label(
            output_frame, 
            text="השאר ריק כדי לשמור בתיקיית המקור של כל קובץ",
            font=("Segoe UI", 9),
            fg=self.colors['light_text'],
            bg="white"
        )
        output_info.pack(anchor="w", pady=(0, 8))
        output_entry_frame = tk.Frame(output_frame, bg="white")
        output_entry_frame.pack(fill="x")
        output_entry = tk.Entry(
            output_entry_frame,
            textvariable=self.output_folder,
            font=("Segoe UI", 10),
            relief="solid",
            borderwidth=1
        )
        output_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        browse_output_btn = tk.Button(
            output_entry_frame, 
            text="  📁 בחר  ", 
            command=self.browse_output_folder,
            bg=self.colors['warning'],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=6,
            relief="flat",
            cursor="hand2",
            activebackground="#E64A19"
        )
        browse_output_btn.pack(side="left", padx=(0, 5))
        clear_output_btn = tk.Button(
            output_entry_frame, 
            text=" ✖ ", 
            command=self.clear_output_folder,
            bg=self.colors['danger'],
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=4,
            pady=6,
            relief="flat",
            cursor="hand2",
            activebackground="#C62828"
        )
        clear_output_btn.pack(side="left")
        # Grid להגדרות
        settings_container = tk.Frame(main_container, bg=self.colors['light_bg'])
        settings_container.pack(fill="x", pady=(0, 10))
        # הגדרות חורים
        holes_frame = tk.LabelFrame(
            settings_container,
            text=" ⚙️ הגדרות חורים ",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=15,
            bg="white",
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        holes_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        # קוטר חור
        tk.Label(holes_frame, text="קוטר חור (מ\"מ):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        diameter_spinbox = tk.Spinbox(
            holes_frame, 
            from_=1.0, 
            to=50.0, 
            increment=0.5,
            textvariable=self.hole_diameter,
            width=10
        )
        diameter_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        # מרחק מהפינות
        tk.Label(holes_frame, text="מרחק ממרכז החור (מ\"מ):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        margin_spinbox = tk.Spinbox(
            holes_frame, 
            from_=5.0, 
            to=100.0, 
            increment=1.0,
            textvariable=self.hole_margin,
            width=10
        )
        margin_spinbox.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        # הגדרות נוספות
        settings_frame = tk.LabelFrame(
            settings_container,
            text=" 🔧 הגדרות נוספות ",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=15,
            bg="white",
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        settings_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
        # מרווח Artboard
        tk.Label(settings_frame, text="מרווח Artboard (מ\"מ):", bg="white", font=("Segoe UI", 10)).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        artboard_spinbox = tk.Spinbox(
            settings_frame, 
            from_=0.0, 
            to=20.0, 
            increment=0.5,
            textvariable=self.artboard_margin,
            width=10,
            font=("Segoe UI", 10)
        )
        artboard_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        # עובי Stroke
        tk.Label(settings_frame, text="עובי Stroke (pt):", bg="white", font=("Segoe UI", 10)).grid(row=0, column=2, sticky="e", padx=5, pady=5)
        stroke_spinbox = tk.Spinbox(
            settings_frame, 
            from_=0.1, 
            to=2.0, 
            increment=0.05,
            textvariable=self.stroke_width,
            width=10,
            font=("Segoe UI", 10)
        )
        stroke_spinbox.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        # שיפור איכות תמונות
        enhance_check = tk.Checkbutton(
            settings_frame,
            text="🎯 שפר תמונות ל-300 DPI + CMYK",
            variable=self.enhance_images,
            bg="white",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors['success'],
            activebackground="white",
            activeforeground=self.colors['success'],
            selectcolor="white"
        )
        enhance_check.grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        # המרה ל-CMYK
        cmyk_check = tk.Checkbutton(
            settings_frame,
            text="🎨 המר RGB ל-CMYK (הדפסה)",
            variable=self.convert_to_cmyk,
            bg="white",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors['primary'],
            activebackground="white",
            activeforeground=self.colors['primary'],
            selectcolor="white"
        )
        cmyk_check.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        # הגדרות שוליים
        margins_frame = tk.LabelFrame(
            main_container,
            text=" 📏 הוספת שוליים לבנים ",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=15,
            bg="white",
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        margins_frame.pack(fill="x", pady=(0, 10))
        tk.Label(
            margins_frame, 
            text="הוסף שוליים לבנים מסביב הגרפיקה (בכל צד):",
            bg="white",
            font=("Segoe UI", 10)
        ).grid(row=0, column=0, sticky="w", padx=5, pady=5)
        additional_margin_spinbox = tk.Spinbox(
            margins_frame, 
            from_=0.0, 
            to=150.0, 
            increment=5.0,
            textvariable=self.additional_margin,
            width=15,
            font=("Segoe UI", 10)
        )
        additional_margin_spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        tk.Label(
            margins_frame,
            text="מ\"מ",
            bg="white",
            font=("Segoe UI", 10, "bold"),
            fg=self.colors['primary']
        ).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        tk.Label(
            margins_frame,
            text="הערה: השוליים יתווספו מסביב ה-Artboard הקיים (TrimBox/BleedBox)",
            bg="white",
            font=("Segoe UI", 9),
            fg=self.colors['light_text']
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=(0, 5))
        # תיאור הצבעים ובחירת שכבות
        colors_frame = tk.LabelFrame(
            main_container,
            text=" 🎨 שכבות Spot Color - בחר מה להוסיף ",
            font=("Segoe UI", 11, "bold"),
            padx=15,
            pady=15,
            bg="white",
            fg=self.colors['dark_text'],
            relief="solid",
            borderwidth=1
        )
        colors_frame.pack(fill="x", pady=(0, 10))
        # CutContour
        cutcontour_frame = tk.Frame(colors_frame, bg="white")
        cutcontour_frame.pack(fill="x", pady=2)
        cutcontour_check = tk.Checkbutton(
            cutcontour_frame,
            text="",
            variable=self.add_cutcontour,
            bg="white",
            activebackground="white",
            selectcolor="white"
        )
        cutcontour_check.pack(side="left")
        tk.Label(cutcontour_frame, text="CutContour - מג'נטה 100% (ורוד)", fg="#FF00FF", bg="white", font=("Segoe UI", 10)).pack(side="left")
        # Holes
        holes_frame = tk.Frame(colors_frame, bg="white")
        holes_frame.pack(fill="x", pady=2)
        holes_check = tk.Checkbutton(
            holes_frame,
            text="",
            variable=self.add_holes,
            bg="white",
            activebackground="white",
            selectcolor="white"
        )
        holes_check.pack(side="left")
        tk.Label(holes_frame, text="Holes - ציאן 50% + צהוב 100% (ירוק)", fg="#80FF00", bg="white", font=("Segoe UI", 10)).pack(side="left")
        # Crease
        crease_frame = tk.Frame(colors_frame, bg="white")
        crease_frame.pack(fill="x", pady=2)
        crease_check = tk.Checkbutton(
            crease_frame,
            text="",
            variable=self.replace_crease,
            bg="white",
            activebackground="white",
            selectcolor="white"
        )
        crease_check.pack(side="left")
        tk.Label(crease_frame, text="Crease - ציאן 100% (כחול) - זיהוי והחלפת שכבות קיימות", fg="#00FFFF", bg="white", font=("Segoe UI", 10)).pack(side="left")
        # כפתור עיבוד
        process_btn = tk.Button(
            main_container,
            text="▶  עבד את כל הקבצים",
            command=self.process_all_files,
            bg=self.colors['primary'],
            fg="white",
            font=("Segoe UI", 16, "bold"),
            pady=12,
            relief="flat",
            cursor="hand2",
            activebackground="#1565C0"
        )
        process_btn.pack(fill="x", pady=(0, 0))
        
        # שורת סטטוס
        self.status_label = tk.Label(
            self.root, 
            text="מוכן לעיבוד",
            font=("Segoe UI", 10),
            bg=self.colors['primary'],
            fg="white",
            anchor="w",
            padx=15,
            pady=8
        )
        self.status_label.pack(side="bottom", fill="x")
    
    def browse_files(self):
        filenames = filedialog.askopenfilenames(
            title="בחר קבצי PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filenames:
            for filename in filenames:
                if filename not in self.input_files:
                    self.input_files.append(filename)
            self.update_files_list()
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="בחר תיקייה")
        if folder:
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
    
    def update_files_list(self):
        # ניקוי הטבלה
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # איפוס מסננים
        self.column_filters = {}
        self.all_tree_items_dict = {}  # שמירת כל הפריטים לצורך מסננים

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
            resolution, dpi, colormode, pixelated = self.get_pdf_info(file_path)
            cutcontour = self.detect_spot_layer(file_path, 'CutContour')
            crease = self.detect_spot_layer(file_path, 'Crease')
            holes = self.detect_spot_layer(file_path, 'Holes')
            
            # יצירת ID ייחודי לפריט
            item_id = f"item_{item_counter}"
            item_values = ('✅', filename, resolution, dpi, colormode, pixelated, cutcontour, crease, holes)
            
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
        if duplicate_count > 0:
            self.files_duplicate_label.config(text=f" | {duplicate_count} כפולים")
            self.files_duplicate_label.pack(side="left")
        else:
            self.files_duplicate_label.pack_forget()

        # תווית אדומה - מפוקסלים
        if pixelated_count > 0:
            self.files_separator_label.pack(side="left")
            self.files_pixelated_label.config(text=f"{pixelated_count} מפוקסלים")
            self.files_pixelated_label.pack(side="left")
        else:
            self.files_separator_label.pack_forget()
            self.files_pixelated_label.pack_forget()

        # תווית כתומה - שגיאות
        if error_count > 0:
            self.files_error_separator_label.pack(side="left")
            self.files_error_label.config(text=f"{error_count} שגיאות")
            self.files_error_label.pack(side="left")
        else:
            self.files_error_separator_label.pack_forget()
            self.files_error_label.pack_forget()
    
    def get_pdf_info(self, pdf_path):
        """מחזיר מידע על PDF: רזולוציה, DPI ומצב פיקסול"""
        try:
            reader = PdfReader(pdf_path)
            page = reader.pages[0]
            
            # קבלת גבולות
            if hasattr(page, 'trimbox') and page.trimbox:
                bbox = page.trimbox
            elif hasattr(page, 'bleedbox') and page.bleedbox:
                bbox = page.bleedbox
            else:
                bbox = page.mediabox
            
            # חישוב מידות בנקודות
            width_pt = float(bbox.right) - float(bbox.left)
            height_pt = float(bbox.top) - float(bbox.bottom)
            
            # המרה למ"מ
            width_mm = width_pt / 72 * 25.4
            height_mm = height_pt / 72 * 25.4
            
            resolution = f"{int(width_mm)}x{int(height_mm)}"
            
            # חישוב DPI אמיתי של תמונות בעמוד
            actual_dpi = self.get_actual_dpi(page)
            
            # תמיד נציג ערך DPI - אם לא מצאנו תמונות, נציג 300 (וקטורי)
            if actual_dpi and actual_dpi > 0:
                dpi = f"{int(actual_dpi)}"
            else:
                dpi = "300"  # ברירת מחדל לגרפיקה וקטורית
            
            # זיהוי מצב צבעים
            colormode = self.detect_color_mode(page)
            
            # בדיקת תמונות בעמוד
            pixelated_status = self.check_images_quality(page, width_mm, height_mm)
            
            return resolution, dpi, colormode, pixelated_status
            
        except Exception as e:
            return "שגיאה", "N/A", "N/A", "שגיאה"
    
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
    
    def detect_color_mode(self, page):
        """מזהה אם ה-PDF במצב CMYK או RGB"""
        try:
            has_cmyk = False
            has_rgb = False

            def resolve_colorspace(cs, resources):
                # If cs is a NameObject, try to resolve from /ColorSpace dict
                if hasattr(cs, 'get_object'):
                    try:
                        cs = cs.get_object()
                    except Exception:
                        pass
                if isinstance(cs, str):
                    return cs
                # If it's a list, first element is the name
                if isinstance(cs, list) and len(cs) > 0:
                    return str(cs[0])
                # Try to resolve from /ColorSpace dict
                if resources and '/ColorSpace' in resources:
                    cs_dict = resources['/ColorSpace']
                    if isinstance(cs, str) and cs.startswith('/') and cs in cs_dict:
                        resolved = cs_dict[cs]
                        return resolve_colorspace(resolved, resources)
                    if hasattr(cs, 'name') and cs.name in cs_dict:
                        resolved = cs_dict[cs.name]
                        return resolve_colorspace(resolved, resources)
                return str(cs)

            # בדיקת ColorSpace בתמונות
            if '/Resources' in page and '/XObject' in page['/Resources']:
                xobjects = page['/Resources']['/XObject'].get_object()
                resources = page['/Resources']
                for obj_name in xobjects:
                    obj = xobjects[obj_name]
                    if obj.get('/Subtype') == '/Image':
                        colorspace = obj.get('/ColorSpace')
                        if colorspace:
                            cs_str = resolve_colorspace(colorspace, resources)
                            print(f"Image {obj_name}: ColorSpace = {cs_str}")
                            if 'CMYK' in cs_str.upper():
                                has_cmyk = True
                                print(f"  -> Detected as CMYK")
                            elif 'RGB' in cs_str.upper() and 'CMYK' not in cs_str.upper():
                                has_rgb = True
                                print(f"  -> Detected as RGB")

            # בדיקת ColorSpace ב-Resources (page-level)
            if '/Resources' in page and '/ColorSpace' in page['/Resources']:
                colorspaces = page['/Resources']['/ColorSpace']
                cs_str = str(colorspaces)
                print(f"Page ColorSpace: {cs_str}")
                # בדיקה ישירה על המילון
                if isinstance(colorspaces, dict):
                    for key, val in colorspaces.items():
                        # פתרון IndirectObject
                        try:
                            if hasattr(val, 'get_object'):
                                resolved = val.get_object()
                            else:
                                resolved = val
                        except Exception:
                            resolved = val
                        resolved_str = str(resolved)
                        print(f"  ColorSpace {key}: {resolved_str}")
                        if 'CMYK' in resolved_str.upper():
                            has_cmyk = True
                            print(f"    -> Detected as CMYK")
                        if 'RGB' in resolved_str.upper() and 'CMYK' not in resolved_str.upper():
                            has_rgb = True
                            print(f"    -> Detected as RGB")
                # בדיקה כללית על המחרוזת
                if 'CMYK' in cs_str.upper():
                    has_cmyk = True
                if 'RGB' in cs_str.upper() and 'CMYK' not in cs_str.upper():
                    has_rgb = True

            # החזרת התוצאה
            result = "N/A"
            if has_cmyk and has_rgb:
                result = "CMYK + RGB"
            elif has_cmyk:
                result = "CMYK"
            elif has_rgb:
                result = "RGB"

            print(f"Final result: {result}")
            return result

        except Exception as e:
            print(f"שגיאה בזיהוי מצב צבעים: {e}")
            import traceback
            traceback.print_exc()
            return "N/A"
    
    def get_content_bounding_box(self, page):
        """מזהה את הגבולות האמיתיים של התוכן הגרפי בעמוד"""
        try:
            # אם יש TrimBox - זה הגבול המדויק ביותר
            if hasattr(page, 'trimbox') and page.trimbox:
                bbox = page.trimbox
                return float(bbox.left), float(bbox.right), float(bbox.bottom), float(bbox.top)
            
            # אם יש BleedBox - גם טוב
            if hasattr(page, 'bleedbox') and page.bleedbox:
                bbox = page.bleedbox
                return float(bbox.left), float(bbox.right), float(bbox.bottom), float(bbox.top)
            
            # אחרת - ננסה לחשב מ-content stream
            content = page.get_contents()
            if content is None:
                bbox = page.mediabox
                return float(bbox.left), float(bbox.right), float(bbox.bottom), float(bbox.top)
            
            content_data = content.get_data()
            if isinstance(content_data, bytes):
                content_str = content_data.decode('latin-1', errors='ignore')
            else:
                content_str = str(content_data)
            
            # חיפוש פקודות ציור וחישוב bounding box
            # חיפוש קואורדינטות ב-content stream
            coords = re.findall(r'([\d\.]+)\s+([\d\.]+)\s+([ml]|re)', content_str)
            
            if coords:
                x_coords = [float(c[0]) for c in coords]
                y_coords = [float(c[1]) for c in coords]
                
                if x_coords and y_coords:
                    min_x = min(x_coords)
                    max_x = max(x_coords)
                    min_y = min(y_coords)
                    max_y = max(y_coords)
                    
                    # אם התוצאה סבירה (לא נקודה אחת), נשתמש בה
                    if (max_x - min_x) > 10 and (max_y - min_y) > 10:
                        return min_x, max_x, min_y, max_y
            
            # אם לא מצאנו או התוצאה לא מספיק טובה - נשתמש ב-MediaBox
            bbox = page.mediabox
            return float(bbox.left), float(bbox.right), float(bbox.bottom), float(bbox.top)
            
        except Exception as e:
            print(f"שגיאה בזיהוי גבולות התוכן: {e}")
            bbox = page.mediabox
            return float(bbox.left), float(bbox.right), float(bbox.bottom), float(bbox.top)
    
    def check_images_quality(self, page, page_width_mm, page_height_mm):
        """בודק את ה-DPI האמיתי של תמונות בעמוד"""
        try:
            if '/Resources' not in page or '/XObject' not in page['/Resources']:
                return "✓ ללא תמונות"
            
            xobjects = page['/Resources']['/XObject'].get_object()
            images_info = []
            
            for obj_name in xobjects:
                obj = xobjects[obj_name]
                
                if obj.get('/Subtype') == '/Image':
                    # קבלת מידות התמונה בפיקסלים
                    width_px = obj.get('/Width', 0)
                    height_px = obj.get('/Height', 0)
                    
                    if width_px and height_px:
                        # ניסיון לקבל את גודל התמונה בעמוד מתוך content stream
                        actual_dpi = self.calculate_image_dpi(page, obj_name, width_px, height_px)
                        
                        if actual_dpi:
                            images_info.append(actual_dpi)
            
            if not images_info:
                return "✓ ללא תמונות"
            
            # שימוש ב-DPI הנמוך ביותר
            min_dpi = min(images_info)
            
            # קביעת סטטוס
            if min_dpi >= 300:
                return f"✓ איכותי ({int(min_dpi)} DPI)"
            elif min_dpi >= 150:
                return f"⚠ בינוני ({int(min_dpi)} DPI)"
            else:
                return f"✗ מפוקסל ({int(min_dpi)} DPI)"
                
        except Exception as e:
            return "לא ניתן לבדוק"
    
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
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=5
        ).pack(fill="x", padx=10, pady=(10, 5))
        
        # רשימת ערכים
        tk.Label(
            filter_window,
            text="בחר ערכים לסינון:",
            font=("Segoe UI", 9, "bold")
        ).pack(pady=(5, 5))
        
        list_frame = tk.Frame(filter_window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        value_listbox = tk.Listbox(
            list_frame,
            selectmode="multiple",
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 9)
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
            font=("Segoe UI", 9, "bold"),
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
        """ביטול כל המסננים והצגת כל השורות"""
        self.column_filters = {}
        
        # אם יש פריטים מוסתרים, נשחזר אותם
        if hasattr(self, 'all_tree_items_dict') and self.all_tree_items_dict:
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
        """טיפול בלחיצה על הטבלה - שינוי checkbox"""
        region = self.files_tree.identify_region(event.x, event.y)
        if region == 'heading':
            return
        
        column = self.files_tree.identify_column(event.x)
        item = self.files_tree.identify_row(event.y)
        
        if item and column == '#1':  # עמודת checkbox
            values = list(self.files_tree.item(item)['values'])
            if values:
                # שינוי מצב checkbox
                values[0] = '✅' if values[0] == '⬜' else '⬜'
                self.files_tree.item(item, values=values)
    
    def toggle_all_checkboxes(self):
        """סימון/ביטול סימון של כל ה-checkboxes"""
        # בדיקה אם כולם מסומנים
        all_checked = True
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item)['values']
            if values and values[0] == '⬜':
                all_checked = False
                break
        
        # שינוי מצב כולם
        new_state = '⬜' if all_checked else '✅'
        for item in self.files_tree.get_children():
            values = list(self.files_tree.item(item)['values'])
            if values:
                values[0] = new_state
                self.files_tree.item(item, values=values)
    
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
        # קבלת הקבצים המסומנים (עם checkbox)
        selected_files = []
        for item in self.files_tree.get_children():
            values = self.files_tree.item(item)['values']
            if values and values[0] == '✅':
                filename = values[1]  # שם הקובץ בעמודה השנייה
                # חיפוש הקובץ המלא לפי שם
                for file_path in self.input_files:
                    if os.path.basename(file_path) == filename:
                        selected_files.append(file_path)
                        break
        
        total_files = len(selected_files)
        success_count = 0
        failed_files = []
        
        for index, input_pdf in enumerate(selected_files, 1):
            try:
                self.update_status(f"מעבד קובץ {index}/{total_files}: {os.path.basename(input_pdf)}...")
                self.process_single_pdf(input_pdf)
                success_count += 1
            except Exception as e:
                failed_files.append((os.path.basename(input_pdf), str(e)))
                print(f"שגיאה בעיבוד {input_pdf}: {e}")
        
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
    
    def process_single_pdf(self, input_pdf):
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
        
        # שוליים נוספים
        additional_margin_val = self.additional_margin.get() * mm
        
        # חישוב גדלים
        new_page_width = (right - left) + (artboard_margin * 2) + (additional_margin_val * 2)
        new_page_height = (top - bottom) + (artboard_margin * 2) + (additional_margin_val * 2)
        
        cutcontour_width_mm = int(round((right - left) / mm))
        cutcontour_height_mm = int(round((top - bottom) / mm))
        
        # קביעת תיקיית יעד
        output_folder = self.output_folder.get()
        if output_folder and os.path.isdir(output_folder):
            # שמירה בתיקיית יעד
            output_pdf = os.path.join(
                output_folder,
                f"{os.path.basename(base)}_{cutcontour_width_mm}x{cutcontour_height_mm}mm{ext}"
            )
        else:
            # שמירה בתיקיית המקור
            output_pdf = f"{base}_{cutcontour_width_mm}x{cutcontour_height_mm}mm{ext}"
        
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
        
        # Holes - ממוקמים על פי margin מהפינות של העמוד החדש
        if self.add_holes.get():
            c.setStrokeColor(holes_color)
            c.setLineWidth(stroke_width)
            
            holes = [
                (margin, new_page_height - margin),
                (new_page_width - margin, new_page_height - margin),
                (margin, margin),
                (new_page_width - margin, margin)
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

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()
