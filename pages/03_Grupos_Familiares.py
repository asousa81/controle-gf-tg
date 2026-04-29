import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import time

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.title("🔒 Acesso Restrito")
    st.warning("Por favor, faça login na página inicial para gerenciar os grupos.")
    if st.button("Ir para o Login"):
        st.switch_page("app.py")
    st.stop()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Grupos", page_icon="🏠", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("🏠 Gestão de Grupos Familiares (GFs)")

tab_cad, tab_edit = st.tabs(["➕ Novo Grupo", "📝 Editar / Inativar"])

# --- ABA 1: NOVO GRUPO ---
with tab_cad:
    with st.form("form_novo_gf", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            numero = st.number_input("Número do GF*", min_value=1, step=1)
            nome_gf = st.text_input("Nome do Grupo*", placeholder="Ex: GF Boqueirão")
            publico = st.selectbox("Público Alvo", ["Misto", "Homens", "Mulheres", "Jovens", "Casais"])

        with col2:
            dia = st.selectbox("Dia da Semana", ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"])
            hora = st.time_input("Horário da Reunião", value=time(20, 0))
            # Campo extra para o BI: Capacidade ou observação
            obs = st.text_input("Observação (Opcional)")

        if st.form_submit_button("🚀 Criar Novo Grupo", type="primary"):
            if nome_gf:
                try:
                    supabase.table("grupos_familiares").insert({
                        "numero": numero,
                        "nome": nome_gf,
                        "publico_alvo": publico,
                        "dia_semana": dia,
                        "horario": str(hora),
                        "ativo": True
                    }).execute()
                    st.success(f"✅ {nome_gf} (GF {numero}) criado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("O nome do grupo é obrigatório.")

# --- ABA 2: EDITAR / INATIVAR ---
with tab_edit:
    st.subheader("Gerenciar Grupos Existentes")
    
    # Busca grupos ordenados por número
    res_g = supabase.table("grupos_familiares").select("*").order("numero").execute()
    
    if res_g.data:
        g_sel = st.selectbox(
            "Selecione o GF para alterar", 
            res_g.data, 
            format_func=lambda x: f"GF {x['numero']} - {x['nome']} ({'Ativo' if x['ativo'] else 'Inativo'})"
        )
        
        if g_sel:
            with st.form("form_edicao_gf"):
                c1, c2 = st.columns(2)
                
                with c1:
                    e_num = st.number_input("Número", value=g_sel['numero'])
                    e_nom = st.text_input("Nome do Grupo", value=g_sel['nome'])
                    
                    lista_pub = ["Misto", "Homens", "Mulheres", "Jovens", "Casais"]
                    pub_banco = g_sel.get('publico_alvo', 'Misto')
                    idx_pub = lista_pub.index(pub_banco) if pub_banco in lista_pub else 0
                    e_pub = st.selectbox("Público Alvo", lista_pub, index=idx_pub)

                with c2:
                    lista_dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
                    dia_banco = g_sel.get('dia_semana', 'Segunda')
                    idx_dia = lista_dias.index(dia_banco) if dia_banco in lista_dias else 0
                    e_dia = st.selectbox("Dia da Semana", lista_dias, index=idx_dia)
                    
                    # Tratamento de horário
                    h_banco = g_sel.get('horario')
                    h_val = time.fromisoformat(h_banco) if h_banco else time(20, 0)
                    e_hor = st.time_input("Horário", value=h_val)
                    
                    st.write("---")
                    e_ativo = st.toggle("Grupo Ativo", value=g_sel.get('ativo', True))

                if st.form_submit_button("💾 Salvar Alterações"):
                    try:
                        supabase.table("grupos_familiares").update({
                            "numero": e_num,
                            "nome": e_nom,
                            "publico_alvo": e_pub,
                            "dia_semana": e_dia,
                            "horario": str(e_hor),
                            "ativo": e_ativo
                        }).eq("id", g_sel["id"]).execute()
                        st.success("Grupo atualizado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na atualização: {e}")
    else:
        st.info("Nenhum grupo cadastrado para edição.")
