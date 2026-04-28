import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="Vincular Membros", page_icon="🔗", layout="wide")

# Função de conexão
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("🔗 Vínculo de Membros ao GF")
supabase = get_supabase_client()

try:
    # 1. Busca Pessoas e Grupos para os seletores
    pessoas_data = supabase.table("pessoas").select("id, nome_completo").eq("ativo", True).execute().data
    grupos_data = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).execute().data

    if not pessoas_data or not grupos_data:
        st.warning("⚠️ Cadastre primeiro as Pessoas e os Grupos nas páginas anteriores.")
    else:
        # 2. Formulário de Vínculo
        with st.form("form_vinculo", clear_on_submit=True):
            p_sel = st.selectbox("Selecione a Pessoa", options=pessoas_data, format_func=lambda x: x["nome_completo"])
            g_sel = st.selectbox("Selecione o Grupo", options=grupos_data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")
            
            if st.form_submit_button("Vincular Agora"):
                supabase.table("membros_grupo").insert({
                    "pessoa_id": p_sel["id"],
                    "grupo_id": g_sel["id"],
                    "ativo": True
                }).execute()
                st.success("✅ Vínculo realizado com sucesso!")

    st.divider()

    # 3. Listagem Simples
    st.subheader("📋 Lista de Vínculos")
    vinc_res = supabase.table("membros_grupo").select("id, pessoas(nome_completo), grupos_familiares(numero, nome)").execute()
    
    if vinc_res.data:
        # Formata os dados para o usuário ler
        display_data = []
        for v in vinc_res.data:
            display_data.append({
                "Nome": v["pessoas"]["nome_completo"] if v.get("pessoas") else "N/A",
                "Grupo": f"GF {v['grupos_familiares']['numero']}" if v.get("grupos_familiares") else "N/A"
            })
        st.table(display_data)
    else:
        st.info("Nenhum vínculo criado ainda.")

except Exception as e:
    st.error(f"Aguardando estrutura: {e}")
