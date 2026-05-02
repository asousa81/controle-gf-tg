def gerar_pdf_dia(data_f, grupos_do_dia):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, f"Lista de Oração - {data_f}", ln=True, align="C")
    pdf.ln(5)

    for nome_gf, lista_pedidos in grupos_do_dia.items():
        pdf.set_font("helvetica", "B", 13)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 10, f" Grupo: {nome_gf}", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 11)
        for item in lista_pedidos:
            nome = item['pessoas']['nome_completo']
            pedido = item['pedido']
            
            # --- AJUSTE PARA EVITAR ERRO DE UNICODE ---
            # 1. Trocamos o '•' por um traço '-'
            # 2. Removemos caracteres que a fonte Helvetica não entende (como emojis)
            texto_limpo = f"- {nome}: {pedido}"
            texto_pdf = texto_limpo.encode('latin-1', 'replace').decode('latin-1')
            
            pdf.multi_cell(0, 7, texto_pdf)
            pdf.ln(1)
        pdf.ln(4)
            
    return pdf.output()
