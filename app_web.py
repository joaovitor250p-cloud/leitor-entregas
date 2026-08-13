import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração do App
st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

# Estilo Visual Dark / App Pro
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
    iframe { 
        width: 100% !important; 
        height: 380px !important; 
        border-radius: 16px !important; 
        border: 3px solid #FF9500 !important; 
        background-color: transparent !important; 
    }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚡ PACOTE É MATO")
    st.write("---")
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)
    st.caption("Versão Pro - Agrupamento Ativo")

st.title("📦 PACOTE É MATO")
st.caption("Logística inteligente")

arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota (Circuit)", type=["pdf"])

def extrair_endereco_base(texto_linha):
    # Remove códigos BR
    texto_limpo = re.sub(r'BR[A-Za-z0-9]+', '', texto_linha)
    # Remove complementos comuns (AP, APTO, BLOCO, CASA, FUNDOS, etc.)
    texto_limpo = re.sub(r'\b(ap|apto|apartamento|bl|bloco|casa|fundos|fd|sala|sobrado)\b.*$', '', texto_limpo, flags=re.IGNORECASE)
    # Remove caracteres especiais desnecessários
    texto_limpo = re.sub(r'[^\w\s]', ' ', texto_limpo)
    # Limpa espaços duplos e deixa em minúsculo
    return " ".join(texto_limpo.lower().split())

if arquivo_pdf:
    with st.spinner('Mapeando endereços e pacotes...'):
        leitor = PdfReader(arquivo_pdf)
        texto = ""
        for p in leitor.pages: 
            texto += p.extract_text() + "\n"

        mapa_rotas = {}           # { "rua genival 1790": ["BR1", "BR2"] }
        stop_correspondente = {}  # { "BR1": 1 }
        
        linhas = [l.strip() for l in texto.split('\n') if l.strip()]
        stop_atual = 1
        
        for linha in linhas:
            # Detecta número de parada no início da linha
            match_stop = re.match(r'^\s*(\d{1,3})\b', linha)
            if match_stop: 
                stop_atual = int(match_stop.group(1))
            
            codigos = re.findall(r'BR[A-Za-z0-9]+', linha)
            
            if codigos:
                end_base = extrair_endereco_base(linha)
                
                # Fallback se a linha for só o código
                if len(end_base) < 3:
                    end_base = f"parada_{stop_atual}"
                
                if end_base not in mapa_rotas:
                    mapa_rotas[end_base] = []
                
                for c in codigos:
                    if c not in mapa_rotas[end_base]:
                        mapa_rotas[end_base].append(c)
                        stop_correspondente[c] = stop_atual

    st.success("✅ Rota mapeada por endereços!")

    st.subheader("📷 Scanner")
    codigo_camera = qrcode_scanner(key="scanner")
    codigo_manual = st.text_input("Ou digite o código:", placeholder="Ex: BR...")
    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        cod = codigo_final.strip()
        achou = False
        
        for end, lista_pacotes in mapa_rotas.items():
            if cod in lista_pacotes:
                num_parada = stop_correspondente.get(cod, "?")
                
                st.markdown('<div class="custom-card" style="border-left-color: #28a745;">', unsafe_allow_html=True)
                st.metric("PARADA Nº", num_parada)
                
                if not end.startswith("parada_"):
                    st.write(f"📍 **Endereço Base:** {end.title()}")
                
                # Alerta para múltiplos pacotes no mesmo endereço
                qtd = len(lista_pacotes)
                if qtd > 1:
                    st.warning(f"⚠️ **ATENÇÃO: {qtd} pacotes para este mesmo endereço!**")
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
                    texto_fala = f"Parada {num_parada}. {qtd} pacotes no endereço." if qtd > 1 else f"Parada {num_parada}"
                    components.html(f"""<script>
                        window.speechSynthesis.cancel();
                        var msg = new SpeechSynthesisUtterance('{texto_fala}');
                        msg.lang = 'pt-BR'; window.speechSynthesis.speak(msg);
                    </script>""", height=0)
                
                achou = True
                break
        
        if not achou:
            st.error("❌ Código não encontrado nesta rota!")
