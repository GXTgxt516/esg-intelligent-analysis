import streamlit as st
import fitz
import os
import requests
import json
from io import BytesIO
from docx import Document

# --------------------------
# 全局页面配置（保持完整UI）
# --------------------------
st.set_page_config(
    page_title="ESG智能解析系统",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# 自定义美化CSS（还原你之前的好看界面）
# --------------------------
st.markdown("""
<style>
.main-title {
    font-size: 3rem !important;
    font-weight: 700;
    color: #1E3A8A;
    text-align: center;
    margin-bottom: 2rem;
    padding: 1rem;
    background: linear-gradient(90deg, #EFF6FF, #DBEAFE);
    border-radius: 12px;
}
.subtitle {
    font-size: 1.5rem !important;
    font-weight: 600;
    color: #1E40AF;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
}
.chat-container {
    background-color: #F8FAFC;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
}
.user-message {
    background-color: #DBEAFE;
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 0.5rem;
}
.ai-message {
    background-color: #F0FDF4;
    padding: 1rem;
    border-radius: 12px;
    margin-bottom: 0.5rem;
}
.auto-question-btn {
    background-color: #EFF6FF;
    color: #1E40AF;
    border: 1px solid #BFDBFE;
    border-radius: 8px;
    padding: 0.5rem 1rem;
    margin: 0.3rem;
    font-size: 0.9rem;
}
.auto-question-btn:hover {
    background-color: #DBEAFE;
    border-color: #1E40AF;
}
</style>
""", unsafe_allow_html=True)

# --------------------------
# 初始化会话状态（所有功能都需要）
# --------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

if "auto_questions" not in st.session_state:
    st.session_state.auto_questions = []

if "trigger_question" not in st.session_state:
    st.session_state.trigger_question = None

# --------------------------
# API KEY 安全读取
# --------------------------
API_KEY = os.getenv("API_KEY")

# --------------------------
# 页面标题（美化版）
# --------------------------
st.markdown('<div class="main-title">🌱 ESG智能解析系统</div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#4B5563; margin-bottom:2rem;">
✅ 支持连续对话 | ✅ 历史记录自动保存 | ✅ 根据报告自动生成高频问题 | ✅ 回答一键导出
</div>
""", unsafe_allow_html=True)

# --------------------------
# 侧边栏：文件上传与管理（还原侧边栏）
# --------------------------
with st.sidebar:
    st.header("📁 文件管理")
    uploaded_file = st.file_uploader("上传ESG报告PDF", type="pdf", key="pdf_uploader")

    if uploaded_file is not None:
        with st.spinner("正在解析PDF并生成高频问题..."):
            # 解析PDF
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            
            # 保存文本（限制长度避免超出API限制）
            st.session_state.pdf_text = text[:9000]

            # 自动生成高频问题
            prompt_questions = f"""
            你是专业的ESG分析师，请根据以下ESG报告内容，生成8个用户最可能提问的高频问题，只返回问题列表，不要多余解释。
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
                st.session_state.auto_questions = [q.strip() for q in qs.strip().split("\n") if q.strip()]
            else:
                st.session_state.auto_questions = ["生成问题失败，请重试"]

            st.success("✅ 解析完成！已自动生成高频问题")

    # 侧边栏功能按钮
    st.divider()
    if st.button("🗑️ 清空对话历史", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.auto_questions = []
        st.session_state.pdf_text = ""
        st.rerun()

    # 导出功能（还原你之前的导出）
    if st.session_state.chat_history:
        if st.button("📥 导出对话记录为Word", use_container_width=True):
            doc = Document()
            doc.add_heading("ESG智能解析对话记录", 0)
            for chat in st.session_state.chat_history:
                doc.add_heading("用户问题", level=1)
                doc.add_paragraph(chat["user"])
                doc.add_heading("AI回答", level=1)
                doc.add_paragraph(chat["ai"])
                doc.add_page_break()
            bio = BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.download_button(
                label="下载Word文件",
                data=bio,
                file_name="ESG解析对话记录.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

# --------------------------
# 主界面：自动生成的高频问题（美化版）
# --------------------------
if st.session_state.auto_questions:
    st.markdown('<div class="subtitle">📋 系统自动生成的高频问题（点击直接提问）</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, q in enumerate(st.session_state.auto_questions):
        with cols[i % 2]:
            if st.button(q, key=f"q_{i}", use_container_width=True, type="primary"):
                st.session_state.trigger_question = q

# --------------------------
# 主界面：对话历史展示（美化版）
# --------------------------
st.markdown('<div class="subtitle">💬 智能问答（支持连续对话）</div>', unsafe_allow_html=True)
with st.container():
    for chat in st.session_state.chat_history:
        st.markdown(f'<div class="user-message"><strong>用户：</strong>{chat["user"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-message"><strong>AI：</strong>{chat["ai"]}</div>', unsafe_allow_html=True)

# --------------------------
# 对话输入框 + 处理逻辑
# --------------------------
user_question = st.chat_input("请输入你的问题，或点击上方的高频问题...")

# 处理点击高频问题触发的提问
if st.session_state.trigger_question is not None:
    user_question = st.session_state.trigger_question
    st.session_state.trigger_question = None

if user_question:
    if not st.session_state.pdf_text:
        st.warning("⚠️ 请先在侧边栏上传PDF文件！")
    else:
        # 构建带上下文的prompt
        prompt = f"""
        你是专业的ESG报告分析师，请根据以下报告内容和历史对话，回答用户的问题，回答要专业、简洁、有条理。
        报告内容：
        {st.session_state.pdf_text}

        历史对话：
        {st.session_state.chat_history}

        用户当前问题：{user_question}
        """

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "qwen-turbo",
            "messages": [{"role": "user", "content": prompt}]
        }

        with st.spinner("AI正在分析回答..."):
            response = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                data=json.dumps(data)
            )

        if response.status_code == 200:
            answer = response.json()["output"]["text"]
        else:
            answer = "❌ API调用失败，请检查你的API Key或网络连接"

        # 保存对话历史
        st.session_state.chat_history.append({
            "user": user_question,
            "ai": answer
        })

        # 刷新页面显示新对话
        st.rerun()
