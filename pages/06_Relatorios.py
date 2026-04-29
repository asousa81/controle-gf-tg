import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login para ver os relatórios.")
    st.stop()

st.set_page_config(page_title="Relatório Mensal", page_icon="📈", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("📈 Relatório Mensal de Desempenho - GFs")

# --- 1. FILTROS MENSAIS ---
with st.sidebar:
    st.header("📅 Período de Análise")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    mes_sel = st.selectbox("Mês", 
                           ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
                           index=datetime.now().month - 1)
    
    # Mapeamento para filtro no banco
    meses_map = {m: i+1 for i, m in enumerate(["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"])}
    mes_num = meses_map[mes_sel]

st.divider()

# --- 2. BUSCA DE DADOS ---
try:
    # Filtro SQL para o mês e ano selecionados
    data_inicio = f"{ano_sel}-{mes_num:02d}-01"
    # Lógica simples para o fim do mês
    data_fim = f"{ano_sel}-{mes_num:02d}-31" if mes_num != 12 else f"{ano_sel}-12-31"

    res = supabase.table("presencas").select(
        "data_reuniao, observacao, pessoas(nome_completo), grupos_familiares(numero, nome)"
    ).gte("data_reuniao", data_inicio).lte("data_reuniao", data_fim).execute()

    if res.data:
        df = pd.json_normalize(res.data)
        df.columns = ['Data', 'Observacao', 'Membro', 'GF_Num', 'GF_Nome']
        df['GF'] = "GF " + df['GF_Num'].astype(str) + " - " + df['GF_Nome']
        
        # --- 3. MÉTRICAS CONSOLIDADAS ---
        total_presentes = len(df)
        reunioes_mes = df['Data'].nunique()
        media_mensal = round(total_presentes / reunioes_mes, 1) if reunioes_mes > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Presenças Totais (Mês)", total_presentes)
        c2.metric("Total de Reuniões", reunioes_mes)
        c3.metric("Média de Engajamento", f"{media_mensal} pessoas/GF")

        st.divider()

        # --- 4. VISÃO POR GRUPO (OBSERVAÇÕES COLETIVAS) ---
        st.subheader(f"📝 Notas e Observações de {mes_sel}")
        
        # Agrupamos por Data e GF para pegar a observação única da reunião
        df_obs = df.groupby(['Data', 'GF'])['Observacao'].first().reset_index()
        
        for idx, row in df_obs.sort_values(by='Data', ascending=False).iterrows():
            with st.expander(f"🗓️ {row['Data']} | {row['GF']}"):
                st.write("**Relatório da Reunião:**")
                st.info(row['Observacao'] if row['Observacao'] else "Sem observações registradas.")
                
                # Lista quem estava presente nessa reunião específica
                presentes = df[df['Data'] == row['Data']]['Membro'].tolist()
                st.write(f"👥 **Presentes ({len(presentes)}):** {', '.join(presentes)}")

    else:
        st.info(f"Nenhum registro encontrado para {mes_sel} de {ano_sel}.")

except Exception as e:
    st.error(f"Erro ao gerar relatório mensal: {e}")
