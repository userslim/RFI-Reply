import streamlit as st
import io
import PyPDF2
from docx import Document
from transformers import pipeline
import torch

# ------------------------------
# 1. Cached model loader (runs once)
# ------------------------------
@st.cache_resource
def load_model():
    # Use a small, instruction‑tuned model that fits within 1GB memory
    # Flan-T5-small is ~300MB and works well for short answer generation
    return pipeline(
        "text2text-generation",
        model="google/flan-t5-small",
        device=0 if torch.cuda.is_available() else -1  # use GPU if available
    )

# ------------------------------
# 2. Text extraction helpers
# ------------------------------
def extract_text_from_pdf(file_bytes):
    reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text(file_bytes, filename):
    if filename.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith('.docx'):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF or DOCX file.")

# ------------------------------
# 3. Answer generation using the model
# ------------------------------
def generate_answer(rfi_text, model):
    # Build a prompt that instructs the model to answer based on Singapore Standards
    prompt = f"""Answer the following Request for Information (RFI) as a consultant.
Use Singapore Standards and codes of practice (e.g., SS CP series) in your answer.
Be concise and cite specific standards if possible.

RFI: {rfi_text}

Answer:"""

    # Generate answer (max 200 tokens)
    result = model(prompt, max_length=200, do_sample=False)
    answer = result[0]['generated_text'].strip()
    return answer

# ------------------------------
# 4. Streamlit UI
# ------------------------------
st.set_page_config(page_title="RFI Answer Assistant", page_icon="📄")
st.title("📄 RFI Answer Assistant (Singapore Standards)")
st.markdown("Upload a **Request for Information** (PDF or DOCX) and get a suggested answer based on **Singapore Standards and codes of practice**.")

# File uploader
uploaded_file = st.file_uploader("Choose a file", type=["pdf", "docx"])

if uploaded_file is not None:
    with st.spinner("Extracting text from file..."):
        try:
            file_bytes = uploaded_file.read()
            text = extract_text(file_bytes, uploaded_file.name)
            if not text.strip():
                st.error("Could not extract any text from the file. It might be empty or scanned.")
                st.stop()
            st.success("Text extracted successfully.")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()

    # Show the extracted text (optional, for debugging)
    with st.expander("Show extracted RFI text"):
        st.text(text)

    # Load model (cached, so it loads only once)
    with st.spinner("Loading AI model (first time may take a moment)..."):
        model = load_model()

    # Generate answer on button click
    if st.button("Generate Answer"):
        with st.spinner("Generating answer..."):
            try:
                answer = generate_answer(text, model)
                st.session_state.answer = answer
            except Exception as e:
                st.error(f"Error generating answer: {e}")
                st.stop()

    # Display answer if available
    if "answer" in st.session_state:
        st.subheader("Suggested Answer")
        st.code(st.session_state.answer, language="text")

        # Copy button (uses Streamlit's native copy‑to‑clipboard via st.code)
        # But we can also add a custom download button
        st.download_button(
            label="📥 Download as TXT",
            data=st.session_state.answer,
            file_name="RFI_Answer.txt",
            mime="text/plain"
        )