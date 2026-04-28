import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="Diagnóstico de Conexão", page_icon="🔍")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("🔍 Diagnóstico de Estrutura")
supabase = get_supabase_client()

# --- TESTE 1: TABELA PESSOAS ---
st.subheader("1. Testando Tabela 'pessoas'")
try:
    p = supabase.table("pessoas").select("count", count="exact").execute()
    st.success(f"✅ Tabela 'pessoas' encontrada! (Total: {p.count})")
except Exception as e:
    st.error(f"❌ Erro na tabela 'pessoas': {e}")

# --- TESTE 2: TABELA GRUPOS ---
st.subheader("2. Testando Tabela 'grupos_familiares'")
try:
    g = supabase.table("grupos_familiares").select("count", count="exact").execute()
    st.success(f"✅ Tabela 'grupos_familiares' encontrada! (Total: {g.count})")
except Exception as e:
    st.error(f"❌ Erro na tabela 'grupos_familiares': {e}")

# --- TESTE 3: TABELA VÍNCULOS ---
st.subheader("3. Testando Tabela 'membros_grupo'")
try:
    m = supabase.table("membros_grupo").select("count", count="exact").execute()
    st.success(f"✅ Tabela 'membros_grupo' encontrada! (Total: {m.count})")
except Exception as e:
    st.error(f"❌ Erro na tabela 'membros_grupo': {e}")

# --- TESTE 4: TESTE DE RELACIONAMENTO (O provável culpado) ---
st.subheader("4. Testando Relacionamento (Join)")
try:
    # Tenta buscar o nome da pessoa através da tabela de vínculos
    res = supabase.table("membros_grupo").select("id, pessoas(nome_completo)").limit(1).execute()
    st.success("✅ Relacionamento entre tabelas está funcionando!")
except Exception as e:
    st.warning(f"⚠️ O relacionamento falhou: {e}")
    st.info("Isso acontece se o Supabase ainda não reconheceu as 'Foreign Keys' (chaves estrangeiras).")

st.markdown("---")
st.info("Tire um print desse diagnóstico para eu ver qual item ficou vermelho.")
