"""
爆款短视频拆解工具 - FastAPI 后端
"""

import os
import sys
import json
import uuid
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

app = FastAPI(title="爆款短视频拆解工具 API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件目录
STATIC_DIR = Path(__file__).parent.parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 任务状态存储（生产环境可换 Redis）
tasks: dict[str, dict] = {}


# ── 数据模型 ───────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    task_id: str
    whisper_model: str = "base"
    language: str = "zh"
    threshold: float = 30.0
    anthropic_api_key: Optional[str] = None


class GenerateRequest(BaseModel):
    task_id: str
    product_name: str
    product_description: str
    model: str = "veo3-fast"
    aspect_ratio: str = "9:16"
    anthropic_api_key: Optional[str] = None
    jimeng_api_key: Optional[str] = None


class SaveLibraryRequest(BaseModel):
    task_id: str
    category: str = ""
    platform: str = "抖音"
    tags: list[str] = []


# ── 辅助函数 ───────────────────────────────────────────────────────────────

def get_task_dir(task_id: str) -> Path:
    d = STATIC_DIR / "tasks" / task_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def update_task(task_id: str, **kwargs):
    if task_id not in tasks:
        tasks[task_id] = {}
    tasks[task_id].update(kwargs)
    tasks[task_id]["updated_at"] = datetime.now().isoformat()


# ── 端点 ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "爆款短视频拆解工具 API v2.0", "docs": "/docs"}


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """上传视频，返回 task_id"""
    if not file.filename:
        raise HTTPException(400, "无效文件")

    ext = Path(file.filename).suffix.lower()
    if ext not in [".mp4", ".mov", ".avi", ".mkv"]:
        raise HTTPException(400, f"不支持的格式: {ext}")

    task_id = str(uuid.uuid4())[:8]
    task_dir = get_task_dir(task_id)

    video_path = task_dir / file.filename
    content = await file.read()
    with open(video_path, "wb") as f:
        f.write(content)

    size_mb = len(content) / 1024 / 1024

    update_task(task_id,
        status="uploaded",
        video_path=str(video_path),
        video_name=Path(file.filename).stem,
        filename=file.filename,
        size_mb=round(size_mb, 2),
        task_dir=str(task_dir)
    )

    return {
        "task_id": task_id,
        "filename": file.filename,
        "size_mb": round(size_mb, 2),
        "status": "uploaded"
    }


@app.post("/api/analyze")
async def analyze_video(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    """启动视频分析（异步后台任务）"""
    task_id = req.task_id
    if task_id not in tasks:
        raise HTTPException(404, f"Task {task_id} 不存在")

    update_task(task_id,
        status="analyzing",
        progress={"upload": 100, "analysis": 0},
        step="shot_breakdown"
    )

    background_tasks.add_task(
        run_full_analysis,
        task_id=task_id,
        whisper_model=req.whisper_model,
        language=req.language,
        threshold=req.threshold,
        anthropic_api_key=req.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    )

    return {"task_id": task_id, "status": "analyzing"}


@app.get("/api/status/{task_id}")
def get_status(task_id: str):
    """轮询任务状态"""
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")
    return tasks[task_id]


@app.get("/api/result/{task_id}")
def get_result(task_id: str):
    """获取完整分析结果"""
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")

    task = tasks[task_id]
    if task.get("status") != "done":
        return {"status": task.get("status"), "step": task.get("step")}

    return task.get("result", {})


@app.post("/api/generate")
async def generate_video(req: GenerateRequest, background_tasks: BackgroundTasks):
    """AI 视频生成"""
    task_id = req.task_id
    if task_id not in tasks or tasks[task_id].get("status") != "done":
        raise HTTPException(400, "请先完成视频分析")

    update_task(task_id, gen_status="generating")

    background_tasks.add_task(
        run_generation,
        task_id=task_id,
        product_name=req.product_name,
        product_description=req.product_description,
        anthropic_api_key=req.anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
        jimeng_api_key=req.jimeng_api_key or os.environ.get("JIMENG_API_KEY", "")
    )

    return {"task_id": task_id, "gen_status": "generating"}


@app.post("/api/library/save")
def save_to_library(req: SaveLibraryRequest):
    """保存到素材库"""
    task_id = req.task_id
    if task_id not in tasks or tasks[task_id].get("status") != "done":
        raise HTTPException(400, "分析未完成")

    from database.material_db import save_video
    task = tasks[task_id]
    result = task.get("result", {})

    video_id = save_video(
        video_name=task.get("video_name", ""),
        shot_result=result.get("shot_result", {}),
        storyboard_result=result.get("storyboard_result", {}),
        analysis_result=result.get("analysis_result", {}),
        tags=req.tags,
        category=req.category,
        platform=req.platform,
        generation_result=result.get("generation_result")
    )

    return {"video_id": video_id, "saved": True}


@app.get("/api/library")
def get_library(search: str = "", category: str = "", platform: str = ""):
    """获取素材库列表"""
    from database.material_db import get_all_videos, get_stats
    videos = get_all_videos(category=category, platform=platform, search=search)
    stats = get_stats()
    return {"videos": videos, "stats": stats}


@app.get("/api/report/{task_id}")
def download_report(task_id: str, fmt: str = "html"):
    """下载报告"""
    if task_id not in tasks:
        raise HTTPException(404, "Task not found")

    task_dir = Path(tasks[task_id].get("task_dir", ""))
    if fmt == "html":
        path = task_dir / "replication_report.html"
    else:
        path = task_dir / "replication_report.md"

    if not path.exists():
        raise HTTPException(404, "报告尚未生成")

    return FileResponse(
        str(path),
        media_type="text/html" if fmt == "html" else "text/markdown",
        filename=f"video_report_{task_id}.{fmt}"
    )


# ── 后台任务函数 ────────────────────────────────────────────────────────────

def run_full_analysis(
    task_id: str,
    whisper_model: str,
    language: str,
    threshold: float,
    anthropic_api_key: str
):
    """完整分析流程（后台执行）"""
    try:
        task = tasks[task_id]
        video_path = task["video_path"]
        task_dir = Path(task["task_dir"])

        # Step 1: 镜头拆解
        update_task(task_id, step="shot_breakdown", progress={"upload": 100, "analysis": 10})
        from modules.shot_breakdown import analyze_shots
        shot_result = analyze_shots(video_path, str(task_dir), threshold)
        # 将路径转为 URL 可访问格式
        shot_result = _normalize_paths(shot_result, task_id)
        update_task(task_id, step="storyboard", progress={"upload": 100, "analysis": 40})

        # Step 2: 分镜脚本
        from modules.storyboard import generate_storyboard
        keyframes_raw = tasks[task_id].get("_raw_keyframes") or shot_result.get("keyframes", [])
        # 用原始路径做 storyboard
        raw_shot = shot_result.copy()
        storyboard_result = generate_storyboard(
            video_path,
            shot_result["keyframes"],
            str(task_dir),
            model_size=whisper_model
        )
        update_task(task_id, step="script_analysis", progress={"upload": 100, "analysis": 70})

        # Step 3: 脚本结构分析
        analysis_result = {"analysis": {}, "tagged_storyboard": storyboard_result.get("storyboard", [])}
        if anthropic_api_key:
            from modules.script_analysis import analyze_script
            full_text = storyboard_result.get("transcript", {}).get("full_text", "")
            analysis_result = analyze_script(
                full_text,
                storyboard_result.get("storyboard", []),
                str(task_dir),
                api_key=anthropic_api_key
            )
        update_task(task_id, step="metrics", progress={"upload": 100, "analysis": 85})

        # Step 4: 数据指标分析
        metrics = compute_metrics(shot_result, storyboard_result, analysis_result)

        # Step 5: 生成报告
        update_task(task_id, step="report", progress={"upload": 100, "analysis": 95})
        from modules.report_generator import generate_html_report, generate_markdown_report
        generate_html_report(
            shot_result.get("video_info", {}),
            shot_result, storyboard_result, analysis_result,
            output_dir=str(task_dir)
        )
        generate_markdown_report(shot_result, storyboard_result, analysis_result, str(task_dir))

        # 完成
        update_task(task_id,
            status="done",
            step="done",
            progress={"upload": 100, "analysis": 100},
            result={
                "shot_result": shot_result,
                "storyboard_result": storyboard_result,
                "analysis_result": analysis_result,
                "metrics": metrics,
                "generation_result": None
            }
        )

    except Exception as e:
        import traceback
        update_task(task_id,
            status="error",
            error=str(e),
            traceback=traceback.format_exc()
        )


def run_generation(
    task_id: str,
    product_name: str,
    product_description: str,
    anthropic_api_key: str,
    jimeng_api_key: str
):
    """AI 视频生成（后台执行）"""
    try:
        task = tasks[task_id]
        result = task.get("result", {})
        task_dir = Path(task["task_dir"])

        product_info = f"产品名称：{product_name}\n\n{product_description}"

        from modules.ai_generation import generate_ai_content
        generation_result = generate_ai_content(
            result["analysis_result"]["analysis"],
            result["analysis_result"]["tagged_storyboard"],
            product_info,
            str(task_dir),
            api_key=anthropic_api_key,
            jimeng_api_key=jimeng_api_key or None
        )

        result["generation_result"] = generation_result
        result["generation_result"]["product_name"] = product_name
        update_task(task_id, gen_status="done", result=result)

    except Exception as e:
        update_task(task_id, gen_status="error", gen_error=str(e))


def compute_metrics(shot_result: dict, storyboard_result: dict, analysis_result: dict) -> dict:
    """计算数据指标：产品首次出现时间、产品露出时长等"""
    video_info = shot_result.get("video_info", {})
    duration = video_info.get("duration", 0)
    total_shots = shot_result.get("total_shots", 0)

    tagged = analysis_result.get("tagged_storyboard", [])

    # 找到产品展示类镜头
    product_shots = [s for s in tagged if "Body" in s.get("structure_tag", "") or "产品" in s.get("narration", "")]
    hook_shots = [s for s in tagged if "Hook" in s.get("structure_tag", "")]

    # 产品首次出现时间（Hook 结束时间）
    product_first_appear = 0.0
    if hook_shots:
        last_hook = hook_shots[-1]
        product_first_appear = round(last_hook["timestamp"] + last_hook.get("duration", 0), 1)
    elif product_shots:
        product_first_appear = product_shots[0]["timestamp"]

    # 产品露出时长（Body 段总时长）
    product_exposure = sum(s.get("duration", 0) for s in product_shots)
    product_exposure_ratio = round(product_exposure / duration * 100, 0) if duration > 0 else 0

    # 平均镜头时长
    avg_shot_duration = round(duration / total_shots, 1) if total_shots > 0 else 0

    # 生成优化建议
    suggestions = []
    if product_first_appear > 5:
        suggestions.append(f"产品首现时间为{product_first_appear}s，建议在5秒内展示产品")
    if product_exposure_ratio < 30:
        suggestions.append(f"产品露出占比{product_exposure_ratio}%，建议提升至30%以上")
    if duration > 60:
        suggestions.append("视频时长超过60秒，短视频建议控制在15-60秒")
    if not suggestions:
        suggestions.append("视频指标良好，保持当前结构")

    return {
        "product_first_appear": product_first_appear,
        "product_exposure": round(product_exposure, 1),
        "product_exposure_ratio": int(product_exposure_ratio),
        "total_duration": duration,
        "total_shots": total_shots,
        "avg_shot_duration": avg_shot_duration,
        "suggestions": suggestions
    }


def _normalize_paths(obj, task_id: str):
    """将本地文件路径转换为 HTTP 可访问的 URL"""
    if isinstance(obj, dict):
        return {k: _normalize_paths(v, task_id) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_normalize_paths(i, task_id) for i in obj]
    elif isinstance(obj, str) and os.path.isabs(obj) and os.path.exists(obj):
        # 转换为相对 static URL
        try:
            rel = Path(obj).relative_to(STATIC_DIR)
            return f"/static/{rel}"
        except ValueError:
            return obj
    return obj
