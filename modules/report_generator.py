"""
复刻方案报告模块
- 生成完整的爆款视频拆解报告
- 包含镜头截图、文案分析、结构标注
- 输出 HTML 和 Markdown 格式
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional


def image_to_base64(image_path: str) -> str:
    """将图片转为 Base64 以嵌入 HTML"""
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


def generate_html_report(
    video_info: dict,
    shot_result: dict,
    storyboard_result: dict,
    analysis_result: dict,
    generation_result: Optional[dict] = None,
    output_dir: str = "."
) -> str:
    """
    生成完整的 HTML 格式复刻方案报告
    """
    video_name = shot_result.get("video_name", "未知视频")
    video_meta = shot_result.get("video_info", {})
    keyframes = shot_result.get("keyframes", [])
    storyboard = storyboard_result.get("storyboard", [])
    transcript = storyboard_result.get("transcript", {})
    analysis = analysis_result.get("analysis", {})
    tagged_storyboard = analysis_result.get("tagged_storyboard", storyboard)

    # 封面图
    cover_path = shot_result.get("cover_path", "")
    cover_b64 = image_to_base64(cover_path) if cover_path else ""
    cover_src = f"data:image/jpeg;base64,{cover_b64}" if cover_b64 else ""

    # 整体评分
    overall = analysis.get("overall_assessment", {})
    total_score = overall.get("total_score", 0)

    # 三段论数据
    hook = analysis.get("hook", {})
    body = analysis.get("body", {})
    cta_data = analysis.get("cta", {})
    viral = analysis.get("viral_elements", {})
    blueprint = analysis.get("replication_blueprint", {})

    # 生成分镜卡片 HTML
    shot_cards = ""
    for shot in tagged_storyboard:
        img_b64 = image_to_base64(shot.get("frame_path", ""))
        img_src = f"data:image/jpeg;base64,{img_b64}" if img_b64 else "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"

        tag = shot.get("structure_tag", "")
        tag_color = shot.get("structure_color", "#888")
        narration = shot.get("narration", "（无台词）")

        shot_cards += f"""
        <div class="shot-card">
            <img src="{img_src}" alt="镜头{shot['shot_index']}">
            <div class="shot-info">
                <div class="shot-header">
                    <span class="shot-num">镜头 {shot['shot_index']}</span>
                    <span class="shot-time">{shot['time_label']}</span>
                    <span class="shot-dur">{shot['duration']}s</span>
                </div>
                <div class="structure-tag" style="background: {tag_color}20; color: {tag_color}; border: 1px solid {tag_color}40;">
                    {tag}
                </div>
                <div class="shot-narration">"{narration}"</div>
            </div>
        </div>"""

    # 生成新脚本部分
    new_script_html = ""
    if generation_result:
        plan = generation_result.get("generation_plan", {})
        if not plan.get("parse_error"):
            concept = plan.get("video_concept", {})
            script = plan.get("new_script", {})
            notes = plan.get("production_notes", {})
            jimeng_prompts = plan.get("jimeng_video_prompts", [])

            new_script_html = f"""
        <section class="section">
            <h2>🤖 AI 复刻方案</h2>
            <div class="concept-box">
                <h3>{concept.get('title', '新视频方案')}</h3>
                <div class="meta-grid">
                    <div><strong>核心信息</strong><br>{concept.get('core_message', '')}</div>
                    <div><strong>目标受众</strong><br>{concept.get('target_audience', '')}</div>
                    <div><strong>情绪基调</strong><br>{concept.get('emotional_tone', '')}</div>
                    <div><strong>预计时长</strong><br>{notes.get('total_duration', '')}秒</div>
                </div>
            </div>

            <h3>📋 新视频分镜脚本</h3>
            <table class="script-table">
                <thead>
                    <tr><th>阶段</th><th>台词</th><th>画面描述</th><th>AI提示词</th></tr>
                </thead>
                <tbody>
                    <tr class="hook-row">
                        <td><strong>🎣 Hook</strong></td>
                        <td>{script.get('hook', {}).get('narration', '')}</td>
                        <td>{script.get('hook', {}).get('visual_description', '')}</td>
                        <td>-</td>
                    </tr>
                    {''.join([
                        f'<tr><td>📦 镜头{s.get("shot_number","")}</td><td>{s.get("narration","")}</td><td>{s.get("visual_description","")}</td><td><code>{s.get("ai_image_prompt","")[:80]}...</code></td></tr>'
                        for s in script.get('body', [])
                    ])}
                    <tr class="cta-row">
                        <td><strong>📢 CTA</strong></td>
                        <td>{script.get('cta', {}).get('narration', '')}</td>
                        <td>{script.get('cta', {}).get('visual_description', '')}</td>
                        <td>-</td>
                    </tr>
                </tbody>
            </table>

            <h3>🎥 即梦AI视频生成提示词</h3>
            <div class="prompts-grid">
                {''.join([
                    f'<div class="prompt-card"><strong>{p.get("scene","")}</strong><br><em>{p.get("prompt_zh","")}</em><br><code>{p.get("prompt_en","")}</code></div>'
                    for p in jimeng_prompts
                ])}
            </div>

            <h3>🎵 制作建议</h3>
            <div class="production-notes">
                <span>背景音乐：{notes.get('music_style', '')}</span>
                <span>推荐色调：{notes.get('color_palette', '')}</span>
                <span>剪辑节奏：{notes.get('editing_rhythm', '')}</span>
            </div>
        </section>"""

    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>爆款视频拆解报告 - {video_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f0f2f5; color: #1a1a2e; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}

        /* Header */
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 16px; padding: 32px; margin-bottom: 24px; display: flex; gap: 24px; align-items: center; }}
        .header-cover {{ width: 120px; height: 200px; object-fit: cover; border-radius: 12px; border: 3px solid rgba(255,255,255,0.3); }}
        .header-info h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header-meta {{ display: flex; gap: 16px; flex-wrap: wrap; margin-top: 12px; }}
        .meta-tag {{ background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 20px; font-size: 13px; }}

        /* Score */
        .score-ring {{ width: 80px; height: 80px; border-radius: 50%; background: conic-gradient(#FFD700 {total_score * 3.6}deg, rgba(255,255,255,0.2) 0); display: flex; align-items: center; justify-content: center; margin-left: auto; flex-shrink: 0; }}
        .score-inner {{ width: 60px; height: 60px; border-radius: 50%; background: rgba(255,255,255,0.15); display: flex; flex-direction: column; align-items: center; justify-content: center; }}
        .score-num {{ font-size: 20px; font-weight: bold; }}
        .score-label {{ font-size: 10px; opacity: 0.8; }}

        /* Section */
        .section {{ background: white; border-radius: 16px; padding: 28px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }}
        .section h2 {{ font-size: 20px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #f0f0f0; color: #333; }}
        .section h3 {{ font-size: 16px; margin: 20px 0 12px; color: #444; }}

        /* Three Parts */
        .three-parts {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
        .part-card {{ border-radius: 12px; padding: 20px; }}
        .part-hook {{ background: #FFF0F0; border-left: 4px solid #FF6B6B; }}
        .part-body {{ background: #F0FFFE; border-left: 4px solid #4ECDC4; }}
        .part-cta {{ background: #F0F8FF; border-left: 4px solid #45B7D1; }}
        .part-card h3 {{ margin-top: 0; font-size: 15px; }}
        .part-text {{ font-size: 13px; color: #666; margin: 8px 0; line-height: 1.6; }}
        .part-badge {{ display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; margin-bottom: 8px; }}
        .score-bar {{ display: flex; align-items: center; gap: 8px; margin-top: 8px; }}
        .score-bar-fill {{ height: 6px; border-radius: 3px; flex: 1; background: #e0e0e0; }}
        .score-bar-inner {{ height: 100%; border-radius: 3px; }}

        /* Shot Cards */
        .shots-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
        .shot-card {{ border: 1px solid #f0f0f0; border-radius: 12px; overflow: hidden; background: #fafafa; }}
        .shot-card img {{ width: 100%; aspect-ratio: 9/16; object-fit: cover; display: block; }}
        .shot-info {{ padding: 12px; }}
        .shot-header {{ display: flex; gap: 6px; align-items: center; margin-bottom: 8px; font-size: 12px; }}
        .shot-num {{ font-weight: bold; color: #333; }}
        .shot-time {{ color: #888; }}
        .shot-dur {{ color: #aaa; margin-left: auto; }}
        .structure-tag {{ display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 500; margin-bottom: 8px; }}
        .shot-narration {{ font-size: 12px; color: #666; line-height: 1.5; font-style: italic; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }}

        /* Viral Elements */
        .viral-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
        .viral-item {{ background: #f8f9fa; border-radius: 8px; padding: 14px; }}
        .viral-item label {{ font-size: 12px; color: #888; display: block; margin-bottom: 4px; }}
        .viral-item span {{ font-size: 14px; color: #333; font-weight: 500; }}

        /* Blueprint */
        .blueprint-box {{ background: linear-gradient(135deg, #667eea10, #764ba210); border: 1px solid #764ba230; border-radius: 12px; padding: 20px; }}
        .blueprint-item {{ margin-bottom: 16px; }}
        .blueprint-item label {{ font-size: 12px; color: #764ba2; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
        .blueprint-item p {{ font-size: 14px; color: #444; margin-top: 4px; line-height: 1.6; }}
        .blueprint-tags {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }}
        .blueprint-tag {{ background: #764ba220; color: #764ba2; padding: 4px 12px; border-radius: 12px; font-size: 12px; }}

        /* Suggestions */
        .suggestions {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
        .suggestion-group h4 {{ font-size: 14px; margin-bottom: 8px; }}
        .suggestion-list {{ list-style: none; }}
        .suggestion-list li {{ padding: 6px 0; font-size: 13px; color: #555; border-bottom: 1px solid #f5f5f5; }}
        .suggestion-list li::before {{ content: "•"; margin-right: 8px; color: #764ba2; }}

        /* Script Table */
        .script-table {{ width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13px; }}
        .script-table th {{ background: #f5f5f5; padding: 10px 14px; text-align: left; color: #555; }}
        .script-table td {{ padding: 10px 14px; border-bottom: 1px solid #f5f5f5; vertical-align: top; }}
        .hook-row td {{ background: #FFF0F0; }}
        .cta-row td {{ background: #F0F8FF; }}

        /* Concept Box */
        .concept-box {{ background: #f8f9fa; border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 12px; font-size: 13px; }}
        .meta-grid div {{ padding: 10px; background: white; border-radius: 8px; }}
        .meta-grid strong {{ color: #666; font-size: 11px; display: block; margin-bottom: 4px; }}

        /* Prompts Grid */
        .prompts-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }}
        .prompt-card {{ background: #1a1a2e; color: #e0e0e0; border-radius: 12px; padding: 16px; }}
        .prompt-card strong {{ color: #667eea; display: block; margin-bottom: 6px; }}
        .prompt-card em {{ font-size: 13px; color: #ccc; display: block; margin-bottom: 8px; }}
        .prompt-card code {{ font-size: 11px; color: #4ECDC4; word-break: break-all; }}

        /* Production Notes */
        .production-notes {{ display: flex; gap: 12px; flex-wrap: wrap; }}
        .production-notes span {{ background: #f0f2f5; padding: 8px 16px; border-radius: 20px; font-size: 13px; color: #555; }}

        /* Footer */
        .footer {{ text-align: center; padding: 24px; color: #aaa; font-size: 12px; }}

        @media (max-width: 768px) {{
            .three-parts {{ grid-template-columns: 1fr; }}
            .viral-grid {{ grid-template-columns: 1fr; }}
            .suggestions {{ grid-template-columns: 1fr; }}
            .meta-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
<div class="container">

    <!-- Header -->
    <div class="header">
        {'<img class="header-cover" src="' + cover_src + '" alt="封面">' if cover_src else ''}
        <div class="header-info">
            <h1>🎬 {video_name}</h1>
            <p style="opacity:0.8; margin-top:4px;">爆款短视频拆解分析报告</p>
            <div class="header-meta">
                <span class="meta-tag">⏱️ {video_meta.get('duration_label', '')}</span>
                <span class="meta-tag">📐 {video_meta.get('resolution', '')}</span>
                <span class="meta-tag">🎞️ {video_meta.get('fps', '')} fps</span>
                <span class="meta-tag">🎭 {shot_result.get('total_shots', 0)} 个镜头</span>
                <span class="meta-tag">📅 {now}</span>
            </div>
        </div>
        <div class="score-ring">
            <div class="score-inner">
                <span class="score-num">{total_score}</span>
                <span class="score-label">综合分</span>
            </div>
        </div>
    </div>

    <!-- Module 1: Shot Breakdown -->
    <section class="section">
        <h2>📸 镜头拆解 — {shot_result.get('total_shots', 0)} 个镜头</h2>
        <div class="shots-grid">
            {shot_cards}
        </div>
    </section>

    <!-- Module 2: Script Structure Analysis -->
    <section class="section">
        <h2>🧠 脚本结构分析 — 三段论拆解</h2>

        <div class="three-parts">
            <!-- Hook -->
            <div class="part-card part-hook">
                <h3>🎣 第一段：钩子（Hook）</h3>
                <span class="part-badge" style="background:#FF6B6B20; color:#FF6B6B;">{hook.get('type', '未识别')}</span>
                <p class="part-text">{hook.get('text', '')}</p>
                <p class="part-text" style="color:#888;"><em>{hook.get('effectiveness', '')}</em></p>
                <div class="score-bar">
                    <span style="font-size:12px; color:#888;">评分</span>
                    <div class="score-bar-fill"><div class="score-bar-inner" style="width:{hook.get('score', 0) * 10}%; background:#FF6B6B;"></div></div>
                    <span style="font-size:12px; font-weight:bold; color:#FF6B6B;">{hook.get('score', 0)}</span>
                </div>
            </div>

            <!-- Body -->
            <div class="part-card part-body">
                <h3>📦 第二段：内容主体（Body）</h3>
                <span class="part-badge" style="background:#4ECDC420; color:#4ECDC4;">{body.get('type', '未识别')}</span>
                <p class="part-text">{body.get('value_delivered', '')}</p>
                <ul style="font-size:13px; color:#555; padding-left:16px; margin-top:8px;">
                    {''.join([f'<li>{kp}</li>' for kp in body.get('key_points', [])])}
                </ul>
                <div class="score-bar">
                    <span style="font-size:12px; color:#888;">评分</span>
                    <div class="score-bar-fill"><div class="score-bar-inner" style="width:{body.get('score', 0) * 10}%; background:#4ECDC4;"></div></div>
                    <span style="font-size:12px; font-weight:bold; color:#4ECDC4;">{body.get('score', 0)}</span>
                </div>
            </div>

            <!-- CTA -->
            <div class="part-card part-cta">
                <h3>📢 第三段：行动号召（CTA）</h3>
                <span class="part-badge" style="background:#45B7D120; color:#45B7D1;">{cta_data.get('type', '未识别')}</span>
                <p class="part-text">{cta_data.get('text', '')}</p>
                <p class="part-text" style="color:#888;">紧迫感：{cta_data.get('urgency_level', '中')}</p>
                <div class="score-bar">
                    <span style="font-size:12px; color:#888;">评分</span>
                    <div class="score-bar-fill"><div class="score-bar-inner" style="width:{cta_data.get('score', 0) * 10}%; background:#45B7D1;"></div></div>
                    <span style="font-size:12px; font-weight:bold; color:#45B7D1;">{cta_data.get('score', 0)}</span>
                </div>
            </div>
        </div>

        <!-- Viral Elements -->
        <h3>💥 爆款要素</h3>
        <div class="viral-grid">
            <div class="viral-item">
                <label>情绪触发点</label>
                <span>{viral.get('emotion_trigger', '—')}</span>
            </div>
            <div class="viral-item">
                <label>核心冲突/矛盾</label>
                <span>{viral.get('conflict', '—')}</span>
            </div>
            <div class="viral-item">
                <label>反转/惊喜元素</label>
                <span>{viral.get('surprise_factor', '—')}</span>
            </div>
            <div class="viral-item">
                <label>受众共鸣点</label>
                <span>{viral.get('relatability', '—')}</span>
            </div>
        </div>

        <!-- Replication Blueprint -->
        <h3>🗺️ 复刻蓝图</h3>
        <div class="blueprint-box">
            <div class="blueprint-item">
                <label>钩子模板</label>
                <p>{blueprint.get('hook_template', '—')}</p>
            </div>
            <div class="blueprint-item">
                <label>内容结构</label>
                <p>{blueprint.get('body_structure', '—')}</p>
            </div>
            <div class="blueprint-item">
                <label>CTA模板</label>
                <p>{blueprint.get('cta_template', '—')}</p>
            </div>
            <div class="blueprint-item">
                <label>核心成功要素</label>
                <div class="blueprint-tags">
                    {''.join([f'<span class="blueprint-tag">{f}</span>' for f in blueprint.get('key_success_factors', [])])}
                </div>
            </div>
        </div>

        <!-- Suggestions -->
        <h3>📈 优化建议</h3>
        <div class="suggestions">
            <div class="suggestion-group">
                <h4>✅ 亮点</h4>
                <ul class="suggestion-list">
                    {''.join([f'<li>{s}</li>' for s in overall.get('strengths', [])])}
                </ul>
            </div>
            <div class="suggestion-group">
                <h4>⚠️ 优化点</h4>
                <ul class="suggestion-list">
                    {''.join([f'<li>{s}</li>' for s in overall.get('optimization_suggestions', [])])}
                </ul>
            </div>
        </div>
    </section>

    <!-- Module 4 & 5: AI Generation & Replication -->
    {new_script_html}

    <div class="footer">
        爆款短视频拆解工具 | 生成时间：{now} | Powered by Claude & Whisper
    </div>
</div>
</body>
</html>"""

    report_path = os.path.join(output_dir, "replication_report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    return report_path


def generate_markdown_report(
    shot_result: dict,
    storyboard_result: dict,
    analysis_result: dict,
    output_dir: str
) -> str:
    """生成 Markdown 格式报告（轻量版）"""
    video_name = shot_result.get("video_name", "未知视频")
    video_meta = shot_result.get("video_info", {})
    storyboard = storyboard_result.get("storyboard", [])
    analysis = analysis_result.get("analysis", {})
    overall = analysis.get("overall_assessment", {})
    hook = analysis.get("hook", {})
    body = analysis.get("body", {})
    cta_data = analysis.get("cta", {})
    blueprint = analysis.get("replication_blueprint", {})

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# 📊 爆款视频拆解报告：{video_name}",
        f"\n> 生成时间：{now} | 综合评分：{overall.get('total_score', 0)}/100\n",
        "## 视频基本信息",
        f"- 时长：{video_meta.get('duration_label', '')}",
        f"- 分辨率：{video_meta.get('resolution', '')}",
        f"- 总镜头数：{shot_result.get('total_shots', 0)}",
        "",
        "## 🧠 三段论结构分析",
        "",
        "### 🎣 钩子（Hook）",
        f"**类型**：{hook.get('type', '—')}",
        f"**文案**：{hook.get('text', '')}",
        f"**评分**：{hook.get('score', 0)}/10",
        "",
        "### 📦 内容主体（Body）",
        f"**形式**：{body.get('type', '—')}",
        f"**核心价值**：{body.get('value_delivered', '')}",
        f"**评分**：{body.get('score', 0)}/10",
        "",
        "### 📢 行动号召（CTA）",
        f"**类型**：{cta_data.get('type', '—')}",
        f"**文案**：{cta_data.get('text', '')}",
        f"**评分**：{cta_data.get('score', 0)}/10",
        "",
        "## 🗺️ 复刻蓝图",
        f"**钩子模板**：{blueprint.get('hook_template', '')}",
        f"**内容结构**：{blueprint.get('body_structure', '')}",
        f"**CTA模板**：{blueprint.get('cta_template', '')}",
        "",
        "## 📋 分镜台词对照",
        "",
        "| 镜头 | 时间 | 时长 | 结构标签 | 台词 |",
        "|------|------|------|----------|------|",
    ]

    tagged = analysis_result.get("tagged_storyboard", storyboard)
    for shot in tagged:
        tag = shot.get("structure_tag", "")
        narration = shot.get("narration", "—")
        lines.append(
            f"| 镜头{shot['shot_index']} "
            f"| {shot['time_label']} "
            f"| {shot['duration']}s "
            f"| {tag} "
            f"| {narration} |"
        )

    lines += [
        "",
        "## 📈 优化建议",
        "",
        "**亮点**",
        *[f"- {s}" for s in overall.get("strengths", [])],
        "",
        "**优化方向**",
        *[f"- {s}" for s in overall.get("optimization_suggestions", [])],
    ]

    content = "\n".join(lines)
    report_path = os.path.join(output_dir, "replication_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)

    return report_path
