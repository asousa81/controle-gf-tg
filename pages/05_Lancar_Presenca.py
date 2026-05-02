import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Lançar Presença", page_icon="📝", layout="wide")

# 2. CONEXÃO COM SUPABASE
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- 3. SEGURANÇA: BLOQUEIO DE ACESSO DIRETO ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login na página inicial.")
    st.stop()

# --- 4. FILTRO DE DADOS POR PERFIL ---
usuario_id = st.session_state.get('usuario_id')
perfil = st.session_state.get('perfil')

if perfil == 'ADMIN':
    # Arthur e Simone veem todos os grupos
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data
else:
    # Líderes veem apenas seus grupos vinculados
    res_g = supabase.table("membros_grupo").select(
        "grupo_id, grupos_familiares(id, numero, nome)"
    ).eq("pessoa_id", usuario_id).filter("funcao", "in", '("LÍDER", "CO-LÍDER")').execute()
    g_opcoes = [item['grupos_familiares'] for item in res_g.data] if res_g.data else []

st.title("📝 Chamada do Grupo Familiar")

if not g_opcoes:
    st.warning("🔍 Nenhum grupo vinculado ao seu perfil.")
    if st.button("🏠 Voltar"):
        st.switch_page("pages/00_Boas_Vindas.py")
    st.stop()

# --- PASSO 1: SELEÇÃO DO GRUPO E CONTEXTO ---
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
    presencas_marcadas = {}
    pedidos_oracao = {}
    obs = ""
    
    # Busca membros ativos do grupo
    res_m = supabase.table("membros_grupo").select(
        "pessoa_id, funcao, pessoas(nome_completo)"
    ).eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()

    if res_m.data:
        membros = [{"id": m["pessoa_id"], "nome": m["pessoas"]["nome_completo"], "funcao": m["funcao"]} for m in res_m.data]
        ordem_funcao = {"LÍDER": 0, "CO-LÍDER": 1, "ANFITRIÃO": 2, "MEMBRO": 3}
        membros_ordenados = sorted(membros, key=lambda x: ordem_funcao.get(x["funcao"], 99))

        # --- INICIALIZAÇÃO DOS DICIONÁRIOS (Linha 79) ---
        pedidos_oracao = {} 

        st.subheader(f"👥 Membros de {grupo_sel['nome']}")
        for m in membros_ordenados: # Linha 81 no seu print
            col_nome, col_presenca = st.columns([3, 1])
            with col_nome:
                prefixo = "⭐ " if "LÍDER" in m["funcao"] else "🏠 " if "ANFITRIÃO" in m["funcao"] else "👤 "
                st.write(f"{prefixo} **{m['nome']}** ({m['funcao']})")
            with col_presenca:
                # Captura a presença
                presencas_marcadas[m["id"]] = st.checkbox("Presente", key=f"p_{m['id']}")
            
            # NOVO: Se o check for marcado, abre o campo de oração logo abaixo
            if presencas_marcadas[m["id"]]:
                pedidos_oracao[m["id"]] = st.text_input(
                    f"Pedido de Oração: {m['nome']}", 
                    key=f"ora_{m['id']}", 
                    placeholder="Escreva o pedido aqui..."
                )

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
            else: st.error("O nome do visitante é obrigatório.")

    if st.session_state.lista_visitantes:
        st.write("#### Visitantes prontos para salvar:")
        st.table(pd.DataFrame(st.session_state.lista_visitantes)[['nome_visitante', 'quem_convidou', 'telefone_visitante']])
        if st.button("🗑️ Limpar Lista de Visitantes"):
            st.session_state.lista_visitantes = []
            st.rerun()

    st.divider()

    # --- PASSO 3: SALVAR E SAIR ---
    col_btn_save, col_btn_exit = st.columns(2)

    with col_btn_save:
        if st.button("🚀 Salvar Chamada Completa", type="primary", use_container_width=True):
            try:
                # A) VALIDAÇÃO DE EXISTÊNCIA (IMPEDE DUPLICIDADE NA FONTE)
                check_p = supabase.table("presencas").select("id", count='exact').eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()
                check_v = supabase.table("visitantes_encontro").select("id", count='exact').eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()

                if (check_p.count and check_p.count > 0) or (check_v.count and check_v.count > 0):
                    st.error(f"⚠️ Já existe um lançamento para o dia {data_reuniao.strftime('%d/%m/%Y')}.")
                    st.info("Para realizar alterações, utilize a aba **'Editar Presença'**.")
                else:
                    # B) PROCESSA MEMBROS
                    lista_membros = []
                    lista_pedidos = []
                    for p_id, presente in presencas_marcadas.items():
            if presente:
                # 1. Adiciona os dados de presença
                lista_membros.append({
                    "data_reuniao": str(data_reuniao), 
                    "pessoa_id": p_id, 
                    "grupo_id": grupo_sel["id"],
                    "observacao": obs, 
                    "horario_inicio": h_inicio.strftime("%H:%M:%S"),
                    "horario_termino": h_fim.strftime("%H:%M:%S")
                })
                
                # 2. Adiciona o pedido de oração (dentro do if presente)
                txt_pedido = pedidos_oracao.get(p_id, "").strip()
                if txt_pedido:
                    lista_pedidos.append({
                        "data_pedido": str(data_reuniao),
                        "pessoa_id": p_id,
                        "grupo_id": grupo_sel["id"],
                        "pedido": txt_pedido
                    })
                
                    # C) GRAVA NO BANCO
                    if lista_membros:
                        supabase.table("presencas").insert(lista_membros).execute()
                    
                    if st.session_state.lista_visitantes:
                        supabase.table("visitantes_encontro").insert(st.session_state.lista_visitantes).execute()
                        st.session_state.lista_visitantes = [] 

                    if lista_pedidos:
                        supabase.table("pedidos_oracao").insert(lista_pedidos).execute()
                    
                    st.success("✅ Chamada registrada com sucesso!")
                    st.balloons()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

    with col_btn_exit:
        # NAVEGAÇÃO EXPLÍCITA PARA A HOME
        if st.button("🏠 Sair", use_container_width=True):
            st.switch_page("pages/00_Boas_Vindas.py")

else:
    st.warning("Este grupo não possui membros vinculados.")
    if st.button("🏠 Voltar"):
        st.switch_page("pages/00_Boas_Vindas.py")
