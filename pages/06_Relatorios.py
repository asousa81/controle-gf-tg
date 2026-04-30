# --- SEÇÃO 2: O RELATÓRIO "PREMIUM" ---
        # Certifique-se de que a string abaixo comece sem espaços na margem esquerda do código
        conteudo_header = f"""
<div class="paper-container">
    <h2 style='text-align:center; color:#764ba2; margin-bottom:0;'>RELATÓRIO DE ATIVIDADES</h2>
    <p style='text-align:center; color:#666; margin-top:5px; margin-bottom:30px;'>{mes_sel.upper()} DE {ano_sel}</p>
    
    <table style="width:100%; border-collapse: collapse; border: 1px solid #eee; margin-bottom:20px;">
        <tr>
            <td style="padding:12px; border:1px solid #eee; width:50%;"><b>GF:</b> {grupo_sel['numero']} - {grupo_sel['nome']}</td>
            <td style="padding:12px; border:1px solid #eee; width:50%;"><b>COORDENAÇÃO:</b> Pr. Arthur e Pra. Simone</td>
        </tr>
        <tr>
            <td style="padding:12px; border:1px solid #eee;"><b>LÍDER:</b> {", ".join(lideres) if lideres else "N/A"}</td>
            <td style="padding:12px; border:1px solid #eee;"><b>LÍDER EM TREINAMENTO:</b> {", ".join(colideres) if colideres else "0"}</td>
        </tr>
    </table>
"""
        st.markdown(conteudo_header, unsafe_allow_html=True)

        # ... (O restante do processamento da grid continua igual) ...
        
        # Ao final, lembre-se de fechar a div do container
        # (Se você estiver renderizando a grid e as notas via st.markdown também)
        # grid_html e notas_html devem ser concatenados ou renderizados sem recuo
