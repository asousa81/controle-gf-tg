import streamlit as st
from supabase import create_client

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Gestão GF's", page_icon="⛪", layout="centered")

# 2. CONEXÃO COM SUPABASE
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# 3. INICIALIZAÇÃO DO ESTADO DE SESSÃO
if "logado" not in st.session_state:
    st.session_state.logado = False
if "primeiro_acesso" not in st.session_state:
    st.session_state.primeiro_acesso = False # Nova flag para forçar a Home

# ... (outras variáveis de sessão: nome_usuario, usuario_id, perfil)
if "nome_usuario" not in st.session_state: st.session_state.nome_usuario = ""
if "usuario_id" not in st.session_state: st.session_state.usuario_id = None
if "perfil" not in st.session_state: st.session_state.perfil = "LIDER"

# 4. FLUXO DE LOGIN
if not st.session_state.logado:
    st.title("🔐 Portal de Gestão GF's")
    
    with st.form("login_form"):
        usuario_input = st.text_input("Usuário").lower().strip()
        senha_input = st.text_input("Senha", type="password")
        btn_login = st.form_submit_button("Entrar", use_container_width=True)
        
        if btn_login:
            res = supabase.table("pessoas").select("*").eq("usuario", usuario_input).eq("senha", senha_input).execute()
            
            if res.data:
                user = res.data[0]
                st.session_state.logado = True
                st.session_state.primeiro_acesso = True # ATIVA O REDIRECIONAMENTO
                st.session_state.usuario_id = user['id']
                st.session_state.nome_usuario = user['nome_completo']
                st.session_state.perfil = user.get('perfil', 'LIDER')
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos.")

else:
    # --- 5. ÁREA LOGADA (NAVEGAÇÃO) ---

    # Definição das Páginas
    pg_home = st.Page("pages/00_Boas_Vindas.py", title="Início", icon="👋", default=True)
    pg_gerenciamento = st.Page("pages/00_Gerenciamento.py", title="Gerenciamento", icon="⚙️")
    pg_pessoas = st.Page("pages/02_Pessoas.py", title="Gestão de Pessoas", icon="👥")
    pg_grupos = st.Page("pages/03_Grupos_Familiares.py", title="Grupos Familiares", icon="⛪")
    pg_vincular = st.Page("pages/04_Vincular_Membros.py", title="Vincular Membros", icon="🔗")
    pg_lancamento = st.Page("pages/05_Lancar_Presenca.py", title="Lançar Presença", icon="📝")
    pg_edicao = st.Page("pages/05_Editar_Presenca.py", title="Editar Presença", icon="✏️")
    pg_relatorios = st.Page("pages/06_Relatorios.py", title="Relatórios", icon="📈")

    # Montagem do Menu por Perfil
    if st.session_state.perfil == 'ADMIN':
        paginas_nav = {
            "Geral": [pg_home],
            "Administração": [pg_gerenciamento, pg_pessoas, pg_grupos, pg_vincular],
            "Operacional": [pg_lancamento, pg_edicao, pg_relatorios]
        }
    else:
        paginas_nav = {
            "Geral": [pg_home],
            "Minha Gestão": [pg_lancamento, pg_edicao, pg_relatorios]
        }

    pg = st.navigation(paginas_nav)

    # --- LÓGICA DE REDIRECIONAMENTO FORÇADO ---
    # Se for o primeiro acesso após o login, ignora a URL e pula para a Home
    if st.session_state.primeiro_acesso:
        st.session_state.primeiro_acesso = False # Desativa para permitir navegação depois
        st.switch_page(pg_home) # Força a troca de página fisicamente

    # Executa a renderização da página
    pg.run()
    
    # 6. SIDEBAR GLOBAL
    with st.sidebar:
        st.divider()
        st.write(f"Logado como: **{st.session_state.nome_usuario}**")
        if st.button("🚪 Sair do Sistema", use_container_width=True):
            st.session_state.logado = False
            st.rerun()
