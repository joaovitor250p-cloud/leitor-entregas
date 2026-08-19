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

# --- TELA LIGADA ---
js_wake = """<script>
async function keepAwake() { if ('wakeLock' in navigator) { try { await navigator.wakeLock.request('screen'); } catch (e) {} } }
document.addEventListener('visibilitychange', keepAwake);
keepAwake();
</script>"""
components.html(js_wake, height=0)

if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()

estilos = {
    "Preto": {"bg": "#000000", "txt": "#FFFFFF", "card": "#0B0B0B", "borda": "#FFFFFF", "btn": "#FFFFFF", "txt_btn": "#000000"}
}
t = estilos["Preto"]
css = f"""<style>
.stApp {{ background-color: {t['bg']} !important; color: {t['txt']} !important; }}
.hero-card {{ background-color: {t['card']}; padding: 20px; border-radius: 20px; border: 2px solid {t['borda']}; text-align: center; margin-bottom: 14px; }}
.custom-card {{ background-color: {t['card']}; padding: 16px; border-radius: 14px; border: 2px solid {t['borda']}; margin-bottom: 15px; text-align: center; }}
</style>"""
st.markdown(css, unsafe_allow_html=True)

# --- CÂMERA ANTI-TRAVA ---
modo = "environment"
js_cam = f"""<script>
async function forcarCamera() {{
    var iframes = window.parent.document.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {{
        try {{
            var doc = iframes[i].contentDocument || iframes[i].contentWindow.document;
            var video = doc.querySelector('video');
            if (video) {{
                var streamAtivo = video.srcObject && video.srcObject.getTracks()[0].readyState === 'live';
                if (!streamAtivo) {{
                    try {{ var stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: "{modo}" }}, audio: false }}); video.srcObject = stream; video.play(); }} catch(e) {{}}
                }}
            }}
        }} catch(e) {{}}
    }}
}}
document.addEventListener('visibilitychange', () => {{ if (document.visibilityState === 'visible') forcarCamera(); }});
setInterval(forcarCamera, 1000);
</script>"""
components.html(js_cam, height=0)
def extrair_cod(t):
    m = re.search(r'BR[A-Za-z0-9]{8,25}', t, re.IGNORECASE)
    return m.group(0).upper().strip() if m else re.sub(r'[^A-Za-z0-9]', '', t).upper().strip()

st.markdown(f'<div class="hero-card"><h2>{NOME_DO_APP}</h2></div>', unsafe_allow_html=True)
pdf = st.file_uploader("Upload Rota", type=["pdf"], key="p", label_visibility="collapsed")

mapa, stop, pacotes = {}, {}, set()
if pdf:
    texto = "\n".join([p.extract_text() or "" for p in PdfReader(pdf).pages])
    for idx, linha in enumerate(texto.split('\n')):
        cods = re.findall(r'BR[A-Za-z0-9]{10,20}', linha, re.IGNORECASE)
        for c in cods:
            c_up = c.upper()
            pacotes.add(c_up)
            stop[c_up] = idx + 1
    
    code = qrcode_scanner(key="scanner")
    bruto = code or st.text_input("Manual:")
    if bruto:
        cod = extrair_cod(bruto)
        if cod in pacotes:
            st.session_state.pacotes_bipados.add(cod)
            st.markdown(f'<div class="custom-card"><h3>Parada: P{stop.get(cod)}</h3><p>{cod}</p></div>', unsafe_allow_html=True)
        else: st.error("❌ Código não encontrado!")
    st.write(f"### 📦 {len(st.session_state.pacotes_bipados)} / {len(pacotes)} Pacotes")
    
