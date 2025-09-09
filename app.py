from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import asyncio
import os
from bilibili_analyzer import BilibiliAnalyzer
import logging
from datetime import datetime
from config import settings, get_log_file

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_log_file(), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 全局Bilibili分析器实例
analyzer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    global analyzer
    analyzer = BilibiliAnalyzer(whisper_model_name=settings.whisper_model)
    logger.info("应用启动完成")
    yield
    # 关闭时清理
    logger.info("正在关闭应用，清理临时文件...")
    if analyzer:
        analyzer.cleanup()


app = FastAPI(
    title="Bilibili Video Analysis API",
    description="哔哩哔哩视频内容解析服务",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)


class VideoAnalysisRequest(BaseModel):
    """视频分析请求模型"""
    url: str = Field(..., description="哔哩哔哩视频URL")
    use_whisper: bool = Field(False, description="是否使用Whisper进行音频转录")
    enable_formatting: bool = Field(True, description="是否启用文本格式化（添加标点和时间戳）")


class VideoInfoResponse(BaseModel):
    """视频信息响应模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "哔哩哔哩视频内容解析服务",
        "version": settings.app_version,
        "endpoints": {
            "/analyze": "完整视频分析（原始格式）",
            "/analyze-formatted": "完整视频分析（格式化文本，添加标点符号）",
            "/info": "获取视频基本信息",
            "/transcript": "获取视频字幕",
            "/transcribe": "使用Whisper转录音频（支持格式化和时间戳）",
            "/health": "健康检查",
            "/docs": "API文档",
            "/config": "服务配置信息"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/analyze", response_model=VideoInfoResponse)
async def analyze_video(request: VideoAnalysisRequest):
    """
    完整分析哔哩哔哩视频（原始格式）
    
    Args:
        request: 包含URL和选项的请求
        
    Returns:
        完整的视频分析结果
    """
    try:
        logger.info(f"开始分析视频: {request.url}")
        
        # 在后台任务中执行分析，避免阻塞
        result = await asyncio.get_event_loop().run_in_executor(
            None, 
            analyzer.analyze_video, 
            request.url, 
            request.use_whisper
        )
        
        logger.info(f"视频分析完成: {request.url}")
        return VideoInfoResponse(success=True, data=result)
        
    except Exception as e:
        error_msg = f"视频分析失败: {str(e)}"
        logger.error(error_msg)
        return VideoInfoResponse(success=False, error=error_msg)


@app.post("/analyze-formatted", response_model=VideoInfoResponse)
async def analyze_video_formatted(request: VideoAnalysisRequest):
    """
    完整分析哔哩哔哩视频（格式化版本 - 添加标点符号）
    
    Args:
        request: 包含URL和选项的请求
        
    Returns:
        完整的视频分析结果，包含格式化的转录文本
    """
    try:
        logger.info(f"开始格式化分析视频: {request.url}")
        
        # 在后台任务中执行格式化分析，避免阻塞
        result = await asyncio.get_event_loop().run_in_executor(
            None, 
            analyzer.analyze_video_with_formatting, 
            request.url, 
            request.use_whisper
        )
        
        logger.info(f"格式化视频分析完成: {request.url}")
        return VideoInfoResponse(success=True, data=result)
        
    except Exception as e:
        error_msg = f"格式化视频分析失败: {str(e)}"
        logger.error(error_msg)
        return VideoInfoResponse(success=False, error=error_msg)


@app.get("/info", response_model=VideoInfoResponse)
async def get_video_info(url: str = Query(..., description="哔哩哔哩视频URL")):
    """
    获取哔哩哔哩视频基本信息
    
    Args:
        url: 哔哩哔哩视频URL
        
    Returns:
        视频基本信息
    """
    try:
        logger.info(f"获取视频信息: {url}")
        
        info = await asyncio.get_event_loop().run_in_executor(
            None, 
            analyzer.get_video_info, 
            url
        )
        
        logger.info(f"视频信息获取完成: {url}")
        return VideoInfoResponse(success=True, data=info)
        
    except Exception as e:
        error_msg = f"获取视频信息失败: {str(e)}"
        logger.error(error_msg)
        return VideoInfoResponse(success=False, error=error_msg)


@app.get("/transcript", response_model=VideoInfoResponse)
async def get_video_transcript(url: str = Query(..., description="哔哩哔哩视频URL")):
    """
    获取哔哩哔哩视频字幕
    
    Args:
        url: 哔哩哔哩视频URL
        
    Returns:
        视频字幕内容
    """
    try:
        logger.info(f"获取视频字幕: {url}")
        
        video_id = analyzer.extract_bvid_or_avid(url)
        if not video_id:
            raise ValueError("无效的哔哩哔哩URL")
        
        subtitle_info = await asyncio.get_event_loop().run_in_executor(
            None, 
            analyzer.get_subtitles_info, 
            url
        )
        
        result = {
            "video_id": video_id,
            "subtitle_info": subtitle_info,
            "has_subtitles": subtitle_info.get('has_subtitles', False) if subtitle_info else False
        }
        
        logger.info(f"视频字幕获取完成: {url}")
        return VideoInfoResponse(success=True, data=result)
        
    except Exception as e:
        error_msg = f"获取视频字幕失败: {str(e)}"
        logger.error(error_msg)
        return VideoInfoResponse(success=False, error=error_msg)


@app.post("/transcribe", response_model=VideoInfoResponse)
async def transcribe_video_audio(request: VideoAnalysisRequest):
    """
    使用Whisper转录哔哩哔哩视频音频（支持格式化）
    
    Args:
        request: 包含URL和格式化选项的请求
        
    Returns:
        音频转录结果，支持原始文本和格式化文本（带时间戳）
    """
    try:
        logger.info(f"开始音频转录: {request.url}, 格式化: {request.enable_formatting}")
        
        if request.enable_formatting:
            # 使用格式化转录
            # 获取视频基本信息以获得标题
            video_info = await asyncio.get_event_loop().run_in_executor(
                None, 
                analyzer.get_video_info, 
                request.url
            )
            video_title = video_info.get('title', '') if video_info else ''
            
            # 下载音频
            audio_path = await asyncio.get_event_loop().run_in_executor(
                None, 
                analyzer.download_audio, 
                request.url
            )
            
            # 格式化转录音频
            transcript_data = await asyncio.get_event_loop().run_in_executor(
                None, 
                analyzer.transcribe_audio_with_formatting, 
                audio_path,
                video_title
            )
            
            # 清理临时文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            # 确保所有字段都有值
            raw_text = transcript_data.get('raw_text', '')
            formatted_text = transcript_data.get('formatted_text', '')
            timestamped_text = transcript_data.get('timestamped_text', '')
            
            logger.info(f"转录结果 - 原始文本长度: {len(raw_text)}, 格式化文本长度: {len(formatted_text)}, 时间戳文本长度: {len(timestamped_text)}")
            logger.info(f"原始文本前50字符: {raw_text[:50] if raw_text else 'Empty'}")
            
            result = {
                "transcript": timestamped_text or formatted_text or raw_text,  # 优先返回带时间戳的文本
                "formatted_text": formatted_text,
                "raw_text": raw_text,  # 始终返回原始文本
                "timestamped_text": timestamped_text,
                "language": transcript_data.get('language', 'unknown'),
                "sentence_count": transcript_data.get('sentence_count', 0),
                "word_count": transcript_data.get('word_count', 0),
                "processing_applied": transcript_data.get('processing_applied', []),
                "source": "whisper",
                "formatted": True
            }
        else:
            # 使用原始转录（兼容旧版本）
            # 下载音频
            audio_path = await asyncio.get_event_loop().run_in_executor(
                None, 
                analyzer.download_audio, 
                request.url
            )
            
            # 转录音频
            transcript = await asyncio.get_event_loop().run_in_executor(
                None, 
                analyzer.transcribe_audio, 
                audio_path
            )
            
            # 清理临时文件
            if os.path.exists(audio_path):
                os.remove(audio_path)
            
            result = {
                "transcript": transcript,
                "source": "whisper",
                "formatted": False
            }
        
        logger.info(f"音频转录完成: {request.url}")
        return VideoInfoResponse(success=True, data=result)
        
    except Exception as e:
        error_msg = f"音频转录失败: {str(e)}"
        logger.error(error_msg)
        return VideoInfoResponse(success=False, error=error_msg)


@app.get("/config")
async def get_config():
    """获取服务配置信息"""
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "whisper_model": settings.whisper_model,
        "preferred_languages": settings.preferred_languages,
        "max_video_duration": settings.max_video_duration,
        "max_concurrent_requests": settings.max_concurrent_requests,
        "request_timeout": settings.request_timeout
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )