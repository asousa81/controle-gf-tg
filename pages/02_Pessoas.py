import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="Pessoas", page_icon="👤", layout="wide")
st.title("👤 Cadastro de Pessoas")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

with st.form("form_pessoa", clear_on_submit=True):
    nome = st.text_input("Nome completo *")
    tel = st.text_input("Telefone")
    est_civil = st.selectbox("Estado civil", [1,2,3,4,5], format_func=lambda x: {1:"Casado", 2:"Solteiro", 3:"Casado s/ cônjuge", 4:"Viúvo", 5:"Divorciado"}[x])
    if st.form_submit_button("Salvar Pessoa"):
        if nome:
            supabase.table("pessoas").insert({"nome_completo": nome, "telefone": tel, "estado_civil_id": est_civil}).execute()
            st.success(f"{nome} cadastrado!")

st.divider()
try:
    res = supabase.table("pessoas").select("*").order("nome_completo").execute()
    if res.data:
        st.dataframe(pd.DataFrame(res.data)[["nome_completo", "telefone"]], use_container_width=True)
except:
    st.info("Nenhuma pessoa cadastrada.")
