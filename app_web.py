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

# Inicialização de Variáveis de Controle
if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()
if "bip_counter" not in st.session_state: st.session_state.bip_counter = 0
if "ultima_leitura" not in st.session_state: st.session_state.ultima_leitura = None
if "usar_audio" not in st.session_state: st.session_state.usar_audio = True

# MENU LATERAL
with st.sidebar:
    st.title(f"🚚 {NOME_DO_APP}")
    tema_cor = st.selectbox("🎨 Cor do Tema", ["Preto (Dark)", "RGB Gamer 🌈", "Branco (Light)", "Cinza", "Azul", "Vermelho"])
    arquivo_pdf_sidebar = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    st.session_state.usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
    if st.button("🔄 Zerar Rota Atual"):
        st.session_state.pacotes_bipados = set()
        st.session_state.ultima_leitura = None
        st.rerun()

# DEFINIÇÃO DAS PALETAS
estilos_temas = {
    "Preto (Dark)": {"bg_app": "#121212", "text_app": "#FFFFFF", "card_bg": "#1E1E1E", "border": "#333333", "accent": "#FF9500"},
    "RGB Gamer 🌈": {"bg_app": "#0D0D11", "text_app": "#FFFFFF", "card_bg": "#16161D", "border": "#222230", "accent": "#00FFCC"},
    "Branco (Light)": {"bg_app": "#F5F5F7", "text_app": "#1D1D1F", "card_bg": "#FFFFFF", "border": "#E5E5EA", "accent": "#007AFF"},
    "Cinza": {"bg_app": "#2C2C2E", "text_app": "#F2F2F7", "card_bg": "#3A3A3C", "border": "#48484A", "accent": "#FF9500"},
    "Azul": {"bg_app": "#0B192C", "text_app": "#E0F2FE", "card_bg": "#1E3E62", "border": "#0087D1", "accent": "#38BDF8"},
    "Vermelho": {"bg_app": "#1A0000", "text_app": "#FFE5E5", "card_bg": "#330000", "border": "#800000", "accent": "#FF4D4D"}
}
t = estilos_temas.get(tema_cor, estilos_temas["Preto (Dark)"])
cor_accent = t["accent"]

# CSS E ANIMAÇÕES
st.markdown(f"""<style>
.stApp {{ background-color: {t['bg_app']}; color: {t['text_app']}; }}
.custom-card {{ background-color: {t['card_bg']}; padding: 16px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 15px; text-align: center; }}
.stop-number-big {{ font-size: 3.8rem; font-weight: 900; color: {t['accent']}; line-height: 1; }}
</style>""", unsafe_allow_html=True)

# SCRIPT DE AJUSTE VISUAL DA CÂMERA (Mantendo os quadradinhos)
js_camera = f"""<script>
function ajustarScanner() {{
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(frame) {{
        try {{
            var doc = frame.contentDocument || frame.contentWindow.document;
            if (doc && !doc.querySelector('.custom-style')) {{
                var s = doc.createElement('style');
                s.className = 'custom-style';
                s.innerHTML = `
                    #qr-shaded-region {{ border: 10px solid rgba(0, 0, 0, 0.5) !important; }}
                    #reader__scan_region {{ border: 2px solid {cor_accent} !important; border-radius: 10px; }}
                `;
                doc.head.appendChild(s);
            }}
        }} catch(e) {{}}
    }});
}}
setInterval(ajustarScanner, 500);
</script>"""
components.html(js_camera, height=0)

# PROCESSAMENTO DO PDF
arquivo_pdf = arquivo_pdf_sidebar
mapa_rotas = {}
stop_correspondente = {}
todos_pacotes = set()

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "\n".join([p.extract_text() or "" for p in leitor.pages])
    linhas = texto.split('\n')
    seq_stop_auto = 0
    for idx, linha in enumerate(linhas):
        cods = re.findall(r'BR[A-Za-z0-9]{10,16}', linha, re.IGNORECASE)
        if cods:
            seq_stop_auto += 1
            m_num = re.match(r'^(\d{1,3})\b', linha)
            stop_num = int(m_num.group(1)) if m_num else seq_stop_auto
            for c in cods:
                todos_pacotes.add(c.upper())
                stop_correspondente[c.upper()] = stop_num

# TELA DE EXECUÇÃO
st.markdown("### ⚡ BIPAGEM ULTRA-RÁPIDA")

# LÓGICA DO SCANNER (Blindada para não travar)
if st.session_state.ultima_leitura is None:
    code = qrcode_scanner(key="scanner_principal")
    if code:
        st.session_state.ultima_leitura = code
        st.rerun()
else:
    # Mostra resultado e botão para limpar
    final_code = st.session_state.ultima_leitura
    
    # Processa o código
    cod = final_code.upper().strip()
    if cod in stop_correspondente:
        st.session_state.pacotes_bipados.add(cod)
        num_p = stop_correspondente[cod]
        st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{num_p}</div><div>📍 Pacote: {cod}</div></div>', unsafe_allow_html=True)
        
        # Feedback de voz
        if st.session_state.usar_audio:
            components.html(f"""<script>
                var msg = new SpeechSynthesisUtterance("{num_p}");
                msg.lang = "pt-BR";
                window.speechSynthesis.speak(msg);
            </script>""", height=0)
    else:
        st.error(f"❌ Código {cod} não encontrado na rota!")

    if st.button("📸 Bipar Próximo Pacote"):
        st.session_state.ultima_leitura = None
        st.rerun()

# RODAPÉ
st.write("---")
st.write(f"Bipados: {len(st.session_state.pacotes_bipados)} / {len(todos_pacotes)}")
