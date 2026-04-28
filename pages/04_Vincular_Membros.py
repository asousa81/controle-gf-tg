import streamlit as st
import pandas as pd
from supabase import create_client, Client

st.set_page_config(page_title="Vincular Membros", page_icon="🔗", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

st.title("🔗 Vincular Pessoas aos Grupos")
supabase = get_supabase_client()

# --- BUSCA DE DADOS PARA OS SELETORES ---
try:
    # Busca pessoas ativas
    res_p = supabase.table("pessoas").select("id, nome_completo").eq("ativo", True).order("nome_completo").execute()
    lista_pessoas = res_p.data
    
    # Busca grupos ativos
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
    lista_grupos = res_g.data

    if not lista_pessoas or not lista_grupos:
        st.warning("⚠️ Certifique-se de ter Pessoas e Grupos cadastrados antes de realizar o vínculo.")
    else:
        # --- FORMULÁRIO ---
        with st.form("form_vinculo", clear_on_submit=True):
            st.subheader("Novo Vínculo")
            
            # Criamos dicionários para facilitar a exibição no selectbox
            pessoa_selecionada = st.selectbox(
                "Selecione a Pessoa", 
                options=lista_pessoas, 
                format_func=lambda x: x["nome_completo"]
            )
            
            grupo_selecionado = st.selectbox(
                "Selecione o Grupo Familiar", 
                options=lista_grupos, 
                format_func=lambda x: f"GF {x['numero']} - {x['nome']}"
            )
            
            obs = st.text_input("Observação (opcional)")
            
            if st.form_submit_button("Vincular Membro"):
                dados_vinculo = {
                    "pessoa_id": pessoa_selecionada["id"],
                    "grupo_id": grupo_selecionado["id"],
                    "ativo": True,
                    "observacao": obs
                }
                
                supabase.table("membros_grupo").insert(dados_vinculo).execute()
                st.success(f"✅ {pessoa_selecionada['nome_completo']} agora faz parte do {grupo_selecionado['nome']}!")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")

st.divider()

# --- LISTAGEM DE MEMBROS (Utilizando a View se existir ou Join simples) ---
st.subheader("📋 Composição Atual dos Grupos")
try:
    # Busca os vínculos atuais
    res_v = supabase.table("membros_grupo").select("id, pessoas(nome_completo), grupos_familiares(numero, nome)").eq("ativo", True).execute()
    
    if res_v.data:
        # Organiza os dados para o DataFrame
        dados_limpos = []
        for item in res_v.data:
            dados_limpos.append({
                "Membro": item["pessoas"]["nome_completo"],
                "Grupo": f"GF {item['grupos_familiares']['numero']} - {item['grupos_familiares']['nome']}"
            })
        
        st.dataframe(pd.DataFrame(dados_limpos), use_container_width=True, hide_index=True)
    else:
        st.info("Ainda não há membros vinculados a nenhum grupo.")
except Exception as e:
    st.info("Cadastre o primeiro vínculo para visualizar a lista.")
