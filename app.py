import streamlit as st
import fitz
import requests
import os
from io import BytesIO
from docx import Document

# ====================== API KEY ======================
API_KEY = os.getenv("API_KEY", "sk-0df70470c0d04e79af0bd705e804db68")
# ======================================================

# 页面配置
st.set_page_config(page_title="ESG智能解析系统", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")

# 自定义CSS（完全保留你原来的样式）
st.markdown("""
<style>
    .main-title {font-size: 3rem !important; font-weight: 700; color: #1E3A8A; text-align: center; margin-bottom: 2rem; padding: 1rem; background: linear-gradient(90deg, #E0F2FE, #D1FAE5); border-radius: 12px;}
    .stFileUploader {padding: 1.5rem; background: #F8FAFC; border-radius: 12px; border: 2px dashed #94A3B8; margin-bottom: 1.5rem;}
    .success-box {background: #D1FAE5; border-left: 4px solid #10B981; padding: 1rem; border-radius: 8px; margin: 1rem 0;}
    .answer-box {background: #F0F9FF; border-left: 4px solid #3B82F6; padding: 1.5rem; border-radius: 8px; margin-top: 1rem;}
    .summary-box {background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;}
    .stButton>button {border-radius: 8px; padding: 0.5rem 1rem; font-weight: 600;}
</style>
""", unsafe_allow_html=True)

# ====================== 会话状态（保存历史） ======================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_pdf_text" not in st.session_state:
    st.session_state.current_pdf_text = ""

if "auto_questions" not in st.session_state:
    st.session_state.auto_questions = []

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

# =================================================================

# 侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/leaf.png", width=80)
    st.title("ESG智能解析系统")
    st.markdown("---")
    st.subheader("📌 项目介绍")
    st.write("本系统基于大语言模型，实现ESG报告的智能解析、摘要生成与自然语言问答，助力企业ESG信息高效提取与分析。")
    st.markdown("---")
    
    # 清空对话
    if st.button("🗑️ 清空对话历史"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.caption("© 2025 大创项目组")

# 主标题
st.markdown('<h1 class="main-title">🌱 ESG报告智能解析与问答平台</h1>', unsafe_allow_html=True)

# ====================== 【功能1：多文件上传】 ======================
st.subheader("📁 上传多个ESG报告PDF")
uploaded_files = st.file_uploader("", type="pdf", accept_multiple_files=True, label_visibility="collapsed")

# 提取PDF文本
def extract_pdf_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# 存储所有上传的文件内容
pdf_store = {}
if uploaded_files:
    for f in uploaded_files:
        pdf_store[f.name] = extract_pdf_text(f)

# 文件选择器（切换文件）
if uploaded_files:
    st.subheader("📂 选择要分析的报告")
    file_names = [f.name for f in uploaded_files]
    selected = st.selectbox("选择文件", file_names)
    st.session_state.current_pdf_text = pdf_store[selected][:15000]
    st.markdown(f'<div class="success-box">✅ 当前分析：{selected}</div>', unsafe_allow_html=True)

# ====================== 【功能2：自动生成摘要】 ======================
if st.session_state.current_pdf_text:
    with st.spinner("🔍 正在生成报告摘要..."):
        summary_prompt = f"""
        请根据以下ESG报告内容，生成一份100-200字的核心摘要，包含：
        1. 环境（E）核心数据
        2. 社会（S）核心举措
        3. 治理（G）核心亮点
        报告内容：{st.session_state.current_pdf_text}
        """
        def call_ai(prompt):
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
            headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
            body = {
                "model": "qwen-turbo",
                "input": {"messages": [{"role": "user", "content": prompt}]},
                "parameters": {"result_format": "message", "temperature": 0.1}
            }
            res = requests.post(url, headers=headers, json=body)
            return res.json()["output"]["choices"][0]["message"]["content"]
        
        summary = call_ai(summary_prompt)
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.subheader("📋 报告核心摘要")
        st.write(summary)
        st.markdown('</div>', unsafe_allow_html=True)

        # ====================== 【功能3：自动生成高频问题】 ======================
        with st.spinner("📝 正在生成高频问题..."):
            q_prompt = f"""
            你是ESG分析师，根据报告生成8个最有价值的问题，只返回问题，换行分隔，不要序号。
            内容：{st.session_state.current_pdf_text}
            """
            try:
                q_text = call_ai(q_prompt)
                q_list = [x.strip() for x in q_text.split("\n") if x.strip() and len(x) > 4]
                st.session_state.auto_questions = q_list[:8]
            except:
                st.session_state.auto_questions = []

# ====================== 【功能4：自动生成的快捷问题】 ======================
st.markdown("---")
st.subheader("💬 系统自动生成的高频问题")
if st.session_state.auto_questions:
    cols = st.columns(3)
    for i, q in enumerate(st.session_state.auto_questions):
        with cols[i % 3]:
            if st.button(q, key=f"aq_{i}"):
                st.session_state["user_q"] = q
else:
    st.info("💡 上传PDF后自动生成高频问题")

# ====================== 【功能5：连续对话 + 历史保存】 ======================
st.markdown("---")
st.subheader("💬 连续智能问答")

# 显示历史对话
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(chat["user"])
    with st.chat_message("assistant"):
        st.write(chat["ai"])

# 输入框
user_q = st.chat_input("输入你的问题……")
if "user_q" in st.session_state and st.session_state.user_q:
    user_q = st.session_state.user_q
    st.session_state.user_q = ""

# 回答逻辑
if user_q and st.session_state.current_pdf_text:
    with st.chat_message("user"):
        st.write(user_q)
    
    with st.spinner("🤖 AI思考中..."):
        prompt = f"""
        你是专业ESG分析师，根据报告精准回答，简洁专业。
        历史对话：{st.session_state.chat_history}
        报告内容：{st.session_state.current_pdf_text}
        问题：{user_q}
        """
        ans = call_ai(prompt)
    
    with st.chat_message("assistant"):
        st.write(ans)
    
    # 保存历史
    st.session_state.chat_history.append({"user": user_q, "ai": ans})
    st.rerun()

# ====================== 导出Word ======================
if st.session_state.chat_history:
    if st.button("📥 导出全部对话为Word"):
        doc = Document()
        doc.add_heading("ESG智能解析对话记录", 0)
        for chat in st.session_state.chat_history:
            doc.add_paragraph(f"用户：{chat['user']}")
            doc.add_paragraph(f"AI：{chat['ai']}")
            doc.add_paragraph("---")
        bio = BytesIO()
        doc.save(bio)
        bio.seek(0)
        st.download_button("下载文件", data=bio, file_name="ESG对话记录.docx")

# 底部
st.markdown("---")
st.caption("💡 支持多文件上传、连续对话、自动生成高频问题、历史记录保存")
