"use client";

import { useState } from "react";
import { AnalysisResult, StoryboardShot, getShotLabel, SHOT_TYPE_COLORS } from "@/lib/api";
import { RefreshCw, Copy, Check, ChevronRight } from "lucide-react";

interface Props {
  analysisResult: AnalysisResult;
  tagged: StoryboardShot[];
  taskId: string;
}

const SECTION_STYLES: Record<string, { bg: string; border: string; badge: string; label: string }> = {
  hook: {
    bg: "bg-pink-500/5",
    border: "border-pink-500/30",
    badge: "bg-pink-500/20 text-pink-400",
    label: "痛点放大",
  },
  body: {
    bg: "bg-blue-500/5",
    border: "border-blue-500/30",
    badge: "bg-blue-500/20 text-blue-400",
    label: "产品展示",
  },
  cta: {
    bg: "bg-green-500/5",
    border: "border-green-500/30",
    badge: "bg-green-500/20 text-green-400",
    label: "行动引导",
  },
};

export default function ScriptAnalysisTab({ analysisResult, tagged, taskId }: Props) {
  const [productName, setProductName] = useState("");
  const [replicating, setReplicating] = useState(false);
  const [replicationResult, setReplicationResult] = useState<any>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const analysis = analysisResult?.analysis || {};
  const hook = analysis.hook;
  const body = analysis.body;
  const cta = analysis.cta;
  const blueprint = analysis.replication_blueprint;
  const overall = analysis.overall_assessment;

  if (analysis.parse_error) {
    return (
      <div className="text-text-secondary text-sm p-4 bg-bg-card rounded-xl border border-bg-border">
        <p className="mb-2 text-accent-orange">⚠️ AI 分析结果解析异常</p>
        <pre className="text-xs overflow-auto text-text-muted">{JSON.stringify(analysis, null, 2)}</pre>
      </div>
    );
  }

  const handleReplicate = async () => {
    if (!productName.trim()) return;
    setReplicating(true);
    try {
      const apiKey = localStorage.getItem("anthropic_key") || "";
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          task_id: taskId,
          product_name: productName,
          product_description: `请为产品「${productName}」生成复刻方案`,
          anthropic_api_key: apiKey,
        }),
      });

      // 轮询等待生成结果
      const poll = setInterval(async () => {
        const statusRes = await fetch(`/api/status/${taskId}`);
        const status = await statusRes.json();
        if (status.gen_status === "done") {
          clearInterval(poll);
          const resultRes = await fetch(`/api/result/${taskId}`);
          const result = await resultRes.json();
          setReplicationResult(result.generation_result);
          setReplicating(false);
        } else if (status.gen_status === "error") {
          clearInterval(poll);
          setReplicating(false);
        }
      }, 2000);
    } catch {
      setReplicating(false);
    }
  };

  const copyText = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-text-primary font-semibold text-lg">脚本结构分析</h3>
        {overall && (
          <div className="flex items-center gap-2">
            <span className="text-text-secondary text-sm">综合评分</span>
            <span className="text-2xl font-bold text-accent-yellow">{overall.total_score}</span>
            <span className="text-text-muted text-sm">/100</span>
          </div>
        )}
      </div>

      <p className="text-text-secondary text-sm mb-6">
        分析和拆解文案脚本结构 &nbsp;
        <span className="font-mono text-text-muted text-xs bg-bg-card px-2 py-1 rounded">
          {taskId}
        </span>
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 左侧：三段论分析 */}
        <div className="space-y-4">
          {/* Hook */}
          {hook && (
            <ScriptSection
              type="hook"
              title="痛点放大"
              range={hook.shot_range}
              score={hook.score}
              text={hook.text}
              subText={hook.effectiveness}
              badge={hook.type}
              extra={`×${hook.score}`}
            />
          )}

          {/* Body */}
          {body && (
            <ScriptSection
              type="body"
              title="产品展示"
              range={body.shot_range}
              score={body.score}
              text={body.value_delivered}
              subText={body.key_points?.join("；")}
              badge={body.type}
              extra={`×${body.score}`}
            />
          )}

          {/* CTA */}
          {cta && (
            <ScriptSection
              type="cta"
              title="行动引导"
              range={cta.shot_range}
              score={cta.score}
              text={cta.text}
              subText={`紧迫感：${cta.urgency_level}`}
              badge={cta.type}
              extra={`×${cta.score}`}
            />
          )}

          {/* Suggestions */}
          {overall?.optimization_suggestions && (
            <div className="bg-bg-card rounded-xl border border-bg-border p-4 space-y-2">
              <p className="text-text-secondary text-xs font-medium">优化建议</p>
              {overall.optimization_suggestions.map((s, i) => (
                <p key={i} className="text-text-primary text-sm leading-relaxed">
                  • {s}
                </p>
              ))}
            </div>
          )}
        </div>

        {/* 右侧：跨品类复刻 */}
        <div className="space-y-4">
          {/* 复刻入口 */}
          <div className="bg-bg-card rounded-xl border border-bg-border p-4">
            <div className="flex items-center gap-2 mb-4">
              <RefreshCw className="w-4 h-4 text-accent-cyan" />
              <span className="text-text-primary text-sm font-medium">将文案脚本进行跨品类复刻</span>
            </div>

            <div className="flex gap-2">
              <input
                value={productName}
                onChange={(e) => setProductName(e.target.value)}
                placeholder="输入产品名称，如：猫咪自动饮水机"
                className="flex-1 px-3 py-2 rounded-lg bg-bg-secondary border border-bg-border text-text-primary placeholder-text-muted text-sm focus:outline-none focus:border-accent-purple/50"
              />
              <button
                onClick={handleReplicate}
                disabled={replicating || !productName.trim()}
                className="btn-gradient px-4 py-2 rounded-lg text-white text-sm font-medium flex-shrink-0 disabled:opacity-50"
              >
                {replicating ? "生成中..." : "复刻"}
              </button>
            </div>

            {replicating && (
              <div className="mt-3 flex items-center gap-2 text-text-secondary text-xs">
                <div className="w-3 h-3 border border-accent-purple border-t-transparent rounded-full spin" />
                Claude 正在生成跨品类复刻方案...
              </div>
            )}
          </div>

          {/* 蓝图 */}
          {blueprint && (
            <div className="bg-bg-card rounded-xl border border-bg-border p-4 space-y-3">
              <p className="text-text-secondary text-xs font-medium mb-3">复刻蓝图</p>

              {[
                { label: "钩子模板", value: blueprint.hook_template, key: "hook" },
                { label: "内容结构", value: blueprint.body_structure, key: "body" },
                { label: "CTA模板", value: blueprint.cta_template, key: "cta" },
              ].map(({ label, value, key }) => (
                <div key={key}>
                  <p className="text-accent-purple text-xs font-medium mb-1">{label}</p>
                  <p className="text-text-primary text-sm leading-relaxed">{value}</p>
                </div>
              ))}

              {blueprint.key_success_factors?.length > 0 && (
                <div>
                  <p className="text-accent-purple text-xs font-medium mb-2">成功要素</p>
                  <div className="flex flex-wrap gap-2">
                    {blueprint.key_success_factors.map((f, i) => (
                      <span key={i} className="text-xs px-2 py-1 rounded-full bg-accent-purple/10 text-accent-purple">
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 复刻结果 */}
          {replicationResult && (
            <ReplicationResult result={replicationResult} onCopy={copyText} copied={copied} />
          )}
        </div>
      </div>
    </div>
  );
}

function ScriptSection({
  type, title, range, score, text, subText, badge, extra
}: {
  type: "hook" | "body" | "cta";
  title: string;
  range?: string;
  score: number;
  text: string;
  subText?: string;
  badge?: string;
  extra?: string;
}) {
  const style = SECTION_STYLES[type];
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={`rounded-xl border ${style.border} ${style.bg} p-4`}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-xs px-2 py-1 rounded-full font-medium ${style.badge}`}>
            {title}
          </span>
          {badge && (
            <span className="text-xs text-text-muted">{badge}</span>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-text-muted flex-shrink-0">
          {range && <span>{range}</span>}
          {extra && <span className="font-medium">{extra}</span>}
        </div>
      </div>

      <p className={`text-text-primary text-sm leading-relaxed ${!expanded && "line-clamp-4"}`}>
        {text}
      </p>

      {subText && (
        <p className="text-text-secondary text-xs mt-2 leading-relaxed">{subText}</p>
      )}

      {text && text.length > 200 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-accent-purple text-xs mt-1 hover:underline"
        >
          {expanded ? "收起" : `+展开全部`}
        </button>
      )}

      {/* 评分条 */}
      <div className="flex items-center gap-2 mt-3">
        <div className="flex-1 h-1 bg-bg-border rounded-full overflow-hidden">
          <div
            className="h-full rounded-full"
            style={{
              width: `${score * 10}%`,
              background: type === "hook" ? "#f72585" : type === "body" ? "#4f9cf9" : "#00c896"
            }}
          />
        </div>
        <span className="text-xs text-text-secondary">{score}/10</span>
      </div>
    </div>
  );
}

function ReplicationResult({ result, onCopy, copied }: {
  result: any;
  onCopy: (text: string, key: string) => void;
  copied: string | null;
}) {
  const plan = result.generation_plan;
  if (!plan || plan.parse_error) return null;

  const jimengPrompts = plan.jimeng_video_prompts || [];

  return (
    <div className="bg-bg-card rounded-xl border border-bg-border p-4 space-y-4">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-accent-green" />
        <p className="text-text-primary text-sm font-medium">
          已改编脚本：{result.product_name}
        </p>
      </div>

      {jimengPrompts.map((p: any, i: number) => {
        const colors = SHOT_TYPE_COLORS[p.scene] || { bar: "#7c6ff7", bg: "bg-purple-500/20", text: "text-purple-400" };
        return (
          <div key={i} className="space-y-2">
            {/* 标签行 */}
            <div className="flex items-center gap-2">
              <span
                className="text-xs px-2 py-0.5 rounded-full"
                style={{ background: `${colors.bar}20`, color: colors.bar }}
              >
                {p.scene}
              </span>
            </div>

            {/* 英文提示词 */}
            <div className="relative">
              <p className="text-text-muted text-xs leading-relaxed">+{p.prompt_en}</p>
              <button
                onClick={() => onCopy(p.prompt_en, `en-${i}`)}
                className="absolute top-0 right-0 text-text-muted hover:text-text-primary"
              >
                {copied === `en-${i}` ? <Check className="w-3 h-3 text-accent-green" /> : <Copy className="w-3 h-3" />}
              </button>
            </div>

            {/* 中文提示词 */}
            <p className="text-accent-orange text-xs">+{p.prompt_zh}</p>

            {/* 推荐镜头 */}
            {plan.new_script?.body?.[i] && (
              <>
                <p className="text-accent-cyan text-xs">{plan.new_script.body[i].narration}</p>
                <p className="text-text-secondary text-xs">{plan.new_script.body[i].visual_description}</p>
              </>
            )}
          </div>
        );
      })}
    </div>
  );
}
