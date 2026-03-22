"use client";

import { useState } from "react";
import { StoryboardShot, getShotLabel, SHOT_TYPE_COLORS } from "@/lib/api";
import { Play, Star } from "lucide-react";

interface Props {
  tagged: StoryboardShot[];
  videoInfo?: { duration: number; total_frames: number };
  taskId: string;
}

export default function ShotGrid({ tagged, videoInfo, taskId }: Props) {
  const [selected, setSelected] = useState<StoryboardShot | null>(null);

  const total = tagged.length;
  const duration = videoInfo?.duration || 1;

  // 计算每个镜头的类型标签
  const shots = tagged.map((shot, i) => ({
    ...shot,
    displayLabel: getShotLabel(shot, i, total),
  }));

  // 按标签分组，计算时间线颜色段
  const timelineSegments = shots.map((shot) => {
    const colors = SHOT_TYPE_COLORS[shot.displayLabel] || SHOT_TYPE_COLORS["Body"];
    return {
      label: shot.displayLabel,
      left: (shot.timestamp / duration) * 100,
      width: (shot.duration / duration) * 100,
      color: colors.bar,
    };
  });

  // 统计各类型
  const labelGroups: Record<string, { count: number; duration: number }> = {};
  shots.forEach((s) => {
    if (!labelGroups[s.displayLabel]) labelGroups[s.displayLabel] = { count: 0, duration: 0 };
    labelGroups[s.displayLabel].count++;
    labelGroups[s.displayLabel].duration += s.duration;
  });

  return (
    <div>
      {/* 镜头总览 */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Play className="w-4 h-4 text-text-secondary" />
          <h3 className="text-text-primary font-medium">
            全部镜头（{total}个分镜）
          </h3>
        </div>
        <div className="flex items-center gap-3 text-xs text-text-secondary">
          <span>点击镜头可放大查看</span>
          <span className="flex items-center gap-1 text-accent-orange">
            <Star className="w-3 h-3 fill-current" />
            产品首现
          </span>
        </div>
      </div>

      {/* 镜头类型标签行 */}
      <div className="mb-2 flex gap-2 overflow-x-auto pb-1">
        {Object.entries(labelGroups).map(([label, info]) => {
          const colors = SHOT_TYPE_COLORS[label] || SHOT_TYPE_COLORS["Body"];
          return (
            <div
              key={label}
              className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}
            >
              {label} ({info.count})
            </div>
          );
        })}
      </div>

      {/* 时间线分段标签 */}
      <div className="mb-2 flex overflow-x-auto gap-0">
        {(() => {
          // 合并连续相同标签的段
          const merged: Array<{ label: string; start: number; end: number }> = [];
          shots.forEach((s) => {
            if (merged.length > 0 && merged[merged.length - 1].label === s.displayLabel) {
              merged[merged.length - 1].end = s.timestamp + s.duration;
            } else {
              merged.push({ label: s.displayLabel, start: s.timestamp, end: s.timestamp + s.duration });
            }
          });
          return merged.map((seg, i) => {
            const colors = SHOT_TYPE_COLORS[seg.label] || SHOT_TYPE_COLORS["Body"];
            const w = ((seg.end - seg.start) / duration) * 100;
            return (
              <div
                key={i}
                className="flex-shrink-0 text-xs px-2 py-1 text-center truncate rounded-sm mx-px"
                style={{
                  width: `${Math.max(w, 8)}%`,
                  background: `${colors.bar}25`,
                  color: colors.bar,
                  border: `1px solid ${colors.bar}40`,
                  fontSize: "10px"
                }}
              >
                {seg.label} {seg.start.toFixed(1)}-{seg.end.toFixed(1)}s
              </div>
            );
          });
        })()}
      </div>

      {/* 镜头卡片网格 */}
      <div className="overflow-x-auto">
        <div className="flex gap-3 pb-3" style={{ minWidth: `${total * 140}px` }}>
          {shots.map((shot, i) => {
            const colors = SHOT_TYPE_COLORS[shot.displayLabel] || SHOT_TYPE_COLORS["Body"];
            const imgSrc = shot.frame_path?.startsWith("/static")
              ? `http://localhost:8000${shot.frame_path}`
              : shot.frame_path;

            return (
              <div
                key={shot.shot_index}
                className="flex-shrink-0 w-32 shot-card cursor-pointer"
                onClick={() => setSelected(shot)}
              >
                {/* 时间戳标签 */}
                <div className="flex justify-between text-xs text-text-muted mb-1 px-0.5">
                  <span>#{shot.shot_index}</span>
                  <span>{shot.timestamp.toFixed(1)}s</span>
                </div>

                {/* 图片 */}
                <div className="relative rounded-lg overflow-hidden bg-bg-card border border-bg-border" style={{ aspectRatio: "9/16" }}>
                  {imgSrc ? (
                    <img
                      src={imgSrc}
                      alt={`镜头${shot.shot_index}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = "none";
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-text-muted text-xs">
                      无预览
                    </div>
                  )}
                  {/* 时长角标 */}
                  <div className="absolute bottom-1 right-1 bg-black/60 text-white text-xs px-1 py-0.5 rounded">
                    {shot.duration.toFixed(1)}s
                  </div>
                </div>

                {/* 类型标签 */}
                <div
                  className="mt-1.5 text-center text-xs py-1 rounded"
                  style={{ background: `${colors.bar}20`, color: colors.bar }}
                >
                  {shot.displayLabel}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 底部时间线 */}
      <div className="mt-4 relative h-3 rounded-full overflow-hidden bg-bg-border">
        {timelineSegments.map((seg, i) => (
          <div
            key={i}
            className="absolute top-0 h-full"
            style={{
              left: `${seg.left}%`,
              width: `${Math.max(seg.width, 0.5)}%`,
              background: seg.color,
              opacity: 0.8,
            }}
          />
        ))}
      </div>
      <div className="flex justify-between text-xs text-text-muted mt-1">
        <span>0s</span>
        <span>{duration.toFixed(0)}s</span>
      </div>

      {/* 放大查看弹窗 */}
      {selected && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
          onClick={() => setSelected(null)}
        >
          <div
            className="bg-bg-card rounded-2xl p-4 max-w-sm w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-3">
              <h4 className="text-text-primary font-medium">镜头 #{selected.shot_index}</h4>
              <button onClick={() => setSelected(null)} className="text-text-muted hover:text-text-primary">✕</button>
            </div>
            <div className="rounded-xl overflow-hidden bg-black mb-3" style={{ aspectRatio: "9/16" }}>
              <img
                src={selected.frame_path?.startsWith("/static")
                  ? `http://localhost:8000${selected.frame_path}`
                  : selected.frame_path}
                alt="放大查看"
                className="w-full h-full object-contain"
              />
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">时间点</span>
                <span className="text-text-primary">{selected.time_label}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">时长</span>
                <span className="text-text-primary">{selected.duration}s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">结构标签</span>
                <span className="text-text-primary">{selected.structure_tag || "—"}</span>
              </div>
              {selected.narration && (
                <div>
                  <p className="text-text-secondary mb-1">台词</p>
                  <p className="text-text-primary bg-bg-secondary rounded-lg p-3 text-xs leading-relaxed">
                    {selected.narration}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
