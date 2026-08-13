import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

if "pacotes_bipados" not in st.session_state: st.session_state.pacotes_bipados = set()
if "pacotes_faltando" not in st.session_state: st.session_state.pacotes_faltando = set()

# Estilos
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .stat-banner { background-color: #1E1E1E; border-radius: 12px; padding: 12px; border: 1px solid #333; display: flex; justify-content: space-around; margin-bottom: 15px; }
    .stat-value { font-size: 1.3rem; font-weight: bold; color: #28a745; }
    .stat-value-orange { font-size: 1.3rem; font-weight: bold; color: #FF9500; }
    .custom-card { background-color: #1E1E1E; padding: 18px; border-radius: 14px; border-left: 6px solid #28a745; margin-bottom: 15px; }
    .stop-number-big { font-size: 3.5rem; font-weight: 900; color: #FF9500; line-height: 1; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

# MENU LATERAL
with st.sidebar:
    st.title("📦 PACOTE É MATO")
    arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota", type=["pdf"])
    if st.button("🔄 Zerar Rota"):
        st.session_state.pacotes_bipados = set()
        st.session_state.pacotes_faltando = set()
        st.rerun()

# Lógica de Extração Super Permissiva
mapa_rotas, stop_correspondente, nome_exibicao, todos_os_pacotes = {}, {}, {}, set()

if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto_total = ""
    for p in leitor.pages: texto_total += p.extract_text() + "\n"
    
    # Pega TUDO que parece um código BR
    codigos_encontrados = re.findall(r'BR[A-Za-z0-9]+', texto_total, re.IGNORECASE)
    for c in codigos_encontrados:
        todos_os_pacotes.add(c.upper())
    
    # Tenta associar paradas (mais robusto)
    blocos = re.split(r'(\d{1,3}\s*-)', texto_total)
    stop_atual = 1
    for i in range(1, len(blocos), 2):
        stop_atual = int(re.sub(r'\D', '', blocos[i]))
        bloco_texto = blocos[i+1]
        cods_no_bloco = re.findall(r'BR[A-Za-z0-9]+', bloco_texto, re.IGNORECASE)
        
        chave = f"parada_{stop_atual}"
        if chave not in mapa_rotas: mapa_rotas[chave] = []
        for c in cods_no_bloco:
            c_upper = c.upper()
            if c_upper not in mapa_rotas[chave]:
                mapa_rotas[chave].append(c_upper)
                stop_correspondente[c_upper] = stop_atual
                nome_exibicao[chave] = "Parada " + str(stop_atual)

# UI
if arquivo_pdf:
    # Painel de Progresso
    total = len(todos_os_pacotes)
    bipados = len(st.session_state.pacotes_bipados)
    st.markdown(f'<div class="stat-banner"><div class="stat-value">{bipados} / {total} Bipados</div></div>', unsafe_allow_html=True)
    
    # Debug
    with st.expander("⚙️ Inspeção de Rota (O que o app leu)"):
        st.write(f"Total de códigos encontrados: {total}")
        st.write(list(todos_os_pacotes)[:20]) # Mostra os primeiros 20
    
    codigo_final = qrcode_scanner(key="scan") or st.text_input("Digitar código:", placeholder="BR...")
    
    if codigo_final:
        cod = codigo_final.strip().upper()
        achou = False
        for chave, lista in mapa_rotas.items():
            if cod in lista:
                st.session_state.pacotes_bipados.add(cod)
                st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{stop_correspondente.get(cod, "?")}</div><div>📍 <b>Pacote:</b> {cod}</div></div>', unsafe_allow_html=True)
                achou = True
                break
        if not achou:
            st.error(f"❌ '{cod}' não foi encontrado na leitura do PDF. Verifique se o PDF está correto.")
else:
    st.info("Envie o PDF.")
