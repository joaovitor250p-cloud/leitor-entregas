import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

# Inicialização da memória
if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()
if "arquivo_atual" not in st.session_state:
    st.session_state.arquivo_atual = None

# Estilo visual
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .stat-banner { background-color: #1E1E1E; border-radius: 12px; padding: 12px; border: 1px solid #333; display: flex; justify-content: space-around; margin-bottom: 10px; }
    .stat-value { font-size: 1.3rem; font-weight: bold; color: #28a745; }
    .stat-value-orange { font-size: 1.3rem; font-weight: bold; color: #FF9500; }
    .custom-card { background-color: #1E1E1E; padding: 18px; border-radius: 14px; border-left: 6px solid #28a745; margin: 10px 0; }
    .stop-number-big { font-size: 3.5rem; font-weight: 900; color: #FF9500; margin-bottom: 10px; }
    div[data-testid="stCustomComponentV1"] { width: 100%; height: 380px; display: flex; justify-content: center; align-items: center; border-radius: 16px; border: 3px solid #FF9500; background-color: #000000; margin-bottom: 10px; overflow: hidden; position: relative; }
    iframe { width: 100%; height: 380px; border: none; }
    </style>
""", unsafe_allow_html=True)

# Função para resetar progresso
def resetar_progresso():
    st.session_state.pacotes_bipados = set()

# MENU LATERAL
with st.sidebar:
    st.title("📦 PACOTE É MATO")
    uploaded_file = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    
    if uploaded_file:
        # Detecta se é um arquivo novo
        if uploaded_file.name != st.session_state.arquivo_atual:
            st.warning("Detectamos uma nova rota!")
            if st.button("🔄 Iniciar Nova Rota (Limpar Antiga)"):
                resetar_progresso()
                st.session_state.arquivo_atual = uploaded_file.name
                st.rerun()
            else:
                st.info("Ou continue de onde parou.")
        
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)
    if st.button("🔄 Zerar Bipados Manualmente"):
        resetar_progresso()
        st.rerun()

# LÓGICA DO PDF
mapa_rotas, stop_correspondente, nome_exibicao, todos_os_pacotes = {}, {}, {}, set()

if uploaded_file:
    leitor = PdfReader(uploaded_file)
    texto_completo = "".join([p.extract_text() + "\n" for p in leitor.pages])
    linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
    stop_atual = 1
    
    for linha in linhas:
        match_stop = re.search(r'^\s*(\d{1,3})\b', linha)
        if match_stop: stop_atual = int(match_stop.group(1))
        codigos = re.findall(r'BR[A-Za-z0-9]+', linha)
        if codigos:
            # Lógica simplificada de extração
            chave_end = "parada_" + str(stop_atual) 
            if chave_end not in mapa_rotas:
                mapa_rotas[chave_end] = []
                nome_exibicao[chave_end] = re.sub(r'BR[A-Za-z0-9]+', '', linha).strip()
            for c in codigos:
                todos_os_pacotes.add(c)
                if c not in mapa_rotas[chave_end]:
                    mapa_rotas[chave_end].append(c)
                    stop_correspondente[c] = stop_atual

# UI PRINCIPAL
if uploaded_file:
    qtd_bipados = len(st.session_state.pacotes_bipados)
    total = len(todos_os_pacotes)
    
    st.markdown(f"""
        <div class="stat-banner">
            <div class="stat-box"><div class="stat-label">BIPADOS / TOTAL</div><div class="stat-value">{qtd_bipados} / {total}</div></div>
            <div class="stat-box"><div class="stat-label">FALTAM</div><div class="stat-value-orange">{total - qtd_bipados} pcts</div></div>
        </div>
    """, unsafe_allow_html=True)
    
    codigo_camera = qrcode_scanner(key="scanner")
    codigo_manual = st.text_input("", placeholder="Ou digite o código BR aqui...", label_visibility="collapsed")
    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        cod = codigo_final.strip()
        achou = False
        for chave, lista in mapa_rotas.items():
            if cod in lista:
                st.session_state.pacotes_bipados.add(cod)
                st.markdown(f"""<div class="custom-card">
                    <div class="stop-number-big">P{stop_correspondente.get(cod, "?")}</div>
                    <div>📍 <b>Pacote:</b> {cod}</div>
                </div>""", unsafe_allow_html=True)
                achou = True; break
        if not achou: st.error("❌ Código não encontrado!")
else:
    st.info("👈 **Abra o menu lateral (seta no topo) para carregar o PDF.**")
