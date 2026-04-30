import streamlit as st
from supabase import create_client

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira linha de comando Streamlit)
st.set_page_config(page_title="Gestão GF's", page_icon="⛪", layout="centered")

# 2. CONEXÃO COM SUPABASE
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# 3. INICIALIZAÇÃO "BULLETPROOF" DO ESTADO (Evita AttributeError)
if "logado" not in st.session_state:
    st.session_state.logado = False
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = ""
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None
if "perfil" not in st.session_state:
    st.session_state.perfil = "LIDER"

# 4. FLUXO DE AUTENTICAÇÃO
if not st.session_state.logado:
    st.title("🔐 Portal de Gestão GF's")
    st.write("Bem-vindo ao sistema de gestão de Grupos Familiares.")
    
    with st.form("login_form"):
        usuario_input = st.text_input("Usuário").lower().strip()
        senha_input = st.text_input("Senha", type="password")
        btn_login = st.form_submit_button("Entrar", use_container_width=True)
        
        if btn_login:
            # Busca o usuário na tabela 'pessoas'
            res = supabase.table("pessoas").select("*").eq("usuario", usuario_input).eq("senha", senha_input).execute()
            
            if res.data:
                user = res.data[0]
                st.session_state.logado = True
                st.session_state.usuario_id = user['id']
                st.session_state.nome_usuario = user['nome_completo']
                st.session_state.perfil = user.get('perfil', 'LIDER') # Garante o perfil ADMIN ou LIDER
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos.")
else:
    # --- ÁREA LOGADA COM NAVEGAÇÃO DINÂMICA ---
    
    # Definição das Páginas (Mapeadas conforme sua estrutura de pastas atual)
    pg_gerenciamento = st.Page("pages/00_Gerenciamento.py", title="Gerenciamento", icon="🏠")
    pg_pessoas = st.Page("pages/02_Pessoas.py", title="Gestão de Pessoas", icon="👥")
    pg_grupos = st.Page("pages/03_Grupos_Familiares.py", title="Grupos Familiares", icon="⚙️")
    pg_vincular = st.Page("pages/04_Vincular_Membros.py", title="Vincular Membros", icon="🔗")
    
    # Páginas Operacionais (Acesso para Líderes e Admins)
    pg_lancamento = st.Page("pages/05_Lancar_Presenca.py", title="Lançar Presença", icon="📝")
    pg_edicao = st.Page("pages/05_Editar_Presenca.py", title="Editar Presença", icon="✏️")
    pg_relatorios = st.Page("pages/06_Relatorios.py", title="Relatórios", icon="📊")

    # Lógica de Visibilidade: Arthur e Simone (ADMIN) vs Líderes
    if st.session_state.perfil == 'ADMIN':
        pg = st.navigation({
            "Administração": [pg_gerenciamento, pg_pessoas, pg_grupos, pg_vincular],
            "Operacional": [pg_lancamento, pg_edicao, pg_relatorios]
        })
    else:
        pg = st.navigation({
            "Minha Gestão": [pg_lancamento, pg_edicao, pg_relatorios]
        })

    # Renderiza a página selecionada
    pg.run()
    
    # Botão de Logout no Menu Lateral
    with st.sidebar:
        st.divider()
        st.write(f"Logado como: **{st.session_state.nome_usuario}**")
        if st.button("🚪 Sair do Sistema", use_container_width=True):
            st.session_state.logado = False
            st.rerun()
