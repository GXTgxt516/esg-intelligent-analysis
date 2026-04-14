import streamlit as st
import fitz
import requests
import os
from io import BytesIO
from docx import Document

# ====================== 在这里填入你的API KEY ======================
API_KEY = os.getenv("API_KEY")
# ==================================================================

# 页面配置
st.set_page_config(page_title="ESG智能解析系统", page_icon="🌱", layout="wide", initial_sidebar_state="expanded")

# 自定义CSS
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

# 侧边栏
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/leaf.png", width=80)
    st.title("ESG智能解析系统")
    st.markdown("---")
    st.subheader("📌 项目介绍")
    st.write("本系统基于大语言模型，实现ESG报告的智能解析、摘要生成与自然语言问答，助力企业ESG信息高效提取与分析。")
    st.markdown("---")
    st.caption("© 2025 大创项目组 | Vibe Coding 实现")

# 主标题
st.markdown('<h1 class="main-title">🌱 ESG报告智能解析与问答平台</h1>', unsafe_allow_html=True)

# PDF上传
st.subheader("📁 上传ESG报告PDF")
uploaded = st.file_uploader("", type="pdf", label_visibility="collapsed")

# 提取PDF
def extract_pdf_text(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# 调用AI函数
def call_ai(prompt):
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    body = {
        "model": "qwen-turbo",
        "input": {"messages": [{"role": "user", "content": prompt}]},
        "parameters": {"result_format": "message", "temperature": 0.1}
    }
    response = requests.post(url, headers=headers, json=body)
    return response.json()["output"]["choices"][0]["message"]["content"]

# 生成Word文档
def create_word_doc(content):
    doc = Document()
    doc.add_heading('ESG报告AI分析结果', 0)
    doc.add_paragraph(content)
    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# 解析PDF + 自动生成摘要
if uploaded:
    with st.spinner("🔍 正在解析PDF并生成摘要..."):
        full_text = extract_pdf_text(uploaded)
        st.session_state["pdf_text"] = full_text[:15000]
        st.markdown('<div class="success-box">✅ PDF解析完成！</div>', unsafe_allow_html=True)
        
        # 自动生成ESG报告摘要
        summary_prompt = f"""
        请根据以下ESG报告内容，生成一份100-200字的核心摘要，包含：
        1. 环境（E）核心数据
        2. 社会（S）核心举措
        3. 治理（G）核心亮点
        报告内容：{st.session_state['pdf_text']}
        """
        summary = call_ai(summary_prompt)
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.subheader("📋 报告核心摘要")
        st.write(summary)
        st.markdown('</div>', unsafe_allow_html=True)

# 常用问题快捷按钮
st.markdown("---")
st.subheader("💬 快速提问（点击直接查询）")
quick_questions = [
    "报告中废弃物回收率是多少？",
    "碳排放数据有哪些？",
    "公司环保措施有哪些？",
    "社会责任部分讲了什么？",
    "ESG治理结构是怎样的？"
]
cols = st.columns(3)
for i, q in enumerate(quick_questions):
    with cols[i%3]:
        if st.button(q, key=f"q_{i}"):
            st.session_state["quick_question"] = q

# 问答区域
st.markdown("---")
st.subheader("💬 自定义提问")
question = st.text_input("", 
                        value=st.session_state.get("quick_question", ""),
                        placeholder="例如：报告中废弃物回收率是多少？碳排放数据有哪些？", 
                        label_visibility="collapsed")

# AI回答 + 导出
if question and "pdf_text" in st.session_state:
    with st.spinner("🤖 AI正在分析报告内容..."):
        try:
            prompt = f"""
            你是专业的ESG报告分析师，回答要精准、简洁，只基于报告内容，不编造信息。
            报告内容：{st.session_state['pdf_text']}
            问题：{question}
            """
            answer = call_ai(prompt)
            
            st.markdown('<div class="answer-box">', unsafe_allow_html=True)
            st.markdown("### 📝 AI专业回答：")
            st.write(answer)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # 导出Word按钮
            if st.button("📥 导出回答为Word文档"):
                doc_content = f"问题：{question}\n\n回答：{answer}"
                word_file = create_word_doc(doc_content)
                st.download_button(
                    label="📄 下载Word",
                    data=word_file,
                    file_name=f"ESG问答结果_{question[:10]}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

        except Exception as e:
            st.error(f"❌ 出错了：{str(e)}")

# 底部提示
st.markdown("---")
st.caption("💡 提示：支持任意ESG相关问题，系统会自动从报告中提取精准答案，支持回答导出")
