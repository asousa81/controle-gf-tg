import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime

# 1. Configuração da Página
st.set_page_config(page_title="Lançar Presença", page_icon="📝", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- 2. SEGURANÇA: BLOQUEIO DE ACESSO DIRETO ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login na página inicial.")
    st.stop()

# --- 3. FILTRO DE DADOS POR PERFIL ---
usuario_id = st.session_state.get('usuario_id')
perfil = st.session_state.get('perfil')

if perfil == 'ADMIN':
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data
else:
    res_g = supabase.table("membros_grupo").select(
        "grupo_id, grupos_familiares(id, numero, nome)"
    ).eq("pessoa_id", usuario_id).filter("funcao", "in", '("LÍDER", "CO-LÍDER")').execute()
    g_opcoes = [item['grupos_familiares'] for item in res_g.data] if res_g.data else []

st.title("📝 Chamada do Grupo Familiar")

if not g_opcoes:
    st.warning("🔍 Nenhum grupo vinculado ao seu perfil.")
    if st.button("🏠 Voltar"):
        st.switch_page("pages/00_Boas_Vindas.py") # Ajustado para sua nova Home
    st.stop()

# --- PASSO 1: SELEÇÃO ---
with st.container():
    col_g, col_d = st.columns(2)
    with col_g:
        grupo_sel = st.selectbox(
            "Selecione o GF", 
            g_opcoes, 
            format_func=lambda x: f"GF {x['numero']} - {x['nome']}"
        )
    with col_d:
        data_reuniao = st.date_input("Data da Reunião", value=date.today())

    st.write("### ⏰ Horários do Encontro")
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        h_inicio = st.time_input("Horário de Início", value=datetime.strptime("20:00", "%H:%M").time())
    with col_h2:
        h_fim = st.time_input("Horário de Término", value=datetime.strptime("21:30", "%H:%M").time())

st.divider()

# --- PASSO 2: LISTA DE CHAMADA E VISITANTES ---
if grupo_sel:
    # Inicialização de variáveis para evitar NameError
    presencas_marcadas = {}
    obs = ""
    
    # Busca membros
    res_m = supabase.table("membros_grupo").select(
        "pessoa_id, funcao, pessoas(nome_completo)"
    ).eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()

    if res_m.data:
        membros = [{"id": m["pessoa_id"], "nome": m["pessoas"]["nome_completo"], "funcao": m["funcao"]} for m in res_m.data]
        ordem_funcao = {"LÍDER": 0, "CO-LÍDER": 1, "ANFITRIÃO": 2, "MEMBRO": 3, "VISITANTE": 4}
        membros_ordenados = sorted(membros, key=lambda x: ordem_funcao.get(x["funcao"], 99))

        st.subheader(f"👥 Membros de {grupo_sel['nome']}")
        for m in membros_ordenados:
            col_nome, col_presenca = st.columns([3, 1])
            with col_nome:
                prefixo = "⭐ " if "LÍDER" in m["funcao"] else "🏠 " if "ANFITRIÃO" in m["funcao"] else "👤 "
                st.write(f"{prefixo} **{m['nome']}** ({m['funcao']})")
            with col_presenca:
                presencas_marcadas[m["id"]] = st.checkbox("Presente", key=f"p_{m['id']}")

        st.divider()
        obs = st.text_area("Anotações da Reunião", placeholder="Pedidos de oração ou observações...")

    # --- SEÇÃO DE VISITANTES ---
    st.subheader("➕ Adicionar Visitantes")
    if "lista_visitantes" not in st.session_state:
        st.session_state.lista_visitantes = []

    with st.expander("Clique para cadastrar um visitante", expanded=False):
        v_col1, v_col2, v_col3 = st.columns([2, 2, 1.5])
        with v_col1: v_nome = st.text_input("Nome do Visitante", key="v_nome_in")
        with v_col2: v_convidado_por = st.text_input("Quem Convidou?", key="v_convite_in")
        with v_col3: v_tel = st.text_input("Telefone (WhatsApp)", key="v_tel_in")
        
        if st.button("➕ Adicionar à Lista"):
            if v_nome:
                st.session_state.lista_visitantes.append({
                    "nome_visitante": v_nome, "quem_convidou": v_convidado_por,
                    "telefone_visitante": v_tel, "data_reuniao": str(data_reuniao), "grupo_id": grupo_sel["id"]
                })
                st.rerun()
            else: st.error("O nome é obrigatório.")

    if st.session_state.lista_visitantes:
        st.write("#### Visitantes prontos para salvar:")
        st.table(pd.DataFrame(st.session_state.lista_visitantes)[['nome_visitante', 'quem_convidou', 'telefone_visitante']])
        if st.button("🗑️ Limpar Lista"):
            st.session_state.lista_visitantes = []
            st.rerun()

    st.divider()

    # --- PASSO 3: SALVAR E SAIR ---
    col_btn_save, col_btn_exit = st.columns(2)

    with col_btn_save:
        if st.button("🚀 Salvar Chamada Completa", type="primary", use_container_width=True):
            try:
                # 1. Processa Membros
                lista_membros = []
                for p_id, presente in presencas_marcadas.items():
                    if presente:
                        lista_membros.append({
                            "data_reuniao": str(data_reuniao), "pessoa_id": p_id, "grupo_id": grupo_sel["id"],
                            "observacao": obs, "horario_inicio": h_inicio.strftime("%H:%M:%S"),
                            "horario_termino": h_fim.strftime("%H:%M:%S")
                        })
                
                if lista_membros:
                    supabase.table("presencas").insert(lista_membros).execute()
                
                # 2. Processa Visitantes
                if st.session_state.lista_visitantes:
                    supabase.table("visitantes_encontro").insert(st.session_state.lista_visitantes).execute()
                    st.session_state.lista_visitantes = [] # Limpa após salvar
                
                st.success("✅ Tudo salvo com sucesso!")
                st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    with col_btn_exit:
        # Trocamos o rerun pela navegação direta para a sua tela de Início
        if st.button("🏠 Sair", use_container_width=True):
            st.switch_page("pages/00_Boas_Vindas.py")[cite: 1]

