"""
Crop Marks Remover Module
==========================
מודול להסרת crop marks עם זיהוי חכם
"""

import fitz  # PyMuPDF
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class CropMarksInfo:
    """מידע מפורט על crop marks בקובץ"""
    has_crop_marks: bool
    total_marks: int
    marks_by_page: Dict[int, int]
    marks_by_type: Dict[str, int]
    trimbox_pages: List[int]


class CropMarksRemover:
    """
    הסרה חכמה של crop marks בשילוב 3 שיטות
    """
    
    def __init__(self, verbose=False):
        """
        Args:
            verbose: הצגת מידע מפורט
        """
        self.verbose = verbose
    
    def detect_crop_marks(self, pdf_path):
        """
        זיהוי והחזרת מידע על crop marks
        
        Returns:
            CropMarksInfo
        """
        try:
            doc = fitz.open(pdf_path)
            
            trimbox_pages = []
            marks_by_page = {}
            marks_by_type = {'trimbox': 0, 'pattern': 0}
            
            for page_num, page in enumerate(doc, 1):
                page_marks = 0
                
                # בדיקת TrimBox
                if self._has_trimbox(page):
                    trimbox_pages.append(page_num)
                    marks_by_type['trimbox'] += 1
                    page_marks += 1
                    if self.verbose:
                        print(f"[CROP] עמוד {page_num}: נמצא TrimBox")
                
                if page_marks > 0:
                    marks_by_page[page_num] = page_marks
            
            doc.close()
            
            total_marks = sum(marks_by_type.values())
            
            return CropMarksInfo(
                has_crop_marks=total_marks > 0,
                total_marks=total_marks,
                marks_by_page=marks_by_page,
                marks_by_type=marks_by_type,
                trimbox_pages=trimbox_pages
            )
            
        except Exception as e:
            if self.verbose:
                print(f"[CROP ERROR] {e}")
            return CropMarksInfo(
                has_crop_marks=False,
                total_marks=0,
                marks_by_page={},
                marks_by_type={},
                trimbox_pages=[]
            )
    
    def remove_crop_marks(self, pdf_path, output_path, method='auto'):
        """
        הסרת crop marks מקובץ PDF
        
        Args:
            pdf_path: נתיב קובץ קלט
            output_path: נתיב קובץ פלט
            method: 'auto', 'position', 'spot_color', 'pattern'
        """
        doc = fitz.open(pdf_path)
        
        for page in doc:
            if method == 'auto':
                # ניסיון 1: לפי TrimBox
                if self._has_trimbox(page):
                    self._crop_to_trimbox(page)
                
                # ניסיון 2: לפי Spot Color
                elif self._has_registration_color(page):
                    self._remove_by_spot_color(page)
                
                # ניסיון 3: לפי זיהוי קווים
                else:
                    self._remove_by_pattern(page)
            
            elif method == 'position':
                self._crop_to_trimbox(page)
            
            elif method == 'spot_color':
                self._remove_by_spot_color(page)
            
            elif method == 'pattern':
                self._remove_by_pattern(page)
        
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()
        
        if self.verbose:
            print(f"[CROP] קובץ נשמר ב: {output_path}")
    
    # ========== שיטות פרטיות ==========
    
    def _has_trimbox(self, page):
        """בדיקה אם יש TrimBox מוגדר"""
        try:
            mediabox = page.mediabox
            trimbox = page.trimbox if hasattr(page, 'trimbox') and page.trimbox else None
            return trimbox is not None and tuple(trimbox) != tuple(mediabox)
        except:
            return False
    
    def _has_registration_color(self, page):
        """בדיקה אם יש Spot Color של Registration"""
        # TODO: לממש בדיקה של ColorSpace
        return False
    
    def _crop_to_trimbox(self, page):
        """חיתוך העמוד ל-TrimBox"""
        try:
            if not self._has_trimbox(page):
                return
            
            trimbox = page.trimbox
            mediabox = page.mediabox
            
            # ולידציה
            trim_rect = fitz.Rect(trimbox)
            media_rect = fitz.Rect(mediabox)
            
            if (trim_rect.x0 >= media_rect.x0 and 
                trim_rect.y0 >= media_rect.y0 and
                trim_rect.x1 <= media_rect.x1 and 
                trim_rect.y1 <= media_rect.y1 and
                trim_rect.width > 0 and 
                trim_rect.height > 0):
                
                # הסרה בפועל - חיתוך לפי TrimBox
                page.set_mediabox(trim_rect)
                page.set_cropbox(trim_rect)
                
                if self.verbose:
                    print(f"[CROP] חותך לפי TrimBox")
        except Exception as e:
            if self.verbose:
                print(f"[CROP ERROR] {e}")
    
    def _remove_by_spot_color(self, page):
        """הסרת אובייקטים עם Spot Color Registration"""
        # TODO: לממש הסרה לפי Spot Color
        pass
    
    def _remove_by_pattern(self, page):
        """זיהוי והסרה לפי דפוסים גרפיים"""
        # TODO: לממש הסרה לפי דפוסים
        pass
