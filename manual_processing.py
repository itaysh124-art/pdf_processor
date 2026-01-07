"""
מודול עיבוד ידני - ממשק וניהול עיבוד מקרים בודדים
"""

import tkinter as tk
from tkinter import ttk
from config import COLORS, FONTS


def create_manual_tab_ui(parent, app):
    """יצירת ממשק לעיבוד ידני"""
    # יצירת Frame עם Canvas ו-Scrollbar לטאב הידני
    container_frame = tk.Frame(parent, bg=COLORS['light_bg'])
    container_frame.pack(fill="both", expand=True)
    
    # Canvas לגלילה
    canvas = tk.Canvas(container_frame, bg=COLORS['light_bg'], highlightthickness=0)
    scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=canvas.yview)
    
    # Main Container בתוך Canvas
    main_container = tk.Frame(canvas, bg=COLORS['light_bg'])
    
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
        canvas_width = canvas.winfo_width()
        canvas.itemconfig(canvas_frame, width=canvas_width)
    
    main_container.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_frame_configure)
    
    # גלילה עם גלגל העכבר
    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    return main_container


def create_file_selection_ui(parent, app):
    """יצירת ממשק בחירת קבצים"""
    file_frame = tk.LabelFrame(
        parent,
        text=" 📁 קבצי PDF לעיבוד ",
        font=FONTS['heading'],
        padx=15,
        pady=15,
        bg="white",
        fg=COLORS['dark_text'],
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
        command=app.browse_files,
        bg=COLORS['success'],
        fg="white",
        font=FONTS['label'] + ('bold',),
        padx=15,
        pady=8,
        relief="flat",
        cursor="hand2"
    )
    browse_files_btn.pack(side="left", padx=5)
    
    browse_folder_btn = tk.Button(
        buttons_frame,
        text="  📁 בחר תיקייה  ",
        command=app.browse_folder,
        bg=COLORS['primary'],
        fg="white",
        font=FONTS['label'] + ('bold',),
        padx=15,
        pady=8,
        relief="flat",
        cursor="hand2"
    )
    browse_folder_btn.pack(side="left", padx=5)
    
    clear_btn = tk.Button(
        buttons_frame,
        text="  🗑️ נקה  ",
        command=app.clear_files,
        bg=COLORS['danger'],
        fg="white",
        font=FONTS['label'] + ('bold',),
        padx=15,
        pady=8,
        relief="flat",
        cursor="hand2"
    )
    clear_btn.pack(side="left", padx=5)
    
    return file_frame


def create_treeview_ui(parent, app):
    """יצירת טבלת קבצים (Treeview)"""
    list_frame = tk.Frame(parent, bg="white")
    list_frame.pack(fill="both", expand=True, pady=(0, 10))
    
    # יצירת Treeview עם עמודות
    columns = ('selected', 'name', 'resolution', 'dpi', 'colormode', 'pixelated', 'cutcontour', 'crease', 'holes')
    app.files_tree = ttk.Treeview(
        list_frame,
        columns=columns,
        show='headings',
        height=12,
        selectmode='browse'
    )
    
    # הגדרת כותרות עם מסננים
    app.files_tree.heading('selected', text='☑', command=app.toggle_all_checkboxes)
    app.files_tree.heading('name', text='שם הקובץ ▼', command=lambda: app.show_column_filter('name'))
    app.files_tree.heading('resolution', text='מידה (מ"מ) ▼', command=lambda: app.show_column_filter('resolution'))
    app.files_tree.heading('dpi', text='DPI ▼', command=lambda: app.show_column_filter('dpi'))
    app.files_tree.heading('colormode', text='מצב צבעים ▼', command=lambda: app.show_column_filter('colormode'))
    app.files_tree.heading('pixelated', text='איכות ▼', command=lambda: app.show_column_filter('pixelated'))
    app.files_tree.heading('cutcontour', text='קו חיתוך ▼', command=lambda: app.show_column_filter('cutcontour'))
    app.files_tree.heading('crease', text='קו קיפול ▼', command=lambda: app.show_column_filter('crease'))
    app.files_tree.heading('holes', text='חורים ▼', command=lambda: app.show_column_filter('holes'))
    
    # הגדרת רוחב עמודות
    app.files_tree.column('selected', minwidth=30, width=30, anchor='center', stretch=False)
    app.files_tree.column('name', minwidth=100, width=100, anchor='w', stretch=True)
    app.files_tree.column('resolution', minwidth=70, width=70, anchor='center', stretch=True)
    app.files_tree.column('dpi', minwidth=50, width=50, anchor='center', stretch=True)
    app.files_tree.column('colormode', minwidth=70, width=70, anchor='center', stretch=True)
    app.files_tree.column('pixelated', minwidth=80, width=80, anchor='center', stretch=True)
    app.files_tree.column('cutcontour', minwidth=80, width=80, anchor='center', stretch=True)
    app.files_tree.column('crease', minwidth=80, width=80, anchor='center', stretch=True)
    app.files_tree.column('holes', minwidth=80, width=80, anchor='center', stretch=True)
    
    scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=app.files_tree.yview)
    app.files_tree.configure(yscrollcommand=scrollbar.set)
    app.files_tree.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    
    # קישור לחיצה לשינוי checkbox
    app.files_tree.bind('<Button-1>', app.on_tree_click)


def create_settings_ui(parent, app):
    """יצירת ממשק הגדרות עיבוד"""
    settings_container = tk.Frame(parent, bg=COLORS['light_bg'])
    settings_container.pack(fill="x", pady=(0, 10))
    
    # הגדרות חורים
    holes_frame = tk.LabelFrame(
        settings_container,
        text=" ⚙️ הגדרות חורים ",
        font=FONTS['heading'],
        padx=15,
        pady=15,
        bg="white",
        fg=COLORS['dark_text'],
        relief="solid",
        borderwidth=1
    )
    holes_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
    
    tk.Label(holes_frame, text="קוטר חור (מ\"מ):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    tk.Spinbox(
        holes_frame,
        from_=1.0,
        to=50.0,
        increment=0.5,
        textvariable=app.hole_diameter,
        width=10
    ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
    
    tk.Label(holes_frame, text="מרחק ממרכז החור (מ\"מ):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    tk.Spinbox(
        holes_frame,
        from_=5.0,
        to=100.0,
        increment=1.0,
        textvariable=app.hole_margin,
        width=10
    ).grid(row=1, column=1, sticky="w", padx=5, pady=5)
    
    # הגדרות נוספות
    settings_frame = tk.LabelFrame(
        settings_container,
        text=" 🔧 הגדרות נוספות ",
        font=FONTS['heading'],
        padx=15,
        pady=15,
        bg="white",
        fg=COLORS['dark_text'],
        relief="solid",
        borderwidth=1
    )
    settings_frame.pack(side="left", fill="both", expand=True, padx=(5, 0))
    
    # מרווח Artboard
    tk.Label(settings_frame, text="מרווח Artboard (מ\"מ):", bg="white", font=FONTS['label']).grid(
        row=0, column=0, sticky="e", padx=5, pady=5
    )
    tk.Spinbox(
        settings_frame,
        from_=0.0,
        to=20.0,
        increment=0.5,
        textvariable=app.artboard_margin,
        width=10,
        font=FONTS['label']
    ).grid(row=0, column=1, sticky="w", padx=5, pady=5)
    
    # עובי Stroke
    tk.Label(settings_frame, text="עובי Stroke (pt):", bg="white", font=FONTS['label']).grid(
        row=0, column=2, sticky="e", padx=5, pady=5
    )
    tk.Spinbox(
        settings_frame,
        from_=0.1,
        to=2.0,
        increment=0.05,
        textvariable=app.stroke_width,
        width=10,
        font=FONTS['label']
    ).grid(row=0, column=3, sticky="w", padx=5, pady=5)
    
    # שיפור איכות תמונות
    tk.Checkbutton(
        settings_frame,
        text="🎯 שפר תמונות ל-300 DPI + CMYK",
        variable=app.enhance_images,
        bg="white",
        font=FONTS['label'] + ('bold',),
        fg=COLORS['success']
    ).grid(row=1, column=0, columnspan=4, sticky="w", padx=5, pady=5)
    
    # המרה ל-CMYK
    tk.Checkbutton(
        settings_frame,
        text="🎨 המר RGB ל-CMYK (הדפסה)",
        variable=app.convert_to_cmyk,
        bg="white",
        font=FONTS['label'] + ('bold',),
        fg=COLORS['primary']
    ).grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=5)
