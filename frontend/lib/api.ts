const API_BASE = "/api";

export interface UploadResult {
  task_id: string;
  filename: string;
  size_mb: number;
  status: string;
}

export interface TaskStatus {
  status: string;
  step: string;
  progress: { upload: number; analysis: number };
  error?: string;
  gen_status?: string;
}

export interface Metrics {
  product_first_appear: number;
  product_exposure: number;
  product_exposure_ratio: number;
  total_duration: number;
  total_shots: number;
  avg_shot_duration: number;
  suggestions: string[];
}

export interface Keyframe {
  shot_index: number;
  frame_path: string;
  timestamp: number;
  duration: number;
  time_label: string;
  score: number;
}

export interface ShotResult {
  video_name: string;
  cover_path: string;
  video_info: {
    fps: number;
    total_frames: number;
    width: number;
    height: number;
    duration: number;
    duration_label: string;
    resolution: string;
    aspect_ratio: string;
  };
  total_shots: number;
  keyframes: Keyframe[];
}

export interface StoryboardShot {
  shot_index: number;
  frame_path: string;
  timestamp: number;
  duration: number;
  time_label: string;
  narration: string;
  has_narration: boolean;
  structure_tag?: string;
  structure_color?: string;
}

export interface StoryboardResult {
  transcript: { language: string; full_text: string };
  storyboard: StoryboardShot[];
  total_shots: number;
  coverage_rate: number;
}

export interface AnalysisResult {
  analysis: {
    hook?: { type: string; text: string; score: number; effectiveness: string; shot_range: string };
    body?: { type: string; text: string; score: number; value_delivered: string; key_points: string[]; shot_range: string };
    cta?: { type: string; text: string; score: number; urgency_level: string; shot_range: string };
    viral_elements?: { emotion_trigger: string; conflict: string; surprise_factor: string; relatability: string };
    overall_assessment?: { total_score: number; strengths: string[]; weaknesses: string[]; optimization_suggestions: string[] };
    replication_blueprint?: { hook_template: string; body_structure: string; cta_template: string; key_success_factors: string[] };
    parse_error?: boolean;
  };
  tagged_storyboard: StoryboardShot[];
}

export interface GenerationPlan {
  video_concept?: { title: string; core_message: string; target_audience: string; emotional_tone: string };
  new_script?: {
    hook: { narration: string; visual_description: string; duration_seconds: number };
    body: Array<{ shot_number: number; narration: string; visual_description: string; camera_angle: string; ai_image_prompt: string; duration_seconds: number }>;
    cta: { narration: string; visual_description: string; duration_seconds: number };
  };
  jimeng_video_prompts?: Array<{ scene: string; prompt_zh: string; prompt_en: string; duration: string }>;
  production_notes?: { total_duration: string; music_style: string; color_palette: string; editing_rhythm: string; shooting_tips: string[] };
}

export interface FullResult {
  shot_result: ShotResult;
  storyboard_result: StoryboardResult;
  analysis_result: AnalysisResult;
  metrics: Metrics;
  generation_result: { product_name: string; product_info: string; generation_plan: GenerationPlan } | null;
}

// 上传视频
export async function uploadVideo(file: File): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// 启动分析
export async function startAnalysis(params: {
  task_id: string;
  whisper_model?: string;
  language?: string;
  threshold?: number;
  anthropic_api_key?: string;
}): Promise<void> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(await res.text());
}

// 轮询状态
export async function getStatus(task_id: string): Promise<TaskStatus & Partial<FullResult>> {
  const res = await fetch(`${API_BASE}/status/${task_id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// 获取完整结果
export async function getResult(task_id: string): Promise<FullResult> {
  const res = await fetch(`${API_BASE}/result/${task_id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// 启动 AI 生成
export async function startGeneration(params: {
  task_id: string;
  product_name: string;
  product_description: string;
  model?: string;
  aspect_ratio?: string;
  anthropic_api_key?: string;
  jimeng_api_key?: string;
}): Promise<void> {
  const res = await fetch(`${API_BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(await res.text());
}

// 保存到素材库
export async function saveToLibrary(params: {
  task_id: string;
  category?: string;
  platform?: string;
  tags?: string[];
}): Promise<void> {
  const res = await fetch(`${API_BASE}/library/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(await res.text());
}

// 格式化秒数
export function formatTime(seconds: number): string {
  if (!seconds) return "0.0s";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const m = Math.floor(seconds / 60);
  const s = (seconds % 60).toFixed(0).padStart(2, "0");
  return `${m}:${s}`;
}

// 镜头类型颜色映射
export const SHOT_TYPE_COLORS: Record<string, { bg: string; text: string; bar: string }> = {
  "痛点放大": { bg: "bg-pink-500/20", text: "text-pink-400", bar: "#f72585" },
  "产品展示": { bg: "bg-orange-500/20", text: "text-orange-400", bar: "#ff9f0a" },
  "使用场景": { bg: "bg-blue-500/20", text: "text-blue-400", bar: "#4f9cf9" },
  "细节特写": { bg: "bg-purple-500/20", text: "text-purple-400", bar: "#7c6ff7" },
  "行动引导": { bg: "bg-green-500/20", text: "text-green-400", bar: "#00c896" },
  "情感共鸣": { bg: "bg-cyan-500/20", text: "text-cyan-400", bar: "#00d2ff" },
  "Hook": { bg: "bg-pink-500/20", text: "text-pink-400", bar: "#f72585" },
  "Body": { bg: "bg-blue-500/20", text: "text-blue-400", bar: "#4f9cf9" },
  "CTA": { bg: "bg-green-500/20", text: "text-green-400", bar: "#00c896" },
};

// 从 structure_tag 推断显示标签
export function getShotLabel(shot: StoryboardShot, index: number, total: number): string {
  const tag = shot.structure_tag || "";
  if (tag.includes("Hook")) return "痛点放大";
  if (tag.includes("CTA")) return "行动引导";
  const ratio = index / total;
  if (ratio < 0.3) return "痛点放大";
  if (ratio < 0.5) return "产品展示";
  if (ratio < 0.7) return "使用场景";
  if (ratio < 0.85) return "细节特写";
  return "行动引导";
}
