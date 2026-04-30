import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Gestão GF's - Login", page_icon=" 교회", layout="centered")

# --- CONEXÃO ---
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- INICIALIZAÇÃO "BULLETPROOF" DO ESTADO ---
# Coloque isso logo após o get_supabase_client()
if "logado" not in st.session_state:
    st.session_state.logado = False
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = ""
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "perfil" not in st.session_state:
    st.session_state.perfil = "LIDER"

# --- TELA DE LOGIN ---
if not st.session_state.logado:
    st.title("⛪ Portal de Gestão GF's")
    st.subheader("Acesse com seu usuário e senha")
    
    with st.form("login_form"):
        # Alterado de E-mail para Usuário
        usuario_input = st.text_input("Usuário", placeholder="ex: arthur.sousa")
        senha_input = st.text_input("Senha", type="password")
        btn_login = st.form_submit_button("Entrar no Sistema", use_container_width=True)
        
        if btn_login:
            # Busca direta pelo campo 'usuario'
            res = supabase.table("pessoas").select("*").eq("usuario", usuario_input.lower()).eq("senha", senha_input).execute()
            
            if res.data:
                user = res.data[0]
                st.session_state.logado = True
                st.session_state.usuario_id = user['id']
                st.session_state.nome_usuario = user['nome_completo']
                st.session_state.perfil = user.get('perfil', 'LIDER')
                
                st.success(f"Bem-vindo, {user['nome_completo']}!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos.")
else:
    # --- DEFINIÇÃO DE PÁGINAS (app.py) ---
if st.session_state.logado:
    # Definimos as páginas disponíveis
    pg_lancamento = st.Page("pages/04_Lancamentos.py", title="Lançar Presença", icon="📝")
    pg_edicao = st.Page("pages/05_Editar_Presenca.py", title="Editar Presença", icon="✏️")
    pg_relatorios = st.Page("pages/06_Relatorios.py", title="Relatórios", icon="📊")
    
    # Páginas exclusivas de ADMIN (Arthur e Simone)
    pg_dashboard = st.Page("pages/01_Dashboard.py", title="Dashboard Geral", icon="🏠")
    pg_membros = st.Page("pages/02_Membros.py", title="Gestão de Membros", icon="👥")
    pg_grupos = st.Page("pages/03_Grupos.py", title="Configurar GFs", icon="⚙️")

    # --- LÓGICA DE VISIBILIDADE ---
    if st.session_state.perfil == 'ADMIN':
        # Você e a Pra. Simone veem TUDO
        pg = st.navigation({
            "Administração": [pg_dashboard, pg_membros, pg_grupos],
            "Operacional": [pg_lancamento, pg_edicao, pg_relatorios]
        })
    else:
        # Líderes veem apenas o essencial
        pg = st.navigation({
            "Minha Gestão": [pg_lancamento, pg_edicao, pg_relatorios]
        })
    
    pg.run()
    
    if st.session_state.perfil == 'ADMIN':
        st.success("👑 Modo Coordenador Ativo: Acesso total liberado.")
    else:
        st.info("📋 Modo Líder Ativo: Visualizando seus grupos vinculados.")
    
    st.divider()
    if st.button("🚪 Sair do Sistema"):
        st.session_state.logado = False
        st.rerun()
