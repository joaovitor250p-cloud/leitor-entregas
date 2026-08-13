import re
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner


# ============================================================
# CONFIGURAÇÃO
# ============================================================

NOME_DO_APP = "PACOTE É MATO"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"

st.set_page_config(
    page_title=NOME_DO_APP,
    page_icon=URL_DO_LOGO,
    layout="centered"
)


# ============================================================
# SESSION STATE
# ============================================================

if "pacotes_bipados" not in st.session_state:
    st.session_state.pacotes_bipados = set()

if "ultimo_codigo" not in st.session_state:
    st.session_state.ultimo_codigo = ""

if "ultimo_resultado" not in st.session_state:
    st.session_state.ultimo_resultado = None


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.stApp {
    background-color: #121212;
    color: #FFFFFF;
}

.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* =========================
   BOAS VINDAS
========================= */

.welcome-card {
    background-color: #1E1E1E;
    padding: 24px;
    border-radius: 18px;
    border: 1px solid #333333;
    text-align: center;
    box-shadow: 0 8px 20px rgba(0,0,0,0.4);
    margin-top: 10px;
    margin-bottom: 20px;
}

.welcome-logo {
    width: 90px;
    height: 90px;
    object-fit: contain;
    margin-bottom: 10px;
}

.welcome-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: #FF9500;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
}

.welcome-subtitle {
    font-size: 0.8rem;
    color: #888888;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 18px;
}

.instruction-box {
    background-color: #141414;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #2A2A2A;
    text-align: left;
    margin-top: 15px;
}

.instruction-step {
    font-size: 0.88rem;
    color: #DDDDDD;
    margin-bottom: 10px;
}


/* =========================
   ESTATÍSTICAS
========================= */

.stat-banner {
    background-color: #1E1E1E;
    border-radius: 12px;
    padding: 12px;
    border: 1px solid #333;
    display: flex;
    justify-content: space-around;
    margin-bottom: 15px;
}

.stat-value {
    font-size: 1.3rem;
    font-weight: bold;
    color: #28a745;
}

.stat-value-orange {
    font-size: 1.3rem;
    font-weight: bold;
    color: #FF9500;
}


/* =========================
   CARTÃO DA PARADA
========================= */

.custom-card {
    background-color: #1E1E1E;
    padding: 18px;
    border-radius: 14px;
    border-left: 6px solid #28a745;
    margin-bottom: 15px;
}

.stop-number-big {
    font-size: 3.5rem;
    font-weight: 900;
    color: #FF9500;
    line-height: 1;
    margin-bottom: 10px;
}


/* =========================
   SCANNER
========================= */

.scanner-title {
    text-align: center;
    color: #FF9500;
    font-size: 1rem;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 8px;
}

.scanner-help {
    text-align: center;
    color: #888888;
    font-size: 0.8rem;
    margin-bottom: 12px;
}

/* Área do componente do scanner */
div[data-testid="stCustomComponentV1"] {
    width: 100% !important;
    border-radius: 16px !important;
    border: 2px solid #FF9500 !important;
    background-color: #000000 !important;
    overflow: hidden !important;
    margin-bottom: 12px !important;
}

/* Vídeo da câmera */
div[data-testid="stCustomComponentV1"] video {
    width: 100% !important;
    height: auto !important;
    object-fit: cover !important;
}


/* =========================
   INPUT MANUAL
========================= */

div[data-testid="stTextInput"] input {
    background-color: #1E1E1E !important;
    color: white !important;
    border: 1px solid #444 !important;
}


/* =========================
   BOTÕES
========================= */

.stButton button {
    border-radius: 10px;
    font-weight: 700;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title(f"🚚 {NOME_DO_APP}")
    st.caption("Sistema Inteligente de Logística")

    st.write("---")

    arquivo_pdf = st.file_uploader(
        "📂 Enviar PDF da Rota",
        type=["pdf"]
    )

    usar_audio = st.toggle(
        "🔊 Falar Número da Parada",
        value=True
    )

    tipo_voz = "Feminina / Normal"

    if usar_audio:

        tipo_voz = st.selectbox(
            "🎙️ Estilo da Voz",
            [
                "Feminina / Normal",
                "Masculina / Grave",
                "Rápida / Ágil",
                "Pica-Pau 🪶"
            ]
        )

    st.write("---")

    if st.button(
        "🔄 Zerar Rota Atual",
        use_container_width=True
    ):
        st.session_state.pacotes_bipados = set()
        st.session_state.ultimo_codigo = ""
        st.session_state.ultimo_resultado = None
        st.rerun()


# ============================================================
# EXTRAÇÃO DE ENDEREÇO
# ============================================================

def extrair_endereco_limpo(texto):

    padrao = (
        r'\b'
        r'(rua|r\.|av\.?|avenida|al\.?|alameda|'
        r'estrada|tv\.?|travessa)'
        r'\s+'
        r'([a-záàâãéèêíïóôõöúçñ0-9\s\.\-]+?)'
        r'\s*,?\s*'
        r'(\d+)'
        r'\b'
    )

    match = re.search(
        padrao,
        texto,
        re.IGNORECASE
    )

    if match:

        logradouro = match.group(1)
        nome = match.group(2)
        numero = match.group(3)

        return (
            f"{logradouro} {nome} {numero}"
            .lower()
            .strip()
        )

    return None


# ============================================================
# NORMALIZAÇÃO DO CÓDIGO
# ============================================================

def normalizar_codigo(codigo):

    if not codigo:
        return None

    codigo = str(codigo).upper().strip()

    # Remove espaços, quebras e caracteres estranhos
    codigo = re.sub(r'[^A-Z0-9]', '', codigo)

    # Código de rastreio precisa começar com BR
    if not codigo.startswith("BR"):
        return None

    # Mantém somente códigos de tamanho plausível
    if not (12 <= len(codigo) <= 16):
        return None

    return codigo


# ============================================================
# LEITURA DO PDF
# ============================================================

mapa_rotas = {}
stop_correspondente = {}
nome_exibicao = {}
todos_pacotes = set()

if arquivo_pdf:

    leitor = PdfReader(arquivo_pdf)

    paginas = []

    for pagina in leitor.pages:

        texto_pagina = pagina.extract_text() or ""
        paginas.append(texto_pagina)

    texto = "\n".join(paginas)

    linhas = texto.splitlines()

    stop_atual = 0

    for linha in linhas:

        # Procura número da parada
        m_stop = re.match(
            r'^\s*(\d{1,3})\b',
            linha
        )

        if m_stop:
            stop_atual = int(m_stop.group(1))

        # Procura possíveis códigos BR
        candidatos = re.findall(
            r'\bBR[A-Z0-9]{10,14}\b',
            linha.upper()
        )

        cods = []

        for candidato in candidatos:

            codigo = normalizar_codigo(candidato)

            if codigo and codigo not in cods:
                cods.append(codigo)

        if not cods:
            continue

        endereco = (
            extrair_endereco_limpo(linha)
            or f"desconhecido_{stop_atual}"
        )

        if endereco not in mapa_rotas:
            mapa_rotas[endereco] = []

        for codigo in cods:

            todos_pacotes.add(codigo)

            if codigo not in mapa_rotas[endereco]:

                mapa_rotas[endereco].append(codigo)

                stop_correspondente[codigo] = stop_atual

                nome_exibicao[endereco] = linha[:80]


# ============================================================
# FUNÇÃO DE ÁUDIO
# ============================================================

def falar_parada(num_p, quantidade):

    if not usar_audio:
        return

    pitch_val = 1.0
    rate_val = 1.0

    if "Pica-Pau" in tipo_voz:

        fala_texto = f"He-he-he-he! Parada {num_p}!"

        if quantidade > 1:
            fala_texto += f" Atenção, {quantidade} pacotes!"

        pitch_val = 1.8
        rate_val = 1.45

    else:

        fala_texto = f"Parada {num_p}"

        if quantidade > 1:
            fala_texto += f". Atenção, {quantidade} pacotes!"

        if "Masculina" in tipo_voz:
            pitch_val = 0.6
            rate_val = 0.95

        elif "Rápida" in tipo_voz:
            pitch_val = 1.1
            rate_val = 1.35

    # Evita problemas com aspas no texto
    fala_segura = (
        fala_texto
        .replace("\\", "\\\\")
        .replace("'", "\\'")
    )

    js_audio = f"""
    <script>
        window.speechSynthesis.cancel();

        var msg = new SpeechSynthesisUtterance('{fala_segura}');

        msg.lang = 'pt-BR';
        msg.pitch = {pitch_val};
        msg.rate = {rate_val};

        window.speechSynthesis.speak(msg);
    </script>
    """

    components.html(
        js_audio,
        height=0
    )


# ============================================================
# PROCESSAMENTO DO CÓDIGO
# ============================================================

def processar_codigo(codigo):

    codigo = normalizar_codigo(codigo)

    if not codigo:
        st.session_state.ultimo_resultado = {
            "tipo": "erro",
            "mensagem": "❌ Código inválido."
        }
        return

    # Evita o scanner processar o mesmo QR várias vezes
    if codigo == st.session_state.ultimo_codigo:
        return

    st.session_state.ultimo_codigo = codigo

    # Procura o pacote
    encontrou = False

    for endereco, lista in mapa_rotas.items():

        if codigo not in lista:
            continue

        encontrou = True

        # Marca como bipado
        st.session_state.pacotes_bipados.add(codigo)

        num_p = stop_correspondente.get(
            codigo,
            "?"
        )

        outros = [
            pacote
            for pacote in lista
            if pacote != codigo
            and pacote not in st.session_state.pacotes_bipados
        ]

        st.session_state.ultimo_resultado = {
            "tipo": "sucesso",
            "codigo": codigo,
            "parada": num_p,
            "endereco": endereco,
            "outros": outros,
            "quantidade": len(lista)
        }

        return

    if not encontrou:

        st.session_state.ultimo_resultado = {
            "tipo": "nao_encontrado",
            "codigo": codigo
        }


# ============================================================
# TELA PRINCIPAL
# ============================================================

if arquivo_pdf:

    bipados = len(st.session_state.pacotes_bipados)
    total = len(todos_pacotes)

    faltam = max(0, total - bipados)

    st.markdown(
        f"""
        <div class="stat-banner">
            <div>
                <div class="stat-value">
                    {bipados} / {total}
                </div>
                <small>BIPADOS</small>
            </div>

            <div>
                <div class="stat-value-orange">
                    {faltam}
                </div>
                <small>FALTAM</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


    # ========================================================
    # DUPLOS
    # ========================================================

    with st.expander(
        "🤖 Ver pacotes no mesmo endereço / duplos"
    ):

        encontrou_duplo = False

        for endereco, pacotes in mapa_rotas.items():

            if len(pacotes) > 1:

                encontrou_duplo = True

                parada = stop_correspondente.get(
                    pacotes[0],
                    "?"
                )

                st.markdown(
                    f"""
                    🚨 **{endereco.title()}**

                    `{len(pacotes)} pacotes`

                    Parada **P{parada}**
                    """
                )

                for pacote in pacotes:
                    st.code(pacote)

        if not encontrou_duplo:
            st.info(
                "Nenhum endereço com múltiplos pacotes nesta rota."
            )


    # ========================================================
    # SCANNER
    # ========================================================

    st.markdown(
        '<div class="scanner-title">📷 BIPAR PACOTE</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="scanner-help">'
        'Aponte a câmera para o QR Code do pacote'
        '</div>',
        unsafe_allow_html=True
    )


    # Scanner principal
    codigo_camera = qrcode_scanner(
        key="scanner_pacotes"
    )


    # Processa somente quando realmente recebeu algo
    if codigo_camera:

        processar_codigo(codigo_camera)


    # ========================================================
    # DIGITAÇÃO MANUAL
    # ========================================================

    st.markdown(
        "##### ⌨️ Digitar código manualmente"
    )

    codigo_manual = st.text_input(
        "Código",
        placeholder="BR123456789012",
        label_visibility="collapsed"
    )

    if codigo_manual:

        processar_codigo(codigo_manual)

        # Limpa o campo no próximo rerun
        st.rerun()


    # ========================================================
    # RESULTADO
    # ========================================================

    resultado = st.session_state.ultimo_resultado

    if resultado:

        if resultado["tipo"] == "sucesso":

            codigo = resultado["codigo"]
            parada = resultado["parada"]
            outros = resultado["outros"]
            quantidade = resultado["quantidade"]

            st.markdown(
                f"""
                <div class="custom-card">
                    <div class="stop-number-big">
                        P{parada}
                    </div>

                    <div>
                        📦 <b>{codigo}</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            if outros:

                st.warning(
                    "⚠️ **MESMO ENDEREÇO!** "
                    "Pegue também: "
                    + ", ".join(outros)
                )

            elif quantidade > 1:

                st.info(
                    "ℹ️ Os outros pacotes desse endereço "
                    "já foram bipados."
                )

            falar_parada(
                parada,
                quantidade
            )

        elif resultado["tipo"] == "nao_encontrado":

            st.error(
                f"❌ Código **{resultado['codigo']}** "
                "não encontrado na rota."
            )

        elif resultado["tipo"] == "erro":

            st.error(
                resultado["mensagem"]
            )


else:

    # ========================================================
    # TELA INICIAL
    # ========================================================

    welcome_html = f"""
    <div class="welcome-card">

        <img
            src="{URL_DO_LOGO}"
            class="welcome-logo"
        >

        <div class="welcome-title">
            {NOME_DO_APP}
        </div>

        <div class="welcome-subtitle">
            Bipagem & Gestão de Rota
        </div>

        <div class="instruction-box">

            <div class="instruction-step">
                <b>1.</b>
                Abra a barra lateral no topo
                <b>( ❯❯ )</b>
            </div>

            <div class="instruction-step">
                <b>2.</b>
                Envie o arquivo
                <b>PDF da Rota</b>
            </div>

            <div class="instruction-step">
                <b>3.</b>
                Permita o acesso à câmera
            </div>

            <div class="instruction-step">
                <b>4.</b>
                Aponte para o QR Code
            </div>

        </div>

    </div>
    """

    st.markdown(
        welcome_html,
        unsafe_allow_html=True
    )
