import os
import tempfile
import json
import asyncio
from typing import Optional, Dict, Any, List
import yt_dlp
import whisper
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import ffmpeg
import re
from urllib.parse import urlparse, parse_qs


class YouTubeAnalyzer:
    """YouTube视频内容分析器"""
    
    def __init__(self, whisper_model_name: str = "base"):
        """
        初始化YouTube分析器
        
        Args:
            whisper_model_name: Whisper模型名称 (tiny, base, small, medium, large)
        """
        self.whisper_model = whisper.load_model(whisper_model_name)
        self.temp_dir = tempfile.gettempdir()
        
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        从YouTube URL中提取视频ID
        
        Args:
            url: YouTube URL
            
        Returns:
            视频ID或None
        """
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        获取YouTube视频基本信息
        
        Args:
            url: YouTube URL
            
        Returns:
            视频信息字典
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
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
                    'categories': info.get('categories', []),
                    'video_id': info.get('id'),
                    'webpage_url': info.get('webpage_url'),
                    'language': info.get('language'),
                    'subtitles': list(info.get('subtitles', {}).keys()) if info.get('subtitles') else [],
                    'automatic_captions': list(info.get('automatic_captions', {}).keys()) if info.get('automatic_captions') else []
                }
            except Exception as e:
                raise Exception(f"获取视频信息失败: {str(e)}")
    
    def get_transcript_from_api(self, video_id: str, languages: List[str] = ['zh', 'en']) -> Optional[str]:
        """
        通过YouTube Transcript API获取字幕
        
        Args:
            video_id: YouTube视频ID
            languages: 优先语言列表
            
        Returns:
            字幕文本或None
        """
        try:
            # 尝试获取指定语言的字幕
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    transcript_data = transcript.fetch()
                    return '\n'.join([entry['text'] for entry in transcript_data])
                except NoTranscriptFound:
                    continue
            
            # 如果没有找到指定语言的字幕，尝试获取任何可用的字幕
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
                transcript_data = transcript.fetch()
                return '\n'.join([entry['text'] for entry in transcript_data])
            except NoTranscriptFound:
                pass
                
        except (TranscriptsDisabled, NoTranscriptFound, Exception):
            pass
        
        return None
    
    def download_audio(self, url: str) -> str:
        """
        下载YouTube视频的音频
        
        Args:
            url: YouTube URL
            
        Returns:
            音频文件路径
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError("无效的YouTube URL")
        
        audio_path = os.path.join(self.temp_dir, f"{video_id}.wav")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(self.temp_dir, f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)
                
                # 转换为WAV格式
                (
                    ffmpeg
                    .input(downloaded_file)
                    .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
                    .overwrite_output()
                    .run(quiet=True)
                )
                
                # 删除原始下载文件
                if os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
                
                return audio_path
                
        except Exception as e:
            raise Exception(f"音频下载失败: {str(e)}")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """
        使用Whisper转录音频
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            转录文本
        """
        try:
            result = self.whisper_model.transcribe(audio_path)
            return result["text"]
        except Exception as e:
            raise Exception(f"音频转录失败: {str(e)}")
    
    def analyze_video(self, url: str, use_whisper: bool = False) -> Dict[str, Any]:
        """
        完整分析YouTube视频
        
        Args:
            url: YouTube URL
            use_whisper: 是否使用Whisper进行音频转录
            
        Returns:
            完整的视频分析结果
        """
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError("无效的YouTube URL")
        
        # 获取视频基本信息
        video_info = self.get_video_info(url)
        
        # 尝试获取字幕
        transcript = self.get_transcript_from_api(video_id)
        
        # 如果没有字幕且用户要求使用Whisper，则下载音频并转录
        if not transcript and use_whisper:
            try:
                audio_path = self.download_audio(url)
                transcript = self.transcribe_audio(audio_path)
                
                # 清理临时文件
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    
            except Exception as e:
                print(f"Whisper转录失败: {str(e)}")
        
        return {
            'video_info': video_info,
            'transcript': transcript,
            'has_transcript': transcript is not None,
            'transcript_source': 'youtube_api' if transcript and not use_whisper else ('whisper' if transcript else None)
        }
    
    def cleanup(self):
        """清理临时文件"""
        try:
            for file in os.listdir(self.temp_dir):
                if file.endswith(('.wav', '.mp4', '.webm', '.m4a')):
                    file_path = os.path.join(self.temp_dir, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
        except Exception:
            pass


# 使用示例
if __name__ == "__main__":
    analyzer = YouTubeAnalyzer()
    
    # 测试URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    try:
        result = analyzer.analyze_video(test_url, use_whisper=False)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"分析失败: {str(e)}")
    finally:
        analyzer.cleanup()