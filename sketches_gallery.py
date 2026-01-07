# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
import os
import glob
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image, ImageTk
import threading


class SketchesGalleryTab:
    def __init__(self, parent, colors, pdf_app=None):
        self.parent = parent
        self.colors = colors
        self.pdf_app = pdf_app  # התייחסות לאפליקציה הראשית
        self.sketches = []
        self.selected_sketch = None
        
        self.create_ui()
        
    def create_ui(self):
        """יצירת ממשק לשונית הסקיצות"""
        # כותרת וכפתור רענון
        header_frame = tk.Frame(self.parent, bg=self.colors['light_bg'])
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = tk.Label(
            header_frame,
            text="📸 גלריית סקיצות לאישור לקוח",
            font=("Arial", 16, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['light_bg']
        )
        title_label.pack(side="right", padx=10)
        
        browse_folder_btn = tk.Button(
            header_frame,
            text="📁 בחר תיקייה",
            command=self.browse_folder,
            bg=self.colors['secondary'] if 'secondary' in self.colors else self.colors['primary'],
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        browse_folder_btn.pack(side="left", padx=(10, 5))
        
        refresh_btn = tk.Button(
            header_frame,
            text="🔄 רענן",
            command=self.refresh_sketches,
            bg=self.colors['primary'],
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        refresh_btn.pack(side="left", padx=5)
        
        # Frame עיקרי עם פריסה split
        main_frame = tk.Frame(self.parent, bg=self.colors['light_bg'])
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # חלוקה ל-2 עמודות: רשימה משמאל, תצוגה מימין
        # רשימת סקיצות (משמאל)
        list_frame = tk.Frame(main_frame, bg=self.colors['card_bg'])
        list_frame.pack(side="right", fill="both", padx=(0, 5), pady=5, expand=False)
        
        list_label = tk.Label(
            list_frame,
            text="סקיצות זמינות",
            font=("Arial", 12, "bold"),
            fg=self.colors['light_text'],
            bg=self.colors['card_bg']
        )
        list_label.pack(pady=10)
        
        # Listbox עם scrollbar
        listbox_container = tk.Frame(list_frame, bg=self.colors['card_bg'])
        listbox_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        scrollbar_list = ttk.Scrollbar(listbox_container, orient="vertical")
        self.sketches_listbox = tk.Listbox(
            listbox_container,
            bg=self.colors['dark_bg'],
            fg=self.colors['light_text'],
            font=("Arial", 10),
            selectbackground=self.colors['primary'],
            selectforeground="white",
            relief="flat",
            bd=0,
            yscrollcommand=scrollbar_list.set,
            width=35
        )
        scrollbar_list.config(command=self.sketches_listbox.yview)
        
        self.sketches_listbox.pack(side="right", fill="both", expand=True)
        scrollbar_list.pack(side="left", fill="y")
        
        self.sketches_listbox.bind('<<ListboxSelect>>', self.on_sketch_select)
        self.sketches_listbox.bind('<Double-Button-1>', self.open_sketch_file)
        
        # פאנל תצוגה (מימין)
        preview_frame = tk.Frame(main_frame, bg=self.colors['card_bg'])
        preview_frame.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        
        preview_label = tk.Label(
            preview_frame,
            text="תצוגה מקדימה",
            font=("Arial", 12, "bold"),
            fg=self.colors['light_text'],
            bg=self.colors['card_bg']
        )
        preview_label.pack(pady=10)
        
        # Canvas לתצוגת הסקיצה
        self.preview_canvas = tk.Canvas(
            preview_frame,
            bg=self.colors['dark_bg'],
            highlightthickness=0
        )
        self.preview_canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Label למידע על הסקיצה
        self.info_label = tk.Label(
            preview_frame,
            text="בחר סקיצה מהרשימה לתצוגה מקדימה",
            font=("Arial", 10),
            fg=self.colors['light_text'],
            bg=self.colors['card_bg'],
            justify="center"
        )
        self.info_label.pack(pady=(0, 10))
        
        # כפתורים
        buttons_frame = tk.Frame(preview_frame, bg=self.colors['card_bg'])
        buttons_frame.pack(pady=(0, 10))
        
        # כפתור אישור - ירוק וגדול
        approve_btn = tk.Button(
            buttons_frame,
            text="✅ אישור - העבר לייצור",
            command=self.approve_sketch,
            bg='#4CAF50',  # ירוק
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=30,
            pady=12,
            cursor="hand2"
        )
        approve_btn.pack(side="top", pady=(0, 10))
        
        # שורה שנייה של כפתורים
        action_buttons_frame = tk.Frame(preview_frame, bg=self.colors['card_bg'])
        action_buttons_frame.pack(pady=(0, 10))
        
        open_btn = tk.Button(
            action_buttons_frame,
            text="📂 פתח קובץ",
            command=self.open_sketch_file,
            bg=self.colors['primary'],
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        open_btn.pack(side="right", padx=5)
        
        delete_btn = tk.Button(
            action_buttons_frame,
            text="🗑️ מחק",
            command=self.delete_sketch,
            bg=self.colors['warning'],
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        delete_btn.pack(side="left", padx=5)
        
        # טעינה ראשונית
        self.refresh_sketches()
    
    def refresh_sketches(self):
        """סריקה מחודשת של סקיצות בתיקיות"""
        self.sketches = []
        self.sketches_listbox.delete(0, tk.END)
        
        # חיפוש קבצי סקיצות בכל הכוננים והתיקיות
        found_files = []
        
        # בדיקה אם יש תיקיית יעד מוגדרת
        output_folder = None
        if self.pdf_app and hasattr(self.pdf_app, 'output_folder'):
            output_folder = self.pdf_app.output_folder.get()
        
        # חיפוש בתיקיית היעד אם קיימת
        if output_folder and os.path.exists(output_folder):
            for root, dirs, files in os.walk(output_folder):
                for file in files:
                    if file.startswith("skiza_") and file.endswith(".pdf"):
                        found_files.append(os.path.join(root, file))
        
        # חיפוש בתיקיה הנוכחית ובתת-תיקיות
        current_dir = os.getcwd()
        for root, dirs, files in os.walk(current_dir):
            for file in files:
                if file.startswith("skiza_") and file.endswith(".pdf"):
                    full_path = os.path.join(root, file)
                    if full_path not in found_files:
                        found_files.append(full_path)
        
        # חיפוש גם בתיקיית pdf אם קיימת
        pdf_dir = os.path.join(current_dir, "pdf")
        if os.path.exists(pdf_dir):
            for root, dirs, files in os.walk(pdf_dir):
                for file in files:
                    if file.startswith("skiza_") and file.endswith(".pdf"):
                        full_path = os.path.join(root, file)
                        if full_path not in found_files:
                            found_files.append(full_path)
        
        # חיפוש גם בתיקייה מעל (parent directory)
        parent_dir = os.path.dirname(current_dir)
        pdf_parent = os.path.join(parent_dir, "pdf")
        if os.path.exists(pdf_parent):
            for root, dirs, files in os.walk(pdf_parent):
                for file in files:
                    if file.startswith("skiza_") and file.endswith(".pdf"):
                        full_path = os.path.join(root, file)
                        if full_path not in found_files:
                            found_files.append(full_path)
        
        # הסרת כפילויות והמרה לנתיבים מלאים
        found_files = list(set(os.path.abspath(f) for f in found_files))
        found_files.sort(key=os.path.getmtime, reverse=True)  # מיון לפי תאריך, החדשים ראשון
        
        for filepath in found_files:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                mod_time = os.path.getmtime(filepath)
                date_str = datetime.fromtimestamp(mod_time).strftime("%d/%m/%Y %H:%M")
                
                # שמירת מידע על הסקיצה
                sketch_info = {
                    'path': filepath,
                    'filename': filename,
                    'date': date_str,
                    'size': os.path.getsize(filepath)
                }
                self.sketches.append(sketch_info)
                
                # הוספה ל-Listbox
                display_text = f"{filename}\n  {date_str}"
                self.sketches_listbox.insert(tk.END, display_text)
        
        # עדכון מונה
        count_text = f"נמצאו {len(self.sketches)} סקיצות"
        if len(self.sketches) == 0:
            count_text = "לא נמצאו סקיצות.\nהסקיצות נשמרות עם שם skiza_*.pdf\nלחץ על 'בחר תיקייה' לחפש בתיקייה אחרת"
        if hasattr(self, 'info_label') and not self.selected_sketch:
            self.info_label.config(text=count_text)
    
    def browse_folder(self):
        """בחירת תיקייה לחיפוש סקיצות"""
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="בחר תיקייה לחיפוש סקיצות")
        if folder:
            self.search_in_folder(folder)
    
    def search_in_folder(self, folder):
        """חיפוש סקיצות בתיקייה ספציפית"""
        self.sketches = []
        self.sketches_listbox.delete(0, tk.END)
        
        found_files = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.startswith("skiza_") and file.endswith(".pdf"):
                    found_files.append(os.path.join(root, file))
        
        found_files.sort(key=os.path.getmtime, reverse=True)
        
        for filepath in found_files:
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                mod_time = os.path.getmtime(filepath)
                date_str = datetime.fromtimestamp(mod_time).strftime("%d/%m/%Y %H:%M")
                
                sketch_info = {
                    'path': filepath,
                    'filename': filename,
                    'date': date_str,
                    'size': os.path.getsize(filepath)
                }
                self.sketches.append(sketch_info)
                
                display_text = f"{filename}\n  {date_str}"
                self.sketches_listbox.insert(tk.END, display_text)
        
        count_text = f"נמצאו {len(self.sketches)} סקיצות בתיקייה: {folder}"
        if len(self.sketches) == 0:
            count_text = f"לא נמצאו סקיצות בתיקייה:\n{folder}"
        if hasattr(self, 'info_label'):
            self.info_label.config(text=count_text)
    
    def on_sketch_select(self, event):
        """טיפול בבחירת סקיצה מהרשימה"""
        selection = self.sketches_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.sketches):
            return
        
        self.selected_sketch = self.sketches[index]
        self.show_preview()
    
    def show_preview(self):
        """הצגת תצוגה מקדימה של הסקיצה"""
        if not self.selected_sketch:
            return
        
        filepath = self.selected_sketch['path']
        
        def load_preview():
            try:
                # פתיחת PDF
                doc = fitz.open(filepath)
                page = doc[0]  # עמוד ראשון
                
                # חישוב גודל תצוגה
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                
                if canvas_width <= 1 or canvas_height <= 1:
                    canvas_width = 600
                    canvas_height = 800
                
                # רנדור לתמונה
                zoom = min(canvas_width / page.rect.width, canvas_height / page.rect.height) * 0.9
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                # המרה ל-PIL Image
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # המרה ל-PhotoImage
                photo = ImageTk.PhotoImage(img)
                
                # עדכון Canvas - חייב להיות ב-main thread
                self.preview_canvas.delete("all")
                x = canvas_width // 2
                y = canvas_height // 2
                self.preview_canvas.create_image(x, y, image=photo, anchor="center")
                self.preview_canvas.image = photo  # שמירת reference
                
                # עדכון מידע
                size_kb = self.selected_sketch['size'] / 1024
                info_text = f"{self.selected_sketch['filename']}\n"
                info_text += f"תאריך: {self.selected_sketch['date']}\n"
                info_text += f"גודל: {size_kb:.1f} KB\n"
                info_text += f"עמודים: {len(doc)}"
                
                self.info_label.config(text=info_text)
                
                doc.close()
                
            except Exception as e:
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(
                    self.preview_canvas.winfo_width() // 2,
                    self.preview_canvas.winfo_height() // 2,
                    text=f"שגיאה בטעינת תצוגה מקדימה:\n{str(e)}",
                    fill=self.colors['warning'],
                    font=("Arial", 10),
                    anchor="center"
                )
        
        # טעינה ב-thread נפרד כדי לא לחסום את הממשק
        threading.Thread(target=load_preview, daemon=True).start()
    
    def open_sketch_file(self, event=None):
        """פתיחת קובץ הסקיצה"""
        if not self.selected_sketch:
            return
        
        filepath = self.selected_sketch['path']
        if os.path.exists(filepath):
            os.startfile(filepath)
    
    def delete_sketch(self):
        """מחיקת סקיצה"""
        if not self.selected_sketch:
            return
        
        from tkinter import messagebox
        
        filename = self.selected_sketch['filename']
        result = messagebox.askyesno(
            "אישור מחיקה",
            f"האם אתה בטוח שברצונך למחוק את הסקיצה?\n{filename}",
            icon="warning"
        )
        
        if result:
            try:
                filepath = self.selected_sketch['path']
                os.remove(filepath)
                messagebox.showinfo("הצלחה", f"הסקיצה נמחקה בהצלחה:\n{filename}")
                self.selected_sketch = None
                self.preview_canvas.delete("all")
                self.refresh_sketches()
            except Exception as e:
                messagebox.showerror("שגיאה", f"שגיאה במחיקת הסקיצה:\n{str(e)}")
    
    def approve_sketch(self):
        """אישור סקיצה והעברת הקבצים המעובדים לתיקיית ייצור"""
        if not self.selected_sketch:
            from tkinter import messagebox
            messagebox.showwarning("אזהרה", "אנא בחר סקיצה לאישור")
            return
        
        from tkinter import messagebox
        import shutil
        
        filename = self.selected_sketch['filename']
        sketch_path = self.selected_sketch['path']
        
        # בדיקה אם יש תיקיית ייצור מוגדרת
        production_folder = None
        if self.pdf_app and hasattr(self.pdf_app, 'production_folder'):
            production_folder = self.pdf_app.production_folder.get()
        
        if not production_folder or not os.path.isdir(production_folder):
            messagebox.showerror(
                "שגיאה",
                "תיקיית ייצור לא הוגדרה!\n\nאנא הגדר תיקיית ייצור בלשונית 'עיבוד ידני'"
            )
            return
        
        # חילוץ מספר הזמנה או שם בסיס מהסקיצה
        # skiza_12345.pdf -> 12345
        base_name = os.path.splitext(filename)[0]  # skiza_12345
        if base_name.startswith('skiza_'):
            identifier = base_name[6:]  # 12345
        else:
            identifier = base_name
        
        # חיפוש קבצים מעובדים שמתאימים לסקיצה
        # הם אמורים להיות באותה תיקייה של הסקיצה או בתיקיית הפלט
        sketch_dir = os.path.dirname(sketch_path)
        
        # חיפוש קבצים שמכילים את המזהה בשם
        moved_files = []
        errors = []
        
        # חיפוש בתיקיית הסקיצה
        for root, dirs, files in os.walk(sketch_dir):
            for file in files:
                # חיפוש קבצים PDF (לא סקיצות) שמכילים מידע דומה
                if file.endswith('.pdf') and not file.startswith('skiza_'):
                    file_path = os.path.join(root, file)
                    
                    try:
                        # העתקה לתיקיית ייצור
                        dest_path = os.path.join(production_folder, file)
                        shutil.copy2(file_path, dest_path)
                        moved_files.append(file)
                        print(f"[APPROVAL] Copied to production: {file}")
                    except Exception as e:
                        errors.append(f"{file}: {str(e)}")
        
        # גם להעתיק את הסקיצה עצמה לתיקיית הייצור
        try:
            sketch_dest = os.path.join(production_folder, filename)
            shutil.copy2(sketch_path, sketch_dest)
            moved_files.append(filename)
            
            # העתקת גם את התמונה אם קיימת
            image_path = sketch_path.replace('.pdf', '.jpg')
            if os.path.exists(image_path):
                image_dest = os.path.join(production_folder, os.path.basename(image_path))
                shutil.copy2(image_path, image_dest)
                moved_files.append(os.path.basename(image_path))
        except Exception as e:
            errors.append(f"Sketch: {str(e)}")
        
        # הצגת תוצאות
        if moved_files:
            files_list = "\n".join(f"  • {f}" for f in moved_files)
            msg = f"✅ הסקיצה אושרה בהצלחה!\n\n"
            msg += f"הקבצים הבאים הועתקו לתיקיית ייצור:\n{files_list}\n\n"
            msg += f"תיקיית ייצור: {production_folder}"
            
            if errors:
                msg += f"\n\n⚠️ שגיאות:\n" + "\n".join(f"  • {e}" for e in errors)
            
            messagebox.showinfo("אישור הצליח", msg)
        else:
            messagebox.showwarning(
                "אזהרה",
                f"לא נמצאו קבצים להעברה.\n\nתיקיית חיפוש: {sketch_dir}"
            )
