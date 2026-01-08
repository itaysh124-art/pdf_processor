"""
מודול אוטומציה - ניטור תיקיות ועיבוד אוטומטי של קבצי PDF
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
import time
import shutil
import glob
from .config import COLORS, FONTS


class AutomationModule:
    """מחלקה לניהול אוטומציה"""
    
    def __init__(self, parent_app):
        """אתחול מודול האוטומציה"""
        self.app = parent_app
        self.automation_active = False
        self.automation_thread = None
        self.watch_folder = tk.StringVar(value="")
        self.automation_output_folder = tk.StringVar(value="")
        self.automation_error_folder = tk.StringVar(value="")
        self.processed_files = set()
    
    def create_automation_tab(self, parent):
        """יצירת ממשק אוטומציה"""
        # Main container with scroll
        main_container = tk.Frame(parent, bg=COLORS['light_bg'])
        main_container.pack(fill="both", expand=True)
        
        # יצירת Canvas ו-Scrollbar
        canvas = tk.Canvas(main_container, bg=COLORS['light_bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['light_bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # הוספת גלילה עם גלגלת העכבר
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Container לתוכן
        container = tk.Frame(scrollable_frame, bg=COLORS['light_bg'])
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # תיקיית ניטור
        watch_frame = tk.LabelFrame(
            container,
            text=" 📁 תיקיית ניטור ",
            font=FONTS['heading'],
            padx=15,
            pady=15, bg=COLORS['card_bg'],
            fg=COLORS['dark_text'],
            relief="solid",
            borderwidth=1
        )
        watch_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            watch_frame,
            text="בחר תיקיה לניטור - כל קובץ PDF חדש יטופל אוטומטית",
            font=FONTS['small'],
            fg=COLORS['light_text'], bg=COLORS['card_bg']
        ).pack(anchor="w", pady=(0, 8))
        
        watch_entry_frame = tk.Frame(watch_frame, bg=COLORS['card_bg'])
        watch_entry_frame.pack(fill="x")
        
        watch_entry = tk.Entry(
            watch_entry_frame,
            textvariable=self.watch_folder,
            font=FONTS['label'],
            relief="solid",
            borderwidth=1
        )
        watch_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(
            watch_entry_frame,
            text="📁 בחר תיקיה",
            command=self.browse_watch_folder,
            bg=COLORS['primary'],
            fg="white",
            font=FONTS['small'] + ('bold',),
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        ).pack(side="right")
        
        # תיקיות יעד
        dest_frame = tk.LabelFrame(
            container,
            text=" 📂 תיקיות יעד ",
            font=FONTS['heading'],
            padx=15,
            pady=15, bg=COLORS['card_bg'],
            fg=COLORS['dark_text'],
            relief="solid",
            borderwidth=1
        )
        dest_frame.pack(fill="x", pady=(0, 10))
        
        # תיקיית הצלחה
        tk.Label(
            dest_frame,
            text="תיקיית קבצים מעובדים:",
            font=FONTS['small'] + ('bold',), bg=COLORS['card_bg']
        ).pack(anchor="w", pady=(0, 5))
        
        success_entry_frame = tk.Frame(dest_frame, bg=COLORS['card_bg'])
        success_entry_frame.pack(fill="x", pady=(0, 10))
        
        tk.Entry(
            success_entry_frame,
            textvariable=self.automation_output_folder,
            font=FONTS['label'],
            relief="solid",
            borderwidth=1
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(
            success_entry_frame,
            text="📁 בחר",
            command=self.browse_automation_output,
            bg=COLORS['success'],
            fg="white",
            font=FONTS['small'] + ('bold',),
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        ).pack(side="right")
        
        # תיקיית שגיאות
        tk.Label(
            dest_frame,
            text="תיקיית קבצים עם שגיאות (UnDone):",
            font=FONTS['small'] + ('bold',), bg=COLORS['card_bg']
        ).pack(anchor="w", pady=(0, 5))
        
        error_entry_frame = tk.Frame(dest_frame, bg=COLORS['card_bg'])
        error_entry_frame.pack(fill="x")
        
        tk.Entry(
            error_entry_frame,
            textvariable=self.automation_error_folder,
            font=FONTS['label'],
            relief="solid",
            borderwidth=1
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(
            error_entry_frame,
            text="📁 בחר",
            command=self.browse_automation_error,
            bg=COLORS['danger'],
            fg="white",
            font=FONTS['small'] + ('bold',),
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        ).pack(side="right")
        
        # הגדרות עיבוד
        settings_frame = tk.LabelFrame(
            container,
            text=" ⚙️ הגדרות עיבוד ",
            font=FONTS['heading'],
            padx=15,
            pady=15, bg=COLORS['card_bg'],
            fg=COLORS['dark_text'],
            relief="solid",
            borderwidth=1
        )
        settings_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            settings_frame,
            text="התכונות שיופעלו באופן אוטומטי על כל קובץ:",
            font=FONTS['small'],
            fg=COLORS['light_text'], bg=COLORS['card_bg']
        ).pack(anchor="w", pady=(0, 10))
        
        # Checkboxes לתכונות
        features_container = tk.Frame(settings_frame, bg=COLORS['card_bg'])
        features_container.pack(fill="x")
        
        tk.Checkbutton(
            features_container,
            text="✂️ הוסף CutContour",
            variable=self.app.add_cutcontour,
            font=FONTS['label'], bg=COLORS['card_bg'],
            activebackground=COLORS['card_bg']
        ).pack(anchor="w", pady=2)
        
        tk.Checkbutton(
            features_container,
            text="🕳️ הוסף חורים",
            variable=self.app.add_holes,
            font=FONTS['label'], bg=COLORS['card_bg'],
            activebackground=COLORS['card_bg']
        ).pack(anchor="w", pady=2)
        
        tk.Checkbutton(
            features_container,
            text="📐 החלף Crease",
            variable=self.app.replace_crease,
            font=FONTS['label'], bg=COLORS['card_bg'],
            activebackground=COLORS['card_bg']
        ).pack(anchor="w", pady=2)
        
        tk.Checkbutton(
            features_container,
            text="🎨 המר ל-CMYK",
            variable=self.app.convert_to_cmyk,
            font=FONTS['label'], bg=COLORS['card_bg'],
            activebackground=COLORS['card_bg']
        ).pack(anchor="w", pady=2)
        
        # הגדרות חורים
        holes_settings_frame = tk.LabelFrame(
            container,
            text=" 🕳️ הגדרות חורים ",
            font=FONTS['heading'],
            padx=15,
            pady=15, bg=COLORS['card_bg'],
            fg=COLORS['dark_text'],
            relief="solid",
            borderwidth=1
        )
        holes_settings_frame.pack(fill="x", pady=(0, 10))
        
        # קוטר חור
        hole_diameter_frame = tk.Frame(holes_settings_frame, bg=COLORS['card_bg'])
        hole_diameter_frame.pack(fill="x", pady=5)
        
        tk.Label(
            hole_diameter_frame,
            text="קוטר חור (מ\"מ):",
            font=FONTS['label'], bg=COLORS['card_bg']
        ).pack(side="left", padx=(0, 10))
        
        tk.Spinbox(
            hole_diameter_frame,
            from_=1.0,
            to=50.0,
            increment=0.5,
            textvariable=self.app.hole_diameter,
            width=10,
            font=FONTS['label']
        ).pack(side="left")
        
        # מרחק ממרכז החור
        hole_margin_frame = tk.Frame(holes_settings_frame, bg=COLORS['card_bg'])
        hole_margin_frame.pack(fill="x", pady=5)
        
        tk.Label(
            hole_margin_frame,
            text="מרחק ממרכז החור (מ\"מ):",
            font=FONTS['label'], bg=COLORS['card_bg']
        ).pack(side="left", padx=(0, 10))
        
        tk.Spinbox(
            hole_margin_frame,
            from_=5.0,
            to=100.0,
            increment=1.0,
            textvariable=self.app.hole_margin,
            width=10,
            font=FONTS['label']
        ).pack(side="left")
        
        # סטטוס ולוג
        status_frame = tk.LabelFrame(
            container,
            text=" 📊 סטטוס ",
            font=FONTS['heading'],
            padx=15,
            pady=15, bg=COLORS['card_bg'],
            fg=COLORS['dark_text'],
            relief="solid",
            borderwidth=1
        )
        status_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.automation_status_label = tk.Label(
            status_frame,
            text="⚪ האוטומציה כבויה",
            font=FONTS['summary'], bg=COLORS['card_bg'],
            fg=COLORS['light_text']
        )
        self.automation_status_label.pack(pady=(0, 10))
        
        # לוג
        log_scroll = tk.Scrollbar(status_frame)
        log_scroll.pack(side="right", fill="y")
        
        self.automation_log = tk.Text(
            status_frame,
            height=10,
            font=FONTS['log'],
            yscrollcommand=log_scroll.set,
            relief="solid",
            borderwidth=1
        )
        self.automation_log.pack(fill="both", expand=True)
        log_scroll.config(command=self.automation_log.yview)
        
        # כפתורי בקרה
        control_frame = tk.Frame(container, bg=COLORS['light_bg'])
        control_frame.pack(fill="x")
        
        self.start_automation_btn = tk.Button(
            control_frame,
            text="▶️ הפעל אוטומציה",
            command=self.start_automation,
            bg=COLORS['success'],
            fg="white",
            font=FONTS['button'],
            padx=30,
            pady=15,
            relief="flat",
            cursor="hand2"
        )
        self.start_automation_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.stop_automation_btn = tk.Button(
            control_frame,
            text="⏹️ עצור אוטומציה",
            command=self.stop_automation,
            bg=COLORS['danger'],
            fg="white",
            font=FONTS['button'],
            padx=30,
            pady=15,
            relief="flat",
            cursor="hand2",
            state="disabled"
        )
        self.stop_automation_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
    
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
        self.automation_log.insert("end", f"[{timestamp}] {message}\n")
        self.automation_log.see("end")
        self.app.root.update()
    
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
            fg=COLORS['success']
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
            fg=COLORS['light_text']
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
            # קריאה לפונקציית העיבוד של האפליקציה הראשית
            output_path = os.path.join(
                self.automation_output_folder.get(),
                os.path.basename(pdf_path)
            )
            
            # שימוש בפונקציה הקיימת
            self.app.process_single_pdf(pdf_path, output_path)
            return True
            
        except Exception as e:
            self.log_automation(f"❌ שגיאה בעיבוד {os.path.basename(pdf_path)}: {e}")
            return False
