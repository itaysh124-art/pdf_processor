"""
PDF Analysis Module
מכיל פונקציות לניתוח PDF - מידות, DPI, צבעים, איכות תמונות
"""
import fitz  # PyMuPDF
import re


class PDFAnalyzer:
    """מחלקה לניתוח מסמכי PDF"""
    
    @staticmethod
    def get_pdf_info(pdf_path):
        """מחזיר מידע על PDF: רזולוציה, DPI, מצב צבעים ומצב פיקסול"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            
            # ניסיון למצוא את גבולות ה-CutContour
            cutcontour_rect = PDFAnalyzer.find_cutcontour_bounds(page)
            
            if cutcontour_rect:
                # אם נמצא CutContour, השתמש במידות שלו
                width_pt = cutcontour_rect[2] - cutcontour_rect[0]
                height_pt = cutcontour_rect[3] - cutcontour_rect[1]
            else:
                # אם לא נמצא CutContour, השתמש ב-MediaBox
                rect = page.rect
                width_pt = rect.width
                height_pt = rect.height
            
            # המרה למ"מ
            width_mm = width_pt / 72 * 25.4
            height_mm = height_pt / 72 * 25.4
            
            resolution = f"{int(width_mm)}x{int(height_mm)}"
            
            # חישוב DPI אמיתי של תמונות בעמוד
            actual_dpi = PDFAnalyzer.get_actual_dpi_fitz(page)
            
            # תמיד נציג ערך DPI - אם לא מצאנו תמונות, נציג 300 (וקטורי)
            if actual_dpi and actual_dpi > 0:
                dpi = f"{int(actual_dpi)}"
            else:
                dpi = "300"  # ברירת מחדל לגרפיקה וקטורית
            
            # זיהוי מצב צבעים
            colormode = PDFAnalyzer.detect_color_mode(page)
            
            # בדיקת תמונות בעמוד
            pixelated_status = PDFAnalyzer.check_images_quality(page, width_mm, height_mm)
            
            # בדיקה אם הקובץ הוא ווקטורי
            is_vector = PDFAnalyzer.is_vector(page)
            vector_status = "✓" if is_vector else ""
            
            print(f"[PDF_INFO] is_vector={is_vector}, vector_status='{vector_status}'")
            
            doc.close()
            
            return resolution, dpi, colormode, pixelated_status, vector_status
            
        except Exception as e:
            return "שגיאה", "N/A", "N/A", "שגיאה", "N/A"
    
    @staticmethod
    def find_cutcontour_bounds(page):
        """מחפש את הגבולות של CutContour layer ומחזיר את ה-bounding box"""
        try:
            # קבלת content stream של העמוד
            xref_list = page.get_contents()
            if not xref_list:
                return None
            
            if not isinstance(xref_list, list):
                xref_list = [xref_list]
            
            # משתנים לאחסון נקודות המלבן
            cutcontour_found = False
            min_x = float('inf')
            min_y = float('inf')
            max_x = float('-inf')
            max_y = float('-inf')
            
            for xref in xref_list:
                try:
                    stream = page.parent.xref_stream(xref)
                    if not stream:
                        continue
                    
                    content_str = stream.decode('latin-1', errors='ignore')
                    
                    # חיפוש פקודת CutContour ופקודות ציור מלבן
                    lines = content_str.split('\n')
                    in_cutcontour = False
                    
                    for i, line in enumerate(lines):
                        # בדיקה אם נכנסנו למצב CutContour
                        if re.search(r'/CutContour\s+(cs|CS)', line, re.IGNORECASE):
                            in_cutcontour = True
                            cutcontour_found = True
                            continue
                        
                        # אם אנחנו במצב CutContour, חפש פקודת re (rectangle)
                        if in_cutcontour:
                            # פורמט: x y width height re
                            match = re.search(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+re', line)
                            if match:
                                x = float(match.group(1))
                                y = float(match.group(2))
                                width = float(match.group(3))
                                height = float(match.group(4))
                                
                                # עדכון גבולות
                                min_x = min(min_x, x)
                                min_y = min(min_y, y)
                                max_x = max(max_x, x + width)
                                max_y = max(max_y, y + height)
                                
                                # יצאנו ממצב CutContour אחרי שמצאנו מלבן
                                in_cutcontour = False
                            
                            # אם נתקלנו בשינוי צבע אחר, יצאנו ממצב CutContour
                            if re.search(r'/\w+\s+(cs|CS)', line) and 'CutContour' not in line:
                                in_cutcontour = False
                
                except Exception as e:
                    print(f"[CUTCONTOUR] Error reading stream: {e}")
                    continue
            
            if cutcontour_found and min_x != float('inf'):
                return (min_x, min_y, max_x, max_y)
            
            return None
            
        except Exception as e:
            print(f"[CUTCONTOUR] Error finding bounds: {e}")
            return None
    
    @staticmethod
    def get_actual_dpi_fitz(page):
        """מחזיר את ה-DPI האמיתי הנמוך ביותר מבין כל התמונות בעמוד - גרסת PyMuPDF"""
        try:
            # קבלת מידות העמוד
            rect = page.rect
            page_width_pt = rect.width
            page_height_pt = rect.height
            
            # קבלת רשימת תמונות בעמוד
            image_list = page.get_images(full=True)
            
            if not image_list:
                print("[DPI] No images found - might be vector-only PDF")
                return 300  # ערך ברירת מחדל טוב עבור PDF וקטורי
            
            all_dpis = []
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                # קבלת מידות התמונה
                pix = fitz.Pixmap(page.parent, xref)
                width_px = pix.width
                height_px = pix.height
                pix = None  # שחרור זיכרון
                
                print(f"[DPI] Found image xref={xref}: {width_px}x{height_px} px")
                
                if width_px and height_px:
                    # חישוב DPI מקורב על בסיס גודל העמוד
                    dpi_x = (width_px / page_width_pt) * 72
                    dpi_y = (height_px / page_height_pt) * 72
                    actual_dpi = min(dpi_x, dpi_y)
                    
                    print(f"[DPI]   Calculated DPI for xref={xref}: {actual_dpi}")
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
    
    @staticmethod
    def detect_color_mode(page):
        """מזהה אם ה-PDF במצב CMYK או RGB - גרסת PyMuPDF משופרת"""
        try:
            has_cmyk = False
            has_rgb = False
            
            # 1. בדיקת תמונות בעמוד
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                try:
                    pix = fitz.Pixmap(page.parent, xref)
                    colorspace = pix.colorspace
                    
                    if colorspace:
                        cs_name = colorspace.name if hasattr(colorspace, 'name') else str(colorspace)
                        print(f"[COLOR] Image xref={xref}: ColorSpace = {cs_name}, n={pix.n}")
                        
                        if 'CMYK' in cs_name.upper() or pix.n == 4:
                            has_cmyk = True
                        elif 'RGB' in cs_name.upper() or pix.n == 3:
                            has_rgb = True
                    
                    pix = None
                except Exception as e:
                    print(f"[COLOR] Error checking image xref={xref}: {e}")
            
            # 2. בדיקת content stream לפקודות צבע
            try:
                xref_list = page.get_contents()
                if xref_list:
                    if not isinstance(xref_list, list):
                        xref_list = [xref_list]
                    
                    for xref in xref_list:
                        try:
                            stream = page.parent.xref_stream(xref)
                            if stream:
                                content_str = stream.decode('latin-1', errors='ignore')
                                
                                # חיפוש פקודות CMYK: k, K (setcmykcolor)
                                # חיפוש פקודות RGB: rg, RG (setrgbcolor)
                                if re.search(r'(\s+k\s+|\s+K\s+|/DeviceCMYK)', content_str):
                                    has_cmyk = True
                                    print(f"[COLOR] Found CMYK operators in content stream")
                                
                                if re.search(r'(\s+rg\s+|\s+RG\s+|/DeviceRGB)', content_str):
                                    has_rgb = True
                                    print(f"[COLOR] Found RGB operators in content stream")
                        except Exception as e:
                            print(f"[COLOR] Stream read error: {e}")
            except Exception as e:
                print(f"[COLOR] Content stream error: {e}")
            
            # החזרת התוצאה
            result = "N/A"
            if has_cmyk and has_rgb:
                result = "CMYK + RGB"
            elif has_cmyk:
                result = "CMYK"
            elif has_rgb:
                result = "RGB"

            print(f"[COLOR] Final result: {result}")
            return result

        except Exception as e:
            print(f"[COLOR] שגיאה בזיהוי מצב צבעים: {e}")
            import traceback
            traceback.print_exc()
            return "N/A"
    
    @staticmethod
    def is_vector(page):
        """בודק האם ה-PDF הוא ווקטורי (ללא תמונות raster)"""
        try:
            image_list = page.get_images(full=True)
            is_vector_result = len(image_list) == 0
            print(f"[VECTOR] Number of images found: {len(image_list)}, is_vector: {is_vector_result}")
            return is_vector_result
        except Exception as e:
            print(f"[VECTOR] Error checking vector status: {e}")
            return False
    
    @staticmethod
    def check_images_quality(page, page_width_mm, page_height_mm):
        """בודק את ה-DPI האמיתי של תמונות בעמוד - גרסת PyMuPDF"""
        try:
            # קבלת רשימת תמונות בעמוד
            image_list = page.get_images(full=True)
            
            if not image_list:
                return "✓ ללא תמונות"
            
            images_info = []
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                # קבלת מידות התמונה
                try:
                    pix = fitz.Pixmap(page.parent, xref)
                    width_px = pix.width
                    height_px = pix.height
                    pix = None  # שחרור זיכרון
                    
                    if width_px and height_px:
                        # חישוב DPI מקורב על בסיס גודל העמוד
                        page_width_inches = page_width_mm / 25.4
                        page_height_inches = page_height_mm / 25.4
                        
                        dpi_x = width_px / page_width_inches
                        dpi_y = height_px / page_height_inches
                        actual_dpi = min(dpi_x, dpi_y)
                        
                        images_info.append(actual_dpi)
                except Exception as e:
                    print(f"Error processing image xref={xref}: {e}")
            
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
    
    @staticmethod
    def detect_spot_layer(pdf_path, spot_name):
        """זיהוי שכבת Spot Color ב-PDF - מחזיר טקסט עם סוג השכבה"""
        try:
            doc = fitz.open(pdf_path)
            page = doc[0]
            found_layers = []
            
            print(f"[LAYER] Checking for '{spot_name}' in {pdf_path}")
            
            # בדיקת OCG (Optional Content Groups) - שכבות
            try:
                oc_count = doc.layer_ui_configs()
                if oc_count:
                    for config in oc_count:
                        config_name = config.get('text', '')
                        if spot_name.lower() in config_name.lower():
                            found_layers.append(f"{config_name} (L)")
                            print(f"[LAYER]   Found OCG: {config_name}")
            except Exception as e:
                print(f"[LAYER]   OCG check error: {e}")
            
            # בדיקת ColorSpace בתוך stream של העמוד
            try:
                xref_list = page.get_contents()
                if xref_list:
                    if not isinstance(xref_list, list):
                        xref_list = [xref_list]
                    
                    for xref in xref_list:
                        try:
                            stream = doc.xref_stream(xref)
                            if stream:
                                content_str = stream.decode('latin-1', errors='ignore')
                                # חיפוש Spot Colors
                                pattern = rf'/{spot_name}\s*(cs|CS|scn|SCN)'
                                if re.search(pattern, content_str, re.IGNORECASE):
                                    if not any(spot_name.lower() in layer.lower() for layer in found_layers):
                                        found_layers.append(f'{spot_name} (S)')
                                        print(f"[LAYER]   Found Spot Color: {spot_name}")
                        except Exception as e:
                            print(f"[LAYER]   Stream read error: {e}")
            except Exception as e:
                print(f"[LAYER]   Content stream error: {e}")
            
            doc.close()
            
            # החזרת התוצאה
            result = ', '.join(found_layers) if found_layers else '-'
            print(f"[LAYER]   Result: {result}")
            return result
        except Exception as e:
            print(f"[LAYER] Error: {e}")
            return '-'
