"""
分镜脚本模块
- 自动提取语音转文字（Whisper）
- 将文案精准匹配到对应的镜头截图
"""

import os
import json
import subprocess
from pathlib import Path


def extract_audio(video_path: str, output_dir: str) -> str:
    """从视频中提取音频"""
    audio_path = os.path.join(output_dir, "audio.wav")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",           # 不处理视频
        "-acodec", "pcm_s16le",
        "-ar", "16000",  # Whisper 最佳采样率
        "-ac", "1",      # 单声道
        "-y",            # 覆盖已有文件
        audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"音频提取失败: {result.stderr}")
    return audio_path


def transcribe_audio(audio_path: str, model_size: str = "base", language: str = "zh") -> dict:
    """
    使用 Whisper 进行语音转文字
    返回带时间戳的转录结果
    """
    try:
        import whisper
    except ImportError:
        raise ImportError("请安装 openai-whisper: pip install openai-whisper")

    model = whisper.load_model(model_size)
    result = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
        verbose=False
    )

    segments = []
    for seg in result.get("segments", []):
        segments.append({
            "start": round(seg["start"], 2),
            "end": round(seg["end"], 2),
            "text": seg["text"].strip(),
            "words": [
                {
                    "word": w.get("word", "").strip(),
                    "start": round(w.get("start", 0), 2),
                    "end": round(w.get("end", 0), 2)
                }
                for w in seg.get("words", [])
            ]
        })

    return {
        "language": result.get("language", "zh"),
        "full_text": result.get("text", "").strip(),
        "segments": segments
    }


def match_text_to_shots(keyframes: list[dict], transcript_segments: list[dict]) -> list[dict]:
    """
    将语音文案精准匹配到对应的镜头截图
    基于时间区间重叠来分配文案
    """
    storyboard = []

    for kf in keyframes:
        shot_start = kf["timestamp"]
        shot_end = shot_start + kf["duration"]

        # 找到时间上与该镜头重叠的所有语音片段
        matched_texts = []
        for seg in transcript_segments:
            seg_start = seg["start"]
            seg_end = seg["end"]

            # 计算重叠比例
            overlap_start = max(shot_start, seg_start)
            overlap_end = min(shot_end, seg_end)

            if overlap_end > overlap_start:
                matched_texts.append(seg["text"])

        # 合并文案
        combined_text = " ".join(matched_texts).strip()

        storyboard.append({
            "shot_index": kf["shot_index"],
            "frame_path": kf["frame_path"],
            "timestamp": kf["timestamp"],
            "duration": kf["duration"],
            "time_label": kf["time_label"],
            "narration": combined_text,
            "has_narration": len(combined_text) > 0
        })

    return storyboard


def generate_storyboard(
    video_path: str,
    keyframes: list[dict],
    output_dir: str,
    model_size: str = "base"
) -> dict:
    """
    完整的分镜脚本生成流程
    1. 提取音频
    2. 语音转文字
    3. 文案匹配到镜头
    """
    # 提取音频
    audio_path = extract_audio(video_path, output_dir)

    # 语音转文字
    transcript = transcribe_audio(audio_path, model_size)

    # 匹配文案到镜头
    storyboard = match_text_to_shots(keyframes, transcript["segments"])

    result = {
        "transcript": transcript,
        "storyboard": storyboard,
        "total_shots": len(storyboard),
        "coverage_rate": round(
            sum(1 for s in storyboard if s["has_narration"]) / max(len(storyboard), 1) * 100, 1
        )
    }

    # 保存结果
    result_path = os.path.join(output_dir, "storyboard.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def format_storyboard_markdown(storyboard: list[dict]) -> str:
    """生成分镜脚本的 Markdown 格式文本"""
    lines = ["# 分镜脚本\n"]
    lines.append("| 镜头 | 时间点 | 时长 | 画面描述 | 台词/旁白 |")
    lines.append("|------|--------|------|----------|-----------|")

    for shot in storyboard:
        narration = shot["narration"] if shot["narration"] else "（无语音）"
        lines.append(
            f"| 镜头{shot['shot_index']} "
            f"| {shot['time_label']} "
            f"| {shot['duration']}s "
            f"| *(待填写)* "
            f"| {narration} |"
        )

    return "\n".join(lines)
