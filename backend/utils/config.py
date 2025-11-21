"""
配置管理模块
负责加载和管理系统配置文件
"""
import yaml
import sys
from pathlib import Path
from typing import Dict, Any
from loguru import logger


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        # 打包后的程序需要从正确的位置加载配置
        if getattr(sys, 'frozen', False):
            # PyInstaller打包后,exe在LabelScan目录下,config也在同级
            exe_dir = Path(sys.executable).parent
            self.config_dir = exe_dir / config_dir
            logger.debug(f"Running in packaged mode, exe_dir: {exe_dir}")
        else:
            # 开发环境
            self.config_dir = Path(config_dir)
        
        logger.info(f"Config directory: {self.config_dir}")
        self._configs: Dict[str, Any] = {}
        self._load_all_configs()
    
    def _load_all_configs(self):
        """加载所有配置文件"""
        config_files = {
            "system": "system.yaml",
            "processing": "processing.yaml",
            "logging": "logging.yaml",
            "ocr": "ocr.yaml",
            "ai": "ai.yaml"
        }
        
        for name, filename in config_files.items():
            filepath = self.config_dir / filename
            
            # 如果ocr.yaml不存在,尝试加载example文件
            if name == "ocr" and not filepath.exists():
                filepath = self.config_dir / "ocr.yaml.example"
            
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._configs[name] = yaml.safe_load(f)
                logger.info(f"Loaded config: {filename}")
            else:
                logger.warning(f"Config file not found: {filename}")
                self._configs[name] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值,支持点号分隔的路径
        例如: get("server.port") -> 8000
        """
        parts = key.split('.')
        config_name = parts[0]
        
        if config_name not in self._configs:
            return default
        
        value = self._configs[config_name]
        for part in parts[1:]:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取整个配置节"""
        return self._configs.get(section, {})


# 全局配置实例
config = ConfigManager()
