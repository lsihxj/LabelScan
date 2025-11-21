"""
图像预处理引擎
实现图像的标准化处理,包括尺寸调整、灰度转换、对比度增强、噪声过滤等
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from loguru import logger
from pathlib import Path


class ImageProcessor:
    """图像预处理引擎"""
    
    def __init__(self, max_size: int = 2000):
        """
        初始化图像处理器
        
        Args:
            max_size: 最大图像尺寸(像素)
        """
        self.max_size = max_size
        logger.info(f"ImageProcessor initialized with max_size={max_size}")
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        加载图像文件
        
        Args:
            image_path: 图像文件路径
            
        Returns:
            numpy数组格式的图像,加载失败返回None
        """
        try:
            image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                logger.error(f"Failed to load image: {image_path}")
                return None
            logger.debug(f"Loaded image: {image_path}, shape={image.shape}")
            return image
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def resize_if_needed(self, image: np.ndarray) -> np.ndarray:
        """
        如果图像尺寸超过限制,按比例缩小
        
        Args:
            image: 输入图像
            
        Returns:
            调整后的图像
        """
        height, width = image.shape[:2]
        max_dim = max(height, width)
        
        if max_dim > self.max_size:
            scale = self.max_size / max_dim
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            return resized
        
        return image
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        将图像转换为灰度图
        
        Args:
            image: 输入图像(BGR或灰度)
            
        Returns:
            灰度图像
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            logger.debug("Converted to grayscale")
            return gray
        return image
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        使用自适应直方图均衡化增强对比度
        
        Args:
            image: 灰度图像
            
        Returns:
            对比度增强后的图像
        """
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        logger.debug("Applied contrast enhancement")
        return enhanced
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """
        使用中值滤波去除噪声
        
        Args:
            image: 灰度图像
            
        Returns:
            去噪后的图像
        """
        denoised = cv2.medianBlur(image, 3)
        logger.debug("Applied denoising")
        return denoised
    
    def binarize(self, image: np.ndarray) -> np.ndarray:
        """
        使用自适应阈值进行二值化
        
        Args:
            image: 灰度图像
            
        Returns:
            二值化图像
        """
        binary = cv2.adaptiveThreshold(
            image, 
            255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 
            11, 
            2
        )
        logger.debug("Applied binarization")
        return binary
    
    def preprocess(
        self, 
        image: np.ndarray, 
        mode: str = "balanced",
        return_steps: bool = False
    ) -> dict:
        """
        执行完整的预处理流程
        
        Args:
            image: 输入图像
            mode: 处理模式 (fast/balanced/full)
            return_steps: 是否返回中间步骤的图像
            
        Returns:
            包含处理结果的字典
        """
        results = {
            "original": image,
            "processed": None,
            "gray": None,
            "steps": []
        }
        
        # 尺寸调整(所有模式)
        processed = self.resize_if_needed(image)
        if return_steps:
            results["steps"].append(("resized", processed.copy()))
        
        # 灰度转换(所有模式)
        gray = self.to_grayscale(processed)
        results["gray"] = gray
        if return_steps:
            results["steps"].append(("gray", gray.copy()))
        
        # 根据模式选择处理步骤
        if mode == "fast":
            # 极速模式:仅基础处理
            results["processed"] = gray
        
        elif mode == "balanced":
            # 均衡模式:标准处理流程
            enhanced = self.enhance_contrast(gray)
            if return_steps:
                results["steps"].append(("enhanced", enhanced.copy()))
            
            denoised = self.denoise(enhanced)
            if return_steps:
                results["steps"].append(("denoised", denoised.copy()))
            
            results["processed"] = denoised
        
        elif mode == "full":
            # 完整模式:完整处理流程
            enhanced = self.enhance_contrast(gray)
            if return_steps:
                results["steps"].append(("enhanced", enhanced.copy()))
            
            denoised = self.denoise(enhanced)
            if return_steps:
                results["steps"].append(("denoised", denoised.copy()))
            
            binary = self.binarize(denoised)
            if return_steps:
                results["steps"].append(("binary", binary.copy()))
            
            results["processed"] = denoised  # 返回去噪图像,二值化图像备用
            results["binary"] = binary
        
        else:
            logger.warning(f"Unknown mode: {mode}, using balanced mode")
            results["processed"] = self.enhance_contrast(gray)
        
        logger.info(f"Preprocessing completed in {mode} mode")
        return results
    
    def preprocess_from_file(
        self, 
        image_path: str, 
        mode: str = "balanced"
    ) -> Optional[dict]:
        """
        从文件加载并预处理图像
        
        Args:
            image_path: 图像文件路径
            mode: 处理模式
            
        Returns:
            预处理结果,失败返回None
        """
        image = self.load_image(image_path)
        if image is None:
            return None
        
        return self.preprocess(image, mode=mode)
