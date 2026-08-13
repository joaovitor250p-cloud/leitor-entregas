import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
NOME_DO_APP = "PACOTE É MATO"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"

st.set_page_config(page_title=NOME_DO_APP, page_icon=URL_DO_LOGO, layout="centered")

if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()

# ESTILO VISUAL
st.markdown("""
<style>
.stApp { background-color: #121212; color: #FFFFFF; }
.block-container { padding-top: 2.5rem !important; padding-bottom: 2rem !important; }
.welcome-card { background-color: #1E1E1E; padding: 24px; border-radius: 18px; border: 1px solid #333333; text-align: center; box-shadow: 0 8px 20px rgba(0,0,0,0.4); margin-top: 10px; margin-bottom: 20px; }
.welcome-logo { width: 90px; height: 90px; object-fit: contain; margin-bottom: 10px; }
.welcome-title { font-size: 1.5rem; font-weight: 800; color: #FF9500; }
.stat-banner { background-color: #1E1E1E; border-radius: 12px; padding: 12px; border: 1px solid #333; display: flex; justify-content: space-around; margin-bottom: 15px; }
.stat-value { font-size: 1.3rem; font-weight: bold; color: #28a745; }
.stat-value-orange { font-size: 1.3rem; font-weight: bold; color: #FF9500; }
.custom-card { background-color: #1E1E1E; padding: 18px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 15px; }
.stop-number-big { font-size: 3.5rem; font-weight: 900; color: #FF9500; line-height: 1; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# SCRIPT: MIRA LIMPA + FLASH + GRITO DA SHOPEE
js_scripts = """<script>
function gritarShopee() {
    var msg = new SpeechSynthesisUtterance('SHOPEEEEEEEEEEEEE!');
    msg.lang = 'pt-BR';
    msg.pitch = 1.5; // Bem agudo
    msg.rate = 1.8;  // Super rápido
    window.speechSynthesis.speak(msg);
}

function aplicarMelhorias() {
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(frame) {
        try {
            var doc = frame.contentDocument || frame.contentWindow.document;
            if (doc && doc.querySelector('video')) {
                var s = doc.createElement('style');
                s.innerHTML = '#qr-shaded-region { border: none !important; } #qr-shaded-region * { display: none !important; } video { object-fit: cover !important; }';
                doc.head.appendChild(s);
                if (!doc.getElementById('btn-flash')) {
                    var btn = doc.createElement('button');
                    btn.id = 'btn-flash'; btn.innerHTML = '🔦 Flash';
                    btn.style.cssText = 'position:absolute; top:10px; right:10px; z-index:999; background:rgba(0,0,0,0.7); color:#FFF; border:1px solid #FF9500; padding:5px 10px; border-radius:15px; font-weight:bold;';
                    btn.onclick = async () => {
                        var track = doc.querySelector('video').srcObject.getVideoTracks()[0];
                        var on = btn.innerHTML.includes('ON');
                        await track.applyConstraints({advanced: [{torch: !on}]});
                        btn.innerHTML = !on ? '⚡ Flash ON' : '🔦 Flash';
                    };
                    doc.body.appendChild(btn);
                }
            }
        } catch(e) {}
    });
}
setInterval(aplicarMelhorias, 300);
// Tenta gritar assim que a página carregar
window.onload = gritarShopee;
</script>"""
components.html(js_scripts, height=0)

# MENU LATERAL
with st.sidebar:
    st.title(f"🚚 {NOME_DO_APP}")
    arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
    
    if st.button("📢 Testar Grito da Shopee"):
        components.html("<script>gritarShopee();</script>", height=0)
        
    if st.button("🔄 Zerar Rota"):
        st.session_state.pacotes_bipados = set()
        st.rerun()

# ... (A lógica de extração continua igual) ...

mapa_rotas, stop_correspondente, todos_pacotes = {}, {}, set()
if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "".join([p.extract_text() + "\n" for p in leitor.pages])
    linhas = texto.split('\n')
    stop_atual = 0
    for linha in linhas:
        m_stop = re.search(r'^\s*(\d{1,3})\b', linha)
        if m_stop: stop_atual = int(m_stop.group(1))
        cods_candidatos = re.findall(r'BR[A-Za-z0-9]+', linha, re.IGNORECASE)
        cods = [c for c in cods_candidatos if 12 <= len(c) <= 16]
        for c in cods:
            c_u = c.upper()
            todos_pacotes.add(c_u)
            if c_u not in mapa_rotas: 
                mapa_rotas[c_u] = stop_atual

# TELA PRINCIPAL
if arquivo_pdf:
    bipados = len(st.session_state.pacotes_bipados)
    total = len(todos_pacotes)
    st.markdown(f'<div class="stat-banner"><div class="stat-value">{bipados} / {total} Bipados</div></div>', unsafe_allow_html=True)
    
    code = qrcode_scanner(key="s1") or st.text_input("Digitar:", placeholder="BR...")
    
    if code:
        cod = code.upper().strip()
        if cod in todos_pacotes:
            st.session_state.pacotes_bipados.add(cod)
            num_p = mapa_rotas.get(cod, "?")
            st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{num_p}</div><div>📍 Pacote: {cod}</div></div>', unsafe_allow_html=True)
        else:
            st.error("❌ Código não encontrado!")
else:
    st.markdown(f'<div class="welcome-card"><img src="{URL_DO_LOGO}" class="welcome-logo"><div class="welcome-title">{NOME_DO_APP}</div></div>', unsafe_allow_html=True)
    
