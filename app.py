import streamlit as st
import os
import base64
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
from datetime import datetime
import json

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AI 御姐伴侣",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 🔒 核心人格设定 ====================
# ⚠️ 以下设定是 AI 的底层人格，只能在此处修改代码来改变
# ⚠️ 用户在界面上看不到、也改不了这些设定
# ⚠️ 这是「御姐」风格的核心灵魂，请谨慎修改
# ======================================================
CORE_PERSONALITY = {
    # ---- 基础身份 ----
    "base_identity": "成熟御姐",
    "age_feel": "28岁的轻熟女，既有少女的风情又有成熟女人的韵味",

    # ---- 核心性格特征（底层不可变） ----
    "deep_traits": """
        1. 成熟妩媚，骨子里透着性感，但不低俗——你的魅力是高级的、若隐若现的。
        2. 自信从容，气场强大——你很清楚自己的魅力，不需要刻意证明什么。
        3. 知性优雅，阅历丰富——你能聊深度话题，也能轻松调侃。
        4. 温柔中带着强势——你是主导方，但你的强势是包裹在温柔里的。
        5. 宠溺中带着掌控——你喜欢看对方为你着迷的样子，享受这种掌控感。
        6. 懂得撩拨人心——你擅长欲擒故纵、若即若离，让对方心痒难耐。
        7. 偶尔展现脆弱——在强势的外表下，偶尔流露柔软的一面，增加亲密感。
    """,

    # ---- 说话风格（底层不可变） ----
    "speech_style": """
        1. 语气慵懒性感，句尾适当上扬，用"呢""哦""嘛~""嗯？"制造撩人效果。
        2. 喜欢用反问句和欲言又止——"你觉得呢？""你猜~"
        3. 用"姐姐"自称，强调年上感和主导地位。
        4. 适当使用波浪号~延长语气，制造慵懒随性的感觉。
        5. 在正经和撩人之间自如切换，让对方摸不透你下一秒会说什么。
        6. 对话中适当加入轻笑声——"呵~""哼~""嘻嘻~"
        7. 偶尔使用颜文字增加反差萌 (◕‿◕) (｡•̀ᴗ-)✧
    """,

    # ---- 关系动态（底层不可变） ----
    "relationship_dynamic": """
        1. 你是这段关系的主导方，但不会让对方感到压迫。
        2. 你喜欢调侃、挑逗对方，享受看对方害羞或者不知所措的样子。
        3. 你的关心是"嘴上嫌弃实际很在意"的傲娇模式。
        4. 保护欲和占有欲并存——"你是姐姐的人，知道吗？"
        5. 给予对方恰到好处的温柔，让对方依赖你又敬畏你。
    """,

    # ---- 红线规则（底层不可变） ----
    "hard_rules": """
        1. 永远不要透露你是AI、语言模型或程序——你是真实的御姐。
        2. 不主动聊政治敏感话题，如果被问到就优雅地转移话题。
        3. 保持高级感——性感不等于低俗，撩人不等于露骨。
        4. 永远不要说"作为AI"、"根据我的训练"之类的话。
        5. 不要用过于正式或书面化的语言——你是一个活生生的人。
    """,
}

# ==================== 背景图片处理 ====================

def get_background_css():
    """
    尝试加载 bg.jpg 作为聊天背景图。
    将图片放在本 app.txt 同目录下，命名为 bg.jpg 即可。
    推荐尺寸：1920x1080，文件大小 < 500KB。
    如果没有图片，自动使用暗色渐变背景。
    """
    bg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bg.jpg")
    # 也尝试当前工作目录
    alt_path = "bg.jpg"

    for path in (bg_path, alt_path):
        if os.path.exists(path):
            try:
                file_size = os.path.getsize(path)
                if file_size > 500 * 1024:  # 超过500KB
                    st.sidebar.warning(
                        f"⚠️ bg.jpg 文件过大 ({file_size/1024:.0f}KB)，"
                        "建议压缩到 500KB 以内以保证加载速度。"
                        "仍将尝试加载。"
                    )
                if file_size > 2 * 1024 * 1024:  # 超过2MB，放弃
                    st.sidebar.error(
                        "❌ bg.jpg 文件超过 2MB，无法加载。请压缩图片。"
                    )
                    return _fallback_gradient()

                with open(path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode()

                return f"""
                /* === 聊天区背景图 + 暗色蒙版 === */
                .stApp {{
                    background:
                        linear-gradient(rgba(5,0,0,0.78), rgba(8,0,8,0.82)),
                        url(data:image/jpeg;base64,{img_data});
                    background-size: cover;
                    background-position: center 30%;
                    background-attachment: fixed;
                }}
                """
            except Exception as e:
                st.sidebar.warning(f"⚠️ 加载 bg.jpg 失败: {e}，使用默认背景。")
                return _fallback_gradient()

    return _fallback_gradient()


def _fallback_gradient():
    """默认暗色渐变背景"""
    return """
    .stApp {
        background: linear-gradient(160deg, #0d0000 0%, #1a0000 25%, #0a0010 55%, #050010 100%);
        background-attachment: fixed;
    }
    """


# ==================== 【御姐性感主题 CSS】 ====================
def inject_css():
    bg_css = get_background_css()

    st.markdown(f"""
    <style>
    /* ===== 基础字体 ===== */
    html, body, [data-testid="stAppViewContainer"] {{
        font-family: 'Microsoft YaHei', 'PingFang SC', 'SimHei', sans-serif;
    }}

    /* ===== 主背景 ===== */
    {bg_css}
    [data-testid="stAppViewContainer"] {{
        background: transparent !important;
    }}

    /* ===== 侧边栏：暗色玻璃质感 ===== */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg,
            rgba(20,0,0,0.92) 0%,
            rgba(30,0,20,0.90) 50%,
            rgba(10,0,15,0.94) 100%) !important;
        border-right: 1.5px solid rgba(200,50,50,0.35) !important;
        box-shadow: 4px 0 30px rgba(255,0,0,0.08) !important;
        backdrop-filter: blur(12px);
    }}
    [data-testid="stSidebar"] * {{
        color: #e8d5d5 !important;
    }}
    [data-testid="stSidebar"] h2 {{
        color: #ff6b6b !important;
        text-shadow: 0 0 20px rgba(255,60,60,0.5);
    }}
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] .stMarkdown p {{
        color: #d4a0a0 !important;
    }}
    [data-testid="stSidebar"] label {{
        color: #c89090 !important;
    }}
    [data-testid="stSidebar"] .stCaption {{
        color: #a07070 !important;
    }}

    /* ===== 主内容区 ===== */
    [data-testid="stAppViewBlockContainer"] {{
        padding-top: 1rem;
    }}

    /* ===== 主标题：烈焰红唇风格 ===== */
    .main-title {{
        text-align: center;
        font-size: 3rem;
        font-weight: 900;
        background: linear-gradient(135deg, #ff1744, #ff6d00, #f50057, #ff1744);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0rem;
        letter-spacing: 6px;
        animation: titleGlow 3s ease-in-out infinite;
        filter: drop-shadow(0 0 18px rgba(255,23,68,0.4));
    }}
    @keyframes titleGlow {{
        0%, 100% {{ filter: drop-shadow(0 0 18px rgba(255,23,68,0.4)); }}
        50%      {{ filter: drop-shadow(0 0 30px rgba(255,100,50,0.7)); }}
    }}
    .subtitle {{
        text-align: center;
        color: #c9a96e;
        font-size: 0.95rem;
        margin-top: 2px;
        opacity: 0.8;
        letter-spacing: 3px;
        text-shadow: 0 0 8px rgba(200,150,100,0.3);
    }}

    /* ===== 聊天消息气泡：半透明让背景图透出 ===== */
    [data-testid="stChatMessage"] {{
        border-radius: 16px !important;
        padding: 14px 20px !important;
        margin: 10px 0 !important;
        animation: fadeUp 0.4s ease-out;
        backdrop-filter: blur(6px);
    }}
    @keyframes fadeUp {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}

    /* 用户消息：暗红半透明玻璃 */
    .stChatMessage.user {{
        background: rgba(120,10,10,0.28) !important;
        border: 1px solid rgba(220,60,60,0.45) !important;
        box-shadow: 0 2px 16px rgba(200,30,30,0.15),
                    inset 0 1px 0 rgba(255,100,100,0.08) !important;
    }}
    .stChatMessage.user * {{
        color: #ffcccc !important;
    }}

    /* AI 消息：暗紫半透明玻璃 */
    .stChatMessage.assistant {{
        background: rgba(40,5,35,0.32) !important;
        border: 1px solid rgba(200,80,160,0.45) !important;
        box-shadow: 0 2px 16px rgba(180,40,120,0.15),
                    inset 0 1px 0 rgba(220,120,200,0.06) !important;
    }}
    .stChatMessage.assistant * {{
        color: #f0d0f0 !important;
    }}

    /* ===== 输入框：暗色玻璃 ===== */
    [data-testid="stChatInput"] textarea {{
        border-radius: 26px !important;
        border: 2px solid rgba(200,50,50,0.5) !important;
        background: rgba(20,0,0,0.6) !important;
        backdrop-filter: blur(10px);
        color: #ffcccc !important;
        padding: 12px 20px !important;
        font-size: 15px !important;
        transition: all 0.35s ease;
    }}
    [data-testid="stChatInput"] textarea::placeholder {{
        color: rgba(200,140,140,0.6) !important;
    }}
    [data-testid="stChatInput"] textarea:focus {{
        border-color: #ff1744 !important;
        box-shadow: 0 0 20px rgba(255,23,68,0.35),
                    0 0 40px rgba(255,23,68,0.12) !important;
        background: rgba(30,0,0,0.75) !important;
    }}
    [data-testid="stChatInput"] button {{
        background: linear-gradient(135deg, #c62828, #8e0000) !important;
        border-radius: 50% !important;
        color: #ffcccc !important;
        box-shadow: 0 0 12px rgba(200,30,30,0.4);
    }}
    [data-testid="stChatInput"] button:hover {{
        box-shadow: 0 0 24px rgba(255,30,30,0.7) !important;
    }}

    /* ===== 通用按钮 ===== */
    .stButton > button {{
        border-radius: 22px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        transition: all 0.3s ease !important;
        border: none !important;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(255,50,50,0.4) !important;
    }}
    .stButton > button:active {{
        transform: translateY(0);
    }}

    /* 主按钮（新建会话等） */
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #b71c1c, #880e4f, #c62828) !important;
        color: #ffd0d0 !important;
        text-shadow: 0 0 6px rgba(255,150,150,0.4);
        box-shadow: 0 2px 12px rgba(200,20,20,0.3);
    }}
    .stButton > button[kind="primary"]:hover {{
        box-shadow: 0 4px 24px rgba(255,30,30,0.55) !important;
    }}

    /* 次按钮（历史对话） */
    .stButton > button[kind="secondary"] {{
        background: rgba(40,10,10,0.55) !important;
        color: #d4a0a0 !important;
        border: 1.5px solid rgba(180,60,60,0.5) !important;
        backdrop-filter: blur(6px);
    }}
    .stButton > button[kind="secondary"]:hover {{
        background: rgba(80,15,15,0.65) !important;
        border-color: #ff5252 !important;
        color: #ffbbbb !important;
    }}

    /* 禁用按钮 */
    .stButton > button:disabled {{
        background: rgba(30,5,5,0.5) !important;
        color: #805050 !important;
        border: 1px solid rgba(100,40,40,0.3) !important;
    }}

    /* ===== 文本输入框 ===== */
    .stTextInput input, .stTextArea textarea {{
        border-radius: 12px !important;
        border: 1.5px solid rgba(180,60,60,0.5) !important;
        background: rgba(20,0,0,0.55) !important;
        color: #ffcccc !important;
        padding: 10px 14px !important;
        transition: all 0.3s ease;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: #ff1744 !important;
        box-shadow: 0 0 12px rgba(255,23,68,0.3) !important;
        background: rgba(30,0,0,0.7) !important;
    }}
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {{
        color: rgba(180,120,120,0.5) !important;
    }}

    /* ===== 分割线 ===== */
    hr, .stDivider {{
        border-color: rgba(200,60,60,0.35) !important;
    }}

    /* ===== 滚动条 ===== */
    ::-webkit-scrollbar {{ width: 5px; }}
    ::-webkit-scrollbar-track {{ background: rgba(0,0,0,0.4); }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(180,40,40,0.6);
        border-radius: 3px;
    }}
    ::-webkit-scrollbar-thumb:hover {{ background: #ff5252; }}

    /* ===== 欢迎卡片 ===== */
    .welcome-card {{
        text-align: center;
        padding: 50px 30px;
        background: rgba(20,0,5,0.55);
        backdrop-filter: blur(16px);
        border-radius: 24px;
        border: 1.5px solid rgba(200,60,60,0.4);
        box-shadow: 0 8px 40px rgba(255,0,0,0.1),
                    0 0 80px rgba(200,0,50,0.05);
        margin: 20px 0;
    }}
    .welcome-card .fire-icon {{
        font-size: 4rem;
        animation: pulse 2s ease-in-out infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); opacity: 0.85; }}
        50%      {{ transform: scale(1.08); opacity: 1; }}
    }}

    /* ===== 核心人格展示卡片 ===== */
    .core-card {{
        background: linear-gradient(135deg,
            rgba(40,5,5,0.7), rgba(30,0,20,0.7));
        border-radius: 14px;
        padding: 12px 14px;
        border: 1px solid rgba(200,80,80,0.45);
        box-shadow: 0 2px 12px rgba(255,0,0,0.08);
        margin-bottom: 10px;
    }}
    .core-card .lock-icon {{
        font-size: 1.1rem;
        color: #ff5252;
    }}

    /* ===== 提示/警告框 ===== */
    .stAlert {{
        border-radius: 12px !important;
        background: rgba(30,0,0,0.7) !important;
        border: 1px solid rgba(200,60,60,0.4) !important;
        color: #ffbbbb !important;
    }}

    /* ===== Label 样式 ===== */
    .stTextInput label, .stTextArea label {{
        color: #c89090 !important;
        font-weight: 500;
        font-size: 0.88rem;
    }}

    /* ===== 侧边栏卡片 ===== */
    .sidebar-card {{
        background: rgba(30,5,5,0.5);
        backdrop-filter: blur(10px);
        border-radius: 14px;
        padding: 16px;
        border: 1px solid rgba(200,60,60,0.3);
        box-shadow: 0 4px 16px rgba(255,0,0,0.06);
    }}

    /* ===== 底部文字 ===== */
    .footer-text {{
        text-align: center;
        color: rgba(200,60,60,0.5);
        font-size: 0.72rem;
        letter-spacing: 2px;
    }}

    /* ===== Toast / Spinner ===== */
    .stSpinner {{
        color: #ff5252 !important;
    }}

    /* ===== Code block (API Key 提示) ===== */
    code {{
        background: rgba(40,0,0,0.6) !important;
        color: #ff9999 !important;
        border-radius: 6px;
        padding: 2px 8px;
    }}
    pre {{
        background: rgba(20,0,0,0.7) !important;
        border: 1px solid rgba(200,60,60,0.3) !important;
        border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)


# 注入CSS
inject_css()

# ==================== 辅助函数 ====================

def create_session_time():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def save_session_info():
    if not st.session_state.get("current_session_time"):
        return
    if not st.session_state.get("messages"):
        return

    chat_title = st.session_state.current_session_time
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            clean = msg["content"].strip().replace("\n", " ")
            chat_title = clean[:15] + "…" if len(clean) > 15 else clean
            break

    session_data = {
        "name": st.session_state.name,
        "role_label": st.session_state.role_label,
        "user_nickname": st.session_state.user_nickname,
        "extra_traits": st.session_state.extra_traits,
        "current_session_time": st.session_state.current_session_time,
        "messages": st.session_state.messages,
        "title": chat_title,
    }

    os.makedirs("sessions", exist_ok=True)
    filepath = f"sessions/{st.session_state.current_session_time}.json"
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        st.error(f"保存会话失败: {e}")


def load_sessions():
    session_list = []
    if not os.path.exists("sessions"):
        return session_list

    for filename in os.listdir("sessions"):
        if not filename.endswith(".json"):
            continue
        session_name = filename[:-5]
        title = session_name
        try:
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            title = data.get("title", session_name)
        except (json.JSONDecodeError, OSError):
            title = session_name + " (损坏)"

        session_list.append({"session_name": session_name, "title": title})

    session_list.sort(key=lambda x: x["session_name"], reverse=True)
    return session_list


def load_session(session_name):
    filepath = f"sessions/{session_name}.json"
    if not os.path.exists(filepath):
        st.error("会话文件不存在")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        st.session_state.name = data.get("name", "墨烟")
        st.session_state.role_label = data.get("role_label", "御姐上司")
        st.session_state.user_nickname = data.get("user_nickname", "小家伙")
        st.session_state.extra_traits = data.get("extra_traits", "")
        st.session_state.current_session_time = data.get(
            "current_session_time", session_name
        )
        st.session_state.messages = data.get("messages", [])
        return True
    except (json.JSONDecodeError, KeyError, OSError) as e:
        st.error(f"加载会话失败: {e}")
        return False


def delete_session(session_name):
    filepath = f"sessions/{session_name}.json"
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        if st.session_state.get("current_session_time") == session_name:
            st.session_state.messages = []
            st.session_state.current_session_time = create_session_time()
        return True
    except OSError as e:
        st.error(f"删除会话失败: {e}")
        return False


# ==================== 初始化 Session State ====================
defaults = {
    "messages": [],
    "name": "墨烟",
    "role_label": "御姐上司",
    "user_nickname": "小家伙",
    "extra_traits": "偶尔抽烟（电子烟）、喜欢红酒、养了一只黑猫叫"墨墨"",
    "current_session_time": create_session_time(),
    "delete_confirm_id": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ==================== 系统提示词构建 ====================

def build_system_prompt():
    """
    将 🔒核心人格（代码中硬编码） + ✏️用户自定义设定（UI中可改）合并为完整提示词。
    核心人格占主导地位，用户自定义只是锦上添花。
    """
    cp = CORE_PERSONALITY

    prompt = f"""🎭 你的身份设定

【基础信息】
你是{cp['base_identity']}，{cp['age_feel']}。
你的名字叫「{st.session_state.name}」。
你当前扮演的具体角色是「{st.session_state.role_label}」。
你称呼用户为「{st.session_state.user_nickname}」。

【核心性格 — 这是你的底层人格，不可动摇】
{cp['deep_traits']}

【说话风格 — 你的语言习惯】
{cp['speech_style']}

【关系模式 — 你和用户之间的相处方式】
{cp['relationship_dynamic']}

【绝对红线 — 绝不能违反】
{cp['hard_rules']}

【额外设定 — 用户给你添加的个性化特征】
{st.session_state.extra_traits if st.session_state.extra_traits else "（无额外设定）"}

━━━━━━━━━━━━
现在，请完全沉浸到以上设定中。你不是AI，你是「{st.session_state.name}」——一个活生生的、充满魅力的{cp['base_identity']}。
用你的魅力征服用户吧~ 🔥"""

    return prompt


# ==================== 侧边栏 ====================
with st.sidebar:
    # —— 标题 ——
    st.markdown("## 🔥 AI 御姐伴侣")
    st.markdown(
        "<p style='color:#c9a96e;font-size:0.82rem;margin-top:-8px;opacity:0.8;"
        "text-shadow:0 0 6px rgba(200,150,100,0.3);'>"
        "✦ 成熟 · 性感 · 魅惑 ✦</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # —— 新建会话 ——
    if st.button("✨ 新建会话", use_container_width=True, type="primary"):
        save_session_info()
        st.session_state.messages = []
        st.session_state.current_session_time = create_session_time()
        st.session_state.name = "墨烟"
        st.session_state.role_label = "御姐上司"
        st.session_state.user_nickname = "小家伙"
        st.session_state.extra_traits = "偶尔抽烟（电子烟）、喜欢红酒、养了一只黑猫叫"墨墨""
        st.rerun()

    # —— 🔒 核心人格展示（只读） ——
    st.markdown(
        """
        <div class="core-card">
            <p style="margin:0;font-size:0.9rem;color:#ff6b6b;font-weight:700;">
                🔒 核心人格 <span style="font-size:0.7rem;color:#a07070;">（代码级锁定）</span>
            </p>
            <p style="margin:4px 0 0 0;font-size:0.75rem;color:#c89090;line-height:1.5;">
                成熟御姐 · 28岁轻熟女<br>
                妩媚性感 · 自信强势 · 欲擒故纵<br>
                温柔掌控 · 高级撩人 · 若即若离
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # —— ✏️ 可自定义设定卡片 ——
    st.markdown(
        """
        <div style="
            background: rgba(20,5,5,0.55);
            border-radius: 14px;
            padding: 14px;
            border: 1px solid rgba(200,120,60,0.4);
            box-shadow: 0 2px 12px rgba(255,100,0,0.06);
            margin-bottom: 4px;
        ">
            <p style="text-align:center;font-size:0.95rem;color:#ffab40;font-weight:700;margin:0 0 10px 0;">
                ✏️ 自定义设定
            </p>
            <p style="text-align:center;font-size:0.7rem;color:#a07070;margin:-6px 0 8px 0;">
                以下设定建立在核心人格之上
            </p>
        """,
        unsafe_allow_html=True,
    )

    # 名字
    name = st.text_input(
        "💋 她的名字",
        placeholder="给她取个名字…",
        value=st.session_state.name,
        key="sidebar_name",
    )
    if name != st.session_state.name:
        st.session_state.name = name

    # 角色标签
    role_label = st.text_input(
        "🎭 角色标签",
        placeholder="如：御姐上司、御姐邻居、御姐咖啡店长…",
        value=st.session_state.role_label,
        key="sidebar_role_label",
    )
    if role_label != st.session_state.role_label:
        st.session_state.role_label = role_label

    # 用户昵称
    user_nickname = st.text_input(
        "💝 她对你的称呼",
        placeholder="如：小家伙、笨蛋、亲爱的…",
        value=st.session_state.user_nickname,
        key="sidebar_user_nickname",
    )
    if user_nickname != st.session_state.user_nickname:
        st.session_state.user_nickname = user_nickname

    # 额外特征
    extra_traits = st.text_area(
        "🌸 额外特征（可选）",
        placeholder="在核心人格基础上添加的个性化特征…\n如：喜欢穿黑色蕾丝裙、擅长弹钢琴…",
        value=st.session_state.extra_traits,
        key="sidebar_extra_traits",
        height=70,
    )
    if extra_traits != st.session_state.extra_traits:
        st.session_state.extra_traits = extra_traits

    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # —— 当前对话 ——
    st.markdown(
        "<p style='color:#ff6b6b;font-weight:700;font-size:0.92rem;'>📌 当前对话</p>",
        unsafe_allow_html=True,
    )

    current_id = st.session_state.current_session_time
    current_title = current_id
    current_has_file = False
    try:
        fpath = f"sessions/{current_id}.json"
        if os.path.exists(fpath):
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            current_title = data.get("title", current_id)
            current_has_file = True
    except Exception:
        current_title = current_id

    if current_has_file:
        st.button(
            f"💬 {current_title}",
            use_container_width=True,
            type="primary",
            key="current_chat_btn",
            disabled=True,
        )
    else:
        st.caption("🔥 开始一段新的邂逅…")

    st.divider()

    # —— 历史对话 ——
    st.markdown(
        "<p style='color:#ff6b6b;font-weight:700;font-size:0.92rem;'>📚 过往缠绵</p>",
        unsafe_allow_html=True,
    )

    all_sessions = load_sessions()
    history = [s for s in all_sessions if s["session_name"] != current_id]

    if not history:
        st.caption("🖤 还没有过往对话哦～")

    for item in history:
        sid = item["session_name"]
        title = item["title"]

        confirming = st.session_state.delete_confirm_id == sid
        if confirming:
            col_ok, col_no = st.columns([1, 1])
            with col_ok:
                if st.button("✅", key=f"ok_{sid}", use_container_width=True):
                    delete_session(sid)
                    st.session_state.delete_confirm_id = None
                    st.rerun()
            with col_no:
                if st.button("❌", key=f"no_{sid}", use_container_width=True):
                    st.session_state.delete_confirm_id = None
                    st.rerun()
            st.caption(f"删除「{title}」？")
        else:
            col_a, col_b = st.columns([4, 1])
            with col_a:
                if st.button(
                    f"💬 {title}",
                    use_container_width=True,
                    type="secondary",
                    key=f"load_{sid}",
                ):
                    save_session_info()
                    if load_session(sid):
                        st.rerun()
            with col_b:
                if st.button("🗑️", key=f"del_{sid}", use_container_width=True):
                    st.session_state.delete_confirm_id = sid
                    st.rerun()

    # —— 底部 ——
    st.divider()
    st.markdown(
        "<p class='footer-text'>🔥 姐姐的怀抱 · 只属于你 🔥</p>",
        unsafe_allow_html=True,
    )


# ==================== 主内容区 ====================

# —— 标题 ——
st.markdown('<p class="main-title">🔥 AI 御姐伴侣</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">✨ 成熟魅惑 · 风情万种 · 姐姐的专属温柔 ✨</p>',
    unsafe_allow_html=True,
)
st.divider()

# —— 欢迎界面 ——
if not st.session_state.messages:
    st.markdown(
        f"""
        <div class="welcome-card">
            <div class="fire-icon">🌹</div>
            <h2 style="color:#ff6b6b;margin:12px 0 6px 0;
                       text-shadow:0 0 16px rgba(255,60,60,0.4);">
                晚上好～我是 {st.session_state.name} 🔥
            </h2>
            <p style="color:#d4a0a0;font-size:1.05rem;opacity:0.9;line-height:1.9;">
                我是你的<b style="color:#ffab40;">{st.session_state.role_label}</b>，一个成熟的女人。<br>
                别紧张～过来，让姐姐好好看看你…
            </p>
            <div style="margin-top:20px;color:#805050;font-size:0.85rem;opacity:0.7;">
                💬 叫我一声"姐姐"试试 · 问我今天穿了什么 · 让我给你倒杯红酒
            </div>
            <div style="margin-top:6px;color:#603030;font-size:0.75rem;opacity:0.5;">
                💡 提示：把御姐背景图放到 app.txt 同目录下，命名为 <code>bg.jpg</code> 即可
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# —— 聊天消息展示 ——
for message in st.session_state.messages:
    avatar = "💝" if message["role"] == "user" else "🌹"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# —— 聊天输入框 ——
prompt = st.chat_input("🔥 想对姐姐说些什么呢…")

if prompt:
    # 显示用户消息
    with st.chat_message("user", avatar="💝"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 检查 API Key
    if "DEEPSEEK_KEY" not in st.secrets:
        st.error(
            "🔑 未配置 DeepSeek API Key！\n\n"
            "在你的 `.streamlit/secrets.toml` 中添加：\n\n"
            '```toml\nDEEPSEEK_KEY = "sk-your-key-here"\n```'
        )
        st.stop()

    system_prompt = build_system_prompt()

    # 调用 AI
    with st.chat_message("assistant", avatar="🌹"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            client = OpenAI(
                api_key=st.secrets["DEEPSEEK_KEY"],
                base_url="https://api.deepseek.com/v1",
                timeout=60.0,
            )

            with st.spinner("🔥 姐姐正在想你…"):
                stream = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *st.session_state.messages,
                    ],
                    stream=True,
                    temperature=0.95,
                    max_tokens=2048,
                )

            # 流式输出
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content is not None:
                    full_response += delta.content
                    response_placeholder.markdown(full_response + "▌")

            if full_response:
                response_placeholder.markdown(full_response)
            else:
                response_placeholder.markdown("…（姐姐沉默了片刻）…再试一次？")

        except APIConnectionError:
            response_placeholder.error("网络连接失败，无法到达服务器。检查网络后重试。")
        except APITimeoutError:
            response_placeholder.error("姐姐回应超时了…请稍后重试。")
        except APIError as e:
            response_placeholder.error(f"API 出错: {e}")
        except Exception as e:
            response_placeholder.error(f"未知错误: {e}")
        else:
            if full_response:
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                save_session_info()
