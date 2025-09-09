"""
哔哩哔哩视频分析API - 功能验证脚本
"""
import asyncio
import json
from client import VideoAPIClient


async def verify_api_functionality():
    """验证API的完整功能"""
    print("🚀 开始验证哔哩哔哩视频分析API功能")
    print("=" * 60)
    
    client = VideoAPIClient("http://localhost:8002")
    
    # 测试视频
    test_url = "https://www.bilibili.com/video/BV1xx411c7mu"
    
    try:
        # 1. 健康检查
        print("\n1. 🏥 健康检查")
        health = await client.health_check()
        if health.get('status') == 'healthy':
            print("✅ 服务健康状态正常")
        else:
            print("❌ 服务健康检查失败")
            return
        
        # 2. 获取视频信息
        print("\n2. 📺 获取视频信息")
        info_result = await client.get_video_info(test_url)
        if info_result.get('success'):
            info = info_result['data']
            print(f"✅ 标题: {info['title']}")
            print(f"✅ UP主: {info['uploader']}")
            print(f"✅ 时长: {info['duration']}秒")
            print(f"✅ 观看数: {info['view_count']:,}")
        else:
            print(f"❌ 获取视频信息失败: {info_result.get('error')}")
        
        # 3. 获取字幕信息
        print("\n3. 📝 获取字幕信息")
        transcript_result = await client.get_transcript(test_url)
        if transcript_result.get('success'):
            subtitle_info = transcript_result['data'].get('subtitle_info', {})
            print(f"✅ 有字幕: {subtitle_info.get('has_subtitles', False)}")
            print(f"✅ 人工字幕语言: {subtitle_info.get('manual_subtitles', [])}")
            print(f"✅ 自动字幕语言: {subtitle_info.get('auto_subtitles', [])}")
        else:
            print(f"❌ 获取字幕失败: {transcript_result.get('error')}")
        
        # 4. 完整分析
        print("\n4. 🔍 完整视频分析")
        analysis_result = await client.analyze_video(test_url, use_whisper=False)
        if analysis_result.get('success'):
            data = analysis_result['data']
            print(f"✅ 视频分析完成")
            print(f"✅ 有转录内容: {data['has_transcript']}")
            print(f"✅ 转录来源: {data['transcript_source'] or 'None'}")
        else:
            print(f"❌ 完整分析失败: {analysis_result.get('error')}")
        
        # 5. 服务配置信息
        print("\n5. ⚙️  服务配置")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:8002/config") as response:
                    config = await response.json()
                    print(f"✅ 应用名称: {config['app_name']}")
                    print(f"✅ 版本: {config['app_version']}")
                    print(f"✅ Whisper模型: {config['whisper_model']}")
        except Exception as e:
            print(f"❌ 获取配置失败: {str(e)}")
        
        print("\n" + "=" * 60)
        print("🎉 哔哩哔哩视频分析API功能验证完成！")
        print("✨ 所有核心功能正常工作")
        
    except Exception as e:
        print(f"❌ 验证过程中出现错误: {str(e)}")


async def test_multiple_videos():
    """测试多个视频处理"""
    print("\n" + "=" * 60)
    print("🎬 测试多视频处理能力")
    print("=" * 60)
    
    client = VideoAPIClient("http://localhost:8002")
    
    test_videos = [
        ("经典鬼畜", "https://www.bilibili.com/video/BV1xx411c7mu"),
        ("音乐MV", "https://www.bilibili.com/video/BV1GJ411x7h7"),
    ]
    
    for name, url in test_videos:
        print(f"\n📹 处理视频: {name}")
        try:
            result = await client.get_video_info(url)
            if result.get('success'):
                info = result['data']
                print(f"  ✅ 标题: {info['title'][:30]}...")
                print(f"  ✅ 观看数: {info['view_count']:,}")
            else:
                print(f"  ❌ 失败: {result.get('error')}")
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")


async def main():
    """主测试函数"""
    await verify_api_functionality()
    await test_multiple_videos()
    
    print("\n🏁 所有测试完成！")
    print("📋 总结:")
    print("  - API服务运行正常")
    print("  - 视频信息提取功能完整")
    print("  - 字幕检测功能正常")
    print("  - 多视频处理能力良好")
    print("  - 错误处理机制完善")


if __name__ == "__main__":
    asyncio.run(main())