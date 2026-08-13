import re
import streamlit as st
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="Leitor de Rotas", page_icon="📦")

st.title("📦 Leitor de Entregas")
st.write("Envie o PDF da rota e busque o pacote rapidamente!")

arquivo_pdf = st.file_uploader("Arraste ou selecione o PDF do Circuit aqui:", type=["pdf"])

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto_completo = ""
    for pagina in leitor.pages:
        texto_completo += pagina.extract_text() + "\n"

    codigos = re.findall(r'BR[A-Za-z0-9]+', texto_completo)
    lista_entregas = {codigo.strip(): posicao for posicao, codigo in enumerate(codigos, start=1)}

    st.success(f"✅ Rota carregada! {len(lista_entregas)} pacotes encontrados.")

    st.markdown("---")

    # Opção da Câmera / QR Code
    st.subheader("📷 Leitor de Câmera")
    st.write("Toque no botão abaixo para ligar a câmera do celular:")
    codigo_camera = qrcode_scanner(key="scanner")

    # Opção Manual
    st.subheader("⌨️ Digitar / Bipar Manualmente")
    codigo_manual = st.text_input("Digite ou bipe o código do pacote abaixo:", placeholder="Ex: BR264290834579T")

    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        codigo_limpo = codigo_final.strip()
        if codigo_limpo in lista_entregas:
            numero = lista_entregas[codigo_limpo]
            st.success(f"### 🎯 PACOTE NÚMERO: {numero}")
        else:
            st.error("❌ Esse pacote NÃO está neste PDF!")