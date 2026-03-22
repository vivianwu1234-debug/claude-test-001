"use client";

import { useState } from "react";
import { Sparkles, Copy, Check } from "lucide-react";
import { AnalysisResult } from "@/lib/api";

interface Props {
  taskId: string;
  analysisResult: AnalysisResult;
  existingGeneration: any;
  onGenerated: (gen: any) => void;
}

const MODELS = [
  { id: "kie-veo3-fast", name: "Kie.ai Veo3.1", sub: "Kie.ai Veo3.1（快速版）", badge: "推荐", price: "~¥0.30/5秒", color: "border-accent-purple/50 bg-accent-purple/5" },
  { id: "kie-veo3-quality", name: "Kie.ai Veo3.1", sub: "Kie.ai Veo3.1（质量）", badge: null, price: "~¥0.50/5秒", color: "border-bg-border" },
];

const FORMATS = [
  { id: "9:16", label: "竖屏 9:16", sub: "TikTok/Shorts" },
  { id: "16:9", label: "横屏 16:9", sub: "YouTube" },
];

export default function AIGenerationTab({ taskId, analysisResult, existingGeneration, onGenerated }: Props) {
  const [productName, setProductName] = useState(existingGeneration?.product_name || "");
  const [productDesc, setProductDesc] = useState("");
  const [selectedModel, setSelectedModel] = useState("kie-veo3-fast");
  const [selectedFormat, setSelectedFormat] = useState("9:16");
  const [generating, setGenerating] = useState(false);
  const [genResult, setGenResult] = useState<any>(existingGeneration);
  const [editingPrompt, setEditingPrompt] = useState(false);
  const [customPrompt, setCustomPrompt] = useState("");
  const [copied, setCopied] = useState<string | null>(null);

  const plan = genResult?.generation_plan;
  const jimengPrompts = plan?.jimeng_video_prompts || [];
  const script = plan?.new_script;
  const notes = plan?.production_notes;

  const handleGenerate = async () => {
    if (!productName.trim()) return;
    setGenerating(true);

    try {
      const apiKey = localStorage.getItem("anthropic_key") || "";
      await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: taskId,
          product_name: productName,
          product_description: productDesc || `产品名称：${productName}`,
          model: selectedModel,
          aspect_ratio: selectedFormat,
          anthropic_api_key: apiKey,
        }),
      });

      const poll = setInterval(async () => {
        const res = await fetch(`/api/status/${taskId}`);
        const status = await res.json();
        if (status.gen_status === "done") {
          clearInterval(poll);
          const resultRes = await fetch(`/api/result/${taskId}`);
          const result = await resultRes.json();
          setGenResult(result.generation_result);
          onGenerated(result.generation_result);
          setGenerating(false);
        } else if (status.gen_status === "error") {
          clearInterval(poll);
          setGenerating(false);
        }
      }, 2000);
    } catch {
      setGenerating(false);
    }
  };

  const copyText = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  // 生成完整提示词文本
  const fullPromptText = jimengPrompts.map((p: any) =>
    `## ${p.scene}\n${p.prompt_en}\n\n${p.prompt_zh}`
  ).join("\n\n---\n\n");

  return (
    <div>
      {/* 标题 */}
      <div className="flex items-center gap-3 mb-6">
        <Sparkles className="w-5 h-5 text-accent-purple" />
        <h3 className="text-text-primary font-semibold text-lg">AI 生成短视频</h3>
        <span className="text-xs bg-bg-card border border-bg-border text-text-secondary px-2 py-1 rounded-full">
          Powered by Fal.ai &nbsp; 由 Fal.ai 提供技术支持
        </span>
      </div>

      {/* 产品输入 */}
      <div className="bg-bg-card rounded-xl border border-bg-border p-4 mb-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-accent-green text-sm">✓</span>
          <span className="text-text-primary text-sm font-medium">
            {genResult ? `已改编脚本：${genResult.product_name}` : "输入你的产品信息"}
          </span>
        </div>

        <div className="space-y-3">
          <input
            value={productName}
            onChange={(e) => setProductName(e.target.value)}
            placeholder="产品名称，如：猫咪自动饮水机"
            className="w-full px-3 py-2.5 rounded-lg bg-bg-secondary border border-bg-border text-text-primary placeholder-text-muted text-sm focus:outline-none focus:border-accent-purple/50"
          />
          <textarea
            value={productDesc}
            onChange={(e) => setProductDesc(e.target.value)}
            placeholder="产品描述（可选）：核心卖点、目标用户、价格区间..."
            rows={3}
            className="w-full px-3 py-2.5 rounded-lg bg-bg-secondary border border-bg-border text-text-primary placeholder-text-muted text-sm focus:outline-none focus:border-accent-purple/50 resize-none"
          />
        </div>

        {/* 分镜预览 */}
        {genResult && jimengPrompts.length > 0 && (
          <div className="mt-4 space-y-2">
            {jimengPrompts.slice(0, 2).map((p: any, i: number) => (
              <div key={i} className="flex gap-3">
                <div className="flex-1 bg-bg-secondary rounded-lg p-3">
                  <p className="text-text-secondary text-xs leading-relaxed line-clamp-2">{p.prompt_en}</p>
                  <p className="text-text-muted text-xs mt-1 line-clamp-1">{p.prompt_zh}</p>
                </div>
                {i === 1 && jimengPrompts.length > 2 && (
                  <div className="flex-1 bg-bg-secondary rounded-lg p-3">
                    <p className="text-text-secondary text-xs leading-relaxed line-clamp-2">
                      {jimengPrompts[2]?.prompt_en}
                    </p>
                    <p className="text-text-muted text-xs mt-1 line-clamp-1">
                      {jimengPrompts[2]?.prompt_zh}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* 左侧：提示词编辑器 */}
        <div className="bg-bg-card rounded-xl border border-bg-border overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-bg-border">
            <span className="text-text-secondary text-sm">视频生成提示词</span>
            <button
              onClick={() => setEditingPrompt(!editingPrompt)}
              className="flex items-center gap-1 text-xs text-accent-purple hover:text-accent-blue transition-colors"
            >
              ✏️ {editingPrompt ? "完成编辑" : "完成编辑"}
            </button>
          </div>

          <div className="p-4 max-h-96 overflow-y-auto">
            {plan ? (
              <div className="space-y-4 text-sm font-mono">
                {/* Video Style */}
                {notes && (
                  <div>
                    <p className="text-accent-blue">## Video Style</p>
                    <p className="text-text-secondary">- Modern, sleek, eye-catching visuals</p>
                    <p className="text-text-secondary">- Professional lighting and composition</p>
                    <p className="text-text-secondary">- Dynamic camera movements and smooth transitions</p>
                    <p className="text-text-secondary">- Fast-paced editing suitable for social media</p>
                    {notes.color_palette && (
                      <p className="text-text-secondary">- Color palette: {notes.color_palette}</p>
                    )}
                  </div>
                )}

                {/* Audio */}
                {notes?.music_style && (
                  <div>
                    <p className="text-accent-blue">## Audio Requirements</p>
                    <p className="text-text-secondary">- Background music: {notes.music_style}</p>
                    <p className="text-text-secondary">- Voiceover: Professional clear and engaging</p>
                  </div>
                )}

                {/* Scene Breakdown */}
                <div>
                  <p className="text-accent-blue">## Scene Breakdown</p>
                  {script?.hook && (
                    <div className="mt-2">
                      <p className="text-accent-pink">Scene 1 (Hook/Pain):</p>
                      <p className="text-text-secondary pl-2">{script.hook.visual_description}</p>
                      <p className="text-text-muted pl-2 text-xs">  - Voiceover: "{script.hook.narration}"</p>
                    </div>
                  )}
                  {script?.body?.map((s: any, i: number) => (
                    <div key={i} className="mt-2">
                      <p className="text-accent-orange">Scene {i + 2} ({s.camera_angle}):</p>
                      <p className="text-text-secondary pl-2">{s.visual_description}</p>
                      <p className="text-text-muted pl-2 text-xs">  - Voiceover: "{s.narration}"</p>
                    </div>
                  ))}
                  {script?.cta && (
                    <div className="mt-2">
                      <p className="text-accent-green">Scene {(script?.body?.length || 0) + 2} (CTA):</p>
                      <p className="text-text-secondary pl-2">{script.cta.visual_description}</p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-text-muted text-sm space-y-2">
                <p className="text-accent-blue">## Video Style</p>
                <p>- Modern, sleek, eye-catching visuals</p>
                <p>- Professional lighting and composition</p>
                <p>- Dynamic camera movements and smooth transitions</p>
                <p className="mt-4 text-accent-blue">## Audio Requirements</p>
                <p>- Background music: Upbeat, modern</p>
                <p>- Voiceover: Professional voice</p>
                <p className="mt-4 text-accent-blue">## Scene Breakdown</p>
                <p className="text-text-muted italic">← 填写产品信息后自动生成</p>
              </div>
            )}
          </div>
        </div>

        {/* 右侧：模型选择 + 格式 + 生成按钮 */}
        <div className="space-y-4">
          {/* 模型选择 */}
          <div>
            <p className="text-text-secondary text-sm mb-3">选择模型</p>
            <div className="space-y-2">
              {MODELS.map((m) => (
                <label
                  key={m.id}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors ${
                    selectedModel === m.id ? m.color : "border-bg-border hover:border-bg-hover"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full border-2 ${
                      selectedModel === m.id ? "border-accent-purple bg-accent-purple" : "border-text-muted"
                    }`} />
                    <input
                      type="radio"
                      name="model"
                      value={m.id}
                      checked={selectedModel === m.id}
                      onChange={() => setSelectedModel(m.id)}
                      className="hidden"
                    />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-text-primary text-sm font-medium">{m.name}</span>
                      {m.badge && (
                        <span className="text-xs bg-accent-purple/20 text-accent-purple px-1.5 py-0.5 rounded-full">
                          {m.badge}
                        </span>
                      )}
                    </div>
                    <p className="text-text-muted text-xs">{m.sub}</p>
                  </div>
                  <span className="text-text-muted text-xs">{m.price}</span>
                </label>
              ))}
            </div>
            <p className="text-text-secondary text-xs mt-2 flex items-center gap-1">
              🎵 所有模型均支持 AI 配音，自动生成英文语音
            </p>
          </div>

          {/* 视频格式 */}
          <div>
            <p className="text-text-secondary text-sm mb-3">视频格式</p>
            <div className="flex gap-2">
              {FORMATS.map((f) => (
                <button
                  key={f.id}
                  onClick={() => setSelectedFormat(f.id)}
                  className={`flex-1 flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm transition-colors ${
                    selectedFormat === f.id
                      ? "border-accent-purple bg-accent-purple/10 text-accent-purple"
                      : "border-bg-border text-text-secondary hover:border-bg-hover"
                  }`}
                >
                  <div className={`w-2 h-2 rounded-full border ${
                    selectedFormat === f.id ? "border-accent-purple bg-accent-purple" : "border-text-muted"
                  }`} />
                  <div>
                    <p className="font-medium text-xs">{f.label}</p>
                    <p className="text-text-muted text-xs">({f.sub})</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* 生成按钮 */}
          <button
            onClick={handleGenerate}
            disabled={generating || !productName.trim()}
            className="w-full btn-gradient py-3.5 rounded-xl text-white font-semibold text-base flex items-center justify-center gap-2 disabled:opacity-50 transition-all"
          >
            <Sparkles className="w-5 h-5" />
            {generating ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spin" />
                生成中...
              </span>
            ) : (
              `生成短视频 (Kie.ai Veo3.1)`
            )}
          </button>

          {/* 即梦提示词 */}
          {jimengPrompts.length > 0 && (
            <div className="bg-bg-card rounded-xl border border-bg-border p-3">
              <div className="flex items-center justify-between mb-2">
                <p className="text-text-secondary text-xs">即梦 AI 视频提示词</p>
                <button
                  onClick={() => copyText(fullPromptText, "all")}
                  className="flex items-center gap-1 text-xs text-text-muted hover:text-text-primary"
                >
                  {copied === "all" ? <Check className="w-3 h-3 text-accent-green" /> : <Copy className="w-3 h-3" />}
                  复制全部
                </button>
              </div>
              {jimengPrompts.slice(0, 2).map((p: any, i: number) => (
                <div key={i} className="mb-2">
                  <p className="text-accent-purple text-xs mb-1">{p.scene}</p>
                  <p className="text-text-muted text-xs leading-relaxed line-clamp-2">{p.prompt_en}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
