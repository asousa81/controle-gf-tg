import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login na página inicial.")
    st.stop()

st.set_page_config(page_title="Editar Presença", page_icon="✏️", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("✏️ Ajustar Lançamentos")

# --- PASSO 1: SELEÇÃO (O gatilho para a busca) ---
col_g, col_d = st.columns(2)

with col_g:
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data if res_g.data else []
    grupo_sel = st.selectbox("Selecione o GF", g_opcoes, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

with col_d:
    data_reuniao = st.date_input("Data do Lançamento que deseja editar", value=date.today())

st.divider()

# --- PASSO 2: BUSCA AUTOMÁTICA DE DADOS EXISTENTES ---
if grupo_sel:
    # Busca quem já teve presença marcada nesta data
    res_presencas_existentes = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()
    
    # Criamos um "Mapa de Presença" (ID da pessoa -> Registro)
    mapa_p = {p['pessoa_id']: p for p in res_presencas_existentes.data}
    
    # Carregamos os dados da reunião (Horários e Obs) do primeiro registro encontrado
    dados_reuniao = res_presencas_existentes.data[0] if res_presencas_existentes.data else {}
    
    obs_previa = dados_reuniao.get('observacao', "")
    h_i_previa = dados_reuniao.get('horario_inicio', "20:00:00")[:5]
    h_f_previa = dados_reuniao.get('horario_termino', "21:30:00")[:5]

    if not res_presencas_existentes.data:
        st.warning(f"🔍 Não encontramos nenhum lançamento para o dia {data_reuniao.strftime('%d/%m/%Y')}. Você pode iniciar um novo ou trocar a data.")

    # --- PASSO 3: INTERFACE DE EDIÇÃO ---
    st.write("### ⏰ Ajustar Horários e Notas")
    c1, c2 = st.columns(2)
    with c1:
        h_inicio = st.time_input("Início", value=datetime.strptime(h_i_previa, "%H:%M").time())
    with c2:
        h_fim = st.time_input("Término", value=datetime.strptime(h_f_previa, "%H:%M").time())

    st.write("### 👥 Lista de Membros")
    
    # Busca todos os membros ativos para garantir que novos membros também apareçam
    res_m = supabase.table("membros_grupo").select("pessoa_id, funcao, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()
    
    presencas_editadas = {}
    
    if res_m.data:
        # Ordenação clássica: Líderes no topo
        ordem = {"LÍDER": 0, "CO-LÍDER": 1, "ANFITRIÃO": 2, "MEMBRO": 3}
        membros_ordenados = sorted(res_m.data, key=lambda x: ordem.get(x["funcao"], 99))

        for m in membros_ordenados:
            p_id = m["pessoa_id"]
            nome = m['pessoas']['nome_completo']
            
            col_n, col_p = st.columns([3, 1])
            with col_n:
                st.write(f"**{nome}** ({m['funcao']})")
            with col_p:
                # O segredo está aqui: o checkbox nasce marcado se o ID estiver no mapa_p
                presencas_editadas[p_id] = st.checkbox("Presente", value=(p_id in mapa_p), key=f"ed_{p_id}_{data_reuniao}")

        st.divider()
        nova_obs = st.text_area("Observações da Reunião", value=obs_previa)

        # --- PASSO 4: PERSISTÊNCIA (SALVAR) ---
        col_save, col_back = st.columns(2)
        
        with col_save:
            if st.button("💾 Atualizar Lançamento", type="primary", use_container_width=True):
                try:
                    # 1. Limpa o que existia para esta data/grupo (Evita duplicidade)
                    supabase.table("presencas").delete().eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()
                    
                    # 2. Insere a nova versão corrigida
                    lista_nova = []
                    for id_pessoa, marcado in presencas_editadas.items():
                        if marcado:
                            lista_nova.append({
                                "data_reuniao": str(data_reuniao),
                                "pessoa_id": id_pessoa,
                                "grupo_id": grupo_sel["id"],
                                "observacao": nova_obs,
                                "horario_inicio": h_inicio.strftime("%H:%M:%S"),
                                "horario_termino": h_fim.strftime("%H:%M:%S")
                            })
                    
                    if lista_nova:
                        supabase.table("presencas").insert(lista_nova).execute()
                    
                    st.success("✅ Lançamento atualizado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar alterações: {e}")
        
        with col_back:
            if st.button("🏠 Voltar ao Início", use_container_width=True):
                st.switch_page("app.py")
