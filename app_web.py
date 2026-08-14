import csv
import hashlib
import html
import io
import json
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Set

import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner


# =========================================================
# CONFIGURAÇÃO
# =========================================================

NOME_DO_APP = "PACOTE É MATO"
URL_DO_LOGO = "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"

st.set_page_config(
    page_title=NOME_DO_APP,
    page_icon=URL_DO_LOGO,
    layout="centered",
)


# =========================================================
# ESTADO DA SESSÃO
# =========================================================

def init_state():
    defaults = {
        "pacotes_bipados": set(),
        "rota_id": None,
        "ultimo_codigo_scanner": "",
        "ultimo_resultado": None,
        "ultimo_evento": "",
        "ultimo_evento_ts": 0.0,
    }

    for chave, valor in defaults.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


init_state()


# =========================================================
# MODELO DA ROTA
# =========================================================

@dataclass
class RouteData:
    mapa_rotas: Dict[str, List[str]]
    pacote_para_endereco: Dict[str, str]
    stop_correspondente: Dict[str, int]
    todos_pacotes: Set[str]
    avisos: List[str]


# =========================================================
# FUNÇÕES DE TEXTO
# =========================================================

def normalizar_espacos(texto: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        texto or ""
    ).strip()


def extrair_stop(linha: str):
    linha = normalizar_espacos(linha)

    padroes = [
        r"\b(?:parada|stop)\s*[:#\-]?\s*(\d{1,3})\b",
        r"\bP\s*[:#\-]?\s*(\d{1,3})\b",
        r"^\s*(\d{1,3})(?=\s|[-–—])",
    ]

    for padrao in padroes:
        match = re.search(
            padrao,
            linha,
            re.IGNORECASE
        )

        if match:
            valor = int(match.group(1))

            if 0 < valor < 1000:
                return valor

    return None


def extrair_endereco_limpo(texto: str):
    texto = normalizar_espacos(texto)

    tipo = (
        r"rua|r\.?|"
        r"av\.?|avenida|"
        r"al\.?|alameda|"
        r"estrada|est\.?|"
        r"tv\.?|travessa|"
        r"rodovia|rod\.?|"
        r"praça|praca|"
        r"viela|via"
    )

    padrao = (
        rf"\b({tipo})\s+"
        rf"([^,;\n]{{2,80}}?)"
        rf"\s*,?\s*"
        rf"(?:n[º°o]?\.?\s*)?"
        rf"(\d+[A-Za-z]?)\b"
    )

    match = re.search(
        padrao,
        texto,
        re.IGNORECASE
    )

    if not match:
        return None

    endereco = (
        f"{match.group(1)} "
        f"{match.group(2)} "
        f"{match.group(3)}"
    )

    return normalizar_espacos(
        endereco
    ).lower()


def extrair_codigos(texto: str) -> List[str]:
    candidatos = re.findall(
        r"\bBR[A-Za-z0-9]{10,14}\b",
        texto or "",
        re.IGNORECASE,
    )

    resultado = []
    vistos = set()

    for codigo in candidatos:
        codigo = codigo.upper().strip()

        if codigo not in vistos:
            vistos.add(codigo)
            resultado.append(codigo)

    return resultado


def normalizar_resultado_scanner(valor) -> str:
    if not valor:
        return ""

    if isinstance(valor, str):
        return valor.upper().strip()

    if isinstance(valor, dict):
        for chave in (
            "data",
            "text",
            "value",
            "result"
        ):
            if chave in valor and valor[chave]:
                return str(
                    valor[chave]
                ).upper().strip()

    return str(valor).upper().strip()


# =========================================================
# LEITURA DO PDF
# =========================================================

@st.cache_data(show_spinner=False)
def ler_rota_pdf(pdf_bytes: bytes) -> RouteData:

    mapa_rotas = {}
    pacote_para_endereco = {}
    stop_correspondente = {}
    todos_pacotes = set()
    avisos = []

    try:
        leitor = PdfReader(
            io.BytesIO(pdf_bytes)
        )

    except Exception as exc:
        raise ValueError(
            f"Não foi possível abrir o PDF: {exc}"
        )

    paginas = []

    for numero, pagina in enumerate(
        leitor.pages,
        start=1
    ):
        try:
            texto_pagina = (
                pagina.extract_text()
                or ""
            )

            paginas.append(
                texto_pagina
            )

            if not texto_pagina.strip():
                avisos.append(
                    f"Página {numero} sem texto extraível. "
                    "Se ela for imagem, pode ser necessário OCR."
                )

        except Exception:
            paginas.append("")

            avisos.append(
                f"Não foi possível extrair o texto da página {numero}."
            )

    linhas = "\n".join(
        paginas
    ).splitlines()

    stop_atual = None

    for i, linha in enumerate(linhas):

        stop_detectado = extrair_stop(
            linha
        )

        if stop_detectado is not None:
            stop_atual = stop_detectado

        codigos = extrair_codigos(
            linha
        )

        if not codigos:
            continue

        inicio = max(
            0,
            i - 2
        )

        fim = min(
            len(linhas),
            i + 3
        )

        contexto = " ".join(
            normalizar_espacos(x)
            for x in linhas[inicio:fim]
            if x.strip()
        )

        endereco = extrair_endereco_limpo(
            contexto
        )

        if not endereco:
            endereco = (
                "endereco_nao_identificado_"
                f"p{stop_atual or 0}_{i}"
            )

        mapa_rotas.setdefault(
            endereco,
            []
        )

        for codigo in codigos:

            if codigo in todos_pacotes:
                continue

            todos_pacotes.add(
                codigo
            )

            mapa_rotas[
                endereco
            ].append(
                codigo
            )

            pacote_para_endereco[
                codigo
            ] = endereco

            stop_correspondente[
                codigo
            ] = stop_atual or 0

    if not todos_pacotes:
        avisos.append(
            "Nenhum código BR foi encontrado no PDF. "
            "Confira se o arquivo possui texto selecionável."
        )

    return RouteData(
        mapa_rotas=mapa_rotas,
        pacote_para_endereco=pacote_para_endereco,
        stop_correspondente=stop_correspondente,
        todos_pacotes=todos_pacotes,
        avisos=avisos,
    )


# =========================================================
# CONFIGURAÇÃO DA VOZ
# =========================================================

def configuracao_voz(
    tipo_voz: str,
    numero_parada,
    mesmo_endereco: bool
):

    fala = str(
        numero_parada
    )

    pitch = 1.0
    rate = 1.0

    if mesmo_endereco:
        fala += (
            ". Atenção, mesmo endereço."
        )

    if "Pica-Pau" in tipo_voz:

        fala = (
            f"He he he! {numero_parada}!"
        )

        if mesmo_endereco:
            fala += " Atenção!"

        pitch = 1.8
        rate = 1.45

    elif "Masculina" in tipo_voz:
        pitch = 0.65
        rate = 0.95

    elif "Rápida" in tipo_voz:
        pitch = 1.1
        rate = 1.35

    elif "Locutor" in tipo_voz:
        pitch = 0.75
        rate = 0.90

    elif "Vilão" in tipo_voz:
        pitch = 0.40
        rate = 0.82

    elif "Esquilo" in tipo_voz:
        pitch = 1.90
        rate = 1.35

    return (
        fala,
        pitch,
        rate
    )


# =========================================================
# BIP + VOZ
# =========================================================

def tocar_bip_e_falar(
    fala: str,
    pitch: float,
    rate: float,
    usar_audio: bool
):

    fala_js = json.dumps(
        fala,
        ensure_ascii=False
    )

    parte_voz = ""

    if usar_audio:

        parte_voz = (
            "try {"
            "window.speechSynthesis.cancel();"
            "const msg = new SpeechSynthesisUtterance("
            + fala_js +
            ");"
            "msg.lang = 'pt-BR';"
            "msg.pitch = "
            + str(float(pitch)) +
            ";"
            "msg.rate = "
            + str(float(rate)) +
            ";"
            "window.speechSynthesis.speak(msg);"
            "} catch (e) {}"
        )

    audio_js = """
    <script>

    (function() {

        try {

            const AudioCtx =
                window.AudioContext ||
                window.webkitAudioContext;

            if (AudioCtx) {

                const ctx =
                    new AudioCtx();

                const osc =
                    ctx.createOscillator();

                const gain =
                    ctx.createGain();

                osc.type =
                    "sine";

                osc.frequency.setValueAtTime(
                    880,
                    ctx.currentTime
                );

                gain.gain.setValueAtTime(
                    0.15,
                    ctx.currentTime
                );

                osc.connect(
                    gain
                );

                gain.connect(
                    ctx.destination
                );

                osc.start();

                osc.stop(
                    ctx.currentTime
                    +
                    0.10
                );

            }

        }

        catch (e) {}

        __VOICE__

    })();

    </script>
    """.replace(
        "__VOICE__",
        parte_voz
    )

    components.html(
        audio_js,
        height=0
    )


# =========================================================
# PROCESSAR PACOTE
# =========================================================

def processar_codigo(
    codigo: str,
    rota: RouteData
):

    codigo = (
        codigo or ""
    ).upper().strip()

    if not codigo:
        return {
            "status": "vazio"
        }

    if codigo not in rota.todos_pacotes:

        return {
            "status":
                "nao_encontrado",

            "codigo":
                codigo,
        }

    endereco = (
        rota.pacote_para_endereco[
            codigo
        ]
    )

    parada = (
        rota.stop_correspondente.get(
            codigo,
            0
        )
    )

    pacotes_mesmo_endereco = (
        rota.mapa_rotas.get(
            endereco,
            []
        )
    )

    ja_bipado = (
        codigo
        in
        st.session_state.pacotes_bipados
    )

    st.session_state.pacotes_bipados.add(
        codigo
    )

    return {
        "status":
            "repetido"
            if ja_bipado
            else "ok",

        "codigo":
            codigo,

        "endereco":
            endereco,

        "parada":
            parada,

        "pacotes_mesmo_endereco":
            pacotes_mesmo_endereco,
    }


# =========================================================
# MENU LATERAL
# =========================================================

with st.sidebar:

    st.title(
        f"🚚 {NOME_DO_APP}"
    )

    st.caption(
        "Sistema Inteligente de Logística"
    )

    st.divider()

    tema_cor = st.selectbox(
        "🎨 Cor do Tema",
        [
            "Preto (Dark)",
            "RGB Gamer 🌈",
            "Branco (Light)",
            "Cinza",
            "Azul",
            "Vermelho",
        ],
    )

    arquivo_pdf_sidebar = (
        st.file_uploader(
            "📂 Enviar PDF da Rota",
            type=["pdf"],
            key="pdf_sidebar",
        )
    )

    usar_audio = st.toggle(
        "🔊 Falar Número da Parada",
        value=True,
    )

    tipo_voz = (
        "Feminina / Normal"
    )

    if usar_audio:

        tipo_voz = st.selectbox(
            "🎙️ Estilo da Voz",
            [
                "Feminina / Normal",
                "Masculina / Grave",
                "Rápida / Ágil",
                "Pica-Pau 🪶",
                "Locutor de Rádio 🎙️",
                "Vilão / Monstro 😈",
                "Esquilo 🐿️",
            ],
        )

    st.divider()

    if st.button(
        "🔄 Zerar Rota Atual",
        use_container_width=True
    ):

        st.session_state.pacotes_bipados = (
            set()
        )

        st.session_state.ultimo_codigo_scanner = (
            ""
        )

        st.session_state.ultimo_resultado = (
            None
        )

        st.session_state.ultimo_evento = (
            ""
        )

        st.session_state.ultimo_evento_ts = (
            0.0
        )

        st.rerun()


# =========================================================
# TEMAS
# =========================================================

estilos_temas = {

    "Preto (Dark)": {
        "bg_app": "#121212",
        "text_app": "#FFFFFF",
        "card_bg": "#1E1E1E",
        "border": "#333333",
        "accent": "#FF9500",
    },

    "RGB Gamer 🌈": {
        "bg_app": "#0D0D11",
        "text_app": "#FFFFFF",
        "card_bg": "#16161D",
        "border": "#222230",
        "accent": "#00FFCC",
    },

    "Branco (Light)": {
        "bg_app": "#F5F5F7",
        "text_app": "#1D1D1F",
        "card_bg": "#FFFFFF",
        "border": "#E5E5EA",
        "accent": "#007AFF",
    },

    "Cinza": {
        "bg_app": "#2C2C2E",
        "text_app": "#F2F2F7",
        "card_bg": "#3A3A3C",
        "border": "#48484A",
        "accent": "#FF9500",
    },

    "Azul": {
        "bg_app": "#0B192C",
        "text_app": "#E0F2FE",
        "card_bg": "#1E3E62",
        "border": "#0087D1",
        "accent": "#38BDF8",
    },

    "Vermelho": {
        "bg_app": "#1A0000",
        "text_app": "#FFE5E5",
        "card_bg": "#330000",
        "border": "#800000",
        "accent": "#FF4D4D",
    },
}


t = estilos_temas.get(
    tema_cor,
    estilos_temas[
        "Preto (Dark)"
    ]
)


# =========================================================
# RGB
# =========================================================

css_rgb_anim = ""

if tema_cor == "RGB Gamer 🌈":

    css_rgb_anim = """

    @keyframes rgbGlow {

        0% {
            border-color:#FF0000;
            color:#FF0000;
            box-shadow:
            0 0 12px rgba(255,0,0,.45);
        }

        20% {
            border-color:#FF8800;
            color:#FF8800;
            box-shadow:
            0 0 12px rgba(255,136,0,.45);
        }

        40% {
            border-color:#FFFF00;
            color:#FFFF00;
            box-shadow:
            0 0 12px rgba(255,255,0,.45);
        }

        60% {
            border-color:#00FF66;
            color:#00FF66;
            box-shadow:
            0 0 12px rgba(0,255,102,.45);
        }

        80% {
            border-color:#00CCFF;
            color:#00CCFF;
            box-shadow:
            0 0 12px rgba(0,204,255,.45);
        }

        100% {
            border-color:#FF0000;
            color:#FF0000;
            box-shadow:
            0 0 12px rgba(255,0,0,.45);
        }

    }


    .welcome-title,
    .camera-title,
    .stop-number-big,
    .stat-value-orange,
    .upload-title {

        animation:
        rgbGlow
        6s
        infinite
        linear !important;

    }

    .upload-card {

        animation:
        rgbGlow
        6s
        infinite
        linear !important;

    }

    """


# =========================================================
# CSS PRINCIPAL
# =========================================================

css_principal = """

<style>

.stApp {
    background-color: __BG__;
    color: __TEXT__;
}


.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 2rem !important;
    max-width: 780px;
}


/* HOME */

.hero-card {

    background:
    linear-gradient(
        145deg,
        __CARD__,
        __BG__
    );

    padding:
    28px
    20px
    20px;

    border-radius:
    22px;

    border:
    1px solid
    __BORDER__;

    text-align:
    center;

    box-shadow:
    0 10px 30px
    rgba(0,0,0,.35);

    margin-bottom:
    20px;

    position:
    relative;

    overflow:
    hidden;
}


.hero-card::before {

    content:'';

    position:
    absolute;

    top:0;
    left:0;
    right:0;

    height:
    4px;

    background:
    linear-gradient(
        90deg,
        #28a745,
        __ACCENT__
    );
}


.welcome-logo {

    width:
    85px;

    height:
    85px;

    object-fit:
    contain;

    margin-bottom:
    12px;

    filter:
    drop-shadow(
        0
        4px
        10px
        rgba(0,0,0,.5)
    );
}


.welcome-title {

    font-size:
    1.8rem;

    font-weight:
    900;

    color:
    __ACCENT__;

    letter-spacing:
    1px;

    margin-bottom:
    2px;
}


.welcome-subtitle {

    font-size:
    .8rem;

    color:
    #888;

    font-weight:
    700;

    letter-spacing:
    1.5px;

    text-transform:
    uppercase;
}


/* UPLOAD */

.upload-card {

    background-color:
    __CARD__;

    padding:
    22px;

    border-radius:
    20px;

    border:
    2px dashed
    __ACCENT__;

    text-align:
    center;

    margin-bottom:
    18px;

    box-shadow:
    0 8px 25px
    rgba(0,0,0,.25);
}


.upload-title {

    font-size:
    1.2rem;

    font-weight:
    800;

    color:
    __TEXT__;

    margin-bottom:
    6px;
}


.upload-sub {

    font-size:
    .85rem;

    color:
    #999;
}


/* PLACAR */

.stat-banner {

    background-color:
    __CARD__;

    border-radius:
    14px;

    padding:
    14px;

    border:
    1px solid
    __BORDER__;

    display:
    flex;

    justify-content:
    space-around;

    text-align:
    center;

    margin-bottom:
    10px;
}


.stat-value-green {

    font-size:
    1.5rem;

    font-weight:
    800;

    color:
    #28a745;
}


.stat-value-orange {

    font-size:
    1.5rem;

    font-weight:
    800;

    color:
    __ACCENT__;
}


.stat-label {

    font-size:
    .72rem;

    color:
    #AAA;

    font-weight:
    800;

    letter-spacing:
    .7px;
}


/* PARADA */

.custom-card {

    background-color:
    __CARD__;

    padding:
    18px;

    border-radius:
    14px;

    border-left:
    6px solid
    #28a745;

    margin:
    14px 0;

    border-top:
    1px solid
    __BORDER__;

    border-right:
    1px solid
    __BORDER__;

    border-bottom:
    1px solid
    __BORDER__;
}


.custom-card.duplicate {

    border-left-color:
    #FF9500;
}


.stop-number-big {

    font-size:
    3.5rem;

    font-weight:
    900;

    color:
    __ACCENT__;

    line-height:
    1;

    margin-bottom:
    10px;
}


.package-code {

    font-weight:
    800;

    word-break:
    break-all;
}


.address-text {

    font-size:
    .9rem;

    opacity:
    .85;

    margin-top:
    5px;
}


/* CÂMERA */

.camera-header {

    text-align:
    center;

    margin-top:
    12px;

    margin-bottom:
    5px;
}


.camera-title {

    font-size:
    1.1rem;

    font-weight:
    800;

    color:
    __ACCENT__;

    text-transform:
    uppercase;
}


.camera-sub {

    font-size:
    .8rem;

    color:
    #888;

    margin-bottom:
    10px;
}


__RGB__

</style>

"""


css_principal = (
    css_principal

    .replace(
        "__BG__",
        t["bg_app"]
    )

    .replace(
        "__TEXT__",
        t["text_app"]
    )

    .replace(
        "__CARD__",
        t["card_bg"]
    )

    .replace(
        "__BORDER__",
        t["border"]
    )

    .replace(
        "__ACCENT__",
        t["accent"]
    )

    .replace(
        "__RGB__",
        css_rgb_anim
    )
)


st.markdown(
    css_principal,
    unsafe_allow_html
