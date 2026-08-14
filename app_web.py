import csv
import hashlib
import html
import io
import json
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import streamlit as st
import streamlit.components.v1 as components
from pypdf import PdfReader
from streamlit_qrcode_scanner import qrcode_scanner


# =========================================================
# CONFIGURAÇÕES DO APP
# =========================================================

NOME_DO_APP = "PACOTE É MATO"

URL_DO_LOGO = (
    "https://cdn-icons-png.flaticon.com/512/3062/3062634.png"
)

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
        "ultimo_codigo_scanner": None,
        "ultimo_resultado": None,
        "ultimo_evento_ts": 0.0,
        "ultima_assinatura_evento": None,
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

    nome_exibicao: Dict[str, str]

    todos_pacotes: Set[str]

    avisos: List[str]


# =========================================================
# NORMALIZAÇÃO
# =========================================================

def normalizar_espacos(texto):

    return re.sub(
        r"\s+",
        " ",
        texto or ""
    ).strip()


# =========================================================
# IDENTIFICAR PARADA
# =========================================================

def extrair_stop(linha):

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


# =========================================================
# EXTRAIR ENDEREÇO
# =========================================================

def extrair_endereco_limpo(texto):

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
        rf"\b({tipo})"
        rf"\s+"
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


# =========================================================
# EXTRAIR CÓDIGOS BR
# =========================================================

def extrair_codigos(texto):

    candidatos = re.findall(
        r"\bBR[A-Za-z0-9]{10,14}\b",
        texto or "",
        re.IGNORECASE,
    )

    vistos = set()

    resultado = []

    for codigo in candidatos:

        codigo = codigo.upper()

        if codigo not in vistos:

            vistos.add(codigo)

            resultado.append(codigo)

    return resultado


# =========================================================
# LEITURA DO PDF
# =========================================================

@st.cache_data(show_spinner=False)
def ler_rota_pdf(pdf_bytes):

    mapa_rotas = {}

    pacote_para_endereco = {}

    stop_correspondente = {}

    nome_exibicao = {}

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
        start=1,
    ):

        try:

            txt = pagina.extract_text() or ""

            paginas.append(txt)

            if not txt.strip():

                avisos.append(
                    f"Página {numero} sem texto extraível."
                )

        except Exception:

            paginas.append("")

            avisos.append(
                f"Não foi possível extrair o texto da página {numero}."
            )

    texto = "\n".join(paginas)

    linhas = texto.splitlines()

    stop_atual = None

    for i, linha in enumerate(linhas):

        # -------------------------
        # Detecta parada
        # -------------------------

        stop_detectado = extrair_stop(
            linha
        )

        if stop_detectado is not None:

            stop_atual = stop_detectado

        # -------------------------
        # Detecta códigos
        # -------------------------

        codigos = extrair_codigos(
            linha
        )

        if not codigos:
            continue

        # -------------------------
        # Procura endereço próximo
        # -------------------------

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

        # Caso não identifique o endereço
        if not endereco:

            endereco = (
                f"endereco_nao_identificado_"
                f"p{stop_atual or 0}_{i}"
            )

        if endereco not in mapa_rotas:

            mapa_rotas[endereco] = []

        # -------------------------
        # Adiciona pacotes
        # -------------------------

        for codigo in codigos:

            # Evita duplicidade no PDF
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

            nome_exibicao[
                endereco
            ] = contexto[:100]

    # -------------------------
    # Caso nenhum pacote seja achado
    # -------------------------

    if not todos_pacotes:

        avisos.append(
            "Nenhum código BR foi encontrado. "
            "Se o PDF for uma imagem ou PDF escaneado, "
            "pode ser necessário usar OCR."
        )

    return RouteData(

        mapa_rotas=mapa_rotas,

        pacote_para_endereco=pacote_para_endereco,

        stop_correspondente=stop_correspondente,

        nome_exibicao=nome_exibicao,

        todos_pacotes=todos_pacotes,

        avisos=avisos,
    )


# =========================================================
# CONFIGURAÇÃO DAS VOZES
# =========================================================

def configuracao_voz(
    tipo_voz,
    numero_parada,
    mesmo_endereco
):

    fala = str(numero_parada)

    pitch = 1.0

    rate = 1.0

    # -------------------------
    # Mesmo endereço
    # -------------------------

    if mesmo_endereco:

        fala += (
            ". Atenção, mesmo endereço."
        )

    # -------------------------
    # Pica-Pau
    # -------------------------

    if "Pica-Pau" in tipo_voz:

        fala = (
            f"He he he! {numero_parada}!"
        )

        if mesmo_endereco:

            fala += " Atenção!"

        pitch = 1.8

        rate = 1.45

    # -------------------------
    # Masculina
    # -------------------------

    elif "Masculina" in tipo_voz:

        pitch = 0.65

        rate = 0.95

    # -------------------------
    # Rápida
    # -------------------------

    elif "Rápida" in tipo_voz:

        pitch = 1.1

        rate = 1.35

    # -------------------------
    # Locutor
    # -------------------------

    elif "Locutor" in tipo_voz:

        pitch = 0.75

        rate = 0.90

    # -------------------------
    # Vilão
    # -------------------------

    elif "Vilão" in tipo_voz:

        pitch = 0.40

        rate = 0.82

    # -------------------------
    # Esquilo
    # -------------------------

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

def tocar_bip_e_falar(fala, pitch, rate, usar_audio):

    fala_js = json.dumps(
        fala,
        ensure_ascii=False
    )

    parte_voz = ""

    if usar_audio:

        parte_voz = (
            "try {"
            "window.speechSynthesis.cancel();"
            "const msg = new SpeechSynthesisUtterance(" + fala_js + ");"
            "msg.lang = 'pt-BR';"
            "msg.pitch = " + str(float(pitch)) + ";"
            "msg.rate = " + str(float(rate)) + ";"
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

                osc.type = 'sine';

                osc.frequency.setValueAtTime(
                    880,
                    ctx.currentTime
                );

                gain.gain.setValueAtTime(
                    0.15,
                    ctx.currentTime
                );

                osc.connect(gain);

                gain.connect(
                    ctx.destination
                );

                osc.start();

                osc.stop(
                    ctx.currentTime + 0.10
                );

            }

        } catch (e) {}

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
# PROCESSAMENTO DO CÓDIGO BIPADO
# =========================================================

def processar_codigo(
    codigo,
    rota
):

    codigo = (
        codigo or ""
    ).upper().strip()

    if not codigo:

        return {
            "status": "vazio"
        }

    # -------------------------
    # Código não está na rota
    # -------------------------

    if codigo not in rota.todos_pacotes:

        return {

            "status": "nao_encontrado",

            "codigo": codigo,
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
        in st.session_state.pacotes_bipados
    )

    # Adiciona ao conjunto
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

    # -------------------------
    # Tema
    # -------------------------

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

    # -------------------------
    # PDF
    # -------------------------

    arquivo_pdf_sidebar = (
        st.file_uploader(

            "📂 Enviar PDF da Rota",

            type=["pdf"],

            key="pdf_sidebar",
        )
    )

    # -------------------------
    # Voz
    # -------------------------

    usar_audio = st.toggle(

        "🔊 Falar Número da Parada",

        value=True
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

    # -------------------------
    # Reset da rota
    # -------------------------

    if st.button(

        "🔄 Zerar Rota Atual",

        use_container_width=True
    ):

        st.session_state.pacotes_bipados = (
            set()
        )

        st.session_state.ultimo_codigo_scanner = (
            None
        )

        st.session_state.ultimo_resultado = (
            None
        )

        st.session_state.ultima_assinatura_evento = (
            None
        )

        st.rerun()


# =========================================================
# TEMAS
# =========================================================

estilos_temas = {

    "Preto (Dark)": {

        "bg_app":
            "#121212",

        "text_app":
            "#FFFFFF",

        "card_bg":
            "#1E1E1E",

        "border":
            "#333333",

        "accent":
            "#FF9500",
    },


    "RGB Gamer 🌈": {

        "bg_app":
            "#0D0D11",

        "text_app":
            "#FFFFFF",

        "card_bg":
            "#16161D",

        "border":
            "#222230",

        "accent":
            "#00FFCC",
    },


    "Branco (Light)": {

        "bg_app":
            "#F5F5F7",

        "text_app":
            "#1D1D1F",

        "card_bg":
            "#FFFFFF",

        "border":
            "#E5E5EA",

        "accent":
            "#007AFF",
    },


    "Cinza": {

        "bg_app":
            "#2C2C2E",

        "text_app":
            "#F2F2F7",

        "card_bg":
            "#3A3A3C",

        "border":
            "#48484A",

        "accent":
            "#FF9500",
    },


    "Azul": {

        "bg_app":
            "#0B192C",

        "text_app":
            "#E0F2FE",

        "card_bg":
            "#1E3E62",

        "border":
            "#0087D1",

        "accent":
            "#38BDF8",
    },


    "Vermelho": {

        "bg_app":
            "#1A0000",

        "text_app":
            "#FFE5E5",

        "card_bg":
            "#330000",

        "border":
            "#800000",

        "accent":
            "#FF4D4D",
    },
}


t = estilos_temas.get(

    tema_cor,

    estilos_temas[
        "Preto (Dark)"
    ]
)


# =========================================================
# ANIMAÇÃO RGB
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


    .upload-card,
    div[data-testid="stCustomComponentV1"] {

        animation:
        rgbGlow
        6s
        infinite
        linear !important;

    }

    """


# =========================================================
# CSS DO APP
# =========================================================

st.markdown(

    f"""

<style>


.stApp {{

    background-color:
    {t['bg_app']};

    color:
    {t['text_app']};

}}


.block-container {{

    padding-top:
    1.2rem !important;

    padding-bottom:
    2rem !important;

    max-width:
    780px;

}}


/* ============================
   TELA INICIAL
============================ */

.hero-card {{

    background:

    linear-gradient(

        145deg,

        {t['card_bg']},

        {t['bg_app']}

    );

    padding:

    28px
    20px
    20px;

    border-radius:
    22px;

    border:
    1px solid
    {t['border']};

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

}}


.hero-card::before {{

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

        {t['accent']}

    );

}}


.welcome-logo {{

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

}}


.welcome-title {{

    font-size:
    1.8rem;

    font-weight:
    900;

    color:
    {t['accent']};

    letter-spacing:
    1px;

    margin-bottom:
    2px;

}}


.welcome-subtitle {{

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

}}


/* ============================
   UPLOAD
============================ */

.upload-card {{

    background-color:
    {t['card_bg']};

    padding:
    22px;

    border-radius:
    20px;

    border:

    2px dashed
    {t['accent']};

    text-align:
    center;

    margin-bottom:
    18px;

    box-shadow:

    0 8px 25px
    rgba(0,0,0,.25);

}}


.upload-title {{

    font-size:
    1.2rem;

    font-weight:
    800;

    color:
    {t['text_app']};

    margin-bottom:
    6px;

}}


.upload-sub {{

    font-size:
    .85rem;

    color:
    #999;

}}


/* ============================
   ESTATÍSTICAS
============================ */

.stat-banner {{

    background-color:
    {t['card_bg']};

    border-radius:
    14px;

    padding:
    14px;

    border:

    1px solid
    {t['border']};

    display:
    flex;

    justify-content:
    space-around;

    text-align:
    center;

    margin-bottom:
    10px;

}}


.stat-value-green {{

    font-size:
    1.5rem;

    font-weight:
    800;

    color:
    #28a745;

}}


.stat-value-orange {{

    font-size:
    1.5rem;

    font-weight:
    800;

    color:
    {t['accent']};

}}


.stat-label {{

    font-size:
    .72rem;

    color:
    #AAA;

    font-weight:
    800;

    letter-spacing:
    .7px;

}}


/* ============================
   PARADA
============================ */

.custom-card {{

    background-color:
    {t['card_bg']};

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
    {t['border']};

    border-right:
    1px solid
    {t['border']};

    border-bottom:
    1px solid
    {t['border']};

}}


.custom-card.duplicate {{

    border-left-color:
    #FF9500;

}}


.stop-number-big {{

    font-size:
    3.5rem;

    font-weight:
    900;

    color:
    {t['accent']};

    line-height:
    1;

    margin-bottom:
    10px;

}}


.package-code {{

    font-weight:
    800;

    word-break:
    break-all;

}}


.address-text {{

    font-size:
    .9rem;

    opacity:
    .85;

    margin-top:
    5px;

}}


/* ============================
   CÂMERA
============================ */

.camera-header {{

    text-align:
    center;

    margin-top:
    12px;

    margin-bottom:
    5px;

}}


.camera-title {{

    font-size:
    1.1rem;

    font-weight:
    800;

    color:
    {t['accent']};

    text-transform:
    uppercase;

}}


.camera-sub {{

    font-size:
    .8rem;

    color:
    #888;

    margin-bottom:
    10px;

}}


div[data-testid="stCustomComponentV1"] {{

    width:
    100%;

    min-height:
    350px;

    display:
    flex;

    justify-content:
    center;

    align-items:
    center;

    border-radius:
    16px;

    border:

    2px solid
    {t['accent']};

    background:
    #000;

    margin-bottom:
    15px;

    overflow:
    hidden;

    position:
    relative;

}}


iframe {{

    width:
    100%;

    min-height:
    350px;

    border:
    none;

}}


{css_rgb_anim}


</style>

""",

    unsafe_allow_html=True,
)


# =========================================================
# CUSTOMIZAÇÃO DA CÂMERA
# =========================================================

js_camera = f"""

<script>

(function() {{

    function aplicarMelhorias() {{

        const iframes =
            window.parent.document
            .querySelectorAll(
                'iframe'
            );


        iframes.forEach(
            function(frame) {{

            try {{

                const doc =
                    frame.contentDocument ||
                    frame.contentWindow.document;


                if (!doc)
                    return;


                const video =
                    doc.querySelector(
                        'video'
                    );


                if (!video)
                    return;


                /* =====================
                   CSS DA CÂMERA
                ====================== */

                if (
                    !doc.getElementById(
                        'pacote-mato-camera-style'
                    )
                ) {{

                    const s =
                        doc.createElement(
                            'style'
                        );

                    s.id =
                        'pacote-mato-camera-style';


                    s.innerHTML = `

                        #qr-shaded-region {{

                            border:
                            none !important;

                        }}


                        #qr-shaded-region * {{

                            display:
                            none !important;

                        }}


                        video {{

                            object-fit:
                            cover !important;

                            width:
                            100% !important;

                            height:
                            100% !important;

                        }}


                        body {{

                            overflow:
                            hidden !important;

                        }}

                    `;


                    doc.head.appendChild(
                        s
                    );

                }}


                /* =====================
                   MIRA
                ====================== */

                if (
                    !doc.getElementById(
                        'custom-target-overlay'
                    )
                ) {{

                    const overlay =
                        doc.createElement(
                            'div'
                        );


                    overlay.id =
                        'custom-target-overlay';


                    overlay.style.cssText =

                    'position:absolute;' +
                    'top:15%;' +
                    'left:10%;' +
                    'right:10%;' +
                    'bottom:15%;' +
                    'pointer-events:none;' +
                    'z-index:90;';


                    overlay.innerHTML = `


                    <div style="
                    position:absolute;
                    top:0;
                    left:0;
                    width:35px;
                    height:35px;
                    border-top:5px solid #FFF;
                    border-left:5px solid #FFF;
                    border-top-left-radius:4px;
                    ">
                    </div>


                    <div style="
                    position:absolute;
                    top:0;
                    right:0;
                    width:35px;
                    height:35px;
                    border-top:5px solid #FFF;
                    border-right:5px solid #FFF;
                    border-top-right-radius:4px;
                    ">
                    </div>


                    <div style="
                    position:absolute;
                    bottom:0;
                    left:0;
                    width:35px;
                    height:35px;
                    border-bottom:5px solid #FFF;
                    border-left:5px solid #FFF;
                    border-bottom-left-radius:4px;
                    ">
                    </div>


                    <div style="
                    position:absolute;
                    bottom:0;
                    right:0;
                    width:35px;
                    height:35px;
                    border-bottom:5px solid #FFF;
                    border-right:5px solid #FFF;
                    border-bottom-right-radius:4px;
                    ">
                    </div>


                    `;


                    doc.body.appendChild(
                        overlay
                    );

                }}


                /* =====================
                   FLASH
                ====================== */

                if (
                    !doc.getElementById(
                        'btn-flash'
                    )
                ) {{

                    const btn =
                        doc.createElement(
                            'button'
                        );


                    btn.id =
                        'btn-flash';


                    btn.innerHTML =
                        '🔦 Flash';


                    btn.style.cssText =

                    'position:absolute;' +
                    'top:10px;' +
                    'right:10px;' +
                    'z-index:999;' +
                    'background:rgba(0,0,0,.75);' +
                    'color:#FFF;' +
                    'border:1px solid {t["accent"]};' +
                    'padding:7px 12px;' +
                    'border-radius:16px;' +
                    'font-weight:bold;' +
                    'cursor:pointer;';


                    btn.dataset.on =
                        '0';


                    btn.onclick =
                    async function() {{

                        try {{

                            if (
                                !video.srcObject
                            ) {{

                                throw new Error(
                                    'Câmera ainda não iniciou'
                                );

                            }}


                            const track =
                                video
                                .srcObject
                                .getVideoTracks()[0];


                            if (!track) {{

                                throw new Error(
                                    'Câmera não encontrada'
                                );

                            }}


                            const caps =
                                track.getCapabilities
                                ?
                                track.getCapabilities()
                                :
                                {{}};


                            if (!caps.torch) {{

                                btn.innerHTML =
                                    '🚫 Sem flash';

                                btn.disabled =
                                    true;

                                return;

                            }}


                            const ligar =
                                btn.dataset.on
                                !==
                                '1';


                            await track.applyConstraints(
                                {{

                                    advanced:
                                    [
                                        {{
                                            torch:
                                            ligar
                                        }}
                                    ]

                                }}
                            );


                            btn.dataset.on =
                                ligar
                                ?
                                '1'
                                :
                                '0';


                            btn.innerHTML =
                                ligar
                                ?
                                '⚡ Flash ON'
                                :
                                '🔦 Flash';


                        }}

                        catch (e) {{

                            btn.innerHTML =
                                '🚫 Sem flash';

                        }}

                    }};


                    doc.body.appendChild(
                        btn
                    );

                }}


            }}

            catch (e) {{}}


        }});

    }


    setInterval(
        aplicarMelhorias,
        500
    );


}})();

</script>

"""


components.html(
    js_camera,
    height=0
)


# =========================================================
# TELA PRINCIPAL
# =========================================================

arquivo_pdf_main = None


if not arquivo_pdf_sidebar:

    st.markdown(

        f"""

        <div class="hero-card">

            <img

            src="{URL_DO_LOGO}"

            class="welcome-logo"

            >


            <div class="welcome-title">

                {NOME_DO_APP}

            </div>


            <div class="welcome-subtitle">

                SISTEMA INTELIGENTE DE LOGÍSTICA

            </div>


        </div>

        """,

        unsafe_allow_html=True
    )


    st.markdown(

        """

        <div class="upload-card">

            <div class="upload-title">

                📄 CARREGAR ROTA DA ENTREGA

            </div>


            <div class="upload-sub">

                Envie o PDF da sua rota
                para liberar a câmera
                e iniciar a bipagem.

            </div>


        </div>

        """,

        unsafe_allow_html=True
    )


    arquivo_pdf_main = (
        st.file_uploader(

            "Selecione o PDF da Rota",

            type=["pdf"],

            key="pdf_main",

            label_visibility=
                "collapsed",
        )
    )


# PDF usado
arquivo_pdf = (

    arquivo_pdf_sidebar

    or

    arquivo_pdf_main
)


# Caso nenhum PDF
if not arquivo_pdf:

    st.info(
        "📦 Carregue um PDF para começar."
    )

    st.stop()


# =========================================================
# IDENTIFICA A ROTA
# =========================================================

pdf_bytes = (
    arquivo_pdf.getvalue()
)


rota_id = (

    hashlib
    .sha256(pdf_bytes)
    .hexdigest()[:16]

)


# =========================================================
# CASO TROQUE O PDF
# =========================================================

if (
    st.session_state.rota_id
    !=
    rota_id
):

    st.session_state.rota_id = (
        rota_id
    )

    st.session_state.pacotes_bipados = (
        set()
    )

    st.session_state.ultimo_codigo_scanner = (
        None
    )

    st.session_state.ultimo_resultado = (
        None
    )

    st.session_state.ultima_assinatura_evento = (
        None
    )


# =========================================================
# LÊ A ROTA
# =========================================================

try:

    with st.spinner(
        "Lendo a rota..."
    ):

        rota = ler_rota_pdf(
            pdf_bytes
        )


except Exception as exc:

    st.error(
        f"❌ Erro ao ler o PDF: {exc}"
    )

    st.stop()


# =========================================================
# AVISOS
# =========================================================

for aviso in rota.avisos:

    st.warning(
        aviso
    )


if not rota.todos_pacotes:

    st.stop()


# =========================================================
# LIMPA BIPAGENS INVÁLIDAS
# =========================================================

st.session_state.pacotes_bipados = {

    codigo

    for codigo
    in st.session_state.pacotes_bipados

    if codigo
    in rota.todos_pacotes

}


# =========================================================
# ESTATÍSTICAS
# =========================================================

bipados = len(
    st.session_state.pacotes_bipados
)


total = len(
    rota.todos_pacotes
)


faltam = max(
    total - bipados,
    0
)


percentual = (

    bipados / total

    if total

    else 0.0
)


st.markdown(

    f"""

    <div class="stat-banner">

        <div>

            <div class="stat-value-green">

                {bipados} / {total}

            </div>


            <div class="stat-label">

                BIPADOS

            </div>

        </div>


        <div>

            <div class="stat-value-orange">

                {faltam}

            </div>


            <div class="stat-label">

                FALTAM

            </div>

        </div>


    </div>

    """,

    unsafe_allow_html=True
)


# Barra de progresso
st.progress(
    percentual
)


if faltam == 0 and total > 0:

    st.success(
        "🏁 Rota 100% bipada!"
    )


# =========================================================
# PACOTES NO MESMO ENDEREÇO
# =========================================================

with st.expander(
    "🤖 Ver pacotes no mesmo endereço / duplos"
):

    grupos = [

        (
            endereco,
            pacotes
        )

        for endereco,
        pacotes
        in rota.mapa_rotas.items()

        if len(pacotes) > 1

    ]


    if not grupos:

        st.info(
            "Nenhum endereço com múltiplos pacotes nesta rota."
        )


    else:

        for endereco, pacotes in grupos:

            stops = sorted({

                rota.stop_correspondente.get(
                    p,
                    0
                )

                for p in pacotes

                if rota.stop_correspondente.get(
                    p,
                    0
                )

            })


            stops_txt = (

                ", ".join(
                    f"P{x}"
                    for x in stops
                )

                if stops

                else
                "Parada não identificada"

            )


            status = sum(

                1

                for p
                in pacotes

                if p
                in st.session_state.pacotes_bipados

            )


            st.markdown(

                f"""
                🚨 **{html.escape(endereco.title())}**

                `{len(pacotes)} pacotes`

                {stops_txt}

                ✅ {status}/{len(pacotes)}
                """
            )


# =========================================================
# CÂMERA
# =========================================================

st.markdown(

    """

    <div class="camera-header">

        <div class="camera-title">

            📸 BIPAR PACOTE

        </div>


        <div class="camera-sub">

            Aponte a câmera para
            o QR Code do pacote.

        </div>


    </div>

    """,

    unsafe_allow_html=True
)


# Scanner
code_scanner = qrcode_scanner(
    key="scanner_rota"
)


# =========================================================
# DIGITAÇÃO MANUAL
# =========================================================

st.markdown(
    "#### ⌨️ Digitar código manualmente"
)


with st.form(
    "form_codigo_manual",
    clear_on_submit=True
):

    input_code = st.text_input(

        "Código do pacote",

        placeholder=
            "BR123456789012",

        label_visibility=
            "collapsed",
    )


    enviar_manual = (
        st.form_submit_button(

            "🔎 Buscar código",

            use_container_width=True
        )
    )


# =========================================================
# DEFINE EVENTO DE LEITURA
# =========================================================

codigo_evento = None

origem_evento = None


# =========================================================
# QR CODE
# =========================================================

if code_scanner:

    scanner_limpo = (

        str(code_scanner)

        .upper()

        .strip()
    )


    if (
        scanner_limpo

        and

        scanner_limpo
        !=
        st.session_state.ultimo_codigo_scanner
    ):

        codigo_evento = (
            scanner_limpo
        )

        origem_evento = (
            "scanner"
        )

        st.session_state.ultimo_codigo_scanner = (
            scanner_limpo
        )


# =========================================================
# MANUAL
# =========================================================

if (
    enviar_manual
    and
    input_code.strip()
):

    codigo_evento = (

        input_code

        .upper()

        .strip()
    )

    origem_evento = (
        "manual"
    )


# =========================================================
# PROTEÇÃO CONTRA DUPLO EVENTO
# =========================================================

if codigo_evento:

    agora = time.time()


    assinatura_evento = (

        f"{origem_evento}:"
        f"{codigo_evento}"

    )


    ultimo = (

        st.session_state.get(
            "ultima_assinatura_evento"
        )
    )


    ultimo_ts = (

        st.session_state.get(
            "ultimo_evento_ts",
            0.0
        )
    )


    if (

        assinatura_evento
        !=
        ultimo

        or

        (
            agora
            -
            ultimo_ts
        )
        >
        1.2
    ):

        resultado = processar_codigo(

            codigo_evento,

            rota
        )


        st.session_state.ultimo_resultado = (
            resultado
        )


        st.session_state.ultima_assinatura_evento = (
            assinatura_evento
        )


        st.session_state.ultimo_evento_ts = (
            agora
        )


        # =====================
        # TOCA SOM APENAS
        # QUANDO É NOVO
        # =====================

        if (
            resultado.get(
                "status"
            )
            ==
            "ok"
        ):

            parada = (
                resultado.get(
                    "parada",
                    0
                )
            )


            mesmo_endereco = (

                len(

                    resultado.get(
                        "pacotes_mesmo_endereco",
                        []
                    )

                )

                > 1
            )


            fala, pitch, rate = (
                configuracao_voz(

                    tipo_voz,

                    parada,

                    mesmo_endereco
                )
            )


            tocar_bip_e_falar(

                fala,

                pitch,

                rate,

                usar_audio
            )


# =========================================================
# RESULTADO MAIS RECENTE
# =========================================================

resultado = (
    st.session_state.ultimo_resultado
)


if resultado:

    status = (
        resultado.get(
            "status"
        )
    )


    # =====================================================
    # NÃO ENCONTRADO
    # =====================================================

    if (
        status
        ==
        "nao_encontrado"
    ):

        st.error(

            "❌ Código não encontrado na rota: "
            f"{resultado.get('codigo', '')}"

        )


    # =====================================================
    # ENCONTRADO
    # =====================================================

    elif status in {
        "ok",
        "repetido"
    }:

        codigo = html.escape(

            resultado.get(
                "codigo",
                ""
            )
        )


        parada = (
            resultado.get(
                "parada",
                0
            )
        )


        parada_txt = (

            f"P{parada}"

            if parada

            else
            "P?"
        )


        endereco = (
            resultado.get(
                "endereco",
                ""
            )
        )


        # Endereço visual
        if endereco.startswith(
            "endereco_nao_identificado_"
        ):

            endereco_legivel = (
                "Endereço não identificado"
            )

        else:

            endereco_legivel = (
                endereco.title()
            )


        classe_extra = (

            " duplicate"

            if status
            ==
            "repetido"

            else ""
        )


        # =================================================
        # CARD DA PARADA
        # =================================================

        st.markdown(

            f"""

            <div class="custom-card{classe_extra}">

                <div class="stop-number-big">

                    {parada_txt}

                </div>


                <div>

                    📦 Pacote:

                    <span class="package-code">

                        {codigo}

                    </span>

                </div>


                <div class="address-text">

                    📍
                    {html.escape(endereco_legivel)}

                </div>


            </div>

            """,

            unsafe_allow_html=True
        )


        # =================================================
        # PACOTE REPETIDO
        # =================================================

        if (
            status
            ==
            "repetido"
        ):

            st.warning(

                "⚠️ Esse pacote já tinha sido bipado anteriormente."

            )


        # =================================================
        # MESMO ENDEREÇO
        # =================================================

        lista_mesmo_endereco = (

            resultado.get(

                "pacotes_mesmo_endereco",

                []
            )
        )


        if (
            len(lista_mesmo_endereco)
            > 1
        ):

            outros = [

                p

                for p
                in lista_mesmo_endereco

                if p
                !=
                resultado.get(
                    "codigo"
                )

            ]


            pendentes_mesmo_endereco = [

                p

                for p
                in outros

                if p
                not in
                st.session_state.pacotes_bipados

            ]


            # =============================================
            # TEM OUTRO PACOTE
            # =============================================

            if pendentes_mesmo_endereco:

                detalhes = []


                for p in pendentes_mesmo_endereco:

                    stop = (

                        rota.stop_correspondente.get(
                            p,
                            0
                        )

                    )


                    if stop:

                        stop_txt = (
                            "P"
                            +
                            str(stop)
                        )

                    else:

                        stop_txt = (
                            "P?"
                        )


                    detalhes.append(

                        f"{p} ({stop_txt})"

                    )


                st.warning(

                    "⚠️ **MESMO ENDEREÇO!** "
                    "Ainda falta pegar: "
                    +
                    ", ".join(
                        detalhes
                    )

                )


            # =============================================
            # TODOS JÁ PEGOS
            # =============================================

            else:

                st.success(

                    "✅ Todos os pacotes deste endereço já foram bipados."

                )


# =========================================================
# PACOTES PENDENTES
# =========================================================

with st.expander(
    "📋 Ver pacotes pendentes"
):

    pendentes = sorted(

        rota.todos_pacotes
        -
        st.session_state.pacotes_bipados

    )


    if not pendentes:

        st.success(

            "Nenhum pacote pendente."

        )


    else:

        for codigo in pendentes:

            parada = (

                rota.stop_correspondente.get(
                    codigo,
                    0
                )

            )


            endereco = (

                rota.pacote_para_endereco.get(
                    codigo,
                    ""
                )

            )


            if endereco.startswith(
                "endereco_nao_identificado_"
            ):

                endereco_txt = (

                    "Endereço não identificado"

                )

            else:

                endereco_txt = (

                    endereco.title()

                )


            if parada:

                parada_txt = (
                    f"P{parada}"
                )

            else:

                parada_txt = (
                    "P?"
                )


            st.write(

                f"• {parada_txt} "
                f"— `{codigo}` "
                f"— {endereco_txt}"

            )


# =========================================================
# RELATÓRIO CSV
# =========================================================

saida = io.StringIO()


writer = csv.writer(
    saida
)


writer.writerow(

    [
        "codigo",
        "parada",
        "endereco",
        "status",
    ]

)


# Ordena por parada
pacotes_ordenados = sorted(

    rota.todos_pacotes,

    key=lambda x: (

        rota.stop_correspondente.get(
            x,
            9999
        ),

        x
    )
)


for codigo in pacotes_ordenados:

    endereco = (

        rota.pacote_para_endereco.get(
            codigo,
            ""
        )

    )


    status_pacote = (

        "BIPADO"

        if codigo
        in st.session_state.pacotes_bipados

        else
        "PENDENTE"

    )


    writer.writerow(

        [
            codigo,

            rota.stop_correspondente.get(
                codigo,
                0
            ),

            endereco,

            status_pacote,
        ]

    )


# =========================================================
# DOWNLOAD RELATÓRIO
# =========================================================

st.download_button(

    "⬇️ Baixar relatório da rota (CSV)",

    data=(
        saida
        .getvalue()
        .encode(
            "utf-8-sig"
        )
    ),

    file_name=(
        f"rota_{rota_id}.csv"
    ),

    mime="text/csv",

    use_container_width=True,
)
