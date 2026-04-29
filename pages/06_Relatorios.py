import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF  # Importação para geração do PDF

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login.")
    st.stop()

st.set_page_config(page_title="Relatório de Atividades", page_icon="📝", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- FUNÇÃO PARA GERAR PDF ---
def exportar_pdf(grupo, mes_ano, lideres, colideres, df_membros, df_visit, obs_texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Título
    pdf.cell(190, 10, f"RELATÓRIO DE ATIVIDADES - {mes_ano}", ln=True, align="C")
    pdf.ln(5)
    
    # Cabeçalho (Estrutura de Tabela)
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 242, 246)
    
    # Linha 1
    pdf.cell(140, 5, "NOME DO GRUPO FAMILIAR", border=1, fill=True)
    pdf.cell(50, 5, "Nº DO GF", border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(140, 8, f"GF {grupo['numero']} - {grupo['nome']}", border=1)
    pdf.cell(50, 8, f"{grupo['numero']}", border=1, ln=True)
    
    # Linha 2
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, "LÍDER", border=1, fill=True)
    pdf.cell(95, 5, "COORDENADOR", border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f"{', '.join(lideres) if lideres else '-'}", border=1)
    pdf.cell(95, 8, "Pr. Arthur e Pra. Simone", border=1, ln=True)
    
    # Linha 3
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, "LÍDER EM TREINAMENTO (CO-LÍDER)", border=1, fill=True)
    pdf.cell(95, 5, "PÚBLICO ALVO", border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, f"{', '.join(colideres) if colideres else '0'}", border=1)
    pdf.cell(95, 8, f"{grupo.get('publico_alvo', 'Misto')}", border=1, ln=True)
    
    pdf.ln(10)
    
    # Tabela de Membros
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Frequência de Membros", ln=True)
    pdf.set_font("Arial", "B", 8)
    
    # Cabeçalho da Tabela
    col_width = 190 / (len(df_membros.columns))
    for col in df_membros.columns:
        pdf.cell(col_width, 8, str(col), border=1, align="C", fill=True)
    pdf.ln()
    
    # Dados da Tabela
    pdf.set_font("Arial", "", 8)
    for _, row in df_membros.iterrows():
        for item in row:
            pdf.cell(col_width, 8, str(item), border=1, align="C")
        pdf.ln()
    
    # Observações
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Observações do Mês", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 8, obs_texto if obs_texto else "Nenhuma observação registrada.")
    
    return pdf.output()

# --- 1. SELEÇÃO DE PARÂMETROS ---
with st.sidebar:
    st.header("⚙️ Configurações")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses_lista = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses_lista, index=datetime.now().month - 1)
    
    res_g = supabase.table("grupos_familiares").select("id, numero, nome, publico_alvo").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

st.title("📄 Relatório de Atividades do Grupo Familiar")

if grupo_sel:
    # --- 2. COLETA DE DADOS ---
    mes_num = meses_lista.index(mes_sel) + 1
    ultimo_dia = calendar.monthrange(ano_sel, mes_num)[1]
    data_inicio = f"{ano_sel}-{mes_num:02d}-01"
    data_fim = f"{ano_sel}-{mes_num:02d}-{ultimo_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("data_reuniao, observacao, pessoa_id").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", data_inicio).lte("data_reuniao", data_fim).execute()

    # Identificação de Lideranças
    lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
    colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']

    # --- 3. GRADE DE PRESENÇAS ---
    if res_presencas.data:
        df_p = pd.DataFrame(res_presencas.data)
        datas_reuniao = sorted(df_p['data_reuniao'].unique())
        colunas_datas = {d: datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b') for d in datas_reuniao}
        
        lista_presenca = []
        for m in res_membros.data:
            nome = m['pessoas']['nome_completo']
            p_id = m['pessoa_id']
            tipo = "Visitante" if m['funcao'] == "VISITANTE" else "Membro"
            
            row = {"Nome": nome, "Tipo": tipo}
            for data_orig, data_format in colunas_datas.items():
                esta_presente = not df_p[(df_p['data_reuniao'] == data_orig) & (df_p['pessoa_id'] == p_id)].empty
                row[data_format] = "C" if esta_presente else "-"
            lista_presenca.append(row)

        df_full = pd.DataFrame(lista_presenca)
        df_membros_print = df_full[df_full['Tipo'] == 'Membro'].drop(columns=['Tipo'])
        df_visit_print = df_full[df_full['Tipo'] == 'Visitante'].drop(columns=['Tipo'])

        # --- 4. EXIBIÇÃO NA TELA ---
        st.write(f"### GF {grupo_sel['numero']} - {grupo_sel['nome']}")
        st.dataframe(df_membros_print, use_container_width=True, hide_index=True)
        
        # Consolidação de Observações para o PDF
        df_obs = df_p.groupby('data_reuniao')['observacao'].first().reset_index().sort_values(by='data_reuniao')
        obs_texto = "\n".join([f"Dia {datetime.strptime(r['data_reuniao'], '%Y-%m-%d').strftime('%d/%m')}: {r['observacao']}" 
                               for _, r in df_obs.iterrows() if r['observacao'] and r['observacao'] != 'None'])

        # --- 5. BOTÃO DE EXPORTAÇÃO ---
        st.divider()
        pdf_bytes = exportar_pdf(grupo_sel, f"{mes_sel}/{ano_sel}", lideres, colideres, df_membros_print, df_visit_print, obs_texto)
        
        st.download_button(
            label="📥 Baixar Relatório em PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_GF{grupo_sel['numero']}_{mes_sel}_{ano_sel}.pdf",
            mime="application/pdf",
            type="primary"
        )
    else:
        st.info("Nenhum lançamento encontrado para este período.")
