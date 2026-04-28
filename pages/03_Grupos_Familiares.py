import streamlit as st
import pandas as pd
# VERIFICAÇÃO DE SEGURANÇA
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Por favor, faça login na página inicial para acessar este conteúdo.")
    st.stop() # Interrompe a execução do restante da página
from supabase import create_client, Client

st.set_page_config(page_title="Grupos Familiares", page_icon="🏠", layout="wide")
st.title("🏠 Cadastro de Grupos Familiares")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

with st.form("form_grupo", clear_on_submit=True):
    num = st.number_input("Número do GF *", min_value=1, step=1)
    nome_gf = st.text_input("Nome do Grupo")
    publico = st.text_input("Público-alvo")
    if st.form_submit_button("Salvar Grupo"):
        supabase.table("grupos_familiares").insert({"numero": int(num), "nome": nome_gf, "publico_alvo": publico}).execute()
        st.success(f"Grupo {num} salvo!")

st.divider()
try:
    res = supabase.table("grupos_familiares").select("*").order("numero").execute()
    if res.data:
        st.dataframe(pd.DataFrame(res.data)[["numero", "nome", "publico_alvo"]], use_container_width=True)
except:
    st.info("Cadastre o primeiro grupo para ver a lista.")
