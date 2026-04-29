import streamlit as st
import pandas as pd
from supabase import create_client

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login na página inicial.")
    st.stop()

st.set_page_config(page_title="Vínculos", page_icon="🔗", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("🔗 Gestão de Vínculos e Papéis")
st.markdown("Organize a composição dos GFs definindo quem é Líder, Anfitrião ou Membro.")

# --- 1. FORMULÁRIO DE VÍNCULO ---
with st.expander("➕ Adicionar Novo Vínculo", expanded=True):
    try:
        # Busca pessoas e grupos ativos
        res_p = supabase.table("pessoas").select("id, nome_completo").eq("ativo", True).order("nome_completo").execute()
        res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
        
        if not res_p.data or not res_g.data:
            st.info("Certifique-se de ter Pessoas e Grupos cadastrados antes de vincular.")
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                p_sel = st.selectbox("Selecione a Pessoa", res_p.data, format_func=lambda x: x["nome_completo"])
            with col2:
                g_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")
            with col3:
                # Agora com a coluna 'funcao' que criamos no SQL
                funcao = st.selectbox("Função neste Grupo", ["MEMBRO", "LÍDER", "ANFITRIÃO", "CO-LÍDER", "VISITANTE"])

            if st.button("Confirmar Vínculo", type="primary"):
                try:
                    supabase.table("membros_grupo").insert({
                        "pessoa_id": p_sel["id"],
                        "grupo_id": g_sel["id"],
                        "funcao": funcao
                    }).execute()
                    st.success(f"✅ {p_sel['nome_completo']} vinculado como {funcao}!")
                    st.rerun()
                except Exception:
                    st.error("⚠️ Este vínculo já existe. Não é possível repetir a mesma pessoa na mesma função no mesmo grupo.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

st.divider()

# --- 2. LISTAGEM E GERENCIAMENTO ---
st.subheader("📋 Composição Atual dos Grupos")

try:
    # Busca vínculos com joins para trazer nomes em vez de IDs
    res_v = supabase.table("membros_grupo").select(
        "id, funcao, pessoas(nome_completo), grupos_familiares(numero, nome)"
    ).execute()

    if res_v.data:
        # Formata dados para exibição
        dados_tabela = []
        for v in res_v.data:
            # Proteção contra registros nulos caso alguém tenha sido excluído
            if v.get("pessoas") and v.get("grupos_familiares"):
                dados_tabela.append({
                    "ID_VINCULO": v["id"],
                    "Membro": v["pessoas"]["nome_completo"],
                    "Grupo Familiar": f"GF {v['grupos_familiares']['numero']} - {v['grupos_familiares']['nome']}",
                    "Função": v["funcao"]
                })
        
        df_vinc = pd.DataFrame(dados_tabela)
        
        # Filtro de busca simples
        busca = st.text_input("🔍 Filtrar por Nome ou Grupo")
        if busca:
            df_vinc = df_vinc[
                df_vinc['Membro'].str.contains(busca, case=False) | 
                df_vinc['Grupo Familiar'].str.contains(busca, case=False)
            ]

        # Exibe a tabela (sem mostrar o ID_VINCULO para o usuário)
        st.dataframe(df_vinc[["Membro", "Grupo Familiar", "Função"]], use_container_width=True, hide_index=True)

        # Ação de Exclusão
        with st.expander("🗑️ Remover Vínculos"):
            v_remover = st.selectbox(
                "Selecione o vínculo para deletar", 
                dados_tabela, 
                format_func=lambda x: f"{x['Membro']} ({x['Função']}) no {x['Grupo Familiar']}"
            )
            if st.button("Excluir Vínculo Selecionado"):
                supabase.table("membros_grupo").delete().eq("id", v_remover["ID_VINCULO"]).execute()
                st.warning("Vínculo removido com sucesso.")
                st.rerun()
    else:
        st.info("Nenhum vínculo cadastrado no momento.")

except Exception as e:
    st.error(f"Erro ao carregar a listagem: {e}")
