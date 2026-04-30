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

st.set_page_config(page_title="Relatório Premium", page_icon="📈", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- FUNÇÃO ROBUSTA PARA GERAÇÃO DO PDF ---
def gerar_pdf_oficial(grupo, mes_ano, lideres, colideres, df_membros, obs_texto):
    pdf = FPDF()
    pdf.add_page()
    
    def c(texto): # Limpeza de caracteres para Latin-1
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, c(f"RELATÓRIO DE ATIVIDADES - {mes_ano}"), ln=True, align="C")
    pdf.ln(5)
    
    # Cabeçalho Cinza (Estilo Secretaria)
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 242, 246)
    
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
    
    pdf.ln(10)
    
    # Grade de Frequência
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, c("Frequência de Membros"), ln=True)
    pdf.set_font("Arial", "B", 8)
    
    col_width = 190 / len(df_membros.columns)
    for col in df_membros.columns:
        pdf.cell(col_width, 8, c(col), border=1, align="C", fill=True)
    pdf.ln()
    
    pdf.set_font("Arial", "", 8)
    for _, row in df_membros.iterrows():
        for item in row:
            pdf.cell(col_width, 8, c(item), border=1, align="C")
        pdf.ln()
    
    # Observações
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, c("Observações do Mês"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 8, c(obs_texto if obs_texto else "Nenhuma observação registrada."))
    
    return bytes(pdf.output())

# --- ESTILIZAÇÃO UI/UX PREMIUM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); text-align: center;
    }
    .paper-container {
        background-color: white; border-radius: 10px;
        border-top: 10px solid #764ba2; padding: 40px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05); margin-top: 20px;
    }
    .styled-table {
        width: 100%; border-collapse: collapse; margin: 20px 0;
        font-size: 0.9em; border-radius: 8px; overflow: hidden;
    }
    .styled-table thead tr {
        background-color: #764ba2; color: #ffffff; text-align: center; font-weight: bold;
    }
    .styled-table th, .styled-table td { padding: 12px 15px; border: 1px solid #eee; }
    .styled-table tbody tr:nth-of-type(even) { background-color: #f9f9f9; }
    .badge-presente {
        background-color: #28a745; color: white; padding: 3px 10px;
        border-radius: 50px; font-weight: bold; font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. FILTROS (SIDEBAR) ---
with st.sidebar:
    st.title("📑 BI Manager")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês de Referência", meses, index=datetime.now().month - 1)
    
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

st.title("📈 Analytics e Desempenho Mensal")

# --- 2. LÓGICA PRINCIPAL ---
if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
        colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']
        
        # --- SEÇÃO DE INSIGHTS ---
        st.markdown("### ✨ Insights de Engajamento")
        c1, c2, c3, c4 = st.columns(4)
        total_m = len([m for m in res_membros.data if m['funcao'] != 'VISITANTE'])
        reunioes_m = len(set(p['data_reuniao'] for p in res_presencas.data)) if res_presencas.data else 0
        
        with c1: st.markdown(f'<div class="metric-card"><small>Membros</small><h2>{total_m}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><small>Reuniões</small><h2>{reunioes_m}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><small>Público</small><h5>{grupo_sel.get("publico_alvo", "Misto")}</h5></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card"><small>Status</small><h5>Ativo</h5></div>', unsafe_allow_html=True)

        st.divider()

        # --- CABEÇALHO DO RELATÓRIO (HTML SEM RECUO) ---
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

        # --- PROCESSAMENTO DA GRADE ---
        if res_presencas.data:
            df_p = pd.DataFrame(res_presencas.data)
            datas = sorted(df_p['data_reuniao'].unique())
            
            grid_html = """<table class="styled-table"><thead><tr><th rowspan="2">Nº</th><th rowspan="2">Membro</th>"""
            grid_html += f"""<th colspan="{len(datas)}">Datas das Reuniões</th></tr><tr>"""
            grid_html += "".join([f"<th>{datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')}</th>" for d in datas])
            grid_html += "</tr></thead><tbody>"

            lista_para_pdf = []
            count = 1
            for m in res_membros.data:
                if m['funcao'] == 'VISITANTE': continue
                nome_m = m['pessoas']['nome_completo']
                grid_html += f"<tr><td style='text-align:center'>{count}</td><td>{nome_m}</td>"
                row_pdf = {"Nº": count, "Membro": nome_m}
                
                for d in datas:
                    presente = not df_p[(df_p['data_reuniao'] == d) & (df_p['pessoa_id'] == m['pessoa_id'])].empty
                    label_data = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')
                    grid_html += f"<td style='text-align:center'>{'<span class=\"badge-presente\">C</span>' if presente else '-'}</td>"
                    row_pdf[label_data] = "C" if presente else "-"
                
                grid_html += "</tr>"
                lista_para_pdf.append(row_pdf)
                count += 1
            
            grid_html += "</tbody></table>"
            st.markdown(grid_html, unsafe_allow_html=True)
            df_final_pdf = pd.DataFrame(lista_para_pdf)

            # Notas de Reunião
            st.markdown("<h4>📝 Notas de Pastoreio</h4>", unsafe_allow_html=True)
            df_obs = df_p.groupby('data_reuniao')['observacao'].first().reset_index().sort_values('data_reuniao')
            obs_pdf_texto = ""
            for _, r in df_obs.iterrows():
                if r['observacao'] and r['observacao'] != 'None':
                    dt_f = datetime.strptime(r['data_reuniao'], '%Y-%m-%d').strftime('%d/%m/%Y')
                    st.markdown(f'<div style="background:#f9f9f9; border-left:5px solid #764ba2; padding:15px; margin-bottom:10px;"><small><b>{dt_f}</b></small><br>{r['observacao']}</div>', unsafe_allow_html=True)
                    obs_pdf_texto += f"Dia {dt_f}: {r['observacao']}\n"
            
            st.markdown("</div>", unsafe_allow_html=True) # Fecha paper-container

            # BOTÃO DE PDF
            st.write("")
            try:
                pdf_bytes = gerar_pdf_oficial(grupo_sel, f"{mes_sel}/{ano_sel}", lideres, colideres, df_final_pdf, obs_pdf_texto)
                st.download_button(label="📥 Exportar Relatório Oficial (PDF)", data=pdf_bytes, file_name=f"Relatorio_{mes_sel}_GF{grupo_sel['numero']}.pdf", mime="application/pdf", type="primary", use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao preparar PDF: {e}")
        else:
            st.markdown("<p style='text-align:center; color:#999;'>Nenhuma presença lançada neste mês.</p></div>", unsafe_allow_html=True)
    else:
        st.info("Este grupo não possui membros vinculados.")
else:
    st.info("Selecione um Grupo Familiar no menu lateral.")
