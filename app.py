import streamlit as st
import io
import pdfplumber
import re

def extract_text_from_pdf(file_bytes):
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text

def generate_answer(rfi_text):
    # ... same rule-based answer logic as before ...
    # (copy from the previous answer)
    pass

st.set_page_config(page_title="RFI Answer Assistant", page_icon="📄")
st.title("📄 RFI Answer Assistant (Singapore Standards)")
st.markdown("Upload a **PDF** Request for Information and get a suggested answer based on **Singapore Standards and codes of practice**.")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Extracting text..."):
        file_bytes = uploaded_file.read()
        text = extract_text_from_pdf(file_bytes)
        if not text.strip():
            st.error("Could not extract text from PDF. It may be scanned or image-based.")
            st.stop()
        st.success("Text extracted.")
    with st.expander("Show extracted RFI text"):
        st.text(text)
    if st.button("Generate Answer"):
        answer = generate_answer(text)
        st.session_state.answer = answer
    if "answer" in st.session_state:
        st.subheader("Suggested Answer")
        st.code(st.session_state.answer, language="text")
        st.download_button("Download as TXT", st.session_state.answer, "RFI_Answer.txt")
