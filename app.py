import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import json

#设置页面配置项
st.set_page_config(
    page_title="AI智能伴侣",
    page_icon="😏",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# ======================【美化CSS区域：全局渐变背景+聊天框样式】======================
# 这里是渐变背景代码，替换了你原来的纯色背景
st.markdown("""
<style>
/* 全局淡紫+浅蓝渐变背景 */
.stApp {
    background: linear-gradient(135deg,#f0e7ff,#e6f7ff);
}
/* 用户消息气泡样式 */
.stChatMessage.user {
    background-color: #e6f7ff;
    border-radius: 12px;
    padding: 10px;
}
/* AI回复气泡样式 */
.stChatMessage.assistant {
    background-color: #fff7e6;
    border-radius: 12px;
    padding: 10px;
}
/* 输入框圆角美化 */
.stTextInput, .stTextArea {
    border-radius: 8px;
}
/* 按钮渐变配色 */
.stButton>button {
    border-radius: 8px;
    background: linear-gradient(90deg,#722ed1,#1890ff);
    color:white;
}
/* 主标题居中 */
h1 {
    color:#1f2937;
    text-align:center;
}
</style>
""",unsafe_allow_html=True)
# ==============================================================================

#创建会话标识
def create_session_time():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

#保存会话信息函数
def save_session_info():
    if st.session_state.current_session_time:
        # 自动生成会话标题：取第一条用户消息，无消息则用时间
        chat_title = st.session_state.current_session_time
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                # 超过12个字截断加省略号
                if len(msg["content"]) > 12:
                    chat_title = msg["content"][:12] + "..."
                else:
                    chat_title = msg["content"]
                break

        session_data = {
            "role": st.session_state.role,
            "name": st.session_state.name,
            "gender": st.session_state.gender,
            "character": st.session_state.character,
            "current_session_time": st.session_state.current_session_time,
            "messages": st.session_state.messages,
            "title": chat_title  # 新增标题字段
        }
        # 创建文件夹
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        # 保存会话信息
        with open(f"sessions/{st.session_state.current_session_time}.json", "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=4)

#加载会话信息函数
def load_sessions():
    session_list=[]
    if os.path.exists("sessions"):
        file_list=os.listdir("sessions")
        for file_name in file_list:
            if file_name.endswith(".json"):
                session_name = file_name[:-5]
                # 读取json获取标题
                try:
                    with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                        data = json.load(f)
                    title = data.get("title", session_name)
                except Exception:
                    title = session_name
                session_list.append({
                    "session_name": session_name,
                    "title": title
                })
    # 倒序：最新会话在最上方
    session_list.sort(key=lambda x:x["session_name"], reverse=True)
    return session_list

#加载指定的会话信息
def load_session(session_name):
    if os.path.exists(f"sessions/{session_name}.json"):
        try:
            with open(f"sessions/{session_name}.json", "r", encoding="utf-8") as f:
                session_data = json.load(f)
                st.session_state.role = session_data["role"]
                st.session_state.name = session_data["name"]
                st.session_state.gender = session_data["gender"]
                st.session_state.character = session_data["character"]
                st.session_state.current_session_time = session_data["current_session_time"]
                st.session_state.messages = session_data["messages"]
        except Exception:
               st.error("加载会话信息失败")
#删除指定会话信息
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json") #删除指定会话文件
            #如果删除是当前会话，则创建新的会话，更新消息列表
            if session_name == st.session_state.current_session_time:
                st.session_state.messages = []
                st.session_state.current_session_time = create_session_time()
    except Exception:
        st.error("删除会话信息失败!")


# ======================【主页面大标题美化代码】======================
# 替换了原来光秃秃的 st.title("AI智能伴侣")
st.markdown("# 💜 AI智能伴侣", unsafe_allow_html=True)
st.divider()
# ===================================================================

#系统提示词
system_prompt = """你是一名的%s,你的名字叫%s，性别%s,请你%s的语气回答客户的问题.
                  
                """

 #初始化聊天信息
if 'messages' not in st.session_state:
    st.session_state.messages = []

#角色
if 'role' not in st.session_state:
    st.session_state.role = "秘书"

#昵称
if 'name' not in st.session_state:
    st.session_state.name = "妖夜"

#性别
if 'gender' not in st.session_state:
    st.session_state.gender = "女"

#性格
if 'character' not in st.session_state:
    st.session_state.character = "妩媚性感"

#会话标识
if 'current_session_time' not in st.session_state:
    st.session_state.current_session_time = create_session_time()

#左侧边栏
with st.sidebar:
    # ======================【侧边栏标题美化代码】======================
    st.markdown("## 💜 AI智能伴侣控制台")
    st.divider()
    # =================================================================

    #新建会话
    if st.button("新建会话",width="stretch",icon="🖋️"):
        #1.保存当前会话信息
        save_session_info()

        #2.创建新的会话
        st.session_state.messages = []
        st.session_state.current_session_time = create_session_time()
        st.session_state.role = "秘书"
        st.session_state.name = "妖夜"
        st.session_state.gender = "女"
        st.session_state.character = "妩媚性感"
        st.rerun()

    st.subheader("伴侣信息")
    # ======================【白色圆角卡片包裹4个输入框】======================
    # 先打开卡片容器
    st.markdown("""
    <div style="background:white;padding:16px;border-radius:12px;box-shadow:0 2px 8px #eee;">
    """,unsafe_allow_html=True)

    # 4个输入框全部放在卡片内部（关键修复：之前写在卡片外面）
    #扮演角色
    role=st.text_input("请输入智能伴侣扮演的角色:",placeholder="请输入智能伴侣扮演的角色", value=st.session_state.role)
    if role != st.session_state.role:
        st.session_state.role = role
    #昵称输入框
    name=st.text_input("请输入伴侣昵称:",placeholder="请输入伴侣昵称", value=st.session_state.name)
    if name != st.session_state.name:
        st.session_state.name = name
    #性别输入框
    gender=st.text_input("请输入伴侣性别:",placeholder="请输入伴侣性别", value=st.session_state.gender)
    if gender != st.session_state.gender:
        st.session_state.gender = gender
    #性格输入框
    character=st.text_area("请输入伴侣性格:",placeholder="请输入伴侣性格", value=st.session_state.character)
    if character != st.session_state.character:
        st.session_state.character = character

    # 闭合卡片容器（输入框写完再关闭div）
    st.markdown("</div>",unsafe_allow_html=True)
    # ======================================================================

    # 分割线
    st.divider()
    # ===== 第一块：当前对话（只展示标题，不显示时间串） =====
    st.subheader("当前对话")
    current_id = st.session_state.current_session_time
    current_title = current_id
    try:
        with open(f"sessions/{current_id}.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            # 优先读取标题
            current_title = data.get("title", current_id)
    except Exception:
        current_title = current_id

    # 按钮只展示标题文字
    if st.button(
            label=f"📄 {current_title}",
            width="stretch",
            type="primary",
            key="current_chat_btn"
    ):
        load_session(current_id)
        st.rerun()

    st.divider()
    # ===== 第二块：历史对话列表 =====
    st.subheader("历史对话")
    all_sessions = load_sessions()
    # 过滤掉当前会话，只展示旧会话
    history_list = [item for item in all_sessions if item["session_name"] != current_id]

    if not history_list:
        st.caption("暂无历史对话")
    else:
        for item in history_list:
            sid = item["session_name"]
            show_title = item["title"]
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(
                        label=f"📄 {show_title}",
                        width="stretch",
                        type="secondary",
                        key=f"load_{sid}"
                ):
                    load_session(sid)
                    st.rerun()
            with col2:
                if st.button("", icon="🗑️", width="stretch", key=f"del_{sid}"):
                    delete_session(sid)
                    st.rerun()

#展示聊天信息
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

#创建OpenAI客户端
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_KEY"],
    base_url="https://api.deepseek.com/v1"
)

#输入框
prompt = st.chat_input("请输入你咨询的问题")
if prompt:
   st.chat_message("user").write(prompt)
   print("调用AI大模型的提示词:", prompt)
   #保存用户的提示词
   st.session_state.messages.append({"role": "user", "content": prompt})

   #调用AI大模型
   response = client.chat.completions.create(
       model="deepseek-v4-pro",
       messages=[
           {"role": "system", "content":system_prompt % (st.session_state.role, st.session_state.name, st.session_state.gender, st.session_state.character)},
            *st.session_state.messages
       ],
       stream=True,
       reasoning_effort="high",
       extra_body={"thinking": {"type": "enabled"}}
   )

   #流式输出
   response_message=st.empty()
   full_response = ""
   for chunk in response:
       if chunk.choices[0].delta.content is not None:
           content = chunk.choices[0].delta.content
           full_response += content
           response_message.chat_message("assistant").write(full_response)

   #保存AI大模型的返回结果
   st.session_state.messages.append({"role": "assistant", "content": full_response})
   #保存会话信息
   save_session_info()