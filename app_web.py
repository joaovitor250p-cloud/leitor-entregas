import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração de App
st.set_page_config(page_title="RotaFácil", page_icon="⚡", layout="centered")

# CSS para estilo "App Profissional" (Dark Mode + Cards)
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .css-1r6slp0 { background-color: #1E1E1E; } /* Sidebar color */
    
    /* Cards */
    .custom-card {
        background-color: #1E1E1E;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        border-left: 5px solid #FF9500;
    }
    
    /* Botões */
    div.stButton > button {
        background-color: #FF9500;
        color: white;
        border-radius: 10px;
        font-weight: bold;
    }
    
    /* Ajuste da Câmera */
    iframe {
        width: 100% !important; height: 290px !important;
        border-radius: 15px !important;
        border: 2px solid #FF9500 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR - Configurações
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3062/3062634.png", width=80)
    st.title("RotaFácil")
    st.write("---")
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)
    st.write("Versão 1.0 - Profissional")

# TELA PRINCIPAL
st.title("📦 RotaFácil")
st.caption("Logística inteligente e rápida")

# Bloco de Upload
with st.container():
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    st.markdown('</div>', unsafe_allow_html=True)

if arquivo_pdf:
    with st.spinner('Processando rota...'):
        leitor = PdfReader(arquivo_pdf)
        texto_completo = ""
        for pagina in leitor.pages:
            texto_completo += pagina.extract_text() + "\n"

        todos_codigos = re.findall(r'BR[A-Za-z0-9]+', texto_completo)
        
        # Mapeamento
        paradas_dict = {}
        codigo_para_parada = {}
        
        linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
        parada_atual = 0

        for linha in linhas:
            match_parada = re.search(r'^(?:Parada\s*)?#?(\d{1,3})(?:\s*[\.\-\:]|\s*$)', linha, re.IGNORECASE)
            if match_parada:
                num = int(match_parada.group(1))
                if 1 <= num <= 500: parada_atual = num
            
            codigos_na_linha = re.findall(r'BR[A-Za-z0-9]+', linha)
            for cod in codigos_na_linha:
                cod_clean = cod.strip()
                if parada_atual == 0: parada_atual = 1
                if parada_atual not in paradas_dict: paradas_dict[parada_atual] = []
                if cod_clean not in paradas_dict[parada_atual]: paradas_dict[parada_atual].append(cod_clean)
                codigo_para_parada[cod_clean] = parada_atual

        if len(paradas_dict) <= 1 and len(todos_codigos) > 3:
            paradas_dict = {}
            codigo_para_parada = {}
            for pos, cod in enumerate(todos_codigos, start=1):
                codigo_para_parada[cod.strip()] = pos
                paradas_dict[pos] = [cod.strip()]

    st.success(f"✅ {len(todos_codigos)} pacotes carregados.")

    # UI DO LEITOR
    col1, col2 = st.columns([1, 1])
    
    st.subheader("📷 Scanner")
    codigo_camera = qrcode_scanner(key="scanner")
    
    st.subheader("⌨️ Entrada Manual")
    codigo_manual = st.text_input("Código do pacote:", placeholder="BR...")
    
    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        codigo_limpo = codigo_final.strip()
        if codigo_limpo in codigo_para_parada:
            num_parada = codigo_para_parada[codigo_limpo]
            pacotes = paradas_dict[num_parada]
            
            # Feedback Visual
            st.markdown(f'<div class="custom-card" style="border-left-color: #28a745;">', unsafe_allow_html=True)
            st.metric(label="PARADA", value=f"Nº {num_parada}")
            
            if usar_audio:
                texto_fala = f"Parada {num_parada}. {len(pacotes)} pacotes!" if len(pacotes) > 1 else f"Parada {num_parada}"
                components.html(f"""<script>
                    var msg = new SpeechSynthesisUtterance('{texto_fala}');
                    msg.lang = 'pt-BR'; window.speechSynthesis.speak(msg);
                </script>""", height=0)

            if len(pacotes) > 1:
                st.warning(f"⚠️ **Atenção:** {len(pacotes)} pacotes neste local!")
                for p in pacotes: st.write(f"• `{p}`")
            else:
                st.info("ℹ️ Apenas 1 pacote nesta parada.")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("❌ Código não encontrado!")
