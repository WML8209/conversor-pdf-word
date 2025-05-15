import streamlit as st
from pdf2docx import Converter
import os
import tempfile

st.set_page_config(page_title="Conversor PDF → Word", layout="centered")

st.title("📄 Conversor de PDF para Word (.docx)")

uploaded_file = st.file_uploader("Escolha um arquivo PDF", type="pdf")

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(uploaded_file.read())
        temp_pdf_path = temp_pdf.name

    output_docx_path = temp_pdf_path.replace(".pdf", ".docx")

    if st.button("Converter para Word"):
        with st.spinner("Convertendo..."):
            converter = Converter(temp_pdf_path)
            converter.convert(output_docx_path, start=0, end=None)
            converter.close()

        with open(output_docx_path, "rb") as f:
            st.success("✅ Conversão concluída!")
            st.download_button(
                label="📥 Baixar Word",
                data=f,
                file_name="documento_convertido.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        os.remove(temp_pdf_path)
        os.remove(output_docx_path)
