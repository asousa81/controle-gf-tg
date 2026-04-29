import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF

# --- FUNÇÃO PARA GERAR PDF (VERSÃO ROBUSTA) ---
def exportar_pdf(grupo, mes_ano, lideres, colideres, df_membros, df_visit, obs_texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Função auxiliar para limpar caracteres especiais (evita erro de encoding)
    def clean_text(text):
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, clean_text(f"RELATÓRIO DE ATIVIDADES - {mes_ano}"), ln=True, align="C")
    pdf.ln(5)
    
    # Cabeçalho
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 242, 246)
    
    pdf.cell(140, 5, "NOME DO GRUPO FAMILIAR", border=1, fill=True)
    pdf.cell(50, 5, "Nº DO GF", border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(140, 8, clean_text(f"GF {grupo['numero']} - {grupo['nome']}"), border=1)
    pdf.cell(50, 8, clean_text(f"{grupo['numero']}"), border=1, ln=True)
    
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, "LÍDER", border=1, fill=True)
    pdf.cell(95, 5, "COORDENADOR", border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, clean_text(f"{', '.join(lideres) if lideres else '-'}"), border=1)
    pdf.cell(95, 8, "Pr. Arthur e Pra. Simone", border=1, ln=True)
    
    pdf.ln(10)
    
    # Tabela de Membros
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Frequência de Membros", ln=True)
    
    # Cabeçalho da Tabela
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 242, 246)
    
    # Ajuste dinâmico de largura
    num_cols = len(df_membros.columns)
    col_width = 190 / num_cols
    
    for col in df_membros.columns:
        pdf.cell(col_width, 8, clean_text(col), border=1, align="C", fill=True)
    pdf.ln()
    
    # Dados
    pdf.set_font("Arial", "", 8)
    for _, row in df_membros.iterrows():
        for item in row:
            pdf.cell(col_width, 8, clean_text(item), border=1, align="C")
        pdf.ln()
    
    # Observações
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Observações do Mês", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 8, clean_text(obs_texto if obs_texto else "Nenhuma observação registrada."))
    
    # RETORNO EXPLÍCITO EM BYTES
    return bytes(pdf.output())

# --- NO BLOCO DO BOTÃO (FINAL DO ARQUIVO) ---
if grupo_sel and res_presencas.data:
    # ... (seu código de processamento de df_membros_print e obs_texto continua igual) ...

    st.divider()
    
    try:
        # Geramos os bytes do PDF
        pdf_output = exportar_pdf(
            grupo_sel, 
            f"{mes_sel}/{ano_sel}", 
            lideres, 
            colideres, 
            df_membros_print, 
            df_visit_print, 
            obs_texto
        )
        
        # O download_button agora recebe explicitamente o objeto de bytes
        st.download_button(
            label="📥 Baixar Relatório em PDF",
            data=pdf_output,
            file_name=f"Relatorio_GF{grupo_sel['numero']}_{mes_sel}_{ano_sel}.pdf",
            mime="application/pdf",
            type="primary"
        )
    except Exception as e:
        st.error(f"Erro ao gerar o arquivo PDF: {e}")
