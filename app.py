import streamlit as st
import io
import PyPDF2
from docx import Document
import requests
import json

# ------------------------------
# 1. Text extraction helpers
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
# 2. Generate answer using Hugging Face free inference API
# ------------------------------
def generate_answer_hf(rfi_text, api_token, model="google/flan-t5-small"):
    # Build prompt
    prompt = f"""Answer the following Request for Information (RFI) as a consultant.
Use Singapore Standards and codes of practice (e.g., SS CP series) in your answer.
Be concise and cite specific standards if possible.

RFI: {rfi_text}

Answer:"""

    API_URL = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {api_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": 200,
            "temperature": 0.3,
            "do_sample": False
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        result = response.json()
        # The response format depends on the model; for text2text-generation it's a list
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "").strip()
        elif isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"].strip()
        else:
            return "Unexpected response format from API."
    else:
        return f"API error {response.status_code}: {response.text}"

# ------------------------------
# 3. Streamlit UI
# ------------------------------
st.set_page_config(page_title="RFI Answer Assistant", page_icon="📄")
st.title("📄 RFI Answer Assistant (Singapore Standards)")
st.markdown("Upload a **Request for Information** (PDF or DOCX) and get a suggested answer based on **Singapore Standards and codes of practice**.")

# --- API token input ---
# Option 1: Use Streamlit secrets (recommended for production)
# Option 2: Let the user enter their own token (for demo)
api_token = None
if "HF_TOKEN" in st.secrets:
    api_token = st.secrets["HF_TOKEN"]
else:
    api_token = st.text_input(
        "Hugging Face API Token (get a free one at huggingface.co/settings/tokens)",
        type="password",
        help="Your token is not stored. It's used only to call the free inference API."
    )
    if not api_token:
        st.warning("Please enter your Hugging Face API token to generate answers.")
        st.stop()

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

    # Show extracted text (optional)
    with st.expander("Show extracted RFI text"):
        st.text(text)

    # Model selection (you can add more models)
    model_name = st.selectbox(
        "Choose a model",
        ["google/flan-t5-small", "google/flan-t5-base", "t5-small"],
        index=0
    )

    if st.button("Generate Answer"):
        with st.spinner("Generating answer via Hugging Face API..."):
            answer = generate_answer_hf(text, api_token, model_name)
            if answer.startswith("API error"):
                st.error(answer)
            else:
                st.session_state.answer = answer

    # Display answer
    if "answer" in st.session_state:
        st.subheader("Suggested Answer")
        st.code(st.session_state.answer, language="text")

        st.download_button(
            label="📥 Download as TXT",
            data=st.session_state.answer,
            file_name="RFI_Answer.txt",
            mime="text/plain"
        )
