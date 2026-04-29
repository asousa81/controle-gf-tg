import streamlit as st
import pandas as pd
from supabase import create_client

# --- TRAVA DE SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito aos Coordenadores.")
    st.stop()

st.set_page_config(page_title="Gerenciamento", page_icon="⚙️", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("⚙️ Painel de Controle Administrativo")
st.markdown("Gerencie aqui os cadastros do sistema.")

tab1, tab2, tab3 = st.tabs(["👥 Pessoas", "🏠 Grupos Familiares", "🔐 Usuários do Sistema"])

# --- ABA 1: GERENCIAR PESSOAS ---
with tab1:
    st.subheader("Gerenciar Membros")
    res_p = supabase.table("pessoas").select("*").order("nome_completo").execute()
    df_p = pd.DataFrame(res_p.data)

    if not df_p.empty:
        # Seletor para editar
        pessoa_edit = st.selectbox("Selecione uma pessoa para editar", df_p, format_func=lambda x: f"{x['nome_completo']} ({'Ativo' if x['ativo'] else 'Inativo'})")
        
        with st.expander(f"Editar: {pessoa_edit['nome_completo']}"):
            new_nome = st.text_input("Nome Completo", pessoa_edit['nome_completo'])
            new_tel = st.text_input("Telefone", pessoa_edit['telefone'])
            new_ativo = st.toggle("Conta Ativa", value=pessoa_edit['ativo'])
            
            c1, c2, _ = st.columns([1,1,2])
            if c1.button("Salvar Alterações", key="save_p"):
                supabase.table("pessoas").update({
                    "nome_completo": new_nome,
                    "telefone": new_tel,
                    "ativo": new_ativo
                }).eq("id", pessoa_edit["id"]).execute()
                st.success("Dados atualizados!")
                st.rerun()
            
            if c2.button("❌ EXCLUIR PERMANENTEMENTE", key="del_p"):
                # Nota: Só funcionará se não houver presenças vinculadas (por causa da integridade)
                try:
                    supabase.table("pessoas").delete().eq("id", pessoa_edit["id"]).execute()
                    st.success("Pessoa excluída!")
                    st.rerun()
                except:
                    st.error("Não é possível excluir: esta pessoa possui histórico de presenças. Inative-a em vez de excluir.")

# --- ABA 2: GERENCIAR GRUPOS ---
with tab2:
    st.subheader("Gerenciar GFs")
    res_g = supabase.table("grupos_familiares").select("*").order("numero").execute()
    df_g = pd.DataFrame(res_g.data)

    if not df_g.empty:
        grupo_edit = st.selectbox("Selecione um grupo", df_g.to_dict('records'), format_func=lambda x: f"GF {x['numero']} - {x['nome']}")
        
        with st.expander(f"Editar: {grupo_edit['nome']}"):
            g_nome = st.text_input("Nome do Grupo", grupo_edit['nome'])
            g_num = st.number_input("Número", value=grupo_edit['numero'])
            g_ativo = st.toggle("Grupo Ativo", value=grupo_edit['ativo'], key="tg_g")
            
            if st.button("Atualizar Grupo"):
                supabase.table("grupos_familiares").update({
                    "nome": g_nome,
                    "numero": g_num,
                    "ativo": g_ativo
                }).eq("id", grupo_edit["id"]).execute()
                st.success("Grupo atualizado!")
                st.rerun()

# --- ABA 3: GERENCIAR USUÁRIOS (LOGIN) ---
with tab3:
    st.subheader("Contas de Coordenadores")
    res_u = supabase.table("usuarios").select("*").execute()
    df_u = pd.DataFrame(res_u.data)

    if not df_u.empty:
        user_edit = st.selectbox("Selecione um coordenador", df_u.to_dict('records'), format_func=lambda x: x['username'])
        
        with st.expander(f"Editar Usuário: {user_edit['username']}"):
            u_nome = st.text_input("Nome Exibição", user_edit['nome'])
            u_senha = st.text_input("Nova Senha (deixe igual para não mudar)", user_edit['password'])
            u_ativo = st.toggle("Usuário Ativo", value=user_edit.get('ativo', True))
            
            if st.button("Salvar Usuário"):
                supabase.table("usuarios").update({
                    "nome": u_nome,
                    "password": u_senha,
                    "ativo": u_ativo
                }).eq("id", user_edit["id"]).execute()
                st.success("Usuário atualizado!")
                st.rerun()
