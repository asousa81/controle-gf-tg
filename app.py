import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Gestão de GFs", page_icon="🔐")

# Conexão
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# Inicializa o estado de login se não existir
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario = None

def realizar_login(user, pwd):
    res = supabase.table("usuarios").select("*").eq("username", user).eq("password", pwd).execute()
    if res.data:
        st.session_state.logado = True
        st.session_state.usuario = res.data[0]["nome"]
        st.success("Login realizado com sucesso!")
        st.rerun()
    else:
        st.error("Usuário ou senha incorretos.")

# --- INTERFACE ---
if not st.session_state.logado:
    st.title("🔐 Acesso Restrito")
    with st.form("login_form"):
        u = st.text_input("Usuário")
        p = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar"):
            realizar_login(u, p)
else:
    st.title(f"🏠 Bem-vindo, {st.session_state.usuario}!")
    st.write("O sistema está liberado. Use o menu lateral para navegar pelas funções de coordenação.")
    
    if st.button("Sair / Logoff"):
        st.session_state.logado = False
        st.session_state.usuario = None
        st.rerun()
