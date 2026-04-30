import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime

st.set_page_config(page_title="Editar Presença", page_icon="✏️", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("✏️ Editar Lançamento de Presença")
st.info("Selecione o grupo e a data para carregar os registros existentes.")

# --- PASSO 1: SELEÇÃO ---
col_g, col_d = st.columns(2)

with col_g:
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data if res_g.data else []
    grupo_sel = st.selectbox("Selecione o GF", g_opcoes, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

with col_d:
    data_reuniao = st.date_input("Data da Reunião Original", value=date.today())

st.divider()

# --- PASSO 2: CARREGAR E EDITAR ---
if grupo_sel:
    # 1. Busca todos os membros do grupo
    res_m = supabase.table("membros_grupo").select(
        "pessoa_id, funcao, pessoas(nome_completo)"
    ).eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()

    # 2. Busca as presenças já lançadas naquela data
    res_p = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()
    
    # Criar um set com IDs de quem já estava presente para busca rápida
    ids_presentes_original = {p['pessoa_id'] for p in res_p.data}
    
    # Pegar horários e observações do primeiro registro encontrado (se houver)
    obs_original = res_p.data[0]['observacao'] if res_p.data else ""
    h_inicio_original = res_p.data[0]['horario_inicio'] if res_p.data else "20:00"
    h_fim_original = res_p.data[0]['horario_termino'] if res_p.data else "21:30"

    if res_m.data:
        # Configuração de Horários
        st.write("### ⏰ Ajustar Horários")
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            h_inicio = st.time_input("Início", value=datetime.strptime(h_inicio_original[:5], "%H:%M").time())
        with c_h2:
            h_fim = st.time_input("Término", value=datetime.strptime(h_fim_original[:5], "%H:%M").time())

        st.write("### 👥 Lista de Presença")
        
        presencas_editadas = {}
        
        # Ordenação por função
        ordem = {"LÍDER": 0, "CO-LÍDER": 1, "ANFITRIÃO": 2, "MEMBRO": 3, "VISITANTE": 4}
        membros_ordenados = sorted(res_m.data, key=lambda x: ordem.get(x["funcao"], 99))

        for m in membros_ordenados:
            col_n, col_p = st.columns([3, 1])
            with col_n:
                st.write(f"**{m['pessoas']['nome_completo']}** ({m['funcao']})")
            with col_p:
                # O checkbox já vem marcado se o ID estava no banco
                presencas_editadas[m["pessoa_id"]] = st.checkbox("Presente", value=(m["pessoa_id"] in ids_presentes_original), key=f"edit_{m['pessoa_id']}")

        st.divider()
        nova_obs = st.text_area("Anotações / Pedidos de Oração", value=obs_original)

        # --- PASSO 3: SALVAR ALTERAÇÕES ---
        c_save, c_exit = st.columns(2)
        
        with c_save:
            if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                try:
                    # Estratégia de Atualização:
                    # 1. Deletar todos os registros daquela data/grupo
                    supabase.table("presencas").delete().eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()
                    
                    # 2. Inserir a nova lista de quem está marcado como presente
                    lista_update = []
                    for p_id, esta_presente in presencas_editadas.items():
                        if esta_presente:
                            lista_update.append({
                                "data_reuniao": str(data_reuniao),
                                "pessoa_id": p_id,
                                "grupo_id": grupo_sel["id"],
                                "observacao": nova_obs,
                                "horario_inicio": h_inicio.strftime("%H:%M:%S"),
                                "horario_termino": h_fim.strftime("%H:%M:%S")
                            })
                    
                    if lista_update:
                        supabase.table("presencas").insert(lista_update).execute()
                    
                    st.success("✅ Lançamento atualizado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")

        with c_exit:
            if st.button("🏠 Voltar", use_container_width=True):
                st.switch_page("app.py")
    else:
        st.warning("Nenhum membro encontrado para este grupo.")
