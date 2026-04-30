import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login na página inicial.")
    st.stop()

st.set_page_config(page_title="Relatório Executivo", page_icon="📈", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- 1. FUNÇÃO PREMIUM PARA GERAÇÃO DO PDF ---
def gerar_pdf_oficial(grupo, mes_ano, lideres, colideres, df_membros, obs_texto, taxa_engaj):
    pdf = FPDF()
    pdf.add_page()
    
    def c(texto): return str(texto).encode('latin-1', 'replace').decode('latin-1')

    # Cabeçalho Principal com Gradiente Simulado
    pdf.set_fill_color(118, 75, 162) # Roxo Executivo
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 12, c(f"RELATÓRIO DE ATIVIDADES - {mes_ano}"), ln=True, align="C", fill=True)
    
    # Box de Métricas (Analytics)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(60, 10, c(f" ENGAJAMENTO: {taxa_engaj:.1f}%"), border=1, fill=True)
    pdf.cell(70, 10, c(f" TOTAL DE MEMBROS: {len(df_membros)}"), border=1, fill=True)
    pdf.cell(60, 10, c(f" LOCAL: Curitiba, PR"), border=1, fill=True, ln=True)
    
    pdf.ln(5)
    
    # Grade de Informações do GF
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(130, 5, c("NOME DO GRUPO FAMILIAR"), border=1, fill=True)
    pdf.cell(60, 5, c("Nº DO GF"), border=1, fill=True, ln=True)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(130, 8, c(f"GF {grupo['numero']} - {grupo['nome']}"), border=1)
    pdf.cell(60, 8, c(f"{grupo['numero']}"), border=1, ln=True)
    
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, c("LIDERANÇA"), border=1, fill=True)
    pdf.cell(95, 5, c("COORDENAÇÃO"), border=1, fill=True, ln=True)
    
    pdf.set_font("Arial", "", 9)
    pdf.cell(95, 8, c(", ".join(lideres) if lideres else "N/A"), border=1)
    pdf.cell(95, 8, c("Pr. Arthur e Pra. Simone"), border=1, ln=True)
    
    pdf.ln(10)
    
    # Tabela de Frequência
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, c("Frequência de Membros"), ln=True)
    
    # Configuração de Colunas
    col_num_w = 10
    col_nome_w = 60
    col_data_w = (190 - col_num_w - col_nome_w) / (len(df_membros.columns) - 2)
    
    pdf.set_font("Arial", "B", 7)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(col_num_w, 10, "Nº", border=1, align="C", fill=True)
    pdf.cell(col_nome_w, 10, "Membro", border=1, align="C", fill=True)
    
    for col in df_membros.columns[2:]:
        x, y = pdf.get_x(), pdf.get_y()
        pdf.rect(x, y, col_data_w, 10, 'FD')
        pdf.set_xy(x, y + 1)
        pdf.cell(col_data_w, 4, c(col), align="C")
        pdf.set_xy(x, y + 5)
        pdf.set_font("Arial", "", 6)
        pdf.cell(col_data_w, 4, c("20:00-21:30"), align="C") # Horário fixo para o PDF
        pdf.set_xy(x + col_data_w, y)
        pdf.set_font("Arial", "B", 7)
    
    pdf.ln(10)
    
    # Linhas com Badges Coloridos (C/F)
    pdf.set_font("Arial", "", 8)
    for _, row in df_membros.iterrows():
        pdf.cell(col_num_w, 8, c(row[0]), border=1, align="C")
        pdf.cell(col_nome_w, 8, c(row[1]), border=1)
        
        for val in row[2:]:
            if val == 'C':
                pdf.set_fill_color(212, 237, 218) # Verde
                pdf.set_text_color(21, 87, 36)
            else:
                pdf.set_fill_color(248, 215, 218) # Vermelho
                pdf.set_text_color(114, 28, 36)
            
            pdf.cell(col_data_w, 8, c(val), border=1, align="C", fill=True)
            pdf.set_text_color(0, 0, 0)
        pdf.ln()
    
    # Observações
    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, c("Observações Pastorais"), ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 7, c(obs_texto if obs_texto else "Nenhuma observação."), border=1)
    
    return bytes(pdf.output())

# --- 2. CSS PARA O DASHBOARD (TELA) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; }
.paper-container { background-color: white; border-radius: 15px; padding: 35px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: 15px; border: 1px solid #eee; }
.badge-c { background-color: #d4edda; color: #155724; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
.badge-f { background-color: #f8d7da; color: #721c24; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- 3. FILTROS ---
with st.sidebar:
    st.title("📑 BI Manager")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses, index=datetime.now().month - 1)
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

st.title("📈 Analytics e Desempenho")

# --- 4. LÓGICA DE DADOS E DASHBOARD ---
if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        # Cálculo de Analytics
        total_m = len([m for m in res_membros.data if m['funcao'] != 'VISITANTE'])
        df_p_calc = pd.DataFrame(res_presencas.data) if res_presencas.data else pd.DataFrame()
        reunioes_m = len(set(df_p_calc['data_reuniao'])) if not df_p_calc.empty else 0
        
        taxa_engajamento = 0
        if total_m > 0 and reunioes_m > 0:
            presencas_reais = len(df_p_calc[df_p_calc['pessoa_id'].isin([m['pessoa_id'] for m in res_membros.data if m['funcao'] != 'VISITANTE'])])
            taxa_engajamento = (presencas_reais / (total_m * reunioes_m)) * 100

        # KPIs no topo
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><small>MEMBROS</small><h2>{total_m}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><small>ENCONTROS</small><h2>{reunioes_m}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><small>% ENGAJAMENTO</small><h2>{taxa_engajamento:.1f}%</h2></div>', unsafe_allow_html=True)

        # Renderização do Relatório na Tela (Omitido aqui por brevidade, mas segue a mesma lógica da grade HTML que já fizemos)
        
        # --- BOTÃO DE EXPORTAÇÃO ---
        st.divider()
        if not df_p_calc.empty:
            # Preparação dos dados para a função do PDF
            datas = sorted(df_p_calc['data_reuniao'].unique())
            lista_para_pdf = []
            count = 1
            for m in res_membros.data:
                if m['funcao'] == 'VISITANTE': continue
                nome = m['pessoas']['nome_completo']
                row = {"Nº": f"{count:02d}", "Membro": nome}
                for d in datas:
                    p = not df_p_calc[(df_p_calc['data_reuniao'] == d) & (df_p_calc['pessoa_id'] == m['pessoa_id'])].empty
                    row[datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')] = "C" if p else "F"
                lista_para_pdf.append(row)
                count += 1
            
            # Chamada da função PDF
            try:
                pdf_bytes = gerar_pdf_oficial(
                    grupo_sel, 
                    f"{mes_sel}/{ano_sel}", 
                    [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER'], 
                    [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER'], 
                    pd.DataFrame(lista_para_pdf), 
                    "Notas coletadas do sistema...", 
                    taxa_engajamento
                )
                st.download_button(label="📥 Gerar PDF para Impressão", data=pdf_bytes, file_name=f"Relatorio_{mes_sel}_GF.pdf", mime="application/pdf", type="primary", use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao preparar PDF: {e}")
