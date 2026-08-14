# PROCESSAMENTO DO PDF
if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "\n".join([p.extract_text() or "" for p in leitor.pages])
    linhas = texto.split('\n')
    
    stop_seq_contador = 0
    
    for idx_l, linha in enumerate(linhas):
        linha_limpa = linha.strip()
        if not linha_limpa:
            continue
            
        # 1. Busca códigos BR...
        cods_candidatos = re.findall(r'BR[A-Za-z0-9]+', linha_limpa, re.IGNORECASE)
        cods = [c for c in cods_candidatos if 12 <= len(c) <= 16]
        
        if cods:
            stop_seq_contador += 1
            
            # Tenta pegar o número da parada na própria linha ou na linha anterior
            # Padrão: número isolado de 1 a 3 dígitos antes do código ou palavras como Parada/Seq/P
            m_stop = re.search(r'(?:parada|seq|p\b|item|\#)\s*[:.-]?\s*(\d{1,3})', linha_limpa, re.IGNORECASE)
            
            if not m_stop and idx_l > 0:
                # Olha a linha imediatamente anterior
                m_stop = re.search(r'(?:parada|seq|p\b|item|\#)\s*[:.-]?\s*(\d{1,3})', linhas[idx_l-1], re.IGNORECASE)
            
            if not m_stop:
                # Procura número no começo da linha que não seja data
                m_num_inicio = re.search(r'^\s*(\d{1,3})\b(?!\s*[\/\-\:\.])', linha_limpa)
                if m_num_inicio:
                    num_cand = int(m_num_inicio.group(1))
                    # Se não for um valor absurdo que parece totalizador
                    if num_cand <= 500:
                        stop_pacote = num_cand
                    else:
                        stop_pacote = stop_seq_contador
                else:
                    stop_pacote = stop_seq_contador
            else:
                stop_pacote = int(m_stop.group(1))

            # Extrai endereço real; se não achar, usa um ID único para NÃO juntar tudo como mesmo endereço
            end_extraido = extrair_endereco_limpo(linha_limpa)
            if not end_extraido and idx_l > 0:
                end_extraido = extrair_endereco_limpo(linhas[idx_l-1])
                
            chave_endereco = end_extraido if end_extraido else f"unico_{cods[0]}"
            
            if chave_endereco not in mapa_rotas:
                mapa_rotas[chave_endereco] = []
                
            for c in cods:
                c_u = c.upper()
                todos_pacotes.add(c_u)
                if c_u not in mapa_rotas[chave_endereco]:
                    mapa_rotas[chave_endereco].append(c_u)
                    stop_correspondente[c_u] = stop_pacote
                    nome_exibicao[chave_endereco] = linha_limpa[:50]
ravessa)\s+([a-záàâãéèêíïóôõöúçñ\s]+?)\s*,\s*(\d+)', texto, re.IGNORECASE)
    if match:
        return f"{match.group(1)} {match.group(2)} {match.group(3)}".lower().strip()
    return None

# TELA PRINCIPAL
arquivo_pdf_main = None
if not arquivo_pdf_sidebar:
    st.markdown(f"""
    <div class="hero-card">
        <img src="{URL_DO_LOGO}" class="welcome-logo">
        <div class="welcome-title">{NOME_DO_APP}</div>
        <div class="welcome-subtitle">SISTEMA INTELIGENTE DE LOGÍSTICA</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-card">
        <div class="upload-title">📄 CARREGAR ROTA DA ENTREGA</div>
        <div class="upload-sub">Envie o arquivo PDF da sua rota para liberar a câmera e a bipagem</div>
    </div>
    """, unsafe_allow_html=True)
    
    arquivo_pdf_main = st.file_uploader("Selecione o PDF da Rota", type=["pdf"], key="pdf_main", label_visibility="collapsed")

arquivo_pdf = arquivo_pdf_sidebar or arquivo_pdf_main

mapa_rotas = {}
stop_correspondente = {}
nome_exibicao = {}
todos_pacotes = set()

# PROCESSAMENTO DO PDF
if arquivo_pdf:
    leitor = PdfReader(arquivo_pdf)
    texto = "".join([p.extract_text() + "\n" for p in leitor.pages])
    linhas = texto.split('\n')
    stop_atual = 0
    
    for linha in linhas:
        m_stop = re.search(r'(?:parada|seq|p\b|\#)\s*[:.-]?\s*(\d{1,3})', linha, re.IGNORECASE)
        if not m_stop:
            m_stop = re.search(r'^\s*(\d{1,3})(?!\s*[\/\-]\s*\d)', linha)
            
        if m_stop:
            stop_atual = int(m_stop.group(1))
        
        cods_candidatos = re.findall(r'BR[A-Za-z0-9]+', linha, re.IGNORECASE)
        cods = [c for c in cods_candidatos if 12 <= len(c) <= 16]
        
        if cods:
            endereco = extrair_endereco_limpo(linha) or f"desconhecido_{stop_atual}"
            if endereco not in mapa_rotas:
                mapa_rotas[endereco] = []
            for c in cods:
                c_u = c.upper()
                todos_pacotes.add(c_u)
                if c_u not in mapa_rotas[endereco]:
                    mapa_rotas[endereco].append(c_u)
                    stop_correspondente[c_u] = stop_atual
                    nome_exibicao[endereco] = linha[:50]

# TELA DE EXECUÇÃO
if arquivo_pdf:
    bipados = len(st.session_state.pacotes_bipados)
    total = len(todos_pacotes)
    faltam = total - bipados
    
    banner_html = f"""<div class="stat-banner">
    <div>
        <div class="stat-value-green">{bipados} / {total}</div>
        <div class="stat-label">BIPADOS</div>
    </div>
    <div>
        <div class="stat-value-orange">{faltam}</div>
        <div class="stat-label">FALTAM</div>
    </div>
</div>"""
    st.markdown(banner_html, unsafe_allow_html=True)
    
    with st.expander("🤖 Ver pacotes no mesmo endereço / duplos"):
        encontrou_duplo = False
        for end, pacotes in mapa_rotas.items():
            if len(pacotes) > 1:
                encontrou_duplo = True
                st.markdown(f"🚨 **{end.title()}**: `{len(pacotes)} pcts` (Parada P{stop_correspondente.get(pacotes[0])})")
        if not encontrou_duplo:
            st.info("Nenhum endereço com múltiplos pacotes nesta rota.")

    st.markdown("""<div class="camera-header">
    <div class="camera-title">📸 BIPAR PACOTE</div>
    <div class="camera-sub">Aponte a câmera para o QR Code do pacote</div>
</div>""", unsafe_allow_html=True)

    code = qrcode_scanner(key="s1")
    
    st.markdown("#### ⌨️ Digitar código manualmente")
    input_code = st.text_input("", placeholder="BR123456789012", label_visibility="collapsed")
    
    final_code = code or input_code
    
    if final_code:
        cod = final_code.upper().strip()
        achou = False
        for endereco, lista in mapa_rotas.items():
            if cod in lista:
                st.session_state.pacotes_bipados.add(cod)
                num_p = stop_correspondente.get(cod, "?")
                
                components.html("<script>playBeep();</script>", height=0)
                
                st.markdown(f'<div class="custom-card"><div class="stop-number-big">P{num_p}</div><div>📍 Pacote: {cod}</div></div>', unsafe_allow_html=True)
                
                if len(lista) > 1:
                    outros_stops = [f"P{stop_correspondente.get(p, '?')}" for p in lista if p != cod]
                    st.warning(f"⚠️ **MESMO ENDEREÇO!** Pegue também o(s) pacote(s) da(s): " + ", ".join(outros_stops))

                if usar_audio:
                    fala_texto = f"{num_p}"
                    if len(lista) > 1:
                        fala_texto += " Atenção!"
                        
                    pitch_val = "1.0"
                    rate_val = "1.0"
                    
                    if "Pica-Pau" in tipo_voz:
                        fala_texto = f"He-he-he-he! {num_p}!"
                        if len(lista) > 1:
                            fala_texto += " Atenção!"
                        pitch_val = "1.8"
                        rate_val = "1.45"
                    elif "Masculina" in tipo_voz:
                        pitch_val = "0.6"
                        rate_val = "0.95"
                    elif "Rápida" in tipo_voz:
                        pitch_val = "1.1"
                        rate_val = "1.35"
                    elif "Locutor" in tipo_voz:
                        pitch_val = "0.7"
                        rate_val = "0.9"
                    elif "Vilão" in tipo_voz:
                        pitch_val = "0.3"
                        rate_val = "0.8"
                    elif "Esquilo" in tipo_voz:
                        pitch_val = "2.0"
                        rate_val = "1.4"

                    js_audio = (
                        "<script>"
                        "window.speechSynthesis.cancel();"
                        f"var msg = new SpeechSynthesisUtterance('{fala_texto}');"
                        "msg.lang = 'pt-BR';"
                        f"msg.pitch = {pitch_val};"
                        f"msg.rate = {rate_val};"
                        "window.speechSynthesis.speak(msg);"
                        "</script>"
                    )
                    components.html(js_audio, height=0)

                achou = True
                break
        if not achou:
            st.error("❌ Código não encontrado!")
