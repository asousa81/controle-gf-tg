import streamlit as st
from services.supabase_client import get_supabase_client

# 1. Configuração da Página (Sempre o primeiro comando)
st.set_page_config(
    page_title="Gestão de Grupos Familiares",
    page_icon="🏠",
    layout="wide"
)

# 2. Conexão com o Banco
try:
    supabase = get_supabase_client()
    conexao_ok = True
except Exception as e:
    conexao_ok = False
    st.error(f"Erro na conexão com o cofre de chaves: {e}")

# 3. Cabeçalho Principal
st.title("🏠 Portal de Gestão - Grupos Familiares")
st.markdown("---")

# 4. Conteúdo da Página Inicial
col_info, col_status = st.columns([2, 1])

with col_info:
    st.markdown(f"""
    ### Bem-vindo, Arthur!
    Este é o sistema centralizado para o controle de frequência e cuidado dos GFs. 
    A estrutura foi desenhada para facilitar o acompanhamento pastoral e a organização das métricas mensais.

    **Como começar:**
    1. Utilize o **menu lateral** para navegar.
    2. Comece cadastrando as pessoas na aba **02 Pessoas**.
    3. Em seguida, configure os grupos em **03 Grupos Familiares**.
    4. O fluxo segue até a geração do relatório mensal consolidado.
    """)

with col_status:
    st.subheader("Status do Sistema")
    if conexao_ok:
        st.success("Conexão com Supabase: Ativa")
        
        # Resumo rápido (Métricas)
        try:
            total_gfs = supabase.table("grupos_familiares").select("id", count="exact").execute().count
            total_pessoas = supabase.table("pessoas").select("id", count="exact").execute().count
            
            st.metric("GFs Ativos", total_gfs)
            st.metric("Pessoas no Sistema", total_pessoas)
        except:
            st.warning("Cadastre os primeiros dados para ver as métricas.")
    else:
        st.error("Conexão com Supabase: Inativa")

st.divider()
st.caption("Sistema desenvolvido para suporte à liderança e gestão de dados eclesiásticos.")
