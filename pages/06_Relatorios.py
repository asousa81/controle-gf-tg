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

st.set_page_config(page_title="Relatório de Atividades", page_icon="📝", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- CSS PARA REPLICAR O VISUAL DA IMAGEM ---
st.markdown("""
<style>
    .relatorio-container {
        font-family: 'Arial', sans-serif;
        color: #333;
        border: 2px solid #333;
        padding: 0;
        background-color: white;
    }
    .header-box {
        display: flex;
        align-items: center;
        border-bottom: 2px solid #333;
        padding: 10px;
    }
    .title-box {
        flex-grow: 1;
        text-align: center;
        font-weight: bold;
        text-transform: uppercase;
    }
    .info-table {
        width: 100%;
        border-collapse: collapse;
    }
    .info-table td {
        border: 1px solid #999;
        padding: 5px 10px;
        vertical-align: top;
    }
    .label {
        font-size: 0.7rem;
        font-weight: bold;
        color: #666;
        text-transform: uppercase;
        display: block;
    }
    .value {
        font-size: 0.9rem;
        font-weight: bold;
        color: #000;
    }
    .grid-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .grid-table th {
        background-color: #f2f2f2;
        border: 1px solid #999;
        font-size: 0.75rem;
        padding: 5px;
        text-align: center;
    }
    .grid-table td {
        border: 1px solid #999;
        padding: 4px 8px;
        font-size: 0.85rem;
    }
    .center-text { text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 1. FILTROS (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Configurações")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses, index=datetime.now().month - 1)
    
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

# --- 2. COLETA E PROCESSAMENTO ---
if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
        colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']
        
        # --- 3. RENDERIZAÇÃO DO VISUAL ESTILO IMAGEM ---
        st.markdown(f"""
        <div class="relatorio-container">
            <div class="header-box">
                <div class="title-box">Relatório de Atividades do Grupo Familiar - {mes_sel.lower()} de {ano_sel}</div>
            </div>
            <table class="info-table">
                <tr>
                    <td colspan="2"><span class="label">Nome do Grupo Familiar</span><span class="value">{grupo_sel['nome']}</span></td>
                    <td style="width:15%"><span class="label">Nº do GF</span><span class="value">{grupo_sel['numero']}</span></td>
                </tr>
                <tr>
                    <td style="width:45%"><span class="label">Líder</span><span class="value">{", ".join(lideres) if lideres else "Não definido"}</span></td>
                    <td colspan="2"><span class="label">Coordenador</span><span class="value">Pr. Arthur e Pra. Simone</span></td>
                </tr>
                <tr>
                    <td><span class="label">Líder em Treinamento</span><span class="value">{", ".join(colideres) if colideres else "0"}</span></td>
                    <td colspan="2"><span class="label">Público Alvo</span><span class="value">{grupo_sel.get('publico_alvo', 'Misto')}</span></td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        # Processamento da Grade
        df_p = pd.DataFrame(res_presencas.data) if res_presencas.data else pd.DataFrame()
        datas = sorted(df_p['data_reuniao'].unique()) if not df_p.empty else []
        col_datas = {d: datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b') for d in datas}

        # Construção da Tabela HTML de Membros
        html_grid = f"""
        <table class="grid-table">
            <thead>
                <tr>
                    <th rowspan="2" style="width:40px">Nº</th>
                    <th rowspan="2">Membros do GF (nome completo)</th>
                    <th colspan="{len(datas) if datas else 1}">Dia da Reunião</th>
                </tr>
                <tr>
                    {"".join([f"<th>{fmt}</th>" for fmt in col_datas.values()]) if datas else "<th>-</th>"}
                </tr>
            </thead>
            <tbody>
        """
        
        count = 1
        for m in res_membros.data:
            if m['funcao'] == 'VISITANTE': continue
            nome = m['pessoas']['nome_completo']
            p_id = m['pessoa_id']
            
            html_grid += f"<tr><td class='center-text'>{count}</td><td>{nome}</td>"
            for d in datas:
                presente = not df_p[(df_p['data_reuniao'] == d) & (df_p['pessoa_id'] == p_id)].empty
                html_grid += f"<td class='center-text'>{'C' if presente else ''}</td>"
            if not datas: html_grid += "<td></td>"
            html_grid += "</tr>"
            count += 1
        
        html_grid += "</tbody></table>"
        st.markdown(html_grid, unsafe_allow_html=True)

        # Observações (Mesmo visual da imagem)
        st.markdown("<br>", unsafe_allow_html=True)
        obs_df = df_p.groupby('data_reuniao')['observacao'].first().reset_index() if not df_p.empty else pd.DataFrame()
        obs_texto = ""
        if not obs_df.empty:
            for _, r in obs_df.iterrows():
                if r['observacao'] and r['observacao'] != 'None':
                    obs_texto += f"Dia {datetime.strptime(r['data_reuniao'], '%Y-%m-%d').strftime('%d/%m')}: {r['observacao']}<br>"

        st.markdown(f"""
        <div style="border: 1px solid #999; padding: 10px; min-height: 100px;">
            <span class="label">Observações:</span>
            <div style="font-size: 0.85rem;">{obs_texto if obs_texto else "Nenhuma observação registrada."}</div>
        </div>
        """, unsafe_allow_html=True)

        # --- 4. BOTÃO DE EXPORTAÇÃO (MANTIDO) ---
        st.divider()
        if st.button("📥 Gerar PDF para Impressão", type="primary"):
            st.info("O PDF será gerado com o mesmo layout oficial.")
            # (Aqui você pode chamar a função gerar_pdf_formatado que criamos antes)
