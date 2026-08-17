import re
import streamlit as st
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="PACOTE É MATO", layout="centered")

# --- ESTADO ---
if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()
if "ultima_leitura" not in st.session_state: st.session_state.ultima_leitura = None

# --- PDF ---
arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
stop_correspondente = {}

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "\n".join([p.extract_text() or "" for p in leitor.pages])
    linhas = texto.split('\n')
    seq_stop_auto = 0
    for linha in linhas:
        cods = re.findall(r'BR[A-Za-z0-9]{10,16}', linha, re.IGNORECASE)
        if cods:
            seq_stop_auto += 1
            m_num = re.match(r'^(\d{1,3})\b', linha)
            stop_num = int(m_num.group(1)) if m_num else seq_stop_auto
            for c in cods:
                stop_correspondente[c.upper()] = stop_num

# --- SCANNER SIMPLIFICADO ---
st.markdown("### ⚡ BIPAGEM ULTRA-RÁPIDA")

# Mostra o scanner se não tiver leitura pendente
if st.session_state.ultima_leitura is None:
    code = qrcode_scanner(key="scanner_simples")
    if code:
        st.session_state.ultima_leitura = code
        st.rerun()
else:
    final_code = st.session_state.ultima_leitura
    st.success(f"✅ Código capturado: {final_code}")
    
    if st.button("📸 Bipar Próximo"):
        st.session_state.ultima_leitura = None
        st.rerun()
    
    # Processa
    cod = final_code.upper().strip()
    if cod in stop_correspondente:
        st.session_state.pacotes_bipados.add(cod)
        st.info(f"📍 PARADA: P{stop_correspondente[cod]}")
    else:
        st.error("❌ Código não encontrado!")
        
