import streamlit as st
from pptx import Presentation
from docx import Document
import tempfile
import os
from llama_cpp import Llama

# Initialize LLM
llm = Llama(model_path="models/llama-7b-q4.bin")

st.set_page_config(page_title="Proposal Slide Generator", layout="wide")
st.title("Proposal Slide Text Generator")

# Sidebar file uploads
st.sidebar.header("Upload Files")
pptx_files = st.sidebar.file_uploader(
    "Upload past PPTX slides", type=["pptx"], accept_multiple_files=True
)
brief_file = st.sidebar.file_uploader(
    "Upload project brief (DOCX or TXT)", type=["docx", "txt"]
)

def extract_text_from_pptx(pptx_streams):
    examples = []
    for f in pptx_streams:
        prs = Presentation(f)
        for slide in prs.slides:
            text = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
            full = "\n".join(text)
            if "Objective" in full or "Solution" in full:
                examples.append(full)
    return examples

def extract_text_from_brief(brief_stream, filename):
    if filename.lower().endswith(".docx"):
        doc = Document(brief_stream)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return brief_stream.read().decode("utf-8")

if st.sidebar.button("Generate Slide Text"):
    if not pptx_files or not brief_file:
        st.sidebar.error("Please upload both past PPTX files and a project brief.")
    else:
        with st.spinner("Extracting examples..."):
            examples = extract_text_from_pptx(pptx_files)
            brief_text = extract_text_from_brief(brief_file, brief_file.name)

        prompt = (
            "You are a proposal writer assistant. Based on the following examples "
            "of Objectives & Solutions slides, and the new project brief, draft an "
            "Objectives & Solutions paragraph in our brand tone.\n\n"
            "=== Examples ===\n" + "\n---\n".join(examples) + "\n\n"
            "=== New Brief ===\n" + brief_text + "\n\n"
            "=== Draft ===\n"
        )

        with st.spinner("Generating draft..."):
            response = llm(prompt=prompt, max_tokens=512, temperature=0.7)
            draft = response["choices"][0]["text"].strip()

        st.subheader("Draft Objectives & Solutions Text")
        draft_edited = st.text_area("Edit as needed:", draft, height=300)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Download as DOCX"):
                doc = Document()
                doc.add_paragraph(draft_edited)
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
                doc.save(tmp.name)
                st.download_button(
                    "Download DOCX",
                    data=open(tmp.name, "rb").read(),
                    file_name="Objectives_Solutions.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
        with col2:
            if st.button("Download as TXT"):
                tmp_txt = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
                with open(tmp_txt.name, "w", encoding="utf-8") as f:
                    f.write(draft_edited)
                st.download_button(
                    "Download TXT",
                    data=open(tmp_txt.name, "rb").read(),
                    file_name="Objectives_Solutions.txt",
                    mime="text/plain",
                )
