import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

# Inicializa estados de memória
if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()
if "pacotes_faltando" not in st.session_state: st.session_state.pacotes_faltando = set()

# Estilo Visual Dark / App Pro
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .block-container { padding-top: 3rem !important; padding-bottom: 1rem !important; }
    .stat-banner { background-color: #1E1E1E; border-radius: 12px; padding: 12px; border: 1px solid #333; display: flex; justify-content: space-around; margin-bottom: 15px; }
    .stat-value { font-size: 1.3rem; font-weight: bold; color: #28a745; }
    .stat-value-orange { font-size: 1.3rem; font-weight: bold; color: #FF9500; }
    .custom-card { background-color: #1E1E1E; padding: 18px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 15px; }
    .success-card { background-color: #0d2a1b; padding: 25px; border-radius: 20px; border: 2px solid #28a745; text-align: center; }
    .stop-number-big { font-size: 3.5rem; font-weight: 900; color: #FF9500; }
    div[data-testid="stCustomComponentV1"] { width: 100%; height: 380px; display: flex; justify-content: center; align-items: center; border-radius: 16px; border: 3px solid #FF9500; background-color: #000000; margin-bottom: 10px; overflow: hidden; position: relative; }
    iframe { width: 100%; height: 380px; border: none; }
    </style>
""", unsafe_allow_html=True)

# Lógica dos botões na câmera
components.html("""<script>
    function aplicarMelhoriasCamera() {
        try {
            var iframes = window.parent.document.querySelectorAll('iframe');
            iframes.forEach(function(frame) {
                try {
                    var doc = frame.contentDocument || frame.contentWindow.document;
                    if (doc && doc.querySelector('video') && !doc.getElementById('btn-flash-custom')) {
                        var btn = doc.createElement('button');
                        btn.id = 'btn-flash-custom';
                        btn.innerHTML = '🔦 Flash';
                        btn.style.cssText = 'position: absolute; top: 12px; right: 12px; z-index: 999999; background: rgba(0, 0, 0, 0.75); color: #FFFFFF; border: 1px solid #FF9500; padding: 8px 14px; border-radius: 20px; font-weight: bold; cursor: pointer;';
                        var flashAtivo = false;
                        btn.onclick = async function() {
                            var video = doc.querySelector('video');
                            var track = video.srcObject.getVideoTracks()[0];
                            flashAtivo = !flashAtivo;
                            await track.applyConstraints({advanced: [{ torch: flashAtivo }]});
                            btn.innerHTML = flashAtivo ? '⚡ Flash ON' : '🔦 Flash';
                        };
                        doc.body.appendChild(btn);
                    }
                } catch(e) {}
            });
        } catch(e) {}
    }
    setInterval(aplicarMelhoriasCamera, 300);
</script>""", height=0)

# MENU LATERAL
with st.sidebar:
    st.title("📦 PACOTE É MATO")
    arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)
    if st.button("🔄 Zerar Tudo"):
        st.session_state.pacotes_bipados = set()
        st.session_state.pacotes_faltando = set()
        st.rerun()

# Processamento
mapa_rotas, stop_correspondente, nome_exibicao, todos_os_pacotes = {}, {}, {}, set()
if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "".join([p.extract_text() + "\n" for p in leitor.pages])
    linhas = [l.strip() for l in texto.split('\n') if l.strip()]
    stop_atual = 1
    for linha in linhas:
        m = re.search(r'^\s*(\d{1,3})\b', linha)
        if m: stop_atual = int(m.group(1))
        cods = re.findall(r'BR[A-Za-z0-9]+', linha)
        for c in cods:
            todos_os_pacotes.add(c)
            chave = "parada_" + str(stop_atual)
            if chave not in mapa_rotas: mapa_rotas[chave] = []
            if c not in mapa_rotas[chave]: mapa_rotas[chave].append(c); stop_correspondente[c] = stop_atual
            nome_exibicao[chave] = re.sub(r'BR[A-Za-z0-9]+', '', linha).strip()

# UI PRINCIPAL
if arquivo_pdf:
    qtd_bipados = len(st.session_state.pacotes_bipados)
    qtd_faltam_reportados = len(st.session_state.pacotes_faltando)
    total = len(todos_os_pacotes)
    
    # Progresso
    st.markdown(f"""<div class="stat-banner">
        <div class="stat-box"><div class="stat-label">BIPADOS / TOTAL</div><div class="stat-value">{qtd_bipados} / {total}</div></div>
        <div class="stat-box"><div class="stat-label">FALTAM</div><div class="stat-value-orange">{total - qtd_bipados - qtd_faltam_reportados}</div></div>
    </div>""", unsafe_allow_html=True)
    st.progress(qtd_bipados / total)

    # Scanner
    codigo_final = qrcode_scanner(key="scanner") or st.text_input("", placeholder="Digitar código BR...", label_visibility="collapsed")

    if codigo_final:
        cod = codigo_final.strip()
        achou = False
        for chave, lista in mapa_rotas.items():
            if cod in lista:
                st.session_state.pacotes_bipados.add(cod)
                if cod in st.session_state.pacotes_faltando: st.session_state.pacotes_faltando.remove(cod)
                
                st.markdown(f"""<div class="custom-card">
                    <div class="stop-number-big">P{stop_correspondente.get(cod, "?")}</div>
                    <div>📍 <b>Pacote:</b> {cod}</div>
                </div>""", unsafe_allow_html=True)
                
                if st.button("❌ Marcar como FALTANDO NA VAN"):
                    st.session_state.pacotes_faltando.add(cod)
                    st.session_state.pacotes_bipados.remove(cod)
                    st.rerun()
                achou = True; break
        if not achou: st.error("❌ Código não encontrado!")

    # TELA DE SUCESSO (FECHAMENTO)
    if qtd_bipados + qtd_faltam_reportados == total and total > 0:
        st.balloons()
        st.markdown("""<div class="success-card">
            <h1>🎉 ROTA CONCLUÍDA!</h1>
            <p>Você processou todos os pacotes.</p>
        </div>""", unsafe_allow_html=True)
        st.metric("Total Bipado", qtd_bipados)
        st.metric("Reportados como Faltando", qtd_faltam_reportados)

else:
    st.info("👈 Envie o PDF na barra lateral para começar.")
