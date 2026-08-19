import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
NOME_DO_APP = "PACOTE É MATO"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"
IMG_MOTO = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f3cd_fe0f/512.gif"
CHAVE_PIX = "Pacoteemato@gmail.com"

st.set_page_config(page_title=NOME_DO_APP, page_icon=URL_DO_LOGO, layout="centered")

# --- SISTEMA DE TELA LIGADA ---
js_wake_lock = """
<script>
let wakeLock = null;
async function requestWakeLock() {
    if ('wakeLock' in navigator) {
        try { wakeLock = await navigator.wakeLock.request('screen'); } catch (err) {}
    }
}
document.addEventListener('visibilitychange', async () => {
    if (document.visibilityState === 'visible') { await requestWakeLock(); }
});
requestWakeLock();
</script>
"""
components.html(js_wake_lock, height=0)

# Memória de Bipados
if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()

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
    usar_frontal = st.toggle("🤳 Câmera Frontal", value=False)
    usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
    tipo_voz = st.selectbox("🎙️ Estilo da Voz", ["Feminina / Normal", "Masculina / Grave", "Rápida / Ágil"])
    st.write("---")
    if st.button("🔄 Zerar Rota Atual"): st.session_state.pacotes_bipados = set(); st.rerun()

t = estilos_temas[tema_cor]
css_style = f"<style>.stApp {{ background-color: {t['bg_app']} !important; color: {t['text_app']} !important; }} .block-container {{ padding-top: 1.2rem !important; }} .hero-card {{ background-color: {t['card_bg']}; padding: 22px 18px; border-radius: 20px; border: 2px solid {t['border']}; text-align: center; box-shadow: 0 8px 24px {t['shadow']}; margin-bottom: 14px; }} .welcome-logo {{ width: 85px; height: 85px; margin-bottom: 8px; }} .welcome-title {{ font-size: 2rem; font-weight: 900; color: {t['text_app']}; }} .upload-card {{ background-color: {t['card_bg']}; padding: 20px; border-radius: 18px; border: 2px dashed {t['border']}; text-align: center; margin-bottom: 14px; }} .stButton > button {{ background-color: {t['btn_bg']} !important; color: {t['btn_text']} !important; border: 2px solid {t['border']} !important; border-radius: 12px !important; font-weight: 900 !important; }} .stat-banner {{ background-color: {t['card_bg']}; border-radius: 16px; padding: 16px 8px; border: 2px solid {t['border']}; display: flex; justify-content: space-around; text-align: center; margin-bottom: 16px; }} .stat-value {{ font-size: 1.6rem; font-weight: 900; color: {t['text_app']}; }} .stat-label {{ font-size: 0.78rem; color: {t['subtext']}; text-transform: uppercase; }} .custom-card {{ background-color: {t['card_bg']}; padding: 16px; border-radius: 14px; border: 2px solid {t['border']}; margin-bottom: 15px; text-align: center; }} .stop-number-big {{ font-size: 4.2rem; font-weight: 900; color: {t['text_app']}; }} .pix-card {{ background-color: {t['card_bg']}; border: 1px solid {t['border']}; border-radius: 14px; padding: 16px; text-align: center; }} .pix-key {{ font-size: 0.9rem; font-weight: 800; color: {t['text_app']}; background: rgba(127,127,127,0.18); padding: 6px; border-radius: 8px; }}</style>"
st.markdown(css_style, unsafe_allow_html=True)

# SCRIPT: CÂMERA INTELIGENTE
modo_cam_js = "user" if usar_frontal else "environment"
js_camera = f"""
<script>
function playBeep() {{ try {{ var ctx = new (window.AudioContext || window.webkitAudioContext)(); var osc = ctx.createOscillator(); osc.type = 'sine'; osc.frequency.setValueAtTime(880, ctx.currentTime); osc.connect(ctx.destination); osc.start(); osc.stop(ctx.currentTime + 0.1); }} catch(e) {{}} }}

async function forcarCamera() {{
    var iframes = window.parent.document.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {{
        try {{
            var doc = iframes[i].contentDocument || iframes[i].contentWindow.document;
            if (doc && doc.querySelector('video')) {{
                var video = doc.querySelector('video');
                var streamAtivo = video.srcObject && video.srcObject.getTracks()[0].readyState === 'live';
                if (!streamAtivo || video.dataset.modeApplied !== '{modo_cam_js}') {{
                    video.dataset.modeApplied = '{modo_cam_js}';
                    if (video.srcObject) {{ video.srcObject.getTracks().forEach(t => t.stop()); }}
                    try {{
                        var stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: {{ exact: '{modo_cam_js}' }} }}, audio: false }});
                        video.srcObject = stream; video.play();
                    }} catch(err) {{
                        var fallback = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: '{modo_cam_js}' }}, audio: false }});
                        video.srcObject = fallback; video.play();
                    }}
                }}
            }}
        }} catch(e) {{}}
    }}
}}
// Reconecta ao voltar para o app
document.addEventListener('visibilitychange', () => {{ if (document.visibilityState === 'visible') forcarCamera(); }});
setInterval(forcarCamera, 1000);
</script>
"""
components.html(js_camera, height=0)

def extrair_codigo_chave(texto):
    match = re.search(r'BR[A-Za-z0-9]{8,25}', texto, re.IGNORECASE)
    return match.group(0).upper().strip() if match else re.sub(r'[^A-Za-z0-9]', '', texto).upper().strip()

def normalizar_endereco(texto):
    m = re.search(r'(?:r(?:ua)?\.?|av(?:enida)?\.?|al(?:ameda)?\.?|est(?:rada)?\.?|tv|travessa)\s+([^,]+?)\s*,\s*(\d+)', texto, re.IGNORECASE)
    return f"{re.sub(r'[^a-zA-Z0-9]', '', m.group(1).lower())}_{m.group(2).strip()}" if m else re.sub(r'[^a-zA-Z0-9]', '', texto)[:35].lower()

# Interface Principal
st.markdown(f'<div class="hero-card"><img src="{URL_DO_LOGO}" class="welcome-logo"><div class="welcome-title">{NOME_DO_APP}</div></div>', unsafe_allow_html=True)
arquivo_pdf = st.file_uploader("Upload Rota", type=["pdf"], key="pdf_main", label_visibility="collapsed")

if not arquivo_pdf: st.markdown(f'<div class="pix-card"><h3>🚀 O app te ajudou?</h3><p>Pix: {CHAVE_PIX}</p></div>', unsafe_allow_html=True)

mapa_rotas, stop_corresp, nome_exibicao, todos_pacotes = {}, {}, {}, set()

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "\n".join([p.extract_text() or "" for p in leitor.pages])
    for idx, linha in enumerate(texto.split('\n')):
        linha_str = linha.strip()
        cods = re.findall(r'BR[A-Za-z0-9]{10,20}', linha_str, re.IGNORECASE)
        if cods:
            for c in cods:
                c_up = c.upper()
                todos_pacotes.add(c_up)
                stop_corresp[c_up] = int(re.match(r'^(\d{1,3})\b', linha_str).group(1)) if re.match(r'^(\d{1,3})\b', linha_str) else 0

    stats_placeholder = st.empty()
    code = qrcode_scanner(key="scanner")
    input_code = st.text_input("Ou digite o código:", key="manual_input")
    bruto = code or input_code
    
    if bruto:
        cod_limpo = extrair_codigo_chave(bruto)
        pacote_id = next((c for c in todos_pacotes if cod_limpo in c or c in bruto.upper()), None)
        if pacote_id:
            st.session_state.pacotes_bipados.add(pacote_id)
            components.html("<script>playBeep();</script>", height=0)
            st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{stop_corresp.get(pacote_id, "?")}</div><div>📍 {pacote_id}</div></div>', unsafe_allow_html=True)
            if usar_audio: components.html(f"<script>window.speechSynthesis.speak(new SpeechSynthesisUtterance('{stop_corresp.get(pacote_id)}'));</script>", height=0)
        else: st.error("❌ Código não encontrado!")
    
    stats_placeholder.markdown(f'<div class="stat-banner"><div class="stat-item"><div class="stat-value">{len(st.session_state.pacotes_bipados)} / {len(todos_pacotes)}</div><div class="stat-label">PACOTES</div></div></div>', unsafe_allow_html=True)
    
