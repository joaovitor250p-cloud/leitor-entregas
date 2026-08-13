import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

st.set_page_config(page_title="PACOTE É MATO", page_icon="📦", layout="centered")

# Estilo Visual Dark / App Pro
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    .custom-card { background-color: #1E1E1E; padding: 18px; border-radius: 14px; border-left: 5px solid #FF9500; margin-bottom: 15px; }
    .ai-card { background-color: #2D2D2D; padding: 15px; border-radius: 10px; border: 1px solid #FF9500; }
    iframe { width: 100% !important; height: 380px !important; border-radius: 16px !important; border: 3px solid #FF9500 !important; background-color: transparent !important; }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚡ PACOTE É MATO")
    st.write("---")
    usar_audio = st.toggle("🔊 Feedback por Voz", value=True)
    st.caption("IA de Mapeamento Ativa")

st.title("📦 PACOTE É MATO")

arquivo_pdf = st.file_uploader("📂 Enviar PDF da Rota (Circuit)", type=["pdf"])

def extrair_endereco_base(texto):
    # Procura por: [Rua/Av/...] + [Nome] + [Numero]
    match = re.search(r'(rua|av|estrada|trav|pca)\s+[a-z\s]+\s+(\d+)', texto.lower())
    if match:
        return match.group(0) # Retorna "rua genival 1790"
    return "sem_endereco"

if arquivo_pdf:
    with st.spinner('IA analisando rota e agrupando...'):
        leitor = PdfReader(arquivo_pdf)
        texto = "".join([p.extract_text() for p in leitor.pages])
        
        mapa_rotas = {}
        stop_correspondente = {}
        
        linhas = [l.strip() for l in texto.split('\n') if l.strip()]
        stop_atual = 1
        
        for linha in linhas:
            if re.match(r'^\s*(\d{1,3})\b', linha): stop_atual = int(re.match(r'^\s*(\d{1,3})\b', linha).group(1))
            
            codigos = re.findall(r'BR[A-Za-z0-9]+', linha)
            if codigos:
                end_base = extrair_endereco_base(linha)
                if end_base == "sem_endereco": end_base = f"parada_{stop_atual}"
                
                if end_base not in mapa_rotas: mapa_rotas[end_base] = []
                for c in codigos:
                    if c not in mapa_rotas[end_base]:
                        mapa_rotas[end_base].append(c)
                        stop_correspondente[c] = stop_atual

    # --- ANÁLISE PROATIVA (IA) ---
    st.success("✅ Rota mapeada!")
    with st.expander("🤖 Análise Inteligente de Endereços (Veja pacotes duplos antes de bipar)"):
        encontrou_multiplos = False
        for end, pacotes in mapa_rotas.items():
            if len(pacotes) > 1:
                st.markdown(f"📍 **{end.title()}**: {len(pacotes)} pacotes")
                encontrou_multiplos = True
        if not encontrou_multiplos: st.write("Tudo limpo, sem endereços com múltiplos pacotes.")

    st.subheader("📷 Scanner")
    codigo_camera = qrcode_scanner(key="scanner")
    codigo_manual = st.text_input("Ou digite o código:", placeholder="Ex: BR...")
    codigo_final = codigo_camera or codigo_manual

    if codigo_final:
        cod = codigo_final.strip()
        achou = False
        for end, lista in mapa_rotas.items():
            if cod in lista:
                num_p = stop_correspondente.get(cod, "?")
                st.markdown('<div class="custom-card" style="border-left-color: #28a745;">', unsafe_allow_html=True)
                st.metric("PARADA Nº", num_p)
                st.write(f"📍 **Endereço:** {end.title()}")
                
                if len(lista) > 1:
                    st.warning(f"⚠️ **ATENÇÃO: {len(lista)} pacotes neste local!**")
                    for i, p in enumerate(lista, 1):
                        st.markdown(f"* {i}. `{'👈 VOCÊ BIPOU' if p==cod else p}`")
                
                if usar_audio:
                    texto_fala = f"Parada {num_p}. {len(lista)} pacotes." if len(lista) > 1 else f"Parada {num_p}"
                    components.html(f"""<script>
                        window.speechSynthesis.cancel();
                        var msg = new SpeechSynthesisUtterance('{texto_fala}');
                        msg.lang = 'pt-BR'; window.speechSynthesis.speak(msg);
                    </script>""", height=0)
                st.markdown('</div>', unsafe_allow_html=True)
                achou = True
                break
        if not achou: st.error("❌ Código não encontrado!")
