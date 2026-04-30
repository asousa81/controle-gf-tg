import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Por favor, faça login para acessar os relatórios.")
    st.stop()

st.set_page_config(page_title="Relatório Executivo", page_icon="📈", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- CSS PREMIUM (Indentação Zero) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.paper-container { background-color: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: 15px; border: 1px solid #eee; }
.header-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 15px; margin-bottom: 25px; padding-bottom: 15px; border-bottom: 2px solid #f4f4f4; }
.info-item { margin-bottom: 8px; }
.label { font-size: 0.75rem; color: #888; text-transform: uppercase; font-weight: 700; display: block; }
.value { font-size: 1rem; color: #222; font-weight: 600; }
.styled-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.85rem; }
.styled-table thead th { background-color: #f8f9fa; color: #444; padding: 12px; border: 1px solid #eee; text-align: center; }
.styled-table td { padding: 10px; border: 1px solid #eee; text-align: center; }
.badge-c { background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 6px; font-weight: 700; }
.badge-f { background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 6px; font-weight: 700; }
.time-sub { font-size: 0.7rem; color: #666; display: block; font-weight: 400; margin-top: 2px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("📑 BI Manager")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses, index=datetime.now().month - 1)
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        lideres = [m['id'] for m in res_membros.data if m['funcao'] == 'LÍDER'] # Exemplo simplificado
        # ... lógica de nomes de líderes ...

        # --- CABEÇALHO (HTML sem recuo para evitar erro de código) ---
        st.markdown(f"""
<div class="paper-container">
<div style="text-align: center; margin-bottom: 25px;">
<h2 style="color: #764ba2; margin: 0;">RELATÓRIO DE ATIVIDADES</h2>
<span style="color: #999; font-weight: 600;">{mes_sel.upper()} / {ano_sel}</span>
</div>
<div class="header-grid">
<div>
<div class="info-item"><span class="label">NOME DO GRUPO FAMILIAR</span><span class="value">GF {grupo_sel['numero']} - {grupo_sel['nome']}</span></div>
<div class="info-item"><span class="label">LIDERANÇA</span><span class="value">Arthur Quirino de Sousa, Simone Sousa</span></div>
</div>
<div>
<div class="info-item"><span class="label">COORDENAÇÃO</span><span class="value">Pr. Arthur e Pra. Simone</span></div>
<div class="info-item"><span class="label">PÚBLICO ALVO</span><span class="value">{grupo_sel.get('publico_alvo', 'Misto')}</span></div>
</div>
</div>
""", unsafe_allow_html=True)

        if res_presencas.data:
            df_p = pd.DataFrame(res_presencas.data)
            # Agrupar por data para pegar os horários daquela reunião específica
            df_reunioes = df_p.groupby('data_reuniao').first().reset_index()
            datas = sorted(df_reunioes['data_reuniao'].tolist())
            
            # Cabeçalho da Tabela
            table_html = f"""<table class="styled-table"><thead><tr><th rowspan="2" style="width: 50px;">Nº</th><th rowspan="2" style="text-align: left;">MEMBROS DO GF</th><th colspan="{len(datas)}">DIAS DE ENCONTRO E HORÁRIOS</th></tr><tr>"""
            
            # Adicionando Datas e Horários logo abaixo no Header
            for d in datas:
                info_r = df_reunioes[df_reunioes['data_reuniao'] == d].iloc[0]
                h_i = info_r.get('horario_inicio', '20:00')[:5]
                h_f = info_r.get('horario_termino', '21:30')[:5]
                dt_fmt = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')
                table_html += f"<th>{dt_fmt}<br><span class='time-sub'>{h_i} às {h_f}</span></th>"
            
            table_html += "</tr></thead><tbody>"

            # Linhas de Membros
            count = 1
            for m in res_membros.data:
                if m['funcao'] == 'VISITANTE': continue
                nome = m['pessoas']['nome_completo']
                table_html += f"<tr><td>{count}</td><td style='text-align: left; font-weight: 600;'>{nome}</td>"
                for d in datas:
                    p = not df_p[(df_p['data_reuniao'] == d) & (df_p['pessoa_id'] == m['pessoa_id'])].empty
                    status = '<span class="badge-c">C</span>' if p else '<span class="badge-f">F</span>'
                    table_html += f"<td>{status}</td>"
                table_html += "</tr>"
                count += 1
            
            table_html += "</tbody></table></div>"
            st.markdown(table_html, unsafe_allow_html=True)
