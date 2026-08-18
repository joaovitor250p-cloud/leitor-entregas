import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
NOME_DO_APP = "PACOTE É MATO"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"

# Emojis Animados Oficiais (Google Noto Animated)
IMG_TRUCK = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f69a/512.gif"
IMG_SOUND = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f50a/512.gif"
IMG_MIC = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f399_fe0f/512.gif"
IMG_DOC = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f4c4/512.gif"
IMG_DOWN = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f447/512.gif"
IMG_CAMERA = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f4f8/512.gif"
IMG_KEYBOARD = "https://fonts.gstatic.com/s/e/notoemoji/latest/2328_fe0f/512.gif"
IMG_PIN = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f4cd/512.gif"
IMG_SIREN = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f6a8/512.gif"
IMG_FLASH = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f526/512.gif"
IMG_BOLT = "https://fonts.gstatic.com/s/e/notoemoji/latest/26a1/512.gif"

st.set_page_config(
    page_title=NOME_DO_APP,
    page_icon=URL_DO_LOGO,
    layout="centered"
)

# Memória de Bipados
if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()

# MENU LATERAL
with st.sidebar:
    st.markdown(
        '<h3 style="color:#FFF;"><img src="' + IMG_TRUCK + '" class="emoji-img-md"> ' + NOME_DO_APP + '</h3>',
        unsafe_allow_html=True
    )
    st.caption("Sistema Inteligente de Logística")
    st.write("---")
    
    st.markdown(
        '<div class="sidebar-label"><img src="' + IMG_SOUND + '" class="emoji-img"> Falar Número da Parada</div>',
        unsafe_allow_html=True
    )
    usar_audio = st.toggle("Falar Número da Parada", value=True, label_visibility="collapsed")
    
    tipo_voz = "Feminina / Normal"
    if usar_audio:
        st.markdown(
            '<div class="sidebar-label"><img src="' + IMG_MIC + '" class="emoji-img"> Estilo da Voz</div>',
            unsafe_allow_html=True
        )
        tipo_voz = st.selectbox(
            "Estilo da Voz", 
            [
                "Feminina / Normal", 
                "Masculina / Grave", 
                "Rápida / Ágil"
            ],
            label_visibility="collapsed"
        )
        
    st.write("---")
    if st.button("🔄 Zerar Rota Atual"):
        st.session_state.pacotes_bipados = set()
        st.rerun()

# ESTILO VISUAL PRETO E BRANCO COM EMOJIS ANIMADOS
css_style = """
<style>
.stApp { 
    background-color: #000000 !important; 
    color: #FFFFFF !important; 
}

.block-container { 
    padding-top: 1.2rem !important; 
    padding-bottom: 2rem !important; 
}

.emoji-img {
    width: 22px;
    height: 22px;
    vertical-align: -4px;
    display: inline-block;
    margin-right: 6px;
}

.emoji-img-md {
    width: 28px;
    height: 28px;
    vertical-align: -5px;
    display: inline-block;
    margin-right: 6px;
}

.emoji-img-lg {
    width: 42px;
    height: 42px;
    display: inline-block;
    margin-top: 6px;
}

.sidebar-label {
    font-size: 0.88rem;
    font-weight: 700;
    margin-bottom: 5px;
    color: #FFFFFF;
}

.hero-card {
    background-color: #0F0F0F;
    padding: 24px 18px;
    border-radius: 20px;
    border: 1px solid #2B2B2B;
    text-align: center;
    box-shadow: 0 8px 24px rgba(255,255,255,0.03);
    margin-bottom: 18px;
}
.welcome-logo { 
    width: 80px; 
    height: 80px; 
    object-fit: contain; 
    margin-bottom: 10px; 
    filter: grayscale(100%) brightness(200%);
}
.welcome-title { font-size: 1.7rem; font-weight: 900; color: #FFFFFF; letter-spacing: 1px; }
.welcome-subtitle { font-size: 0.75rem; color: #888888; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; }

.upload-card {
    background-color: #0F0F0F;
    padding: 20px;
    border-radius: 18px;
    border: 2px dashed #FFFFFF;
    text-align: center;
    margin-bottom: 14px;
}
.upload-title { font-size: 1.1rem; font-weight: 800; color: #FFFFFF; margin-bottom: 4px; }
.upload-sub { font-size: 0.8rem; color: #888888; margin-bottom: 4px; }

.stButton > button, 
div[data-testid="stFileUploader"] button,
button[kind="secondary"],
button[kind="primary"] {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid #FFFFFF !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    box-shadow: 0 4px 12px rgba(255,255,255,0.15) !important;
    transition: all 0.2s ease-in-out !important;
}

.stButton > button:hover, 
div[data-testid="stFileUploader"] button:hover {
    background-color: #D9D9D9 !important;
    color: #000000 !important;
    transform: scale(1.02);
}

.stat-banner { 
    background-color: #0F0F0F; 
    border-radius: 14px; 
    padding: 14px 8px; 
    border: 1px solid #2B2B2B; 
    display: flex; 
    justify-content: space-around; 
    text-align: center; 
    margin-bottom: 15px; 
    box-shadow: 0 4px 14px rgba(255,255,255,0.04);
}
.stat-item { flex: 1; }
.stat-value-green { font-size: 1.35rem; font-weight: 900; color: #FFFFFF; }
.stat-value-blue { font-size: 1.35rem; font-weight: 900; color: #FFFFFF; text-decoration: underline; }
.stat-value-orange { font-size: 1.35rem; font-weight: 900; color: #888888; }
.stat-label { font-size: 0.68rem; color: #888888; font-weight: bold; margin-top: 2px; letter-spacing: 0.5px; }

.custom-card { 
    background-color: #0F0F0F; 
    padding: 16px; 
    border-radius: 14px; 
    border: 1px solid #FFFFFF; 
    margin-bottom: 15px; 
    text-align: center; 
    color: #FFFFFF;
    box-shadow: 0 4px 14px rgba(255,255,255,0.06);
}
.stop-number-big { font-size: 4rem; font-weight: 900; color: #FFFFFF; line-height: 1; margin-bottom: 8px; }

.camera-header { text-align: center; margin-top: 5px; margin-bottom: 8px; }
.camera-title { font-size: 1.05rem; font-weight: 800; color: #FFFFFF; text-transform: uppercase; }
.camera-sub { font-size: 0.78rem; color: #888888; }

div[data-testid="stCustomComponentV1"] { 
    width: 100% !important;
    border-radius: 16px;
    border: 2px solid #FFFFFF;
    background-color: #000000;
    margin-bottom: 15px;
    overflow: hidden;
}

div[data-testid="stExpander"] {
    background-color: #0F0F0F !important;
    border: 1px solid #2B2B2B !important;
    border-radius: 12px !important;
}
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# SCRIPT: FLASH E BEEP
js_flash_html = '<img src="' + IMG_FLASH + '" style="width:18px; height:18px; vertical-align:-3px; margin-right:4px;"> Flash'
js_bolt_html = '<img src="' + IMG_BOLT + '" style="width:18px; height:18px; vertical-align:-3px; margin-right:4px;"> Flash ON'

js_camera = """<script>
function playBeep() {
    try {
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var osc = ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, ctx.currentTime);
        osc.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.1);
    } catch(e) {}
}

function aplicarMelhorias() {
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(frame) {
        try {
            var doc = frame.contentDocument || frame.contentWindow.document;
            if (doc && doc.querySelector('video')) {
                if (!doc.getElementById('btn-flash')) {
                    var btn = doc.createElement('button');
                    btn.id = 'btn-flash'; 
                    btn.innerHTML = '""" + js_flash_html + """';
                    btn.style.cssText = 'position:absolute; top:10px; right:10px; z-index:9999; background:#FFFFFF; color:#000000; border:1px solid #FFF; padding:6px 14px; border-radius:18px; font-weight:800; font-size:12px; cursor:pointer; box-shadow:0 2px 8px rgba(0,0,0,0.4); display:flex; align-items:center;';
                    btn.onclick = async function() {
                        try {
                            var track = doc.querySelector('video').srcObject.getVideoTracks()[0];
                            var capabilities = track.getCapabilities ? track.getCapabilities() : {};
                            if (capabilities.torch) {
                                var on = btn.innerHTML.includes('ON');
                                await track.applyConstraints({advanced: [{torch: !on}]});
                                btn.innerHTML = !on ? '""" + js_bolt_html + """' : '""" + js_flash_html + """';
                            }
                        } catch(err) {}
                    };
                    doc.body.appendChild(btn);
                }
            }
        } catch(e) {}
    });
}
setInterval(aplicarMelhorias, 400);
</script>"""
components.html(js_camera, height=0)

# FUNÇÕES AUXILIARES
def extrair_codigo_chave(texto):
    if not texto:
        return ""
    match_br = re.search(r'BR[A-Za-z0-9]{8,25}', texto, re.IGNORECASE)
    if match_br:
        return match_br.group(0).upper().strip()
    return re.sub(r'[^A-Za-z0-9]', '', texto).upper().strip()

def normalizar_endereco(texto):
    if not texto:
        return ""
    m = re.search(r'(?:r(?:ua)?\.?|av(?:enida)?\.?|al(?:ameda)?\.?|est(?:rada)?\.?|tv|travessa)\s+([^,]+?)\s*,\s*(\d+)', texto, re.IGNORECASE)
    if m:
        rua_limpa = re.sub(r'[^a-zA-Z0-9]', '', m.group(1).lower())
        num_limpo = m.group(2).strip()
        return f"{rua_limpa}_{num_limpo}"
    return re.sub(r'[^a-zA-Z0-9]', '', texto)[:35].lower()

# TELA PRINCIPAL
st.markdown(
    '<div class="hero-card">'
    '<img src="' + URL_DO_LOGO + '" class="welcome-logo">'
    '<div class="welcome-title"><img src="' + IMG_TRUCK + '" class="emoji-img-md"> ' + NOME_DO_APP + '</div>'
    '<div class="welcome-subtitle">SISTEMA INTELIGENTE DE LOGÍSTICA</div>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="upload-card">'
    '<div class="upload-title"><img src="' + IMG_DOC + '" class="emoji-img-md"> CARREGAR ROTA DA ENTREGA</div>'
    '<div class="upload-sub">Envie o arquivo PDF da sua rota logo abaixo para liberar a câmera</div>'
    '<div><img src="' + IMG_DOWN + '" class="emoji-img-lg"></div>'
    '</div>',
    unsafe_allow_html=True
)

arquivo_pdf = st.file_uploader(
    "Selecione o PDF da Rota", 
    type=["pdf"], 
    key="pdf_main", 
    label_visibility="collapsed"
)

mapa_rotas = {}
stop_correspondente = {}
nome_exibicao = {}
todos_pacotes = set()

# PROCESSAMENTO DO PDF
if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "\n".join([p.extract_text() or "" for p in leitor.pages])
    linhas = texto.split('\n')
    
    seq_stop_auto = 0
    termos_ignorar = [
        "ADDRESS", "NOTES", "CIRCUIT", "OPTIMIZED", "STOP", 
        "DELIVERY", "ROUTE", "DISPATCH", "TOTAL", "PACKAGE"
    ]
    
    for idx, linha in enumerate(linhas):
        linha_str = linha.strip()
        if not linha_str:
            continue
            
        cods_validos = re.findall(r'BR[A-Za-z0-9]{10,20}', linha_str, re.IGNORECASE)
        
        if not cods_validos:
            candidatos = re.findall(r'\b[A-Za-z0-9]{10,22}\b', linha_str)
            for c in candidatos:
                c_up = c.upper()
                if (
                    not c.isdigit() 
                    and not c.isalpha() 
                    and not any(t in c_up for t in termos_ignorar)
                ):
                    cods_validos.append(c)
        
        cods_validos = [c.upper() for c in cods_validos]
        
        if cods_validos:
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
                end_key = f"pacote_isolado_{cods_validos[0]}"
                
            if end_key not in mapa_rotas:
                mapa_rotas[end_key] = []
                nome_exibicao[end_key] = linha_str[:45]
                
            for c in cods_validos:
                todos_pacotes.add(c)
                if c not in mapa_rotas[end_key]:
                    mapa_rotas[end_key].append(c)
                stop_correspondente[c] = stop_num

# TELA DE EXECUÇÃO
if arquivo_pdf:
    banner_placeholder = st.empty()
    
    with st.expander("Ver pacotes no mesmo endereço / duplos"):
        encontrou_duplo = False
        for end, pacotes in mapa_rotas.items():
            if len(pacotes) > 1 and not end.startswith("pacote_isolado_"):
                encontrou_duplo = True
                numeros_stops = ", ".join([f"P{stop_correspondente.get(p)}" for p in pacotes])
                msg_duplo = '<img src="' + IMG_SIREN + '" class="emoji-img"> <b>' + nome_exibicao.get(end, end).title() + '</b>: <code>' + str(len(pacotes)) + ' pcts</code> (' + numeros_stops + ')'
                st.markdown(msg_duplo, unsafe_allow_html=True)
        if not encontrou_duplo:
            st.info("Nenhum endereço com múltiplos pacotes nesta rota.")

    st.markdown(
        '<div class="camera-header">'
        '<div class="camera-title"><img src="' + IMG_CAMERA + '" class="emoji-img-md"> BIPAR PACOTE</div>'
        '<div class="camera-sub">Aponte a câmera para o QR Code do pacote</div>'
        '</div>',
        unsafe_allow_html=True
    )

    code = qrcode_scanner(key="s1")
    
    st.markdown(
        '#### <img src="' + IMG_KEYBOARD + '" class="emoji-img"> Digitar código manualmente',
        unsafe_allow_html=True
    )
    input_code = st.text_input("", placeholder="Digite ou cole o código aqui...", label_visibility="collapsed")
    
    bruto = code or input_code
    
    if bruto:
        cod_limpo = extrair_codigo_chave(bruto)
        achou = False
        pacote_identificado = None
        
        for cod_registrado in todos_pacotes:
            if cod_registrado == cod_limpo or cod_registrado in bruto.upper() or cod_limpo in cod_registrado:
                pacote_identificado = cod_registrado
                achou = True
                break
                
        if achou and pacote_identificado:
            st.session_state.pacotes_bipados.add(pacote_identificado)
            num_p = stop_correspondente.get(pacote_identificado, "?")
            
            end_match = ""
            lista_duplos = []
            for end, pacs in mapa_rotas.items():
                if pacote_identificado in pacs:
                    end_match = end
                    lista_duplos = pacs
                    break

            components.html("<script>playBeep();</script>", height=0)
            
            card_pacote_html = (
                '<div class="custom-card">'
                '<div class="stop-number-big">P' + str(num_p) + '</div>'
                '<div><img src="' + IMG_PIN + '" class="emoji-img"> Pacote: ' + str(pacote_identificado) + '</div>'
                '</div>'
            )
            st.markdown(card_pacote_html, unsafe_allow_html=True)
            
            outros_stops = [f"P{stop_correspondente.get(p, '?')}" for p in lista_duplos if p != pacote_identificado]
            if outros_stops and not end_match.startswith("pacote_isolado_"):
                st.warning("⚠️ **MESMO ENDEREÇO!** Este local também tem o(s) pacote(s): " + ", ".join(outros_stops))

            if usar_audio:
                fala_texto = str(num_p)
                if outros_stops and not end_match.startswith("pacote_isolado_"):
                    fala_texto += " Atenção! Mesmo endereço da parada " + outros_stops[0].replace('P', '') + "!"
                    
                pitch_val = "1.0"
                rate_val = "1.0"
                
                if "Masculina" in tipo_voz:
                    pitch_val = "0.6"
                    rate_val = "0.95"
                elif "Rápida" in tipo_voz:
                    pitch_val = "1.1"
                    rate_val = "1.35"

                js_audio = (
                    "<script>"
                    "(function() {"
                    "    try {"
                    "        window.speechSynthesis.cancel();"
                    "        var msg = new SpeechSynthesisUtterance('" + fala_texto + "');"
                    "        msg.lang = 'pt-BR';"
                    "        msg.pitch = " + pitch_val + ";"
                    "        msg.rate = " + rate_val + ";"
                    "        window.speechSynthesis.speak(msg);"
                    "    } catch(e) {}"
                    "})();"
                    "</script>"
                )
                components.html(js_audio, height=0)
        else:
            st.error(f"❌ Código `{cod_limpo or bruto}` não encontrado no PDF!")
            st.caption(f"Valor bruto lido: `{bruto}`")

    # Renderiza o banner instantaneamente sem quebra de aspas
    bipados = len(st.session_state.pacotes_bipados)
    total_pacotes = len(todos_pacotes)
    faltam = max(0, total_pacotes - bipados)
    total_paradas = len(mapa_rotas)
    
    html_banner = (
        '<div class="stat-banner">'
        '    <div class="stat-item">'
        '        <div class="stat-value-green">' + str(bipados) + ' / ' + str(total_pacotes) + '</div>'
        '        <div class="stat-label">PACOTES</div>'
        '    </div>'
        '    <div class="stat-item">'
        '        <div class="stat-value-blue">' + str(total_paradas) + '</div>'
        '        <div class="stat-label">PARADAS REAIS</div>'
        '    </div>'
        '    <div class="stat-item">'
        '        <div class="stat-value-orange">' + str(faltam) + '</div>'
        '        <div class="stat-label">FALTAM</div>'
        '    </div>'
        '</div>'
    )
    banner_placeholder.markdown(html_banner, unsafe_allow_html=True)
            
