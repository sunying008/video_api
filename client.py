import asyncio
import aiohttp
import json
from typing import Dict, Any

class VideoAPIClient:
    """哔哩哔哩视频分析API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        self.base_url = base_url.rstrip('/')
        
    async def analyze_video(self, url: str, use_whisper: bool = False) -> Dict[str, Any]:
        """
        完整分析哔哩哔哩视频
        
        Args:
            url: 哔哩哔哩视频URL
            use_whisper: 是否使用Whisper进行音频转录
            
        Returns:
            分析结果
        """
        async with aiohttp.ClientSession() as session:
            data = {
                "url": url,
                "use_whisper": use_whisper
            }
            async with session.post(f"{self.base_url}/analyze", json=data) as response:
                return await response.json()
    
    async def get_video_info(self, url: str) -> Dict[str, Any]:
        """
        获取视频基本信息
        
        Args:
            url: 哔哩哔哩视频URL
            
        Returns:
            视频信息
        """
        async with aiohttp.ClientSession() as session:
            params = {"url": url}
            async with session.get(f"{self.base_url}/info", params=params) as response:
                return await response.json()
    
    async def get_transcript(self, url: str) -> Dict[str, Any]:
        """
        获取视频字幕
        
        Args:
            url: 哔哩哔哩视频URL
            
        Returns:
            字幕内容
        """
        async with aiohttp.ClientSession() as session:
            params = {"url": url}
            async with session.get(f"{self.base_url}/transcript", params=params) as response:
                return await response.json()
    
    async def transcribe_audio(self, url: str) -> Dict[str, Any]:
        """
        使用Whisper转录视频音频
        
        Args:
            url: 哔哩哔哩视频URL
            
        Returns:
            转录结果
        """
        async with aiohttp.ClientSession() as session:
            data = {"url": url}
            async with session.post(f"{self.base_url}/transcribe", json=data) as response:
                return await response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as response:
                return await response.json()


# 使用示例
async def main():
    client = VideoAPIClient()
    
    # 测试URL - 哔哩哔哩视频
    test_url = "https://www.bilibili.com/video/BV1xx411c7mu"
    
    try:
        # 健康检查
        health = await client.health_check()
        print("健康检查:", health)
        
        # 获取视频信息
        info = await client.get_video_info(test_url)
        print("视频信息:", json.dumps(info, indent=2, ensure_ascii=False))
        
        # 获取字幕
        transcript = await client.get_transcript(test_url)
        print("字幕:", json.dumps(transcript, indent=2, ensure_ascii=False))
        
        # 完整分析
        analysis = await client.analyze_video(test_url, use_whisper=False)
        print("完整分析:", json.dumps(analysis, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"客户端测试失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())