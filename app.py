# app.py
import streamlit as st
from supabase import create_client, Client

# Configuração da página
st.set_page_config(page_title="Gestão de GFs", page_icon="🏠", layout="wide")

# Função de conexão direta (sem precisar de pasta externa por enquanto)
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

st.title("🏠 Portal de Gestão - Grupos Familiares")
st.markdown("---")

try:
    supabase = get_supabase_client()
    st.success("🟢 Conectado ao Supabase!")
    
    st.markdown("""
    ### Bem-vindo!
    O sistema está online. 
    
    **Próximos passos:**
    1. Crie uma pasta chamada `pages` no seu GitHub.
    2. Coloque os arquivos de cadastro (como o `02_Pessoas.py`) dentro dessa pasta.
    """)
    
except Exception as e:
    st.error("🔴 Erro de conexão. Verifique se os 'Secrets' foram salvos corretamente.")
    st.exception(e)
