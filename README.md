# 🎬 爆款短视频拆解工具

本地部署的短视频分析工具，帮助你系统化拆解爆款视频，沉淀创作方法论，并利用 AI 快速复刻到自己的产品。

---

## ✨ 功能模块

| 模块 | 功能 | 技术 |
|------|------|------|
| 📸 **镜头拆解** | 自动识别转场、提取封面与关键帧 | OpenCV 帧差检测 |
| 🎙️ **分镜脚本** | 语音转文字，精准匹配到对应镜头 | OpenAI Whisper |
| 🧠 **脚本结构分析** | 三段论打标（Hook→Body→CTA） | Claude API |
| 🤖 **AI 视频生成** | 根据拆解结构 + 新产品信息生成复刻方案 | Claude API + 即梦 AI |
| 📊 **复刻方案报告** | 生成完整的 HTML/MD 分析报告 | 内置报告引擎 |
| 📚 **素材库** | SQLite 持久化管理所有拆解结果 | SQLite + 标签系统 |

---

## 🚀 快速启动

### 前置要求
- Python 3.9+
- ffmpeg（视频处理必须）
- Anthropic API Key（结构分析 + AI 生成必须）

### 一键启动

```bash
# 1. 克隆或下载项目
cd video-analysis-tool

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 Anthropic API Key

# 3. 启动（自动安装依赖）
chmod +x start.sh
./start.sh
```

### 手动安装

```bash
# 安装 ffmpeg
# macOS
brew install ffmpeg
# Ubuntu
sudo apt-get install ffmpeg

# 安装 Python 依赖
pip install -r requirements.txt

# 启动
streamlit run app.py
```

浏览器打开 **http://localhost:8501**

---

## 📁 项目结构

```
video-analysis-tool/
├── app.py                      # 主入口 (Streamlit UI)
├── requirements.txt
├── start.sh                    # 一键启动脚本
├── .env.example                # 环境变量模板
│
├── modules/
│   ├── shot_breakdown.py       # 模块1: 镜头拆解
│   ├── storyboard.py           # 模块2: 分镜脚本
│   ├── script_analysis.py      # 模块3: 脚本结构分析 (Claude)
│   ├── ai_generation.py        # 模块4: AI 视频生成
│   └── report_generator.py     # 模块5: 复刻方案报告
│
├── database/
│   └── material_db.py          # 素材库 (SQLite)
│
├── static/                     # 生成的图片/报告
├── uploads/                    # 上传的视频
└── data/
    └── material_library.db     # 素材库数据文件
```

---

## 🧠 三段论框架说明

工具基于短视频"三段论"框架进行结构分析：

```
┌─────────────────────────────────────────────────────┐
│  🎣 Hook（钩子）— 前 3-5 秒                          │
│  目标：抓住注意力，防止划走                             │
│  类型：痛点型 / 悬念型 / 反常识型 / 福利型 / 共情型     │
├─────────────────────────────────────────────────────┤
│  📦 Body（内容主体）— 中间段                          │
│  目标：交付价值，维持观看，建立信任                     │
│  类型：干货列举 / 故事叙述 / 对比呈现 / 演示教学         │
├─────────────────────────────────────────────────────┤
│  📢 CTA（行动号召）— 最后 3-5 秒                      │
│  目标：引导关注/互动/购买                               │
│  类型：关注型 / 互动型 / 收藏型 / 购买型                │
└─────────────────────────────────────────────────────┘
```

---

## ⚙️ 环境变量配置

| 变量 | 说明 | 必填 |
|------|------|------|
| `ANTHROPIC_API_KEY` | Claude API Key | ✅ |
| `JIMENG_API_KEY` | 即梦 AI Key（视频生成） | ❌ |
| `WHISPER_MODEL` | 模型大小 (tiny/base/small/medium/large) | ❌ |

---

## 💡 使用流程

1. **上传视频** → 支持 MP4/MOV/AVI，建议 1-5 分钟短视频
2. **镜头拆解** → 自动检测转场，提取所有关键帧
3. **分镜脚本** → Whisper 转写语音，自动对应到每个镜头
4. **结构分析** → Claude 分析三段论结构，识别爆款要素
5. **AI 生成** → 输入你的产品信息，AI 生成复刻脚本+分镜提示词
6. **下载报告** → 获取完整的 HTML 可视化报告，保存到素材库

---

## 🔧 常见问题

**Q: Whisper 下载太慢？**
A: 使用 `tiny` 或 `base` 模型，或配置镜像源。中文推荐 `medium` 效果更好。

**Q: 镜头检测太多/太少？**
A: 在侧边栏调整「场景切换阈值」，值越小越敏感（检测更多切换）。

**Q: 即梦 API 如何获取？**
A: 访问 [即梦 AI 开放平台](https://platform.jimeng.com) 申请。不配置则只生成提示词。
