# VERSAO DE TESTE - LEITOR ENTREGAS
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

# Inicialização de Variáveis de Controle
usar_audio = True
tipo_voz = "Feminina / Normal"

# Memória de Bipados
if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()

# MENU LATERAL
with st.sidebar:
    st.title(f"🚚 {NOME_DO_APP}")
    st.caption("Sistema Inteligente de Logística")
    st.write("---")
    
    # SELEÇÃO DE TEMA / COR DO APP (INCLUINDO RGB)
    tema_cor = st.selectbox(
        "🎨 Cor do Tema",
        ["Preto (Dark)", "RGB Gamer 🌈", "Branco (Light)", "Cinza", "Azul", "Vermelho"]
    )
    
    arquivo_pdf_sidebar = st.file_uploader("📂 Enviar PDF da Rota (Menu)", type=["pdf"], key="pdf_sidebar")
    
    usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
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

# ANIMAÇÃO CSS RGB SE O TEMA FOR "RGB Gamer 🌈"
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
    .welcome-title, .camera-title, .stop-number-big, .stat-value-orange, .upload-title {
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
.block-container {{ padding-top: 1.5rem !important; padding-bottom: 2rem !important; }}

/* CARTÃO DE BOAS-VINDAS / HERO DA TELA PRINCIPAL */
.hero-card {{
    background: linear-gradient(145deg, {t['card_bg']}, {t['bg_app']});
    padding: 28px 20px 20px 20px;
    border-radius: 22px;
    border: 1px solid {t['border']};
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}}
.hero-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 4px;
    background: linear-gradient(90deg, #28a745, {t['accent']});
}}
.welcome-logo {{ width: 85px; height: 85px; object-fit: contain; margin-bottom: 12px; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.5)); }}
.welcome-title {{ font-size: 1.8rem; font-weight: 900; color: {t['accent']}; letter-spacing: 1px; margin-bottom: 2px; }}
.welcome-subtitle {{ font-size: 0.8rem; color: #888888; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 10px; }}

/* BANNER DE UPLOAD NA TELA INICIAL */
.upload-card {{
    background-color: {t['card_bg']};
    padding: 22px;
    border-radius: 20px;
    border: 2px dashed {t['accent']};
    text-align: center;
    margin-bottom: 25px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
}}
.upload-title {{ font-size: 1.2rem; font-weight: 800; color: {t['text_app']}; margin-bottom: 6px; display: flex; align-items: center; justify-content: center; gap: 8px; }}
.upload-sub {{ font-size: 0.85rem; color: #999999; margin-bottom: 15px; }}

/* Banner de Estatísticas */
.stat-banner {{ background-color: {t['card_bg']}; border-radius: 12px; padding: 14px; border: 1px solid {t['border']}; display: flex; justify-content: space-around; text-align: center; margin-bottom: 15px; }}
.stat-value-green {{ font-size: 1.5rem; font-weight: bold; color: #28a745; }}
.stat-value-orange {{ font-size: 1.5rem; font-weight: bold; color: {t['accent']}; }}
.stat-label {{ font-size: 0.75rem; color: #AAAAAA; font-weight: bold; letter-spacing: 0.5px; }}

/* Cartão da Parada */
.custom-card {{ background-color: {t['card_bg']}; padding: 18px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 15px; border-top: 1px solid {t['border']}; border-right: 1px solid {t['border']}; border-bottom: 1px solid {t['border']}; }}
.stop-number-big {{ font-size: 3.5rem; font-weight: 900; color: {t['accent']}; line-height: 1; margin-bottom: 10px; }}

/* Seções de Câmera e Digitação */
.camera-header {{ text-align: center; margin-top: 10px; margin-bottom: 5px; }}
.camera-title {{ font-size: 1.1rem; font-weight: 800; color: {t['accent']}; text-transform: uppercase; }}
.camera-sub {{ font-size: 0.8rem; color: #888888; margin-bottom: 10px; }}

div[data-testid="stCustomComponentV1"] {{ 
    width: 100%; height: 350px; display: flex; justify-content: center; align-items: center; border-radius: 16px; border: 2px solid {t['accent']}; background-color: #000000; margin-bottom: 15px; overflow: hidden; position: relative; 
}}
iframe {{ width: 100%; height: 350px; border: none; }}

{css_rgb_anim}
</style>
""", unsafe_allow_html=True)

# SCRIPT: MIRA COM CANTOS BRANCOS + FLASH + BIP
js_camera = f"""<script>
function playBeep() {{
    var ctx = new (window.AudioContext || window.webkitAudioContext)();
    var osc = ctx.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.1);
}}

function aplicarMelhorias() {{
    var iframes = window.parent.document.querySelectorAll('iframe');
    iframes.forEach(function(frame) {{
        try {{
            var doc = frame.contentDocument || frame.contentWindow.document;
            if (doc && doc.querySelector('video')) {{
                var s = doc.createElement('style');
                s.innerHTML = '#qr-shaded-region {{ border: none !important; }} #qr-shaded-region * {{ display: none !important; }} video {{ object-fit: cover !important; }}';
                doc.head.appendChild(s);

                if (!doc.getElementById('custom-target-overlay')) {{
                    var overlay = doc.createElement('div');
                    overlay.id = 'custom-target-overlay';
                    overlay.style.cssText = 'position:absolute; top:15%; left:10%; right:10%; bottom:15%; pointer-events:none; z-index:90;';
                    overlay.innerHTML = `
                        <div style="position:absolute; top:0; left:0; width:35px; height:35px; border-top:5px solid #FFFFFF; border-left:5px solid #FFFFFF; border-top-left-radius:4px;"></div>
                        <div style="position:absolute; top:0; right:0; width:35px; height:35px; border-top:5px solid #FFFFFF; border-right:5px solid #FFFFFF; border-top-right-radius:4px;"></div>
                        <div style="position:absolute; bottom:0; left:0; width:35px; height:35px; border-bottom:5px solid #FFFFFF; border-left:5px solid #FFFFFF; border-bottom-left-radius:4px;"></div>
                        <div style="position:absolute; bottom:0; right:0; width:35px; height:35px; border-bottom:5px solid #FFFFFF; border-right:5px solid #FFFFFF; border-bottom-right-radius:4px;"></div>
                    `;
                    doc.body.appendChild(overlay);
                }}

                if (!doc.getElementById('btn-flash')) {{
                    var btn = doc.createElement('button');
                    btn.id = 'btn-flash'; btn.innerHTML = '🔦 Flash';
                    btn.style.cssText = 'position:absolute; top:10px; right:10px; z-index:999; background:rgba(0,0,0,0.7); color:#FFF; border:1px solid {t["accent"]}; padding:5px 10px; border-radius:15px; font-weight:bold;';
                    btn.onclick = async () => {{
                        var track = doc.querySelector('video').srcObject.getVideoTracks()[0];
                        var on = btn.innerHTML.includes('ON');
                        await track.applyConstraints({{advanced: [{{torch: !on}}]}});
                        btn.innerHTML = !on ? '⚡ Flash ON' : '🔦 Flash';
                    }};
                    doc.body.appendChild(btn);
                }}
            }}
        }} catch(e) {{}}
    }});
}}
setInterval(aplicarMelhorias, 300);
</script>"""
components.html(js_camera, height=0)

# LÓGICA DE EXTRAÇÃO POR ENDEREÇO REAL
def extrair_endereco_limpo(texto):
    match = re.search(r'(rua|av|avenida|al|alameda|estrada|tv|travessa)\s+([a-záàâãéèêíïóôõöúçñ\s]+?)\s*,\s*(\d+)', texto, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2)} {match.group(3)}".lower().strip()
    return None

# TELA PRINCIPAL - VERIFICA SE O PDF FOI ENVIADO NA PRINCIPAL OU NO MENU
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

# DEFINE O ARQUIVO QUE FOI ENVIADO EM QUALQUER UM DOS CAMPOS
arquivo_pdf = arquivo_pdf_sidebar or arquivo_pdf_main

mapa_rotas = {}
stop_correspondente = {}
nome_exibicao = {}
todos_pacotes = set()

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "".join([p.extract_text() + "\n" for p in leitor.pages])
    linhas = texto.split('\n')
    stop_atual = 0
    for linha in linhas:
        m_stop = re.search(r'^\s*(\d{1,3})\b', linha)
        if m_stop:
            stop_atual = int(m_stop.group(1))
        
        cods_candidatos = re.findall(r'BR[A-Za-z0-9]+', linha, re.IGNORECASE)
        cods = [c for c in cods_candidatos if 12 <= len(c) <= 16]
        
        if cods:
            endereco = extrair_endereco_limpo(linha) or f"desconhecido_{stop_atual}"
            if endereco not in mapa_rotas:
                mapa_rotas[endereco] = []
            for c in cods:
                c_u = c.upper()
                todos_pacotes.add(c_u)
                if c_u not in mapa_rotas[endereco]:
                    mapa_rotas[endereco].append(c_u)
                    stop_correspondente[c_u] = stop_atual
                    nome_exibicao[endereco] = linha[:50]

# TELA DE EXECUÇÃO (QUANDO O PDF JÁ FOI CARREGADO)
if arquivo_pdf:
    bipados = len(st.session_state.pacotes_bipados)
    total = len(todos_pacotes)
    faltam = total - bipados
    
    # BANNER PLACAR
    banner_html = f"""<div class="stat-banner">
    <div>
        <div class="stat-value-green">{bipados} / {total}</div>
        <div class="stat-label">BIPADOS</div>
    </div>
    <div>
        <div class="stat-value-orange">{faltam}</div>
        <div class="stat-label">FALTAM</div>
    </div>
</div>"""
    st.markdown(banner_html, unsafe_allow_html=True)
    
    # PAINEL DE PACOTES DUPLOS/TRIPLOS
    with st.expander("🤖 Ver pacotes no mesmo endereço / duplos"):
        encontrou_duplo = False
        for end, pacotes in mapa_rotas.items():
            if len(pacotes) > 1:
                encontrou_duplo = True
                st.markdown(f"🚨 **{end.title()}**: `{len(pacotes)} pcts` (Parada P{stop_correspondente.get(pacotes[0])})")
        if not encontrou_duplo:
            st.info("Nenhum endereço com múltiplos pacotes nesta rota.")

    # TITULO DA CÂMERA
    st.markdown("""<div class="camera-header">
    <div class="camera-title">📸 BIPAR PACOTE</div>
    <div class="camera-sub">Aponte a câmera para o QR Code do pacote</div>
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
                num_p = stop_correspondente.get(cod, "?")
                
                # SOUND BEEP
                components.html("<script>playBeep();</script>", height=0)
                
                st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{num_p}</div><div>📍 Pacote: {cod}</div></div>', unsafe_allow_html=True)
                
                # AVISO COM NÚMERO DA PARADA
                if len(lista) > 1:
                    outros_stops = [f"P{stop_correspondente.get(p, '?')}" for p in lista if p != cod]
                    st.warning(f"⚠️ **MESMO ENDEREÇO!** Pegue também o(s) pacote(s) da(s): " + ", ".join(outros_stops))

                # AUDIO VOICE
                if usar_audio:
                    fala_texto = f"{num_p}"
                    if len(lista) > 1:
                        fala_texto += " Atenção!"
                        
                    pitch_val = "1.0"
                    rate_val = "1.0"
                    
                    if "Pica-Pau" in tipo_voz:
                        fala_texto = f"He-he-he-he! {num_p}!"
                        if len(lista) > 1:
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

                    js_audio = (
                        "<script>"
                        "window.speechSynthesis.cancel();"
                        f"var msg = new SpeechSynthesisUtterance('{fala_texto}');"
                        "msg.lang = 'pt-BR';"
                        f"msg.pitch = {pitch_val};"
                        f"msg.rate = {rate_val};"
                        "window.speechSynthesis.speak(msg);"
                        "</script>"
                    )
                    components.html(js_audio, height=0)

                achou = True
                break
        if not achou:
            st.error("❌ Código não encontrado!")
            
