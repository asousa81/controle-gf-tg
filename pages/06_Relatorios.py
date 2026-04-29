import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login para ver os relatórios.")
    st.stop()

st.set_page_config(page_title="Relatórios de Presença", page_icon="📊", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("📊 BI de Frequência e Saúde dos GFs")

# --- 1. FILTROS DE PESQUISA ---
with st.sidebar:
    st.header("🔍 Filtros de Análise")
    data_inicio = st.date_input("Início", value=datetime.now() - timedelta(days=30))
    data_fim = st.date_input("Fim", value=datetime.now())
    
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").order("numero").execute()
    g_opcoes = [{"id": "TODOS", "nome": "Todos os Grupos"}] + res_g.data
    grupo_sel = st.selectbox("Filtrar por Grupo", g_opcoes, format_func=lambda x: f"{x['nome']}")

st.divider()

# --- 2. BUSCA E TRATAMENTO DE DADOS ---
try:
    query = supabase.table("presencas").select(
        "data_reuniao, observacao, pessoas(nome_completo), grupos_familiares(numero, nome)"
    ).gte("data_reuniao", str(data_inicio)).lte("data_reuniao", str(data_fim))
    
    if grupo_sel["id"] != "TODOS":
        query = query.eq("grupo_id", grupo_sel["id"])
        
    res_p = query.execute()

    if res_p.data:
        # 1. Criamos o DataFrame
        df_raw = pd.DataFrame(res_p.data)
        
        # 2. Achatamos as colunas aninhadas (pessoas e grupos_familiares)
        # Usamos uma abordagem mais segura para evitar erros de índice
        df = pd.json_normalize(res_p.data)
        
        # 3. Mapeamento explícito das colunas para evitar erros de ordem
        # O json_normalize cria nomes como 'pessoas.nome_completo'
        col_map = {
            'data_reuniao': 'Data',
            'observacao': 'Observação',
            'pessoas.nome_completo': 'Membro',
            'grupos_familiares.numero': 'GF_Num',
            'grupos_familiares.nome': 'GF_Nome'
        }
        df = df.rename(columns=col_map)

        # 4. FORÇAR TIPAGEM (Onde o erro acontecia)
        # Garantimos que os nomes sejam strings e os números sejam strings para a concatenação do nome do GF
        df['Membro'] = df['Membro'].astype(str)
        df['GF_Nome'] = df['GF_Nome'].astype(str)
        df['GF_Num'] = df['GF_Num'].astype(str)
        
        # Criamos a coluna combinada sem risco de conflito int vs str
        df['GF'] = "GF " + df['GF_Num'] + " - " + df['GF_Nome']
        
        # --- 3. DASHBOARD DE MÉTRICAS ---
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Presenças", len(df))
        with col2:
            reunioes = df['Data'].nunique()
            st.metric("Total de Reuniões", reunioes)
        with col3:
            media = round(len(df) / reunioes, 1) if reunioes > 0 else 0
            st.metric("Média por Reunião", media)

        st.divider()

        # --- 4. VISUALIZAÇÕES ---
        tab_detalhe, tab_ranking = st.tabs(["📋 Lista Detalhada", "🏆 Ranking de Frequência"])

        with tab_detalhe:
            # Ordenação garantida por data
            df_view = df[['Data', 'GF', 'Membro', 'Observação']].sort_values(by='Data', ascending=False)
            st.dataframe(df_view, use_container_width=True, hide_index=True)

        with tab_ranking:
            st.write("### Frequência por Membro")
            ranking = df['Membro'].value_counts().reset_index()
            ranking.columns = ['Nome do Membro', 'Vezes Presente']
            st.dataframe(ranking, use_container_width=True, hide_index=True)

    else:
        st.info("Nenhum registro de presença encontrado para este período.")

except Exception as e:
    st.error(f"Erro ao processar relatório: {e}")
