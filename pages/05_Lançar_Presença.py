import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

# --- TRAVA DE SEGURANÇA ---
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
res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).execute()
if not res_g.data:
    st.info("Nenhum grupo cadastrado.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")
with col2:
    data_reuniao = st.date_input("Data da Reunião", date.today())

tema = st.text_input("Tema da Reunião (Opcional)")

# 2. BUSCAR MEMBROS E LIMPAR DUPLICATAS
if grupo_sel:
    res_m = supabase.table("membros_grupo").select("pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()
    
    if not res_m.data:
        st.info("Este grupo ainda não possui membros vinculados.")
    else:
        # 💡 O TRUQUE: Usamos um dicionário para remover duplicatas de pessoa_id automaticamente
        membros_unicos = {m["pessoa_id"]: m["pessoas"]["nome_completo"] for m in res_m.data if m["pessoas"]}
        
        st.subheader(f"Lista de Chamada")
        st.write("Marque quem compareceu:")
        
        presencas_dict = {}
        
        # Criamos as colunas para os checkboxes ficarem organizados
        cols = st.columns(3)
        for i, (p_id, nome) in enumerate(membros_unicos.items()):
            with cols[i % 3]:
                presencas_dict[p_id] = st.checkbox(nome, key=f"p_{p_id}")

        st.divider()
        
        # 3. BOTÃO DE SALVAR
        if st.button("🚀 Finalizar e Salvar Chamada", type="primary"):
            try:
                # Cria o registro da reunião
                reuniao_res = supabase.table("reunioes").insert({
                    "grupo_id": grupo_sel["id"],
                    "data_reuniao": str(data_reuniao),
                    "tema": tema
                }).execute()
                
                reuniao_id = reuniao_res.data[0]["id"]
                
                # Prepara a lista de presença (apenas quem foi marcado)
                dados_presenca = []
                for p_id, presente in presencas_dict.items():
                    if presente: # Opcional: você pode salvar apenas quem foi ou todos com True/False
                        dados_presenca.append({
                            "reuniao_id": reuniao_id,
                            "pessoa_id": p_id,
                            "presente": presente
                        })
                
                if dados_presenca:
                    supabase.table("presencas").insert(dados_presenca).execute()
                
                st.success(f"Presença de {len(dados_presenca)} pessoas registrada!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
