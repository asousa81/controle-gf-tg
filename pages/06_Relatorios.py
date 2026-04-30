import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Relatório Executivo", page_icon="📈", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- 2. SEGURANÇA E ACESSO ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login na página inicial.")
    st.stop()

usuario_id = st.session_state.get('usuario_id')
perfil = st.session_state.get('perfil')

if perfil == 'ADMIN':
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data
else:
    res_g = supabase.table("membros_grupo").select("grupo_id, grupos_familiares(*)").eq("pessoa_id", usuario_id).filter("funcao", "in", '("LÍDER", "CO-LÍDER")').execute()
    g_opcoes = [item['grupos_familiares'] for item in res_g.data] if res_g.data else []

# --- 3. FUNÇÃO PDF PREMIUM (INCLUINDO VISITANTES) ---
def gerar_pdf_oficial(grupo, mes_ano, lideres, colideres, df_membros, df_visitantes, obs_texto, taxa_engaj, mapa_horarios):
    pdf = FPDF()
    pdf.add_page()
    def c(texto): return str(texto).encode('latin-1', 'replace').decode('latin-1')

    # Cabeçalho
    pdf.set_fill_color(118, 75, 162) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 12, c(f"RELATÓRIO DE ATIVIDADES - {mes_ano}"), ln=True, align="C", fill=True)
    
    # Analytics Box
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(63, 10, c(f" ENGAJAMENTO: {taxa_engaj:.1f}%"), border=1, fill=True)
    pdf.cell(63, 10, c(f" MEMBROS: {len(df_membros)}"), border=1, fill=True)
    pdf.cell(64, 10, c(f" VISITANTES: {len(df_visitantes)}"), border=1, fill=True, ln=True)
    
    # Grade de Infos (Mantendo seu estilo)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(130, 5, c("NOME DO GRUPO FAMILIAR"), border=1, fill=True)
    pdf.cell(60, 5, c("Nº DO GF"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(130, 8, c(f"{grupo['nome']}"), border=1)
    pdf.cell(60, 8, c(f"{grupo['numero']}"), border=1, ln=True)

    # Frequência de Membros
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, c("Frequência de Membros"), ln=True)
    
    col_num_w, col_nome_w = 10, 60
    qtd_datas = len(df_membros.columns) - 2
    col_data_w = (190 - col_num_w - col_nome_w) / qtd_datas if qtd_datas > 0 else 30
    
    pdf.set_font("Arial", "B", 7)
    for col in df_membros.columns[2:]:
        pdf.cell(col_data_w, 8, c(col), border=1, align="C", fill=True)
    pdf.ln()

    for _, row in df_membros.iterrows():
        pdf.cell(col_num_w, 8, c(row.iloc[0]), border=1)
        pdf.cell(col_nome_w, 8, c(row.iloc[1]), border=1)
        for val in row.iloc[2:]:
            pdf.cell(col_data_w, 8, c(val), border=1, align="C")
        pdf.ln()

    # SEÇÃO DE VISITANTES NO PDF
    if not df_visitantes.empty:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 10, c("Visitantes no Período"), ln=True)
        pdf.set_font("Arial", "B", 8)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(30, 8, c("Data"), border=1, fill=True)
        pdf.cell(160, 8, c("Nome do Visitante (Convidado por)"), border=1, fill=True, ln=True)
        pdf.set_font("Arial", "", 8)
        for _, v in df_visitantes.iterrows():
            data_v = datetime.strptime(v['data_reuniao'], '%Y-%m-%d').strftime('%d/%m')
            pdf.cell(30, 8, c(data_v), border=1)
            pdf.cell(160, 8, c(f"{v['nome_visitante']} (Por: {v['quem_convidou']})"), border=1, ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, c("Notas Pastorais"), ln=True)
    pdf.multi_cell(0, 7, c(obs_texto), border=1)
    
    return bytes(pdf.output())

# --- 4. CSS (ESTILO ORIGINAL PRESERVADO) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.paper-container { background-color: white; border-radius: 15px; padding: 35px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); border: 1px solid #eee; }
.badge-c { background-color: #d4edda; color: #155724; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
.badge-f { background-color: #f8d7da; color: #721c24; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# --- 5. FILTROS ---
with st.sidebar:
    st.title("📑 BI Manager")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses, index=datetime.now().month - 1)
    grupo_sel = st.selectbox("Selecione o GF", g_opcoes, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

# --- 6. PROCESSAMENTO ---
if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_p = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()
    res_v = supabase.table("visitantes_encontro").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        df_p = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame()
        df_v = pd.DataFrame(res_v.data) if res_v.data else pd.DataFrame()
        
        # Métricas em 4 colunas
        c1, c2, c3, c4 = st.columns(4)
        total_m = len([m for m in res_membros.data if m['funcao'] != 'VISITANTE'])
        reunioes = len(set(df_p['data_reuniao'])) if not df_p.empty else 0
        
        with c1: st.markdown(f'<div class="metric-card"><small>MEMBROS</small><h2>{total_m}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><small>ENCONTROS</small><h2>{reunioes}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><small>VISITANTES</small><h2>{len(df_v)}</h2></div>', unsafe_allow_html=True)
        with c4: 
            engaj = (len(df_p)/(total_m*reunioes)*100) if total_m*reunioes > 0 else 0
            st.markdown(f'<div class="metric-card"><small>% ENGAJ</small><h2>{engaj:.1f}%</h2></div>', unsafe_allow_html=True)

        st.markdown('<div class="paper-container">', unsafe_allow_html=True)
        st.subheader(f"📊 Relatório {mes_sel} - {grupo_sel['nome']}")

        # Tabela de Membros
        if not df_p.empty:
            datas = sorted(df_p['data_reuniao'].unique())
            lista_pdf = []
            for i, m in enumerate(res_membros.data):
                if m['funcao'] == 'VISITANTE': continue
                row = {"Nº": f"{i+1:02d}", "Membro": m['pessoas']['nome_completo']}
                for d in datas:
                    dt_f = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')
                    p = not df_p[(df_p['data_reuniao'] == d) & (df_p['pessoa_id'] == m['pessoa_id'])].empty
                    row[dt_f] = "C" if p else "F"
                lista_pdf.append(row)
            st.write("#### Frequência de Membros")
            st.table(pd.DataFrame(lista_pdf))

        # Tabela de Visitantes
        if not df_v.empty:
            st.write("#### 🌟 Novos Visitantes")
            st.table(df_v[['data_reuniao', 'nome_visitante', 'quem_convidou', 'telefone_visitante']])
        
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        if st.button("📥 Gerar PDF"):
            # Lógica simples de obs para o PDF
            obs_texto = "\n".join([f"[{r['data_reuniao']}] {r['observacao']}" for r in res_p.data if r['observacao']])
            pdf_bytes = gerar_pdf_oficial(grupo_sel, f"{mes_sel}/{ano_sel}", [], [], pd.DataFrame(lista_pdf), df_v, obs_texto, engaj, {})
            st.download_button("Clique para Baixar", pdf_bytes, f"Relatorio_{mes_sel}.pdf", "application/pdf")
