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
    manter_tela_ligada = st.toggle("💡 Manter Tela Ligada", value=True)
    usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
    tipo_voz = st.selectbox("🎙️ Estilo da Voz", ["Feminina / Normal", "Masculina / Grave", "Rápida / Ágil"])
    st.write("---")
    if st.button("🔄 Zerar Rota Atual"): st.session_state.pacotes_bipados = set(); st.rerun()

t = estilos_temas[tema_cor]
css_style = f"<style>.stApp {{ background-color: {t['bg_app']} !important; color: {t['text_app']} !important; }} .block-container {{ padding-top: 1.2rem !important; }} .hero-card {{ background-color: {t['card_bg']}; padding: 22px 18px; border-radius: 20px; border: 2px solid {t['border']}; text-align: center; box-shadow: 0 8px 24px {t['shadow']}; margin-bottom: 14px; }} .welcome-logo {{ width: 85px; height: 85px; margin-bottom: 8px; }} .welcome-title {{ font-size: 2rem; font-weight: 900; color: {t['text_app']}; }} .upload-card {{ background-color: {t['card_bg']}; padding: 20px; border-radius: 18px; border: 2px dashed {t['border']}; text-align: center; margin-bottom: 14px; }} .stButton > button {{ background-color: {t['btn_bg']} !important; color: {t['btn_text']} !important; border: 2px solid {t['border']} !important; border-radius: 12px !important; font-weight: 900 !important; }} .stat-banner {{ background-color: {t['card_bg']}; border-radius: 16px; padding: 16px 8px; border: 2px solid {t['border']}; display: flex; justify-content: space-around; text-align: center; margin-bottom: 16px; }} .stat-value {{ font-size: 1.6rem; font-weight: 900; color: {t['text_app']}; }} .stat-label {{ font-size: 0.78rem; color: {t['subtext']}; text-transform: uppercase; }} .custom-card {{ background-color: {t['card_bg']}; padding: 16px; border-radius: 14px; border: 2px solid {t['border']}; margin-bottom: 15px; text-align: center; }} .stop-number-big {{ font-size: 4.2rem; font-weight: 900; color: {t['text_app']}; }} .pix-card {{ background-color: {t['card_bg']}; border: 1px solid {t['border']}; border-radius: 14px; padding: 16px; text-align: center; }} .pix-key {{ font-size: 0.9rem; font-weight: 800; color: {t['text_app']}; background: rgba(127,127,127,0.18); padding: 6px; border-radius: 8px; }}</style>"
st.markdown(css_style, unsafe_allow_html=True)modo_cam_js = "user" if usar_frontal else "environment"
js_core = f"""<script>
let wakeLock = null; async function requestWakeLock() {{ if ({str(manter_tela_ligada).lower()} && 'wakeLock' in navigator) {{ try {{ wakeLock = await navigator.wakeLock.request('screen'); }} catch (err) {{}} }} }}
document.addEventListener('visibilitychange', async () => {{ if (wakeLock !== null && document.visibilityState === 'visible') {{ await requestWakeLock(); }} }}); requestWakeLock();
function playBeep() {{ try {{ var ctx = new (window.AudioContext || window.webkitAudioContext)(); var osc = ctx.createOscillator(); osc.type = 'sine'; osc.frequency.setValueAtTime(880, ctx.currentTime); osc.connect(ctx.destination); osc.start(); osc.stop(ctx.currentTime + 0.1); }} catch(e) {{}} }}
setInterval(function forcarCamera() {{ var iframes = window.parent.document.querySelectorAll('iframe'); for (var i = 0; i < iframes.length; i++) {{ try {{ var doc = iframes[i].contentDocument || iframes[i].contentWindow.document; if (doc && doc.querySelector('video')) {{ var video = doc.querySelector('video'); if (!video.dataset.modeApplied || video.dataset.modeApplied !== '{modo_cam_js}') {{ video.dataset.modeApplied = '{modo_cam_js}'; if (video.srcObject) {{ var tracks = video.srcObject.getTracks(); tracks.forEach(function(track) {{ track.stop(); }}); }} try {{ var stream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: {{ exact: '{modo_cam_js}' }} }}, audio: false }}); video.srcObject = stream; video.play(); }} catch(err) {{ var fallbackStream = await navigator.mediaDevices.getUserMedia({{ video: {{ facingMode: '{modo_cam_js}' }}, audio: false }}); video.srcObject = fallbackStream; video.play(); }} }} if ('{modo_cam_js}' === 'environment') {{ if (!doc.getElementById('btn-flash')) {{ var btn = doc.createElement('button'); btn.id = 'btn-flash'; btn.innerHTML = '🔦 Flash'; btn.style.cssText = 'position:absolute; top:10px; right:10px; z-index:9999; background:{t['btn_bg']}; color:{t['btn_text']}; border:2px solid {t['border']}; padding:6px 14px; border-radius:18px; font-weight:900;'; btn.onclick = async function() {{ try {{ var track = video.srcObject.getVideoTracks()[0]; var capabilities = track.getCapabilities ? track.getCapabilities() : {{}}; if (capabilities.torch) {{ await track.applyConstraints({{advanced: [{{torch: !btn.innerHTML.includes('ON')}}]}}); btn.innerHTML = !btn.innerHTML.includes('ON') ? '⚡ Flash ON' : '🔦 Flash'; }} }} catch(err) {{}} }}; doc.body.appendChild(btn); }} }} }} }} catch(e) {{}} }} }}, 500);
</script>"""
components.html(js_core, height=0)

def extrair_codigo_chave(texto):
    match = re.search(r'BR[A-Za-z0-9]{8,25}', texto, re.IGNORECASE)
    return match.group(0).upper().strip() if match else re.sub(r'[^A-Za-z0-9]', '', texto).upper().strip()

def normalizar_endereco(texto):
    m = re.search(r'(?:r(?:ua)?\.?|av(?:enida)?\.?|al(?:ameda)?\.?|est(?:rada)?\.?|tv|travessa)\s+([^,]+?)\s*,\s*(\d+)', texto, re.IGNORECASE)
    return f"{re.sub(r'[^a-zA-Z0-9]', '', m.group(1).lower())}_{m.group(2).strip()}" if m else re.sub(r'[^a-zA-Z0-9]', '', texto)[:35].lower()

st.markdown(f'<div class="hero-card"><img src="{URL_DO_LOGO}" class="welcome-logo"><div class="welcome-title">{NOME_DO_APP}</div><div class="welcome-subtitle">SISTEMA INTELIGENTE</div></div>', unsafe_allow_html=True)
arquivo_pdf = st.file_uploader("Upload Rota", type=["pdf"], key="pdf_main", label_visibility="collapsed")

if not arquivo_pdf:
    st.markdown(f'<div class="pix-card"><h3>🚀 O app te ajudou?</h3><p>Pix: {CHAVE_PIX}</p></div>', unsafe_allow_html=True)

mapa_rotas, stop_corresp, nome_exibicao, todos_pacotes = {}, {}, {}, set()

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "\n".join([p.extract_text() or "" for p in leitor.pages])
    linhas = texto.split('\n')
    termos = ["ADDRESS", "NOTES", "CIRCUIT", "OPTIMIZED", "STOP", "DELIVERY", "ROUTE", "TOTAL"]
    for idx, linha in enumerate(linhas):
        linha_str = linha.strip()
        cods = re.findall(r'BR[A-Za-z0-9]{10,20}', linha_str, re.IGNORECASE) or [c for c in re.findall(r'\b[A-Za-z0-9]{10,22}\b', linha_str) if not any(t in c.upper() for t in termos)]
        if cods:
            end_key = normalizar_endereco(linha_str) or f"pacote_{cods[0]}"
            if end_key not in mapa_rotas: mapa_rotas[end_key] = []; nome_exibicao[end_key] = linha_str[:45]
            for c in cods:
                c_up = c.upper()
                todos_pacotes.add(c_up)
                if c_up not in mapa_rotas[end_key]: mapa_rotas[end_key].append(c_up)
                stop_corresp[c_up] = int(re.match(r'^(\d{1,3})\b', linha_str).group(1)) if re.match(r'^(\d{1,3})\b', linha_str) else (int(re.match(r'^(\d{1,3})$', linhas[idx-1].strip()).group(1)) if idx > 0 and re.match(r'^(\d{1,3})$', linhas[idx-1].strip()) else 0)

    stats_placeholder = st.empty()
    with st.expander("🤖 Ver pacotes no mesmo endereço"):
        for end, pacs in mapa_rotas.items():
            if len(pacs) > 1: st.markdown(f"🚨 **{nome_exibicao.get(end, end).title()}**: `{len(pacs)} pcts`")

    st.markdown(f'<div class="camera-header"><div class="camera-title">📸 BIPAR PACOTE</div></div>', unsafe_allow_html=True)
    code = qrcode_scanner(key=f"scanner_{modo_cam_js}")
    input_code = st.text_input("Ou digite o código:", key="manual_input")
    bruto = code or input_code
    
    if bruto:
        cod_limpo = extrair_codigo_chave(bruto)
        pacote_identificado = next((c for c in todos_pacotes if cod_limpo in c or c in bruto.upper()), None)
        if pacote_identificado:
            st.session_state.pacotes_bipados.add(pacote_identificado)
            components.html("<script>playBeep();</script>", height=0)
            st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{stop_corresp.get(pacote_identificado, "?")}</div><div>📍 {pacote_identificado}</div></div>', unsafe_allow_html=True)
            if usar_audio:
                components.html(f"<script>window.speechSynthesis.speak(new SpeechSynthesisUtterance('{stop_corresp.get(pacote_identificado)}'));</script>", height=0)
        else: st.error("❌ Código não encontrado!")
    
    bipados = len(st.session_state.pacotes_bipados)
    stats_placeholder.markdown(f'<div class="stat-banner"><div class="stat-item"><div class="stat-value">{bipados} / {len(todos_pacotes)}</div><div class="stat-label">PACOTES</div></div></div>', unsafe_allow_html=True)
    
