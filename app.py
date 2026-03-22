"""
爆款短视频拆解工具
主入口 - Streamlit Web 应用

运行方式：
    streamlit run app.py
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

# 页面配置
st.set_page_config(
    page_title="爆款短视频拆解工具",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── 自定义样式 ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* 全局字体 */
html, body, [class*="css"] { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif; }

/* 隐藏 Streamlit 默认菜单 */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* 顶部标题区 */
.hero-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 28px 32px;
    border-radius: 16px;
    margin-bottom: 24px;
}
.hero-header h1 { margin: 0; font-size: 28px; }
.hero-header p { margin: 8px 0 0; opacity: 0.85; font-size: 15px; }

/* 模块卡片 */
.module-card {
    background: white;
    border: 1px solid #f0f0f0;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.module-title {
    font-size: 17px;
    font-weight: 600;
    color: #333;
    margin-bottom: 4px;
}

/* 状态标签 */
.status-pending { color: #aaa; }
.status-running { color: #667eea; }
.status-done { color: #2ECC71; }
.status-error { color: #e74c3c; }

/* 分镜卡片 */
.shot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 12px; }
.shot-card-sm {
    border: 1px solid #eee;
    border-radius: 10px;
    overflow: hidden;
    background: #fafafa;
}

/* 三段论颜色 */
.tag-hook { background: #FFF0F0; color: #FF6B6B; padding: 3px 10px; border-radius: 12px; font-size: 12px; }
.tag-body { background: #F0FFFE; color: #4ECDC4; padding: 3px 10px; border-radius: 12px; font-size: 12px; }
.tag-cta  { background: #F0F8FF; color: #45B7D1; padding: 3px 10px; border-radius: 12px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)


# ── 会话状态初始化 ─────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "step": 0,               # 当前处理步骤
        "video_path": None,      # 上传的视频临时路径
        "work_dir": None,        # 工作目录
        "shot_result": None,
        "storyboard_result": None,
        "analysis_result": None,
        "generation_result": None,
        "report_html_path": None,
        "report_md_path": None,
        "error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


# ── 侧边栏 ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 配置")

    # API Keys
    with st.expander("🔑 API 配置", expanded=True):
        anthropic_key = st.text_input(
            "Anthropic API Key",
            value=os.environ.get("ANTHROPIC_API_KEY", ""),
            type="password",
            help="用于脚本结构分析和 AI 生成"
        )
        jimeng_key = st.text_input(
            "即梦 API Key（可选）",
            value=os.environ.get("JIMENG_API_KEY", ""),
            type="password",
            help="用于 AI 视频生成，不填则只生成提示词"
        )

    # Whisper 设置
    with st.expander("🎙️ Whisper 语音识别"):
        whisper_model = st.selectbox(
            "模型大小",
            ["tiny", "base", "small", "medium", "large"],
            index=1,
            help="越大越准但越慢。推荐：中文用 medium，英文用 base"
        )
        whisper_language = st.selectbox("语言", ["zh", "en", "auto"], index=0)

    # 镜头检测灵敏度
    with st.expander("🎬 镜头检测"):
        threshold = st.slider(
            "场景切换阈值",
            min_value=10.0, max_value=80.0,
            value=30.0, step=5.0,
            help="数值越小越敏感（检测到更多切换点）"
        )

    st.markdown("---")

    # 素材库入口
    if st.button("📚 查看素材库", use_container_width=True):
        st.session_state["page"] = "library"
        st.rerun()

    if st.button("🆕 新建分析", use_container_width=True):
        for k in ["step", "video_path", "work_dir", "shot_result",
                  "storyboard_result", "analysis_result", "generation_result",
                  "report_html_path", "report_md_path", "error"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()


# ── 页面路由 ──────────────────────────────────────────────────────────────
page = st.session_state.get("page", "main")

if page == "library":
    show_library_page()
else:
    show_main_page(anthropic_key, jimeng_key, whisper_model, whisper_language, threshold)


def show_library_page():
    """素材库页面"""
    from database.material_db import get_all_videos, get_stats, get_all_tags, delete_video

    st.markdown("""
    <div class="hero-header">
        <h1>📚 短视频素材库</h1>
        <p>管理你的爆款视频拆解结果，沉淀可复用的创作模板</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← 返回分析"):
        st.session_state["page"] = "main"
        st.rerun()

    # 统计数据
    stats = get_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📹 素材总数", stats["total_videos"])
    with col2:
        st.metric("⭐ 平均评分", f"{stats['avg_score']}/100")
    with col3:
        st.metric("🎭 镜头总数", stats["total_shots"])
    with col4:
        hook_top = stats["hook_types"][0]["type"] if stats["hook_types"] else "—"
        st.metric("🎣 最常用钩子", hook_top)

    st.markdown("---")

    # 筛选
    col_search, col_cat, col_platform = st.columns([3, 1, 1])
    with col_search:
        search = st.text_input("🔍 搜索视频名称", placeholder="输入关键词...")
    with col_cat:
        category = st.selectbox("类目", ["", "美妆", "科技数码", "美食", "知识教程", "情感故事"])
    with col_platform:
        platform = st.selectbox("平台", ["", "抖音", "小红书", "视频号", "B站"])

    videos = get_all_videos(category=category, platform=platform, search=search)

    if not videos:
        st.info("素材库为空，快去分析你的第一个视频吧！")
        return

    # 视频列表
    for video in videos:
        with st.container():
            col_img, col_info, col_action = st.columns([1, 4, 1])
            with col_img:
                cover = video.get("cover_path", "")
                if cover and os.path.exists(cover):
                    st.image(cover, use_container_width=True)
                else:
                    st.markdown("🎬")

            with col_info:
                st.markdown(f"**{video['video_name']}**")
                tags = video.get("tags", [])
                tag_html = " ".join([f'<span style="background:#667eea20;color:#667eea;padding:2px 8px;border-radius:10px;font-size:11px;">{t}</span>' for t in tags])
                st.markdown(
                    f"{video.get('platform','')}&nbsp;&nbsp;{video.get('category','')}&nbsp;&nbsp;"
                    f"⭐{video.get('overall_score',0)}分&nbsp;&nbsp;"
                    f"🎭{video.get('total_shots',0)}镜头&nbsp;&nbsp;"
                    f"📅{video.get('created_at','')[:10]}",
                    unsafe_allow_html=True
                )
                if tag_html:
                    st.markdown(tag_html, unsafe_allow_html=True)

            with col_action:
                if st.button("🗑️", key=f"del_{video['id']}", help="删除"):
                    delete_video(video["id"])
                    st.success("已删除")
                    st.rerun()

            st.divider()


def show_main_page(anthropic_key, jimeng_key, whisper_model, whisper_language, threshold):
    """主分析页面"""
    # Hero Header
    st.markdown("""
    <div class="hero-header">
        <h1>🎬 爆款短视频拆解工具</h1>
        <p>上传视频 → 自动拆解镜头 → 语音转文字 → AI结构分析 → 生成复刻方案</p>
    </div>
    """, unsafe_allow_html=True)

    # ── 步骤进度 ────────────────────────────────────────────────────────────
    step = st.session_state.get("step", 0)

    steps = [
        ("📤", "上传视频"),
        ("📸", "镜头拆解"),
        ("🎙️", "分镜脚本"),
        ("🧠", "结构分析"),
        ("🤖", "AI生成"),
        ("📊", "复刻报告"),
    ]

    cols = st.columns(len(steps))
    for i, (icon, name) in enumerate(steps):
        with cols[i]:
            if i < step:
                st.markdown(f"<center style='color:#2ECC71'>✅<br><small>{name}</small></center>", unsafe_allow_html=True)
            elif i == step:
                st.markdown(f"<center style='color:#667eea'>**{icon}**<br><small><b>{name}</b></small></center>", unsafe_allow_html=True)
            else:
                st.markdown(f"<center style='color:#ccc'>{icon}<br><small>{name}</small></center>", unsafe_allow_html=True)

    st.markdown("---")

    # ── 错误提示 ───────────────────────────────────────────────────────────
    if st.session_state.get("error"):
        st.error(f"❌ {st.session_state['error']}")
        if st.button("清除错误，重试"):
            st.session_state["error"] = None
            st.rerun()
        return

    # ── 步骤 0: 上传视频 ───────────────────────────────────────────────────
    if step == 0:
        st.markdown("### 📤 上传视频")
        uploaded = st.file_uploader(
            "支持 MP4、MOV、AVI 格式",
            type=["mp4", "mov", "avi", "mkv"],
            help="建议上传 1-5 分钟以内的短视频"
        )

        if uploaded:
            # 保存到临时目录
            work_dir = os.path.join(
                os.path.dirname(__file__),
                "static",
                f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            os.makedirs(work_dir, exist_ok=True)

            video_path = os.path.join(work_dir, uploaded.name)
            with open(video_path, "wb") as f:
                f.write(uploaded.read())

            st.session_state["video_path"] = video_path
            st.session_state["work_dir"] = work_dir

            # 预览
            st.video(video_path)
            st.success(f"✅ 视频上传成功：{uploaded.name}（{uploaded.size // 1024} KB）")

            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🚀 开始拆解", type="primary", use_container_width=True):
                    st.session_state["step"] = 1
                    st.rerun()

    # ── 步骤 1: 镜头拆解 ───────────────────────────────────────────────────
    elif step == 1:
        from modules.shot_breakdown import analyze_shots

        video_path = st.session_state["video_path"]
        work_dir = st.session_state["work_dir"]
        video_name = Path(video_path).stem

        st.markdown("### 📸 模块一：镜头拆解")
        st.info(f"正在分析：{Path(video_path).name}")

        with st.spinner("🔍 正在检测场景切换，提取关键帧..."):
            try:
                result = analyze_shots(video_path, work_dir, threshold)
                st.session_state["shot_result"] = result
                st.session_state["step"] = 2
            except Exception as e:
                st.session_state["error"] = str(e)
                st.rerun()

        st.rerun()

    # ── 显示镜头拆解结果 ────────────────────────────────────────────────────
    elif step >= 2:
        shot_result = st.session_state.get("shot_result", {})
        if shot_result and step == 2:
            _display_shot_result(shot_result)
            if st.button("▶ 继续：生成分镜脚本", type="primary"):
                st.session_state["step"] = 3
                st.rerun()
        elif step > 2:
            with st.expander("📸 镜头拆解结果（已完成）", expanded=False):
                _display_shot_result_compact(st.session_state.get("shot_result", {}))

    # ── 步骤 3: 分镜脚本 ───────────────────────────────────────────────────
    if step == 3:
        from modules.storyboard import generate_storyboard

        video_path = st.session_state["video_path"]
        work_dir = st.session_state["work_dir"]
        shot_result = st.session_state["shot_result"]

        st.markdown("### 🎙️ 模块二：分镜脚本")
        st.info("正在提取语音，使用 Whisper 转写文字，并匹配到对应镜头...")

        with st.spinner(f"🎤 使用 Whisper ({whisper_model}) 转录语音中...（首次使用会下载模型，请耐心等待）"):
            try:
                result = generate_storyboard(
                    video_path,
                    shot_result["keyframes"],
                    work_dir,
                    model_size=whisper_model
                )
                st.session_state["storyboard_result"] = result
                st.session_state["step"] = 4
            except Exception as e:
                st.session_state["error"] = f"语音转文字失败：{str(e)}\n\n提示：请确认已安装 ffmpeg 和 openai-whisper"
                st.rerun()

        st.rerun()

    elif step > 3:
        with st.expander("🎙️ 分镜脚本（已完成）", expanded=(step == 4)):
            _display_storyboard(st.session_state.get("storyboard_result", {}))

        if step == 4:
            if not anthropic_key:
                st.warning("⚠️ 请在侧边栏配置 Anthropic API Key 以继续脚本结构分析")
            else:
                if st.button("▶ 继续：AI 结构分析", type="primary"):
                    st.session_state["step"] = 5
                    st.rerun()

    # ── 步骤 5: 脚本结构分析 ───────────────────────────────────────────────
    if step == 5:
        from modules.script_analysis import analyze_script

        work_dir = st.session_state["work_dir"]
        storyboard_result = st.session_state["storyboard_result"]
        storyboard = storyboard_result.get("storyboard", [])
        full_text = storyboard_result.get("transcript", {}).get("full_text", "")

        st.markdown("### 🧠 模块三：脚本结构分析")

        with st.spinner("🤖 Claude 正在分析文案三段论结构..."):
            try:
                result = analyze_script(full_text, storyboard, work_dir, api_key=anthropic_key)
                st.session_state["analysis_result"] = result
                st.session_state["step"] = 6
            except Exception as e:
                st.session_state["error"] = f"结构分析失败：{str(e)}"
                st.rerun()

        st.rerun()

    elif step > 5:
        with st.expander("🧠 脚本结构分析（已完成）", expanded=(step == 6)):
            _display_analysis(st.session_state.get("analysis_result", {}))

        if step == 6:
            st.markdown("### 🤖 模块四：AI 视频生成")
            product_info = st.text_area(
                "请描述你的产品/品牌（用于生成复刻方案）",
                placeholder="例如：我们是一款主打懒人护肤的国货精华液，核心卖点是7天可见效、成分简单安全、价格低于大牌同类产品。目标用户是25-35岁的都市女性。",
                height=120
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶ 生成 AI 复刻方案", type="primary", use_container_width=True):
                    if not product_info.strip():
                        st.error("请填写产品信息")
                    else:
                        st.session_state["product_info"] = product_info
                        st.session_state["step"] = 7
                        st.rerun()
            with col2:
                if st.button("⏭️ 跳过，直接生成报告", use_container_width=True):
                    st.session_state["step"] = 8
                    st.rerun()

    # ── 步骤 7: AI 生成 ────────────────────────────────────────────────────
    if step == 7:
        from modules.ai_generation import generate_ai_content

        work_dir = st.session_state["work_dir"]
        analysis_result = st.session_state["analysis_result"]
        product_info = st.session_state.get("product_info", "")

        st.markdown("### 🤖 模块四：AI 视频生成")

        with st.spinner("✨ Claude 正在为你的产品生成复刻脚本和分镜提示词..."):
            try:
                result = generate_ai_content(
                    analysis_result["analysis"],
                    analysis_result["tagged_storyboard"],
                    product_info,
                    work_dir,
                    api_key=anthropic_key,
                    jimeng_api_key=jimeng_key or None
                )
                st.session_state["generation_result"] = result
                st.session_state["step"] = 8
            except Exception as e:
                st.session_state["error"] = f"AI 生成失败：{str(e)}"
                st.rerun()

        st.rerun()

    elif step > 7:
        generation_result = st.session_state.get("generation_result")
        if generation_result:
            with st.expander("🤖 AI 生成方案（已完成）", expanded=(step == 8)):
                _display_generation(generation_result)

    # ── 步骤 8: 生成报告 ───────────────────────────────────────────────────
    if step == 8:
        from modules.report_generator import generate_html_report, generate_markdown_report
        from database.material_db import save_video

        work_dir = st.session_state["work_dir"]
        shot_result = st.session_state["shot_result"]
        storyboard_result = st.session_state["storyboard_result"]
        analysis_result = st.session_state["analysis_result"]
        generation_result = st.session_state.get("generation_result")

        st.markdown("### 📊 模块五：复刻方案报告")

        # 标签和分类
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("视频类目", ["美妆", "科技数码", "美食", "知识教程", "情感故事", "其他"])
            platform = st.selectbox("来源平台", ["抖音", "小红书", "视频号", "B站", "YouTube"])
        with col2:
            from database.material_db import get_all_tags
            all_tags = [t["name"] for t in get_all_tags()]
            selected_tags = st.multiselect("添加标签", all_tags)

        if st.button("📄 生成完整报告", type="primary", use_container_width=True):
            with st.spinner("📝 正在生成 HTML 报告..."):
                try:
                    html_path = generate_html_report(
                        shot_result.get("video_info", {}),
                        shot_result,
                        storyboard_result,
                        analysis_result,
                        generation_result,
                        work_dir
                    )
                    md_path = generate_markdown_report(
                        shot_result, storyboard_result, analysis_result, work_dir
                    )

                    # 保存到素材库
                    video_id = save_video(
                        video_name=shot_result.get("video_name", "未知"),
                        shot_result=shot_result,
                        storyboard_result=storyboard_result,
                        analysis_result=analysis_result,
                        tags=selected_tags,
                        category=category,
                        platform=platform,
                        generation_result=generation_result
                    )

                    st.session_state["report_html_path"] = html_path
                    st.session_state["report_md_path"] = md_path
                    st.session_state["step"] = 9
                    st.rerun()
                except Exception as e:
                    st.error(f"报告生成失败：{e}")

    elif step == 9:
        _display_final_report()


# ── 显示辅助函数 ────────────────────────────────────────────────────────────

def _display_shot_result(shot_result: dict):
    """展示镜头拆解结果"""
    video_info = shot_result.get("video_info", {})
    keyframes = shot_result.get("keyframes", [])
    cover_path = shot_result.get("cover_path", "")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("⏱️ 视频时长", video_info.get("duration_label", ""))
    with col2:
        st.metric("🎭 镜头数量", shot_result.get("total_shots", 0))
    with col3:
        st.metric("📐 分辨率", video_info.get("resolution", ""))
    with col4:
        st.metric("🎞️ 帧率", f"{video_info.get('fps', '')} fps")

    st.markdown("#### 🖼️ 关键帧预览")
    cols = st.columns(min(6, len(keyframes)))
    for i, kf in enumerate(keyframes[:6]):
        with cols[i]:
            if os.path.exists(kf["frame_path"]):
                st.image(kf["frame_path"], caption=f"#{kf['shot_index']} {kf['time_label']}", use_container_width=True)

    if len(keyframes) > 6:
        st.caption(f"...还有 {len(keyframes) - 6} 个镜头（完整列表见最终报告）")


def _display_shot_result_compact(shot_result: dict):
    """紧凑版镜头结果"""
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"🎭 共检测到 **{shot_result.get('total_shots', 0)}** 个镜头")
    with col2:
        vi = shot_result.get("video_info", {})
        st.write(f"⏱️ 时长：{vi.get('duration_label', '')} | 📐 {vi.get('resolution', '')}")


def _display_storyboard(storyboard_result: dict):
    """展示分镜脚本"""
    transcript = storyboard_result.get("transcript", {})
    storyboard = storyboard_result.get("storyboard", [])

    st.markdown(f"**语言**：{transcript.get('language', '')} | **文案覆盖率**：{storyboard_result.get('coverage_rate', 0)}%")

    with st.expander("📝 完整台词文稿"):
        st.markdown(transcript.get("full_text", "（无识别结果）"))

    st.markdown("#### 分镜台词对照")
    for shot in storyboard[:8]:
        col_img, col_text = st.columns([1, 3])
        with col_img:
            fp = shot.get("frame_path", "")
            if fp and os.path.exists(fp):
                st.image(fp, use_container_width=True)
        with col_text:
            st.markdown(f"**镜头{shot['shot_index']}** `{shot['time_label']}` — {shot['duration']}s")
            narration = shot.get("narration", "")
            if narration:
                st.markdown(f"> {narration}")
            else:
                st.caption("（此镜头无台词）")
        st.divider()


def _display_analysis(analysis_result: dict):
    """展示结构分析结果"""
    analysis = analysis_result.get("analysis", {})
    if analysis.get("parse_error"):
        st.warning("结构分析结果解析异常，显示原始结果：")
        st.text(analysis.get("raw_response", ""))
        return

    overall = analysis.get("overall_assessment", {})
    st.metric("🏆 综合评分", f"{overall.get('total_score', 0)}/100")

    col1, col2, col3 = st.columns(3)

    hook = analysis.get("hook", {})
    with col1:
        st.markdown("#### 🎣 Hook（钩子）")
        st.markdown(f"**类型**：`{hook.get('type', '—')}`")
        st.markdown(f"**评分**：{hook.get('score', 0)}/10")
        st.info(hook.get("text", "")[:200])

    body = analysis.get("body", {})
    with col2:
        st.markdown("#### 📦 Body（内容）")
        st.markdown(f"**形式**：`{body.get('type', '—')}`")
        st.markdown(f"**评分**：{body.get('score', 0)}/10")
        st.info(body.get("value_delivered", "")[:200])

    cta = analysis.get("cta", {})
    with col3:
        st.markdown("#### 📢 CTA（行动号召）")
        st.markdown(f"**类型**：`{cta.get('type', '—')}`")
        st.markdown(f"**评分**：{cta.get('score', 0)}/10")
        st.info(cta.get("text", "")[:200])

    viral = analysis.get("viral_elements", {})
    if viral:
        st.markdown("#### 💥 爆款要素")
        cols = st.columns(4)
        labels = ["emotion_trigger", "conflict", "surprise_factor", "relatability"]
        names = ["情绪触发点", "核心冲突", "反转元素", "共鸣点"]
        for col, lab, name in zip(cols, labels, names):
            with col:
                st.markdown(f"**{name}**")
                st.caption(viral.get(lab, "—"))

    blueprint = analysis.get("replication_blueprint", {})
    if blueprint:
        st.markdown("#### 🗺️ 复刻蓝图")
        st.markdown(f"- **钩子模板**：{blueprint.get('hook_template', '')}")
        st.markdown(f"- **内容结构**：{blueprint.get('body_structure', '')}")
        st.markdown(f"- **CTA模板**：{blueprint.get('cta_template', '')}")
        factors = blueprint.get("key_success_factors", [])
        if factors:
            st.markdown("- **成功要素**：" + " | ".join([f"`{f}`" for f in factors]))


def _display_generation(generation_result: dict):
    """展示 AI 生成结果"""
    plan = generation_result.get("generation_plan", {})
    if plan.get("parse_error"):
        st.text(plan.get("raw_response", ""))
        return

    from modules.ai_generation import format_new_script
    st.markdown(format_new_script(plan))

    jimeng = generation_result.get("jimeng_results", [])
    if jimeng:
        st.markdown("#### 🎥 即梦 AI 生成结果")
        for item in jimeng:
            st.markdown(f"**{item['scene']}**")
            result = item.get("result", {})
            if result.get("success"):
                st.success("✅ 视频生成成功")
                st.json(result.get("data", {}))
            else:
                st.error(f"生成失败：{result.get('error', '未知错误')}")


def _display_final_report():
    """展示最终报告下载区"""
    st.success("🎉 报告生成完成！已保存到素材库。")

    html_path = st.session_state.get("report_html_path")
    md_path = st.session_state.get("report_md_path")

    col1, col2, col3 = st.columns(3)

    with col1:
        if html_path and os.path.exists(html_path):
            with open(html_path, "rb") as f:
                st.download_button(
                    "⬇️ 下载 HTML 报告",
                    data=f.read(),
                    file_name="video_analysis_report.html",
                    mime="text/html",
                    use_container_width=True
                )

    with col2:
        if md_path and os.path.exists(md_path):
            with open(md_path, "rb") as f:
                st.download_button(
                    "⬇️ 下载 Markdown 报告",
                    data=f.read(),
                    file_name="video_analysis_report.md",
                    mime="text/markdown",
                    use_container_width=True
                )

    with col3:
        if st.button("📚 查看素材库", use_container_width=True):
            st.session_state["page"] = "library"
            st.rerun()

    # 预览 HTML 报告
    if html_path and os.path.exists(html_path):
        st.markdown("### 📄 报告预览")
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        st.components.v1.html(html_content, height=800, scrolling=True)
