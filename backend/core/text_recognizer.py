"""
文字识别引擎
使用Tesseract OCR识别图像中的文字,并解析结构化字段
"""
import pytesseract
import cv2
import numpy as np
import re
from typing import List, Dict, Any, Optional
from loguru import logger
import time


class TextRecognizer:
    """文字识别引擎"""
    
    def __init__(
        self, 
        tesseract_cmd: Optional[str] = None,
        lang: str = "eng+chi_sim",
        psm_modes: List[int] = None
    ):
        """
        初始化文字识别器
        
        Args:
            tesseract_cmd: Tesseract可执行文件路径,None表示使用系统PATH
            lang: 识别语言
            psm_modes: Page Segmentation Mode列表
        """
        self.tesseract_available = False
        
        try:
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            
            # 测试Tesseract是否可用
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
            
            self.lang = lang
            # 扩展PSM模式列表,覆盖更多场景
            self.psm_modes = psm_modes or [3, 4, 6, 11, 12, 13]  # 多种PSM模式
            
            logger.info(f"TextRecognizer initialized with lang={lang}, psm_modes={self.psm_modes}")
        except Exception as e:
            logger.warning(f"Tesseract OCR not available: {e}. OCR functionality will be disabled.")
            self.lang = lang
            self.psm_modes = psm_modes or [3, 4, 6, 11, 12, 13]
    
    def recognize_text(
        self, 
        image: np.ndarray, 
        psm: int = 6
    ) -> str:
        """
        识别图像中的文字
        
        Args:
            image: 输入图像
            psm: Page Segmentation Mode
            
        Returns:
            识别的文字
        """
        if not self.tesseract_available:
            logger.debug("Tesseract not available, skipping OCR")
            return ""
        
        try:
            # 添加tesseract配置选项,提高识别准确度
            config = f'--oem 3 --psm {psm} -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-/:,().'
            text = pytesseract.image_to_string(image, lang=self.lang, config=config)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR error with psm={psm}: {e}")
            return ""
    
    def recognize_with_data(
        self, 
        image: np.ndarray, 
        psm: int = 6
    ) -> Dict[str, Any]:
        """
        识别文字并返回详细数据(包括位置信息)
        
        Args:
            image: 输入图像
            psm: Page Segmentation Mode
            
        Returns:
            OCR数据字典
        """
        if not self.tesseract_available:
            logger.debug("Tesseract not available, skipping OCR")
            return {}
        
        try:
            config = f'--oem 3 --psm {psm}'
            data = pytesseract.image_to_data(
                image, 
                lang=self.lang, 
                config=config, 
                output_type=pytesseract.Output.DICT
            )
            return data
        except Exception as e:
            logger.error(f"OCR data extraction error with psm={psm}: {e}")
            return {}
    
    def preprocess_for_ocr(self, image: np.ndarray) -> List[np.ndarray]:
        """
        对图像进行预处理,生成候选图像(快速版)
        
        Args:
            image: 输入图像
            
        Returns:
            预处理后的图像列表
        """
        processed_images = []
        
        # 转为灰度图
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # 1. 放大2.5倍 + CLAHE增强(平衡速度和效果)
        scaled = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced_scaled = clahe.apply(scaled)
        processed_images.append(enhanced_scaled)
        
        # 2. 增强后Otsu二值化
        _, binary = cv2.threshold(enhanced_scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        processed_images.append(binary)
        
        return processed_images
    
    def recognize_multimode(self, image: np.ndarray) -> str:
        """
        使用多种预处理方法和PSM模式组合识别(快速版)
        
        Args:
            image: 输入图像
            
        Returns:
            识别的文字
        """
        # 生成2种预处理图像
        processed_images = self.preprocess_for_ocr(image)
        
        all_results = []
        
        # 只使用2个最有效的PSM模式
        effective_psm = [3, 6]  # 全自动、单块
        
        # 对每种预处理图像尝试PSM模式(共4种组合)
        for idx, proc_img in enumerate(processed_images):
            for psm in effective_psm:
                text = self.recognize_text(proc_img, psm=psm)
                if text:
                    # 计算文字质量分数
                    score = len(text)
                    if 'ITEM' in text.upper() or 'LOT' in text.upper() or 'QTY' in text.upper():
                        score += 100
                    
                    all_results.append({
                        'text': text,
                        'score': score,
                        'preprocess': idx,
                        'psm': psm
                    })
        
        if not all_results:
            return ""
        
        # 选择得分最高的结果
        best = max(all_results, key=lambda x: x['score'])
        logger.debug(f"Best OCR: preprocess={best['preprocess']}, PSM={best['psm']}, score={best['score']}")
        
        return best['text']
    
    def extract_text_regions(
        self, 
        image: np.ndarray, 
        min_confidence: float = 40.0
    ) -> List[Dict[str, Any]]:
        """
        提取文字区域及其位置(快速版)
        
        Args:
            image: 输入图像
            min_confidence: 最小置信度阈值
            
        Returns:
            文字区域列表,每个包含text, position, confidence
        """
        start_time = time.time()
        
        # 使用最有效的预处理方法
        processed_images = self.preprocess_for_ocr(image)
        best_img = processed_images[0]  # 使用放大2.5倍+增强的图像
        
        all_regions = []
        seen_texts = set()  # 去重
        
        # 只使用PSM 3(全自动)
        data = self.recognize_with_data(best_img, psm=3)
        if data and 'text' in data:
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                confidence = float(data['conf'][i])
                text = data['text'][i].strip()
                
                if confidence < min_confidence or not text:
                    continue
                
                # 去重
                key = f"{text}_{data['left'][i]//15}_{data['top'][i]//15}"
                if key in seen_texts:
                    continue
                seen_texts.add(key)
                
                region = {
                    "text": text,
                    "position": {
                        "x": int(data['left'][i] * 0.4),  # 缩放回原始尺寸(2.5倍)
                        "y": int(data['top'][i] * 0.4),
                        "width": int(data['width'][i] * 0.4),
                        "height": int(data['height'][i] * 0.4)
                    },
                    "confidence": confidence / 100.0,
                    "level": data['level'][i]
                }
                
                all_regions.append(region)
        
        # 按位置排序
        all_regions.sort(key=lambda x: (x['position']['y'], x['position']['x']))
        
        elapsed = int((time.time() - start_time) * 1000)
        logger.info(f"Extracted {len(all_regions)} text regions in {elapsed}ms")
        
        return all_regions
    
    def parse_structured_fields(self, text: str) -> Dict[str, str]:
        """
        从文字中解析结构化字段
        
        Args:
            text: 输入文字
            
        Returns:
            字段字典 {field_name: value}
        """
        fields = {}
        
        # P/N (料号)
        pn_patterns = [
            r'P/N[:\s]+([A-Z0-9\-]+)',
            r'Part\s+Number[:\s]+([A-Z0-9\-]+)',
            r'PN[:\s]+([A-Z0-9\-]+)'
        ]
        for pattern in pn_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['part_number'] = match.group(1)
                break
        
        # QTY (数量)
        qty_patterns = [
            r'QTY[:\s]+(\d+)',
            r'Quantity[:\s]+(\d+)',
            r'Q[:\s]+(\d+)'
        ]
        for pattern in qty_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['quantity'] = match.group(1)
                break
        
        # DATE (日期)
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}/\d{2}/\d{4})',
            r'Date[:\s]+(\d{4}-\d{2}-\d{2})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['date'] = match.group(1)
                break
        
        # LOT (批次号)
        lot_patterns = [
            r'LOT[:\s]+([A-Z0-9\-]+)',
            r'Batch[:\s]+([A-Z0-9\-]+)',
            r'BATCH[:\s]+([A-Z0-9\-]+)'
        ]
        for pattern in lot_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                fields['lot'] = match.group(1)
                break
        
        logger.debug(f"Parsed fields: {fields}")
        return fields
    
    def recognize_full(
        self, 
        image: np.ndarray, 
        parse_fields: bool = True
    ) -> Dict[str, Any]:
        """
        完整的文字识别流程
        
        Args:
            image: 输入图像
            parse_fields: 是否解析结构化字段
            
        Returns:
            识别结果字典
        """
        start_time = time.time()
        
        # 全图文字识别
        full_text = self.recognize_multimode(image)
        
        # 提取文字区域
        text_regions = self.extract_text_regions(image)
        
        # 解析字段
        fields = {}
        if parse_fields and full_text:
            fields = self.parse_structured_fields(full_text)
        
        result = {
            "full_text": full_text,
            "text_regions": text_regions,
            "structured_fields": fields,
            "ocr_time": int((time.time() - start_time) * 1000)
        }
        
        logger.info(f"OCR completed: {len(full_text)} chars, {len(text_regions)} regions, {len(fields)} fields")
        return result
