"""
智能排序引擎
按人类阅读习惯对识别结果进行排序
"""
from typing import List, Dict, Any
from loguru import logger


class OrderSorter:
    """智能排序引擎"""
    
    def __init__(
        self,
        row_tolerance: int = 30,
        col_tolerance: int = 20,
        min_object_distance: int = 15
    ):
        """
        初始化排序器
        
        Args:
            row_tolerance: 行容差(像素)
            col_tolerance: 列容差(像素)
            min_object_distance: 最小对象间距(像素)
        """
        self.row_tolerance = row_tolerance
        self.col_tolerance = col_tolerance
        self.min_object_distance = min_object_distance
        
        logger.info(f"OrderSorter initialized with row_tolerance={row_tolerance}, col_tolerance={col_tolerance}")
    
    def _get_y_center(self, obj: Dict[str, Any]) -> float:
        """获取对象Y坐标中心"""
        pos = obj.get("position", {})
        return pos.get("y", 0) + pos.get("height", 0) / 2
    
    def _get_x_center(self, obj: Dict[str, Any]) -> float:
        """获取对象X坐标中心"""
        pos = obj.get("position", {})
        return pos.get("x", 0) + pos.get("width", 0) / 2
    
    def sort_top_to_bottom(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按从上到下排序
        
        Args:
            objects: 对象列表
            
        Returns:
            排序后的对象列表
        """
        sorted_objects = sorted(objects, key=lambda obj: self._get_y_center(obj))
        logger.debug(f"Sorted {len(objects)} objects top-to-bottom")
        return sorted_objects
    
    def sort_left_to_right(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按从左到右排序
        
        Args:
            objects: 对象列表
            
        Returns:
            排序后的对象列表
        """
        sorted_objects = sorted(objects, key=lambda obj: self._get_x_center(obj))
        logger.debug(f"Sorted {len(objects)} objects left-to-right")
        return sorted_objects
    
    def sort_reading_order(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按阅读顺序排序(先按行分组,行内从左到右)
        
        Args:
            objects: 对象列表
            
        Returns:
            排序后的对象列表
        """
        if not objects:
            return []
        
        # 先按Y坐标排序
        y_sorted = sorted(objects, key=lambda obj: self._get_y_center(obj))
        
        # 行分组
        rows = []
        current_row = [y_sorted[0]]
        current_y = self._get_y_center(y_sorted[0])
        
        for obj in y_sorted[1:]:
            obj_y = self._get_y_center(obj)
            
            # 判断是否在同一行
            if abs(obj_y - current_y) <= self.row_tolerance:
                current_row.append(obj)
            else:
                # 开始新行
                rows.append(current_row)
                current_row = [obj]
                current_y = obj_y
        
        # 添加最后一行
        if current_row:
            rows.append(current_row)
        
        logger.debug(f"Grouped into {len(rows)} rows")
        
        # 每行内按X坐标排序
        result = []
        for row in rows:
            sorted_row = sorted(row, key=lambda obj: self._get_x_center(obj))
            result.extend(sorted_row)
        
        logger.info(f"Sorted {len(objects)} objects in reading order")
        return result
    
    def sort_grid_order(self, objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按网格顺序排序(适用于整齐排列的多标签)
        
        Args:
            objects: 对象列表
            
        Returns:
            排序后的对象列表
        """
        # 简化版:先按行分组,再按列分组
        reading_sorted = self.sort_reading_order(objects)
        return reading_sorted
    
    def sort(
        self, 
        objects: List[Dict[str, Any]], 
        order: str = "reading_order"
    ) -> List[Dict[str, Any]]:
        """
        排序主入口
        
        Args:
            objects: 对象列表
            order: 排序方式 (reading_order/top_to_bottom/left_to_right/grid_order)
            
        Returns:
            排序后的对象列表
        """
        if not objects:
            return []
        
        if order == "top_to_bottom":
            return self.sort_top_to_bottom(objects)
        elif order == "left_to_right":
            return self.sort_left_to_right(objects)
        elif order == "grid_order":
            return self.sort_grid_order(objects)
        else:  # reading_order (default)
            return self.sort_reading_order(objects)
    
    def add_order_numbers(
        self, 
        objects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        为对象添加排序序号
        
        Args:
            objects: 已排序的对象列表
            
        Returns:
            添加了order字段的对象列表
        """
        for idx, obj in enumerate(objects):
            obj["order"] = idx + 1
        
        return objects
