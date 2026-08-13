import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração do App
st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

# Estilo Visual Dark / App Pro + CÂMERA SUPER AMPLIADA
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .custom-card { 
        background-color: #1E1E1E; 
        padding: 18px; 
        border-radius: 14px; 
        border-left: 5px solid #FF9500; 
        margin-bottom: 15px; 
    }
    
    /* Câmera com altura de 480px e Zoom de leitura ampliado */
    iframe { 
        width: 100% !important; 
        height: 480px !important; 
        border-radius: 18px !important; 
        border: 3px solid #FF9500 !important; 
        background-color: transparent !important; 
        transform: scale(1.15);
    }
    
    div[data-testid="stCustomComponentV1"] {
        width: 100% !important;
        display: flex;
        justify-content: center;
        overflow: hidden;
        border-radius: 18px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚡ PACOTE É MATO")
    st.write("---")
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)
    st.caption("IA de Mapeamento Ultrassensível")

st.title("📦 PACOTE É MATO")
st.caption("Logística inteligente e sem falhas")

arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota (Circuit)", type=["pdf"])

def extrair_chave_endereco(texto_linha):
    txt = texto_linha.lower()
    
    # 1. Limpa códigos de rastreio e marcas
    txt = re.sub(r'br[a-za-z0-9]+', '', txt)
    
    # 2. Remove número da parada no início (ex: "1.", "1 -", "#1")
    txt = re.sub(r'^\s*#?\d{1,3}\b[\.\-\:]?', '', txt)
    
    # 3. Remove complementos (AP, APTO, CASA, BLOCO, SOBRADO, FUNDOS, etc.)
    txt = re.sub(r'\b(ap|apto|apartamento|bl|bloco|casa|fundos|fd|sala|sl|sobrado|lote|qd|quadra|kitnet|andar)\b.*$', '', txt)
    
    # 4. Remove prefixos de logradouro comuns para padronizar
    txt = re.sub(r'\b(rua|r|av|avenida|al|alameda|estrada|estr|est|tv|travessa|rod|rodovia|praça|prc)\b\.?', '', txt)
    
    # 5. Captura a combinação do Nome + Número principal (Ex: "genival 1790")
    match = re.search(r'([a-z0-9áàâãéèêíïóôõöúçñ\s]+?\d+)', txt)
    if match:
        chave = " ".join(match.group(1).strip().split())
        if len(chave) > 3:
            return chave
            
    # Fallback se não tiver número
    txt_limpo = re.sub(r'[^\w\s]', '', txt)
    return " ".join(txt_limpo.split())

if arquivo_pdf:
    with st.spinner('Mapeando pacotes duplos e triplos...'):
        leitor = PdfReader(arquivo_pdf)
        texto_completo = ""
        for p in leitor.pages: 
            texto_completo += p.extract_text() + "\n"

        mapa_rotas = {}           # { "genival 1790": ["BR1", "BR2"] }
        stop_correspondente = {}  # { "BR1": 1 }
        nome_exibicao = {}        # { "genival 1790": "Rua Genival 1790" }
        
        linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
        stop_atual = 1
        
        for linha in linhas:
            # Captura número da parada
            match_stop = re.search(r'^\s*(\d{1,3})\b', linha)
            if match_stop: 
                stop_atual = int(match_stop.group(1))
            
            codigos = re.findall(r'BR[A-Za-z0-9]+', linha)
            
            if codigos:
                chave_end = extrair_chave_endereco(linha)
                
                if not chave_end or len(chave_end) < 3:
                    chave_end = f"parada_{stop_atual}"
                
                if chave_end not in mapa_rotas:
                    mapa_rotas[chave_end] = []
                    # Guarda a linha original limpa para exibir bonito na tela
                    nome_exibicao[chave_end] = re.sub(r'BR[A-Za-z0-9]+', '', linha).strip()
                
                for c in codigos:
                    if c not in mapa_rotas[chave_end]:
                        mapa_rotas[chave_end].append(c)
                        stop_correspondente[c] = stop_atual

    st.success("✅ Rota processada com sucesso!")

    # --- ABA DE ANÁLISE PROATIVA DE MÚLTIPLOS PACOTES ---
    with st.expander("🤖 Análise Inteligente de Endereços (Pacotes Duplos/Triplos)", expanded=True):
        multiplos_encontrados = 0
        for chave, pacotes in mapa_rotas.items():
            if len(pacotes) > 1:
                multiplos_encontrados += 1
                endereco_mostra = nome_exibicao.get(chave, chave).title()
                st.markdown(f"🚨 **{endereco_mostra}**: `{len(pacotes)} PACOTES`")
                for p in pacotes:
                    st.caption(f"└─ Pacote: `{p}` (Parada aprox: #{stop_correspondente.get(p, '?')})")
        
        if multiplos_encontrados == 0:
            st.info("Nenhum endereço duplicado foi identificado nesta rota.")

    st.markdown("---")
    st.subheader("📷 Scanner")
    codigo_camera = qrcode_scanner(key="scanner")
    codigo_manual = st.text_input("Ou digite o código:", placeholder="Ex: BR...")
    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        cod = codigo_final.strip()
        achou = False
        
        for chave, lista_pacotes in mapa_rotas.items():
            if cod in lista_pacotes:
                num_parada = stop_correspondente.get(cod, "?")
                end_formatado = nome_exibicao.get(chave, chave).title()
                qtd = len(lista_pacotes)
                
                st.markdown('<div class="custom-card" style="border-left-color: #28a745;">', unsafe_allow_html=True)
                st.metric("PARADA Nº", num_parada)
                st.write(f"📍 **Endereço:** {end_formatado}")
                
                if qtd > 1:
                    st.warning(f"⚠️ **ATENÇÃO: HÁ {qtd} PACOTES PARA ESTE MESMO ENDEREÇO!**")
                    for idx, p in enumerate(lista_pacotes, 1):
                        if p == cod:
                            st.markdown(f"* **{idx}. `{p}` 👈 (Este que você bipou)**")
                        else:
                            st.markdown(f"* {idx}. `{p}`")
                else:
                    st.info("ℹ️ Apenas 1 pacote neste endereço.")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Áudio em voz alta
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
        
