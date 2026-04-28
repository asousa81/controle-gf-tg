import streamlit as st
import pandas as pd
from supabase import create_client, Client

# 1. Configuração inicial
st.set_page_config(page_title="Diagnóstico Supremo", page_icon="🔍")

# 2. Função para pegar as chaves do "cofre" (Secrets)
@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

st.title("🔍 Diagnóstico de Conexão")

try:
    # 3. Criando o cliente (apresentando o 'supabase' ao código)
    supabase = get_supabase_client()
    
    st.subheader("Teste de Acesso Direto")
    
    # 4. Tentativa de ler a tabela 'pessoas'
    # Usamos .from_() que é um método padrão da biblioteca
    res = supabase.from_("pessoas").select("*", count="exact").limit(1).execute()
    
    st.success(f"✅ Sucesso! Conectamos na tabela 'pessoas'.")
    st.write(f"Total de registros encontrados: {res.count}")

except Exception as e:
    st.error("❌ Falha na conexão")
    st.code(e)
    
    st.markdown("---")
    st.warning("### 🧐 O que conferir agora:")
    st.write("""
    Se o erro for **PGRST125**, o problema é 100% de comunicação. Confira:
    1. **Secrets no Streamlit:** Se a URL não tem um '/' sobrando no final.
    2. **Tabelas no Supabase:** Se elas estão no schema **'public'**.
    3. **Permissões (RLS):** No Supabase, vá em **Authentication > Policies** e veja se as tabelas estão abertas para leitura (ou se o RLS está desativado para teste).
    """)
