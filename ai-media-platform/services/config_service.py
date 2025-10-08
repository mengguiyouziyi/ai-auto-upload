"""
配置服务模块
提供配置文件的加载和管理功能
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class ConfigService:
    """配置服务类"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 尝试多个可能的配置文件位置
        possible_paths = [
            "../config/config.yaml",
            "config/config.yaml",
            "../config/config.example.yaml",
            "config/config.example.yaml"
        ]

        for path in possible_paths:
            if Path(path).exists():
                return path

        raise FileNotFoundError("找不到配置文件")

    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"配置文件加载成功: {self.config_path}")
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def reload(self):
        """重新加载配置文件"""
        self._load_config()


# 全局配置服务实例
_config_service: Optional[ConfigService] = None


def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """获取配置服务实例"""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService(config_path)
    return _config_service.get_all()


def get_config_service() -> ConfigService:
    """获取配置服务实例"""
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service


def reload_config():
    """重新加载配置"""
    global _config_service
    if _config_service is not None:
        _config_service.reload()