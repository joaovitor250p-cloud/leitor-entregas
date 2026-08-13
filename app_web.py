import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração da Página
st.set_page_config(page_title="RotaFácil", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .custom-card { background-color: #1E1E1E; padding: 18px; border-radius: 14px; border-left: 5px solid #FF9500; margin-bottom: 15px; }
    iframe { width: 100% !important; height: 350px !important; border-radius: 14px !important; border: 3px solid #FF9500 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 PacoteMato")

# Carregamento do PDF
arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])

if arquivo_pdf:
    with st.spinner('Mapeando pacotes por endereço...'):
        leitor = PdfReader(arquivo_pdf)
        texto = ""
        for p in leitor.pages: texto += p.extract_text() + "\n"
        
        # Estrutura: { parada_numero: [lista_de_codigos] }
        mapa_rotas = {}
        stop_atual = 1
        
        # Regex para encontrar números de parada (ex: "1", "01", "Parada 1") e códigos BR
        linhas = texto.split('\n')
        
        for linha in linhas:
            # Tenta achar se a linha começa com um número de parada (ex: "1 BR...")
            match_stop = re.match(r'^\s*(\d{1,3})\.?\s*', linha.strip())
            if match_stop:
                stop_atual = int(match_stop.group(1))
            
            # Pega todos os códigos BR na linha
            codigos = re.findall(r'BR[A-Za-z0-9]+', linha)
            if codigos:
                if stop_atual not in mapa_rotas: mapa_rotas[stop_atual] = []
                for c in codigos:
                    if c not in mapa_rotas[stop_atual]:
                        mapa_rotas[stop_atual].append(c)

    st.success(f"✅ Rota mapeada com sucesso!")

    # SCANNER
    st.subheader("📷 Scanner")
    codigo_camera = qrcode_scanner(key="scanner")
    codigo_manual = st.text_input("Ou digite o código:", placeholder="Ex: BR...")
    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        cod = codigo_final.strip()
        achou = False
        
        # Busca em qual parada esse código está
        for stop, lista_pacotes in mapa_rotas.items():
            if cod in lista_pacotes:
                st.markdown(f'<div class="custom-card" style="border-left-color: #28a745;">', unsafe_allow_html=True)
                st.metric("PARADA Nº", stop)
                
                # Feedback de Múltiplos
                if len(lista_pacotes) > 1:
                    st.warning(f"⚠️ **ATENÇÃO: {len(lista_pacotes)} pacotes neste local!**")
                    for idx, p in enumerate(lista_pacotes, 1):
                        st.write(f"{idx}. `{'👈 VOCÊ BIPOU' if p==cod else p}`")
                else:
                    st.info("ℹ️ Apenas 1 pacote neste local.")
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Áudio
                components.html(f"""<script>
                    var msg = new SpeechSynthesisUtterance('Parada {stop}. {len(lista_pacotes)} pacotes.');
                    msg.lang = 'pt-BR'; window.speechSynthesis.speak(msg);
                </script>""", height=0)
                
                achou = True
                break
        
        if not achou:
            st.error("❌ Código não encontrado nesta rota!")
            
