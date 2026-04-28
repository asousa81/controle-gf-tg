import streamlit as st
import pandas as pd
from datetime import date, time
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

col_gf, col_dt = st.columns(2)
with col_gf:
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")
with col_dt:
    data_reuniao = st.date_input("Data da Reunião", date.today())

# --- NOVOS CAMPOS DE HORÁRIO ---
col_ini, col_fim = st.columns(2)
with col_ini:
    h_inicio = st.time_input("Horário de Início", time(19, 30)) # Sugestão padrão 19:30
with col_fim:
    h_fim = st.time_input("Horário de Término", time(21, 00))   # Sugestão padrão 21:00

# Substituindo Tema por Observações
obs = st.text_area("Observações da Reunião", placeholder="Pedidos de oração, testemunhos ou avisos importantes...")

# 2. BUSCAR MEMBROS E LIMPAR DUPLICATAS
if grupo_sel:
    res_m = supabase.table("membros_grupo").select("pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()
    
    if not res_m.data:
        st.info("Este grupo ainda não possui membros vinculados.")
    else:
        # Garante membros únicos
        membros_unicos = {m["pessoa_id"]: m["pessoas"]["nome_completo"] for m in res_m.data if m["pessoas"]}
        
        st.subheader("Lista de Presença")
        st.write("Selecione quem esteve presente:")
        
        presencas_dict = {}
        cols = st.columns(3)
        for i, (p_id, nome) in enumerate(membros_unicos.items()):
            with cols[i % 3]:
                presencas_dict[p_id] = st.checkbox(nome, key=f"p_{p_id}")

        st.divider()
        
        # 3. BOTÃO DE SALVAR
        if st.button("🚀 Finalizar e Salvar Chamada", type="primary"):
            try:
                # Cria o registro da reunião com os novos campos
                reuniao_res = supabase.table("reunioes").insert({
                    "grupo_id": grupo_sel["id"],
                    "data_reuniao": str(data_reuniao),
                    "hora_inicio": str(h_inicio),
                    "hora_fim": str(h_fim),
                    "observacoes": obs
                }).execute()
                
                reuniao_id = reuniao_res.data[0]["id"]
                
                # Prepara e insere a lista de presença (apenas marcados como presente)
                dados_presenca = [
                    {"reuniao_id": reuniao_id, "pessoa_id": p_id, "presente": True}
                    for p_id, marcado in presencas_dict.items() if marcado
                ]
                
                if dados_presenca:
                    supabase.table("presencas").insert(dados_presenca).execute()
                
                st.success(f"✅ Reunião registrada! {len(dados_presenca)} presenças confirmadas.")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
