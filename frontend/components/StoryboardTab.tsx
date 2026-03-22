"use client";

import { useState } from "react";
import { StoryboardResult, getShotLabel, SHOT_TYPE_COLORS } from "@/lib/api";
import { Copy, Check } from "lucide-react";

interface Props {
  storyboardResult: StoryboardResult;
}

export default function StoryboardTab({ storyboardResult }: Props) {
  const [copied, setCopied] = useState(false);

  if (!storyboardResult) return <p className="text-text-secondary">暂无数据</p>;

  const { transcript, storyboard, coverage_rate } = storyboardResult;

  const copyAll = () => {
    const text = storyboard
      .map((s) => `[${s.time_label}] 镜头${s.shot_index}: ${s.narration || "（无台词）"}`)
      .join("\n");
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* 统计 */}
      <div className="flex items-center gap-6">
        <div>
          <p className="text-2xl font-bold text-text-primary">{storyboard.length}</p>
          <p className="text-text-secondary text-xs">分镜总数</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-accent-cyan">{coverage_rate}%</p>
          <p className="text-text-secondary text-xs">台词覆盖率</p>
        </div>
        <div>
          <p className="text-sm text-text-secondary">识别语言</p>
          <p className="text-text-primary text-sm">{transcript?.language === "zh" ? "中文" : transcript?.language}</p>
        </div>
        <button
          onClick={copyAll}
          className="ml-auto flex items-center gap-2 px-3 py-2 rounded-lg bg-bg-card border border-bg-border text-text-secondary hover:text-text-primary text-sm transition-colors"
        >
          {copied ? <Check className="w-4 h-4 text-accent-green" /> : <Copy className="w-4 h-4" />}
          {copied ? "已复制" : "复制全部"}
        </button>
      </div>

      {/* 完整台词 */}
      <div className="bg-bg-card rounded-xl border border-bg-border p-4">
        <p className="text-text-secondary text-xs mb-2">完整台词文稿</p>
        <p className="text-text-primary text-sm leading-relaxed">{transcript?.full_text || "（未识别到语音）"}</p>
      </div>

      {/* 分镜表格 */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-bg-border">
              <th className="text-left text-text-muted text-xs py-3 px-2 w-16">镜头</th>
              <th className="text-left text-text-muted text-xs py-3 px-2 w-20">截图</th>
              <th className="text-left text-text-muted text-xs py-3 px-2 w-24">时间点</th>
              <th className="text-left text-text-muted text-xs py-3 px-2 w-16">时长</th>
              <th className="text-left text-text-muted text-xs py-3 px-2 w-24">类型标签</th>
              <th className="text-left text-text-muted text-xs py-3 px-2">台词 / 旁白</th>
            </tr>
          </thead>
          <tbody>
            {storyboard.map((shot, i) => {
              const label = getShotLabel(shot, i, storyboard.length);
              const colors = SHOT_TYPE_COLORS[label] || SHOT_TYPE_COLORS["Body"];
              const imgSrc = shot.frame_path?.startsWith("/static")
                ? `http://localhost:8000${shot.frame_path}`
                : shot.frame_path;

              return (
                <tr key={shot.shot_index} className="border-b border-bg-border/50 hover:bg-bg-hover/30 transition-colors">
                  <td className="py-3 px-2">
                    <span className="text-text-secondary text-sm">#{shot.shot_index}</span>
                  </td>
                  <td className="py-3 px-2">
                    <div className="w-10 rounded overflow-hidden bg-bg-border" style={{ aspectRatio: "9/16" }}>
                      {imgSrc && (
                        <img src={imgSrc} alt="" className="w-full h-full object-cover"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }} />
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-2">
                    <span className="text-text-secondary text-xs font-mono">{shot.time_label}</span>
                  </td>
                  <td className="py-3 px-2">
                    <span className="text-text-secondary text-xs">{shot.duration}s</span>
                  </td>
                  <td className="py-3 px-2">
                    <span
                      className="text-xs px-2 py-1 rounded-full"
                      style={{ background: `${colors.bar}20`, color: colors.bar }}
                    >
                      {label}
                    </span>
                  </td>
                  <td className="py-3 px-2">
                    <p className="text-text-primary text-sm leading-relaxed">
                      {shot.narration || <span className="text-text-muted italic">（无台词）</span>}
                    </p>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
