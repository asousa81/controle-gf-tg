import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Por favor, faça login para acessar a chamada.")
    st.stop()

st.set_page_config(page_title="Lançar Presença", page_icon="📝", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("📝 Chamada do Grupo Familiar")

# --- PASSO 1: SELEÇÃO DO GRUPO E DATA ---
col_g, col_d = st.columns(2)

with col_g:
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data if res_g.data else []
    grupo_sel = st.selectbox("Selecione o GF", g_opcoes, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

with col_d:
    data_reuniao = st.date_input("Data da Reunião", value=date.today())

st.divider()

# --- PASSO 2: LISTA DE CHAMADA DINÂMICA ---
if grupo_sel:
    # Busca membros vinculados ao grupo selecionado, trazendo a função
    res_m = supabase.table("membros_grupo").select(
        "pessoa_id, funcao, pessoas(nome_completo)"
    ).eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()

    if res_m.data:
        # Organiza os dados para facilitar (Líderes primeiro)
        membros = []
        for m in res_m.data:
            membros.append({
                "id": m["pessoa_id"],
                "nome": m["pessoas"]["nome_completo"],
                "funcao": m["funcao"]
            })
        
        # Ordenação: Líderes, Co-Líderes, Anfitriões e depois Membros
        ordem_funcao = {"LÍDER": 0, "CO-LÍDER": 1, "ANFITRIÃO": 2, "MEMBRO": 3, "VISITANTE": 4}
        membros_ordenados = sorted(membros, key=lambda x: ordem_funcao.get(x["funcao"], 99))

        st.subheader(f"👥 Membros de {grupo_sel['nome']}")
        st.info("Marque quem esteve presente hoje:")

        # Dicionário para armazenar o estado da presença (checkboxes)
        presencas_marcadas = {}
        
        # Interface de lista de chamada
        for m in membros_ordenados:
            col_nome, col_presenca = st.columns([3, 1])
            with col_nome:
                # Destaque visual para funções de liderança
                prefixo = "⭐ " if "LÍDER" in m["funcao"] else "🏠 " if "ANFITRIÃO" in m["funcao"] else "👤 "
                st.write(f"{prefixo} **{m['nome']}** ({m['funcao']})")
            with col_presenca:
                presencas_marcadas[m["id"]] = st.checkbox("Presente", key=f"p_{m['id']}")

        st.divider()
        obs = st.text_area("Anotações da Reunião (Pedidos de oração, observações)", placeholder="Opcional...")

        # --- PASSO 3: SALVAR NO BANCO ---
        if st.button("🚀 Finalizar e Salvar Chamada", type="primary", use_container_width=True):
            try:
                lista_insert = []
                for p_id, presente in presencas_marcadas.items():
                    if presente:
                        lista_insert.append({
                            "data_reuniao": str(data_reuniao),
                            "pessoa_id": p_id,
                            "grupo_id": grupo_sel["id"],
                            "observacao": obs
                        })
                
                if lista_insert:
                    supabase.table("presencas").insert(lista_insert).execute()
                    st.success(f"✅ Presença de {len(lista_insert)} pessoas registrada com sucesso!")
                    st.balloons()
                else:
                    st.warning("Nenhuma presença foi marcada.")
            except Exception as e:
                st.error(f"Erro ao salvar presenças: {e}")
    else:
        st.warning("Este grupo ainda não possui membros vinculados. Vá em 'Vincular Membros' primeiro.")
