# ÁUDIO (VOZ) - AGORA APENAS O NÚMERO E O AVISO DE ATENÇÃO
if usar_audio:
    pitch_val = "1.0"
    rate_val = "1.0"
    
    if "Pica-Pau" in tipo_voz:
        fala_texto = f"He-he-he-he! {num_p}!"
        if len(lista) > 1: fala_texto += " Atenção!"
        pitch_val = "1.8"
        rate_val = "1.45"
    else:
        # Apenas o número e o aviso de atenção se for duplo
        fala_texto = f"{num_p}"
        if len(lista) > 1: fala_texto += " Atenção!"

        if "Masculina" in tipo_voz:
            pitch_val = "0.6"
            rate_val = "0.95"
        elif "Rápida" in tipo_voz:
            pitch_val = "1.1"
            rate_val = "1.35"
            
