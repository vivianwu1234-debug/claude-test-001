"""
短视频素材库
- 基于 SQLite 存储拆解结果
- 支持标签管理、搜索、导出
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "material_library.db")


def get_db_path() -> str:
    """获取数据库路径，确保目录存在"""
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    return DB_PATH


def init_db():
    """初始化数据库，创建所有必要的表"""
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    # 视频素材表
    c.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_name TEXT NOT NULL,
            video_path TEXT,
            duration REAL,
            resolution TEXT,
            total_shots INTEGER,
            cover_path TEXT,
            tags TEXT,           -- JSON array
            category TEXT,       -- 类目：美妆/科技/美食 等
            platform TEXT,       -- 平台：抖音/小红书/视频号 等
            overall_score INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 分镜脚本表
    c.execute("""
        CREATE TABLE IF NOT EXISTS storyboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            shot_index INTEGER,
            frame_path TEXT,
            timestamp REAL,
            duration REAL,
            narration TEXT,
            structure_tag TEXT,  -- Hook/Body/CTA
            ai_prompt TEXT,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)

    # 脚本分析表
    c.execute("""
        CREATE TABLE IF NOT EXISTS script_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            hook_type TEXT,
            hook_text TEXT,
            hook_score INTEGER,
            body_type TEXT,
            body_value TEXT,
            body_score INTEGER,
            cta_type TEXT,
            cta_text TEXT,
            cta_score INTEGER,
            viral_elements TEXT,   -- JSON
            blueprint TEXT,        -- JSON
            full_analysis TEXT,    -- JSON
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)

    # AI生成方案表
    c.execute("""
        CREATE TABLE IF NOT EXISTS generation_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id INTEGER,
            product_info TEXT,
            generation_plan TEXT,  -- JSON
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (video_id) REFERENCES videos(id)
        )
    """)

    # 素材标签表（预设标签库）
    c.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            color TEXT DEFAULT '#667eea',
            usage_count INTEGER DEFAULT 0
        )
    """)

    # 预置常用标签
    default_tags = [
        ("痛点型钩子", "hook", "#FF6B6B"),
        ("悬念型钩子", "hook", "#FF6B6B"),
        ("反常识钩子", "hook", "#FF9F43"),
        ("干货列举", "body", "#4ECDC4"),
        ("故事叙述", "body", "#4ECDC4"),
        ("对比演示", "body", "#54A0FF"),
        ("关注CTA", "cta", "#45B7D1"),
        ("互动CTA", "cta", "#45B7D1"),
        ("美妆", "category", "#FF9FF3"),
        ("科技数码", "category", "#48DBFB"),
        ("美食", "category", "#FF9F43"),
        ("知识教程", "category", "#1DD1A1"),
        ("情感故事", "category", "#F368E0"),
        ("爆款", "quality", "#FFD700"),
        ("高完播率", "quality", "#2ECC71"),
    ]

    for name, cat, color in default_tags:
        c.execute(
            "INSERT OR IGNORE INTO tags (name, category, color) VALUES (?, ?, ?)",
            (name, cat, color)
        )

    conn.commit()
    conn.close()


def save_video(
    video_name: str,
    shot_result: dict,
    storyboard_result: dict,
    analysis_result: dict,
    tags: list[str] = None,
    category: str = "",
    platform: str = "抖音",
    generation_result: Optional[dict] = None
) -> int:
    """保存完整的视频分析结果到素材库"""
    init_db()
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    video_info = shot_result.get("video_info", {})
    analysis = analysis_result.get("analysis", {})
    overall = analysis.get("overall_assessment", {})

    # 插入视频主记录
    c.execute("""
        INSERT INTO videos (
            video_name, video_path, duration, resolution,
            total_shots, cover_path, tags, category, platform, overall_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        video_name,
        shot_result.get("video_path", ""),
        video_info.get("duration", 0),
        video_info.get("resolution", ""),
        shot_result.get("total_shots", 0),
        shot_result.get("cover_path", ""),
        json.dumps(tags or [], ensure_ascii=False),
        category,
        platform,
        overall.get("total_score", 0)
    ))
    video_id = c.lastrowid

    # 插入分镜数据
    tagged_storyboard = analysis_result.get("tagged_storyboard", [])
    for shot in tagged_storyboard:
        c.execute("""
            INSERT INTO storyboard (
                video_id, shot_index, frame_path, timestamp, duration,
                narration, structure_tag
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            video_id,
            shot.get("shot_index", 0),
            shot.get("frame_path", ""),
            shot.get("timestamp", 0),
            shot.get("duration", 0),
            shot.get("narration", ""),
            shot.get("structure_tag", "")
        ))

    # 插入脚本分析
    hook = analysis.get("hook", {})
    body = analysis.get("body", {})
    cta = analysis.get("cta", {})

    c.execute("""
        INSERT INTO script_analysis (
            video_id, hook_type, hook_text, hook_score,
            body_type, body_value, body_score,
            cta_type, cta_text, cta_score,
            viral_elements, blueprint, full_analysis
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        video_id,
        hook.get("type", ""),
        hook.get("text", ""),
        hook.get("score", 0),
        body.get("type", ""),
        body.get("value_delivered", ""),
        body.get("score", 0),
        cta.get("type", ""),
        cta.get("text", ""),
        cta.get("score", 0),
        json.dumps(analysis.get("viral_elements", {}), ensure_ascii=False),
        json.dumps(analysis.get("replication_blueprint", {}), ensure_ascii=False),
        json.dumps(analysis, ensure_ascii=False)
    ))

    # 插入生成方案
    if generation_result:
        c.execute("""
            INSERT INTO generation_plans (video_id, product_info, generation_plan)
            VALUES (?, ?, ?)
        """, (
            video_id,
            generation_result.get("product_info", ""),
            json.dumps(generation_result.get("generation_plan", {}), ensure_ascii=False)
        ))

    # 更新标签使用次数
    for tag in (tags or []):
        c.execute(
            "UPDATE tags SET usage_count = usage_count + 1 WHERE name = ?",
            (tag,)
        )

    conn.commit()
    conn.close()

    return video_id


def get_all_videos(
    category: str = "",
    platform: str = "",
    tag: str = "",
    search: str = "",
    limit: int = 50
) -> list[dict]:
    """查询素材库中的视频列表"""
    init_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = "SELECT * FROM videos WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if platform:
        query += " AND platform = ?"
        params.append(platform)

    if search:
        query += " AND video_name LIKE ?"
        params.append(f"%{search}%")

    if tag:
        query += " AND tags LIKE ?"
        params.append(f'%"{tag}"%')

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = c.execute(query, params).fetchall()
    conn.close()

    result = []
    for row in rows:
        d = dict(row)
        try:
            d["tags"] = json.loads(d.get("tags", "[]"))
        except Exception:
            d["tags"] = []
        result.append(d)

    return result


def get_video_detail(video_id: int) -> dict:
    """获取视频完整详情"""
    init_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    video = dict(c.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone() or {})
    shots = [dict(r) for r in c.execute(
        "SELECT * FROM storyboard WHERE video_id = ? ORDER BY shot_index", (video_id,)
    ).fetchall()]
    analysis_row = c.execute(
        "SELECT * FROM script_analysis WHERE video_id = ?", (video_id,)
    ).fetchone()
    analysis = dict(analysis_row) if analysis_row else {}

    conn.close()

    if analysis.get("full_analysis"):
        try:
            analysis["full_analysis"] = json.loads(analysis["full_analysis"])
        except Exception:
            pass

    return {"video": video, "shots": shots, "analysis": analysis}


def get_all_tags() -> list[dict]:
    """获取所有标签"""
    init_db()
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    tags = [dict(r) for r in conn.execute(
        "SELECT * FROM tags ORDER BY usage_count DESC"
    ).fetchall()]
    conn.close()
    return tags


def get_stats() -> dict:
    """获取素材库统计数据"""
    init_db()
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()

    total = c.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    avg_score = c.execute("SELECT AVG(overall_score) FROM videos").fetchone()[0] or 0
    total_shots = c.execute("SELECT SUM(total_shots) FROM videos").fetchone()[0] or 0
    categories = c.execute(
        "SELECT category, COUNT(*) as cnt FROM videos GROUP BY category ORDER BY cnt DESC"
    ).fetchall()
    hook_types = c.execute(
        "SELECT hook_type, COUNT(*) as cnt FROM script_analysis GROUP BY hook_type ORDER BY cnt DESC"
    ).fetchall()

    conn.close()

    return {
        "total_videos": total,
        "avg_score": round(avg_score, 1),
        "total_shots": total_shots,
        "categories": [{"name": r[0], "count": r[1]} for r in categories if r[0]],
        "hook_types": [{"type": r[0], "count": r[1]} for r in hook_types if r[0]]
    }


def delete_video(video_id: int):
    """从素材库删除视频记录"""
    init_db()
    conn = sqlite3.connect(get_db_path())
    c = conn.cursor()
    c.execute("DELETE FROM storyboard WHERE video_id = ?", (video_id,))
    c.execute("DELETE FROM script_analysis WHERE video_id = ?", (video_id,))
    c.execute("DELETE FROM generation_plans WHERE video_id = ?", (video_id,))
    c.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    conn.commit()
    conn.close()
