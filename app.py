import streamlit as st
import PyPDF2
from io import BytesIO
import os
import pymupdf  # Para o Redutor
from pdf2docx import Converter  # Para o Conversor PDF->Word
import tempfile  # Para o Conversor PDF->Word

# --- Funções do Combinador de PDF (de teste.py) ---

def get_file_size_mb(file):
    """Retorna o tamanho do arquivo em MB"""
    if file is not None:
        return len(file.getvalue()) / (1024 * 1024)
    return 0

def combine_pdfs(pdf_files):
    """Combina múltiplos arquivos PDF em um único arquivo"""
    pdf_merger = PyPDF2.PdfMerger()
    
    for pdf_file in pdf_files:
        pdf_file.seek(0)  # Reset do ponteiro do arquivo
        pdf_merger.append(pdf_file)
    
    # Criar arquivo combinado em memória
    output_buffer = BytesIO()
    pdf_merger.write(output_buffer)
    pdf_merger.close()
    
    output_buffer.seek(0)
    return output_buffer.getvalue()

# --- Funções do Redutor de PDF (adaptado de redutor_pdf.py) ---

def otimizar_pdf_streamlit(input_bytes: bytes, qualidade_img: int = 75, dpi_img: int = 150):
    """
    Otimiza um arquivo PDF (recebido como bytes) e retorna os bytes otimizados.
    """
    try:
        # Abre o documento a partir dos bytes em memória
        doc = pymupdf.open(stream=input_bytes, filetype="pdf")

        # Etapa 1: Remover "peso morto" e metadados desnecessários.
        doc.scrub()

        # Etapa 2: Otimizar imagens (downsampling e recompressão).
        doc.rewrite_images(dpi_target=dpi_img, quality=qualidade_img)

        # Etapa 3: Criar subconjuntos de fontes.
        doc.subset_fonts()

        # Etapa 4: Salvar o arquivo em um buffer de bytes com otimizações.
        output_buffer = BytesIO()
        doc.save(output_buffer, garbage=4, deflate=True, use_objstms=True)
        doc.close()

        return output_buffer.getvalue()

    except Exception as e:
        st.error(f"Ocorreu um erro durante a otimização do PDF: {e}")
        return None

# --- Definição das Páginas da Aplicação ---

def pagina_combinador():
    """Função que renderiza a página do Combinador de PDFs"""
    st.title("📄 Combinador de PDFs")
    st.markdown("---")
    
    # Limite máximo em MB
    MAX_SIZE_MB = 200
    
    # Upload de arquivos
    st.subheader("Upload de Arquivos PDF")
    uploaded_files = st.file_uploader(
        "Selecione os arquivos PDF para combinar:",
        type=['pdf'],
        accept_multiple_files=True,
        help="Selecione múltiplos arquivos PDF. Limite total: 200MB",
        key="uploader_combinador" # Chave única para o uploader
    )
    
    if uploaded_files:
        total_size_mb = sum(get_file_size_mb(file) for file in uploaded_files)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Arquivos Selecionados")
            for i, file in enumerate(uploaded_files):
                size_mb = get_file_size_mb(file)
                st.write(f"📄 **{file.name}** - {size_mb:.2f} MB")
        
        with col2:
            st.subheader("Controle de Tamanho")
            progress_percentage = min(total_size_mb / MAX_SIZE_MB, 1.0)
            st.progress(progress_percentage)
            st.metric(
                label="Tamanho Total",
                value=f"{total_size_mb:.2f} MB",
                delta=f"{total_size_mb - MAX_SIZE_MB:.2f} MB do limite"
            )
            
            if total_size_mb <= MAX_SIZE_MB:
                st.success(f"✅ Dentro do limite ({MAX_SIZE_MB} MB)")
            else:
                st.error(f"❌ Excede o limite em {total_size_mb - MAX_SIZE_MB:.2f} MB")
        
        st.markdown("---")
        
        if total_size_mb <= MAX_SIZE_MB:
            if st.button("🔗 Combinar PDFs", type="primary", use_container_width=True):
                try:
                    with st.spinner("Combinando arquivos PDF..."):
                        combined_pdf = combine_pdfs(uploaded_files)
                        output_filename = "arquivos_combinados.pdf"
                        
                        st.success("✅ PDFs combinados com sucesso!")
                        
                        st.download_button(
                            label="📥 Download PDF Combinado",
                            data=combined_pdf,
                            file_name=output_filename,
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        final_size_mb = len(combined_pdf) / (1024 * 1024)
                        st.info(f"📊 Arquivo final: {final_size_mb:.2f} MB")
                        
                except Exception as e:
                    st.error(f"❌ Erro ao combinar PDFs: {str(e)}")
        else:
            st.warning("⚠️ Remova alguns arquivos para ficar dentro do limite de 200MB")
    else:
        st.info("👆 Faça upload dos arquivos PDF para começar")

def pagina_redutor():
    """Função que renderiza a página do Redutor de PDFs"""
    st.title("🗜️ Redutor de PDFs")
    st.markdown("---")

    # Opções de otimização na barra lateral
    st.sidebar.subheader("Opções de Otimização")
    qualidade_img = st.sidebar.slider(
        "Qualidade da Imagem (JPEG)", 
        min_value=10, 
        max_value=100, 
        value=75, 
        help="Menor qualidade = menor tamanho de arquivo."
    )
    dpi_img = st.sidebar.slider(
        "DPI (Dots Per Inch) da Imagem", 
        min_value=50, 
        max_value=300, 
        value=150, 
        help="Menor DPI = menor resolução e menor tamanho. 72-150 é bom para tela."
    )
    
    st.subheader("Upload de Arquivo PDF")
    uploaded_file = st.file_uploader(
        "Selecione o arquivo PDF para reduzir:",
        type=['pdf'],
        accept_multiple_files=False,
        help="Selecione um único arquivo PDF para otimizar.",
        key="uploader_redutor" # Chave única para o uploader
    )
    
    if uploaded_file:
        input_bytes = uploaded_file.getvalue()
        tamanho_inicial_mb = len(input_bytes) / (1024 * 1024)

        col1, col2 = st.columns(2)
        col1.metric("Arquivo", uploaded_file.name)
        col2.metric("Tamanho Original", f"{tamanho_inicial_mb:.2f} MB")
        
        st.markdown("---")
        
        if st.button("🗜️ Reduzir PDF", type="primary", use_container_width=True):
            try:
                with st.spinner("Otimizando arquivo PDF... (Isso pode levar um momento)"):
                    optimized_pdf = otimizar_pdf_streamlit(input_bytes, qualidade_img, dpi_img)
                    
                    if optimized_pdf:
                        st.success("✅ PDF otimizado com sucesso!")
                        
                        tamanho_final_mb = len(optimized_pdf) / (1024 * 1024)
                        reducao_percentual = 1 - (tamanho_final_mb / tamanho_inicial_mb)
                        
                        nome_base, extensao = os.path.splitext(uploaded_file.name)
                        output_filename = f"{nome_base}_otimizado.pdf"
                        
                        st.download_button(
                            label="📥 Download PDF Reduzido",
                            data=optimized_pdf,
                            file_name=output_filename,
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        st.subheader("Resultados da Otimização")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Tamanho Original", f"{tamanho_inicial_mb:.2f} MB")
                        col2.metric("Tamanho Final", f"{tamanho_final_mb:.2f} MB")
                        col3.metric("Redução", f"{reducao_percentual:.1%}")

            except Exception as e:
                st.error(f"❌ Erro ao reduzir o PDF: {str(e)}")
    else:
        st.info("👆 Faça upload de um arquivo PDF para começar")

def pagina_conversor_word():
    """Função que renderiza a página do Conversor PDF -> Word (de app.py)"""
    st.title("🔃 Conversor de PDF para Word (.docx)")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Escolha um arquivo PDF", 
        type="pdf",
        key="uploader_pdf_to_word" # Chave única para o uploader
    )

    if uploaded_file is not None:
        # Salva o arquivo PDF temporariamente no disco (necessário para pdf2docx)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_file.read())
            temp_pdf_path = temp_pdf.name

        # Define o caminho do arquivo de saída
        output_docx_path = temp_pdf_path.replace(".pdf", ".docx")

        if st.button("Converter para Word", type="primary", use_container_width=True):
            with st.spinner("Convertendo... (Isso pode levar alguns minutos)"):
                try:
                    # Executa a conversão
                    converter = Converter(temp_pdf_path)
                    converter.convert(output_docx_path, start=0, end=None)
                    converter.close()

                    # Lê o arquivo Word convertido do disco
                    with open(output_docx_path, "rb") as f:
                        st.success("✅ Conversão concluída!")
                        st.download_button(
                            label="📥 Baixar Word",
                            data=f,
                            file_name=f"{os.path.splitext(uploaded_file.name)[0]}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                
                except Exception as e:
                    st.error(f"❌ Ocorreu um erro durante a conversão: {e}")
                
                finally:
                    # Limpa os arquivos temporários do disco
                    if os.path.exists(temp_pdf_path):
                        os.remove(temp_pdf_path)
                    if os.path.exists(output_docx_path):
                        os.remove(output_docx_path)
    else:
        st.info("👆 Faça upload de um arquivo PDF para começar a conversão")


# --- Aplicação Principal (Hub) ---

def main():
    # Configuração da página (deve ser a primeira chamada do Streamlit)
    st.set_page_config(
        page_title="Hub de Ferramentas PDF",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Navegação na barra lateral
    st.sidebar.title("🚀 Hub de Ferramentas")
    st.sidebar.markdown("---")
    
    app_selecionada = st.sidebar.radio(
        "Escolha a ferramenta:",
        ("📄 Combinador de PDFs", "🗜️ Redutor de PDFs", "🔃 PDF para Word")
    )
    st.sidebar.markdown("---")

    # Renderiza a página selecionada
    if app_selecionada == "📄 Combinador de PDFs":
        pagina_combinador()
    elif app_selecionada == "🗜️ Redutor de PDFs":
        pagina_redutor()
    elif app_selecionada == "🔃 PDF para Word":
        pagina_conversor_word()

if __name__ == "__main__":
    main()
