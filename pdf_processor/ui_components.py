"""
UI Components for PDF Processor
מכיל רכיבי ממשק מותאמים אישית
"""
import tkinter as tk

class ToggleSwitch(tk.Canvas):
    """כפתור Toggle מודרני בסגנון טלפונים חכמים"""
    def __init__(self, parent, variable, on_color='#4CAF50', off_color='#4A4A4A', bg='#353535', **kwargs):
        # גודל הכפתור (קטן יותר ומעוגל)
        self.width = 40
        self.height = 20
        
        super().__init__(parent, width=self.width, height=self.height, 
                        bg=bg, highlightthickness=0, **kwargs)
        
        self.variable = variable
        self.on_color = on_color
        self.off_color = off_color
        self.bg_color = bg
        
        # יצירת האליפסה והכפתור (עיגול מלא יותר)
        self.oval = self.create_oval(1, 1, self.width-1, self.height-1, 
                                     fill=off_color, outline=off_color, width=1)
        self.circle = self.create_oval(3, 3, self.height-3, self.height-3, 
                                       fill='white', outline='')
        
        # קישור לאירועים
        self.bind('<Button-1>', self.toggle)
        
        # עדכון מצב התחלתי
        self.update_display()
        
        # מעקב אחרי שינויים במשתנה
        self.variable.trace_add('write', lambda *args: self.update_display())
    
    def toggle(self, event=None):
        """החלפת מצב הכפתור"""
        self.variable.set(not self.variable.get())
    
    def update_display(self):
        """עדכון התצוגה לפי המצב"""
        is_on = self.variable.get()
        
        if is_on:
            # מצב ON - ירוק, כפתור בצד ימין
            self.itemconfig(self.oval, fill=self.on_color, outline=self.on_color)
            self.coords(self.circle, self.width-self.height+3, 3, 
                       self.width-3, self.height-3)
        else:
            # מצב OFF - אפור, כפתור בצד שמאל
            self.itemconfig(self.oval, fill=self.off_color, outline=self.off_color)
            self.coords(self.circle, 3, 3, self.height-3, self.height-3)
            self.coords(self.circle, 4, 4, self.height-4, self.height-4)
