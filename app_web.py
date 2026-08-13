import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# Configuração de App
st.set_page_config(page_title="RotaFácil", page_icon="⚡", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .custom-card { background-color: #1E1E1E; padding: 18px; border-radius: 14px; border-left: 5px solid #FF9500; margin-bottom: 15px; }
    iframe { width: 100% !important; height: 380px !important; border-radius: 16px !important; border: 3px solid #FF9500 !important; background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚡ RotaFácil")
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)

st.title("📦 RotaFácil")

arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota (Circuit)", type=["pdf"])

if arquivo_pdf:
    with st.spinner('Mapeando endereços...'):
        leitor = PdfReader(arquivo_pdf)
        texto = ""
        for p in leitor.pages: texto += p.extract_text() + "\n"

        # Dicionário: { "rua genival 1790": ["BR1", "BR2"] }
        mapa_enderecos = {}
        stop_correspondente = {} # { "BR1": 1 }
        
        linhas = [l.strip() for l in texto.split('\n') if l.strip()]
        stop_atual = 1
        
        for linha in linhas:
            # Detecta Parada
            match_stop = re.match(r'^\s*(\d+)', linha)
            if match_stop: stop_atual = int(match_stop.group(1))
            
            # Extrai Nome da Rua + Número (ignora AP, casa, etc)
            # Procura por: [Nome da Rua] [Numero]
            match_endereco = re.search(r'(Rua|Av|Estrada|Trav)\s+[a-zA-Z]+\s+(\d+)', linha, re.IGNORECASE)
            
            codigos = re.findall(r'BR[A-Za-z0-9]+', linha)
            
            if match_endereco and codigos:
                key = match_endereco.group(0).lower() # Ex: "rua genival 1790"
                if key not in mapa_rotas: mapa_rotas[key] = []
                
                for c in codigos:
                    if c not in mapa_rotas[key]:
                        mapa_rotas[key].append(c)
                        stop_correspondente[c] = stop_atual

    st.success(f"✅ Rota mapeada por endereços!")

    st.subheader("📷 Scanner")
    codigo_camera = qrcode_scanner(key="scanner")
    codigo_manual = st.text_input("Ou digite o código:", placeholder="Ex: BR...")
    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        cod = codigo_final.strip()
        achou = False
        
        # Procura em qual endereço esse pacote está
        for end, lista_pacotes in mapa_rotas.items():
            if cod in lista_pacotes:
                num_parada = stop_correspondente.get(cod, "?")
                
                st.markdown('<div class="custom-card" style="border-left-color: #28a745;">', unsafe_allow_html=True)
                st.metric("PARADA Nº", num_parada)
                st.write(f"📍 **Endereço:** {end.title()}")
                
                # Feedback de Múltiplos no MESMO endereço
                if len(lista_pacotes) > 1:
                    st.warning(f"⚠️ **ATENÇÃO: {len(lista_pacotes)} pacotes para este endereço!**")
                    for idx, p in enumerate(lista_pacotes, 1):
                        st.markdown(f"* {idx}. `{'👈 VOCÊ BIPOU' if p==cod else p}`")
                
                # Áudio
                if usar_audio:
                    texto_fala = f"Parada {num_parada}. {len(lista_pacotes)} pacotes no endereço."
                    components.html(f"""<script>
                        var msg = new SpeechSynthesisUtterance('{texto_fala}');
                        msg.lang = 'pt-BR'; window.speechSynthesis.speak(msg);
                    </script>""", height=0)
                
                achou = True
                break
        
        if not achou:
            st.error("❌ Código não encontrado!")
