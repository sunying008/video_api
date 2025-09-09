import os
import tempfile
import json
import asyncio
from typing import Optional, Dict, Any, List
import yt_dlp
import whisper
import ffmpeg
import re
import requests
import subprocess
import shutil
from urllib.parse import urlparse, parse_qs
from text_processor import TextPostProcessor


class BilibiliAnalyzer:
    """哔哩哔哩视频内容分析器"""
    
    def __init__(self, whisper_model_name: str = "base"):
        """
        初始化Bilibili分析器
        
        Args:
            whisper_model_name: Whisper模型名称 (tiny, base, small, medium, large)
        """
        try:
            self.whisper_model = whisper.load_model(whisper_model_name)
        except Exception as e:
            print(f"警告: 无法加载Whisper模型 {whisper_model_name}: {str(e)}")
            self.whisper_model = None
        self.temp_dir = tempfile.gettempdir()
        
        # 初始化文本后处理器
        self.text_processor = TextPostProcessor()
        
        # 检查ffmpeg是否可用
        self.ffmpeg_available = self._check_ffmpeg()
        if not self.ffmpeg_available:
            print("警告: 未找到ffmpeg，音频转录功能将不可用")
    
    def _check_ffmpeg(self) -> bool:
        """检查ffmpeg是否可用"""
        try:
            # 尝试查找ffmpeg
            ffmpeg_path = shutil.which('ffmpeg')
            if ffmpeg_path:
                return True
            
            # 尝试直接运行ffmpeg命令
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            return False
        
    def extract_bvid_or_avid(self, url: str) -> Optional[str]:
        """
        从Bilibili URL中提取BVID或AVID
        
        Args:
            url: Bilibili URL
            
        Returns:
            视频ID或None
        """
        patterns = [
            r'BV([0-9A-Za-z]{10})',  # BV号
            r'av(\d+)',              # av号
            r'bilibili\.com/video/(BV[0-9A-Za-z]{10})',
            r'bilibili\.com/video/(av\d+)',
            r'b23\.tv/([0-9A-Za-z]+)',  # 短链接
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1) if pattern.startswith('BV') or pattern.startswith('av') else match.group(1)
        return None
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        获取Bilibili视频基本信息
        
        Args:
            url: Bilibili URL
            
        Returns:
            视频信息字典
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'duration': info.get('duration'),  # 秒
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'upload_date': info.get('upload_date'),
                    'uploader': info.get('uploader'),
                    'uploader_id': info.get('uploader_id'),
                    'thumbnail': info.get('thumbnail'),
                    'tags': info.get('tags', []),
                    'video_id': info.get('id'),
                    'webpage_url': info.get('webpage_url'),
                    'extractor': info.get('extractor'),
                    'extractor_key': info.get('extractor_key'),
                    'formats': [{'format_id': f.get('format_id'), 'ext': f.get('ext'), 'quality': f.get('quality')} for f in info.get('formats', [])[:5]],  # 只显示前5个格式
                }
            except Exception as e:
                raise Exception(f"获取视频信息失败: {str(e)}")
    
    def get_subtitles_info(self, url: str) -> Optional[Dict]:
        """
        获取Bilibili视频字幕信息
        
        Args:
            url: Bilibili URL
            
        Returns:
            字幕信息字典或None
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                subtitles = info.get('subtitles', {})
                auto_subtitles = info.get('automatic_captions', {})
                
                # 提取字幕内容
                subtitle_text = None
                subtitle_source = None
                
                # 优先使用人工字幕
                if subtitles:
                    for lang in ['zh-CN', 'zh', 'en']:
                        if lang in subtitles:
                            subtitle_source = f'manual_{lang}'
                            # 这里简化处理，实际中可能需要下载字幕文件
                            break
                
                # 如果没有人工字幕，尝试自动字幕
                if not subtitle_source and auto_subtitles:
                    for lang in ['zh-CN', 'zh', 'en']:
                        if lang in auto_subtitles:
                            subtitle_source = f'auto_{lang}'
                            break
                
                return {
                    'has_subtitles': bool(subtitles or auto_subtitles),
                    'manual_subtitles': list(subtitles.keys()) if subtitles else [],
                    'auto_subtitles': list(auto_subtitles.keys()) if auto_subtitles else [],
                    'subtitle_source': subtitle_source,
                    'subtitle_text': subtitle_text
                }
        except Exception:
            return None
    
    def download_audio(self, url: str) -> str:
        """
        下载Bilibili视频的音频
        
        Args:
            url: Bilibili URL
            
        Returns:
            音频文件路径
        """
        if not self.ffmpeg_available:
            raise Exception("ffmpeg不可用，无法进行音频转换。请安装ffmpeg并确保它在系统PATH中。")
            
        video_id = self.extract_bvid_or_avid(url) or "bilibili_audio"
        audio_path = os.path.join(self.temp_dir, f"{video_id}.wav")
        temp_video_path = None
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.temp_dir, f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                temp_video_path = ydl.prepare_filename(info)
                
                if not os.path.exists(temp_video_path):
                    raise Exception(f"下载的文件不存在: {temp_video_path}")
                
                # 使用ffmpeg转换为WAV格式
                try:
                    (
                        ffmpeg
                        .input(temp_video_path)
                        .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
                        .overwrite_output()
                        .run(quiet=True, capture_stdout=True)
                    )
                except ffmpeg.Error as e:
                    error_msg = f"ffmpeg转换失败: {e.stderr.decode() if e.stderr else str(e)}"
                    raise Exception(error_msg)
                
                if not os.path.exists(audio_path):
                    raise Exception("音频转换后文件不存在")
                
                return audio_path
                
        except Exception as e:
            # 清理可能的临时文件
            for path in [temp_video_path, audio_path]:
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except:
                        pass
            raise Exception(f"音频下载失败: {str(e)}")
        finally:
            # 清理原始下载文件
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except:
                    pass
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        使用Whisper转录音频（原始文本，不添加标点）
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转录文本
        """
        if not self.whisper_model:
            raise Exception("Whisper模型未加载")
            
        try:
            result = self.whisper_model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            raise Exception(f"音频转录失败: {str(e)}")
    
    def transcribe_audio_with_formatting(self, audio_path: str, title: str = "") -> Dict[str, Any]:
        """
        使用Whisper转录音频并进行格式化处理（包含时间戳）
        
        Args:
            audio_path: 音频文件路径
            title: 视频标题（可选）
            
        Returns:
            包含原始和格式化文本的字典，以及时间戳信息
        """
        if not self.whisper_model:
            raise Exception("Whisper模型未加载")
            
        try:
            # 获取原始转录结果，包含时间戳
            print(f"开始Whisper转录，音频文件: {audio_path}")
            
            # 尝试带时间戳的转录，如果失败则使用基本转录
            try:
                result = self.whisper_model.transcribe(audio_path, word_timestamps=True)
                print("使用word_timestamps=True转录成功")
            except Exception as timestamp_error:
                print(f"带时间戳转录失败，使用基本转录: {timestamp_error}")
                result = self.whisper_model.transcribe(audio_path)
                print("使用基本转录成功")
            
            print(f"Whisper转录完成，结果类型: {type(result)}")
            print(f"结果键: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            raw_text = result.get("text", "")
            segments = result.get("segments", [])
            
            print(f"原始文本长度: {len(raw_text)}")
            print(f"段落数量: {len(segments)}")
            print(f"原始文本前100字符: {raw_text[:100] if raw_text else 'Empty'}")
            
            if not raw_text:
                print("警告: Whisper返回的文本为空")
                return {
                    'raw_text': '',
                    'formatted_text': '',
                    'timestamped_text': '',
                    'language': 'unknown',
                    'sentence_count': 0,
                    'word_count': 0,
                    'processing_applied': ['转录失败'],
                    'segments': []
                }
            
            # 使用文本后处理器格式化
            formatted_result = self.text_processor.format_transcript_with_timestamps(
                text=raw_text,
                segments=segments,
                title=title,
                language='auto'
            )
            
            return {
                'raw_text': raw_text,
                'formatted_text': formatted_result['formatted_text'],
                'timestamped_text': formatted_result['timestamped_text'],
                'language': formatted_result['language'],
                'sentence_count': formatted_result['sentence_count'],
                'word_count': formatted_result['word_count'],
                'processing_applied': formatted_result['processing_applied'],
                'segments': segments
            }
        except Exception as e:
            raise Exception(f"音频转录失败: {str(e)}")
    
    def analyze_video(self, url: str, use_whisper: bool = False) -> Dict[str, Any]:
        """
        完整分析Bilibili视频
        
        Args:
            url: Bilibili URL
            use_whisper: 是否使用Whisper进行音频转录
            
        Returns:
            完整的视频分析结果
        """
        video_id = self.extract_bvid_or_avid(url)
        if not video_id:
            raise ValueError("无效的Bilibili URL")
        
        # 获取视频基本信息
        video_info = self.get_video_info(url)
        
        # 获取字幕信息
        subtitle_info = self.get_subtitles_info(url)
        
        transcript = None
        transcript_source = None
        
        # 如果有字幕信息
        if subtitle_info and subtitle_info.get('has_subtitles'):
            transcript = subtitle_info.get('subtitle_text')
            transcript_source = subtitle_info.get('subtitle_source')
        
        # 如果没有字幕且用户要求使用Whisper，则下载音频并转录
        if not transcript and use_whisper:
            if not self.whisper_model:
                print("警告: Whisper模型未加载，跳过音频转录")
            elif not self.ffmpeg_available:
                print("警告: ffmpeg不可用，跳过音频转录")
            else:
                try:
                    audio_path = self.download_audio(url)
                    transcript = self.transcribe_audio(audio_path)
                    transcript_source = 'whisper'
                    
                    # 清理临时文件
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                        
                except Exception as e:
                    print(f"Whisper转录失败: {str(e)}")
        
        return {
            'video_info': video_info,
            'subtitle_info': subtitle_info,
            'transcript': transcript,
            'has_transcript': transcript is not None,
            'transcript_source': transcript_source
        }
    
    def analyze_video_with_formatting(self, url: str, use_whisper: bool = False) -> Dict[str, Any]:
        """
        完整分析Bilibili视频，包含格式化的转录文本
        
        Args:
            url: Bilibili URL
            use_whisper: 是否使用Whisper进行音频转录
            
        Returns:
            完整的视频分析结果，包含格式化文本
        """
        video_id = self.extract_bvid_or_avid(url)
        if not video_id:
            raise ValueError("无效的Bilibili URL")
        
        # 获取视频基本信息
        video_info = self.get_video_info(url)
        video_title = video_info.get('title', '') if video_info else ''
        
        # 获取字幕信息
        subtitle_info = self.get_subtitles_info(url)
        
        transcript_data = None
        transcript_source = None
        
        # 如果有字幕信息
        if subtitle_info and subtitle_info.get('has_subtitles'):
            raw_transcript = subtitle_info.get('subtitle_text')
            if raw_transcript:
                # 格式化现有字幕
                formatted_result = self.text_processor.format_transcript(
                    text=raw_transcript,
                    title=video_title,
                    language='auto'
                )
                transcript_data = {
                    'raw_text': raw_transcript,
                    'formatted_text': formatted_result['formatted_text'],
                    'language': formatted_result['language'],
                    'sentence_count': formatted_result['sentence_count'],
                    'word_count': formatted_result['word_count'],
                    'processing_applied': formatted_result['processing_applied']
                }
                transcript_source = subtitle_info.get('subtitle_source')
        
        # 如果没有字幕且用户要求使用Whisper，则下载音频并转录
        if not transcript_data and use_whisper:
            if not self.whisper_model:
                print("警告: Whisper模型未加载，跳过音频转录")
            elif not self.ffmpeg_available:
                print("警告: ffmpeg不可用，跳过音频转录")
            else:
                try:
                    audio_path = self.download_audio(url)
                    transcript_data = self.transcribe_audio_with_formatting(audio_path, video_title)
                    transcript_source = 'whisper'
                    
                    # 清理临时文件
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                        
                except Exception as e:
                    print(f"Whisper转录失败: {str(e)}")
        
        return {
            'video_info': video_info,
            'subtitle_info': subtitle_info,
            'transcript_data': transcript_data,
            'has_transcript': transcript_data is not None,
            'transcript_source': transcript_source
        }
    
    def cleanup(self):
        """清理临时文件"""
        try:
            for file in os.listdir(self.temp_dir):
                if file.endswith(('.wav', '.mp4', '.flv', '.m4a')) and ('bilibili' in file or 'BV' in file or 'av' in file):
                    file_path = os.path.join(self.temp_dir, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
        except Exception:
            pass


# 使用示例
if __name__ == "__main__":
    analyzer = BilibiliAnalyzer()
    
    # 测试URL
    test_url = "https://www.bilibili.com/video/BV1xx411c7mu"  # 示例B站视频
    
    try:
        result = analyzer.analyze_video(test_url, use_whisper=False)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"分析失败: {str(e)}")
    finally:
        analyzer.cleanup()