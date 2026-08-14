import io
import re
import hashlib
import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner

# =========================
# CONFIGURAÇÃO
# =========================

APP = "PACOTE É MATO"
LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"

st.set_page_config(
    page_title=APP,
    page_icon="📦",
    layout="centered"
)

# =========================
# MEMÓRIA
# =========================

for key, default in {
    "bipados": set(),
    "rota_id": None,
    "ultimo_qr": "",
    "ultimo_resultado": None,
}.items():

    if key not in st.session_state:
        st.session_state[key] = default


# =========================
# FUNÇÕES
# =========================

def limpar(texto):
    return re.sub(
        r"\s+",
        " ",
        texto or ""
    ).strip()


def extrair_parada(linha, atual):

    padroes = [
        r"\b(?:parada|stop)\s*[:#-]?\s*(\d{1,3})\b",
        r"\bP\s*[:#-]?\s*(\d{1,3})\b",
        r"^\s*(\d{1,3})\b",
    ]

    for padrao in padroes:

        m = re.search(
            padrao,
            linha,
            re.I
        )

        if m:
            return int(
                m.group(1)
            )

    return atual


def extrair_endereco(texto):

    m = re.search(
        r"\b(rua|r\.?|avenida|av\.?|travessa|tv\.?|alameda|estrada|rodovia|praça|praca)"
        r"\s+([^,\n]{2,70}?)\s*,?\s*(?:n[º°o]?\s*)?(\d+[A-Za-z]?)\b",
        texto,
        re.I,
    )

    if not m:
        return None

    return limpar(
        f"{m.group(1)} {m.group(2)} {m.group(3)}"
    ).lower()


def ler_pdf(pdf_bytes):

    reader = PdfReader(
        io.BytesIO(pdf_bytes)
    )

    linhas = []

    for page in reader.pages:

        texto = (
            page.extract_text()
            or ""
        )

        linhas.extend(
            texto.splitlines()
        )

    pacotes = {}
    grupos = {}

    parada = 0

    for i, linha in enumerate(linhas):

        parada = extrair_parada(
            linha,
            parada
        )

        codigos = re.findall(
            r"\bBR[A-Za-z0-9]{10,14}\b",
            linha,
            re.I
        )

        if not codigos:
            continue

        contexto = " ".join(
            linhas[
                max(0, i - 2):
                min(len(linhas), i + 3)
            ]
        )

        endereco = (
            extrair_endereco(contexto)
            or
            f"parada_{parada}_{i}"
        )

        for codigo in codigos:

            codigo = codigo.upper()

            if codigo in pacotes:
                continue

            pacotes[codigo] = {
                "parada": parada,
                "endereco": endereco
            }

            grupos.setdefault(
                endereco,
                []
            ).append(
                codigo
            )

    return pacotes, grupos


# =========================
# VOZ
# =========================

def falar(
    parada,
    mesmo_endereco
):

    texto = str(
        parada
    )

    if mesmo_endereco:

        texto += (
            ". Atenção, mesmo endereço."
        )

    js = """
    <script>

    try {

        window.speechSynthesis.cancel();

        const msg =
            new SpeechSynthesisUtterance(
                __TEXT__
            );

        msg.lang =
            'pt-BR';

        msg.rate =
            1.0;

        window.speechSynthesis.speak(
            msg
        );

    }

    catch(e) {}

    </script>
    """

    js = js.replace(
        "__TEXT__",
        repr(texto)
    )

    components.html(
        js,
        height=0
    )


# =========================
# MENU LATERAL
# =========================

with st.sidebar:

    st.title(
        "🚚 " + APP
    )

    tema = st.selectbox(
        "🎨 Tema",
        [
            "Escuro",
            "Claro",
            "Azul",
            "Vermelho"
        ]
    )

    usar_audio = st.toggle(
        "🔊 Falar parada",
        value=True
    )

    arquivo_sidebar = (
        st.file_uploader(
            "📂 PDF da rota",
            type=["pdf"],
            key="pdf_sidebar"
        )
    )

    if st.button(
        "🔄 Zerar rota",
        use_container_width=True
    ):

        st.session_state.bipados = set()

        st.session_state.ultimo_qr = ""

        st.session_state.ultimo_resultado = None

        st.rerun()


# =========================
# CORES
# =========================

cores = {

    "Escuro": (
        "#111111",
        "#1d1d1d",
        "#ffffff",
        "#ff9500"
    ),

    "Claro": (
        "#f5f5f5",
        "#ffffff",
        "#111111",
        "#007aff"
    ),

    "Azul": (
        "#081a2b",
        "#123455",
        "#ffffff",
        "#38bdf8"
    ),

    "Vermelho": (
        "#1d0505",
        "#330909",
        "#ffffff",
        "#ff4d4d"
    ),
}


bg, card, text, accent = (
    cores[tema]
)


# =========================
# CSS
# =========================

css = """
<style>

.stApp {
    background: __BG__;
    color: __TEXT__;
}

.block-container {
    max-width: 760px;
    padding-top: 1rem;
}

.hero {
    background: __CARD__;
    border: 1px solid __ACCENT__;
    border-radius: 18px;
    padding: 20px;
    text-align: center;
    margin-bottom: 16px;
}

.hero img {
    width: 72px;
}

.hero h1 {
    color: __ACCENT__;
    margin: 6px 0 0 0;
    font-size: 1.8rem;
}

.stats {
    background: __CARD__;
    border: 1px solid __ACCENT__;
    border-radius: 14px;
    padding: 14px;
    display: flex;
    justify-content: space-around;
    text-align: center;
    margin-bottom: 12px;
}

.big {
    font-size: 1.6rem;
    font-weight: 800;
    color: __ACCENT__;
}

.parada {
    background: __CARD__;
    border-left: 6px solid __ACCENT__;
    border-radius: 12px;
    padding: 16px;
    margin-top: 12px;
}

.parada-num {
    font-size: 3rem;
    font-weight: 900;
    color: __ACCENT__;
}

</style>
"""

css = (
    css
    .replace(
        "__BG__",
        bg
    )
    .replace(
        "__CARD__",
        card
    )
    .replace(
        "__TEXT__",
        text
    )
    .replace(
        "__ACCENT__",
        accent
    )
)

st.markdown(
    css,
    unsafe_allow_html=True
)


# =========================
# TELA INICIAL
# =========================

arquivo_main = None

if not arquivo_sidebar:

    hero = """
    <div class="hero">

        <img src="__LOGO__">

        <h1>
            __APP__
        </h1>

        <div>
            Sistema inteligente de logística
        </div>

    </div>
    """

    hero = (
        hero
        .replace(
            "__LOGO__",
            LOGO
        )
        .replace(
            "__APP__",
            APP
        )
    )

    st.markdown(
        hero,
        unsafe_allow_html=True
    )

    arquivo_main = (
        st.file_uploader(
            "📄 Carregar PDF da rota",
            type=["pdf"],
            key="pdf_main"
        )
    )


arquivo = (
    arquivo_sidebar
    or
    arquivo_main
)


if not arquivo:

    st.info(
        "Envie o PDF da rota para começar."
    )

    st.stop()


# =========================
# CARREGA ROTA
# =========================

pdf_bytes = (
    arquivo.getvalue()
)

rota_id = (
    hashlib
    .sha256(pdf_bytes)
    .hexdigest()[:12]
)


if (
    st.session_state.rota_id
    !=
    rota_id
):

    st.session_state.rota_id = (
        rota_id
    )

    st.session_state.bipados = set()

    st.session_state.ultimo_qr = ""

    st.session_state.ultimo_resultado = None


try:

    pacotes, grupos = (
        ler_pdf(pdf_bytes)
    )

except Exception as e:

    st.error(
        f"Erro ao ler PDF: {e}"
    )

    st.stop()


if not pacotes:

    st.error(
        "Nenhum código BR foi encontrado no PDF."
    )

    st.stop()


# =========================
# PLACAR
# =========================

total = len(
    pacotes
)

bipados = len(
    st.session_state.bipados
)

faltam = (
    total - bipados
)


st.markdown(
    f"""
    <div class="stats">

        <div>

            <div class="big">
                {bipados}/{total}
            </div>

            <div>
                BIPADOS
            </div>

        </div>

        <div>

            <div class="big">
                {faltam}
            </div>

            <div>
                FALTAM
            </div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
)


st.progress(
    bipados / total
)


if faltam == 0:

    st.success(
        "🏁 Rota concluída!"
    )


# =========================
# MESMO ENDEREÇO
# =========================

with st.expander(
    "🤖 Pacotes no mesmo endereço"
):

    encontrou = False

    for endereco, lista in grupos.items():

        if len(lista) > 1:

            encontrou = True

            paradas = sorted({
                pacotes[c]["parada"]
                for c in lista
            })

            st.write(
                f"🚨 {endereco.title()} "
                f"— {len(lista)} pacotes "
                f"— "
                +
                ", ".join(
                    f"P{x}"
                    for x in paradas
                )
            )

    if not encontrou:

        st.info(
            "Nenhum endereço com mais de um pacote."
        )


# =========================
# SCANNER
# =========================

st.subheader(
    "📸 Bipar pacote"
)

codigo_scanner = (
    qrcode_scanner(
        key="scanner"
    )
)


# =========================
# DIGITAÇÃO MANUAL
# =========================

st.caption(
    "Ou digite o código manualmente:"
)


col1, col2 = st.columns(
    [3, 1]
)


with col1:

    codigo_manual = (
        st.text_input(
            "Código",
            placeholder="BR123456789012",
            label_visibility="collapsed"
        )
    )


with col2:

    buscar = st.button(
        "Buscar",
        use_container_width=True
    )


# =========================
# DEFINE O CÓDIGO
# =========================

codigo = ""


if codigo_scanner:

    qr = (
        str(codigo_scanner)
        .upper()
        .strip()
    )

    if (
        qr
        !=
        st.session_state.ultimo_qr
    ):

        codigo = qr

        st.session_state.ultimo_qr = (
            qr
        )


elif buscar and codigo_manual:

    codigo = (
        codigo_manual
        .upper()
        .strip()
    )


# =========================
# PROCESSA
# =========================

if codigo:

    if codigo not in pacotes:

        st.session_state.ultimo_resultado = {
            "tipo":
                "erro",

            "codigo":
                codigo
        }

    else:

        ja_bipado = (
            codigo
            in
            st.session_state.bipados
        )

        st.session_state.bipados.add(
            codigo
        )

        info = (
            pacotes[codigo]
        )

        mesmo_endereco = (
            len(
                grupos[
                    info["endereco"]
                ]
            )
            >
            1
        )

        st.session_state.ultimo_resultado = {

            "tipo":
                "repetido"
                if ja_bipado
                else
                "ok",

            "codigo":
                codigo,

            "parada":
                info["parada"],

            "endereco":
                info["endereco"],
        }


        if (
            usar_audio
            and
            not ja_bipado
        ):

            falar(
                info["parada"],
                mesmo_endereco
            )


# =========================
# RESULTADO
# =========================

r = (
    st.session_state.ultimo_resultado
)


if r:

    if r["tipo"] == "erro":

        st.error(
            "❌ Código não encontrado: "
            +
            r["codigo"]
        )

    else:

        endereco_txt = (
            r["endereco"]
        )

        if endereco_txt.startswith(
            "parada_"
        ):

            endereco_txt = (
                "Endereço não identificado"
            )


        card_html = """
        <div class="parada">

            <div class="parada-num">
                __PARADA__
            </div>

            <div>
                📦 __CODIGO__
            </div>

            <div>
                📍 __ENDERECO__
            </div>

        </div>
        """


        card_html = (
            card_html
            .replace(
                "__PARADA__",
                f"P{r['parada']}"
            )
            .replace(
                "__CODIGO__",
                r["codigo"]
            )
            .replace(
                "__ENDERECO__",
                endereco_txt.title()
            )
        )


        st.markdown(
            card_html,
            unsafe_allow_html=True
        )


        if (
            r["tipo"]
            ==
            "repetido"
        ):

            st.warning(
                "⚠️ Esse pacote já foi bipado."
            )


        lista = (
            grupos[
                r["endereco"]
            ]
        )


        pendentes_mesmo_endereco = [

            c

            for c in lista

            if c
            not in
            st.session_state.bipados
        ]


        if (
            len(lista) > 1
            and
            pendentes_mesmo_endereco
        ):

            st.warning(

                "⚠️ Mesmo endereço! "
                "Ainda falta: "

                +

                ", ".join(

                    f"{c} "
                    f"(P{pacotes[c]['parada']})"

                    for c
                    in pendentes_mesmo_endereco
                )

            )


# =========================
# PENDENTES
# =========================

with st.expander(
    "📋 Ver pacotes pendentes"
):

    pendentes = [

        c

        for c in pacotes

        if c
        not in
        st.session_state.bipados
    ]


    if not pendentes:

        st.success(
            "Nenhum pacote pendente."
        )

    else:

        for c in sorted(

            pendentes,

            key=lambda x:
                pacotes[x]["parada"]

        ):

            st.write(
                f"P{pacotes[c]['parada']} — {c}"
    )
