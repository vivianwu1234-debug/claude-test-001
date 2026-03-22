"""
AI视频生成模块
- 基于拆解出的结构，结合自身产品生成新的画面描述
- 调用即梦 AI / Claude 视觉描述生成提示词
- 支持生成完整的视频脚本和分镜提示词
"""

import os
import json
import requests
import anthropic
from typing import Optional


IMAGE_PROMPT_SYSTEM = """你是一位专业的短视频创意导演和 AI 绘图提示词专家。

你的任务是根据原视频的镜头结构分析，结合用户提供的新产品信息，生成：
1. 新的分镜画面描述（用于 AI 图像/视频生成）
2. 对应的旁白/台词文案
3. 完整的制作指导

生成的内容要保持原视频的爆款结构（三段论），但融入新产品的特点。

画面提示词风格：专业、电影感、细节丰富，适合 AI 视频/图像生成工具使用。"""


def generate_shot_prompts(
    analysis: dict,
    tagged_storyboard: list[dict],
    product_info: str,
    api_key: Optional[str] = None
) -> dict:
    """
    基于原视频结构，为新产品生成每个镜头的 AI 生成提示词
    """
    client = anthropic.Anthropic(
        api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
    )

    # 提取关键结构信息
    hook_info = analysis.get("hook", {})
    body_info = analysis.get("body", {})
    cta_info = analysis.get("cta", {})
    blueprint = analysis.get("replication_blueprint", {})

    original_structure = f"""
原视频结构分析：
- 钩子类型：{hook_info.get('type', '未知')}
- 钩子文案：{hook_info.get('text', '')}
- 内容形式：{body_info.get('type', '未知')}
- 核心价值：{body_info.get('value_delivered', '')}
- CTA类型：{cta_info.get('type', '未知')}
- 成功要素：{', '.join(blueprint.get('key_success_factors', []))}
"""

    storyboard_info = "\n".join([
        f"镜头{s['shot_index']} ({s['structure_tag']}): {s.get('narration', '无台词')}"
        for s in tagged_storyboard[:10]  # 最多10个镜头
    ])

    user_prompt = f"""请根据以下信息，为新产品生成完整的短视频拍摄方案：

{original_structure}

原视频分镜结构：
{storyboard_info}

## 新产品信息
{product_info}

请生成以下内容，以 JSON 格式输出：

```json
{{
  "video_concept": {{
    "title": "视频标题",
    "core_message": "核心传达信息",
    "target_audience": "目标受众",
    "emotional_tone": "情绪基调"
  }},
  "new_script": {{
    "hook": {{
      "narration": "新钩子台词",
      "visual_description": "画面描述",
      "duration_seconds": 5
    }},
    "body": [
      {{
        "shot_number": 1,
        "narration": "台词",
        "visual_description": "详细画面描述",
        "camera_angle": "镜头角度（如：近景、俯拍、特写）",
        "duration_seconds": 5,
        "ai_image_prompt": "英文AI绘图提示词，详细描述画面内容、风格、光线、氛围"
      }}
    ],
    "cta": {{
      "narration": "新CTA台词",
      "visual_description": "画面描述",
      "duration_seconds": 3
    }}
  }},
  "production_notes": {{
    "total_duration": "预计总时长（秒）",
    "shooting_tips": ["拍摄技巧1", "拍摄技巧2"],
    "music_style": "推荐背景音乐风格",
    "color_palette": "推荐色调",
    "editing_rhythm": "剪辑节奏建议"
  }},
  "jimeng_video_prompts": [
    {{
      "scene": "场景名称",
      "prompt_zh": "中文视频生成提示词",
      "prompt_en": "English video generation prompt for AI tools",
      "duration": "3s"
    }}
  ]
}}
```"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=IMAGE_PROMPT_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}]
    )

    response_text = message.content[0].text.strip()

    # 提取 JSON
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()

    try:
        generation_plan = json.loads(response_text)
    except json.JSONDecodeError:
        generation_plan = {"raw_response": response_text, "parse_error": True}

    return generation_plan


def generate_with_jimeng(prompt: str, api_key: str, duration: int = 5) -> dict:
    """
    调用即梦 AI API 生成视频
    即梦 AI API 文档：https://platform.jimeng.com
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "video-01",
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": "9:16"
    }

    try:
        response = requests.post(
            "https://api.jimeng.com/v1/video/generate",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def generate_ai_content(
    analysis: dict,
    tagged_storyboard: list[dict],
    product_info: str,
    output_dir: str,
    api_key: Optional[str] = None,
    jimeng_api_key: Optional[str] = None
) -> dict:
    """
    完整的 AI 内容生成流程
    """
    # 生成分镜提示词和新脚本
    generation_plan = generate_shot_prompts(
        analysis, tagged_storyboard, product_info, api_key
    )

    result = {
        "product_info": product_info,
        "generation_plan": generation_plan,
        "jimeng_results": []
    }

    # 如果有即梦 API Key，尝试生成视频
    if jimeng_api_key and not generation_plan.get("parse_error"):
        jimeng_prompts = generation_plan.get("jimeng_video_prompts", [])
        for i, prompt_item in enumerate(jimeng_prompts[:3]):  # 最多生成3段
            prompt_en = prompt_item.get("prompt_en", "")
            if prompt_en:
                video_result = generate_with_jimeng(prompt_en, jimeng_api_key)
                result["jimeng_results"].append({
                    "scene": prompt_item.get("scene", f"场景{i+1}"),
                    "prompt": prompt_en,
                    "result": video_result
                })

    # 保存结果
    result_path = os.path.join(output_dir, "ai_generation.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def format_new_script(generation_plan: dict) -> str:
    """将生成方案格式化为可读的脚本"""
    if "parse_error" in generation_plan:
        return generation_plan.get("raw_response", "生成失败")

    lines = []
    concept = generation_plan.get("video_concept", {})
    lines.append(f"# 🎬 {concept.get('title', '新视频方案')}\n")
    lines.append(f"**核心信息**: {concept.get('core_message', '')}")
    lines.append(f"**目标受众**: {concept.get('target_audience', '')}")
    lines.append(f"**情绪基调**: {concept.get('emotional_tone', '')}\n")

    script = generation_plan.get("new_script", {})

    hook = script.get("hook", {})
    lines.append("## 🎣 第一段：钩子（Hook）")
    lines.append(f"**台词**: {hook.get('narration', '')}")
    lines.append(f"**画面**: {hook.get('visual_description', '')}")
    lines.append(f"**时长**: {hook.get('duration_seconds', 5)}秒\n")

    body_shots = script.get("body", [])
    lines.append("## 📦 第二段：内容主体（Body）")
    for shot in body_shots:
        lines.append(f"\n### 镜头 {shot.get('shot_number', '')}")
        lines.append(f"**台词**: {shot.get('narration', '')}")
        lines.append(f"**画面**: {shot.get('visual_description', '')}")
        lines.append(f"**镜头角度**: {shot.get('camera_angle', '')}")
        lines.append(f"**AI提示词**: `{shot.get('ai_image_prompt', '')}`")

    cta = script.get("cta", {})
    lines.append("\n## 📢 第三段：行动号召（CTA）")
    lines.append(f"**台词**: {cta.get('narration', '')}")
    lines.append(f"**画面**: {cta.get('visual_description', '')}")

    notes = generation_plan.get("production_notes", {})
    lines.append("\n## 🎵 制作建议")
    lines.append(f"**预计时长**: {notes.get('total_duration', '')}秒")
    lines.append(f"**背景音乐**: {notes.get('music_style', '')}")
    lines.append(f"**推荐色调**: {notes.get('color_palette', '')}")
    lines.append(f"**剪辑节奏**: {notes.get('editing_rhythm', '')}")

    return "\n".join(lines)
