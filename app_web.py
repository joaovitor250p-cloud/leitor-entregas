import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração do App
st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

# Estilo Visual Minimalista (Apenas Câmera em Destaque)
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    
    /* Remove padding do topo para subir a câmera */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    .custom-card { 
        background-color: #1E1E1E; 
        padding: 18px; 
        border-radius: 14px; 
        border-left: 5px solid #28a745; 
        margin-top: 10px; 
        margin-bottom: 15px; 
    }
    
    /* Container da Câmera Gigante */
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
    }
    
    iframe { 
        width: 100% !important; 
        height: 380px !important; 
        border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# SCRIPT QUE FORÇA A MIRA INTERNA QUADRADA (1:1)
components.html("""
    <script>
    function forcarMiraQuadrada() {
        try {
            var iframes = window.parent.document.querySelectorAll('iframe');
            iframes.forEach(function(frame) {
                try {
                    var doc = frame.contentDocument || frame.contentWindow.document;
                    if (doc) {
                        var styleId = "mira-quadrada-style";
                        if (!doc.getElementById(styleId)) {
                            var css = doc.createElement('style');
                            css.id = styleId;
                            css.innerHTML = `
                                #qr-shaded-region, div[id*="qr-shaded"], div[style*="border"] {
                                    height: 250px !important;
                                    width: 250px !important;
                                    max-width: 85% !important;
                                    max-height: 85% !important;
                                    margin: auto !important;
                                    box-sizing: border-box !important;
                                }
                                video { object-fit: cover !important; }
                            `;
                            doc.head.appendChild(css);
                        }
                    }
                } catch(e) {}
            });
        } catch(e) {}
    }
    setInterval(forcarMiraQuadrada, 300);
    </script>
""", height=0)

# MENU LATERAL (GUARDOU O PDF E AS CONFIGURAÇÕES)
with st.sidebar:
    st.title("📦 PACOTE É MATO")
    st.write("---")
    arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)
    st.caption("Modo Câmera Direta")

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
                if c not in mapa_rotas[chave_end]:
                    mapa_rotas[chave_end].append(c)
                    stop_correspondente[c] = stop_atual

    # Análise de pacotes múltiplos guardada na lateral
    with st.sidebar:
        st.write("---")
        with st.expander("🤖 Ver Pacotes Duplos/Triplos"):
            multiplos = 0
            for chave, pacotes in mapa_rotas.items():
                if len(pacotes) > 1:
                    multiplos += 1
                    st.markdown(f"🚨 **{nome_exibicao.get(chave, chave).title()}**: `{len(pacotes)} pcts`")
            if multiplos == 0: st.info("Sem pacotes duplos.")

# TELA PRINCIPAL (SÓ CÂMERA E RESULTADOS)
if not arquivo_pdf:
    st.info("👈 **Abra o menu lateral (seta no canto superior esquerdo) para enviar o PDF da rota.**")

# 1. Câmera no topo
codigo_camera = qrcode_scanner(key="scanner")

# 2. Entrada Manual Discreta
codigo_manual = st.text_input("", placeholder="Ou digite o código BR aqui...", label_visibility="collapsed")
codigo_final = codigo_camera or codigo_manual

# 3. Cartão de Resultado (Aparece logo abaixo ao bipar)
if codigo_final and arquivo_pdf:
    cod = codigo_final.strip()
    achou = False
    
    for chave, lista_pacotes in mapa_rotas.items():
        if cod in lista_pacotes:
            num_parada = stop_correspondente.get(cod, "?")
            end_formatado = nome_exibicao.get(chave, chave).title()
            qtd = len(lista_pacotes)
            
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            st.metric("PARADA Nº", num_parada)
            st.write(f"📍 **Endereço:** {end_formatado}")
            
            if qtd > 1:
                st.warning(f"⚠️ **ATENÇÃO: HÁ {qtd} PACOTES PARA ESTE MESMO ENDEREÇO!**")
                for idx, p in enumerate(lista_pacotes, 1):
                    if p == cod:
                        st.markdown(f"* **{idx}. `{p}` 👈 (Bipado)**")
                    else:
                        st.markdown(f"* {idx}. `{p}`")
            else:
                st.info("ℹ️ Apenas 1 pacote neste endereço.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if usar_audio:
                texto_fala = f"Parada {num_parada}. Atenção, {qtd} pacotes para este endereço!" if qtd > 1 else f"Parada {num_parada}"
                components.html(f"""<script>
                    window.speechSynthesis.cancel();
                    var msg = new SpeechSynthesisUtterance('{texto_fala}');
                    msg.lang = 'pt-BR'; window.speechSynthesis.speak(msg);
                </script>""", height=0)
            
            achou = True
            break
    
    if not achou:
        st.error("❌ Código não encontrado nesta rota!")
