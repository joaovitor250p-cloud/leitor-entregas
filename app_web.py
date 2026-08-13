import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração do App
st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

# Inicializa estados de memória
if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()

# Estilo Visual Dark / App Pro
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .block-container { padding-top: 2rem !important; }
    .stat-banner { background-color: #1E1E1E; border-radius: 12px; padding: 12px; border: 1px solid #333; display: flex; justify-content: space-around; margin-bottom: 10px; }
    .stat-value { font-size: 1.2rem; font-weight: bold; color: #28a745; }
    .stat-value-orange { font-size: 1.2rem; font-weight: bold; color: #FF9500; }
    .custom-card { background-color: #1E1E1E; padding: 15px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 10px; }
    .stop-number-big { font-size: 3.5rem; font-weight: 900; color: #FF9500; line-height: 1; margin-bottom: 5px; }
    div[data-testid="stCustomComponentV1"] { width: 100%; height: 350px; display: flex; justify-content: center; align-items: center; border-radius: 16px; border: 3px solid #FF9500; background-color: #000000; overflow: hidden; position: relative; }
    iframe { width: 100%; height: 350px; border: none; }
    </style>
""", unsafe_allow_html=True)

# SCRIPT: MIRA LIMPA + BOTÃO FLASH
components.html("""<script>
    function aplicarMelhorias() {
        var iframes = window.parent.document.querySelectorAll('iframe');
        iframes.forEach(function(frame) {
            try {
                var doc = frame.contentDocument || frame.contentWindow.document;
                if (doc && doc.querySelector('video')) {
                    // Mira Limpa
                    var s = doc.createElement('style');
                    s.innerHTML = '#qr-shaded-region { border: none !important; } #qr-shaded-region * { display: none !important; }';
                    doc.head.appendChild(s);
                    // Botão Flash
                    if (!doc.getElementById('btn-flash')) {
                        var btn = doc.createElement('button');
                        btn.id = 'btn-flash'; btn.innerHTML = '🔦 Flash';
                        btn.style.cssText = 'position:absolute; top:10px; right:10px; z-index:999; background:rgba(0,0,0,0.7); color:#FFF; border:1px solid #FF9500; padding:5px 10px; border-radius:15px;';
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
</script>""", height=0)

# MENU LATERAL
with st.sidebar:
    st.title("📦 PACOTE É MATO")
    arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    if st.button("🔄 Zerar Rota"):
        st.session_state.pacotes_bipados = set()
        st.rerun()

# LÓGICA DE PROCESSAMENTO (ROBUSTA)
mapa_rotas, stop_correspondente, nome_exibicao, todos_os_pacotes = {}, {}, {}, set()

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "".join([p.extract_text() + "\n" for p in leitor.pages])
    
    # Busca inteligente (ignora maiúsculas/minúsculas)
    cods_all = re.findall(r'BR[A-Za-z0-9]+', texto, re.IGNORECASE)
    for c in cods_all: todos_os_pacotes.add(c.upper())
    
    # Organiza por parada
    blocos = re.split(r'(\d{1,3}\s*-)', texto)
    stop = 1
    for i in range(1, len(blocos), 2):
        stop = int(re.sub(r'\D', '', blocos[i]))
        bloco = blocos[i+1]
        cods_bloco = re.findall(r'BR[A-Za-z0-9]+', bloco, re.IGNORECASE)
        chave = f"parada_{stop}"
        if chave not in mapa_rotas: mapa_rotas[chave] = []
        for c in cods_bloco:
            c_u = c.upper()
            if c_u not in mapa_rotas[chave]:
                mapa_rotas[chave].append(c_u)
                stop_correspondente[c_u] = stop

# TELA PRINCIPAL
if arquivo_pdf:
    total = len(todos_os_pacotes)
    bipados = len(st.session_state.pacotes_bipados)
    
    # Painel
    st.markdown(f'<div class="stat-banner"><div class="stat-value">{bipados} / {total} Bipados</div><div class="stat-value-orange">{total-bipados} Faltam</div></div>', unsafe_allow_html=True)
    
    # Expander de Duplos
    with st.expander("🤖 Ver Pacotes Duplos/Triplos"):
        for chave, pacotes in mapa_rotas.items():
            if len(pacotes) > 1:
                st.markdown(f"🚨 **Parada {stop_correspondente.get(pacotes[0])}**: `{len(pacotes)} pcts`")
    
    # Scanner
    code = qrcode_scanner(key="s1") or st.text_input("Digitar:", placeholder="BR...")
    
    if code:
        cod = code.upper().strip()
        achou = False
        for chave, lista in mapa_rotas.items():
            if cod in lista:
                st.session_state.pacotes_bipados.add(cod)
                st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{stop_correspondente.get(cod)}</div><div>📍 Pacote: {cod}</div></div>', unsafe_allow_html=True)
                if len(lista) > 1:
                    st.warning(f"⚠️ PARADA COM {len(lista)} PACOTES! Pegue também: " + ", ".join([p for p in lista if p != cod]))
                achou = True; break
        if not achou: st.error("❌ Código não encontrado!")
else:
    st.info("Envie o PDF.")
