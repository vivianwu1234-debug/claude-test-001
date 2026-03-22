"""
脚本结构分析模块
- 接入 Claude 大模型
- 依据"三段论"框架对文案进行结构化打标
- 三段论：钩子（Hook）→ 内容（Body）→ 行动号召（CTA）
"""

import os
import json
import anthropic
from typing import Optional


THREE_PART_SYSTEM_PROMPT = """你是一位专业的短视频内容策略分析师，专门分析爆款短视频的文案结构。

请严格按照"三段论"框架分析提供的视频文案：

## 三段论框架说明

### 第一段：钩子（Hook）
- **目标**：前3秒抓住观众注意力，防止划走
- **常见形式**：
  * 痛点型：直击用户痛点（"你是不是也..."）
  * 悬念型：制造好奇（"99%的人不知道..."）
  * 反常识型：颠覆认知（"原来这是错的！"）
  * 福利型：直接利益承诺（"免费教你..."）
  * 共情型：情感共鸣（"这个场景太真实了"）

### 第二段：内容（Body）
- **目标**：交付价值，维持观看，建立信任
- **常见形式**：
  * 干货列举（1、2、3 步骤）
  * 故事叙述（问题→过程→结果）
  * 对比呈现（before/after）
  * 演示教学（手把手）
  * 案例分享（真实场景）

### 第三段：行动号召（CTA）
- **目标**：引导用户完成期望行为
- **常见形式**：
  * 关注型（"关注我，每天分享..."）
  * 互动型（"评论区告诉我..."）
  * 收藏型（"收藏防丢失"）
  * 购买型（"点击链接购买..."）
  * 分享型（"转发给需要的人"）

## 输出要求
请以 JSON 格式输出，包含：
1. 三段论各部分的文案内容及位置
2. 每部分的具体类型标签
3. 爆款要素分析
4. 整体评分和优化建议
"""


def analyze_script_structure(
    full_text: str,
    storyboard: list[dict],
    api_key: Optional[str] = None
) -> dict:
    """
    使用 Claude 对文案进行三段论结构化分析
    """
    client = anthropic.Anthropic(
        api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
    )

    # 构建带时间戳的完整文案
    timed_script = "\n".join([
        f"[{shot['time_label']} | 镜头{shot['shot_index']}] {shot['narration']}"
        for shot in storyboard
        if shot.get("narration")
    ])

    user_prompt = f"""请分析以下短视频的文案结构：

## 完整文案
{full_text}

## 带时间戳的分镜文案
{timed_script}

请按照三段论框架进行结构化分析，以下面的 JSON 格式输出：

```json
{{
  "hook": {{
    "text": "钩子部分文案",
    "shot_range": "镜头1-镜头X",
    "time_range": "00:00 - 00:XX",
    "type": "钩子类型（痛点型/悬念型/反常识型/福利型/共情型）",
    "effectiveness": "钩子效果评价",
    "score": 8
  }},
  "body": {{
    "text": "内容主体文案",
    "shot_range": "镜头X-镜头Y",
    "time_range": "00:XX - 00:YY",
    "type": "内容形式（干货列举/故事叙述/对比呈现/演示教学/案例分享）",
    "key_points": ["核心要点1", "核心要点2", "核心要点3"],
    "value_delivered": "交付的核心价值",
    "score": 8
  }},
  "cta": {{
    "text": "行动号召文案",
    "shot_range": "镜头Y-镜头Z",
    "time_range": "00:YY - 结束",
    "type": "CTA类型（关注型/互动型/收藏型/购买型/分享型）",
    "urgency_level": "紧迫感强度（高/中/低）",
    "score": 8
  }},
  "viral_elements": {{
    "emotion_trigger": "情绪触发点",
    "conflict": "核心冲突/矛盾",
    "surprise_factor": "反转/惊喜元素",
    "relatability": "受众共鸣点"
  }},
  "overall_assessment": {{
    "total_score": 80,
    "strengths": ["亮点1", "亮点2"],
    "weaknesses": ["不足1", "不足2"],
    "optimization_suggestions": ["优化建议1", "优化建议2", "优化建议3"]
  }},
  "replication_blueprint": {{
    "hook_template": "可复用的钩子模板",
    "body_structure": "可复用的内容结构",
    "cta_template": "可复用的CTA模板",
    "key_success_factors": ["成功要素1", "成功要素2"]
  }}
}}
```

请严格按照上述 JSON 格式输出，不要添加额外说明。"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=THREE_PART_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}]
    )

    response_text = message.content[0].text.strip()

    # 提取 JSON 内容
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        response_text = response_text[json_start:json_end].strip()

    try:
        analysis = json.loads(response_text)
    except json.JSONDecodeError:
        # 如果解析失败，返回原始文本
        analysis = {"raw_response": response_text, "parse_error": True}

    return analysis


def tag_shots_with_structure(storyboard: list[dict], analysis: dict) -> list[dict]:
    """
    将三段论标签添加到每个镜头
    """
    if "parse_error" in analysis:
        return storyboard

    # 从分析结果中提取各段的时间范围
    tagged_storyboard = []
    for shot in storyboard:
        shot_copy = shot.copy()
        shot_idx = shot["shot_index"]

        # 简单的区间判断
        total = len(storyboard)
        if shot_idx <= max(1, total // 4):
            shot_copy["structure_tag"] = "🎣 Hook (钩子)"
            shot_copy["structure_color"] = "#FF6B6B"
        elif shot_idx <= max(2, total * 3 // 4):
            shot_copy["structure_tag"] = "📦 Body (内容)"
            shot_copy["structure_color"] = "#4ECDC4"
        else:
            shot_copy["structure_tag"] = "📢 CTA (行动号召)"
            shot_copy["structure_color"] = "#45B7D1"

        tagged_storyboard.append(shot_copy)

    return tagged_storyboard


def analyze_script(
    full_text: str,
    storyboard: list[dict],
    output_dir: str,
    api_key: Optional[str] = None
) -> dict:
    """
    完整的脚本结构分析流程
    """
    # Claude 分析
    analysis = analyze_script_structure(full_text, storyboard, api_key)

    # 为分镜打标
    tagged_storyboard = tag_shots_with_structure(storyboard, analysis)

    result = {
        "analysis": analysis,
        "tagged_storyboard": tagged_storyboard
    }

    # 保存结果
    result_path = os.path.join(output_dir, "script_analysis.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result
