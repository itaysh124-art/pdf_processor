"""
Changes Log Module
מודול לניהול ויומן של שינויים שבוצעו בקבצי PDF
"""
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os


class ChangesLog:
    """מחלקה לניהול יומן שינויים"""
    
    def __init__(self):
        self.changes = []  # רשימת כל השינויים
        
    def add_change(self, input_file, output_file, changes_made, success=True, error_message=None, order_number=""):
        """
        הוספת שינוי ליומן
        
        Args:
            input_file: נתיב קובץ המקור
            output_file: נתיב קובץ היעד
            changes_made: רשימת השינויים שבוצעו
            success: האם העיבוד הצליח
            error_message: הודעת שגיאה (אם יש)
            order_number: מספר הזמנה
        """
        change_entry = {
            'timestamp': datetime.now(),
            'input_file': input_file,
            'output_file': output_file,
            'changes': changes_made,
            'success': success,
            'error': error_message,
            'order_number': order_number
        }
        self.changes.append(change_entry)
    
    def get_changes(self):
        """החזרת כל השינויים"""
        return self.changes
    
    def clear_changes(self):
        """ניקוי יומן השינויים"""
        self.changes = []
    
    @staticmethod
    def generate_ai_summary(changes_list):
        """
        יצירת סיכום AI של השינויים
        
        Args:
            changes_list: רשימת השינויים
            
        Returns:
            str: סיכום מפורט של השינויים
        """
        if not changes_list:
            return "טרם בוצעו שינויים בקבצים"
        
        # ספירת כל סוג של שינוי
        change_counts = {}
        for change in changes_list:
            if change in change_counts:
                change_counts[change] += 1
            else:
                change_counts[change] = 1
        
        # בניית סיכום מפורט
        summary = "📊 סיכום השינויים שבוצעו:\n"
        summary += "=" * 50 + "\n\n"
        
        # הצגת כל סוג שינוי עם ספירה
        for change_type, count in sorted(change_counts.items(), key=lambda x: x[1], reverse=True):
            if count > 1:
                summary += f"✓ {change_type} - בוצע ב-{count} קבצים\n"
            else:
                summary += f"✓ {change_type}\n"
        
        summary += "\n" + "=" * 50 + "\n"
        summary += f"סה\"כ פעולות שבוצעו: {len(changes_list)}\n"
        summary += f"סוגי שינויים שונים: {len(change_counts)}"
        
        return summary


class ChangesLogTab:
    """טאב יומן שינויים בממשק"""
    
    def __init__(self, parent, colors):
        self.parent = parent
        self.colors = colors
        self.changes_log = ChangesLog()
        
        # יצירת הממשק
        self.create_ui()
    
    def create_ui(self):
        """יצירת ממשק המשתמש לטאב"""
        # כותרת
        header_frame = tk.Frame(self.parent, bg=self.colors['card_bg'], pady=15, padx=20)
        header_frame.pack(fill="x", padx=8, pady=(8, 0))
        
        tk.Label(
            header_frame,
            text="📋 יומן שינויים",
            font=("Arial", 16, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['card_bg']
        ).pack(side="left")
        
        # כפתור ניקוי יומן
        clear_btn = tk.Button(
            header_frame,
            text="🗑️ נקה יומן",
            command=self.clear_log,
            bg=self.colors['danger'],
            fg="white",
            font=("Arial", 10, "bold"),
            padx=15,
            pady=5,
            relief="flat",
            cursor="hand2"
        )
        clear_btn.pack(side="right", padx=5)
        
        # סיכום
        self.summary_label = tk.Label(
            header_frame,
            text="0 קבצים עובדו",
            font=("Arial", 11),
            fg=self.colors['dark_text'],
            bg=self.colors['card_bg']
        )
        self.summary_label.pack(side="right", padx=20)
        
        # טבלת שינויים
        table_frame = tk.Frame(self.parent, bg=self.colors['card_bg'], padx=8, pady=8)
        table_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Treeview
        columns = ('time', 'order_number', 'input_file', 'output_file', 'status', 'changes')
        self.changes_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        # הגדרת כותרות
        self.changes_tree.heading('time', text='שעה')
        self.changes_tree.heading('order_number', text='מספר הזמנה')
        self.changes_tree.heading('input_file', text='קובץ מקור')
        self.changes_tree.heading('output_file', text='קובץ יעד')
        self.changes_tree.heading('status', text='סטטוס')
        self.changes_tree.heading('changes', text='שינויים')
        
        # הגדרת רוחב עמודות - דינמי
        self.changes_tree.column('time', width=80, minwidth=60, stretch=True, anchor='center')
        self.changes_tree.column('order_number', width=100, minwidth=80, stretch=True, anchor='center')
        self.changes_tree.column('input_file', width=180, minwidth=120, stretch=True, anchor='w')
        self.changes_tree.column('output_file', width=180, minwidth=120, stretch=True, anchor='w')
        self.changes_tree.column('status', width=80, minwidth=60, stretch=True, anchor='center')
        self.changes_tree.column('changes', width=350, minwidth=200, stretch=True, anchor='w')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.changes_tree.yview)
        self.changes_tree.configure(yscrollcommand=scrollbar.set)
        
        self.changes_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # דאבל קליק לפרטים
        self.changes_tree.bind('<Double-Button-1>', self.show_details)
        
        # פאנל פרטים
        details_frame = tk.Frame(self.parent, bg=self.colors['card_bg'], padx=20, pady=15)
        details_frame.pack(fill="x", padx=8, pady=(0, 8))
        
        tk.Label(
            details_frame,
            text="פירוט AI של השינויים:",
            font=("Arial", 12, "bold"),
            fg=self.colors['primary'],
            bg=self.colors['card_bg']
        ).pack(anchor="w", pady=(0, 5))
        
        # Text widget for AI summary
        self.details_text = tk.Text(
            details_frame,
            height=8,
            font=("Arial", 10),
            bg=self.colors['dark_bg'],
            fg=self.colors['dark_text'],
            wrap="word",
            padx=10,
            pady=10
        )
        self.details_text.pack(fill="x", pady=5)
        self.details_text.config(state='disabled')
    
    def add_change(self, input_file, output_file, changes_made, success=True, error_message=None, order_number=""):
        """הוספת שינוי ליומן והצגה בטבלה"""
        # הוספה ליומן
        self.changes_log.add_change(input_file, output_file, changes_made, success, error_message, order_number)
        
        # הוספה לטבלה
        timestamp = datetime.now().strftime("%H:%M:%S")
        input_name = os.path.basename(input_file)
        output_name = os.path.basename(output_file) if output_file else "-"
        status = "✓ הצלחה" if success else "✗ שגיאה"
        changes_summary = ", ".join(changes_made) if changes_made else "אין שינויים"
        
        self.changes_tree.insert('', 0, values=(timestamp, order_number, input_name, output_name, status, changes_summary))
        
        # עדכון סיכום
        total = len(self.changes_log.get_changes())
        successful = sum(1 for c in self.changes_log.get_changes() if c['success'])
        self.summary_label.config(text=f"{total} קבצים עובדו | {successful} הצליחו")
        
        # עדכון פירוט AI
        self.update_ai_summary()
    
    def update_ai_summary(self):
        """עדכון הפירוט AI"""
        changes = self.changes_log.get_changes()
        if not changes:
            summary = "טרם בוצעו שינויים"
        else:
            # בניית סיכום מפורט
            all_changes = []
            for change in changes:
                if change['success'] and change['changes']:
                    all_changes.extend(change['changes'])
            
            summary = ChangesLog.generate_ai_summary(all_changes)
        
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', 'end')
        self.details_text.insert('1.0', summary)
        self.details_text.config(state='disabled')
    
    def clear_log(self):
        """ניקוי היומן"""
        # ניקוי הנתונים
        self.changes_log.clear_changes()
        
        # ניקוי הטבלה
        for item in self.changes_tree.get_children():
            self.changes_tree.delete(item)
        
        # איפוס הסיכום
        self.summary_label.config(text="0 קבצים עובדו")
        
        # ניקוי הפירוט
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', 'end')
        self.details_text.insert('1.0', "טרם בוצעו שינויים")
        self.details_text.config(state='disabled')
    
    def show_details(self, event):
        """הצגת תצוגה מקדימה של הקובץ המעובד"""
        item = self.changes_tree.identify_row(event.y)
        if not item:
            return
        
        values = self.changes_tree.item(item)['values']
        if not values or len(values) < 4:
            return
        
        # מציאת השינוי המתאים
        timestamp_str = values[0]
        order_number = values[1]
        input_name = values[2]
        
        # חיפוש בלוג
        for change in self.changes_log.get_changes():
            if (change['timestamp'].strftime("%H:%M:%S") == timestamp_str and 
                os.path.basename(change['input_file']) == input_name):
                
                output_file = change['output_file']
                if not output_file or not os.path.exists(output_file):
                    import tkinter.messagebox as mb
                    mb.showerror("שגיאה", "קובץ הפלט לא נמצא")
                    return
                
                # הצגת תצוגה מקדימה
                self.show_pdf_preview(output_file, change)
                break
    
    def show_pdf_preview(self, pdf_path, change_data):
        """הצגת חלון תצוגה מקדימה של הקובץ המעובד"""
        try:
            import fitz  # PyMuPDF
            from PIL import Image, ImageTk
            import io
            
            # פתיחת PDF
            doc = fitz.open(pdf_path)
            page = doc[0]
            
            # המרה לתמונה ברזולוציה נמוכה (150 DPI)
            zoom = 150 / 72  # 150 DPI
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # המרה ל-PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # יצירת חלון תצוגה
            preview_window = tk.Toplevel()
            preview_window.title(f"תצוגה מקדימה - {os.path.basename(pdf_path)}")
            preview_window.configure(bg=self.colors['dark_bg'])
            
            # כותרת עם פרטים
            header_frame = tk.Frame(preview_window, bg=self.colors['card_bg'], pady=10, padx=15)
            header_frame.pack(fill="x")
            
            tk.Label(
                header_frame,
                text=f"📄 {os.path.basename(pdf_path)}",
                font=("Arial", 12, "bold"),
                fg=self.colors['primary'],
                bg=self.colors['card_bg']
            ).pack()
            
            if change_data.get('order_number'):
                tk.Label(
                    header_frame,
                    text=f"מספר הזמנה: {change_data['order_number']}",
                    font=("Arial", 10),
                    fg=self.colors['dark_text'],
                    bg=self.colors['card_bg']
                ).pack()
            
            # פירוט שינויים
            if change_data.get('changes'):
                changes_text = ", ".join(change_data['changes'])
                tk.Label(
                    header_frame,
                    text=f"שינויים: {changes_text}",
                    font=("Arial", 9),
                    fg=self.colors['light_text'],
                    bg=self.colors['card_bg'],
                    wraplength=600
                ).pack(pady=(5, 0))
            
            # תמונה
            img_frame = tk.Frame(preview_window, bg=self.colors['dark_bg'])
            img_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # שמירת הרזולוציה המקורית אבל הגבלת גודל מקסימלי
            max_width = 800
            max_height = 600
            
            img_width, img_height = img.size
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width / img_width, max_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            
            label = tk.Label(img_frame, image=photo, bg=self.colors['dark_bg'])
            label.image = photo  # שמירת reference
            label.pack()
            
            # כפתור סגירה
            btn_frame = tk.Frame(preview_window, bg=self.colors['dark_bg'], pady=10)
            btn_frame.pack(fill="x")
            
            close_btn = tk.Button(
                btn_frame,
                text="✖ סגור",
                command=preview_window.destroy,
                bg=self.colors['danger'],
                fg="white",
                font=("Arial", 10, "bold"),
                padx=20,
                pady=5,
                relief="flat",
                cursor="hand2"
            )
            close_btn.pack()
            
            # מרכוז החלון
            preview_window.update_idletasks()
            window_width = preview_window.winfo_width()
            window_height = preview_window.winfo_height()
            screen_width = preview_window.winfo_screenwidth()
            screen_height = preview_window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            preview_window.geometry(f"+{x}+{y}")
            
            doc.close()
            
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("שגיאה", f"לא ניתן להציג תצוגה מקדימה:\n{str(e)}")
            print(f"[ERROR] Preview failed: {e}")
            import traceback
            traceback.print_exc()
