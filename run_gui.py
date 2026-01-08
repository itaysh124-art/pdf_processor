#!/usr/bin/env python3
"""
PDF Processor Pro - Entry point for GUI application
Wrapper script to run the main GUI from the root directory
"""

if __name__ == "__main__":
    from pdf_processor.pdf_processor_gui import PDFProcessorApp
    import tkinter as tk
    
    root = tk.Tk()
    app = PDFProcessorApp(root)
    root.mainloop()
