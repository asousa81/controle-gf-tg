import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Configuração da página
st.set_page_config(page_title="Grupos Familiares", page_icon="🏠", layout="wide")

# Função de conexão (repetimos aqui para garantir autonomia da página)
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

st.title("🏠 Cadastro de Grupos Familiares")

supabase = get_supabase_client()

# --- FORMULÁRIO DE CADASTRO ---
with st.form("form_grupo", clear_on_submit=True):
    col1, col2 = st.columns([1, 3])
    with col1:
        numero = st.number_input("Número do GF *", min_value=1, step=1)
    with col2:
        nome = st.text_input("Nome do Grupo Familiar (Opcional)")
    
    publico_alvo = st.text_input("Público-alvo (Ex: Adultos, Jovens, Casais)")

    salvar = st.form_submit_button("Salvar Grupo")

if salvar:
    data = {
        "numero": int(numero),
        "nome": nome.strip() if nome.strip() else f"GF {numero}",
        "publico_alvo": publico_alvo.strip() if publico_alvo.strip() else None,
        "ativo": True
    }

    try:
        supabase.table("grupos_familiares").insert(data).execute()
        st.success(f"Grupo {numero} cadastrado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao cadastrar grupo: {e}")

st.divider()

# --- LISTAGEM ---
st.subheader("📋 Grupos Cadastrados")

try:
    response = supabase.table("grupos_familiares").select("*").order("numero").execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.info("Nenhum grupo cadastrado ainda.")
    else:
        df = df.rename(columns={"numero": "Nº", "nome": "Nome do Grupo", "publico_alvo": "Público", "ativo": "Status"})
        st.dataframe(df[["Nº", "Nome do Grupo", "Público", "Status"]], use_container_width=True, hide_index=True)
except Exception as e:
    st.error(f"Erro ao carregar grupos: {e}")
