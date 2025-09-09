import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # API服务配置
    app_name: str = "Bilibili Video Analysis API"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8002
    
    # 哔哩哔哩分析配置
    whisper_model: str = "base"  # tiny, base, small, medium, large
    preferred_languages: List[str] = ["zh-CN", "zh", "en", "en-US"]
    max_video_duration: int = 3600  # 最大视频时长（秒）
    
    # 文件存储配置
    temp_dir: str = ""  # 为空时使用系统临时目录
    keep_temp_files: bool = False  # 是否保留临时文件
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = ""  # 为空时自动生成
    
    # API限制
    max_concurrent_requests: int = 10
    request_timeout: int = 300  # 请求超时时间（秒）
    
    class Config:
        env_file = ".env"
        env_prefix = "VIDEO_API_"


# 全局设置实例
settings = Settings()


def get_temp_dir() -> str:
    """获取临时目录路径"""
    if settings.temp_dir:
        os.makedirs(settings.temp_dir, exist_ok=True)
        return settings.temp_dir
    return os.path.join(os.path.dirname(__file__), "temp")


def get_log_file() -> str:
    """获取日志文件路径"""
    if settings.log_file:
        return settings.log_file
    
    from datetime import datetime
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f'video_api_{datetime.now().strftime("%Y%m%d")}.log')