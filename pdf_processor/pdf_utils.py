"""
פונקציות עזר לעיבוד PDF
כולל: זיהוי שכבות, ניתוח איכות תמונה, שיפור תמונות
"""

import cv2
import numpy as np
from skimage import restoration, filters
from pypdf import PdfReader
import re

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


def detect_spot_layer(pdf_path, spot_name):
    """זיהוי שכבה ב-PDF לפי שם. מחזיר שם שכבה עם סוג (S=Spot/P=Process/L=Layer) או '-' אם לא נמצא."""
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


def analyze_image_quality(pil_image):
    """ניתוח איכות תמונה באמצעות AI: חדות, רעש, רזולוציה."""
    if not PIL_AVAILABLE:
        return {'sharpness': 0, 'noise': 0, 'dpi': 72}
    
    img = np.array(pil_image.convert('L'))
    
    # חדות: variance of Laplacian
    sharpness = cv2.Laplacian(img, cv2.CV_64F).var()
    
    # רעש: הערכה באמצעות wavelet
    noise = restoration.estimate_sigma(img, multichannel=False)
    
    # רזולוציה: pixels per inch
    dpi = pil_image.info.get('dpi', (72, 72))[0]
    
    return {
        'sharpness': sharpness,
        'noise': noise,
        'dpi': dpi
    }


def enhance_image_ai(pil_image):
    """שיפור תמונה באמצעות AI: הגדלה והסרת רעש."""
    if not PIL_AVAILABLE:
        return pil_image
    
    img = np.array(pil_image)
    
    # הסרת רעש
    img_denoised = restoration.denoise_wavelet(img, multichannel=True, convert2ycbcr=True, mode='soft')
    img_denoised = (img_denoised * 255).astype(np.uint8)
    pil_denoised = Image.fromarray(img_denoised)
    
    # הגדלה (אם RealESRGAN זמין)
    if REALESRGAN_AVAILABLE:
        try:
            model = RealESRGAN('cuda' if torch.cuda.is_available() else 'cpu', scale=2)
            model.load_weights('RealESRGAN_x2.pth', download=True)
            upscaled = model.predict(pil_denoised)
            return upscaled
        except Exception as e:
            print(f"[AI] RealESRGAN failed: {e}")
    
    # Fallback: שינוי גודל עם PIL
    upscaled = pil_denoised.resize(
        (pil_denoised.width * 2, pil_denoised.height * 2),
        Image.LANCZOS
    )
    return upscaled


def get_smart_recommendations(pdf_info):
    """החזרת המלצות אוטומטיות לאיכות קובץ ואופטימיזציה להדפסה."""
    recs = []
    dpi = pdf_info.get('dpi', None)
    colormode = pdf_info.get('colormode', None)
    pixelated = pdf_info.get('pixelated', '')
    
    # המלצת DPI
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
    
    # המלצת מצב צבעים
    if colormode == "RGB":
        recs.append("🟠 מומלץ להמיר ל-CMYK להדפסה")
    elif colormode == "CMYK":
        recs.append("🟢 מצב צבעים תקין להדפסה")
    elif colormode == "N/A":
        recs.append("⚠ לא זוהה מצב צבעים - בדוק את הקובץ")
    
    # פיקסול
    if "✗ מפוקסל" in pixelated:
        recs.append("🔴 יש תמונות מפוקסלות - מומלץ לשפר איכות")
    elif "⚠ בינוני" in pixelated:
        recs.append("🟠 איכות תמונה בינונית - אפשר לשפר")
    elif "✓ איכותי" in pixelated:
        recs.append("🟢 איכות תמונה טובה")
    
    return recs
