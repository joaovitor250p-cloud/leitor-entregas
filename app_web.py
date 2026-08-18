import datetime
import re
from zoneinfo import ZoneInfo
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
NOME_DO_APP = "BIPAI"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"
IMG_MOTO = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f3cd_fe0f/512.gif"
CHAVE_PIX = "093.547.085-95"

st.set_page_config(
    page_title=NOME_DO_APP,
    page_icon=URL_DO_LOGO,
    layout="centered"
)

# Memória de Bipados
if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()

# TRADUÇÕES DO SISTEMA (PT / ES / EN)
TRADUCOES = {
    "Português 🇧🇷": {
        "lang_code": "pt-BR",
        "subtitulo": "SISTEMA INTELIGENTE DE LOGÍSTICA",
        "cor_modo": "🎨 Modo de Cor",
        "opcao_preto": "Preto (Dark)",
        "opcao_branco": "Branco (Light)",
        "falar_toggle": "🔊 Falar Número da Parada",
        "estilo_voz": "🎙️ Estilo da Voz",
        "vozes": ["Feminina / Normal", "Masculina / Grave", "Rápida / Ágil"],
        "btn_zerar": "🔄 Zerar Rota Atual",
        "upload_titulo": "📄 CARREGAR ROTA DA ENTREGA",
        "upload_sub": "Envie o arquivo PDF da sua rota logo abaixo para liberar a câmera",
        "pix_titulo": "🚀 Fortaleça o Projeto BIPAI!",
        "pix_desc": "O app agilizou sua rota e organização? Contribua com qualquer valor para manter o sistema online:",
        "pix_rotulo": "🔑 Pix (CPF):",
        "duplos_titulo": "🤖 Ver pacotes no mesmo endereço / duplos",
        "nenhum_duplo": "Nenhum endereço com múltiplos pacotes nesta rota.",
        "camera_titulo": "📸 BIPAR PACOTE",
        "camera_sub": "Aponte a câmera para o QR Code do pacote",
        "digitar_manual": "⌨️ Digitar código manualmente",
        "placeholder_input": "Digite ou cole o código aqui...",
        "pacote_rotulo": "📍 Pacote: ",
        "alerta_duplo": "⚠️ **MESMO ENDEREÇO!** Este local também tem o(s) pacote(s): ",
        "fala_atencao": " Atenção! Mesmo endereço da parada ",
        "erro_nao_encontrado": "❌ Código `{code}` não encontrado no PDF!",
        "valor_bruto": "Valor bruto lido: `{bruto}`",
        "horario": "🕒 HORÁRIO: ",
        "card_pacotes": "PACOTES",
        "card_paradas": "PARADAS REAIS",
        "card_faltam": "FALTAM"
    },
    "Español 🇪🇸": {
        "lang_code": "es-ES",
        "subtitulo": "SISTEMA INTELIGENTE DE LOGÍSTICA",
        "cor_modo": "🎨 Modo de Color",
        "opcao_preto": "Negro (Dark)",
        "opcao_branco": "Blanco (Light)",
        "falar_toggle": "🔊 Decir Número de Parada",
        "estilo_voz": "🎙️ Estilo de Voz",
        "vozes": ["Femenina / Normal", "Masculina / Grave", "Rápida / Ágil"],
        "btn_zerar": "🔄 Reiniciar Ruta Actual",
        "upload_titulo": "📄 CARGAR RUTA DE ENTREGA",
        "upload_sub": "Envía el archivo PDF de tu ruta abajo para habilitar la cámara",
        "pix_titulo": "🚀 ¡Apoya el Proyecto BIPAI!",
        "pix_desc": "¿La app agilizó tu ruta y organización? Contribuye con cualquier monto para mantener el sistema activo:",
        "pix_rotulo": "🔑 Pix (Brasil):",
        "duplos_titulo": "🤖 Ver paquetes en la misma dirección / dobles",
        "nenhum_duplo": "Ninguna dirección con múltiples paquetes en esta ruta.",
        "camera_titulo": "📸 ESCANEAR PAQUETE",
        "camera_sub": "Apunta la cámara al código QR del paquete",
        "digitar_manual": "⌨️ Escribir código manualmente",
        "placeholder_input": "Escribe o pega el código aquí...",
        "pacote_rotulo": "📍 Paquete: ",
        "alerta_duplo": "⚠️ **¡MISMA DIRECCIÓN!** Esta ubicación también tiene el/los paquete(s): ",
        "fala_atencao": " ¡Atención! ¡Misma dirección que la parada ",
        "erro_nao_encontrado": "❌ ¡Código `{code}` no encontrado en el PDF!",
        "valor_bruto": "Valor bruto leído: `{bruto}`",
        "horario": "🕒 HORA: ",
        "card_pacotes": "PAQUETES",
        "card_paradas": "PARADAS REALES",
        "card_faltam": "FALTAN"
    },
    "English 🇺🇸": {
        "lang_code": "en-US",
        "subtitulo": "INTELLIGENT LOGISTICS SYSTEM",
        "cor_modo": "🎨 Color Mode",
        "opcao_preto": "Black (Dark)",
        "opcao_branco": "White (Light)",
        "falar_toggle": "🔊 Speak Stop Number",
        "estilo_voz": "🎙️ Voice Style",
        "vozes": ["Female / Normal", "Male / Deep", "Fast / Agile"],
        "btn_zerar": "🔄 Reset Current Route",
        "upload_titulo": "📄 UPLOAD DELIVERY ROUTE",
        "upload_sub": "Upload your route PDF file below to unlock the camera scanner",
        "pix_titulo": "🚀 Support the BIPAI Project!",
        "pix_desc": "Did the app speed up your route? Contribute any amount to keep the system online:",
        "pix_rotulo": "🔑 Pix (Brazil):",
        "duplos_titulo": "🤖 View packages at same address / duplicates",
        "nenhum_duplo": "No multiple packages found for the same address.",
        "camera_titulo": "📸 SCAN PACKAGE",
        "camera_sub": "Point your camera at the package QR Code",
        "digitar_manual": "⌨️ Type code manually",
        "placeholder_input": "Type or paste tracking code here...",
        "pacote_rotulo": "📍 Package: ",
        "alerta_duplo": "⚠️ **SAME ADDRESS!** This location also includes package(s): ",
        "fala_atencao": " Attention! Same address as stop ",
        "erro_nao_encontrado": "❌ Code `{code}` not found in PDF!",
        "valor_bruto": "Raw scanned value: `{bruto}`",
        "horario": "🕒 TIME: ",
        "card_pacotes": "PACKAGES",
        "card_paradas": "REAL STOPS",
        "card_faltam": "REMAINING"
    }
}

# MENU LATERAL
with st.sidebar:
    st.markdown(
        '<h2 style="margin-bottom:2px; font-weight:900;"><img src="' + IMG_MOTO + '" style="width:30px; height:30px; vertical-align:-5px; margin-right:6px;"> ' + NOME_DO_APP + '</h2>',
        unsafe_allow_html=True
    )
    
    idioma = st.selectbox(
        "🌐 Idioma / Language",
        ["Português 🇧🇷", "Español 🇪🇸", "English 🇺🇸"],
        index=0
    )
    
    t_lang = TRADUCOES[idioma]
    st.caption(t_lang["subtitulo"])
    st.write("---")
    
    modo_cor_opcao = st.selectbox(
        t_lang["cor_modo"],
        [t_lang["opcao_preto"], t_lang["opcao_branco"]],
        index=0
    )
    tema_escuro = (modo_cor_opcao == t_lang["opcao_preto"])
    
    usar_audio = st.toggle(t_lang["falar_toggle"], value=True)
    tipo_voz_index = 0
    if usar_audio:
        tipo_voz = st.selectbox(
            t_lang["estilo_voz"], 
            t_lang["vozes"]
        )
        tipo_voz_index = t_lang["vozes"].index(tipo_voz)
        
    st.write("---")
    if st.button(t_lang["btn_zerar"]):
        st.session_state.pacotes_bipados = set()
        st.rerun()

# PALETA PRETO & BRANCO
if tema_escuro:
    t = {
        "bg_app": "#000000",
        "text_app": "#FFFFFF",
        "card_bg": "#0B0B0B",
        "border": "#FFFFFF",
        "btn_bg": "#FFFFFF",
        "btn_text": "#000000",
        "subtext": "#AAAAAA",
        "shadow": "rgba(255,255,255,0.12)"
    }
else:
    t = {
        "bg_app": "#FFFFFF",
        "text_app": "#000000",
        "card_bg": "#F5F5F7",
        "border": "#000000",
        "btn_bg": "#000000",
        "btn_text": "#FFFFFF",
        "subtext": "#555555",
        "shadow": "rgba(0,0,0,0.15)"
    }

# CSS DINÂMICO
css_style = (
    "<style>"
    ".stApp { background-color: " + t['bg_app'] + " !important; color: " + t['text_app'] + " !important; }"
    ".block-container { padding-top: 1.2rem !important; padding-bottom: 2rem !important; }"
    
    ".hero-card {"
    "    background-color: " + t['card_bg'] + ";"
    "    padding: 22px 18px;"
    "    border-radius: 20px;"
    "    border: 2px solid " + t['border'] + ";"
    "    text-align: center;"
    "    box-shadow: 0 8px 24px " + t['shadow'] + ";"
    "    margin-bottom: 14px;"
    "}"
    ".welcome-logo { width: 85px; height: 85px; object-fit: contain; margin-bottom: 8px; }"
    ".welcome-title { font-size: 2rem; font-weight: 900; color: " + t['text_app'] + "; letter-spacing: 2px; text-transform: uppercase; }"
    ".welcome-subtitle { font-size: 0.72rem; color: " + t['subtext'] + "; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; }"
    
    ".clock-banner {"
    "    background-color: " + t['card_bg'] + ";"
    "    border-radius: 12px;"
    "    padding: 8px 12px;"
    "    border: 1px solid " + t['border'] + ";"
    "    text-align: center;"
    "    margin-bottom: 12px;"
    "    font-weight: 900;"
    "    font-size: 1rem;"
    "    color: " + t['text_app'] + ";"
    "    letter-spacing: 1px;"
    "}"
    
    ".upload-card {"
    "    background-color: " + t['card_bg'] + ";"
    "    padding: 20px;"
    "    border-radius: 18px;"
    "    border: 2px dashed " + t['border'] + ";"
    "    text-align: center;"
    "    margin-bottom: 14px;"
    "}"
    ".upload-title { font-size: 1.1rem; font-weight: 800; color: " + t['text_app'] + "; margin-bottom: 4px; }"
    ".upload-sub { font-size: 0.8rem; color: " + t['subtext'] + "; margin-bottom: 6px; }"
    ".upload-arrow { font-size: 1.6rem; animation: bounce 1.5s infinite; }"
    
    "@keyframes bounce {"
    "    0%, 20%, 50%, 80%, 100% { transform: translateY(0); }"
    "    40% { transform: translateY(6px); }"
    "    60% { transform: translateY(3px); }"
    "}"
    
    ".stButton > button, div[data-testid='stFileUploader'] button, button[kind='secondary'], button[kind='primary'] {"
    "    background-color: " + t['btn_bg'] + " !important;"
    "    color: " + t['btn_text'] + " !important;"
    "    border: 2px solid " + t['border'] + " !important;"
    "    border-radius: 12px !important;"
    "    font-weight: 900 !important;"
    "    font-size: 0.95rem !important;"
    "    box-shadow: 0 4px 12px " + t['shadow'] + " !important;"
    "    transition: all 0.2s ease-in-out !important;"
    "}"
    
    ".stat-banner {"
    "    background-color: " + t['card_bg'] + ";"
    "    border-radius: 14px;"
    "    padding: 12px 6px;"
    "    border: 2px solid " + t['border'] + ";"
    "    display: flex;"
    "    justify-content: space-around;"
    "    text-align: center;"
    "    margin-bottom: 12px;"
    "    box-shadow: 0 4px 14px " + t['shadow'] + ";"
    "}"
    ".stat-item { flex: 1; }"
    ".stat-value { font-size: 1.25rem; font-weight: 900; color: " + t['text_app'] + "; }"
    ".stat-label { font-size: 0.65rem; color: " + t['subtext'] + "; font-weight: 900; margin-top: 2px; letter-spacing: 0.5px; }"
    
    ".custom-card {"
    "    background-color: " + t['card_bg'] + ";"
    "    padding: 16px;"
    "    border-radius: 14px;"
    "    border: 2px solid " + t['border'] + ";"
    "    margin-bottom: 15px;"
    "    text-align: center;"
    "    color: " + t['text_app'] + ";"
    "    box-shadow: 0 4px 14px " + t['shadow'] + ";"
    "}"
    ".stop-number-big { font-size: 4.2rem; font-weight: 900; color: " + t['text_app'] + "; line-height: 1; margin-bottom: 8px; }"
    
    ".pix-card {"
    "    background-color: " + t['card_bg'] + ";"
    "    border: 1px solid " + t['border'] + ";"
    "    border-radius: 14px;"
    "    padding: 14px;"
    "    text-align: center;"
    "    margin-top: 20px;"
    "    box-shadow: 0 4px 12px " + t['shadow'] + ";"
    "}"
    ".pix-title { font-size: 0.95rem; font-weight: 900; color: " + t['text_app'] + "; margin-bottom: 4px; letter-spacing: 0.5px; }"
    ".pix-desc { font-size: 0.78rem; color: " + t['subtext'] + "; margin-bottom: 8px; }"
    ".pix-key { font-size: 1.05rem; font-weight: 900; color: " + t['text_app'] + "; background: rgba(127,127,127,0.18); padding: 6px 12px; border-radius: 8px; display: inline-block; letter-spacing: 1px; }"
    
    ".camera-header { text-align: center; margin-top: 5px; margin-bottom: 8px; }"
    ".camera-title { font-size: 1.05rem; font-weight: 900; color: " + t['text_app'] + "; text-transform: uppercase; }"
    ".camera-sub { font-size: 0.78rem; color: " + t['subtext'] + "; }"
    
    "div[data-testid='stCustomComponentV1'] {"
    "    width: 100% !important;"
    "    border-radius: 16px;"
    "    border: 2px solid " + t['border'] + ";"
    "    background-color: #000000;"
    "    margin-bottom: 15px;"
    "    overflow: hidden;"
    "}"
    
    "div[data-testid='stExpander'] {"
    "    background-color: " + t['card_bg'] + " !important;"
    "    border: 2px solid " + t['border'] + " !important;"
    "    border-radius: 12px !important;"
    "    color: " + t['text_app'] + " !important;"
    "}"
    "</style>"
)
st.markdown(css_style, unsafe_allow_html=True)

# SCRIPT: FLASH E BEEP
js_camera = (
    "<script>"
    "function playBeep() {"
    "    try {"
    "        var ctx = new (window.AudioContext || window.webkitAudioContext)();"
    "        var osc = ctx.createOscillator();"
    "        osc.type = 'sine';"
    "        osc.frequency.setValueAtTime(880, ctx.currentTime);"
    "        osc.connect(ctx.destination);"
    "        osc.start();"
    "        osc.stop(ctx.currentTime + 0.1);"
    "    } catch(e) {}"
    "}"
    "function aplicarMelhorias() {"
    "    var iframes = window.parent.document.querySelectorAll('iframe');"
    "    iframes.forEach(function(frame) {"
    "        try {"
    "            var doc = frame.contentDocument || frame.contentWindow.document;"
    "            if (doc && doc.querySelector('video')) {"
    "                if (!doc.getElementById('btn-flash')) {"
    "                    var btn = doc.createElement('button');"
    "                    btn.id = 'btn-flash';"
    "                    btn.innerHTML = '🔦 Flash';"
    "                    btn.style.cssText = 'position:absolute; top:10px; right:10px; z-index:9999; background:" + t['btn_bg'] + "; color:" + t['btn_text'] + "; border:2px solid " + t['border'] + "; padding:6px 14px; border-radius:18px; font-weight:900; font-size:12px; cursor:pointer; box-shadow:0 2px 8px " + t['shadow'] + ";';"
    "                    btn.onclick = async function() {"
    "                        try {"
    "                            var track = doc.querySelector('video').srcObject.getVideoTracks()[0];"
    "                            var capabilities = track.getCapabilities ? track.getCapabilities() : {};"
    "                            if (capabilities.torch) {"
    "                                var on = btn.innerHTML.includes('ON');"
    "                                await track.applyConstraints({advanced: [{torch: !on}]});"
    "                                btn.innerHTML = !on ? '⚡ Flash ON' : '🔦 Flash';"
    "                            }"
    "                        } catch(err) {}"
    "                    };"
    "                    doc.body.appendChild(btn);"
    "                }"
    "            }"
    "        } catch(e) {}"
    "    });"
    "}"
    "setInterval(aplicarMelhorias, 400);"
    "</script>"
)
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

# TELA PRINCIPAL (BIPAI)
st.markdown(
    '<div class="hero-card">'
    '<img src="' + URL_DO_LOGO + '" class="welcome-logo">'
    '<div class="welcome-title"><img src="' + IMG_MOTO + '" style="width:36px; height:36px; vertical-align:-6px; margin-right:8px;">' + NOME_DO_APP + '</div>'
    '<div class="welcome-subtitle">' + t_lang["subtitulo"] + '</div>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="upload-card">'
    '<div class="upload-title">' + t_lang["upload_titulo"] + '</div>'
    '<div class="upload-sub">' + t_lang["upload_sub"] + '</div>'
    '<div class="upload-arrow">👇</div>'
    '</div>',
    unsafe_allow_html=True
)

arquivo_pdf = st.file_uploader(
    "Selecione o PDF da Rota", 
    type=["pdf"], 
    key="pdf_main", 
    label_visibility="collapsed"
)

# CARD DO PIX (SOME AO CARREGAR O PDF)
if not arquivo_pdf:
    st.markdown(
        '<div class="pix-card">'
        '    <div class="pix-title">' + t_lang["pix_titulo"] + '</div>'
        '    <div class="pix-desc">' + t_lang["pix_desc"] + '</div>'
        '    <div class="pix-key">' + t_lang["pix_rotulo"] + ' ' + CHAVE_PIX + '</div>'
        '</div>',
        unsafe_allow_html=True
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

# TELA DE EXECUÇÃO (CÂMERA E LEITURA)
if arquivo_pdf:
    banner_placeholder = st.empty()
    
    with st.expander(t_lang["duplos_titulo"]):
        encontrou_duplo = False
        for end, pacotes in mapa_rotas.items():
            if len(pacotes) > 1 and not end.startswith("pacote_isolado_"):
                encontrou_duplo = True
                numeros_stops = ", ".join([f"P{stop_correspondente.get(p)}" for p in pacotes])
                st.markdown(f"🚨 **{nome_exibicao.get(end, end).title()}**: `{len(pacotes)} pcts` ({numeros_stops})")
        if not encontrou_duplo:
            st.info(t_lang["nenhum_duplo"])

    st.markdown(
        '<div class="camera-header">'
        '<div class="camera-title">' + t_lang["camera_titulo"] + '</div>'
        '<div class="camera-sub">' + t_lang["camera_sub"] + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    code = qrcode_scanner(key="s1")
                
