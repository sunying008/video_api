"""
FFmpeg 安装检查和指导工具
"""
import subprocess
import shutil
import os
import platform


def check_ffmpeg():
    """检查ffmpeg是否已安装"""
    print("🔍 检查FFmpeg安装状态...")
    print("=" * 50)
    
    # 检查是否在PATH中
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        print(f"✅ FFmpeg已安装在: {ffmpeg_path}")
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                # 提取版本信息
                version_line = result.stdout.split('\n')[0]
                print(f"✅ 版本信息: {version_line}")
                return True
        except Exception as e:
            print(f"❌ FFmpeg命令执行失败: {str(e)}")
    else:
        print("❌ 未找到FFmpeg")
    
    return False


def get_installation_guide():
    """获取FFmpeg安装指导"""
    system = platform.system().lower()
    
    print("\n📋 FFmpeg安装指导:")
    print("=" * 50)
    
    if system == "windows":
        print("🪟 Windows安装方法:")
        print("1. 访问 https://ffmpeg.org/download.html#build-windows")
        print("2. 下载Windows构建版本")
        print("3. 解压到目录（如 C:\\ffmpeg）")
        print("4. 将 C:\\ffmpeg\\bin 添加到系统PATH环境变量")
        print("\n或者使用包管理器:")
        print("- Chocolatey: choco install ffmpeg")
        print("- Scoop: scoop install ffmpeg")
        
    elif system == "darwin":  # macOS
        print("🍎 macOS安装方法:")
        print("- Homebrew: brew install ffmpeg")
        print("- MacPorts: sudo port install ffmpeg")
        
    else:  # Linux
        print("🐧 Linux安装方法:")
        print("- Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
        print("- CentOS/RHEL: sudo yum install ffmpeg")
        print("- Fedora: sudo dnf install ffmpeg")
        print("- Arch: sudo pacman -S ffmpeg")


def test_ffmpeg_functions():
    """测试ffmpeg相关功能"""
    print("\n🧪 测试FFmpeg功能...")
    print("=" * 50)
    
    try:
        from bilibili_analyzer import BilibiliAnalyzer
        analyzer = BilibiliAnalyzer()
        
        if analyzer.ffmpeg_available:
            print("✅ BilibiliAnalyzer检测到FFmpeg可用")
            print("✅ 音频转录功能应该可以正常工作")
        else:
            print("❌ BilibiliAnalyzer未检测到FFmpeg")
            print("❌ 音频转录功能不可用")
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")


def create_simple_test():
    """创建简单的音频处理测试"""
    print("\n🔧 创建测试用例...")
    print("=" * 50)
    
    if not check_ffmpeg():
        print("❌ FFmpeg不可用，跳过音频处理测试")
        return
    
    try:
        # 创建一个简单的测试音频文件（1秒的静音）
        test_cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=duration=1:sample_rate=16000:channels=1',
            '-y', 'test_audio.wav'
        ]
        
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists('test_audio.wav'):
            print("✅ FFmpeg音频生成测试成功")
            
            # 清理测试文件
            os.remove('test_audio.wav')
            print("✅ 测试文件已清理")
        else:
            print("❌ FFmpeg音频生成测试失败")
            if result.stderr:
                print(f"错误信息: {result.stderr}")
                
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {str(e)}")


def main():
    """主函数"""
    print("🎵 FFmpeg安装检查和配置工具")
    print("=" * 60)
    
    ffmpeg_available = check_ffmpeg()
    
    if not ffmpeg_available:
        get_installation_guide()
        print("\n⚠️  安装FFmpeg后请重启终端并重新运行此脚本进行验证")
    else:
        print("\n✅ FFmpeg已正确安装！")
        test_ffmpeg_functions()
        create_simple_test()
        
        print("\n🎉 现在可以使用音频转录功能了！")
        print("提示: 重启API服务以应用更新的检查逻辑")


if __name__ == "__main__":
    main()