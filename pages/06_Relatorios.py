import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit)
st.set_page_config(page_title="Relatório Executivo", page_icon="📈", layout="wide")

# 2. CONEXÃO COM SUPABASE (Definida antes de ser usada)
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- 3. SEGURANÇA: BLOQUEIO DE ACESSO DIRETO ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login na página inicial.")
    st.stop()

# --- 4. FILTRO DE DADOS POR PERFIL ---
usuario_id = st.session_state.get('usuario_id')
perfil = st.session_state.get('perfil')

if perfil == 'ADMIN':
    # Arthur e Simone veem tudo
    res_g = supabase.table("grupos_familiares").select("id, numero, nome, publico_alvo").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data
else:
    # Líderes veem apenas seus grupos vinculados no CCM
    res_g = supabase.table("membros_grupo").select(
        "grupo_id, grupos_familiares(id, numero, nome, publico_alvo)"
    ).eq("pessoa_id", usuario_id).filter("funcao", "in", '("LÍDER", "CO-LÍDER")').execute()
    g_opcoes = [item['grupos_familiares'] for item in res_g.data] if res_g.data else []

# --- FUNÇÃO PARA GERAÇÃO DO PDF ---
def gerar_pdf_oficial(grupo, mes_ano, lideres, colideres, df_membros, obs_texto, taxa_engaj, mapa_horarios):
    pdf = FPDF()
    pdf.add_page()
    
    def c(texto): return str(texto).encode('latin-1', 'replace').decode('latin-1')

    # Cabeçalho
    pdf.set_fill_color(118, 75, 162) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 12, c(f"RELATÓRIO DE ATIVIDADES - {mes_ano}"), ln=True, align="C", fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(95, 10, c(f" ENGAJAMENTO: {taxa_engaj:.1f}%"), border=1, fill=True)
    pdf.cell(95, 10, c(f" TOTAL DE MEMBROS: {len(df_membros)}"), border=1, fill=True, ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(130, 5, c("NOME DO GRUPO FAMILIAR"), border=1, fill=True)
    pdf.cell(60, 5, c("Nº DO GF"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(130, 8, c(f"{grupo['nome']}"), border=1)
    pdf.cell(60, 8, c(f"{grupo['numero']}"), border=1, ln=True)
    
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, c("LIDERANÇA"), border=1, fill=True)
    pdf.cell(95, 5, c("COORDENAÇÃO"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(95, 8, c(", ".join(lideres) if lideres else "N/A"), border=1)
    pdf.cell(95, 8, c("Pr. Arthur e Pra. Simone"), border=1, ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, c("Frequência de Membros"), ln=True)
    
    # Tabela dinâmica
    col_num_w, col_nome_w = 10, 60
    qtd_datas = len(df_membros.columns) - 2
    col_data_w = (190 - col_num_w - col_nome_w) / qtd_datas if qtd_datas > 0 else 30
    
    pdf.set_font("Arial", "B", 7)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(col_num_w, 10, "N", border=1, align="C", fill=True)
    pdf.cell(col_nome_w, 10, "Membro", border=1, align="C", fill=True)
    
    for col in df_membros.columns[2:]:
        pdf.cell(col_data_w, 10, c(col), border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    for _, row in df_membros.iterrows():
        pdf.cell(col_num_w, 8, c(row.iloc[0]), border=1, align="C")
        pdf.cell(col_nome_w, 8, c(row.iloc[1]), border=1)
        for val in row.iloc[2:]:
            pdf.cell(col_data_w, 8, c(val), border=1, align="C")
        pdf.ln()
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, c("Observações Pastorais"), ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 7, c(obs_texto if obs_texto else "Nenhuma observação registrada."), border=1)
    
    return bytes(pdf.output())

# --- ESTILIZAÇÃO CSS ---
st.markdown("""
<style>
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; }
.paper-container { background-color: white; border-radius: 15px; padding: 35px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid #eee; }
.styled-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
.styled-table th { background-color: #f8f9fa; padding: 12px; border: 1px solid #eee; }
.styled-table td { padding: 10px; border: 1px solid #eee; text-align: center; }
.badge-c { color: #155724; font-weight: bold; }
.badge-f { color: #721c24; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Filtros Filtrados) ---
with st.sidebar:
    st.title("📑 BI Manager")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses, index=datetime.now().month - 1)
    
    if g_opcoes:
        grupo_sel = st.selectbox("Selecione o GF", g_opcoes, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")
    else:
        st.error("Nenhum grupo vinculado.")
        st.stop()

st.title("📈 Analytics e Desempenho")

if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
        colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']
        total_m = len([m for m in res_membros.data if m['funcao'] != 'VISITANTE'])
        
        df_p_calc = pd.DataFrame(res_presencas.data) if res_presencas.data else pd.DataFrame()
        reunioes_m = len(set(df_p_calc['data_reuniao'])) if not df_p_calc.empty else 0
        
        taxa_engajamento = 0
        if total_m > 0 and reunioes_m > 0:
            membros_ids = [m['pessoa_id'] for m in res_membros.data if m['funcao'] != 'VISITANTE']
            presencas_reais = len(df_p_calc[df_p_calc['pessoa_id'].isin(membros_ids)])
            taxa_engajamento = (presencas_reais / (total_m * reunioes_m)) * 100

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><small>MEMBROS</small><h2>{total_m}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><small>ENCONTROS</small><h2>{reunioes_m}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><small>% ENGAJAMENTO</small><h2>{taxa_engajamento:.1f}%</h2></div>', unsafe_allow_html=True)

        st.markdown(f'<div class="paper-container"><h3>{grupo_sel["nome"]}</h3>', unsafe_allow_html=True)

        if not df_p_calc.empty:
            datas_orig = sorted(df_p_calc['data_reuniao'].unique())
            mapa_horarios = {}
            
            # Tabela de Visualização
            table_html = f'<table class="styled-table"><thead><tr><th>Membro</th>'
            for d in datas_orig:
                dt_fmt = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')
                table_html += f'<th>{dt_fmt}</th>'
            table_html += '</tr></thead><tbody>'

            lista_para_pdf = []
            for m in res_membros.data:
                if m['funcao'] == 'VISITANTE': continue
                nome = m['pessoas']['nome_completo']
                table_html += f'<tr><td style="text-align:left;">{nome}</td>'
                row_pdf = {"N": f"{len(lista_para_pdf)+1:02d}", "Membro": nome}
                
                for d in datas_orig:
                    dt_f = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')
                    p = not df_p_calc[(df_p_calc['data_reuniao'] == d) & (df_p_calc['pessoa_id'] == m['pessoa_id'])].empty
                    row_pdf[dt_f] = "C" if p else "F"
                    table_html += f'<td>{"✅" if p else "❌"}</td>'
                
                table_html += '</tr>'
                lista_para_pdf.append(row_pdf)
            
            table_html += '</tbody></table>'
            st.markdown(table_html, unsafe_allow_html=True)

            obs_pdf_texto = "\n".join([f"• {r['data_reuniao']}: {r['observacao']}" for _, r in df_p_calc.drop_duplicates('data_reuniao').iterrows() if r['observacao']])
            
            st.divider()
            pdf_bytes = gerar_pdf_oficial(grupo_sel, f"{mes_sel}/{ano_sel}", lideres, colideres, pd.DataFrame(lista_para_pdf), obs_pdf_texto, taxa_engajamento, {})
            st.download_button("📥 Gerar PDF do Mês", pdf_bytes, f"Relatorio_{grupo_sel['numero']}.pdf", "application/pdf", type="primary")
        else:
            st.info("Nenhum registro de presença para o período selecionado.")
