"""
关联分析引擎
建立条码与周围文字的语义关联
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from loguru import logger
import math


class AssociationAnalyzer:
    """关联分析引擎"""
    
    def __init__(
        self,
        max_search_radius_multiplier: float = 2.0,
        direction_weights: Dict[str, float] = None,
        strong_threshold: float = 0.5,
        weak_threshold: float = 0.3
    ):
        """
        初始化关联分析器
        
        Args:
            max_search_radius_multiplier: 最大搜索半径倍数(相对条码宽度)
            direction_weights: 方向权重
            strong_threshold: 强关联阈值
            weak_threshold: 弱关联阈值
        """
        self.max_search_radius_multiplier = max_search_radius_multiplier
        self.direction_weights = direction_weights or {
            "right": 0.8,
            "bottom": 0.6,
            "left": 0.4,
            "top": 0.3
        }
        self.strong_threshold = strong_threshold
        self.weak_threshold = weak_threshold
        
        logger.info(f"AssociationAnalyzer initialized with thresholds: strong={strong_threshold}, weak={weak_threshold}")
    
    def _get_center(self, position: Dict[str, int]) -> Tuple[float, float]:
        """获取区域中心点"""
        x = position["x"] + position["width"] / 2
        y = position["y"] + position["height"] / 2
        return (x, y)
    
    def _calculate_distance(
        self, 
        pos1: Dict[str, int], 
        pos2: Dict[str, int]
    ) -> float:
        """计算两个区域中心点的欧氏距离"""
        cx1, cy1 = self._get_center(pos1)
        cx2, cy2 = self._get_center(pos2)
        return math.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)
    
    def _get_direction(
        self, 
        barcode_pos: Dict[str, int], 
        text_pos: Dict[str, int]
    ) -> str:
        """
        判断文字相对于条码的方向
        
        Returns:
            "right", "bottom", "left", "top"
        """
        bc_cx, bc_cy = self._get_center(barcode_pos)
        txt_cx, txt_cy = self._get_center(text_pos)
        
        dx = txt_cx - bc_cx
        dy = txt_cy - bc_cy
        
        # 根据角度判断主要方向
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        else:
            return "bottom" if dy > 0 else "top"
    
    def _calculate_association_score(
        self,
        barcode: Dict[str, Any],
        text_region: Dict[str, Any]
    ) -> float:
        """
        计算条码和文字区域的关联评分
        
        Returns:
            关联评分(0-1),值越高表示关联越强
        """
        barcode_pos = barcode["position"]
        text_pos = text_region["position"]
        
        # 计算最大搜索半径
        max_radius = barcode_pos["width"] * self.max_search_radius_multiplier
        
        # 计算距离
        distance = self._calculate_distance(barcode_pos, text_pos)
        
        # 超出搜索半径,不关联
        if distance > max_radius:
            return 0.0
        
        # 距离评分(距离越近评分越高)
        distance_score = 1.0 - (distance / max_radius)
        
        # 方向权重
        direction = self._get_direction(barcode_pos, text_pos)
        direction_weight = self.direction_weights.get(direction, 0.5)
        
        # 综合评分
        score = distance_score * direction_weight
        
        return score
    
    def associate_text_with_barcodes(
        self,
        barcodes: List[Dict[str, Any]],
        text_regions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        为每个条码关联相关的文字区域
        
        Args:
            barcodes: 条码列表
            text_regions: 文字区域列表
            
        Returns:
            关联结果列表,每个包含:
            - barcode: 条码信息
            - related_text: 关联的文字列表
            - relation_type: 关联类型(strong/weak/none)
        """
        results = []
        used_text_indices = set()
        
        for barcode in barcodes:
            associations = []
            
            for idx, text_region in enumerate(text_regions):
                if idx in used_text_indices:
                    continue
                
                score = self._calculate_association_score(barcode, text_region)
                
                if score >= self.weak_threshold:
                    associations.append({
                        "text": text_region["text"],
                        "position": text_region["position"],
                        "confidence": text_region.get("confidence", 1.0),
                        "score": score,
                        "relation_type": "strong" if score >= self.strong_threshold else "weak"
                    })
                    
                    # 如果是强关联,标记为已使用
                    if score >= self.strong_threshold:
                        used_text_indices.add(idx)
            
            # 按评分降序排序
            associations.sort(key=lambda x: x["score"], reverse=True)
            
            result = {
                "barcode": barcode,
                "related_text": associations,
                "has_association": len(associations) > 0
            }
            
            results.append(result)
            
            logger.debug(f"Barcode {barcode['barcode_data']}: {len(associations)} associations")
        
        # 记录未关联的文字(独立文字)
        independent_text = []
        for idx, text_region in enumerate(text_regions):
            if idx not in used_text_indices:
                independent_text.append({
                    "text": text_region["text"],
                    "position": text_region["position"],
                    "type": "independent"
                })
        
        logger.info(f"Association complete: {len(results)} barcodes, {len(independent_text)} independent text")
        
        return results, independent_text
    
    def create_groups(
        self,
        associations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        创建条码-文字混合组
        
        Args:
            associations: 关联结果
            
        Returns:
            混合组列表
        """
        groups = []
        
        for assoc in associations:
            barcode = assoc["barcode"]
            related = assoc["related_text"]
            
            # 合并相关文字
            combined_text = " ".join([r["text"] for r in related])
            
            group = {
                "barcode_data": barcode["barcode_data"],
                "barcode_type": barcode["barcode_type"],
                "position": barcode["position"],
                "related_text": combined_text,
                "text_count": len(related),
                "relation_strength": "strong" if any(r["relation_type"] == "strong" for r in related) else "weak"
            }
            
            groups.append(group)
        
        return groups
