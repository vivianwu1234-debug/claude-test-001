"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { Camera, FileText, BarChart2, Sparkles, Download, ArrowLeft, Star } from "lucide-react";
import { getResult, FullResult, getShotLabel, SHOT_TYPE_COLORS, formatTime } from "@/lib/api";
import ShotGrid from "@/components/ShotGrid";
import StoryboardTab from "@/components/StoryboardTab";
import ScriptAnalysisTab from "@/components/ScriptAnalysisTab";
import AIGenerationTab from "@/components/AIGenerationTab";

const TABS = [
  { id: "shots", label: "镜头截图", icon: Camera },
  { id: "storyboard", label: "分镜脚本", icon: FileText },
  { id: "analysis", label: "脚本结构分析", icon: BarChart2 },
  { id: "generation", label: "AI 视频生成", icon: Sparkles },
  { id: "export", label: "导出报告", icon: Download },
];

const METRIC_HINTS: Record<string, string> = {
  product_first_appear: "黄金3秒内出现最佳",
  product_exposure: "建议占比30%以上",
  product_exposure_ratio: "高转化视频建议40%+",
  total_duration: "短视频15-60秒最佳",
  total_shots: "平均2-3秒/镜头",
};

export default function AnalysisPage() {
  const router = useRouter();
  const params = useParams();
  const taskId = params.id as string;

  const [result, setResult] = useState<FullResult | null>(null);
  const [activeTab, setActiveTab] = useState("shots");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!taskId) return;
    getResult(taskId)
      .then((r) => { setResult(r); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [taskId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-accent-purple border-t-transparent rounded-full spin" />
          <p className="text-text-secondary text-sm">加载分析结果...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <p className="text-accent-red mb-4">{error || "结果加载失败"}</p>
          <button onClick={() => router.push("/")} className="btn-gradient px-4 py-2 rounded-lg text-white text-sm">
            重新上传
          </button>
        </div>
      </div>
    );
  }

  const { shot_result, storyboard_result, analysis_result, metrics } = result;
  const videoName = shot_result?.video_name || "视频分析";
  const overall = analysis_result?.analysis?.overall_assessment;
  const tagged = analysis_result?.tagged_storyboard || storyboard_result?.storyboard || [];

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-20 flex items-center gap-3 px-6 py-3 border-b border-bg-border bg-bg-primary/90 backdrop-blur">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-accent-purple to-accent-blue flex items-center justify-center flex-shrink-0">
          <Camera className="w-3.5 h-3.5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs text-text-secondary">爆款短视频拆解工具</p>
          <p className="text-xs text-text-muted truncate">分析报告 · {videoName}</p>
        </div>
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-1.5 text-xs text-text-secondary hover:text-text-primary transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          重新分析
        </button>
      </header>

      <div className="flex-1 px-4 md:px-8 py-6 max-w-7xl mx-auto w-full">
        {/* Metrics Cards */}
        {metrics && (
          <>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-4">
              <MetricCard
                value={`${metrics.product_first_appear}秒`}
                label="产品首次出现"
                hint={METRIC_HINTS.product_first_appear}
                color="text-accent-orange"
                warn={metrics.product_first_appear > 5}
              />
              <MetricCard
                value={`${metrics.product_exposure}秒`}
                label="产品露出时长"
                hint={METRIC_HINTS.product_exposure}
                color="text-accent-blue"
                warn={metrics.product_exposure_ratio < 30}
              />
              <MetricCard
                value={`${metrics.product_exposure_ratio}%`}
                label="产品露出占比"
                hint={METRIC_HINTS.product_exposure_ratio}
                color="text-accent-cyan"
                warn={metrics.product_exposure_ratio < 40}
              />
              <MetricCard
                value={`${metrics.total_duration}秒`}
                label="视频总时长"
                hint={METRIC_HINTS.total_duration}
                color="text-accent-purple"
                warn={metrics.total_duration > 60}
              />
              <MetricCard
                value={`${metrics.total_shots}个`}
                label="镜头数量"
                hint={METRIC_HINTS.total_shots}
                color="text-text-primary"
                warn={false}
              />
            </div>

            {/* Suggestion Banner */}
            {metrics.suggestions?.[0] && (
              <div className="flex items-center gap-2.5 px-4 py-3 rounded-xl bg-accent-yellow/5 border border-accent-yellow/20 mb-5">
                <span className="text-accent-yellow text-sm">💡</span>
                <p className="text-accent-yellow/90 text-sm">{metrics.suggestions[0]}</p>
              </div>
            )}
          </>
        )}

        {/* Tabs */}
        <div className="flex items-center gap-1 border-b border-bg-border mb-6 overflow-x-auto">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              className={`flex items-center gap-1.5 px-3 py-2.5 text-sm whitespace-nowrap transition-colors relative ${
                activeTab === id
                  ? "text-text-primary tab-active font-medium"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
              {id === "generation" && (
                <span className="text-xs bg-accent-purple/20 text-accent-purple px-1.5 py-0.5 rounded-full ml-1">
                  Beta
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="fade-in">
          {activeTab === "shots" && (
            <ShotGrid
              tagged={tagged}
              videoInfo={shot_result?.video_info}
              taskId={taskId}
            />
          )}

          {activeTab === "storyboard" && (
            <StoryboardTab storyboardResult={storyboard_result} />
          )}

          {activeTab === "analysis" && (
            <ScriptAnalysisTab
              analysisResult={analysis_result}
              tagged={tagged}
              taskId={taskId}
            />
          )}

          {activeTab === "generation" && (
            <AIGenerationTab
              taskId={taskId}
              analysisResult={analysis_result}
              existingGeneration={result.generation_result}
              onGenerated={(gen) => setResult({ ...result, generation_result: gen })}
            />
          )}

          {activeTab === "export" && (
            <ExportTab taskId={taskId} videoName={videoName} />
          )}
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  value, label, hint, color, warn
}: {
  value: string; label: string; hint: string; color: string; warn: boolean;
}) {
  return (
    <div className={`bg-bg-card rounded-xl p-4 border ${warn ? "border-accent-orange/30" : "border-bg-border"}`}>
      <p className={`text-2xl font-bold ${warn ? "text-accent-orange" : color}`}>{value}</p>
      <p className="text-text-secondary text-xs mt-1">{label}</p>
      <p className="text-text-muted text-xs mt-2 leading-relaxed">{hint}</p>
    </div>
  );
}

function ExportTab({ taskId, videoName }: { taskId: string; videoName: string }) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch("/api/library/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: taskId, category: "其他", platform: "抖音", tags: [] })
      });
      setSaved(true);
    } catch (e) {
      console.error(e);
    }
    setSaving(false);
  };

  return (
    <div className="max-w-2xl space-y-4">
      <h3 className="text-text-primary font-semibold text-lg">导出报告</h3>
      <p className="text-text-secondary text-sm">下载完整的视频拆解分析报告</p>

      <div className="grid grid-cols-2 gap-3">
        <a
          href={`/api/report/${taskId}?fmt=html`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 p-4 bg-bg-card border border-bg-border rounded-xl hover:border-accent-purple/50 transition-colors group"
        >
          <div className="w-10 h-10 rounded-lg bg-accent-purple/10 flex items-center justify-center group-hover:bg-accent-purple/20 transition-colors">
            <Download className="w-5 h-5 text-accent-purple" />
          </div>
          <div>
            <p className="text-text-primary text-sm font-medium">HTML 报告</p>
            <p className="text-text-secondary text-xs">可视化完整报告</p>
          </div>
        </a>

        <a
          href={`/api/report/${taskId}?fmt=md`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-3 p-4 bg-bg-card border border-bg-border rounded-xl hover:border-accent-blue/50 transition-colors group"
        >
          <div className="w-10 h-10 rounded-lg bg-accent-blue/10 flex items-center justify-center group-hover:bg-accent-blue/20 transition-colors">
            <FileText className="w-5 h-5 text-accent-blue" />
          </div>
          <div>
            <p className="text-text-primary text-sm font-medium">Markdown 报告</p>
            <p className="text-text-secondary text-xs">文字版分析结果</p>
          </div>
        </a>
      </div>

      <div className="border-t border-bg-border pt-4">
        <button
          onClick={handleSave}
          disabled={saving || saved}
          className="btn-gradient px-5 py-2.5 rounded-lg text-white text-sm font-medium disabled:opacity-50"
        >
          {saved ? "✅ 已保存到素材库" : saving ? "保存中..." : "💾 保存到素材库"}
        </button>
      </div>
    </div>
  );
}
