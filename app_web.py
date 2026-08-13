import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

# Memória de Bipados
if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()

# CSS e Scripts
st.markdown("""
<style>
.stApp { background-color: #121212; color: #FFFFFF; }
.block-container { padding-top: 2rem !important; }
.custom-card { background-color: #1E1E1E; padding: 18px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 15px; }
.stop-number-big { font-size: 3rem; font-weight: 900; color: #FF9500; }
</style>
""", unsafe_allow_html=True)

# SCRIPT: FLASH + SOM DE BIP
components.html("""<script>
function playBeep() {
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.1);
}

// Flash Script
function aplicarMelhorias() {
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(frame) {
        try {
            var doc = frame.contentDocument || frame.contentWindow.document;
            if (doc && doc.querySelector('video') && !doc.getElementById('btn-flash')) {
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
        } catch(e) {}
    });
}
setInterval(aplicarMelhorias, 300);
</script>""", height=0)

# MENU LATERAL
with st.sidebar:
    st.title("📦 PACOTE É MATO")
    arquivo_pdf = st.file_uploader("📂 Enviar PDF", type=["pdf"])
    if st.button("🔄 Zerar Rota"):
        st.session_state.pacotes_bipados = set()
        st.rerun()

# LÓGICA
mapa_rotas, todos_pacotes = {}, set()
if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "".join([p.extract_text() + "\n" for p in leitor.pages])
    for linha in texto.split('\n'):
        cods = [c for c in re.findall(r'BR[A-Za-z0-9]+', linha, re.IGNORECASE) if 12 <= len(c) <= 16]
        for c in cods:
            c_u = c.upper()
            todos_pacotes.add(c_u)
            m_stop = re.search(r'^\s*(\d{1,3})\b', linha)
            stop = int(m_stop.group(1)) if m_stop else "?"
            mapa_rotas[c_u] = stop

# TELA PRINCIPAL
if arquivo_pdf:
    st.write(f"### {len(st.session_state.pacotes_bipados)} / {len(todos_pacotes)} Bipados")
    code = qrcode_scanner(key="s1") or st.text_input("Digitar:", placeholder="BR...")
    
    if code:
        cod = code.upper().strip()
        if cod in todos_pacotes:
            if cod not in st.session_state.pacotes_bipados:
                st.session_state.pacotes_bipados.add(cod)
                # TOCA O BIP
                components.html("<script>playBeep();</script>", height=0)
            
            st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{mapa_rotas[cod]}</div><div>📍 {cod}</div></div>', unsafe_allow_html=True)
        else:
            st.error("❌ Código não encontrado!")
else:
    st.info("Envie o PDF na barra lateral para começar.")
    
