import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()

# Estilos (Mantendo seu visual preferido)
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .block-container { padding-top: 2rem !important; }
    .stat-banner { background-color: #1E1E1E; border-radius: 12px; padding: 12px; border: 1px solid #333; display: flex; justify-content: space-around; margin-bottom: 15px; }
    .stat-value { font-size: 1.3rem; font-weight: bold; color: #28a745; }
    .stat-value-orange { font-size: 1.3rem; font-weight: bold; color: #FF9500; }
    .custom-card { background-color: #1E1E1E; padding: 18px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 15px; }
    .stop-number-big { font-size: 3.5rem; font-weight: 900; color: #FF9500; line-height: 1; margin-bottom: 10px; }
    div[data-testid="stCustomComponentV1"] { width: 100%; height: 380px; display: flex; justify-content: center; align-items: center; border-radius: 16px; border: 3px solid #FF9500; background-color: #000000; margin-bottom: 10px; overflow: hidden; position: relative; }
    iframe { width: 100%; height: 380px; border: none; }
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
</script>""", height=0)

# MENU LATERAL
with st.sidebar:
    st.title("📦 PACOTE É MATO")
    arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    if st.button("🔄 Zerar Rota"):
        st.session_state.pacotes_bipados = set()
        st.rerun()

# LÓGICA DE EXTRAÇÃO (Agora agrupando POR ENDEREÇO, não por parada)
def extrair_endereco_limpo(texto):
    # Tenta pegar "Rua Nome, Numero"
    match = re.search(r'(rua|av|avenida|al|alameda|estrada|tv|travessa)\s+([a-záàâãéèêíïóôõöúçñ\s]+?)\s*,\s*(\d+)', texto, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2)} {match.group(3)}".lower().strip()
    return None

mapa_rotas, stop_correspondente, nome_exibicao, todos_pacotes = {}, {}, {}, set()
if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "".join([p.extract_text() + "\n" for p in leitor.pages])
    
    # Identifica blocos de paradas
    linhas = texto.split('\n')
    stop_atual = 0
    for linha in linhas:
        m_stop = re.search(r'^\s*(\d{1,3})\b', linha)
        if m_stop: stop_atual = int(m_stop.group(1))
        
        cods = re.findall(r'BR[A-Za-z0-9]+', linha, re.IGNORECASE)
        if cods:
            endereco = extrair_endereco_limpo(linha) or f"desconhecido_{stop_atual}"
            if endereco not in mapa_rotas: mapa_rotas[endereco] = []
            for c in cods:
                c_u = c.upper()
                todos_pacotes.add(c_u)
                if c_u not in mapa_rotas[endereco]:
                    mapa_rotas[endereco].append(c_u)
                    stop_correspondente[c_u] = stop_atual
                    nome_exibicao[endereco] = linha[:50] # Nome para exibição

# TELA PRINCIPAL
if arquivo_pdf:
    bipados = len(st.session_state.pacotes_bipados)
    total = len(todos_pacotes)
    st.markdown(f'<div class="stat-banner"><div class="stat-value">{bipados} / {total} Bipados</div><div class="stat-value-orange">{total-bipados} Faltam</div></div>', unsafe_allow_html=True)
    
    with st.expander("🤖 Ver Pacotes no mesmo endereço"):
        encontrou_duplo = False
        for end, pacotes in mapa_rotas.items():
            if len(pacotes) > 1:
                encontrou_duplo = True
                st.markdown(f"🚨 **{end.title()}**: `{len(pacotes)} pcts` (Parada P{stop_correspondente.get(pacotes[0])})")
        if not encontrou_duplo: st.info("Nenhum endereço com múltiplos pacotes.")

    code = qrcode_scanner(key="s1") or st.text_input("Digitar:", placeholder="BR...")
    
    if code:
        cod = code.upper().strip()
        achou = False
        for endereco, lista in mapa_rotas.items():
            if cod in lista:
                st.session_state.pacotes_bipados.add(cod)
                st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{stop_correspondente.get(cod)}</div><div>📍 Pacote: {cod}</div></div>', unsafe_allow_html=True)
                if len(lista) > 1: st.warning(f"⚠️ **MESMO ENDEREÇO!** Pegue também: " + ", ".join([p for p in lista if p != cod]))
                achou = True; break
        if not achou: st.error("❌ Código não encontrado!")
else:
    st.info("Envie o PDF na barra lateral.")
    
