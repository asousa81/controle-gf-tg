import streamlit as st
from supabase import create_client, Client

# Configuração da página
st.set_page_config(page_title="Relatórios GFs", page_icon="📋", layout="wide")

# Função para conectar ao banco usando as chaves secretas
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

st.title("📋 Sistema de Relatórios de Grupos Familiares")
st.markdown("---")

# Teste de Conexão
try:
    supabase = get_supabase_client()
    st.success("🟢 Conectado ao Supabase com sucesso!")
    
    # Faz uma pequena busca no banco apenas para provar que a comunicação está funcionando
    res = supabase.table("grupos_familiares").select("id", count="exact").execute()
    st.info(f"O banco de dados está respondendo perfeitamente! (Total de grupos cadastrados: {res.count})")
    
except Exception as e:
    st.error("🔴 Ops! Houve um erro de conexão.")
    st.code(e)
    st.warning("Verifique se as aspas e as chaves estão corretas lá na aba 'Secrets' do Streamlit.")
