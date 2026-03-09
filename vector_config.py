#!/usr/bin/env python3
"""
OpenClaw 向量记忆配置管理
"""

import os
import json
from typing import Optional, Dict
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
CONFIG_DIR = os.path.join(WORKSPACE, ".vector_store")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# 默认配置
DEFAULT_CONFIG = {
    "auto_sync": False,
    "sync_interval_minutes": 30,
    "api_port": 8765,
    "api_host": "127.0.0.1",
    "log_level": "INFO",
    "log_max_bytes": 5 * 1024 * 1024,  # 5MB
    "log_backup_count": 3,
    "max_results": 10,
    "indexed_extensions": [".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml"],
}


class Config:
    """配置管理器"""
    
    def __init__(self):
        self._config: Dict = {}
        self._load()
    
    def _load(self):
        """加载配置"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self._config = json.load(f)
                # 合并默认配置
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self._config:
                        self._config[key] = value
            except json.JSONDecodeError:
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
    
    def save(self):
        """保存配置"""
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._config, f, indent=2)
    
    def get(self, key: str, default=None):
        """获取配置"""
        return self._config.get(key, default)
    
    def set(self, key: str, value):
        """设置配置"""
        self._config[key] = value
        self.save()
    
    def __getitem__(self, key: str):
        return self._config[key]
    
    def __setitem__(self, key: str, value):
        self._config[key] = value
    
    @property
    def auto_sync(self) -> bool:
        return self._config.get("auto_sync", False)
    
    @auto_sync.setter
    def auto_sync(self, value: bool):
        self._config["auto_sync"] = value
        self.save()
    
    @property
    def sync_interval(self) -> int:
        return self._config.get("sync_interval_minutes", 30)
    
    @sync_interval.setter
    def sync_interval(self, value: int):
        self._config["sync_interval_minutes"] = value
        self.save()


# ============== 配置校验 ==============
def validate_config(config_dict: dict) -> tuple[bool, str]:
    """校验配置"""
    
    # 端口校验
    port = config_dict.get("api_port")
    if port and (not isinstance(port, int) or port < 1 or port > 65535):
        return False, f"端口必须为 1-65535 的整数，当前值: {port}"
    
    # 同步间隔校验
    interval = config_dict.get("sync_interval_minutes")
    if interval and (not isinstance(interval, int) or interval < 1 or interval > 1440):
        return False, f"同步间隔必须为 1-1440 分钟，当前值: {interval}"
    
    # 日志大小校验
    log_max = config_dict.get("log_max_bytes")
    if log_max and (not isinstance(log_max, int) or log_max < 1024):
        return False, f"日志大小必须 >= 1024 字节，当前值: {log_max}"
    
    return True, ""


# 修改 Config 类的 set 方法
_original_set = Config.set

def _validated_set(self, key: str, value):
    """带校验的设置"""
    # 校验
    test_config = self._config.copy()
    test_config[key] = value
    valid, msg = validate_config(test_config)
    if not valid:
        raise ValueError(msg)
    _original_set(self, key, value)

Config.set = _validated_set

# 全局配置实例
config = Config()
