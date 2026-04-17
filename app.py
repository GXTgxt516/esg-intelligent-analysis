import streamlit as st
import fitz
import os
import requests
import json

# --------------------------
# 页面配置
# --------------------------
st.set_page_config(
    page_title="ESG智能解析系统",
    page_icon="📊",
    layout="wide"
)

st.title("📊 ESG智能报告解析系统")
st.markdown("✅ 支持连续对话 | ✅ 历史记录保存 | ✅ 自动生成高频问题")

# --------------------------
# 初始化会话状态
# --------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "auto_questions" not in st.session_state:
    st.session_state.auto_questions = []

# --------------------------
# API KEY
# --------------------------
API_KEY = os.getenv("API_KEY")

# --------------------------
# 上传 PDF（支持重复上传）
# --------------------------
st.subheader("1️⃣ 上传 ESG 报告 PDF")
uploaded_file = st.file_uploader("选择PDF文件", type="pdf", key="pdf_uploader")

if uploaded_file is not None:
    with st.spinner("正在解析PDF..."):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        
        # 保存文本
        st.session_state.pdf_text = text[:9000]

        # ======================
        # 自动生成高频常见问题
        # ======================
        prompt_questions = f"""
        你是ESG分析师，请根据这份ESG报告，自动生成8个用户最可能问的常见问题。
        只返回问题列表，不要多余解释。
        报告内容：
        {st.session_state.pdf_text}
        """

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "qwen-turbo",
            "messages": [{"role": "user", "content": prompt_questions}]
        }

        res = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            data=json.dumps(data)
        )

        if res.status_code == 200:
            qs = res.json()["output"]["text"]
            st.session_state.auto_questions = qs.strip().split("\n")
        else:
            st.session_state.auto_questions = ["生成常见问题失败，请重试"]

        st.success("✅ PDF解析成功！常见问题已自动生成！")

# --------------------------
# 自动生成的常问问题
# --------------------------
if st.session_state.auto_questions:
    st.subheader("📋 系统自动生成的高频问题")
    for q in st.session_state.auto_questions:
        if q.strip():
            if st.button(q.strip()):
                st.session_state.auto_click = q.strip()

# --------------------------
# 聊天历史展示
# --------------------------
st.subheader("2️⃣ 智能问答（支持连续对话）")
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(chat["user"])
    with st.chat_message("assistant"):
        st.write(chat["ai"])

# --------------------------
# 输入框
# --------------------------
user_question = st.chat_input("请输入你的问题...")

# 处理自动点击常见问题
if "auto_click" in st.session_state and st.session_state.auto_click:
    user_question = st.session_state.auto_click
    st.session_state.auto_click = ""

if user_question:
    if not st.session_state.pdf_text:
        st.warning("⚠️ 请先上传PDF文件！")
    else:
        with st.chat_message("user"):
            st.write(user_question)

        #  you: 构建上下文 + 历史对话
        prompt = f"""
        你是专业ESG报告分析师，回答专业、简洁、有条理。
        报告内容：
        {st.session_state.pdf_text}

        历史对话：
        {st.session_state.chat_history}

        用户问题：{user_question}
        """

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "qwen-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }

        response = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            data=json.dumps(data)
        )

        if response.status_code == 200:
            answer = response.json()["output"]["text"]
        else:
            answer = "❌ API调用失败"

        # 显示回答
        with st.chat_message("assistant"):
            st.write(answer)

        # 保存历史
        st.session_state.chat_history.append({
            "user": user_question,
            "ai": answer
        })
