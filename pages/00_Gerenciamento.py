import streamlit as st
import pandas as pd
from supabase import create_client

# --- TRAVA DE SEGURANÇA (Obrigatório) ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.title("🔒 Acesso Restrito")
    st.warning("Área administrativa. Por favor, faça login na página inicial.")
    if st.button("Ir para o Login"):
        st.switch_page("app.py")
    st.stop()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gerenciamento", page_icon="⚙️", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("⚙️ Painel de Gerenciamento")
st.markdown("Controle total de membros, grupos e acessos ao sistema.")

# Criação das abas para organizar o gerenciamento
tab_p, tab_g, tab_u = st.tabs(["👥 Membros", "🏠 Grupos (GFs)", "🔐 Coordenadores"])

# --- ABA 1: GERENCIAR PESSOAS (MEMBROS) ---
with tab_p:
    st.subheader("Edição de Membros")
    res_p = supabase.table("pessoas").select("*").order("nome_completo").execute()
    if res_p.data:
        df_p = pd.DataFrame(res_p.data)
        
        # Seletor amigável
        p_escolhida = st.selectbox(
            "Selecione alguém para gerenciar", 
            res_p.data, 
            format_func=lambda x: f"{x['nome_completo']} ({'✅ Ativo' if x['ativo'] else '❌ Inativo'})"
        )
        
        with st.expander(f"📝 Editar Cadastro: {p_escolhida['nome_completo']}"):
            col1, col2 = st.columns(2)
            with col1:
                n_nome = st.text_input("Nome", p_escolhida['nome_completo'])
                n_tel = st.text_input("Telefone", p_escolhida['telefone'])
            with col2:
                n_ativo = st.toggle("Membro Ativo", value=p_escolhida['ativo'], help="Inativos não aparecem nas listas de chamada.")
            
            c_save, c_del, _ = st.columns([1, 1, 2])
            if c_save.button("Salvar Alterações", key="btn_save_p"):
                supabase.table("pessoas").update({
                    "nome_completo": n_nome,
                    "telefone": n_tel,
                    "ativo": n_ativo
                }).eq("id", p_escolhida["id"]).execute()
                st.success("Dados atualizados!")
                st.rerun()
            
            if c_del.button("🗑️ EXCLUIR", key="btn_del_p"):
                try:
                    supabase.table("pessoas").delete().eq("id", p_escolhida["id"]).execute()
                    st.success("Removido com sucesso!")
                    st.rerun()
                except:
                    st.error("Não é possível excluir membros que já possuem histórico de presença. Use a opção 'Inativar'.")

# --- ABA 2: GERENCIAR GRUPOS FAMILIARES ---
with tab_g:
    st.subheader("Edição de GFs")
    res_g = supabase.table("grupos_familiares").select("*").order("numero").execute()
    if res_g.data:
        g_escolhido = st.selectbox(
            "Selecione o Grupo", 
            res_g.data, 
            format_func=lambda x: f"GF {x['numero']} - {x['nome']} ({'Ativo' if x['ativo'] else 'Inativo'})"
        )
        
        with st.expander(f"🏠 Configurar {g_escolhido['nome']}"):
            g_num = st.number_input("Número do GF", value=g_escolhido['numero'])
            g_nom = st.text_input("Nome do GF", g_escolhido['nome'])
            g_pa = st.text_input("Público Alvo", g_escolhido['publico_alvo'])
            g_at = st.toggle("GF Ativo", value=g_escolhido['ativo'])
            
            if st.button("Atualizar GF"):
                supabase.table("grupos_familiares").update({
                    "numero": g_num,
                    "nome": g_nom,
                    "publico_alvo": g_pa,
                    "ativo": g_at
                }).eq("id", g_escolhido["id"]).execute()
                st.success("GF atualizado!")
                st.rerun()

# --- ABA 3: GERENCIAR USUÁRIOS (COORDENADORES) ---
with tab_u:
    st.subheader("Contas de Acesso")
    res_u = supabase.table("usuarios").select("*").execute()
    if res_u.data:
        u_escolhido = st.selectbox("Selecione o Usuário", res_u.data, format_func=lambda x: x['username'])
        
        with st.expander(f"🔐 Segurança: {u_escolhido['username']}"):
            u_nome = st.text_input("Nome de Exibição", u_escolhido['nome'])
            u_pass = st.text_input("Senha", u_escolhido['password'], type="password")
            u_ativ = st.toggle("Acesso Ativo", value=u_escolhido.get('ativo', True))
            
            if st.button("Salvar Usuário"):
                supabase.table("usuarios").update({
                    "nome": u_nome,
                    "password": u_pass,
                    "ativo": u_ativ
                }).eq("id", u_escolhido["id"]).execute()
                st.success("Usuário atualizado!")
                st.rerun()
