"use client";

import { useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Camera, BarChart2, FileText, RefreshCw } from "lucide-react";
import { uploadVideo, startAnalysis } from "@/lib/api";

const FEATURES = [
  {
    icon: Camera,
    title: "智能镜头拆解",
    desc: "自动识别场景切换，提取关键帧截图",
    color: "text-accent-purple",
    border: "border-accent-purple/30",
  },
  {
    icon: BarChart2,
    title: "数据指标分析",
    desc: "产品露出时长、首现时间等关键指标",
    color: "text-accent-blue",
    border: "border-accent-blue/30",
  },
  {
    icon: FileText,
    title: "分镜脚本生成",
    desc: "生成完整分镜表格，一键导出",
    color: "text-accent-cyan",
    border: "border-accent-cyan/30",
  },
  {
    icon: RefreshCw,
    title: "跨品类改编",
    desc: "智能改编脚本，适配不同产品",
    color: "text-accent-green",
    border: "border-accent-green/30",
  },
];

type Phase = "idle" | "uploading" | "analyzing" | "done";

export default function HomePage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);

  const [phase, setPhase] = useState<Phase>("idle");
  const [filename, setFilename] = useState("");
  const [sizeMb, setSizeMb] = useState(0);
  const [uploadPct, setUploadPct] = useState(0);
  const [analysisPct, setAnalysisPct] = useState(0);
  const [analysisLabel, setAnalysisLabel] = useState("准备中...");
  const [error, setError] = useState("");
  const [apiKey, setApiKey] = useState(
    typeof window !== "undefined" ? localStorage.getItem("anthropic_key") || "" : ""
  );

  const STEP_LABELS: Record<string, [number, string]> = {
    shot_breakdown: [20, "镜头拆解中..."],
    storyboard: [45, "语音转文字中..."],
    script_analysis: [70, "AI 结构分析中..."],
    metrics: [85, "计算指标中..."],
    report: [95, "生成报告中..."],
    done: [100, "分析完成！"],
  };

  const handleFile = useCallback(async (file: File) => {
    if (!file) return;
    setError("");
    setFilename(file.name);
    setSizeMb(parseFloat((file.size / 1024 / 1024).toFixed(2)));
    setPhase("uploading");
    setUploadPct(0);
    setAnalysisPct(0);

    // 模拟上传进度
    const uploadTimer = setInterval(() => {
      setUploadPct((p) => {
        if (p >= 90) { clearInterval(uploadTimer); return 90; }
        return p + 10;
      });
    }, 100);

    try {
      const result = await uploadVideo(file);
      clearInterval(uploadTimer);
      setUploadPct(100);

      if (apiKey) localStorage.setItem("anthropic_key", apiKey);

      // 启动分析
      setPhase("analyzing");
      setAnalysisLabel("爆品内容拆解中...");
      await startAnalysis({
        task_id: result.task_id,
        whisper_model: "base",
        language: "zh",
        threshold: 30,
        anthropic_api_key: apiKey,
      });

      // 轮询状态
      const poll = setInterval(async () => {
        try {
          const res = await fetch(`/api/status/${result.task_id}`);
          const status = await res.json();

          if (status.step && STEP_LABELS[status.step]) {
            const [pct, label] = STEP_LABELS[status.step];
            setAnalysisPct(pct);
            setAnalysisLabel(label);
          }

          if (status.status === "done") {
            clearInterval(poll);
            setAnalysisPct(100);
            setPhase("done");
            setTimeout(() => router.push(`/analysis/${result.task_id}`), 600);
          } else if (status.status === "error") {
            clearInterval(poll);
            setError(status.error || "分析失败，请重试");
            setPhase("idle");
          }
        } catch {
          // 忽略轮询网络错误
        }
      }, 1500);

    } catch (e: any) {
      clearInterval(uploadTimer);
      setError(e.message || "上传失败");
      setPhase("idle");
    }
  }, [apiKey, router]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, [handleFile]);

  const isProcessing = phase === "uploading" || phase === "analyzing";

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Header */}
      <header className="flex items-center gap-3 px-6 py-4 border-b border-bg-border">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-purple to-accent-blue flex items-center justify-center">
          <Camera className="w-4 h-4 text-white" />
        </div>
        <div>
          <h1 className="text-sm font-semibold text-text-primary">爆款短视频拆解工具</h1>
          <p className="text-xs text-text-secondary">AI驱动的视频结构分析</p>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center px-4 py-12 gap-8">
        {/* API Key input */}
        {!isProcessing && (
          <div className="w-full max-w-2xl">
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="输入 Anthropic API Key（用于 AI 结构分析）"
              className="w-full px-4 py-2.5 rounded-lg bg-bg-card border border-bg-border text-text-primary placeholder-text-muted text-sm focus:outline-none focus:border-accent-purple/50 transition-colors"
            />
          </div>
        )}

        {/* Upload / Loading Card */}
        <div
          className={`w-full max-w-2xl rounded-2xl border-2 transition-all ${
            isProcessing
              ? "border-bg-border bg-bg-card"
              : "border-dashed border-bg-border hover:border-accent-purple/50 bg-bg-card cursor-pointer"
          }`}
          onDragOver={(e) => e.preventDefault()}
          onDrop={onDrop}
          onClick={() => !isProcessing && fileRef.current?.click()}
        >
          {!isProcessing ? (
            <div className="flex flex-col items-center gap-4 py-16 px-8">
              <div className="w-16 h-16 rounded-full bg-accent-purple/10 border border-accent-purple/20 flex items-center justify-center">
                <Camera className="w-7 h-7 text-accent-purple" />
              </div>
              <div className="text-center">
                <p className="text-text-primary font-medium">拖拽视频文件到此处</p>
                <p className="text-text-secondary text-sm mt-1">或点击选择文件 · 支持 MP4、MOV、AVI</p>
              </div>
              <button className="btn-gradient px-6 py-2.5 rounded-lg text-white text-sm font-medium">
                选择视频文件
              </button>
              {error && (
                <p className="text-accent-red text-sm">{error}</p>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center gap-6 py-12 px-8">
              {/* 旋转加载圈 */}
              <div className="relative w-20 h-20">
                <svg className="w-20 h-20 spin" viewBox="0 0 80 80">
                  <circle cx="40" cy="40" r="34" fill="none" stroke="#2a2f45" strokeWidth="4" />
                  <circle
                    cx="40" cy="40" r="34" fill="none"
                    stroke="url(#grad)" strokeWidth="4"
                    strokeLinecap="round"
                    strokeDasharray="180 36"
                  />
                  <defs>
                    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor="#7c6ff7" />
                      <stop offset="100%" stopColor="#00d2ff" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>

              <div className="text-center">
                <p className="text-text-primary font-medium text-lg">
                  {phase === "uploading" ? "正在上传视频..." : "正在分析视频..."}
                </p>
                <p className="text-text-secondary text-sm mt-1">
                  {phase === "uploading" ? "提取视频帧中，请稍候" : analysisLabel}
                </p>
              </div>

              {/* 进度条 */}
              <div className="w-full max-w-sm space-y-4">
                {/* 上传进度 */}
                <div>
                  <div className="flex justify-between text-xs text-text-secondary mb-1.5">
                    <span>上传进度</span>
                    <span className="text-accent-cyan font-medium">{uploadPct}%</span>
                  </div>
                  <div className="h-1.5 bg-bg-border rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{
                        width: `${uploadPct}%`,
                        background: "linear-gradient(90deg, #7c6ff7, #00d2ff)"
                      }}
                    />
                  </div>
                </div>

                {/* 分析进度 */}
                <div>
                  <div className="flex justify-between text-xs text-text-secondary mb-1.5">
                    <span>爆品内容拆解</span>
                    <span className="text-accent-purple font-medium">
                      {phase === "uploading" ? "等待中..." : `${analysisPct}%`}
                    </span>
                  </div>
                  <div className="h-1.5 bg-bg-border rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${analysisPct}%`,
                        background: "linear-gradient(90deg, #f72585, #7c6ff7)"
                      }}
                    />
                  </div>
                </div>
              </div>

              {filename && (
                <p className="text-text-muted text-xs">
                  {filename} ({sizeMb} MB)
                </p>
              )}
            </div>
          )}
        </div>

        {/* Feature Cards */}
        {!isProcessing && (
          <div className="w-full max-w-2xl grid grid-cols-2 gap-3 fade-in">
            {FEATURES.map(({ icon: Icon, title, desc, color, border }) => (
              <div
                key={title}
                className={`bg-bg-card border ${border} rounded-xl p-4 flex items-start gap-3`}
              >
                <div className={`mt-0.5 ${color}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-text-primary text-sm font-medium">{title}</p>
                  <p className="text-text-secondary text-xs mt-0.5">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        <input
          ref={fileRef}
          type="file"
          accept=".mp4,.mov,.avi,.mkv"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
      </main>
    </div>
  );
}
