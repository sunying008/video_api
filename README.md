# 哔哩哔哩视频内容解析API服务

这是一个基于FastAPI的哔哩哔哩视频内容解析服务，能够提取视频信息、获取字幕、并使用Whisper进行音频转录。支持**智能断句**、**自动标点**和**时间戳标注**功能。

## ✨ 功能特性

- 🎥 **视频信息提取**: 获取哔哩哔哩视频的元数据（标题、描述、时长、观看数等）
- 📝 **字幕获取**: 自动获取哔哩哔哩官方字幕或自动生成的字幕
- 🎙️ **智能音频转录**: 使用OpenAI Whisper模型进行音频内容转录
- 📍 **时间戳标注**: 为每个句子自动添加时间戳（格式：`[时:分:秒]`）
- ✂️ **智能断句**: 基于语义自动断句，支持中英文混合内容
- 📖 **自动标点**: 智能添加标点符号（句号、问号、感叹号）
- 🌍 **多语言支持**: 自动检测语言并应用相应的处理规则
- 🚀 **RESTful API**: 提供完整的REST API接口
- ⚡ **异步处理**: 支持异步请求处理，提高并发性能
- 📊 **健康监控**: 提供健康检查和日志记录

## 🔧 环境设置与安装

### 系统要求
- Python 3.8+
- FFmpeg (音频处理)
- 足够的磁盘空间用于临时音频文件

### FFmpeg 安装

**Windows:**
```bash
# 使用 winget 安装
winget install ffmpeg

# 或手动下载并添加到PATH环境变量
# https://ffmpeg.org/download.html#build-windows
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd video_api

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖包
pip install -r requirements.txt
```

### 环境变量配置 (可选)

创建 `.env` 文件:
```env
# Whisper模型配置
DEFAULT_WHISPER_MODEL=base
WHISPER_DEVICE=cpu

# API配置
API_HOST=0.0.0.0
API_PORT=8002

# 日志级别
LOG_LEVEL=INFO
```

## 快速开始

### 启动服务

```bash
python app.py
```

服务将在 `http://localhost:8002` 启动。

### API文档

启动服务后，访问以下地址查看完整的API文档：
- Swagger UI: `http://localhost:8002/docs`
- ReDoc: `http://localhost:8002/redoc`

## API端点

### 1. 根端点
```http
GET /
```
返回服务信息和可用端点列表。

### 2. 健康检查
```http
GET /health
```
检查服务状态。

### 3. 获取视频信息
```http
GET /info?url={bilibili_url}
```
获取哔哩哔哩视频的基本信息。

### 4. 获取字幕
```http
GET /transcript?url={bilibili_url}
```
获取哔哩哔哩视频的字幕内容。

### 5. 完整分析（原始格式）
```http
POST /analyze
Content-Type: application/json

{
    "url": "https://www.bilibili.com/video/BV1xx411c7mu",
    "use_whisper": false
}
```
进行完整的视频分析，包括基本信息和字幕（原始格式，无格式化处理）。

### 6. 完整分析（格式化版本）🆕
```http
POST /analyze-formatted
Content-Type: application/json

{
    "url": "https://www.bilibili.com/video/BV1xx411c7mu",
    "use_whisper": true
}
```
进行完整的视频分析，返回格式化的转录文本（带标点、断句和时间戳）。

### 7. 音频转录（智能格式化）⭐
```http
POST /transcribe
Content-Type: application/json

{
    "url": "https://www.bilibili.com/video/BV1xx411c7mu",
    "use_whisper": true,
    "enable_formatting": true
}
```

**请求参数**：
- `url`: 哔哩哔哩视频URL（必填）
- `use_whisper`: 是否使用Whisper转录（默认：false）
- `enable_formatting`: 是否启用格式化功能（默认：true）

**响应格式**：
```json
{
    "success": true,
    "data": {
        "transcript": "《视频标题》\n[00:00:00] 大家好，今天我们来学习人工智能。\n[00:00:05] 首先了解机器学习的基本概念。",
        "raw_text": "大家好今天我们来学习人工智能首先了解机器学习的基本概念",
        "formatted_text": "大家好，今天我们来学习人工智能。\n首先了解机器学习的基本概念。",
        "timestamped_text": "[00:00:00] 大家好，今天我们来学习人工智能。\n[00:00:05] 首先了解机器学习的基本概念。",
        "language": "zh",
        "sentence_count": 2,
        "word_count": 28,
        "processing_applied": ["添加标点符号", "添加时间戳", "添加标题"],
        "source": "whisper",
        "formatted": true
    }
}
```

## 🚀 使用示例

### Python客户端

```python
import asyncio
from client import VideoAPIClient

async def main():
    client = VideoAPIClient("http://localhost:8002")
    
    # 智能格式化转录（推荐）
    result = await client.transcribe_audio_formatted(
        "https://www.bilibili.com/video/BV1xx411c7mu"
    )
    print("转录文本（带时间戳）:", result['timestamped_text'])
    print("原始文本:", result['raw_text'])
    
    # 完整分析
    result = await client.analyze_video(
        "https://www.bilibili.com/video/BV1xx411c7mu",
        use_whisper=True
    )
    print(result)

asyncio.run(main())
```

### cURL示例

```bash
# 获取视频信息
curl "http://localhost:8002/info?url=https://www.bilibili.com/video/BV1xx411c7mu"

# 智能转录（带时间戳和标点）
curl -X POST "http://localhost:8002/transcribe" \
     -H "Content-Type: application/json" \
     -d '{
         "url": "https://www.bilibili.com/video/BV1xx411c7mu",
         "use_whisper": true,
         "enable_formatting": true
     }'

# 格式化分析
curl -X POST "http://localhost:8002/analyze-formatted" \
     -H "Content-Type: application/json" \
     -d '{
         "url": "https://www.bilibili.com/video/BV1xx411c7mu",
         "use_whisper": true
     }'
```

## ⚙️ 配置选项

### Whisper模型

在 `config.py` 中可以配置Whisper模型：
- `tiny`: 最快，准确度最低（39 MB）
- `base`: 默认，平衡速度和准确度（74 MB）
- `small`: 较好的准确度（244 MB）
- `medium`: 更好的准确度（769 MB）
- `large`: 最高准确度，最慢（1550 MB）

### 文本处理配置

支持的语言检测和处理：
- **中文**: 智能分句（基于"然后"、"所以"、"但是"等连接词）
- **英文**: 智能分句（基于"then"、"so"、"however"等连接词）
- **自动检测**: 根据文本内容自动选择处理规则

### 时间戳格式

时间戳格式为 `[HH:MM:SS]`，例如：
- `[00:00:00]` - 开始
- `[00:01:30]` - 1分30秒
- `[01:23:45]` - 1小时23分45秒

### 日志配置

日志文件按日期命名，格式为 `logs/video_api_YYYYMMDD.log`，支持UTF-8编码。

## 错误处理

API返回统一的错误格式：
```json
{
    "success": false,
    "error": "错误描述信息"
}
```

## 性能优化

1. **缓存**: 可以考虑添加Redis缓存来存储视频信息
2. **队列**: 对于大批量处理，可以使用Celery等任务队列
3. **并发**: 调整uvicorn的worker数量来处理更多并发请求

## 🧪 测试

运行不同类型的测试：

```bash
# 测试文本格式化功能
python test_formatting.py

# 测试中文分句功能  
python test_chinese_split.py

# 测试改进的格式化功能
python test_improved_formatting.py

# 测试API端点
python test_api_fix.py

# 完整功能测试
pytest test_video_api.py -v
```

## 📋 更新日志

### v2.0.0 (2025-09-09)
- ✅ **智能文本处理**: 新增断句功能，支持中英文智能分割
- ✅ **标点符号增强**: 自动添加适当的标点符号
- ✅ **时间戳注释**: 为每个句子添加播放时间标记 `[时:分:秒]`
- ✅ **API功能扩展**: 新增 `/analyze-formatted` 专用端点
- ✅ **转录接口增强**: `/transcribe` 端点支持格式化选项控制
- ✅ **算法优化**: 改进中文分句算法，提高准确率
- ✅ **编码修复**: 解决UTF-8中文字符处理问题
- ✅ **日志改进**: 增强错误处理和调试日志记录

### v1.0.0 
- ✅ **基础功能**: 视频信息提取和字幕获取
- ✅ **音频转录**: Whisper音频转文本功能
- ✅ **API服务**: RESTful API接口框架

## 📦 项目架构

```
video_api/
├── 🚀 app.py                    # FastAPI主程序和API路由定义
├── 📺 bilibili_analyzer.py      # B站视频解析和音频处理引擎  
├── 📝 text_processor.py         # 智能文本格式化和时间戳处理器
├── 📋 requirements.txt          # 项目依赖包配置
├── 📖 README.md                # 完整项目文档
├── 🧪 test_app.py              # API接口测试脚本
├── ⚙️ .env                     # 环境配置文件 (可选)
└── 📁 log/                     # 日志系统目录
    ├── app.log                 # 应用运行日志
    └── transcription.log       # 转录处理详细日志
```

### 🏗️ 核心模块说明

- **app.py**: 
  - FastAPI应用程序入口
  - 定义所有API端点和请求处理逻辑
  - 集成健康检查和错误处理

- **bilibili_analyzer.py**: 
  - 哔哩哔哩视频URL解析和验证
  - 音频文件提取和临时文件管理
  - Whisper模型集成和转录处理

- **text_processor.py**: 
  - 智能中英文句子分割算法
  - 自动标点符号识别和添加
  - 时间戳格式化和句子对齐

## ⚠️ 注意事项

1. **依赖要求**: 需要安装ffmpeg用于音频处理
2. **性能考虑**: Whisper转录需要下载音频文件，会消耗时间和存储空间
3. **API限制**: 哔哩哔哩的API使用策略可能会发生变化，需要定期更新
4. **版权合规**: 请遵守哔哩哔哩的使用条款和版权规定
5. **生产部署**: 建议在生产环境中添加速率限制和用户认证
6. **模型选择**: 根据准确度和速度需求选择合适的Whisper模型
7. **存储空间**: 确保有足够的临时存储空间用于音频文件处理

## 🎯 最佳实践

1. **推荐使用 `/transcribe` 端点**进行音频转录，默认启用格式化功能
2. **短视频(＜10分钟)**使用`tiny`或`base`模型，**长视频**使用`small`或`medium`模型  
3. **中文内容**的断句效果优于英文，建议针对具体场景调试参数
4. **时间戳精度**取决于Whisper的segment分割，可能存在±2秒的偏差
5. **批量处理**时建议添加适当的延时(500ms+)，避免触发哔哩哔哩API限制
6. **生产环境**建议配置日志轮转和磁盘空间监控
7. **模型选择**平衡表：
   - `tiny`: 速度最快，准确率较低，适合快速预览
   - `base`: 速度快，准确率中等，推荐日常使用  
   - `small`: 速度中等，准确率较高，适合重要内容
   - `medium`: 速度慢，准确率最高，适合专业用途

## 🔍 故障排查

### 常见问题及解决方案

**1. FFmpeg未找到错误**
```bash
# 确认FFmpeg安装并在PATH中
ffmpeg -version
```

**2. 音频提取失败**
- 检查视频URL是否有效
- 确认网络连接稳定
- 尝试较短的视频进行测试

**3. Whisper转录错误**
```python
# 检查可用模型
import whisper
print(whisper.available_models())
```

**4. 中文分句效果不佳**
- 确认安装了jieba分词库
- 尝试调整`min_sentence_length`参数
- 检查输入文本是否包含特殊字符

**5. API响应超时**
- 增加请求超时时间
- 使用较小的Whisper模型
- 分段处理长视频

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目：

1. Fork项目到您的GitHub
2. 创建feature分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add some amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 提交Pull Request

### 开发环境设置
```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8

# 运行代码格式化
black .

# 运行测试
pytest
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 技术支持

如果您遇到问题或有功能建议：

- 🐛 **Bug报告**: 请在GitHub Issues中详细描述问题
- 💡 **功能请求**: 欢迎提交新功能建议
- 📧 **技术咨询**: 发送邮件至项目维护者
- 💬 **社区讨论**: 加入项目讨论组

---

**⭐ 如果这个项目对您有帮助，请给个Star支持我们！**

## 许可证

本项目采用MIT许可证。