import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

NOME_DO_APP = "PACOTE É MATO"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"
IMG_MOTO = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f3cd_fe0f/512.gif"
CHAVE_PIX = "Pacoteemato@gmail.com"

st.set_page_config(page_title=NOME_DO_APP, page_icon=URL_DO_LOGO, layout="centered")

if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()

estilos_temas = {
    "Preto (Dark)": {"bg_app": "#000000", "text_app": "#FFFFFF", "card_bg": "#0B0B0B", "border": "#FFFFFF", "btn_bg": "#FFFFFF", "btn_text": "#000000", "subtext": "#AAAAAA", "shadow": "rgba(255,255,255,0.12)"},
    "Branco (Light)": {"bg_app": "#FFFFFF", "text_app": "#000000", "card_bg": "#F5F5F7", "border": "#000000", "btn_bg": "#000000", "btn_text": "#FFFFFF", "subtext": "#555555", "shadow": "rgba(0,0,0,0.15)"},
    "Cinza (Gray)": {"bg_app": "#1C1C1E", "text_app": "#F2F2F7", "card_bg": "#2C2C2E", "border": "#8E8E93", "btn_bg": "#48484A", "btn_text": "#FFFFFF", "subtext": "#AEAEB2", "shadow": "rgba(0,0,0,0.35)"}
}

with st.sidebar:
    st.markdown(f'<h2 style="margin-bottom:2px; font-weight:900;"><img src="{IMG_MOTO}" style="width:30px; height:30px; vertical-align:-5px; margin-right:6px;"> {NOME_DO_APP}</h2>', unsafe_allow_html=True)
    st.caption("Sistema Inteligente de Triagem e Logística")
    st.write("---")
    tema_cor = st.selectbox("🎨 Modo de Cor", ["Preto (Dark)", "Branco (Light)", "Cinza (Gray)"], index=0)
    usar_frontal = st.toggle("🤳 Câmera Frontal (Selfie)", value=False)
    manter_tela_ligada = st.toggle("💡 Manter Tela Sempre Ligada", value=True)
    usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
    tipo_voz = st.selectbox("🎙️ Estilo da Voz", ["Feminina / Normal", "Masculina / Grave", "Rápida / Ágil"])
    st.write("---")
    if st.button("🔄 Zerar Rota Atual"):
        st.session_state.pacotes_bipados = set()
        st.rerun()
t = estilos_temas[tema_cor]
css_style = f"""
<style>
.stApp {{ background-color: {t['bg_app']} !important; color: {t['text_app']} !important; }}
.hero-card {{ background-color: {t['card_bg']}; padding: 22px; border-radius: 20px; border: 2px solid {t['border']}; text-align: center; margin-bottom: 14px; }}
.upload-card {{ background-color: {t['card_bg']}; padding: 20px; border-radius: 18px; border: 2px dashed {t['border']}; text-align: center; margin-bottom: 14px; }}
.stat-banner {{ background-color: {t['card_bg']}; border-radius: 16px; padding: 15px; border: 2px solid {t['border']}; display: flex; justify-content: space-around; text-align: center; margin-bottom: 16px; }}
.stat-value {{ font-size: 1.5rem; font-weight: 900; color: {t['text_app']}; }}
.stat-label {{ font-size: 0.7rem; color: {t['subtext']}; text-transform: uppercase; }}
.custom-card {{ background-color: {t['card_bg']}; padding: 15px; border-radius: 14px; border: 2px solid {t['border']}; margin-bottom: 10px; text-align: center; }}
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

modo_cam_js = "user" if usar_frontal else "environment"
js_core = f"""
<script>
async function init() {{
    if ({manter_tela_ligada} && 'wakeLock' in navigator) {{ try {{ await navigator.wakeLock.request('screen'); }} catch (err) {{}} }}
}}
init();
function playBeep() {{ var ctx = new (window.AudioContext || window.webkitAudioContext)(); var osc = ctx.createOscillator(); osc.type = 'sine'; osc.frequency.setValueAtTime(880, ctx.currentTime); osc.connect(ctx.destination); osc.start(); osc.stop(ctx.currentTime + 0.1); }}
</script>
"""
components.html(js_core, height=0)
def extrair_codigo(texto):
    match = re.search(r'BR[A-Za-z0-9]{8,25}', texto, re.IGNORECASE)
    return match.group(0).upper().strip() if match else re.sub(r'[^A-Za-z0-9]', '', texto).upper().strip()

st.markdown(f'<div class="hero-card"><h2>{NOME_DO_APP}</h2></div>', unsafe_allow_html=True)
arquivo_pdf = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")
mapa_rotas, stop_corresp, todos_pacotes = {}, {}, set()

if arquivo_pdf:
    texto = "\n".join([p.extract_text() or "" for p in PdfReader(arquivo_pdf).pages])
    for idx, linha in enumerate(texto.split('\n')):
        cods = re.findall(r'BR[A-Za-z0-9]{10,20}', linha, re.IGNORECASE)
        if cods:
            for c in cods:
                todos_pacotes.add(c.upper())
                stop_corresp[c.upper()] = idx + 1
    
    stats_placeholder = st.empty()
    code = qrcode_scanner(key="scanner")
    bruto = code or st.text_input("Manual")
    
    if bruto:
        cod_limpo = extrair_codigo(bruto)
        if cod_limpo in todos_pacotes:
            st.session_state.pacotes_bipados.add(cod_limpo)
            components.html("<script>playBeep();</script>", height=0)
            st.markdown(f'<div class="custom-card"><h3>Parada: {stop_corresp.get(cod_limpo)}</h3><p>{cod_limpo}</p></div>', unsafe_allow_html=True)
        else:
            st.error("Código não encontrado!")

    bipados = len(st.session_state.pacotes_bipados)
    stats_placeholder.markdown(f'<div class="stat-banner"><div class="stat-item"><div class="stat-value">{bipados} / {len(todos_pacotes)}</div><div class="stat-label">PACOTES</div></div></div>', unsafe_allow_html=True)
    

