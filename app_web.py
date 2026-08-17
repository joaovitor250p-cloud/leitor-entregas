import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
NOME_DO_APP = "PACOTE É MATO"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"

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
    st.title(f"🚚 {NOME_DO_APP}")
    st.caption("Sistema Inteligente de Logística")
    st.write("---")
    
    tema_cor = st.selectbox(
        "🎨 Cor do Tema",
        ["Preto (Dark)", "RGB Gamer 🌈", "Branco (Light)", "Cinza", "Azul", "Vermelho"]
    )
    
    arquivo_pdf_sidebar = st.file_uploader("📂 Enviar PDF da Rota (Menu)", type=["pdf"], key="pdf_sidebar")
    
    usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
    tipo_voz = "Feminina / Normal"
    if usar_audio:
        tipo_voz = st.selectbox(
            "🎙️ Estilo da Voz", 
            [
                "Feminina / Normal", 
                "Masculina / Grave", 
                "Rápida / Ágil", 
                "Pica-Pau 🪶",
                "Locutor de Rádio 🎙️",
                "Vilão / Monstro 😈",
                "Esquilo 🐿️"
            ]
        )
        
    st.write("---")
    if st.button("🔄 Zerar Rota Atual"):
        st.session_state.pacotes_bipados = set()
        st.rerun()

# DEFINIÇÃO DAS PALETAS DE CORES
estilos_temas = {
    "Preto (Dark)": {
        "bg_app": "#121212", "text_app": "#FFFFFF", "card_bg": "#1E1E1E", "border": "#333333", "accent": "#FF9500"
    },
    "RGB Gamer 🌈": {
        "bg_app": "#0D0D11", "text_app": "#FFFFFF", "card_bg": "#16161D", "border": "#222230", "accent": "#00FFCC"
    },
    "Branco (Light)": {
        "bg_app": "#F5F5F7", "text_app": "#1D1D1F", "card_bg": "#FFFFFF", "border": "#E5E5EA", "accent": "#007AFF"
    },
    "Cinza": {
        "bg_app": "#2C2C2E", "text_app": "#F2F2F7", "card_bg": "#3A3A3C", "border": "#48484A", "accent": "#FF9500"
    },
    "Azul": {
        "bg_app": "#0B192C", "text_app": "#E0F2FE", "card_bg": "#1E3E62", "border": "#0087D1", "accent": "#38BDF8"
    },
    "Vermelho": {
        "bg_app": "#1A0000", "text_app": "#FFE5E5", "card_bg": "#330000", "border": "#800000", "accent": "#FF4D4D"
    }
}

t = estilos_temas.get(tema_cor, estilos_temas["Preto (Dark)"])
cor_accent = t["accent"]

# ANIMAÇÃO CSS RGB
css_rgb_anim = ""
if tema_cor == "RGB Gamer 🌈":
    css_rgb_anim = """
    @keyframes rgbGlow {
        0% { border-color: #FF0000; color: #FF0000; box-shadow: 0 0 12px rgba(255,0,0,0.5); }
        20% { border-color: #FF8800; color: #FF8800; box-shadow: 0 0 12px rgba(255,136,0,0.5); }
        40% { border-color: #FFFF00; color: #FFFF00; box-shadow: 0 0 12px rgba(255,255,0,0.5); }
        60% { border-color: #00FF66; color: #00FF66; box-shadow: 0 0 12px rgba(0,255,102,0.5); }
        80% { border-color: #00CCFF; color: #00CCFF; box-shadow: 0 0 12px rgba(0,204,255,0.5); }
        100% { border-color: #FF0000; color: #FF0000; box-shadow: 0 0 12px rgba(255,0,0,0.5); }
    }
    .welcome-title, .camera-title, .stop-number-big, .stat-value-orange, .stat-value-blue, .upload-title {
        animation: rgbGlow 6s infinite linear !important;
    }
    .upload-card, div[data-testid="stCustomComponentV1"] {
        animation: rgbGlow 6s infinite linear !important;
    }
    """

# ESTILO VISUAL DINÂMICO
st.markdown(f"""
<style>
.stApp {{ background-color: {t['bg_app']}; color: {t['text_app']}; }}
.block-container {{ padding-top: 1.2rem !important; padding-bottom: 2rem !important; }}

.hero-card {{
    background: linear-gradient(145deg, {t['card_bg']}, {t['bg_app']});
    padding: 24px 18px;
    border-radius: 20px;
    border: 1px solid {t['border']};
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    margin-bottom: 18px;
}}
.welcome-logo {{ width: 80px; height: 80px; object-fit: contain; margin-bottom: 10px; }}
.welcome-title {{ font-size: 1.7rem; font-weight: 900; color: {t['accent']}; letter-spacing: 1px; }}
.welcome-subtitle {{ font-size: 0.75rem; color: #888888; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; }}

.upload-card {{
    background-color: {t['card_bg']};
    padding: 20px;
    border-radius: 18px;
    border: 2px dashed {t['accent']};
    text-align: center;
    margin-bottom: 20px;
}}
.upload-title {{ font-size: 1.1rem; font-weight: 800; color: {t['text_app']}; margin-bottom: 6px; }}
.upload-sub {{ font-size: 0.8rem; color: #999999; }}

.stat-banner {{ 
    background-color: {t['card_bg']}; 
    border-radius: 14px; 
    padding: 14px 8px; 
    border: 1px solid {t['border']}; 
    display: flex; 
    justify-content: space-around; 
    text-align: center; 
    margin-bottom: 15px; 
}}
.stat-item {{ flex: 1; }}
.stat-value-green {{ font-size: 1.35rem; font-weight: bold; color: #28a745; }}
.stat-value-blue {{ font-size: 1.35rem; font-weight: bold; color: {t['accent']}; }}
.stat-value-orange {{ font-size: 1.35rem; font-weight: bold; color: #FFB703; }}
.stat-label {{ font-size: 0.68rem; color: #AAAAAA; font-weight: bold; margin-top: 2px; letter-spacing: 0.5px; }}

.custom-card {{ background-color: {t['card_bg']}; padding: 16px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 15px; border-top: 1px solid {t['border']}; border-right: 1px solid {t['border']}; border-bottom: 1px solid {t['border']}; text-align: center; }}
.stop-number-big {{ font-size: 3.8rem; font-weight: 900; color: {t['accent']}; line-height: 1; margin-bottom: 8px; }}

.camera-header {{ text-align: center; margin-top: 5px; margin-bottom: 8px; }}
.camera-title {{ font-size: 1.05rem; font-weight: 800; color: {t['accent']}; text-transform: uppercase; }}
.camera-sub {{ font-size: 0.78rem; color: #888888; }}

div[data-testid="stCustomComponentV1"] {{ 
    width: 100% !important;
    border-radius: 16px;
    border: 2px solid {t['accent']};
    background-color: #000000;
    margin-bottom: 15px;
    overflow: hidden;
}}

{css_rgb_anim}
</style>
""", unsafe_allow_html=True)

# SCRIPT: FLASH E BEEP
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
                    btn.innerHTML = '🔦 Flash';
                    btn.style.cssText = 'position:absolute; top:10px; right:10px; z-index:9999; background:rgba(0,0,0,0.75); color:#FFF; border:1px solid ' + ACCENT_COLOR + '; padding:6px 12px; border-radius:18px; font-weight:bold; font-size:12px; cursor:pointer;';
                    btn.onclick = async function() {
                        try {
                            var track = doc.querySelector('video').srcObject.getVideoTracks()[0];
                            var capabilities = track.getCapabilities ? track.getCapabilities() : {};
                            if (capabilities.torch) {
                                var on = btn.innerHTML.includes('ON');
                                await track.applyConstraints({advanced: [{torch: !on}]});
                                btn.innerHTML = !on ? '⚡ Flash ON' : '🔦 Flash';
                            }
                        } catch(err) {}
                    };
                    doc.body.appendChild(btn);
                }
            }
        } catch(e) {}
    });
}
var ACCENT_COLOR = '""" + cor_accent + """';
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
arquivo_pdf_main = None
if not arquivo_pdf_sidebar:
    st.markdown(f"""
    <div class="hero-card">
        <img src="{URL_DO_LOGO}" class="welcome-logo">
        <div class="welcome-title">{NOME_DO_APP}</div>
        <div class="welcome-subtitle">SISTEMA INTELIGENTE DE LOGÍSTICA</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-card">
        <div class="upload-title">📄 CARREGAR ROTA DA ENTREGA</div>
        <div class="upload-sub">Envie o arquivo PDF da sua rota para liberar a câmera e a bipagem</div>
    </div>
    """, unsafe_allow_html=True)
    
    arquivo_pdf_main = st.file_uploader("Selecione o PDF da Rota", type=["pdf"], key="pdf_main", label_visibility="collapsed")

arquivo_pdf = arquivo_pdf_sidebar or arquivo_pdf_main

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
            
            # Pega o número real sequencial do pacote na rota (ex: 11, 12, etc.)
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
                # Cada pacote guarda seu próprio número real individual
                stop_correspondente[c] = stop_num

# TELA DE EXECUÇÃO
if arquivo_pdf:
    bipados = len(st.session_state.pacotes_bipados)
    total_pacotes = len(todos_pacotes)
    faltam = max(0, total_pacotes - bipados)
    
    # Paradas Reais = total de endereços físicos únicos
    total_paradas = len(mapa_rotas)
    
    st.markdown(f"""<div class="stat-banner">
        <div class="stat-item">
            <div class="stat-value-green">{bipados} / {total_pacotes}</div>
            <div class="stat-label">PACOTES</div>
        </div>
        <div class="stat-item">
            <div class="stat-value-blue">{total_paradas}</div>
            <div class="stat-label">PARADAS REAIS</div>
        </div>
        <div class="stat-item">
            <div class="stat-value-orange">{faltam}</div>
            <div class="stat-label">FALTAM</div>
        </div>
    </div>""", unsafe_allow_html=True)
    
    with st.expander("🤖 Ver pacotes no mesmo endereço / duplos"):
        encontrou_duplo = False
        for end, pacotes in mapa_rotas.items():
            if len(pacotes) > 1 and not end.startswith("pacote_isolado_"):
                encontrou_duplo = True
                numeros_stops = ", ".join([f"P{stop_correspondente.get(p)}" for p in pacotes])
                st.markdown(f"🚨 **{nome_exibicao.get(end, end).title()}**: `{len(pacotes)} pcts` ({numeros_stops})")
        if not encontrou_duplo:
            st.info("Nenhum endereço com múltiplos pacotes nesta rota.")

    st.markdown("""<div class="camera-header">
        <div class="camera-title">📸 BIPAR PACOTE</div>
        <div class="camera-sub">Aponte a câmera para o QR Code do pacote</div>
    </div>""", unsafe_allow_html=True)

    code = qrcode_scanner(key="s1")
    
    st.markdown("#### ⌨️ Digitar código manualmente")
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
            
            st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{num_p}</div><div>📍 Pacote: {pacote_identificado}</div></div>', unsafe_allow_html=True)
            
            # Se tiver outros pacotes no mesmo local, lista exatamente os números irmãos
            outros_stops = [f"P{stop_correspondente.get(p, '?')}" for p in lista_duplos if p != pacote_identificado]
            if outros_stops and not end_match.startswith("pacote_isolado_"):
                st.warning(f"⚠️ **MESMO ENDEREÇO!** Este local também tem o(s) pacote(s): " + ", ".join(outros_stops))

            if usar_audio:
                fala_texto = f"{num_p}"
                if outros_stops and not end_match.startswith("pacote_isolado_"):
                    fala_texto += f" Atenção! Mesmo endereço da parada {outros_stops[0].replace('P', '')}!"
                    
                pitch_val = "1.0"
                rate_val = "1.0"
                
                if "Pica-Pau" in tipo_voz:
                    fala_texto = f"He-he-he-he! {num_p}!"
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

                js_audio = f"""
                <script>
                (function() {{
                    try {{
                        window.speechSynthesis.cancel();
                        var msg = new SpeechSynthesisUtterance('{fala_texto}');
                        msg.lang = 'pt-BR';
                        msg.pitch = {pitch_val};
                        msg.rate = {rate_val};
                        window.speechSynthesis.speak(msg);
                    }} catch(e) {{}}
                }})();
                </script>
                """
                components.html(js_audio, height=0)
        else:
            st.error(f"❌ Código `{cod_limpo or bruto}` não encontrado no PDF!")
            st.caption(f"Valor bruto lido: `{bruto}`")
            
