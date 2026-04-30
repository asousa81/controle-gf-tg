import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Por favor, faça login para acessar os relatórios.")
    st.stop()

st.set_page_config(page_title="Relatório Executivo", page_icon="📈", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- CSS PREMIMUM (Refinado para eliminar o 'quadradão') ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 15px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); text-align: center;
    }
    .paper-container {
        background-color: white; border-radius: 15px;
        padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        margin-top: 15px; border: 1px solid #eee;
    }
    .header-grid {
        display: grid; grid-template-columns: 2fr 1fr; gap: 15px;
        margin-bottom: 25px; padding-bottom: 15px; border-bottom: 2px solid #f4f4f4;
    }
    .info-item { margin-bottom: 8px; }
    .label { font-size: 0.75rem; color: #888; text-transform: uppercase; font-weight: 700; display: block; }
    .value { font-size: 1rem; color: #222; font-weight: 600; }
    
    .styled-table {
        width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 0.85rem;
    }
    .styled-table thead th {
        background-color: #f8f9fa; color: #444; padding: 12px;
        border: 1px solid #eee; text-align: center; font-weight: 700;
    }
    .styled-table td { padding: 10px; border: 1px solid #eee; text-align: center; }
    
    .badge-c { background-color: #d4edda; color: #155724; padding: 4px 8px; border-radius: 6px; font-weight: 700; }
    .badge-f { background-color: #f8d7da; color: #721c24; padding: 4px 8px; border-radius: 6px; font-weight: 700; }
    
    .obs-section {
        background: #fdfdfd; border-radius: 8px; padding: 15px;
        margin-top: 20px; border-left: 5px solid #764ba2;
    }
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

        # --- SEÇÃO DE INSIGHTS (Limpas e diretas) ---
        c1, c2, c3 = st.columns(3)
        total_m = len([m for m in res_membros.data if m['funcao'] != 'VISITANTE'])
        reunioes_m = len(set(p['data_reuniao'] for p in res_presencas.data)) if res_presencas.data else 0
        with c1: st.markdown(f'<div class="metric-card"><small>MEMBROS ATIVOS</small><h2>{total_m}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><small>ENCONTROS NO MÊS</small><h2>{reunioes_m}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><small>TIPO DE GRUPO</small><h4>{grupo_sel.get("publico_alvo", "Misto")}</h4></div>', unsafe_allow_html=True)

        # --- RELATÓRIO VISUAL ---
        st.markdown(f"""
<div class="paper-container">
    <div style="text-align: center; margin-bottom: 25px;">
        <h2 style="color: #764ba2; margin: 0;">RELATÓRIO DE ATIVIDADES</h2>
        <span style="color: #999; font-weight: 600;">{mes_sel.upper()} / {ano_sel}</span>
    </div>
    
    <div class="header-grid">
        <div>
            <div class="info-item"><span class="label">NOME DO GRUPO FAMILIAR</span><span class="value">GF {grupo_sel['numero']} - {grupo_sel['nome']}</span></div>
            <div class="info-item"><span class="label">LIDERANÇA</span><span class="value">{", ".join(lideres) if lideres else "Não definido"}</span></div>
            <div class="info-item"><span class="label">LÍDER EM TREINAMENTO</span><span class="value">{", ".join(colideres) if colideres else "Nenhum"}</span></div>
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
            datas = sorted(df_p['data_reuniao'].unique())
            
            # Cabeçalho da Tabela
            table_html = f"""<table class="styled-table"><thead><tr><th rowspan="2" style="width: 50px;">Nº</th><th rowspan="2" style="text-align: left;">MEMBROS DO GF</th><th colspan="{len(datas)}">DIAS DE ENCONTRO</th></tr><tr>"""
            table_html += "".join([f"<th>{datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')}</th>" for d in datas])
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
            
            # Linhas de Horários (Conforme imagem referência)
            table_html += f"<tr style='background: #fafafa;'><td colspan='2' style='text-align: right; font-weight: 700;'>HORÁRIO INÍCIO</td>"
            for d in datas: table_html += f"<td style='font-size: 0.75rem;'>{grupo_sel.get('horario', '20:00')}</td>"
            table_html += "</tr>"
            
            table_html += f"<tr style='background: #fafafa;'><td colspan='2' style='text-align: right; font-weight: 700;'>HORÁRIO TÉRMINO</td>"
            for d in datas: table_html += f"<td style='font-size: 0.75rem;'>21:30</td>"
            table_html += "</tr></tbody></table>"
            
            st.markdown(table_html, unsafe_allow_html=True)

            # Seção de Observações
            st.markdown('<div class="obs-section"><span class="label">Observações e Pedidos de Oração</span>', unsafe_allow_html=True)
            df_obs = df_p.groupby('data_reuniao')['observacao'].first().reset_index()
            for _, r in df_obs.iterrows():
                if r['observacao'] and r['observacao'] != 'None':
                    st.write(f"**• {datetime.strptime(r['data_reuniao'], '%Y-%m-%d').strftime('%d/%m')}:** {r['observacao']}")
            st.markdown('</div></div>', unsafe_allow_html=True)

            st.divider()
            st.button("📥 Baixar Versão para Impressão (PDF)", type="primary", use_container_width=True)
        else:
            st.markdown("<p style='text-align:center; padding: 40px; color: #999;'>Aguardando lançamentos de presença para este período...</p></div>", unsafe_allow_html=True)
    else:
        st.info("Cadastre os membros deste grupo primeiro.")
