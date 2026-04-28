import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="Vincular Membros", page_icon="🔗", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("🔗 Vínculo de Membros ao GF")
supabase = get_supabase_client()

try:
    # Busca dados das tabelas individualmente para teste
    res_p = supabase.table("pessoas").select("id, nome_completo").eq("ativo", True).execute()
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).execute()
    
    pessoas = res_p.data
    grupos = res_g.data

    if not pessoas or not grupos:
        st.warning("Cadastre pessoas e grupos antes de fazer o vínculo.")
    else:
        with st.form("form_vinculo"):
            p_sel = st.selectbox("Pessoa", options=pessoas, format_func=lambda x: x["nome_completo"])
            g_sel = st.selectbox("Grupo", options=grupos, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")
            
            if st.form_submit_button("Vincular"):
                supabase.table("membros_grupo").insert({
                    "pessoa_id": p_sel["id"],
                    "grupo_id": g_sel["id"],
                    "ativo": True
                }).execute()
                st.success("Vínculo realizado!")

except Exception as e:
    st.error(f"Erro de conexão com as tabelas: {e}")

st.divider()

# Listagem simples sem 'joins' complexos para evitar o erro PGRST125
st.subheader("📋 Composição dos Grupos")
try:
    res_v = supabase.table("membros_grupo").select("*").eq("ativo", True).execute()
    if res_v.data:
        st.write(f"Existem {len(res_v.data)} vínculos cadastrados.")
        st.dataframe(pd.DataFrame(res_v.data), use_container_width=True)
    else:
        st.info("Nenhum vínculo encontrado.")
except Exception as e:
    st.info("Aguardando o primeiro vínculo para exibir a lista.")
