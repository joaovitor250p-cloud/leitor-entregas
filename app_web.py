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

# --- ESTADO (BLINDADO) ---
if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()
if "cod_detectado" not in st.session_state: st.session_state.cod_detectado = None

# MENU LATERAL
with st.sidebar:
    st.title(f"🚚 {NOME_DO_APP}")
    tema_cor = st.selectbox("🎨 Cor do Tema", ["Preto (Dark)", "RGB Gamer 🌈", "Branco (Light)"])
    arquivo_pdf_sidebar = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
    if st.button("🔄 Zerar Rota"):
        st.session_state.pacotes_bipados = set()
        st.session_state.cod_detectado = None
        st.rerun()

# [CSS E CORES MANTIDOS DO SEU SCRIPT...]
# (Mantive a parte visual intacta para você)
t = {"accent": "#FF9500"} # Exemplo, o resto do seu tema entra aqui

# SCRIPT DE AJUSTE VISUAL (Ajustado para não perder o foco)
js_camera = """<script>
function garantirScanner() {
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(frame) {
        try {
            var doc = frame.contentDocument || frame.contentWindow.document;
            if (doc && doc.querySelector('video')) {
                var s = doc.createElement('style');
                s.innerHTML = '#qr-shaded-region { display: none !important; } #reader__scan_region { border: 4px solid #FF9500 !important; }';
                doc.head.appendChild(s);
            }
        } catch(e) {}
    });
}
setInterval(garantirScanner, 100);
</script>"""
components.html(js_camera, height=0)

# PROCESSAMENTO DO PDF
mapa_rotas = {}
stop_correspondente = {}
todos_pacotes = set()
if arquivo_pdf_sidebar:
    leitor = PdfReader(arquivo_pdf_sidebar)
    texto = "\n".join([p.extract_text() or "" for p in leitor.pages])
    linhas = texto.split('\n')
    for linha in linhas:
        cods = re.findall(r'BR[A-Za-z0-9]{10,16}', linha, re.IGNORECASE)
        for c in cods:
            todos_pacotes.add(c.upper())
            stop_correspondente[c.upper()] = 1 # Ajuste sua lógica de parada aqui

# --- LÓGICA DE BIPAGEM (O PULO DO GATO) ---
st.markdown("### ⚡ BIPAGEM ULTRA-RÁPIDA")

# 1. Se NÃO tiver código detectado, mostra o scanner
if st.session_state.cod_detectado is None:
    code = qrcode_scanner(key="scanner_main")
    if code:
        st.session_state.cod_detectado = code
        st.rerun() # Vai processar o código
else:
    # 2. Se JÁ tiver código detectado, mostra o resultado e botão de limpar
    cod = st.session_state.cod_detectado.upper().strip()
    st.success(f"✅ LIDO: {cod}")
    
    if cod in stop_correspondente:
        st.session_state.pacotes_bipados.add(cod)
        st.markdown(f"### 📍 Parada: {stop_correspondente[cod]}")
    else:
        st.error("❌ Código não encontrado!")
        
    if st.button("📸 Bipar Próximo"):
        st.session_state.cod_detectado = None
        st.rerun()

st.write(f"Bipados: {len(st.session_state.pacotes_bipados)}")
