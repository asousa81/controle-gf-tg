import streamlit as st
import pandas as pd
from datetime import date, time
from supabase import create_client

# --- CONFIGURAÇÃO DA PÁGINA (PÚBLICA) ---
st.set_page_config(page_title="Lançar Presença", page_icon="📝", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("📝 Lançamento de Presença")
st.info("Líder, preencha os dados da reunião do seu GF abaixo.")

# 1. SELEÇÃO DO GRUPO E DATA
try:
    # Busca apenas grupos ativos
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).execute()
    
    if not res_g.data:
        st.warning("Nenhum grupo encontrado no sistema.")
        st.stop()

    col_gf, col_dt = st.columns(2)
    with col_gf:
        grupo_sel = st.selectbox("Selecione o seu GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")
    with col_dt:
        data_reuniao = st.date_input("Data da Reunião", date.today())

    # --- CAMPOS DE HORÁRIO E OBS ---
    col_ini, col_fim = st.columns(2)
    with col_ini:
        h_inicio = st.time_input("Horário de Início", time(19, 30))
    with col_fim:
        h_fim = st.time_input("Horário de Término", time(21, 0))

    obs = st.text_area("Observações / Pedidos de Oração", placeholder="Escreva aqui como foi a reunião...")

    # 2. LISTA DE CHAMADA
    if grupo_sel:
        st.divider()
        st.subheader(f"Lista de Chamada")
        
        # Busca membros vinculados ao grupo
        res_m = supabase.table("membros_grupo").select("pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()
        
        if not res_m.data:
            st.warning("⚠️ Não encontramos membros vinculados a este grupo. Fale com o Coordenador.")
        else:
            # Filtro para evitar nomes duplicados
            membros_unicos = {m["pessoa_id"]: m["pessoas"]["nome_completo"] for m in res_m.data if m["pessoas"]}
            
            presencas_dict = {}
            cols = st.columns(3)
            for i, (p_id, nome) in enumerate(membros_unicos.items()):
                with cols[i % 3]:
                    presencas_dict[p_id] = st.checkbox(nome, key=f"p_{p_id}")

            st.divider()
            
            # 3. BOTÃO DE SALVAR (Aberto para todos)
            if st.button("🚀 Salvar Relatório de Reunião", type="primary"):
                # Registra a reunião
                reuniao_res = supabase.table("reunioes").insert({
                    "grupo_id": grupo_sel["id"],
                    "data_reuniao": str(data_reuniao),
                    "hora_inicio": str(h_inicio),
                    "hora_fim": str(h_fim),
                    "observacoes": obs
                }).execute()
                
                reuniao_id = reuniao_res.data[0]["id"]
                
                # Registra as presenças confirmadas
                dados_presenca = [
                    {"reuniao_id": reuniao_id, "pessoa_id": p_id, "presente": True}
                    for p_id, marcado in presencas_dict.items() if marcado
                ]
                
                if dados_presenca:
                    supabase.table("presencas").insert(dados_presenca).execute()
                
                st.success("✨ Relatório enviado com sucesso! Deus abençoe seu GF.")
                st.balloons()

except Exception as e:
    st.error("Ocorreu um erro ao carregar o formulário.")
    st.info("Verifique se o banco de dados está online.")
