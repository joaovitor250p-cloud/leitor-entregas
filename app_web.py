import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="Leitor de Rotas", page_icon="📦", layout="centered")

# CSS para aumentar o leitor da Câmera na tela do celular
st.markdown(
    """
    <style>
    iframe {
        width: 100% !important;
        min-height: 380px !important;
        border-radius: 16px !important;
        border: 2px solid #FF4B4B !important;
    }
    div[data-testid="stCustomComponentV1"] {
        width: 100% !important;
        display: flex;
        justify-content: center;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📦 Leitor de Entregas")
st.write("Envie o PDF da rota e busque o pacote rapidamente!")

# Botão para Ligar/Desligar o Áudio
usar_audio = st.toggle("🔊 Falar número do pacote em voz alta", value=True)

arquivo_pdf = st.file_uploader("Arraste ou selecione o PDF do Circuit aqui:", type=["pdf"])

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto_completo = ""
    for pagina in leitor.pages:
        texto_completo += pagina.extract_text() + "\n"

    # Mapeamento de Paradas e Pacotes por Endereço
    linhas = [l.strip() for l in texto_completo.split('\n') if l.strip()]
    paradas_dict = {}  # { num_parada: [codigo1, codigo2, ...] }
    codigo_para_parada = {}  # { codigo: num_parada }
    
    parada_atual = 0
    todos_codigos = re.findall(r'BR[A-Za-z0-9]+', texto_completo)

    for linha in linhas:
        if re.match(r'^\d{1,3}$', linha):
            parada_atual = int(linha)
            if parada_atual not in paradas_dict:
                paradas_dict[parada_atual] = []
        else:
            codigos_na_linha = re.findall(r'BR[A-Za-z0-9]+', linha)
            for cod in codigos_na_linha:
                cod_clean = cod.strip()
                if parada_atual == 0:
                    parada_atual = 1
                if parada_atual not in paradas_dict:
                    paradas_dict[parada_atual] = []
                if cod_clean not in paradas_dict[parada_atual]:
                    paradas_dict[parada_atual].append(cod_clean)
                codigo_para_parada[cod_clean] = parada_atual

    if not codigo_para_parada:
        for pos, cod in enumerate(todos_codigos, start=1):
            cod_clean = cod.strip()
            paradas_dict[pos] = [cod_clean]
            codigo_para_parada[cod_clean] = pos

    st.success(f"✅ Rota carregada! {len(todos_codigos)} pacotes em {len(paradas_dict)} paradas.")

    st.markdown("---")

    # Opção da Câmera / QR Code
    st.subheader("📷 Leitor de Câmera")
    codigo_camera = qrcode_scanner(key="scanner")

    # Opção Manual
    st.subheader("⌨️ Digitar / Bipar Manualmente")
    codigo_manual = st.text_input("Digite ou bipe o código do pacote abaixo:", placeholder="Ex: BR264290834579T")

    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        codigo_limpo = codigo_final.strip()
        
        if codigo_limpo in codigo_para_parada:
            num_parada = codigo_para_parada[codigo_limpo]
            pacotes_da_parada = paradas_dict[num_parada]
            qtd_pacotes = len(pacotes_da_parada)

            st.markdown("---")
            st.success(f"### 🎯 PACOTE NÚMERO / PARADA: {num_parada}")

            # RECURSO DE ÁUDIO / FALA NO CELULAR
            if usar_audio:
                if qtd_pacotes > 1:
                    texto_fala = f"Pacote número {num_parada}. Atenção, {qtd_pacotes} pacotes!"
                else:
                    texto_fala = f"Pacote número {num_parada}"

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

            # ALERTA DE MÚLTIPLOS PACOTES NA TELA
            if qtd_pacotes > 1:
                st.warning(f"⚠️ **ATENÇÃO! Há {qtd_pacotes} PACOTES para este mesmo endereço!**")
                st.write("**Lista de todos os pacotes desta parada:**")
                for idx, pkg in enumerate(pacotes_da_parada, start=1):
                    if pkg == codigo_limpo:
                        st.markdown(f"* **{idx}. `{pkg}` 👈 (Este que você bipou)**")
                    else:
                        st.markdown(f"* {idx}. `{pkg}`")
            else:
                st.info("ℹ️ Esta parada possui apenas **1 pacote**.")
        else:
            st.error("❌ Esse pacote NÃO está neste PDF!")
