import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta

st.set_page_config(page_title="Relatórios de Presença", page_icon="📊", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("📊 BI de Frequência e Saúde dos GFs")

# --- 1. FILTROS DE PESQUISA ---
with st.sidebar:
    st.header("🔍 Filtros de Análise")
    
    # Filtro de Data (Padrão: Últimos 30 dias)
    data_inicio = st.date_input("Início", value=datetime.now() - timedelta(days=30))
    data_fim = st.date_input("Fim", value=datetime.now())
    
    # Filtro de Grupo
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").order("numero").execute()
    g_opcoes = [{"id": "TODOS", "nome": "Todos os Grupos"}] + res_g.data
    grupo_sel = st.selectbox("Filtrar por Grupo", g_opcoes, format_func=lambda x: f"{x['nome']}")

st.divider()

# --- 2. BUSCA DE DADOS ---
try:
    # Query básica de presenças com joins
    query = supabase.table("presencas").select(
        "data_reuniao, observacao, pessoas(nome_completo), grupos_familiares(numero, nome)"
    ).gte("data_reuniao", str(data_inicio)).lte("data_reuniao", str(data_fim))
    
    if grupo_sel["id"] != "TODOS":
        query = query.eq("grupo_id", grupo_sel["id"])
        
    res_p = query.execute()

    if res_p.data:
        # Transformar em DataFrame para análise
        df = pd.json_normalize(res_p.data)
        
        # Renomear colunas para ficar "amigável"
        df.columns = ['Data', 'Observação', 'Membro', 'GF_Num', 'GF_Nome']
        df['GF'] = df['GF_Num'].astype(str) + " - " + df['GF_Nome']
        
        # --- 3. DASHBOARD DE MÉTRICAS ---
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_presencas = len(df)
            st.metric("Total de Presenças no Período", total_presencas)
            
        with col2:
            reunioes_distintas = df['Data'].nunique()
            st.metric("Total de Reuniões Realizadas", reunioes_distintas)
            
        with col3:
            media = round(total_presencas / reunioes_distintas, 1) if reunioes_distintas > 0 else 0
            st.metric("Média de Pessoas por Reunião", media)

        st.divider()

        # --- 4. VISUALIZAÇÕES ANALÍTICAS ---
        tab_detalhe, tab_ranking = st.tabs(["📋 Lista Detalhada", "🏆 Ranking de Frequência"])

        with tab_detalhe:
            st.write("### Histórico de Presenças")
            # Ordenar por data mais recente
            df_view = df[['Data', 'GF', 'Membro', 'Observação']].sort_values(by='Data', ascending=False)
            st.dataframe(df_view, use_container_width=True, hide_index=True)

        with tab_ranking:
            st.write("### Quem mais participou no período?")
            ranking = df['Membro'].value_counts().reset_index()
            ranking.columns = ['Nome do Membro', 'Vezes Presente']
            st.dataframe(ranking, use_container_width=True, hide_index=True)

    else:
        st.info("Nenhum registro de presença encontrado para os filtros selecionados.")

except Exception as e:
    st.error(f"Erro ao processar relatório: {e}")
