# 🎬 爆款短视频拆解工具 v2.0

本地部署的短视频分析工具。深色主题，Next.js + FastAPI 架构，帮你系统化拆解爆款视频，沉淀创作方法论，并利用 AI 快速复刻到自己的产品。

---

## ✨ 功能模块

| 模块 | 功能 | 技术 |
|------|------|------|
| 📸 **镜头拆解** | 自动识别转场、横向滚动镜头时间线、颜色分类 | OpenCV 帧差检测 |
| 📊 **数据指标分析** | 产品首次出现时间、露出时长、露出占比 | 自动计算 |
| 🎙️ **分镜脚本** | 语音转文字，精准匹配到对应镜头截图，可导出 | OpenAI Whisper |
| 🧠 **脚本结构分析** | 三段论打标（Hook→Body→CTA），跨品类改编面板 | Claude API |
| 🤖 **AI 视频生成** | 生成分镜提示词，支持 Kie.ai/即梦 AI 接口 | Claude + Kie.ai |
| 📊 **复刻方案报告** | 生成 HTML/MD 报告，一键保存到素材库 | 内置引擎 |

---

## 🚀 快速启动

### 前置要求
- Python 3.9+
- Node.js 18+
- ffmpeg

### 一键启动

```bash
# 1. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

# 2. 启动（自动安装依赖）
chmod +x start.sh
./start.sh
```

浏览器打开 **http://localhost:3000**

### 分开启动（调试）

```bash
# 终端1：后端
./start_backend.sh    # http://localhost:8000

# 终端2：前端
./start_frontend.sh   # http://localhost:3000
```

---

## 📁 项目结构

```
video-analysis-tool/
├── backend/
│   └── main.py                 # FastAPI 后端 API
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # 上传页（深色主题）
│   │   └── analysis/[id]/      # 分析结果页
│   ├── components/
│   │   ├── ShotGrid.tsx        # 镜头截图网格 + 时间线
│   │   ├── StoryboardTab.tsx   # 分镜脚本表格
│   │   ├── ScriptAnalysisTab.tsx # 结构分析 + 跨品类改编
│   │   └── AIGenerationTab.tsx # AI 视频生成
│   └── lib/api.ts              # API 客户端
├── modules/                    # Python 处理模块
│   ├── shot_breakdown.py       # 镜头拆解
│   ├── storyboard.py           # 分镜脚本
│   ├── script_analysis.py      # Claude 结构分析
│   ├── ai_generation.py        # AI 视频生成
│   └── report_generator.py     # 报告生成
├── database/
│   └── material_db.py          # SQLite 素材库
├── start.sh                    # 一键启动（前端+后端）
├── start_backend.sh
└── start_frontend.sh
```

---

## 📊 数据指标说明

| 指标 | 说明 | 建议值 |
|------|------|--------|
| 产品首次出现 | 产品首帧出现时间 | ≤ 5秒 |
| 产品露出时长 | 产品镜头总时长 | 越长越好 |
| 产品露出占比 | 产品镜头 / 视频总时长 | ≥ 30% (高转化 ≥ 40%) |
| 视频总时长 | 全片时长 | 15-60 秒 |

---

## ⚙️ 环境变量

```env
ANTHROPIC_API_KEY=your_key_here    # Claude 结构分析必须
JIMENG_API_KEY=                    # 即梦 AI 视频生成（可选）
WHISPER_MODEL=base                 # tiny/base/small/medium/large
```
