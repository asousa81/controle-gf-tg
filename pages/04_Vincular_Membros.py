import streamlit as st
import pandas as pd
# VERIFICAÇÃO DE SEGURANÇA
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Por favor, faça login na página inicial para acessar este conteúdo.")
    st.stop() # Interrompe a execução do restante da página
from supabase import create_client, Client

# 1. Configuração da página
st.set_page_config(page_title="Vincular Membros", page_icon="🔗", layout="wide")

# 2. Função de conexão centralizada
@st.cache_resource
def get_supabase_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

st.title("🔗 Vínculo de Membros ao Grupo Familiar")
st.markdown("Utilize esta página para organizar quem pertence a cada GF.")

supabase = get_supabase_client()

# --- CARREGAMENTO DE DADOS ---
try:
    # Busca pessoas e grupos ativos para os seletores
    res_pessoas = supabase.table("pessoas").select("id, nome_completo").eq("ativo", True).order("nome_completo").execute()
    res_grupos = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
    
    lista_pessoas = res_pessoas.data
    lista_grupos = res_grupos.data

    if not lista_pessoas or not lista_grupos:
        st.info("💡 Para realizar um vínculo, primeiro cadastre Pessoas e Grupos Familiares nas páginas anteriores.")
    else:
        # --- FORMULÁRIO DE VÍNCULO ---
        with st.form("form_vinculo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                pessoa_selecionada = st.selectbox(
                    "Selecione a Pessoa",
                    options=lista_pessoas,
                    format_func=lambda x: x["nome_completo"]
                )
            
            with col2:
                grupo_selecionado = st.selectbox(
                    "Selecione o Grupo Familiar",
                    options=lista_grupos,
                    format_func=lambda x: f"GF {x['numero']} - {x['nome']}"
                )
            
            observacao = st.text_input("Observação (opcional)")
            
            if st.form_submit_button("Confirmar Vínculo"):
                novo_vinculo = {
                    "pessoa_id": pessoa_selecionada["id"],
                    "grupo_id": grupo_selecionado["id"],
                    "ativo": True,
                    "observacao": observacao.strip() if observacao.strip() else None
                }
                
                supabase.table("membros_grupo").insert(novo_vinculo).execute()
                st.success(f"✅ {pessoa_selecionada['nome_completo']} vinculado ao {grupo_selecionado['nome']} com sucesso!")

    st.divider()

    # --- LISTAGEM DE COMPOSIÇÃO DOS GRUPOS ---
    st.subheader("📋 Composição Atual dos Grupos")
    
    # Busca os vínculos e traz os nomes relacionados
    res_vinc = supabase.table("membros_grupo").select(
        "id, pessoas(nome_completo), grupos_familiares(numero, nome)"
    ).eq("ativo", True).execute()

    if res_vinc.data:
        dados_tabela = []
        for item in res_vinc.data:
            dados_tabela.append({
                "Membro": item["pessoas"]["nome_completo"],
                "Grupo Familiar": f"GF {item['grupos_familiares']['numero']} - {item['grupos_familiares']['nome']}"
            })
        
        df_vinc = pd.DataFrame(dados_tabela)
        st.table(df_vinc)
    else:
        st.write("Ainda não existem membros vinculados aos grupos.")

except Exception as e:
    st.error("Erro ao carregar ou processar dados do banco.")
    with st.expander("Detalhes técnicos do erro"):
        st.code(e)
