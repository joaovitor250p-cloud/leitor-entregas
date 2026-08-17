import re
import time
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
NOME_DO_APP = "PACOTE É MATO"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"
st.set_page_config(page_title=NOME_DO_APP, page_icon=URL_DO_LOGO, layout="centered")

# --- ESTADO ---
if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()
if "ultima_leitura" not in st.session_state: st.session_state.ultima_leitura = ""

# --- MENU LATERAL (SEU ORIGINAL) ---
with st.sidebar:
    st.title(f"🚚 {NOME_DO_APP}")
    tema_cor = st.selectbox("🎨 Cor do Tema", ["Preto (Dark)", "RGB Gamer 🌈", "Branco (Light)"])
    arquivo_pdf_sidebar = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    if st.button("🔄 Zerar Rota"):
        st.session_state.pacotes_bipados = set()
        st.rerun()

# --- CSS E ESTILOS (SEU ORIGINAL) ---
st.markdown("""<style>
.stApp { background-color: #121212; color: white; }
.custom-card { background-color: #1E1E1E; padding: 16px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 15px; text-align: center; }
.stop-number-big { font-size: 3.8rem; font-weight: 900; color: #FF9500; line-height: 1; }
</style>""", unsafe_allow_html=True)

# --- SCRIPT DA CÂMERA (FIXO E VISÍVEL) ---
js_camera = """<script>
function garantirQuadrado() {
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(frame) {
        try {
            var doc = frame.contentDocument || frame.contentWindow.document;
            if (doc && !doc.querySelector('.quadrado-fixo')) {
                var s = doc.createElement('style');
                s.className = 'quadrado-fixo';
                s.innerHTML = '#reader__scan_region { border: 4px solid #FF9500 !important; border-radius: 10px; }';
                doc.head.appendChild(s);
            }
        } catch(e) {}
    });
}
setInterval(garantirQuadrado, 500);
</script>"""
components.html(js_camera, height=0)

# --- LÓGICA DE PROCESSAMENTO ---
arquivo_pdf = arquivo_pdf_sidebar
mapa_rotas = {}
stop_correspondente = {}
todos_pacotes = set()

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "\n".join([p.extract_text() or "" for p in leitor.pages])
    for linha in texto.split('\n'):
        cods = re.findall(r'BR[A-Za-z0-9]{10,16}', linha, re.IGNORECASE)
        for c in cods:
            todos_pacotes.add(c.upper())
            stop_correspondente[c.upper()] = 1 # Ajuste conforme sua regra

# --- LAYOUT PRINCIPAL (SEU ORIGINAL) ---
st.markdown("### ⚡ BIPAGEM ULTRA-RÁPIDA")

# AQUI ESTÁ O SCANNER NO MEIO DO LAYOUT
code = qrcode_scanner(key="scanner_bipagem")

# AQUI PROCESSAMOS O QUE FOI LIDO
if code and code != st.session_state.ultima_leitura:
    st.session_state.ultima_leitura = code
    cod = code.upper().strip()
    
    if cod in stop_correspondente:
        st.session_state.pacotes_bipados.add(cod)
        st.markdown(f'<div class="custom-card"><h3>📍 Parada P{stop_correspondente[cod]}</h3><p>Pacote: {cod}</p></div>', unsafe_allow_html=True)
    else:
        st.error(f"❌ {cod} não encontrado!")

# STATUS (PARA NÃO SUMIR)
st.write("---")
st.write(f"### Bipados: {len(st.session_state.pacotes_bipados)} / {len(todos_pacotes)}")
