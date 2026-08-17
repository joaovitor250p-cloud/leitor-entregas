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

# --- ESTADO DA SESSÃO ---
if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()
if "bip_counter" not in st.session_state: st.session_state.bip_counter = 0
if "ultima_leitura" not in st.session_state: st.session_state.ultima_leitura = None

# --- MENU LATERAL ---
with st.sidebar:
    st.title(f"🚚 {NOME_DO_APP}")
    tema_cor = st.selectbox("🎨 Cor do Tema", ["Preto (Dark)", "RGB Gamer 🌈", "Branco (Light)"])
    arquivo_pdf_sidebar = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
    
    if st.button("🔄 Zerar Rota Atual"):
        st.session_state.pacotes_bipados = set()
        st.session_state.ultima_leitura = None
        st.rerun()

# --- CORES E ESTILOS ---
estilos_temas = {
    "Preto (Dark)": {"bg": "#121212", "text": "#FFFFFF", "card": "#1E1E1E", "border": "#333333", "accent": "#FF9500"},
    "RGB Gamer 🌈": {"bg": "#0D0D11", "text": "#FFFFFF", "card": "#16161D", "border": "#222230", "accent": "#00FFCC"},
    "Branco (Light)": {"bg": "#F5F5F7", "text": "#1D1D1F", "card": "#FFFFFF", "border": "#E5E5EA", "accent": "#007AFF"}
}
t = estilos_temas.get(tema_cor, estilos_temas["Preto (Dark)"])

st.markdown(f"""
<style>
.stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
.camera-container {{ border: 3px solid {t['accent']}; border-radius: 20px; overflow: hidden; }}
.hero-card {{ background: {t['card']}; padding: 20px; border-radius: 20px; text-align: center; border: 1px solid {t['border']}; margin-bottom: 20px; }}
</style>
""", unsafe_allow_html=True)

# --- SCRIPT DA CÂMERA (COM OS QUADRADINHOS) ---
# Removi os comandos 'display: none' para permitir que a biblioteca mostre o guia visual
js_camera = f"""<script>
function ajustarScanner() {{
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(frame) {{
        try {{
            var doc = frame.contentDocument || frame.contentWindow.document;
            if (doc && doc.querySelector('video')) {{
                // Deixamos o box de escaneamento visível!
                var s = doc.createElement('style');
                s.innerHTML = `
                    #reader__scan_region {{ border: 2px solid {t['accent']} !important; }}
                    #reader__dashboard {{ background: rgba(0,0,0,0.5); padding: 10px; border-radius: 10px; }}
                `;
                doc.head.appendChild(s);
            }}
        }} catch(e) {{}}
    }});
}}
setInterval(ajustarScanner, 1000);
</script>"""
components.html(js_camera, height=0)

# --- LÓGICA DE PROCESSAMENTO PDF ---
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
                c_u = c.upper()
                todos_pacotes.add(c_u)
                stop_correspondente[c_u] = stop_num

# --- TELA PRINCIPAL E SCANNER ---
st.markdown("### ⚡ BIPAGEM ULTRA-RÁPIDA")

# Lógica BLINDADA: Só mostra o scanner se não tivermos leitura pendente
if st.session_state.ultima_leitura is None:
    code = qrcode_scanner(key="scanner_unico")
    if code:
        st.session_state.ultima_leitura = code
        st.rerun() # Vai processar o código lido
else:
    # Mostra o código lido e botão para limpar
    final_code = st.session_state.ultima_leitura
    st.success(f"✅ Código capturado: {final_code}")
    if st.button("📸 Bipar Próximo"):
        st.session_state.ultima_leitura = None
        st.rerun()
    
    # Processa o código
    cod = final_code.upper().strip()
    if cod in stop_correspondente:
        st.session_state.pacotes_bipados.add(cod)
        num_p = stop_correspondente[cod]
        st.markdown(f'<div class="hero-card"><h2>Parada: <span style="color:{t["accent"]}">P{num_p}</span></h2><p>Pacote: {cod}</p></div>', unsafe_allow_html=True)
        
        # Audio simples (SpeechSynthesis)
        js_audio = f"""<script>
        var msg = new SpeechSynthesisUtterance("{num_p}");
        msg.lang = "pt-BR";
        window.speechSynthesis.speak(msg);
        </script>"""
        components.html(js_audio, height=0)
    else:
        st.error("❌ Código não encontrado na rota!")

# --- STATUS BAR ---
st.write("---")
bipados = len(st.session_state.pacotes_bipados)
st.metric("Total de Pacotes Bipados", f"{bipados} / {len(todos_pacotes)}")
card">
        <img src="{URL_DO_LOGO}" class="welcome-logo">
        <div class="welcome-title">{NOME_DO_APP}</div>
        <div class="welcome-subtitle">SISTEMA INTELIGENTE DE LOGÍSTICA</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-card">
        <div class="upload-title">📄 CARREGAR ROTA DA ENTREGA</div>
        <div class="upload-sub">Envie o arquivo PDF da sua rota para liberar a câmera e a bipagem rápida</div>
    </div>
    """, unsafe_allow_html=True)
    
    arquivo_pdf_main = st.file_uploader("Selecione o PDF da Rota", type=["pdf"], key="pdf_main", label_visibility="collapsed")

arquivo_pdf = arquivo_pdf_sidebar or arquivo_pdf_main

mapa_rotas = {}
stop_correspondente = {}
nome_exibicao = {}
todos_pacotes = set()

# PROCESSAMENTO CIRCUIT
if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "\n".join([p.extract_text() or "" for p in leitor.pages])
    linhas = texto.split('\n')
    
    seq_stop_auto = 0
    
    for idx, linha in enumerate(linhas):
        linha_str = linha.strip()
        if not linha_str or "Address" in linha_str or "Notes" in linha_str or "Circuit" in linha_str:
            continue
            
        cods = re.findall(r'BR[A-Za-z0-9]{10,16}', linha_str, re.IGNORECASE)
        
        if cods:
            seq_stop_auto += 1
            
            m_num = re.match(r'^(\d{1,3})\b', linha_str)
            if m_num:
                stop_num = int(m_num.group(1))
            else:
                m_num_ant = re.match(r'^(\d{1,3})$', linhas[idx-1].strip()) if idx > 0 else None
                if m_num_ant:
                    stop_num = int(m_num_ant.group(1))
                else:
                    stop_num = seq_stop_auto
            
            end_key = normalizar_endereco(linha_str)
            if not end_key or len(end_key) < 3:
                end_key = f"pacote_isolado_{cods[0]}"
                
            if end_key not in mapa_rotas:
                mapa_rotas[end_key] = []
                
            for c in cods:
                c_u = c.upper()
                todos_pacotes.add(c_u)
                if c_u not in mapa_rotas[end_key]:
                    mapa_rotas[end_key].append(c_u)
                    stop_correspondente[c_u] = stop_num
                    nome_exibicao[end_key] = linha_str[:45]

# TELA DE EXECUÇÃO
if arquivo_pdf:
    bipados = len(st.session_state.pacotes_bipados)
    total = len(todos_pacotes)
    faltam = max(0, total - bipados)
    
    banner_html = f"""<div class="stat-banner">
    <div>
        <div class="stat-value-green">{bipados} / {total}</div>
        <div class="stat-label">BIPADOS ÚNICOS</div>
    </div>
    <div>
        <div class="stat-value-orange">{faltam}</div>
        <div class="stat-label">FALTAM</div>
    </div>
</div>"""
    st.markdown(banner_html, unsafe_allow_html=True)
    
    with st.expander("🤖 Ver pacotes no mesmo endereço / duplos"):
        encontrou_duplo = False
        for end, pacotes in mapa_rotas.items():
            if len(pacotes) > 1 and not end.startswith("pacote_isolado_"):
                encontrou_duplo = True
                st.markdown(f"🚨 **{nome_exibicao.get(end, end).title()}**: `{len(pacotes)} pcts` (Parada P{stop_correspondente.get(pacotes[0])})")
        if not encontrou_duplo:
            st.info("Nenhum endereço com múltiplos pacotes nesta rota.")

    st.markdown("""<div class="camera-header">
    <div class="camera-title">⚡ BIPAGEM ULTRA-RÁPIDA</div>
    <div class="camera-sub">Aponte para o QR Code em qualquer ângulo</div>
</div>""", unsafe_allow_html=True)

    code = qrcode_scanner(key="s1")
    
    st.markdown("#### ⌨️ Digitar código manualmente")
    input_code = st.text_input("", placeholder="BR123456789012", label_visibility="collapsed")
    
    final_code = code or input_code
    
    if final_code:
        cod = final_code.upper().strip()
        achou = False
        for endereco, lista in mapa_rotas.items():
            if cod in lista:
                st.session_state.pacotes_bipados.add(cod)
                st.session_state.bip_counter += 1
                num_p = stop_correspondente.get(cod, "?")
                
                st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{num_p}</div><div>📍 Pacote: {cod}</div></div>', unsafe_allow_html=True)
                
                if len(lista) > 1 and not endereco.startswith("pacote_isolado_"):
                    outros_stops = [f"P{stop_correspondente.get(p, '?')}" for p in lista if p != cod]
                    st.warning(f"⚠️ **MESMO ENDEREÇO!** Pegue também o(s) pacote(s) da(s): " + ", ".join(outros_stops))

                fala_texto = f"{num_p}"
                if len(lista) > 1 and not endereco.startswith("pacote_isolado_"):
                    fala_texto += " Atenção!"
                    
                pitch_val = "1.0"
                rate_val = "1.0"
                
                if "Pica-Pau" in tipo_voz:
                    fala_texto = f"He-he-he-he! {num_p}!"
                    if len(lista) > 1 and not endereco.startswith("pacote_isolado_"):
                        fala_texto += " Atenção!"
                    pitch_val = "1.8"
                    rate_val = "1.45"
                elif "Masculina" in tipo_voz:
                    pitch_val = "0.6"
                    rate_val = "0.95"
                elif "Rápida" in tipo_voz:
                    pitch_val = "1.1"
                    rate_val = "1.35"
                elif "Locutor" in tipo_voz:
                    pitch_val = "0.7"
                    rate_val = "0.9"
                elif "Vilão" in tipo_voz:
                    pitch_val = "0.3"
                    rate_val = "0.8"
                elif "Esquilo" in tipo_voz:
                    pitch_val = "2.0"
                    rate_val = "1.4"

                # Áudio e som sem erro de sintaxe
                js_exec = f"""
                <script>
                (function() {{
                    try {{
                        var ctx = new (window.AudioContext || window.webkitAudioContext)();
                        var osc = ctx.createOscillator();
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(880, ctx.currentTime);
                        osc.connect(ctx.destination);
                        osc.start();
                        osc.stop(ctx.currentTime + 0.08);
                    }} catch(e) {{}}

                    if ({str(usar_audio).lower()}) {{
                        try {{
                            window.speechSynthesis.cancel();
                            var msg = new SpeechSynthesisUtterance("{fala_texto}");
                            msg.lang = "pt-BR";
                            msg.pitch = {pitch_val};
                            msg.rate = {rate_val};
                            window.speechSynthesis.speak(msg);
                        }} catch(e) {{}}
                    }}
                }})();
                </script>
                """
                components.html(js_exec, height=0)

                achou = True
                break
        if not achou:
            st.error("❌ Código não encontrado!")
            
