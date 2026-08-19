import os
import json
import hashlib
import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
NOME_DO_APP = "PACOTE É MATO"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"
IMG_MOTO = "https://fonts.gstatic.com/s/e/notoemoji/latest/1f3cd_fe0f/512.gif"
CHAVE_PIX = "Pacoteemato@gmail.com"

st.set_page_config(
    page_title=NOME_DO_APP,
    page_icon=URL_DO_LOGO,
    layout="centered"
)

# --- SISTEMA DE TELA LIGADA (WAKE LOCK) ---
js_wake_lock = """
<script>
let wakeLock = null;
async function requestWakeLock() {
    if ('wakeLock' in navigator) {
        try {
            wakeLock = await navigator.wakeLock.request('screen');
        } catch (err) {}
    }
}
document.addEventListener('visibilitychange', async () => {
    if (wakeLock !== null && document.visibilityState === 'visible') {
        await requestWakeLock();
    }
});
requestWakeLock();
</script>
"""
components.html(js_wake_lock, height=0)

# Memória de Bipados e Arquivo Atual
if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()

if "arquivo_salvo_atual" not in st.session_state:
    st.session_state.arquivo_salvo_atual = None

# DEFINIÇÃO DOS TEMAS GERAIS
estilos_temas = {
    "Preto (Dark)": {
        "bg_app": "#000000",
        "text_app": "#FFFFFF",
        "card_bg": "#0B0B0B",
        "border": "#FFFFFF",
        "btn_bg": "#FFFFFF",
        "btn_text": "#000000",
        "subtext": "#AAAAAA",
        "shadow": "rgba(255,255,255,0.12)"
    },
    "Branco (Light)": {
        "bg_app": "#FFFFFF",
        "text_app": "#000000",
        "card_bg": "#F5F5F7",
        "border": "#000000",
        "btn_bg": "#000000",
        "btn_text": "#FFFFFF",
        "subtext": "#555555",
        "shadow": "rgba(0,0,0,0.15)"
    },
    "Cinza (Gray)": {
        "bg_app": "#1C1C1E",
        "text_app": "#F2F2F7",
        "card_bg": "#2C2C2E",
        "border": "#8E8E93",
        "btn_bg": "#48484A",
        "btn_text": "#FFFFFF",
        "subtext": "#AEAEB2",
        "shadow": "rgba(0,0,0,0.35)"
    }
}

# FUNÇÃO DE CORES PERSONALIZADAS ATÉ A PARADA 250
def obter_estilo_parada(num_parada):
    try:
        n = int(num_parada)
    except Exception:
        return {"cor": "#00FF66", "bg": "rgba(0, 255, 102, 0.12)", "nome": "Faixa Padrão"}

    if 1 <= n <= 9:
        return {"cor": "#00FF66", "bg": "rgba(0, 255, 102, 0.15)", "nome": "Verde Limão (1-9)"}
    elif 10 <= n <= 19:
        return {"cor": "#007BFF", "bg": "rgba(0, 123, 255, 0.18)", "nome": "Azul Cobalto (10-19)"}
    elif 20 <= n <= 29:
        return {"cor": "#FF6B00", "bg": "rgba(255, 107, 0, 0.18)", "nome": "Laranja Elétrico (20-29)"}
    elif 30 <= n <= 39:
        return {"cor": "#A855F7", "bg": "rgba(168, 85, 247, 0.18)", "nome": "Roxo Neon (30-39)"}
    elif 40 <= n <= 49:
        return {"cor": "#FFD600", "bg": "rgba(255, 214, 0, 0.18)", "nome": "Amarelo Ouro (40-49)"}
    elif 50 <= n <= 59:
        return {"cor": "#FF003C", "bg": "rgba(255, 0, 60, 0.18)", "nome": "Vermelho Fogo (50-59)"}
    elif 60 <= n <= 69:
        return {"cor": "#00E5FF", "bg": "rgba(0, 229, 255, 0.18)", "nome": "Turquesa (60-69)"}
    elif 70 <= n <= 79:
        return {"cor": "#FF1493", "bg": "rgba(255, 20, 147, 0.18)", "nome": "Rosa Choque (70-79)"}
    elif 80 <= n <= 89:
        return {"cor": "#D97706", "bg": "rgba(217, 119, 6, 0.18)", "nome": "Cobre Metálico (80-89)"}
    elif 90 <= n <= 99:
        return {"cor": "#E2E8F0", "bg": "rgba(226, 232, 240, 0.18)", "nome": "Branco Gelo (90-99)"}
    elif 100 <= n <= 109:
        return {"cor": "#10B981", "bg": "rgba(16, 185, 129, 0.18)", "nome": "Verde Menta (100-109)"}
    elif 110 <= n <= 119:
        return {"cor": "#3B82F6", "bg": "rgba(59, 130, 246, 0.18)", "nome": "Azul Marinho Neon (110-119)"}
    elif 120 <= n <= 129:
        return {"cor": "#FB7185", "bg": "rgba(251, 113, 133, 0.18)", "nome": "Coral Intenso (120-129)"}
    elif 130 <= n <= 139:
        return {"cor": "#8B5CF6", "bg": "rgba(139, 92, 246, 0.18)", "nome": "Uva / Violeta (130-139)"}
    elif 140 <= n <= 149:
        return {"cor": "#FACC15", "bg": "rgba(250, 204, 21, 0.18)", "nome": "Amarelo Neon (140-149)"}
    elif 150 <= n <= 159:
        return {"cor": "#E11D48", "bg": "rgba(225, 29, 72, 0.18)", "nome": "Carmesim (150-159)"}
    elif 160 <= n <= 169:
        return {"cor": "#06B6D4", "bg": "rgba(6, 182, 212, 0.18)", "nome": "Azul Piscina (160-169)"}
    elif 170 <= n <= 179:
        return {"cor": "#C026D3", "bg": "rgba(192, 38, 211, 0.18)", "nome": "Magenta (170-179)"}
    elif 180 <= n <= 189:
        return {"cor": "#B45309", "bg": "rgba(180, 83, 9, 0.18)", "nome": "Caramelo (180-189)"}
    elif 190 <= n <= 199:
        return {"cor": "#94A3B8", "bg": "rgba(148, 163, 184, 0.18)", "nome": "Prata Metálico (190-199)"}
    elif 200 <= n <= 209:
        return {"cor": "#84CC16", "bg": "rgba(132, 204, 22, 0.18)", "nome": "Verde Oliva Vibrante (200-209)"}
    elif 210 <= n <= 219:
        return {"cor": "#2563EB", "bg": "rgba(37, 99, 255, 0.18)", "nome": "Azul Royal (210-219)"}
    elif 220 <= n <= 229:
        return {"cor": "#EA580C", "bg": "rgba(234, 88, 12, 0.18)", "nome": "Âmbar Queimado (220-229)"}
    elif 230 <= n <= 239:
        return {"cor": "#4F46E5", "bg": "rgba(79, 70, 229, 0.18)", "nome": "Índigo Puro (230-239)"}
    else:
        return {"cor": "#FFD700", "bg": "rgba(255, 215, 0, 0.20)", "nome": "Ouro Real (240-250+)"}

# MENU LATERAL
with st.sidebar:
    st.markdown(
        f'<h2 style="margin-bottom:2px; font-weight:900;"><img src="{IMG_MOTO}" style="width:30px; height:30px; vertical-align:-5px; margin-right:6px;"> {NOME_DO_APP}</h2>',
        unsafe_allow_html=True
    )
    st.caption("Sistema Inteligente de Triagem e Logística")
    st.write("---")
    
    tema_cor = st.selectbox(
        "🎨 Modo de Cor do App",
        ["Preto (Dark)", "Branco (Light)", "Cinza (Gray)"],
        index=0
    )
    
    usar_frontal = st.toggle("🤳 Câmera Frontal (Selfie)", value=False)
    
    usar_audio = st.toggle("🔊 Falar Número da Parada", value=True)
    tipo_voz = "Feminina / Normal"
    if usar_audio:
        tipo_voz = st.selectbox(
            "🎙️ Estilo da Voz", 
            [
                "Feminina / Normal", 
                "Masculina / Grave", 
                "Rápida / Ágil"
            ]
        )
        
    st.write("---")
    if st.button("🔄 Zerar Bipagens (Manter Rota)"):
        st.session_state.pacotes_bipados = set()
        if st.session_state.arquivo_salvo_atual:
            try:
                with open(st.session_state.arquivo_salvo_atual, "w", encoding="utf-8") as f:
                    json.dump([], f)
            except Exception:
                pass
        st.rerun()

t = estilos_temas[tema_cor]

# CSS DINÂMICO
css_style = f"""
<style>
.stApp {{ background-color: {t['bg_app']} !important; color: {t['text_app']} !important; }}
.block-container {{ padding-top: 3.8rem !important; padding-bottom: 2rem !important; }}

.hero-card {{
    background-color: {t['card_bg']};
    padding: 24px 18px;
    border-radius: 20px;
    border: 2px solid {t['border']};
    text-align: center;
    box-shadow: 0 8px 24px {t['shadow']};
    margin-top: 8px;
    margin-bottom: 14px;
}}
.welcome-logo {{ width: 85px; height: 85px; object-fit: contain; margin-top: 4px; margin-bottom: 12px; }}
.welcome-title {{ font-size: 2rem; font-weight: 900; color: {t['text_app']}; letter-spacing: 2px; text-transform: uppercase; }}
.welcome-subtitle {{ font-size: 0.72rem; color: {t['subtext']}; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; }}

.upload-card {{
    background-color: {t['card_bg']};
    padding: 20px;
    border-radius: 18px;
    border: 2px dashed {t['border']};
    text-align: center;
    margin-bottom: 14px;
}}
.upload-title {{ font-size: 1.1rem; font-weight: 800; color: {t['text_app']}; margin-bottom: 4px; }}
.upload-sub {{ font-size: 0.8rem; color: {t['subtext']}; margin-bottom: 6px; }}
.upload-arrow {{ font-size: 1.6rem; animation: bounce 1.5s infinite; }}

@keyframes bounce {{
    0%, 20%, 50%, 80%, 100% {{ transform: translateY(0); }}
    40% {{ transform: translateY(6px); }}
    60% {{ transform: translateY(3px); }}
}}

.stButton > button, div[data-testid='stFileUploader'] button, button[kind='secondary'], button[kind='primary'] {{
    background-color: {t['btn_bg']} !important;
    color: {t['btn_text']} !important;
    border: 2px solid {t['border']} !important;
    border-radius: 12px !important;
    font-weight: 900 !important;
    font-size: 0.95rem !important;
    box-shadow: 0 4px 12px {t['shadow']} !important;
    transition: all 0.2s ease-in-out !important;
}}

.stat-banner {{
    background-color: {t['card_bg']};
    border-radius: 16px;
    padding: 16px 8px;
    border: 2px solid {t['border']};
    display: flex;
    justify-content: space-around;
    text-align: center;
    margin-bottom: 16px;
    box-shadow: 0 6px 18px {t['shadow']};
}}
.stat-item {{ flex: 1; }}
.stat-value {{ font-size: 1.6rem; font-weight: 900; color: {t['text_app']}; line-height: 1.1; }}
.stat-label {{ font-size: 0.78rem; color: {t['subtext']}; font-weight: 900; margin-top: 4px; letter-spacing: 0.8px; text-transform: uppercase; }}

.custom-card-dinamico {{
    padding: 20px 16px;
    border-radius: 16px;
    margin-bottom: 15px;
    text-align: center;
    transition: all 0.3s ease;
}}
.stop-number-big {{ font-size: 4.8rem; font-weight: 900; line-height: 1; margin-bottom: 6px; }}
.tag-faixa {{ font-size: 0.85rem; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; }}

.pix-card {{
    background-color: {t['card_bg']};
    border: 1px solid {t['border']};
    border-radius: 14px;
    padding: 16px;
    text-align: center;
    margin-top: 20px;
    box-shadow: 0 4px 12px {t['shadow']};
}}
.pix-title {{ font-size: 0.95rem; font-weight: 900; color: {t['text_app']}; margin-bottom: 6px; letter-spacing: 0.5px; }}
.pix-desc {{ font-size: 0.82rem; color: {t['subtext']}; margin-bottom: 12px; line-height: 1.4; }}
.pix-key {{ font-size: 0.9rem; font-weight: 800; color: {t['text_app']}; background: rgba(127,127,127,0.18); padding: 6px 10px; border-radius: 8px; display: inline-block; }}

.camera-header {{ text-align: center; margin-top: 5px; margin-bottom: 8px; }}
.camera-title {{ font-size: 1.05rem; font-weight: 900; color: {t['text_app']}; text-transform: uppercase; }}
.camera-sub {{ font-size: 0.78rem; color: {t['subtext']}; }}

div[data-testid='stCustomComponentV1'] {{
    width: 100% !important;
    border-radius: 16px;
    border: 2px solid {t['border']};
    background-color: #000000;
    margin-bottom: 15px;
    overflow: hidden;
}}

div[data-testid='stExpander'] {{
    background-color: {t['card_bg']} !important;
    border: 2px solid {t['border']} !important;
    border-radius: 12px !important;
    color: {t['text_app']} !important;
}}
</style>
"""
st.markdown(css_style, unsafe_allow_html=True)

# SCRIPT: FORÇAR CÂMERA, FLASH E BEEP
modo_cam_js = "user" if usar_frontal else "environment"
js_camera = f"""
<script>
function playBeep() {{
    try {{
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var osc = ctx.createOscillator();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, ctx.currentTime);
        osc.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.1);
    }} catch(e) {{}}
}}

var trocandoSensor = false;

async function forcarCamera() {{
    if (trocandoSensor) return;
    
    var iframes = window.parent.document.querySelectorAll('iframe');
    for (var i = 0; i < iframes.length; i++) {{
        try {{
            var doc = iframes[i].contentDocument || iframes[i].contentWindow.document;
            if (doc && doc.querySelector('video')) {{
                var video = doc.querySelector('video');
                
                if (video && video.dataset.sensorAtivo !== "{modo_cam_js}") {{
                    trocandoSensor = true;
                    video.dataset.sensorAtivo = "{modo_cam_js}";
                    
                    if (video.srcObject) {{
                        video.srcObject.getTracks().forEach(function(t) {{ t.stop(); }});
                    }}
                    
                    try {{
                        var stream = await navigator.mediaDevices.getUserMedia({{
                            video: {{ facingMode: "{modo_cam_js}" }},
                            audio: false
                        }});
                        video.srcObject = stream;
                        video.setAttribute("playsinline", "true");
                        await video.play();
                    }} catch(err) {{
                        try {{
                            var fallback = await navigator.mediaDevices.getUserMedia({{ video: true, audio: false }});
                            video.srcObject = fallback;
                            video.setAttribute("playsinline", "true");
                            await video.play();
                        }} catch(e) {{}}
                    }} finally {{
                        trocandoSensor = false;
                    }}
                }}
                
                if ("{modo_cam_js}" === "environment" && video && video.srcObject) {{
                    if (!doc.getElementById('btn-flash')) {{
                        var btn = doc.createElement('button');
                        btn.id = 'btn-flash';
                        btn.innerHTML = '🔦 Flash';
                        btn.style.cssText = 'position:absolute; top:10px; right:10px; z-index:9999; background:{t['btn_bg']}; color:{t['btn_text']}; border:2px solid {t['border']}; padding:6px 14px; border-radius:18px; font-weight:900; font-size:12px; cursor:pointer; box-shadow:0 2px 8px {t['shadow']};';
                        btn.onclick = async function() {{
                            try {{
                                var track = video.srcObject.getVideoTracks()[0];
                                var capabilities = track.getCapabilities ? track.getCapabilities() : {{}};
                                if (capabilities.torch) {{
                                    var on = btn.innerHTML.includes('ON');
                                    await track.applyConstraints({{advanced: [{{torch: !on}}]}});
                                    btn.innerHTML = !on ? '⚡ Flash ON' : '🔦 Flash';
                                }}
                            }} catch(err) {{}}
                        }};
                        doc.body.appendChild(btn);
                    }}
                }} else if (doc) {{
                    var flashBtn = doc.getElementById('btn-flash');
                    if (flashBtn) flashBtn.remove();
                }}
            }}
        }} catch(e) {{
            trocandoSensor = false;
        }}
    }}
}}

setInterval(forcarCamera, 500);
</script>
"""
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
    f"""
    <div class="hero-card">
        <img src="{URL_DO_LOGO}" class="welcome-logo">
        <div class="welcome-title"><img src="{IMG_MOTO}" style="width:36px; height:36px; vertical-align:-6px; margin-right:8px;">{NOME_DO_APP}</div>
        <div class="welcome-subtitle">SISTEMA INTELIGENTE DE LOGÍSTICA</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="upload-card">
        <div class="upload-title">📄 CARREGAR ROTA DA ENTREGA</div>
        <div class="upload-sub">Envie o arquivo PDF da sua rota logo abaixo para liberar a câmera</div>
        <div class="upload-arrow">👇</div>
    </div>
    """,
    unsafe_allow_html=True
)

arquivo_pdf = st.file_uploader(
    "Selecione o PDF da Rota", 
    type=["pdf"], 
    key="pdf_main", 
    label_visibility="collapsed"
)

# CARD DO PIX
if not arquivo_pdf:
    st.markdown(
        f"""
        <div class="pix-card">
            <div class="pix-title">🚀 O app te ajudou no corre?</div>
            <div class="pix-desc">Fortaleça o projeto! Qualquer valor ajuda a manter o sistema rodando liso na rua. Tamo junto!</div>
            <div class="pix-key">🔑 Pix: {CHAVE_PIX}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

mapa_rotas = {}
stop_correspondente = {}
nome_exibicao = {}
todos_pacotes = set()

# PROCESSAMENTO DO PDF E RECUPERAÇÃO AUTOMÁTICA
if arquivo_pdf:
    pdf_bytes = arquivo_pdf.getvalue()
    hash_pdf = hashlib.md5(pdf_bytes).hexdigest()
    nome_salvamento = f"progresso_{hash_pdf}.json"
    st.session_state.arquivo_salvo_atual = nome_salvamento

    if os.path.exists(nome_salvamento) and not st.session_state.pacotes_bipados:
        try:
            with open(nome_salvamento, "r", encoding="utf-8") as f:
                st.session_state.pacotes_bipados = set(json.load(f))
        except Exception:
            pass

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
    stats_placeholder = st.empty()

    with st.expander("🤖 Ver pacotes no mesmo endereço / duplos"):
        encontrou_duplo = False
        for end, pacotes in mapa_rotas.items():
            if len(pacotes) > 1 and not end.startswith("pacote_isolado_"):
                encontrou_duplo = True
                numeros_stops = ", ".join([f"P{stop_correspondente.get(p)}" for p in pacotes])
                st.markdown(f"🚨 **{nome_exibicao.get(end, end).title()}**: `{len(pacotes)} pcts` ({numeros_stops})")
        if not encontrou_duplo:
            st.info("Nenhum endereço com múltiplos pacotes nesta rota.")

    st.markdown(
        f"""
        <div class="camera-header">
            <div class="camera-title">📸 BIPAR PACOTE ({'FRONTAL' if usar_frontal else 'TRASEIRA'})</div>
            <div class="camera-sub">Aponte o QR Code para a câmera</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    code = qrcode_scanner(key=f"scanner_{'front' if usar_frontal else 'back'}")
    
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
            
            if st.session_state.arquivo_salvo_atual:
                try:
                    with open(st.session_state.arquivo_salvo_atual, "w", encoding="utf-8") as f:
                        json.dump(list(st.session_state.pacotes_bipados), f)
                except Exception:
                    pass

            num_p = stop_correspondente.get(pacote_identificado, "?")
            estilo_p = obter_estilo_parada(num_p)
            
            end_match = ""
            lista_duplos = []
            for end, pacs in mapa_rotas.items():
                if pacote_identificado in pacs:
                    end_match = end
                    lista_duplos = pacs
                    break

            components.html("<script>playBeep();</script>", height=0)
            
            card_html = f"""
            <div class="custom-card-dinamico" style="background-color: {estilo_p['bg']}; border: 3px solid {estilo_p['cor']}; box-shadow: 0 0 20px {estilo_p['cor']}44;">
                <div class="tag-faixa" style="color: {estilo_p['cor']};">🎨 {estilo_p['nome']}</div>
                <div class="stop-number-big" style="color: {estilo_p['cor']}; text-shadow: 0 0 10px {estilo_p['cor']}66;">P{num_p}</div>
                <div style="font-weight: 900; font-size: 1rem; color: #FFFFFF; letter-spacing: 0.5px;">📍 Pacote: {pacote_identificado}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
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

    # ATUALIZAÇÃO DOS CONTADORES ACIMA DA CÂMERA
    bipados = len(st.session_state.pacotes_bipados)
    total_pacotes = len(todos_pacotes)
    faltam = max(0, total_pacotes - bipados)
    total_paradas = len(mapa_rotas)
    
    html_stats = f"""
    <div class="stat-banner">
        <div class="stat-item">
            <div class="stat-value">{bipados} / {total_pacotes}</div>
            <div class="stat-label">PACOTES</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{total_paradas}</div>
            <div class="stat-label">PARADAS REAIS</div>
        </div>
        <div class="stat-item">
            <div class="stat-value">{faltam}</div>
            <div class="stat-label">FALTAM</div>
        </div>
    </div>
    """
    stats_placeholder.markdown(html_stats, unsafe_allow_html=True)
