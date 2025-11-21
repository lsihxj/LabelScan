"""
主处理器
整合所有引擎,提供完整的图像识别流程
"""
import time
import numpy as np
from typing import Dict, Any, List, Optional
from loguru import logger

from .image_processor import ImageProcessor
from .barcode_detector import BarcodeDetector
from .text_recognizer import TextRecognizer
from .ai_recognizer import AIRecognizer
from .association_analyzer import AssociationAnalyzer
from .order_sorter import OrderSorter


class LabelProcessor:
    """电子标签处理器"""
    
    def __init__(self, config: dict = None):
        """
        初始化处理器
        
        Args:
            config: 配置字典
        """
        config = config or {}
        
        # 初始化各引擎
        self.image_processor = ImageProcessor(
            max_size=config.get("max_image_size", 2000)
        )
        self.barcode_detector = BarcodeDetector()
        self.text_recognizer = TextRecognizer(
            tesseract_cmd=config.get("tesseract_cmd"),
            lang=config.get("ocr_lang", "eng+chi_sim")
        )
        # 初始化AI识别器
        self.ai_recognizer = AIRecognizer(config.get("ai", {}))
        
        self.association_analyzer = AssociationAnalyzer(
            max_search_radius_multiplier=config.get("max_search_radius_multiplier", 2.0),
            strong_threshold=config.get("strong_threshold", 0.5),
            weak_threshold=config.get("weak_threshold", 0.3)
        )
        self.order_sorter = OrderSorter(
            row_tolerance=config.get("row_tolerance", 30),
            col_tolerance=config.get("col_tolerance", 20)
        )
        
        logger.info("LabelProcessor initialized")
    
    def process_image(
        self,
        image: np.ndarray,
        mode: str = "balanced",
        recognition_mode: str = "barcode_only",
        sort_order: str = "top_to_bottom",
        ocr_mode: str = "local"
    ) -> Dict[str, Any]:
        """
        处理单张图像
        
        Args:
            image: 输入图像
            mode: 处理模式 (fast/balanced/full)
            recognition_mode: 识别模式 (barcode_only/ocr_only/barcode_and_ocr/ai)
            sort_order: 排序方式
            ocr_mode: OCR模式 (local/cloud)
            
        Returns:
            处理结果字典
        """
        start_time = time.time()
        logger.info(f"Processing image in {mode} mode, recognition_mode={recognition_mode}")
        
        result = {
            "success": True,
            "mode_used": mode,
            "recognition_mode": recognition_mode,
            "sort_order": sort_order,
            "results": [],
            "process_time": 0,
            "error": None
        }
        
        try:
            # 1. 图像预处理
            preprocessed = self.image_processor.preprocess(image, mode=mode)
            processed_img = preprocessed["processed"]
            
            # 2. 根据识别模式执行不同的识别流程
            if recognition_mode == "ai":
                # AI识别模式
                logger.info("Starting AI recognition...")
                if not self.ai_recognizer.is_available():
                    error_msg = "AI识别功能不可用,请检查配置:"
                    if not self.ai_recognizer.enabled:
                        error_msg += " AI功能未启用"
                    elif not self.ai_recognizer.active_model_id:
                        error_msg += " 未选择激活的模型"
                    else:
                        model = self.ai_recognizer.models.get(self.ai_recognizer.active_model_id)
                        if not model:
                            error_msg += f" 模型{self.ai_recognizer.active_model_id}不存在"
                        else:
                            provider = self.ai_recognizer.providers.get(model.get('provider_id'))
                            if not provider:
                                error_msg += f" 提供商{model.get('provider_id')}不存在"
                            elif not provider.get('enabled'):
                                error_msg += f" 提供商{model.get('provider_id')}未启用"
                            elif not provider.get('api_key'):
                                error_msg += f" 提供商{model.get('provider_id')}缺少API Key"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                try:
                    ai_result = self.ai_recognizer.recognize(image)
                except Exception as e:
                    logger.error(f"AI recognition failed: {e}", exc_info=True)
                    raise Exception(f"AI识别失败: {str(e)}")
                
                # 合并条码和文字结果
                mixed_objects = []
                
                for bc in ai_result.get("barcodes", []):
                    mixed_objects.append({
                        "type": "barcode",
                        "position": bc["position"],
                        "data": {
                            "barcode_data": bc["barcode_data"],
                            "barcode_type": bc["barcode_type"]
                        }
                    })
                
                for text in ai_result.get("texts", []):
                    mixed_objects.append({
                        "type": "text",
                        "position": text["position"],
                        "data": {
                            "text": text["text"],
                            "confidence": text.get("confidence", 1.0)
                        }
                    })
                
                # 排序
                sorted_objects = self.order_sorter.sort(mixed_objects, order=sort_order)
                sorted_objects = self.order_sorter.add_order_numbers(sorted_objects)
                
                result["results"] = sorted_objects
                result["ai_raw_response"] = ai_result.get("raw_response")
            
            elif recognition_mode == "barcode_only":
                # 纯条码识别
                barcodes = self.barcode_detector.detect(processed_img, try_enhancement=True)
                logger.info(f"Detected {len(barcodes)} barcodes")
                
                sorted_barcodes = self.order_sorter.sort(barcodes, order=sort_order)
                sorted_barcodes = self.order_sorter.add_order_numbers(sorted_barcodes)
                
                result["results"] = [
                    {
                        "order": bc["order"],
                        "type": "barcode",
                        "data": {
                            "barcode_data": bc["barcode_data"],
                            "barcode_type": bc["barcode_type"]
                        },
                        "position": bc["position"]
                    }
                    for bc in sorted_barcodes
                ]
            
            elif recognition_mode == "ocr_only":
                # 纯OCR识别 - 根据mode调整OCR策略
                if not self.text_recognizer.tesseract_available:
                    raise Exception("OCR功能不可用,请安装Tesseract OCR")
                
                # 使用原图进行OCR识别(预处理后的图可能不适合OCR)
                if mode == "fast":
                    # 极速模式: 仅使用基础OCR
                    ocr_result = self.text_recognizer.recognize_full(image, parse_fields=True)
                elif mode == "balanced":
                    # 均衡模式: 使用多模式OCR
                    ocr_result = self.text_recognizer.recognize_full(image, parse_fields=True)
                else:  # full
                    # 完整模式: 使用多模式OCR + 原图
                    ocr_result = self.text_recognizer.recognize_full(image, parse_fields=True)
                
                text_regions = ocr_result["text_regions"]
                
                sorted_texts = self.order_sorter.sort(text_regions, order=sort_order)
                sorted_texts = self.order_sorter.add_order_numbers(sorted_texts)
                
                result["results"] = [
                    {
                        "order": text["order"],
                        "type": "text",
                        "data": {
                            "text": text["text"],
                            "confidence": text.get("confidence", 0)
                        },
                        "position": text["position"]
                    }
                    for text in sorted_texts
                ]
                result["structured_fields"] = ocr_result["structured_fields"]
                if mode == "full":
                    result["full_text"] = ocr_result["full_text"]
            
            elif recognition_mode == "barcode_and_ocr":
                # OCR&条码：智能关联处理
                # 条码识别
                barcodes = self.barcode_detector.detect(processed_img, try_enhancement=True)
                logger.info(f"Detected {len(barcodes)} barcodes")
                
                # 根据mode执行不同流程
                if mode == "fast" or not self.text_recognizer.tesseract_available:
                    # 极速模式或OCR不可用:仅条码
                    if not self.text_recognizer.tesseract_available:
                        logger.warning("OCR not available, using barcode only")
                    
                    sorted_barcodes = self.order_sorter.sort(barcodes, order=sort_order)
                    sorted_barcodes = self.order_sorter.add_order_numbers(sorted_barcodes)
                    
                    result["results"] = [
                        {
                            "order": bc["order"],
                            "type": "barcode",
                            "data": {
                                "barcode_data": bc["barcode_data"],
                                "barcode_type": bc["barcode_type"]
                            },
                            "position": bc["position"]
                        }
                        for bc in sorted_barcodes
                    ]
                
                elif mode == "balanced":
                    # 均衡模式:条码+关键文字(使用原图)
                    ocr_result = self.text_recognizer.recognize_full(image, parse_fields=True)
                    text_regions = ocr_result["text_regions"]
                    
                    associations, independent_text = self.association_analyzer.associate_text_with_barcodes(
                        barcodes, text_regions
                    )
                    
                    mixed_objects = []
                    
                    for assoc in associations:
                        bc = assoc["barcode"]
                        related_texts = [r["text"] for r in assoc["related_text"]]
                        
                        obj = {
                            "type": "barcode_group",
                            "position": bc["position"],
                            "data": {
                                "barcode_data": bc["barcode_data"],
                                "barcode_type": bc["barcode_type"],
                                "related_text": " ".join(related_texts) if related_texts else None
                            }
                        }
                        mixed_objects.append(obj)
                    
                    for text in independent_text:
                        obj = {
                            "type": "text",
                            "position": text["position"],
                            "data": {
                                "text": text["text"]
                            }
                        }
                        mixed_objects.append(obj)
                    
                    sorted_objects = self.order_sorter.sort(mixed_objects, order=sort_order)
                    sorted_objects = self.order_sorter.add_order_numbers(sorted_objects)
                    
                    result["results"] = sorted_objects
                    result["structured_fields"] = ocr_result["structured_fields"]
                
                elif mode == "full":
                    # 完整模式:条码+全文字+深度关联(使用原图)
                    ocr_result = self.text_recognizer.recognize_full(image, parse_fields=True)
                    text_regions = ocr_result["text_regions"]
                    
                    associations, independent_text = self.association_analyzer.associate_text_with_barcodes(
                        barcodes, text_regions
                    )
                    
                    mixed_objects = []
                    
                    for assoc in associations:
                        bc = assoc["barcode"]
                        
                        obj = {
                            "type": "barcode_group",
                            "position": bc["position"],
                            "data": {
                                "barcode_data": bc["barcode_data"],
                                "barcode_type": bc["barcode_type"],
                                "related_text_details": assoc["related_text"]
                            }
                        }
                        mixed_objects.append(obj)
                    
                    for text in independent_text:
                        obj = {
                            "type": "text",
                            "position": text["position"],
                            "data": {
                                "text": text["text"]
                            }
                        }
                        mixed_objects.append(obj)
                    
                    sorted_objects = self.order_sorter.sort(mixed_objects, order=sort_order)
                    sorted_objects = self.order_sorter.add_order_numbers(sorted_objects)
                    
                    result["results"] = sorted_objects
                    result["full_text"] = ocr_result["full_text"]
                    result["structured_fields"] = ocr_result["structured_fields"]
        
        except Exception as e:
            logger.error(f"Error processing image: {e}", exc_info=True)
            result["success"] = False
            result["error"] = str(e)
        
        result["process_time"] = int((time.time() - start_time) * 1000)
        logger.info(f"Processing completed in {result['process_time']}ms")
        
        return result
    
    def process_image_file(
        self,
        image_path: str,
        mode: str = "balanced",
        recognition_mode: str = "barcode_only",
        sort_order: str = "top_to_bottom",
        ocr_mode: str = "local"
    ) -> Optional[Dict[str, Any]]:
        """
        从文件处理图像
        
        Args:
            image_path: 图像文件路径
            mode: 处理模式
            recognition_mode: 识别模式
            sort_order: 排序方式
            ocr_mode: OCR模式
            
        Returns:
            处理结果,失败返回None
        """
        image = self.image_processor.load_image(image_path)
        if image is None:
            return {
                "success": False,
                "error": "Failed to load image"
            }
        
        return self.process_image(image, mode, recognition_mode, sort_order, ocr_mode)
