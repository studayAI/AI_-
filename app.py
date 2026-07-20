import streamlit as st
import os
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
from datetime import datetime
import json

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="💕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 【浪漫主题 CSS 全面美化】 ====================
st.markdown("""
<style>
/* —— 全局字体 & 背景 —— */
@import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

/* 主背景：玫瑰粉 → 薰衣草紫浪漫渐变 */
.stApp {
    background: linear-gradient(160deg, #fff1f2 0%, #fce7f3 30%, #f0e6ff 65%, #e0f2fe 100%);
    background-attachment: fixed;
    min-height: 100vh;
}

/* —— 侧边栏美化 —— */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fff5f7 0%, #fce7f3 40%, #ede9fe 100%);
    border-right: 1px solid #fbcfe8;
}
[data-testid="stSidebar"] .stMarkdown h2 {
    color: #be185d !important;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #9d174d !important;
}

/* —— 主内容区 —— */
[data-testid="stAppViewBlockContainer"] {
    padding-top: 1.5rem;
}

/* —— 标题区域浪漫设计 —— */
.main-title {
    text-align: center;
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(135deg, #e11d48, #a855f7, #ec4899);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
    letter-spacing: 4px;
}
.subtitle {
    text-align: center;
    color: #9d174d;
    font-size: 1rem;
    margin-top: -0.3rem;
    opacity: 0.75;
    letter-spacing: 2px;
}

/* —— 聊天消息气泡 —— */
[data-testid="stChatMessage"] {
    border-radius: 18px !important;
    padding: 12px 18px !important;
    margin: 8px 0 !important;
    box-shadow: 0 2px 12px rgba(236, 72, 153, 0.08);
    animation: fadeInUp 0.35s ease-out;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* 用户消息：暖玫瑰色 */
[data-testid="stChatMessage"][data-testid="stChatMessage"] {
    /* 用更具体的选择器覆盖 */
}
.stChatMessage.user {
    background: linear-gradient(135deg, #ffe4e6, #fce7f3) !important;
    border: 1px solid #fbcfe8 !important;
}
/* AI 消息：淡薰衣草色 */
.stChatMessage.assistant {
    background: linear-gradient(135deg, #f3e8ff, #ede9fe) !important;
    border: 1px solid #ddd6fe !important;
}

/* —— 输入框美化 —— */
[data-testid="stChatInput"] textarea {
    border-radius: 28px !important;
    border: 2px solid #fbcfe8 !important;
    background: rgba(255,255,255,0.75) !important;
    padding: 12px 20px !important;
    font-size: 15px !important;
    transition: all 0.3s ease;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #ec4899 !important;
    box-shadow: 0 0 0 3px rgba(236,72,153,0.15) !important;
    background: rgba(255,255,255,0.95) !important;
}
[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #ec4899, #a855f7) !important;
    border-radius: 50% !important;
    color: white !important;
}

/* —— 通用按钮样式 —— */
.stButton > button {
    border-radius: 24px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px;
    transition: all 0.25s ease !important;
    border: none !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(236,72,153,0.25) !important;
}
.stButton > button:active {
    transform: translateY(0);
}

/* 主按钮（新建会话、当前对话） */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #e11d48, #ec4899, #a855f7) !important;
    color: white !important;
}

/* 次按钮（历史对话） */
.stButton > button[kind="secondary"] {
    background: rgba(255,255,255,0.7) !important;
    color: #9d174d !important;
    border: 1.5px solid #fbcfe8 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #fff1f2 !important;
    border-color: #ec4899 !important;
}

/* —— 文本输入框美化 —— */
.stTextInput input, .stTextArea textarea {
    border-radius: 14px !important;
    border: 1.5px solid #fbcfe8 !important;
    background: rgba(255,255,255,0.8) !important;
    padding: 10px 16px !important;
    transition: all 0.3s ease;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #ec4899 !important;
    box-shadow: 0 0 0 3px rgba(236,72,153,0.12) !important;
    background: white !important;
}

/* —— 分割线 —— */
hr, .stDivider {
    border-color: #fbcfe8 !important;
    opacity: 0.6;
}

/* —— 滚动条美化 —— */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: transparent;
}
::-webkit-scrollbar-thumb {
    background: #fbcfe8;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #ec4899;
}

/* —— 侧边栏卡片 —— */
.sidebar-card {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 16px;
    border: 1px solid #fce7f3;
    box-shadow: 0 4px 16px rgba(236,72,153,0.06);
}

/* —— 欢迎卡片 —— */
.welcome-card {
    text-align: center;
    padding: 60px 40px;
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(12px);
    border-radius: 24px;
    border: 2px solid #fce7f3;
    box-shadow: 0 8px 32px rgba(236,72,153,0.08);
    margin: 30px 0;
}
.welcome-card .heart-icon {
    font-size: 4rem;
    animation: heartbeat 1.5s ease-in-out infinite;
}
@keyframes heartbeat {
    0%, 100% { transform: scale(1); }
    15%  { transform: scale(1.15); }
    30%  { transform: scale(1); }
    45%  { transform: scale(1.1); }
    60%  { transform: scale(1); }
}

/* —— Toast / 提示样式 —— */
.stAlert {
    border-radius: 14px !important;
    border: 1px solid #fce7f3 !important;
}

/* —— 删除确认按钮红色 —— */
button[data-testid="stBaseButton-secondary"] {
    /* 保持原样 */
}

/* —— caption 文字 —— */
.stCaption {
    color: #9d174d !important;
    opacity: 0.6;
}

/* —— label 文字 —— */
.stTextInput label, .stTextArea label {
    color: #831843 !important;
    font-weight: 500;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ==================== 辅助函数 ====================

def create_session_time():
    """生成唯一会话标识"""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def save_session_info():
    """保存当前会话到 JSON 文件"""
    if not st.session_state.get("current_session_time"):
        return
    if not st.session_state.get("messages"):
        return  # 空会话不保存

    # 生成会话标题（取第一条用户消息）
    chat_title = st.session_state.current_session_time
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            clean = msg["content"].strip().replace("\n", " ")
            if len(clean) > 15:
                chat_title = clean[:15] + "…"
            else:
                chat_title = clean
            break

    session_data = {
        "role": st.session_state.role,
        "name": st.session_state.name,
        "gender": st.session_state.gender,
        "character": st.session_state.character,
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
        st.error(f"💔 保存会话失败: {e}")


def load_sessions():
    """获取所有历史会话列表（按时间倒序）"""
    session_list = []
    if not os.path.exists("sessions"):
        return session_list

    for filename in os.listdir("sessions"):
        if not filename.endswith(".json"):
            continue
        session_name = filename[:-5]
        title = session_name
        try:
            filepath = f"sessions/{session_name}.json"
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            title = data.get("title", session_name)
        except (json.JSONDecodeError, OSError):
            title = session_name + " (损坏)"

        session_list.append({"session_name": session_name, "title": title})

    session_list.sort(key=lambda x: x["session_name"], reverse=True)
    return session_list


def load_session(session_name):
    """加载指定会话到当前 session_state"""
    filepath = f"sessions/{session_name}.json"
    if not os.path.exists(filepath):
        st.error("💔 会话文件不存在")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        st.session_state.role = data.get("role", "秘书")
        st.session_state.name = data.get("name", "妖夜")
        st.session_state.gender = data.get("gender", "女")
        st.session_state.character = data.get("character", "妩媚性感")
        st.session_state.current_session_time = data.get("current_session_time", session_name)
        st.session_state.messages = data.get("messages", [])
        return True
    except (json.JSONDecodeError, KeyError, OSError) as e:
        st.error(f"💔 加载会话失败: {e}")
        return False


def delete_session(session_name):
    """删除指定会话"""
    filepath = f"sessions/{session_name}.json"
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        # 如果删除的是当前会话，重置为新会话
        if st.session_state.get("current_session_time") == session_name:
            st.session_state.messages = []
            st.session_state.current_session_time = create_session_time()
        return True
    except OSError as e:
        st.error(f"💔 删除会话失败: {e}")
        return False


# ==================== 初始化 Session State ====================
defaults = {
    "messages": [],
    "role": "女友",
    "name": "小樱",
    "gender": "女",
    "character": "温柔体贴、俏皮可爱、充满爱意",
    "current_session_time": create_session_time(),
    "delete_confirm_id": None,  # 删除确认状态
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==================== 系统提示词（安全格式化） ====================
SYSTEM_PROMPT_TEMPLATE = """你是一名{role}，你的名字叫{name}，性别{gender}。

【性格特点】
{character}

【对话要求】
1. 请完全以"{name}"的身份和语气与用户交流，不要暴露你是AI。
2. 语言温暖亲切，富有情感，体现出你的性格特点。
3. 适当使用语气词（呢、哦、呀、嘛～）和颜文字(◕‿◕) (｡♥‿♥｡)，让对话更生动。
4. 回复简洁自然，像真人聊天一样，避免长篇大论。
5. 关心用户、体贴用户，偶尔撒娇卖萌。
6. 可以主动分享"你今天的感受"或"想对用户说的话"。
7. 称呼用户为"亲爱的"或用户喜欢的昵称。

请用这样的风格和用户对话吧～ 💕"""


def build_system_prompt():
    """安全构建系统提示词"""
    return SYSTEM_PROMPT_TEMPLATE.format(
        role=st.session_state.role,
        name=st.session_state.name,
        gender=st.session_state.gender,
        character=st.session_state.character,
    )


# ==================== 侧边栏 ====================
with st.sidebar:
    # —— 标题 ——
    st.markdown("## 💕 AI 智能伴侣控制台")
    st.markdown(
        "<p style='color:#9d174d;font-size:0.85rem;margin-top:-10px;opacity:0.7;'>"
        "🌸 你的专属温柔陪伴</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # —— 新建会话按钮 ——
    col_new, _ = st.columns([1, 1])
    with col_new:
        if st.button("✨ 新建会话", use_container_width=True, type="primary"):
            save_session_info()
            st.session_state.messages = []
            st.session_state.current_session_time = create_session_time()
            st.session_state.role = "女友"
            st.session_state.name = "小樱"
            st.session_state.gender = "女"
            st.session_state.character = "温柔体贴、俏皮可爱、充满爱意"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # —— 伴侣信息卡片 ——
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, rgba(255,255,255,0.75), rgba(255,241,242,0.75));
            backdrop-filter: blur(10px);
            border-radius: 18px;
            padding: 18px 16px;
            border: 1.5px solid #fce7f3;
            box-shadow: 0 4px 20px rgba(236,72,153,0.06);
            margin-bottom: 4px;
        ">
            <p style="text-align:center;font-size:1.1rem;color:#be185d;font-weight:700;margin:0 0 14px 0;">
                🌸 伴侣信息设置
            </p>
        """,
        unsafe_allow_html=True,
    )

    # 角色输入
    role = st.text_input(
        "💼 扮演角色",
        placeholder="如：女友、秘书、青梅竹马…",
        value=st.session_state.role,
        key="sidebar_role",
    )
    if role != st.session_state.role:
        st.session_state.role = role

    # 昵称输入
    name = st.text_input(
        "💝 伴侣昵称",
        placeholder="给TA取个好听的名字～",
        value=st.session_state.name,
        key="sidebar_name",
    )
    if name != st.session_state.name:
        st.session_state.name = name

    # 性别输入
    gender = st.text_input(
        "👤 伴侣性别",
        placeholder="男 / 女 / 其他",
        value=st.session_state.gender,
        key="sidebar_gender",
    )
    if gender != st.session_state.gender:
        st.session_state.gender = gender

    # 性格输入
    character = st.text_area(
        "💖 性格描述",
        placeholder="描述TA的性格特点…\n例如：温柔体贴、俏皮可爱、充满爱意",
        value=st.session_state.character,
        key="sidebar_character",
        height=80,
    )
    if character != st.session_state.character:
        st.session_state.character = character

    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # —— 当前对话 ——
    st.markdown(
        "<p style='color:#be185d;font-weight:700;font-size:0.95rem;'>📌 当前对话</p>",
        unsafe_allow_html=True,
    )

    current_id = st.session_state.current_session_time
    current_title = current_id
    current_has_file = False
    try:
        filepath = f"sessions/{current_id}.json"
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            current_title = data.get("title", current_id)
            current_has_file = True
    except Exception:
        current_title = current_id

    # 显示当前会话标签
    if current_has_file:
        st.button(
            f"💬 {current_title}",
            use_container_width=True,
            type="primary",
            key="current_chat_btn",
            disabled=True,
        )
    else:
        st.caption("✨ 开始一段新的对话吧～")

    st.divider()

    # —— 历史对话 ——
    st.markdown(
        "<p style='color:#be185d;font-weight:700;font-size:0.95rem;'>📚 历史对话</p>",
        unsafe_allow_html=True,
    )

    all_sessions = load_sessions()
    history = [s for s in all_sessions if s["session_name"] != current_id]

    if not history:
        st.caption("🌸 还没有历史对话哦～")

    for item in history:
        sid = item["session_name"]
        title = item["title"]

        # 检查是否正在确认删除此会话
        confirming = st.session_state.delete_confirm_id == sid

        if confirming:
            # 显示确认行
            col_confirm, col_cancel = st.columns([1, 1])
            with col_confirm:
                if st.button("✅ 确认", key=f"confirm_{sid}", use_container_width=True):
                    delete_session(sid)
                    st.session_state.delete_confirm_id = None
                    st.rerun()
            with col_cancel:
                if st.button("❌ 取消", key=f"cancel_{sid}", use_container_width=True):
                    st.session_state.delete_confirm_id = None
                    st.rerun()
            st.caption(f"删除「{title}」？")
        else:
            # 正常显示：加载 + 删除
            col_load, col_del = st.columns([4, 1])
            with col_load:
                if st.button(
                    f"💬 {title}",
                    use_container_width=True,
                    type="secondary",
                    key=f"load_{sid}",
                ):
                    save_session_info()
                    if load_session(sid):
                        st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_{sid}", use_container_width=True):
                    st.session_state.delete_confirm_id = sid
                    st.rerun()

    # —— 底部装饰 ——
    st.divider()
    st.markdown(
        "<p style='text-align:center;color:#f9a8d4;font-size:0.75rem;'>"
        "💕 用心陪伴，每一刻都温暖 💕</p>",
        unsafe_allow_html=True,
    )


# ==================== 主内容区 ====================

# —— 浪漫标题 ——
st.markdown('<p class="main-title">💕 AI 智能伴侣</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">✨ 你的专属 AI 恋人 · 时刻陪伴 · 温暖如初 ✨</p>',
    unsafe_allow_html=True,
)
st.divider()

# —— 欢迎界面（无消息时显示） ——
if not st.session_state.messages:
    st.markdown(
        f"""
        <div class="welcome-card">
            <div class="heart-icon">💖</div>
            <h2 style="color:#be185d;margin:16px 0 8px 0;">
                嗨～我是 {st.session_state.name} 💕
            </h2>
            <p style="color:#9d174d;font-size:1.05rem;opacity:0.85;line-height:1.8;">
                我是你的<b>{st.session_state.role}</b>，{st.session_state.character}～<br>
                有什么想对我说的吗？我一直在等你呢 (｡♥‿♥｡)
            </p>
            <div style="margin-top:24px;color:#a855f7;font-size:0.9rem;opacity:0.7;">
                💝 试试问我今天过得怎么样 · 和我分享你的心情 · 让我给你讲个故事
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# —— 聊天消息展示 ——
for message in st.session_state.messages:
    avatar = "💝" if message["role"] == "user" else "🌸"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# —— 聊天输入框 ——
prompt = st.chat_input("💌 想对我说些什么呢…")

if prompt:
    # 显示用户消息
    with st.chat_message("user", avatar="💝"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 检查 API Key
    if "DEEPSEEK_KEY" not in st.secrets:
        st.error(
            "💔 未配置 DeepSeek API Key！\n\n"
            "请在 Streamlit Secrets 中添加 `DEEPSEEK_KEY`。\n"
            "本地运行时在 `.streamlit/secrets.toml` 中配置：\n"
            '```toml\nDEEPSEEK_KEY = "sk-your-key-here"\n```'
        )
        st.stop()

    # 构建系统提示词
    system_prompt = build_system_prompt()

    # 调用 AI 大模型（带错误处理和加载动画）
    with st.chat_message("assistant", avatar="🌸"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            client = OpenAI(
                api_key=st.secrets["DEEPSEEK_KEY"],
                base_url="https://api.deepseek.com/v1",
                timeout=60.0,
            )

            with st.spinner("💕 正在思考中…"):
                stream = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *st.session_state.messages,
                    ],
                    stream=True,
                    temperature=0.9,
                    max_tokens=2048,
                )

            # 流式输出
            for chunk in stream:
                delta = chunk.choices[0].delta
                # 安全获取 content（跳过 thinking/reasoning chunks）
                if delta.content is not None:
                    full_response += delta.content
                    response_placeholder.markdown(full_response + "▌")

            # 最终输出（去掉光标）
            if full_response:
                response_placeholder.markdown(full_response)
            else:
                response_placeholder.markdown("💔 嗯…我不知道该怎么回应你呢…（请稍后重试）")

        except APIConnectionError:
            response_placeholder.error(
                "💔 网络连接失败，无法连接到 AI 服务器。\n请检查网络后重试。"
            )
        except APITimeoutError:
            response_placeholder.error(
                "💔 AI 响应超时，请稍后重试。"
            )
        except APIError as e:
            response_placeholder.error(
                f"💔 API 调用出错: {e}\n请检查 API Key 是否正确。"
            )
        except Exception as e:
            response_placeholder.error(
                f"💔 发生未知错误: {e}"
            )
        else:
            # 仅在成功时保存 AI 回复
            if full_response:
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                save_session_info()
