import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.title("🔒 Acesso Restrito")
    st.warning("Por favor, faça login na página inicial.")
    if st.button("Ir para o Login"):
        st.switch_page("app.py")
    st.stop()

st.set_page_config(page_title="Relatório Mensal", page_icon="📝", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- FUNÇÃO EXCLUSIVA PARA GERAÇÃO DO PDF ---
def gerar_pdf_formatado(grupo, mes_ano, lideres, colideres, df_membros, obs_texto):
    pdf = FPDF()
    pdf.add_page()
    
    def c(texto): # Helper para tratar caracteres latinos
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    # Cabeçalho Visual do PDF
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, c(f"RELATÓRIO DE ATIVIDADES - {mes_ano}"), ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 242, 246)
    
    # Linhas do cabeçalho (Tabela cinza no PDF)
    pdf.cell(140, 5, c("NOME DO GRUPO FAMILIAR"), border=1, fill=True)
    pdf.cell(50, 5, c("Nº DO GF"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(140, 8, c(f"GF {grupo['numero']} - {grupo['nome']}"), border=1)
    pdf.cell(50, 8, c(f"{grupo['numero']}"), border=1, ln=True)
    
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, c("LÍDER"), border=1, fill=True)
    pdf.cell(95, 5, c("COORDENADOR"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, c(", ".join(lideres) if lideres else "Não definido"), border=1)
    pdf.cell(95, 8, c("Pr. Arthur e Pra. Simone"), border=1, ln=True)
    
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, c("LÍDER EM TREINAMENTO (CO-LÍDER)"), border=1, fill=True)
    pdf.cell(95, 5, c("PÚBLICO ALVO"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, c(", ".join(colideres) if colideres else "0"), border=1)
    pdf.cell(95, 8, c(grupo.get('publico_alvo', 'Misto')), border=1, ln=True)
    
    pdf.ln(10)
    
    # Grade de Frequência no PDF
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, c("Frequência de Membros"), ln=True)
    pdf.set_font("Arial", "B", 8)
    num_cols = len(df_membros.columns)
    col_width = 190 / num_cols
    
    for col in df_membros.columns:
        pdf.cell(col_width, 8, c(col), border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font("Arial", "", 8)
    for _, row in df_membros.iterrows():
        for item in row:
            pdf.cell(col_width, 8, c(item), border=1, align="C")
        pdf.ln()
    
    # Observações no PDF
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, c("Observações do Mês"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 8, c(obs_texto if obs_texto else "Sem observações registradas."))
    
    return bytes(pdf.output())

# --- 1. INTERFACE DE FILTROS (SIDEBAR) ---
with st.sidebar:
    st.header("🔍 Filtros")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses, index=datetime.now().month - 1)
    
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

st.title("📈 Relatório Mensal de Desempenho")

# --- 2. PROCESSAMENTO E EXIBIÇÃO EM TELA ---
if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    # Busca de dados
    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data and res_presencas.data:
        # Extração de lideranças
        lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
        colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']

        # Layout Simples em Tela (Métricas)
        c1, c2, c3 = st.columns(3)
        c1.metric("Membros Vinculados", len(res_membros.data))
        c2.metric("Reuniões no Mês", len(set(p['data_reuniao'] for p in res_presencas.data)))
        c3.metric("Público", grupo_sel.get('publico_alvo', 'Misto'))

        # Pivot de Presenças para a Tabela
        df_p = pd.DataFrame(res_presencas.data)
        datas = sorted(df_p['data_reuniao'].unique())
        col_datas = {d: datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b') for d in datas}
        
        lista_final = []
        for m in res_membros.data:
            nome = m['pessoas']['nome_completo']
            p_id = m['pessoa_id']
            row = {"Nome": nome, "Tipo": "Membro" if m['funcao'] != "VISITANTE" else "Visitante"}
            for d_orig, d_fmt in col_datas.items():
                presente = not df_p[(df_p['data_reuniao'] == d_orig) & (df_p['pessoa_id'] == p_id)].empty
                row[d_fmt] = "C" if presente else "-"
            lista_final.append(row)

        df_resumo = pd.DataFrame(lista_final)
        df_exibir = df_resumo[df_resumo['Tipo'] == 'Membro'].drop(columns=['Tipo'])

        st.write(f"### Grade de Frequência - {mes_sel}")
        st.dataframe(df_exibir, use_container_width=True, hide_index=True)

        # Observações em Tela (Lista Simples)
        st.write("### Observações Registradas")
        df_obs = df_p.groupby('data_reuniao')['observacao'].first().reset_index().sort_values('data_reuniao')
        obs_texto = ""
        for _, r in df_obs.iterrows():
            if r['observacao'] and r['observacao'] != 'None':
                data_f = datetime.strptime(r['data_reuniao'], '%Y-%m-%d').strftime('%d/%m')
                st.info(f"**Dia {data_f}:** {r['observacao']}")
                obs_texto += f"Dia {data_f}: {r['observacao']}\n"

        st.divider()
        
        # --- 3. BOTÃO DE DOWNLOAD DO PDF (FORMATADO) ---
        try:
            pdf_bytes = gerar_pdf_formatado(grupo_sel, f"{mes_sel}/{ano_sel}", lideres, colideres, df_exibir, obs_texto)
            st.download_button(
                label="📥 Baixar Relatório Oficial em PDF",
                data=pdf_bytes,
                file_name=f"Relatorio_{mes_sel}_{grupo_sel['numero']}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Erro ao preparar PDF: {e}")
    else:
        st.info("Aguardando lançamentos de presença para gerar os dados do mês.")
else:
    st.info("Selecione um Grupo Familiar para visualizar o desempenho.")
