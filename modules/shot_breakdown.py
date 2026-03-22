"""
镜头拆解模块
- 自动识别爆款视频的转场
- 抓取封面及每个镜头关键帧
"""

import os
import cv2
import numpy as np
from pathlib import Path
from PIL import Image
import json
import time


def extract_cover(video_path: str, output_dir: str) -> str:
    """提取视频封面（第一帧）"""
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise ValueError(f"无法读取视频: {video_path}")

    cover_path = os.path.join(output_dir, "cover.jpg")
    cv2.imwrite(cover_path, frame)
    return cover_path


def detect_scene_changes(video_path: str, threshold: float = 30.0) -> list[dict]:
    """
    基于帧差法检测场景切换点
    threshold: 帧差阈值，越小越敏感
    返回: [{"frame_idx": int, "timestamp": float, "score": float}]
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    scene_changes = []
    prev_gray = None
    frame_idx = 0

    # 添加第一帧作为起始场景
    scene_changes.append({
        "frame_idx": 0,
        "timestamp": 0.0,
        "score": 0.0
    })

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_gray is not None:
            diff = cv2.absdiff(gray, prev_gray)
            score = float(np.mean(diff))

            if score > threshold:
                timestamp = frame_idx / fps
                scene_changes.append({
                    "frame_idx": frame_idx,
                    "timestamp": round(timestamp, 2),
                    "score": round(score, 2)
                })

        prev_gray = gray
        frame_idx += 1

    cap.release()

    # 过滤过于密集的切换点（间隔小于0.5秒的合并）
    filtered = [scene_changes[0]]
    for sc in scene_changes[1:]:
        if sc["timestamp"] - filtered[-1]["timestamp"] > 0.5:
            filtered.append(sc)

    return filtered


def extract_keyframes(video_path: str, scene_changes: list[dict], output_dir: str) -> list[dict]:
    """
    从每个场景切换点提取关键帧
    返回包含帧图片路径和时间戳的列表
    """
    os.makedirs(output_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    keyframes = []

    for i, sc in enumerate(scene_changes):
        frame_idx = sc["frame_idx"]
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()

        if not ret:
            continue

        frame_path = os.path.join(output_dir, f"keyframe_{i:03d}.jpg")
        cv2.imwrite(frame_path, frame)

        # 计算该镜头时长
        if i + 1 < len(scene_changes):
            shot_duration = round(scene_changes[i + 1]["timestamp"] - sc["timestamp"], 2)
        else:
            shot_duration = round(duration - sc["timestamp"], 2)

        keyframes.append({
            "shot_index": i + 1,
            "frame_path": frame_path,
            "timestamp": sc["timestamp"],
            "duration": shot_duration,
            "score": sc["score"],
            "time_label": format_time(sc["timestamp"])
        })

    cap.release()
    return keyframes


def format_time(seconds: float) -> str:
    """将秒数格式化为 MM:SS.ms"""
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:05.2f}"


def get_video_info(video_path: str) -> dict:
    """获取视频基本信息"""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = total_frames / fps if fps > 0 else 0
    cap.release()

    return {
        "fps": round(fps, 2),
        "total_frames": total_frames,
        "width": width,
        "height": height,
        "duration": round(duration, 2),
        "duration_label": format_time(duration),
        "resolution": f"{width}x{height}",
        "aspect_ratio": "9:16" if height > width else "16:9"
    }


def analyze_shots(video_path: str, output_dir: str, threshold: float = 30.0) -> dict:
    """
    完整的镜头拆解分析
    返回包含封面、镜头信息的完整结果
    """
    video_name = Path(video_path).stem
    shot_dir = os.path.join(output_dir, "keyframes")
    os.makedirs(shot_dir, exist_ok=True)

    # 获取视频信息
    video_info = get_video_info(video_path)

    # 提取封面
    cover_path = extract_cover(video_path, output_dir)

    # 检测场景切换
    scene_changes = detect_scene_changes(video_path, threshold)

    # 提取关键帧
    keyframes = extract_keyframes(video_path, scene_changes, shot_dir)

    result = {
        "video_name": video_name,
        "video_path": video_path,
        "cover_path": cover_path,
        "video_info": video_info,
        "total_shots": len(keyframes),
        "keyframes": keyframes,
        "scene_changes": scene_changes
    }

    # 保存结果
    result_path = os.path.join(output_dir, "shot_analysis.json")
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result
