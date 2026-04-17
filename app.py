import streamlit as st
import fitz
import os
import requests
import json
from io import BytesIO
from docx import Document

# --------------------------
# 页面配置
# --------------------------
st.set_page_config(
    page_title="ESG智能解析系统",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# 美化 CSS
# --------------------------
st.markdown("""
<style>
.main-title {
    font-size: 2.8rem !important;
    font-weight: 700;
    color: #0e4b70;
    text-align: center;
    margin-bottom: 1rem;
}
.box {
    background: #f7f9fc;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
.question-btn {
    width: 100%;
    margin: 4px 0;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------
# 会话状态初始化
# --------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "auto_questions" not in st.session_state:
    st.session_state.auto_questions = []
if "trigger_q" not in st.session_state:
    st.session_state.trigger_q = None

API_KEY = os.getenv("API_KEY")

# --------------------------
# 侧边栏（全新有用内容）
# --------------------------
with st.sidebar:
    st.title("🌱 系统菜单")
    st.divider()

    st.subheader("📌 功能导航")
    st.markdown("""
    - 上传 PDF 开始分析
    - 自动生成高频问题
    - 连续对话问答
    - 历史记录永久保存
    - 一键导出对话记录
    """)

    st.divider()
    st.subheader("⚙️ 对话管理")
    if st.button("🗑️ 清空所有对话", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.pdf_text = ""
        st.session_state.auto_questions = []
        st.rerun()

    if st.session_state.chat_history:
        if st.button("📥 导出对话为Word", use_container_width=True):
            doc = Document()
            doc.add_heading("ESG智能解析对话记录", 0)
            for item in st.session_state.chat_history:
                doc.add_heading("用户问题", level=2)
                doc.add_paragraph(item["user"])
                doc.add_heading("AI 回答", level=2)
                doc.add_paragraph(item["ai"])
                doc.add_page_break()
            bio = BytesIO()
            doc.save(bio)
            bio.seek(0)
            st.download_button(
                "点击下载Word",
                data=bio,
                file_name="ESG对话记录.docx",
                use_container_width=True
            )

    st.divider()
    st.caption("✅ ESG智能解析系统 | 完整版")
    st.caption("🎓 大创项目专用")

# --------------------------
# 网页中央主界面（填满内容）
# --------------------------
st.markdown('<div class="main-title">🌱 ESG智能报告解析系统</div>', unsafe_allow_html=True)

# 中央区域：文件上传（你要的！）
st.markdown('<div class="box">', unsafe_allow_html=True)
st.subheader("📁 第一步：上传 ESG 报告 PDF")
uploaded_file = st.file_uploader("将文件拖入此处或点击选择", type="pdf")
if uploaded_file is not None:
    with st.spinner("正在解析PDF并生成高频问题..."):
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        st.session_state.pdf_text = text[:9000]

        # 自动生成高频问题
        prompt_q = f"""
        你是专业ESG分析师，根据报告生成8个最有价值的高频问题，只返回问题，不要多余内容。
        内容：{st.session_state.pdf_text}
        """
        resp = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            data=json.dumps({"model": "qwen-turbo", "messages": [{"role": "user", "content": prompt_q}]})
        )
        if resp.status_code == 200:
            qs = resp.json()["output"]["text"].strip().split("\n")
            st.session_state.auto_questions = [x.strip() for x in qs if x.strip()]
        else:
            st.session_state.auto_questions = ["生成失败，请重新上传PDF"]
        st.success("✅ 解析完成！高频问题已自动生成")
st.markdown('</div>', unsafe_allow_html=True)

# 中央区域：自动生成的高频问题
st.markdown('<div class="box">', unsafe_allow_html=True)
st.subheader("📋 第二步：系统自动生成高频问题（点击直接提问）")
if st.session_state.auto_questions:
    cols = st.columns(2)
    for i, q in enumerate(st.session_state.auto_questions):
        with cols[i % 2]:
            if st.button(q, key=i, use_container_width=True):
                st.session_state.trigger_q = q
st.markdown('</div>', unsafe_allow_html=True)

# 中央区域：智能对话
st.markdown('<div class="box">', unsafe_allow_html=True)
st.subheader("💬 第三步：连续智能问答")
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(chat["user"])
    with st.chat_message("assistant"):
        st.write(chat["ai"])

# 输入框
user_input = st.chat_input("输入你的问题……")
if st.session_state.trigger_q is not None:
    user_input = st.session_state.trigger_q
    st.session_state.trigger_q = None

if user_input:
    if not st.session_state.pdf_text:
        st.warning("⚠️ 请先上传PDF")
    else:
        with st.chat_message("user"):
            st.write(user_input)
        prompt = f"""
        你是专业ESG分析师，根据报告内容回答，专业、简洁、有条理。
        报告：{st.session_state.pdf_text}
        历史对话：{st.session_state.chat_history}
        用户问题：{user_input}
        """
        with st.spinner("AI思考中..."):
            res = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                data=json.dumps({"model": "qwen-turbo", "messages": [{"role": "user", "content": prompt}]})
            )
        ans = res.json()["output"]["text"] if res.status_code == 200 else "❌ 调用失败"
        with st.chat_message("assistant"):
            st.write(ans)
        st.session_state.chat_history.append({"user": user_input, "ai": ans})
st.markdown('</div>', unsafe_allow_html=True)
