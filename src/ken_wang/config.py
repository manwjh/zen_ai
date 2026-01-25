"""
KenWang 配置加载工具
"""

from pathlib import Path
import yaml
from typing import Dict, Any


def load_ken_wang_config() -> Dict[str, Any]:
    """加载 KenWang 配置"""
    config_path = Path(__file__).parent.parent.parent / "config.yml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_zen_content_url() -> str:
    """获取 ZenContent 服务 URL"""
    config = load_ken_wang_config()
    return config.get('services', {}).get('zen_content_url', 'http://localhost:5002')


def get_internal_api_key() -> str:
    """获取内部API密钥"""
    config = load_ken_wang_config()
    return config.get('security', {}).get('internal_api_key', '')
