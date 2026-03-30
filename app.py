import streamlit as st
import io
import re
import sys
import subprocess

# ------------------------------
# Ensure pypdf is installed (safety net)
# ------------------------------
try:
    from pypdf import PdfReader
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
    from pypdf import PdfReader

# ------------------------------
# Text extraction from PDF
# ------------------------------
def extract_text_from_pdf(file_bytes):
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

# ------------------------------
# Rule‑based answer generator referencing Singapore Standards
# ------------------------------
def generate_answer(rfi_text):
    # Keywords to detect technical areas
    keywords = []
    patterns = [
        r'\b(?:fire\s+safety|fire\s+protection)\b',
        r'\b(structural|structure|beam|column|slab|foundation)\b',
        r'\b(ventilation|HVAC|air\s+conditioning)\b',
        r'\b(electrical|lighting|power\s+supply)\b',
        r'\b(plumbing|sanitary|drainage)\b',
        r'\b(waterproofing|dampness|leakage)\b',
        r'\b(acoustic|noise|sound\s+insulation)\b',
        r'\b(accessibility|barrier\s+free|ramp)\b',
        r'\b(material|concrete|steel|timber)\b',
    ]
    for pat in patterns:
        if re.search(pat, rfi_text, re.IGNORECASE):
            keywords.append(re.search(pat, rfi_text, re.IGNORECASE).group())

    keywords = list(set(keywords))
    answer = "Based on Singapore Standards and codes of practice:\n\n"

    if not keywords:
        answer += ("The RFI does not contain obvious technical keywords. "
                   "Please refer to the relevant Singapore Standard applicable to your discipline "
                   "(e.g., SS CP series, SS EN). For general guidance, consult the Building Control Act and regulations.")
    else:
        answer += f"The following points are relevant to the terms found: {', '.join(keywords)}.\n\n"
        answer += "- All works shall comply with the Singapore Standards (SS) and CP (Code of Practice) series, as applicable.\n"
        answer += "- For specific requirements, refer to:\n"

        # Add specific standards based on keywords
        if any(k in ['fire safety', 'fire protection'] for k in keywords):
            answer += "  * Fire Safety: SS 578 (Code of Practice for Fire Safety) and Fire Code (SCDF).\n"
        if any(k in ['structural', 'structure', 'beam', 'column', 'slab'] for k in keywords):
            answer += "  * Structural: SS EN 1992 (Eurocode 2 for concrete) and SS EN 1993 (for steel).\n"
        if any(k in ['ventilation', 'HVAC', 'air conditioning'] for k in keywords):
            answer += "  * Ventilation: SS 553 (Code of Practice for Air‑conditioning and Mechanical Ventilation).\n"
        if any(k in ['electrical', 'lighting', 'power supply'] for k in keywords):
            answer += "  * Electrical: SS 638 (Code of Practice for Electrical Installations).\n"
        if any(k in ['plumbing', 'sanitary', 'drainage'] for k in keywords):
            answer += "  * Plumbing: SS 636 (Code of Practice for Water Services).\n"
        if any(k in ['waterproofing', 'dampness', 'leakage'] for k in keywords):
            answer += "  * Waterproofing: SS 615 (Code of Practice for Waterproofing).\n"
        if any(k in ['acoustic', 'noise', 'sound insulation'] for k in keywords):
            answer += "  * Acoustic: SS 553 (Acoustic requirements) and relevant SS EN standards.\n"
        if any(k in ['accessibility', 'barrier free', 'ramp'] for k in keywords):
            answer += "  * Accessibility: SS 580 (Code of Practice for Accessibility).\n"
        if any(k in ['material', 'concrete', 'steel', 'timber'] for k in keywords):
            answer += "  * Materials: SS EN 206 (Concrete), SS EN 10025 (Steel), etc.\n"

        answer += "\nAny deviation must be submitted to the relevant authority for approval with supporting documentation."

    return answer

# ------------------------------
# Streamlit UI
# ------------------------------
st.set_page_config(page_title="RFI Answer Assistant", page_icon="📄")
st.title("📄 RFI Answer Assistant (Singapore Standards)")
st.markdown("Upload a **Request for Information** (PDF only) and get a suggested answer based on **Singapore Standards and codes of practice**.")

uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Extracting text from file..."):
        try:
            file_bytes = uploaded_file.read()
            text = extract_text_from_pdf(file_bytes)
            if not text.strip():
                st.error("Could not extract any text from the file. It might be empty or scanned.")
                st.stop()
            st.success("Text extracted successfully.")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

    with st.expander("Show extracted RFI text"):
        st.text(text)

    if st.button("Generate Answer"):
        answer = generate_answer(text)
        st.session_state.answer = answer

    if "answer" in st.session_state:
        st.subheader("Suggested Answer")
        st.code(st.session_state.answer, language="text")
        st.download_button(
            label="📥 Download as TXT",
            data=st.session_state.answer,
            file_name="RFI_Answer.txt",
            mime="text/plain"
        )
