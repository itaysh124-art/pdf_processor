"""
בדיקה מהירה של זמינות כלי PDF
בודק אילו כלים מותקנים ופועלים במערכת
"""

import sys
from pathlib import Path


def check_pymupdf():
    """בדיקת PyMuPDF"""
    print("\n1. בדיקת PyMuPDF (fitz)")
    print("   " + "=" * 50)
    try:
        import fitz
        print(f"   ✓ PyMuPDF מותקן")
        print(f"   גרסה: {fitz.VersionBind}")
        print(f"   תיאור: חילוץ טקסט, ניתוח ומניפולציות בסיסיות")
        return True
    except ImportError:
        print(f"   ✗ PyMuPDF לא מותקן")
        print(f"   התקנה: pip install PyMuPDF")
        return False


def check_ghostscript():
    """בדיקת Ghostscript"""
    print("\n2. בדיקת Ghostscript")
    print("   " + "=" * 50)
    
    try:
        from .pdf_analysis import PDFConverter
        
        converter = PDFConverter()
        
        if converter.gs_path:
            print(f"   ✓ Ghostscript נמצא")
            print(f"   נתיב: {converter.gs_path}")
            print(f"   תיאור: המרות מורכבות, דחיסה ו-rendering")
            
            # ניסיון לקבל גרסה
            try:
                import subprocess
                result = subprocess.run(
                    [converter.gs_path, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"   גרסה: {result.stdout.strip()}")
            except Exception:
                pass
            
            return True
        else:
            print(f"   ✗ Ghostscript לא נמצא")
            print(f"   הורדה: https://www.ghostscript.com/download/gsdnld.html")
            print(f"   אחרי התקנה, הוסף לנתיב המערכת (PATH)")
            return False
            
    except Exception as e:
        print(f"   ✗ שגיאה בבדיקת Ghostscript: {e}")
        return False


def check_pdftoolbox():
    """בדיקת PDFToolbox"""
    print("\n3. בדיקת PDFToolbox")
    print("   " + "=" * 50)
    
    try:
        from .pdf_analysis import PDFValidator
        
        validator = PDFValidator()
        
        if validator.pdftoolbox_path:
            print(f"   ✓ PDFToolbox נמצא")
            print(f"   נתיב: {validator.pdftoolbox_path}")
            print(f"   תיאור: validations, preflight ותיקון PDFs")
            return True
        else:
            print(f"   ✗ PDFToolbox לא נמצא (אופציונלי)")
            print(f"   הערה: PDFToolbox הוא כלי מסחרי ואינו נדרש")
            print(f"   מידע: https://www.callassoftware.com/")
            return False
            
    except Exception as e:
        print(f"   ✗ שגיאה בבדיקת PDFToolbox: {e}")
        return False


def check_config():
    """בדיקת קובץ הגדרות"""
    print("\n4. בדיקת קובץ הגדרות")
    print("   " + "=" * 50)
    
    try:
        from .config import (
            PDF_TOOLS_CONFIG,
            OPTIMIZATION_CONFIG,
            CONVERSION_CONFIG,
            VALIDATION_CONFIG
        )
        
        print(f"   ✓ קובץ config.py נטען בהצלחה")
        print(f"\n   הגדרות כלים:")
        
        for tool, settings in PDF_TOOLS_CONFIG.items():
            status = "✓" if settings.get('enabled', False) else "✗"
            print(f"     {status} {tool}: {settings.get('description', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ שגיאה בטעינת config.py: {e}")
        return False


def test_basic_functionality():
    """בדיקת פונקציונליות בסיסית"""
    print("\n5. בדיקת פונקציונליות בסיסית")
    print("   " + "=" * 50)
    
    try:
        from .pdf_analysis import PDFAnalyzer, PDFValidator, PDFConverter
        
        print(f"   ✓ PDFAnalyzer נטען")
        print(f"   ✓ PDFValidator נטען")
        print(f"   ✓ PDFConverter נטען")
        
        # בדיקה שהמתודות קיימות
        methods_to_check = [
            ('PDFAnalyzer', 'extract_text'),
            ('PDFAnalyzer', 'extract_metadata'),
            ('PDFAnalyzer', 'extract_images'),
            ('PDFAnalyzer', 'get_pdf_info'),
            ('PDFValidator', 'validate_pdf'),
            ('PDFValidator', 'fix_corrupted_pdf'),
            ('PDFConverter', 'optimize_pdf'),
            ('PDFConverter', 'convert_to_images'),
        ]
        
        print(f"\n   מתודות זמינות:")
        for class_name, method_name in methods_to_check:
            cls = PDFAnalyzer if class_name == 'PDFAnalyzer' else (
                  PDFValidator if class_name == 'PDFValidator' else PDFConverter)
            
            if hasattr(cls, method_name):
                print(f"     ✓ {class_name}.{method_name}")
            else:
                print(f"     ✗ {class_name}.{method_name} - לא נמצא!")
        
        return True
        
    except Exception as e:
        print(f"   ✗ שגיאה: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """הדפסת סיכום"""
    print("\n" + "=" * 70)
    print("סיכום בדיקת המערכת")
    print("=" * 70)
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\nתוצאות: {passed}/{total} בדיקות עברו בהצלחה")
    
    print("\nפירוט:")
    for check, passed in results.items():
        status = "✓" if passed else "✗"
        print(f"  {status} {check}")
    
    if results['PyMuPDF']:
        print("\n✓ מוכן לעבודה בסיסית (PyMuPDF)")
    
    if results['PyMuPDF'] and results['Ghostscript']:
        print("✓ מוכן לעבודה מלאה (PyMuPDF + Ghostscript)")
    
    if all(results.values()):
        print("✓✓✓ כל הכלים זמינים - מוכן לעבודה מקצועית!")
    
    print("\nהמלצות:")
    if not results['PyMuPDF']:
        print("  • התקן PyMuPDF: pip install PyMuPDF (חובה)")
    
    if not results['Ghostscript']:
        print("  • התקן Ghostscript להמרות ואופטימיזציה (מומלץ מאוד)")
        print("    הורדה: https://www.ghostscript.com/download/gsdnld.html")
    
    if not results['PDFToolbox']:
        print("  • PDFToolbox אופציונלי - נדרש רק לתכונות validation מתקדמות")
    
    print("\n" + "=" * 70)


def main():
    """הפעלת כל הבדיקות"""
    print("=" * 70)
    print("בדיקת זמינות כלי PDF - PDF Processor Pro")
    print("=" * 70)
    
    results = {}
    
    # ביצוע כל הבדיקות
    results['PyMuPDF'] = check_pymupdf()
    results['Ghostscript'] = check_ghostscript()
    results['PDFToolbox'] = check_pdftoolbox()
    results['Config'] = check_config()
    results['Functionality'] = test_basic_functionality()
    
    # הדפסת סיכום
    print_summary(results)
    
    return 0 if results['PyMuPDF'] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
