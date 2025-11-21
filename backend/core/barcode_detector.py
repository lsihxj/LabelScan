"""
条码识别引擎
使用pyzbar库识别图像中的所有条码(一维码和二维码)
"""
import cv2
import numpy as np
from pyzbar import pyzbar
from typing import List, Dict, Any, Tuple
from loguru import logger
import time


class BarcodeDetector:
    """条码识别引擎"""
    
    def __init__(self):
        """初始化条码检测器"""
        logger.info("BarcodeDetector initialized")
    
    def decode_barcodes(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        识别图像中的所有条码
        
        Args:
            image: 输入图像(灰度或彩色)
            
        Returns:
            条码列表,每个条码包含:
            - barcode_data: 条码内容
            - barcode_type: 条码类型
            - position: 位置信息 {x, y, width, height}
            - confidence: 置信度(pyzbar不提供,设为1.0)
            - decode_time: 解码耗时(毫秒)
            - polygon: 多边形顶点坐标
        """
        start_time = time.time()
        
        try:
            # pyzbar解码
            decoded_objects = pyzbar.decode(image)
            
            barcodes = []
            for obj in decoded_objects:
                # 提取位置信息
                rect = obj.rect
                position = {
                    "x": rect.left,
                    "y": rect.top,
                    "width": rect.width,
                    "height": rect.height
                }
                
                # 多边形顶点
                polygon = [(point.x, point.y) for point in obj.polygon]
                
                # 解码数据
                data = obj.data.decode('utf-8', errors='ignore')
                
                barcode_info = {
                    "barcode_data": data,
                    "barcode_type": obj.type,
                    "position": position,
                    "confidence": 1.0,  # pyzbar不提供置信度
                    "decode_time": int((time.time() - start_time) * 1000),
                    "polygon": polygon
                }
                
                barcodes.append(barcode_info)
                logger.debug(f"Detected {obj.type}: {data}")
            
            decode_time = int((time.time() - start_time) * 1000)
            logger.info(f"Detected {len(barcodes)} barcodes in {decode_time}ms")
            
            return barcodes
        
        except Exception as e:
            logger.error(f"Error detecting barcodes: {e}")
            return []
    
    def decode_with_enhancement(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        使用多种图像增强方法进行多次解码，合并结果
        
        Args:
            image: 输入图像
            
        Returns:
            条码列表
        """
        all_barcodes = []
        detected_data = set()  # 用于去重
        
        # 第一次尝试:原图
        logger.debug("Try 1: Original image")
        barcodes = self.decode_barcodes(image)
        for bc in barcodes:
            if bc['barcode_data'] not in detected_data:
                all_barcodes.append(bc)
                detected_data.add(bc['barcode_data'])
        
        # 第二次尝试:增强对比度
        logger.debug("Try 2: Contrast enhancement")
        if len(image.shape) == 2:
            enhanced = cv2.equalizeHist(image)
        else:
            enhanced = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            enhanced = cv2.equalizeHist(enhanced)
        
        barcodes = self.decode_barcodes(enhanced)
        for bc in barcodes:
            if bc['barcode_data'] not in detected_data:
                all_barcodes.append(bc)
                detected_data.add(bc['barcode_data'])
                logger.debug(f"Found new barcode with contrast enhancement: {bc['barcode_data']}")
        
        # 第三次尝试:CLAHE自适应直方图均衡化
        logger.debug("Try 3: CLAHE enhancement")
        gray = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        clahe_img = clahe.apply(gray)
        
        barcodes = self.decode_barcodes(clahe_img)
        for bc in barcodes:
            if bc['barcode_data'] not in detected_data:
                all_barcodes.append(bc)
                detected_data.add(bc['barcode_data'])
                logger.debug(f"Found new barcode with CLAHE: {bc['barcode_data']}")
        
        # 第四次尝试:二值化(Otsu)
        logger.debug("Try 4: Otsu binarization")
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        barcodes = self.decode_barcodes(binary)
        for bc in barcodes:
            if bc['barcode_data'] not in detected_data:
                all_barcodes.append(bc)
                detected_data.add(bc['barcode_data'])
                logger.debug(f"Found new barcode with Otsu: {bc['barcode_data']}")
        
        # 第五次尝试:反色二值化
        logger.debug("Try 5: Inverted Otsu binarization")
        _, binary_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        barcodes = self.decode_barcodes(binary_inv)
        for bc in barcodes:
            if bc['barcode_data'] not in detected_data:
                all_barcodes.append(bc)
                detected_data.add(bc['barcode_data'])
                logger.debug(f"Found new barcode with inverted Otsu: {bc['barcode_data']}")
        
        # 第六次尝试:锐化
        logger.debug("Try 6: Sharpening")
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(gray, -1, kernel)
        barcodes = self.decode_barcodes(sharpened)
        for bc in barcodes:
            if bc['barcode_data'] not in detected_data:
                all_barcodes.append(bc)
                detected_data.add(bc['barcode_data'])
                logger.debug(f"Found new barcode with sharpening: {bc['barcode_data']}")
        
        # 第七次尝试:形态学操作(增强条码线条)
        logger.debug("Try 7: Morphological operations")
        kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph_close = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel_morph)
        barcodes = self.decode_barcodes(morph_close)
        for bc in barcodes:
            if bc['barcode_data'] not in detected_data:
                all_barcodes.append(bc)
                detected_data.add(bc['barcode_data'])
                logger.debug(f"Found new barcode with morphology: {bc['barcode_data']}")
        
        # 第八次尝试:增大图像(如果条码很小)
        logger.debug("Try 8: Upscaling")
        height, width = gray.shape[:2]
        if max(height, width) < 1500:
            upscaled = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
            barcodes = self.decode_barcodes(upscaled)
            # 调整坐标回原始尺寸
            for bc in barcodes:
                if bc['barcode_data'] not in detected_data:
                    bc['position']['x'] = int(bc['position']['x'] / 1.5)
                    bc['position']['y'] = int(bc['position']['y'] / 1.5)
                    bc['position']['width'] = int(bc['position']['width'] / 1.5)
                    bc['position']['height'] = int(bc['position']['height'] / 1.5)
                    all_barcodes.append(bc)
                    detected_data.add(bc['barcode_data'])
                    logger.debug(f"Found new barcode with upscaling: {bc['barcode_data']}")
        
        logger.info(f"Total detected {len(all_barcodes)} unique barcodes using multi-method approach")
        return all_barcodes
    
    def detect(
        self, 
        image: np.ndarray, 
        try_enhancement: bool = True
    ) -> List[Dict[str, Any]]:
        """
        检测图像中的条码(主入口)
        
        Args:
            image: 输入图像
            try_enhancement: 是否在失败时尝试图像增强
            
        Returns:
            条码列表
        """
        if try_enhancement:
            return self.decode_with_enhancement(image)
        else:
            return self.decode_barcodes(image)
    
    def get_barcode_region(
        self, 
        image: np.ndarray, 
        barcode: Dict[str, Any],
        expand_ratio: float = 0.1
    ) -> np.ndarray:
        """
        提取条码区域图像(可用于后续分析)
        
        Args:
            image: 原图像
            barcode: 条码信息
            expand_ratio: 扩展比例(扩大区域以包含周围文字)
            
        Returns:
            条码区域图像
        """
        pos = barcode["position"]
        x, y, w, h = pos["x"], pos["y"], pos["width"], pos["height"]
        
        # 扩展区域
        expand_w = int(w * expand_ratio)
        expand_h = int(h * expand_ratio)
        
        x1 = max(0, x - expand_w)
        y1 = max(0, y - expand_h)
        x2 = min(image.shape[1], x + w + expand_w)
        y2 = min(image.shape[0], y + h + expand_h)
        
        return image[y1:y2, x1:x2]
    
    def draw_barcodes(
        self, 
        image: np.ndarray, 
        barcodes: List[Dict[str, Any]],
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        在图像上绘制条码边界框
        
        Args:
            image: 输入图像
            barcodes: 条码列表
            color: 边框颜色(BGR)
            thickness: 线条宽度
            
        Returns:
            标注后的图像
        """
        result = image.copy()
        if len(result.shape) == 2:
            result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
        
        for idx, barcode in enumerate(barcodes):
            pos = barcode["position"]
            x, y, w, h = pos["x"], pos["y"], pos["width"], pos["height"]
            
            # 绘制矩形
            cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
            
            # 绘制序号和类型
            label = f"{idx + 1}:{barcode['barcode_type']}"
            cv2.putText(
                result, 
                label, 
                (x, y - 5), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, 
                color, 
                1
            )
        
        return result
