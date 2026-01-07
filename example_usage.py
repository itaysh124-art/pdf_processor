"""
דוגמאות שימוש בכלים המקצועיים לעיבוד PDF
מדגים את השימוש ב-PyMuPDF, PDFToolbox ו-Ghostscript
"""

from pdf_analysis import PDFAnalyzer, PDFValidator, PDFConverter
from pathlib import Path


def example_pymupdf():
    """דוגמאות שימוש ב-PyMuPDF לניתוח ומניפולציות בסיסיות"""
    print("\n=== דוגמאות PyMuPDF ===")
    
    pdf_path = "example.pdf"
    
    # 1. חילוץ מידע בסיסי
    print("\n1. מידע על PDF:")
    resolution, dpi, colormode, pixelated_status, vector_status = PDFAnalyzer.get_pdf_info(pdf_path)
    print(f"   רזולוציה: {resolution}")
    print(f"   DPI: {dpi}")
    print(f"   מצב צבעים: {colormode}")
    print(f"   סטטוס פיקסול: {pixelated_status}")
    print(f"   וקטורי: {vector_status}")
    
    # 2. חילוץ מטא-דאטה
    print("\n2. מטא-דאטה:")
    metadata = PDFAnalyzer.extract_metadata(pdf_path)
    for key, value in metadata.items():
        if value:
            print(f"   {key}: {value}")
    
    # 3. חילוץ טקסט
    print("\n3. חילוץ טקסט:")
    text = PDFAnalyzer.extract_text(pdf_path, page_num=0)
    print(f"   טקסט מעמוד ראשון: {text[:200]}...")
    
    # 4. חילוץ תמונות
    print("\n4. חילוץ תמונות:")
    images = PDFAnalyzer.extract_images(pdf_path, output_folder="extracted_images")
    print(f"   חולצו {len(images)} תמונות")
    
    # 5. פיצול PDF
    print("\n5. פיצול PDF:")
    split_files = PDFAnalyzer.split_pdf(pdf_path, output_folder="split_pdfs", pages_per_file=1)
    print(f"   נוצרו {len(split_files)} קבצים")
    
    # 6. סיבוב עמודים
    print("\n6. סיבוב עמודים:")
    success = PDFAnalyzer.rotate_pages(pdf_path, output_path="rotated.pdf", rotation=90)
    print(f"   סיבוב {'הצליח' if success else 'נכשל'}")
    
    # 7. מיזוג PDFs
    print("\n7. מיזוג PDFs:")
    pdfs_to_merge = ["file1.pdf", "file2.pdf", "file3.pdf"]
    success = PDFAnalyzer.merge_pdfs(pdfs_to_merge, "merged.pdf")
    print(f"   מיזוג {'הצליח' if success else 'נכשל'}")
    
    # 8. זיהוי שכבות Spot
    print("\n8. זיהוי שכבות:")
    cutcontour = PDFAnalyzer.detect_spot_layer(pdf_path, "CutContour")
    crease = PDFAnalyzer.detect_spot_layer(pdf_path, "Crease")
    print(f"   CutContour: {cutcontour}")
    print(f"   Crease: {crease}")


def example_pdftoolbox():
    """דוגמאות שימוש ב-PDFToolbox לvalidation ותיקון"""
    print("\n\n=== דוגמאות PDFToolbox ===")
    
    validator = PDFValidator()
    pdf_path = "example.pdf"
    
    # 1. בדיקת PDF
    print("\n1. Preflight Validation:")
    result = validator.validate_pdf(pdf_path, profile='PDF/X-4')
    print(f"   תוצאה: {'עבר' if result['success'] else 'נכשל'}")
    if result.get('errors'):
        print(f"   שגיאות: {result['errors']}")
    if result.get('warnings'):
        print(f"   אזהרות: {result['warnings']}")
    
    # 2. תיקון PDF פגום
    print("\n2. תיקון PDF פגום:")
    success = validator.fix_corrupted_pdf("corrupted.pdf", "fixed.pdf")
    print(f"   תיקון {'הצליח' if success else 'נכשל'}")
    
    # 3. המרה ל-PDF/A
    print("\n3. המרה ל-PDF/A:")
    success = validator.convert_to_pdfa(pdf_path, "output_pdfa.pdf", standard='PDF/A-2b')
    print(f"   המרה {'הצלחה' if success else 'נכשלה'}")
    
    # 4. המרה ל-PDF/X
    print("\n4. המרה ל-PDF/X:")
    success = validator.convert_to_pdfx(pdf_path, "output_pdfx.pdf", standard='PDF/X-4')
    print(f"   המרה {'הצלחה' if success else 'נכשלה'}")
    
    # 5. בדיקת עמידה בתקן
    print("\n5. בדיקת Compliance:")
    compliance = validator.check_compliance(pdf_path, standard='PDF/X-4')
    print(f"   עומד בתקן: {'כן' if compliance['compliant'] else 'לא'}")
    if compliance.get('issues'):
        print(f"   בעיות: {compliance['issues']}")


def example_ghostscript():
    """דוגמאות שימוש ב-Ghostscript להמרות ואופטימיזציה"""
    print("\n\n=== דוגמאות Ghostscript ===")
    
    converter = PDFConverter()
    pdf_path = "example.pdf"
    
    # בדיקה אם Ghostscript זמין
    if not converter.gs_path:
        print("   Ghostscript לא נמצא במערכת!")
        print("   הורד מ: https://www.ghostscript.com/download/gsdnld.html")
        return
    
    print(f"   Ghostscript נמצא: {converter.gs_path}")
    
    # 1. אופטימיזציה ודחיסה
    print("\n1. אופטימיזציה (רמות איכות שונות):")
    
    # איכות מסך - קובץ קטן
    success = converter.optimize_pdf(pdf_path, "optimized_screen.pdf", quality='screen')
    print(f"   Screen (72 DPI): {'הצליח' if success else 'נכשל'}")
    
    # איכות ספר אלקטרוני
    success = converter.optimize_pdf(pdf_path, "optimized_ebook.pdf", quality='ebook')
    print(f"   eBook (150 DPI): {'הצליח' if success else 'נכשל'}")
    
    # איכות הדפסה (מומלץ)
    success = converter.optimize_pdf(pdf_path, "optimized_printer.pdf", quality='printer')
    print(f"   Printer (300 DPI): {'הצליח' if success else 'נכשל'}")
    
    # איכות דפוס
    success = converter.optimize_pdf(pdf_path, "optimized_prepress.pdf", quality='prepress')
    print(f"   Prepress (300 DPI + colors): {'הצליח' if success else 'נכשל'}")
    
    # 2. המרה לתמונות
    print("\n2. המרה לתמונות:")
    
    # PNG ברזולוציה גבוהה
    images = converter.convert_to_images(pdf_path, "output_images", dpi=300, format='png')
    print(f"   נוצרו {len(images)} תמונות PNG ב-300 DPI")
    
    # JPEG לדוגמה
    images = converter.convert_to_images(pdf_path, "output_images", dpi=150, format='jpg')
    print(f"   נוצרו {len(images)} תמונות JPEG ב-150 DPI")
    
    # 3. המרה ל-PDF/A
    print("\n3. המרה ל-PDF/A:")
    success = converter.convert_to_pdfa_gs(pdf_path, "output_pdfa_gs.pdf", pdfa_version='2')
    print(f"   PDF/A-2: {'הצליח' if success else 'נכשל'}")
    
    # 4. מיזוג PDFs
    print("\n4. מיזוג PDFs:")
    pdfs = ["file1.pdf", "file2.pdf", "file3.pdf"]
    success = converter.merge_pdfs(pdfs, "merged_gs.pdf")
    print(f"   מיזוג: {'הצליח' if success else 'נכשל'}")


def example_combined_workflow():
    """דוגמה לתהליך עבודה משולב עם כל הכלים"""
    print("\n\n=== תהליך עבודה משולב ===")
    
    pdf_path = "input.pdf"
    
    # שלב 1: ניתוח ראשוני עם PyMuPDF
    print("\nשלב 1: ניתוח PDF")
    resolution, dpi, colormode, _, _ = PDFAnalyzer.get_pdf_info(pdf_path)
    metadata = PDFAnalyzer.extract_metadata(pdf_path)
    
    print(f"   קובץ: {metadata.get('title', 'ללא שם')}")
    print(f"   עמודים: {metadata.get('page_count')}")
    print(f"   רזולוציה: {resolution}")
    print(f"   DPI: {dpi}")
    print(f"   צבעים: {colormode}")
    
    # שלב 2: Validation עם PDFToolbox
    print("\nשלב 2: בדיקת תקינות")
    validator = PDFValidator()
    validation = validator.validate_pdf(pdf_path, profile='PDF/X-4')
    
    if not validation['success']:
        print("   נמצאו בעיות - מנסה לתקן...")
        validator.fix_corrupted_pdf(pdf_path, "fixed.pdf")
        pdf_path = "fixed.pdf"
    else:
        print("   ✓ הקובץ תקין")
    
    # שלב 3: אופטימיזציה עם Ghostscript
    print("\nשלב 3: אופטימיזציה")
    converter = PDFConverter()
    
    if converter.gs_path:
        # אופטימיזציה לפי צורך
        if metadata.get('file_size', 0) > 10 * 1024 * 1024:  # מעל 10MB
            print("   קובץ גדול - מבצע דחיסה...")
            converter.optimize_pdf(pdf_path, "optimized.pdf", quality='printer')
            pdf_path = "optimized.pdf"
        else:
            print("   ✓ גודל הקובץ מתאים")
    
    # שלב 4: המרה לתקן מתאים
    print("\nשלב 4: המרה לתקן")
    
    if colormode == "CMYK":
        # קובץ CMYK מתאים ל-PDF/X
        validator.convert_to_pdfx(pdf_path, "final_pdfx.pdf", standard='PDF/X-4')
        print("   ✓ הומר ל-PDF/X-4 (דפוס)")
    else:
        # קובץ RGB מתאים ל-PDF/A
        validator.convert_to_pdfa(pdf_path, "final_pdfa.pdf", standard='PDF/A-2b')
        print("   ✓ הומר ל-PDF/A-2b (ארכיון)")
    
    # שלב 5: יצירת תמונות תצוגה
    print("\nשלב 5: יצירת תמונות Preview")
    if converter.gs_path:
        preview_images = converter.convert_to_images(
            pdf_path, 
            "previews", 
            dpi=150, 
            format='jpg'
        )
        print(f"   ✓ נוצרו {len(preview_images)} תמונות preview")
    
    print("\n✓ תהליך העבודה הושלם בהצלחה!")


def main():
    """הפעלת כל הדוגמאות"""
    print("=" * 70)
    print("דוגמאות שימוש בכלים המקצועיים לעיבוד PDF")
    print("=" * 70)
    
    try:
        # הדגמת PyMuPDF
        example_pymupdf()
    except Exception as e:
        print(f"\n   שגיאה ב-PyMuPDF: {e}")
    
    try:
        # הדגמת PDFToolbox
        example_pdftoolbox()
    except Exception as e:
        print(f"\n   שגיאה ב-PDFToolbox: {e}")
    
    try:
        # הדגמת Ghostscript
        example_ghostscript()
    except Exception as e:
        print(f"\n   שגיאה ב-Ghostscript: {e}")
    
    try:
        # תהליך עבודה משולב
        example_combined_workflow()
    except Exception as e:
        print(f"\n   שגיאה בתהליך המשולב: {e}")
    
    print("\n" + "=" * 70)
    print("הדוגמאות הסתיימו")
    print("=" * 70)


if __name__ == "__main__":
    main()
