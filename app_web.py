import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração do App
st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

# Inicializa memória de pacotes bipados
if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()

# Estilo Visual Dark / App Pro com Parada Gigante
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 1rem !important;
    }

    .stat-banner {
        background-color: #1E1E1E;
        border-radius: 12px;
        padding: 12px 15px;
        border: 1px solid #333333;
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin-bottom: 15px;
    }
    .stat-box { text-align: center; }
    .stat-label { font-size: 0.72rem; color: #888888; font-weight: bold; letter-spacing: 0.5px; }
    .stat-value { font-size: 1.3rem; font-weight: bold; color: #28a745; }
    .stat-value-orange { font-size: 1.3rem; font-weight: bold; color: #FF9500; }

    .custom-card { 
        background-color: #1E1E1E; 
        padding: 18px; 
        border-radius: 14px; 
        border-left: 6px solid #28a745; 
        margin-top: 10px; 
        margin-bottom: 15px; 
    }

    /* Número da Parada Gigante */
    .stop-number-title {
        font-size: 0.8rem;
        color: #AAAAAA;
        font-weight: bold;
        letter-spacing: 1px;
    }
    .stop-number-big {
        font-size: 3.8rem !important;
        font-weight: 900 !important;
        color: #FF9500 !important;
        line-height: 1 !important;
        margin-top: 2px !important;
        margin-bottom: 12px !important;
    }
    
    /* Container da Câmera */
    div[data-testid="stCustomComponentV1"] {
        width: 100% !important;
        height: 380px !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        border-radius: 16px !important;
        border: 3px solid #FF9500 !important;
        background-color: #000000 !important;
        margin-bottom: 10px !important;
        overflow: hidden !important;
        position: relative !important;
    }
    
    iframe { 
        width: 100% !important; 
        height: 380px !important; 
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# SCRIPT QUE MANTÉM APENAS O QUADRADO ESCURO E ESCONDE AS LINHAS BRANCAS
components.html("""
    <script>
    function aplicarMelhoriasCamera() {
        try {
            var iframes = window.parent.document.querySelectorAll('iframe');
            iframes.forEach(function(frame) {
                try {
                    var doc = frame.contentDocument || frame.contentWindow.document;
                    if (doc && doc.querySelector('video')) {
                        var styleId = "mira-limpa-style";
                        if (!doc.getElementById(styleId)) {
                            var css = doc.createElement('style');
                            css.id = styleId;
                            css.innerHTML = `
                                #qr-shaded-region {
                                    height: 250px !important;
                                    width: 250px !important;
                                    max-width: 85% !important;
                                    max-height: 85% !important;
                                    margin: auto !important;
                                    box-sizing: border-box !important;
                                    border: none !important;
                                }
                                #qr-shaded-region * {
                                    display: none !important;
                                    border: none !important;
                                }
                                video { object-fit: cover !important; }
                            `;
                            doc.head.appendChild(css);
                        }

                        if (!doc.getElementById('btn-flash-custom')) {
                            var btn = doc.createElement('button');
                            btn.id = 'btn-flash-custom';
                            btn.innerHTML = '🔦 Flash';
                            btn.style.cssText = `
                                position: absolute;
                                top: 12px;
                                right: 12px;
                                z-index: 999999;
                                background: rgba(0, 0, 0, 0.75);
                                color: #FFFFFF;
                                border: 1px solid #FF9500;
                                padding: 8px 14px;
                                border-radius: 20px;
                                font-size: 0.85rem;
                                font-weight: bold;
                                cursor: pointer;
                                box-shadow: 0 2px 6px rgba(0,0,0,0.5);
                            `;

                            var flashAtivo = false;
                            btn.onclick = async function() {
                                var video = doc.querySelector('video');
                                if (video && video.srcObject) {
                                    var track = video.srcObject.getVideoTracks()[0];
                                    if (track) {
                                        flashAtivo = !flashAtivo;
                                        try {
                                            await track.applyConstraints({
                                                advanced: [{ torch: flashAtivo }]
                                            });
                                            btn.innerHTML = flashAtivo ? '⚡ Flash ON' : '🔦 Flash';
                                            btn.style.background = flashAtivo ? '#FF9500' : 'rgba(0,0,0,0.75)';
                                            btn.style.color = flashAtivo ? '#000000' : '#FFFFFF';
                                        } catch (err) {
                                            alert("O flash não é suportado nesta câmera ou navegador.");
                                        }
                                    }
                                }
                            };
                            doc.body.appendChild(btn);
                        }
                    }
                } catch(e) {}
            });
        } catch(e) {}
    }
    setInterval(aplicarMelhoriasCamera, 300);
    </script>
""", height=0)

# MENU LATERAL
with st.sidebar:
    st.title("📦 PACOTE É MATO")
    st.write("---")
    arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)
    st.write("---")
    if st.button("🔄 Zerar Bipados da Rota"):
        st.session_state.pacotes_bipados = set()
        st.rerun()

def extrair_chave_endereco(texto_linha):
    txt = texto_linha.lower()
    txt = re.sub(r'br[a-za-z0-9]+', '', txt)
    txt = re.sub(r'^\s*#?\d{1,3}\b[\.\-\:]?', '', txt)
    txt = re.sub(r'\b(ap|apto|apartamento|bl|bloco|casa|fundos|fd|sala|sl|sobrado|lote|qd|quadra|kitnet|andar)\b.*$', '', txt)
    txt = re.sub(r'\b(rua|r|av|avenida|al|alameda|estrada|estr|est|tv|travessa|rod|rodovia|praça|prc)\b\.?', '', txt)
    match = re.search(r'([a-z0-9áàâãéèêíïóôõöúçñ\s]+?\d+)', txt)
    if match:
        chave = " ".join(match.group(1).strip().split())
        if len(chave) > 3: return chave
    txt_limpo = re.sub(r'[^\w\s]', '', txt)
    return " ".join(txt_limpo.split())

mapa_rotas = {}
stop_correspondente = {}
nome_exibicao = {}
todos_os_pacotes = set()

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto_completo = "".join([p.extract_text() + "\n" for p in leitor.pages])
    linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
    stop_atual = 1
    
    for linha in linhas:
        match_stop = re.search(r'^\s*(\d{1,3})\b', linha)
        if match_stop: stop_atual = int(match_stop.group(1))
        
        codigos = re.findall(r'BR[A-Za-z0-9]+', linha)
        if codigos:
            chave_end = extrair_chave_endereco(linha)
            if not chave_end or len(chave_end) < 3: chave_end = f"parada_{stop_atual}"
            
            if chave_end not in mapa_rotas:
                mapa_rotas[chave_end] = []
                nome_exibicao[chave_end] = re.sub(r'BR[A-Za-z0-9]+', '', linha).strip()
            
            for c in codigos:
                todos_os_pacotes.add(c)
                if c not in mapa_rotas[chave_end]:
                    mapa_rotas[chave_end].append(c)
                    stop_correspondente[c] = stop_atual

if not arquivo_pdf:
    st.info("👈 **Abra o menu lateral (seta no topo) para carregar o PDF da rota.**")

# 1. PAINEL DE PROGRESSO (SEM A BARRA VERDE)
if arquivo_pdf and len(todos_os_pacotes) > 0:
    total_pacotes = len(todos_os_pacotes)
    qtd_bipados = len(st.session_state.pacotes_bipados)
    qtd_faltam = total_pacotes - qtd_bipados
    
    st.markdown(f"""
        <div class="stat-banner">
            <div class="stat-box">
                <div class="stat-label">BIPADOS / TOTAL</div>
                <div class="stat-value">{qtd_bipados} / {total_pacotes}</div>
            </div>
            <div style="border-left: 1px solid #333; height: 30px;"></div>
            <div class="stat-box">
                <div class="stat-label">FALTAM</div>
                <div class="stat-value-orange">{qtd_faltam} pcts</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. ANÁLISE DE DUPLOS/TRIPLOS
    with st.expander("🤖 Ver Pacotes Duplos e Triplos da Rota", expanded=False):
        multiplos_encontrados = 0
        for chave, pacotes in mapa_rotas.items():
            if len(pacotes) > 1:
                multiplos_encontrados += 1
                end_nome = nome_exibicao.get(chave, chave).title()
                st.markdown(f"🚨 **{end_nome}**: `{len(pacotes)} PACOTES`")
                for p in pacotes:
                    st.caption(f"└─ `{p}` (Parada aprox: P{stop_correspondente.get(p, '?')})")
        if multiplos_encontrados == 0:
            st.info("Nenhum endereço com múltiplos pacotes identificado.")

# 3. CÂMERA
codigo_camera = qrcode_scanner(key="scanner")

# 4. ENTRADA MANUAL
codigo_manual = st.text_input("", placeholder="Ou digite o código BR aqui...", label_visibility="collapsed")
codigo_final = codigo_camera or codigo_manual

# 5. CARTÃO DE RESULTADO COM PARADA DESTAQUE
if codigo_final and arquivo_pdf:
    cod = codigo_final.strip()
    achou = False
    
    for chave, lista_pacotes in mapa_rotas.items():
        if cod in lista_pacotes:
            num_parada = stop_correspondente.get(cod, "?")
            end_formatado = nome_exibicao.get(chave, chave).title()
            qtd = len(lista_pacotes)
            
            ja_bipado_antes = cod in st.session_state.pacotes_bipados
            st.session_state.pacotes_bipados.add(cod)
            
            st.markdown(f"""
                <div class="custom-card">
                    <div class="stop-number-title">PARADA Nº</div>
                    <div class="stop-number-big">P{num_parada}</div>
                    <div>📍 <b>Endereço:</b> {end_formatado}</div>
                </div>
            """, unsafe_allow_html=True)
            
            if ja_bipado_antes:
                st.warning(f"⚠️ **Este pacote `{cod}` JÁ HAVIA SIDO BIPADO!**")
            else:
                st.success(f"✅ **Pacote Bipado:** `{cod}`")
            
            if qtd > 1:
                st.warning(f"⚠️ **ATENÇÃO: ESTA PARADA TEM {qtd} PACOTES NO TOTAL!**")
                st.markdown("👇 **PEGUE TAMBÉM ESTE(S) OUTRO(S) PACOTE(S):**")
                for idx, p in enumerate(lista_pacotes, 1):
                    if p != cod:
                        status_p = "✅ (Já Bipado)" if p in st.session_state.pacotes_bipados else "⏳ (Pendente)"
                        st.markdown(f"* 📦 `{p}` {status_p}")
            else:
                st.info("ℹ️ Apenas 1 pacote nesta parada.")
            
            if usar_audio and not ja_bipado_antes:
                texto_fala = f"Parada {num_parada}. Atenção, {qtd} pacotes!" if qtd > 1 else f"Parada {num_parada}"
                components.html(f"""<script>
                    window.speechSynthesis.cancel();
                    var msg = new SpeechSynthesisUtterance('{texto_fala}');
                    msg.lang = 'pt-BR'; window.speechSynthesis.speak(msg);
                </script>""", height=0)
            
            achou = True
            break
    
    if not achou:
        st.error("❌ Código não encontrado nesta rota!")
