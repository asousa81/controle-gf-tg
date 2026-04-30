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

# --- CSS PREMIUM ATUALIZADO ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.paper-container { background-color: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: 15px; border: 1px solid #eee; }
.header-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 25px; padding-bottom: 20px; border-bottom: 2px solid #f8f9fa; }
.info-item { margin-bottom: 10px; }
.label { font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 700; display: block; margin-bottom: 2px; }
.value { font-size: 0.95rem; color: #111; font-weight: 600; }
.styled-table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.85rem; }
.styled-table thead th { background-color: #fcfcfc; color: #444; padding: 12px 8px; border: 1px solid #eee; text-align: center; }
.styled-table td { padding: 10px; border: 1px solid #eee; text-align: center; }
.badge-c { background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 6px; font-weight: 700; }
.badge-f { background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 6px; font-weight: 700; }
.time-sub { font-size: 0.65rem; color: #777; display: block; font-weight: 400; margin-top: 4px; line-height: 1.2; }
.obs-section { background: #f9f9f9; border-radius: 8px; padding: 20px; margin-top: 25px; border-left: 4px solid #764ba2; }
</style>
""", unsafe_allow_html=True)

# --- 1. FILTROS (SIDEBAR) ---
with st.sidebar:
    st.title("📑 BI Manager")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses, index=datetime.now().month - 1)
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

# --- 2. LÓGICA DE DADOS ---
if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    # Busca Membros e Presenças (Corrigido para evitar KeyError)
    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        # Extração correta dos nomes dos líderes e co-líderes
        lideres_nomes = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
        colideres_nomes = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']

        # --- CABEÇALHO DO RELATÓRIO (HTML LIMPO) ---
        st.markdown(f"""
<div class="paper-container">
<div style="text-align: center; margin-bottom: 30px;">
<h2 style="color: #764ba2; margin: 0; letter-spacing: 1px;">RELATÓRIO DE ATIVIDADES</h2>
<span style="color: #999; font-weight: 600;">{mes_sel.upper()} / {ano_sel}</span>
</div>
<div class="header-grid">
<div>
<div class="info-item"><span class="label">NOME DO GRUPO FAMILIAR</span><span class="value">GF {grupo_sel['numero']} - {grupo_sel['nome']}</span></div>
<div class="info-item"><span class="label">LIDERANÇA</span><span class="value">{", ".join(lideres_nomes) if lideres_nomes else "Não definido"}</span></div>
<div class="info-item"><span class="label">LÍDER EM TREINAMENTO</span><span class="value">{", ".join(colideres_nomes) if colideres_nomes else "Nenhum"}</span></div>
</div>
<div>
<div class="info-item"><span class="label">COORDENAÇÃO</span><span class="value">Pr. Arthur e Pra. Simone</span></div>
<div class="info-item"><span class="label">PÚBLICO ALVO</span><span class="value">{grupo_sel.get('publico_alvo', 'Misto')}</span></div>
<div class="info-item"><span class="label">SECRETARIA</span><span class="value">CCM Curitiba</span></div>
</div>
</div>
""", unsafe_allow_html=True)

        if res_presencas.data:
            df_p = pd.DataFrame(res_presencas.data)
            # Agrupar por data para pegar os horários reais lançados
            df_reunioes = df_p.groupby('data_reuniao').first().reset_index()
            datas = sorted(df_reunioes['data_reuniao'].tolist())
            
            # Montagem da Tabela com Horários no Header
            table_html = f"""<table class="styled-table"><thead><tr><th rowspan="2" style="width: 40px;">Nº</th><th rowspan="2" style="text-align: left;">MEMBROS DO GF</th><th colspan="{len(datas)}">DATAS E HORÁRIOS DOS ENCONTROS</th></tr><tr>"""
            
            for d in datas:
                info_r = df_reunioes[df_reunioes['data_reuniao'] == d].iloc[0]
                h_i = info_r.get('horario_inicio', '20:00')[:5]
                h_f = info_r.get('horario_termino', '21:30')[:5]
                dt_fmt = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')
                table_html += f"<th>{dt_fmt}<br><span class='time-sub'>{h_i} às {h_f}</span></th>"
            
            table_html += "</tr></thead><tbody>"

            # Linhas dos Membros (com H/F Estilizado)
            count = 1
            for m in res_membros.data:
                if m['funcao'] == 'VISITANTE': continue
                nome = m['pessoas']['nome_completo']
                table_html += f"<tr><td style='color: #888;'>{count:02d}</td><td style='text-align: left; font-weight: 600;'>{nome}</td>"
                for d in datas:
                    presente = not df_p[(df_p['data_reuniao'] == d) & (df_p['pessoa_id'] == m['pessoa_id'])].empty
                    status = '<span class="badge-c">C</span>' if presente else '<span class="badge-f">F</span>'
                    table_html += f"<td>{status}</td>"
                table_html += "</tr>"
                count += 1
            
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

            # Seção de Observações
            st.markdown('<div class="obs-section"><span class="label">Observações e Notas do Mês</span>', unsafe_allow_html=True)
            df_obs = df_p.groupby('data_reuniao')['observacao'].first().reset_index()
            for _, r in df_obs.iterrows():
                if r['observacao'] and r['observacao'] != 'None' and r['observacao'].strip() != "":
                    st.write(f"**• {datetime.strptime(r['data_reuniao'], '%Y-%m-%d').strftime('%d/%m')}:** {r['observacao']}")
            st.markdown('</div></div>', unsafe_allow_html=True)

            st.divider()
            if st.button("📥 Gerar PDF para Impressão", type="primary", use_container_width=True):
                st.info("Função de exportação sendo preparada com o novo layout...")
        else:
            st.markdown("<p style='text-align:center; padding: 60px; color: #999; font-style: italic;'>Nenhum registro de presença encontrado para este período.</p></div>", unsafe_allow_html=True)
    else:
        st.info("Nenhum membro vinculado a este grupo.")
