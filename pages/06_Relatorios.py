import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF

# --- SEGURANÇA E CONFIGURAÇÃO ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito.")
    st.stop()

st.set_page_config(page_title="Analytics de GF", page_icon="📈", layout="wide")

# --- CSS DE ALTO IMPACTO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Card de KPI */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    /* Container do Relatório "Papel Premium" */
    .paper-container {
        background-color: white;
        border-radius: 10px;
        border-top: 10px solid #764ba2;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        padding: 40px;
        margin-top: 20px;
    }
    
    /* Tabela Estilizada */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 25px 0;
        font-size: 0.9em;
        border-radius: 5px 5px 0 0;
        overflow: hidden;
    }
    .styled-table thead tr {
        background-color: #764ba2;
        color: #ffffff;
        text-align: center;
        font-weight: bold;
    }
    .styled-table th, .styled-table td { padding: 12px 15px; border: 1px solid #dddddd; }
    .styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
    
    /* Badge de Presença */
    .badge-presente {
        background-color: #28a745;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- SIDEBAR E FILTROS ---
with st.sidebar:
    st.title("📊 BI Manager")
    ano_sel = st.selectbox("Ano Fiscal", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês de Referência", meses, index=datetime.now().month - 1)
    
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("Grupo Familiar", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

# --- LÓGICA DE DADOS ---
if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
        colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']

        # --- SEÇÃO 1: MÉTRICAS DE IMPACTO (O toque de Analytics) ---
        st.markdown("### ✨ Insights do Mês")
        c1, c2, c3, c4 = st.columns(4)
        
        total_membros = len([m for m in res_membros.data if m['funcao'] != 'VISITANTE'])
        reunioes = len(set(p['data_reuniao'] for p in res_presencas.data))
        
        with c1:
            st.markdown(f'<div class="metric-card"> <small>Membros</small> <h2>{total_membros}</h2> </div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"> <small>Reuniões</small> <h2>{reunioes}</h2> </div>', unsafe_allow_html=True)
        with c3:
            engajamento = "85%" # Exemplo de cálculo futuro
            st.markdown(f'<div class="metric-card"> <small>Engajamento</small> <h2>{engajamento}</h2> </div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="metric-card"> <small>Público</small> <h2>{grupo_sel.get("publico_alvo", "Misto")}</h2> </div>', unsafe_allow_html=True)

        st.divider()

        # --- SEÇÃO 2: O RELATÓRIO "PREMIUM" (A sua referência, mas moderna) ---
        st.markdown(f"""
        <div class="paper-container">
            <h2 style='text-align:center; color:#764ba2;'>RELATÓRIO DE ATIVIDADES</h2>
            <p style='text-align:center; color:#666;'>{mes_sel.upper()} DE {ano_sel}</p>
            
            <table class="info-table" style="width:100%; border:1px solid #eee; margin-bottom:20px;">
                <tr>
                    <td style="padding:10px; border:1px solid #eee;"><b>GF:</b> {grupo_sel['numero']} - {grupo_sel['nome']}</td>
                    <td style="padding:10px; border:1px solid #eee;"><b>COORDENAÇÃO:</b> Pr. Arthur e Pra. Simone</td>
                </tr>
                <tr>
                    <td style="padding:10px; border:1px solid #eee;"><b>LÍDER:</b> {", ".join(lideres) if lideres else "N/A"}</td>
                    <td style="padding:10px; border:1px solid #eee;"><b>LÍDER EM TREINAMENTO:</b> {", ".join(colideres) if colideres else "0"}</td>
                </tr>
            </table>
        """, unsafe_allow_html=True)

        # Processamento da Grade de Frequência
        df_p = pd.DataFrame(res_presencas.data) if res_presencas.data else pd.DataFrame()
        datas = sorted(df_p['data_reuniao'].unique()) if not df_p.empty else []
        
        grid_html = """<table class="styled-table"><thead><tr><th rowspan="2">Nº</th><th rowspan="2">Membro</th><th colspan='"""+str(len(datas))+"""'>Presenças</th></tr><tr>"""
        grid_html += "".join([f"<th>{datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')}</th>" for d in datas])
        grid_html += "</tr></thead><tbody>"

        count = 1
        for m in res_membros.data:
            if m['funcao'] == 'VISITANTE': continue
            grid_html += f"<tr><td style='text-align:center'>{count}</td><td>{m['pessoas']['nome_completo']}</td>"
            for d in datas:
                presente = not df_p[(df_p['data_reuniao'] == d) & (df_p['pessoa_id'] == m['pessoa_id'])].empty
                val = '<span class="badge-presente">C</span>' if presente else ""
                grid_html += f"<td style='text-align:center'>{val}</td>"
            grid_html += "</tr>"
            count += 1
        
        grid_html += "</tbody></table>"
        st.markdown(grid_html, unsafe_allow_html=True)

        # Observações Estilizadas
        st.markdown("<h4>📝 Notas do Período</h4>", unsafe_allow_html=True)
        df_obs = df_p.groupby('data_reuniao')['observacao'].first().reset_index().sort_values('data_reuniao')
        for _, r in df_obs.iterrows():
            if r['observacao'] and r['observacao'] != 'None':
                st.markdown(f"""
                <div style="background:#f9f9f9; border-left:5px solid #764ba2; padding:10px; margin-bottom:10px;">
                    <small style='color:#764ba2;'><b>{datetime.strptime(r['data_reuniao'], '%Y-%m-%d').strftime('%d/%m/%Y')}</b></small><br>{r['observacao']}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True) # Fecha paper-container

        # --- SEÇÃO 3: EXPORTAÇÃO ---
        st.write("")
        st.download_button(
            label="📄 BAIXAR RELATÓRIO OFICIAL (PDF)",
            data=b"dummy", # Aqui você manteria sua função de bytes do PDF
            file_name=f"Relatorio_{mes_sel}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

else:
    st.info("Selecione um grupo para carregar o Analytics.")
