import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
st.set_page_config(page_title="RotaFácil", page_icon="⚡", layout="centered")

# Estilo Visual Profissional + Câmera e Mira Ampliadas
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    
    .custom-card {
        background-color: #1E1E1E;
        padding: 18px;
        border-radius: 14px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.4);
        margin-bottom: 15px;
        border-left: 5px solid #FF9500;
    }
    
    /* Expande a janela e a mira de leitura do QR Code */
    iframe {
        width: 100% !important;
        height: 380px !important;
        border-radius: 16px !important;
        border: 3px solid #FF9500 !important;
        background-color: transparent !important;
        transform: scale(1.05);
    }
    
    div[data-testid="stCustomComponentV1"] {
        width: 100% !important;
        display: flex;
        justify-content: center;
        overflow: hidden;
        border-radius: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# SIDEBAR - Configurações
with st.sidebar:
    st.title("⚡ RotaFácil")
    st.write("---")
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)
    st.caption("Versão 2.2 - Leitor Ampliado")

# TELA PRINCIPAL
st.title("📦 RotaFácil")
st.caption("Logística inteligente e rápida")

# Upload do PDF
with st.container():
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota (Circuit)", type=["pdf"])
    st.markdown('</div>', unsafe_allow_html=True)

if arquivo_pdf:
    with st.spinner('Mapeando pacotes e endereços...'):
        leitor = PdfReader(arquivo_pdf)
        texto_completo = ""
        for pagina in leitor.pages:
            texto_completo += pagina.extract_text() + "\n"

        todos_codigos = re.findall(r'BR[A-Za-z0-9]+', texto_completo)
        
        # AGRUPAMENTO SEQUENCIAL INTELIGENTE POR PARADA
        paradas_dict = {}
        codigo_para_parada = {}
        
        linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
        
        current_stop = 1
        expected_stop = 1
        paradas_dict[1] = []

        for linha in linhas:
            match_next = re.search(rf'(?:^|\b|Parada\s*|Stop\s*|#){expected_stop}(?:[\.\-\:\/\s]|$)', linha, re.IGNORECASE)
            
            if match_next:
                current_stop = expected_stop
                if current_stop not in paradas_dict:
                    paradas_dict[current_stop] = []
                expected_stop += 1

            codigos_na_linha = re.findall(r'BR[A-Za-z0-9]+', linha)
            for cod in codigos_na_linha:
                cod_clean = cod.strip()
                if cod_clean not in paradas_dict[current_stop]:
                    paradas_dict[current_stop].append(cod_clean)
                codigo_para_parada[cod_clean] = current_stop

        paradas_dict = {k: v for k, v in paradas_dict.items() if v}

    st.success(f"✅ {len(todos_codigos)} pacotes mapeados em {len(paradas_dict)} paradas.")

    st.markdown("---")

    # SCANNER E ENTRADA
    st.subheader("📷 Leitor de Câmera")
    codigo_camera = qrcode_scanner(key="scanner")
    
    st.subheader("⌨️ Entrada Manual")
    codigo_manual = st.text_input("Digite ou bipe o código:", placeholder="Ex: BR264290...")
    
    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        codigo_limpo = codigo_final.strip()
        
        if codigo_limpo in codigo_para_parada:
            num_parada = codigo_para_parada[codigo_limpo]
            pacotes_da_parada = paradas_dict[num_parada]
            qtd_pacotes = len(pacotes_da_parada)

            st.markdown("---")
            st.markdown('<div class="custom-card" style="border-left-color: #28a745;">', unsafe_allow_html=True)
            st.metric(label="PARADA / ENDEREÇO", value=f"Nº {num_parada}")

            # Feedback por Voz
            if usar_audio:
                if qtd_pacotes > 1:
                    texto_fala = f"Parada número {num_parada}. Atenção, {qtd_pacotes} pacotes para este endereço!"
                else:
                    texto_fala = f"Parada número {num_parada}"

                components.html(
                    f"""
                    <script>
                        window.speechSynthesis.cancel();
                        var msg = new SpeechSynthesisUtterance('{texto_fala}');
                        msg.lang = 'pt-BR';
                        msg.rate = 1.1;
                        window.speechSynthesis.speak(msg);
                    </script>
                    """,
                    height=0,
                )

            # Alerta de Múltiplos Pacotes
            if qtd_pacotes > 1:
                st.warning(f"⚠️ **ATENÇÃO! Há {qtd_pacotes} PACOTES para este mesmo endereço!**")
                st.write("**Lista dos pacotes desta parada:**")
                for idx, pkg in enumerate(pacotes_da_parada, start=1):
                    if pkg == codigo_limpo:
                        st.markdown(f"* **{idx}. `{pkg}` 👈 (Este que você bipou)**")
                    else:
                        st.markdown(f"* {idx}. `{pkg}`")
            else:
                st.info("ℹ️ Apenas **1 pacote** nesta parada.")
                
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("❌ Código NÃO encontrado nesta rota!")
