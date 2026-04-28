import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# --- TRAVA DE SEGURANÇA (Obrigatório em todas as páginas) ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Por favor, faça login na página inicial.")
    st.stop()

st.set_page_config(page_title="Lançar Presença", page_icon="📝", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("📝 Lançamento de Presença")

# 1. SELEÇÃO DO GRUPO E DATA
col1, col2 = st.columns(2)
with col1:
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).execute()
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

with col2:
    data_reuniao = st.date_input("Data da Reunião", date.today())

tema = st.text_input("Tema da Reunião (Opcional)")

# 2. BUSCAR MEMBROS DO GRUPO
if grupo_sel:
    # Busca pessoas vinculadas a este grupo específico
    res_m = supabase.table("membros_grupo").select("pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()
    membros = res_m.data

    if not membros:
        st.info("Este grupo ainda não possui membros vinculados.")
    else:
        st.subheader(f"Lista de Chamada - {grupo_sel['nome']}")
        
        # Criamos um dicionário para guardar quem está presente
        presencas_dict = {}
        
        for m in membros:
            nome = m["pessoas"]["nome_completo"]
            p_id = m["pessoa_id"]
            # Checkbox para cada pessoa
            presencas_dict[p_id] = st.checkbox(nome, key=f"p_{p_id}")

        # 3. SALVAR NO BANCO
        if st.form_submit_button("Salvar Presença") if False else st.button("Finalizar Chamada"):
            try:
                # Primeiro, cria o registro da reunião
                reuniao_res = supabase.table("reunioes").insert({
                    "grupo_id": grupo_sel["id"],
                    "data_reuniao": str(data_reuniao),
                    "tema": tema
                }).execute()
                
                reuniao_id = reuniao_res.data[0]["id"]
                
                # Depois, insere a lista de presença
                lista_presenca = []
                for p_id, presente in presencas_dict.items():
                    lista_presenca.append({
                        "reuniao_id": reuniao_id,
                        "pessoa_id": p_id,
                        "presente": presente
                    })
                
                supabase.table("presencas").insert(lista_presenca).execute()
                st.success("✨ Presença lançada com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

st.divider()
st.info("Dica: Os dados lançados aqui alimentarão os gráficos de crescimento dos GFs futuramente.")
