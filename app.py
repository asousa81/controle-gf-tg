import streamlit as st
from supabase import create_client

# 1. Configuração da Página (Sempre no topo)
st.set_page_config(page_title="Gestão CCM", page_icon="⛪", layout="centered")

# 2. Conexão com Supabase
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# 3. Inicialização Segura das Variáveis de Sessão
if "logado" not in st.session_state:
    st.session_state.logado = False
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = ""
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "perfil" not in st.session_state:
    st.session_state.perfil = "LIDER"

# 4. Fluxo de Autenticação e Navegação
if not st.session_state.logado:
    # --- TELA DE LOGIN ---
    st.title("🔐 Portal de Gestão CCM")
    with st.form("login_form"):
        usuario_input = st.text_input("Usuário").lower()
        senha_input = st.text_input("Senha", type="password")
        if st.form_submit_button("Entrar", use_container_width=True):
            res = supabase.table("pessoas").select("*").eq("usuario", usuario_input).eq("senha", senha_input).execute()
            if res.data:
                user = res.data[0]
                st.session_state.logado = True
                st.session_state.usuario_id = user['id']
                st.session_state.nome_usuario = user['nome_completo']
                st.session_state.perfil = user.get('perfil', 'LIDER')
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos.")
else:
    # --- ÁREA LOGADA (Onde o erro de indentação aconteceu) ---
    # Definimos as referências das páginas
    pg_lancamento = st.Page("pages/04_Lancamentos.py", title="Lançar Presença", icon="📝")
    pg_edicao = st.Page("pages/05_Editar_Presenca.py", title="Editar Presença", icon="✏️")
    pg_relatorios = st.Page("pages/06_Relatorios.py", title="Relatórios", icon="📊")
    
    # Páginas de Administração (Dashboard e Configurações)
    pg_dashboard = st.Page("pages/01_Dashboard.py", title="Dashboard Geral", icon="🏠")
    pg_membros = st.Page("pages/02_Membros.py", title="Gestão de Membros", icon="👥")
    pg_grupos = st.Page("pages/03_Grupos.py", title="Configurar GFs", icon="⚙️")

    # Controle de Navegação por Perfil
    if st.session_state.perfil == 'ADMIN':
        # Arthur e Simone Sousa veem tudo
        pg = st.navigation({
            "Administração": [pg_dashboard, pg_membros, pg_grupos],
            "Operacional": [pg_lancamento, pg_edicao, pg_relatorios]
        })
    else:
        # Líderes de Curitiba veem apenas o operacional
        pg = st.navigation({
            "Minha Gestão": [pg_lancamento, pg_edicao, pg_relatorios]
        })

    # Executa a página selecionada no menu
    pg.run()
    
    # Botão de Logout no final do Menu Lateral
    with st.sidebar:
        st.divider()
        if st.button("🚪 Sair do Sistema"):
            st.session_state.logado = False
            st.rerun()
