import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime

st.set_page_config(page_title="Editar Presenca", page_icon="✏️", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("Acesso restrito. Faca login na pagina inicial.")
    st.stop()

usuario_id = st.session_state.get("usuario_id")
perfil = st.session_state.get("perfil")

if perfil == "ADMIN":
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data
else:
    res_g = supabase.table("membros_grupo").select(
        "grupo_id, grupos_familiares(id, numero, nome)"
    ).eq("pessoa_id", usuario_id).filter("funcao", "in", '("LIDER", "CO-LIDER")').execute()
    g_opcoes = [item["grupos_familiares"] for item in res_g.data] if res_g.data else []

st.title("✏️ Ajustar Lancamentos")

if not g_opcoes:
    st.warning("Nenhum grupo vinculado ao seu perfil.")
    if st.button("🏠 Voltar ao Inicio"):
        st.switch_page("pages/00_Boas_Vindas.py")
    st.stop()

col_g, col_d = st.columns(2)

with col_g:
    grupo_sel = st.selectbox(
        "Selecione o GF",
        g_opcoes,
        format_func=lambda x: "GF " + str(x["numero"]) + " - " + x["nome"]
    )

with col_d:
    data_reuniao = st.date_input("Data do Lancamento que deseja editar", value=date.today())

st.divider()

if grupo_sel:
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()

    if res_presencas.data:
        mapa_p = {p["pessoa_id"]: p for p in res_presencas.data}
        dados_reuniao = res_presencas.data[0]

        res_pedidos = supabase.table("pedidos_oracao").select("*").eq("grupo_id", grupo_sel["id"]).eq("data_pedido", str(data_reuniao)).execute()
        mapa_pedidos = {p["pessoa_id"]: p["pedido"] for p in res_pedidos.data} if res_pedidos.data else {}

        def format_time_safe(val, default):
            if val is None or str(val).lower() == "none":
                return default
            return str(val)[:5]

        obs_previa = dados_reuniao.get("observacao", "")
        h_i_previa = format_time_safe(dados_reuniao.get("horario_inicio"), "20:00")
        h_f_previa = format_time_safe(dados_reuniao.get("horario_termino"), "21:30")

        st.write("### ⏰ Ajustar Horarios e Notas")
        c1, c2 = st.columns(2)
        with c1:
            h_inicio = st.time_input("Inicio", value=datetime.strptime(h_i_previa, "%H:%M").time())
        with c2:
            h_fim = st.time_input("Termino", value=datetime.strptime(h_f_previa, "%H:%M").time())

        st.write("### 👥 Lista de Membros")

        res_m = supabase.table("membros_grupo").select(
            "pessoa_id, funcao, pessoas(nome_completo)"
        ).eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()

        presencas_editadas = {}
        pedidos_editados = {}

        if res_m.data:
            ordem = {"LIDER": 0, "CO-LIDER": 1, "ANFITRIAO": 2, "MEMBRO": 3}
            membros_ordenados = sorted(res_m.data, key=lambda x: ordem.get(x["funcao"], 99))

            for m in membros_ordenados:
                p_id = m["pessoa_id"]
                nome = m["pessoas"]["nome_completo"]
                col_n, col_p = st.columns([3, 1])
                with col_n:
                    st.write("**" + nome + "** (" + m["funcao"] + ")")
                with col_p:
                    presencas_editadas[p_id] = st.checkbox("Presente", value=(p_id in mapa_p), key="ed_" + str(p_id) + "_" + str(data_reuniao))

                if presencas_editadas[p_id]:
                    pedidos_editados[p_id] = st.text_area(
                        "Pedido de Oracao: " + nome,
                        value=mapa_pedidos.get(p_id, ""),
                        key="ora_ed_" + str(p_id) + "_" + str(data_reuniao),
                        placeholder="Escreva ou edite o pedido aqui..."
                    )

            st.divider()
            nova_obs = st.text_area("Observacoes da Reuniao", value=obs_previa)

            col_save, col_back = st.columns(2)

            with col_save:
                if st.button("💾 Atualizar Lancamento", type="primary", use_container_width=True):
                    try:
                        supabase.table("presencas").delete().eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()

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

                        supabase.table("pedidos_oracao").delete().eq("grupo_id", grupo_sel["id"]).eq("data_pedido", str(data_reuniao)).execute()

                        lista_pedidos = []
                        for id_pessoa, txt_pedido in pedidos_editados.items():
                            if txt_pedido and txt_pedido.strip():
                                lista_pedidos.append({
                                    "data_pedido": str(data_reuniao),
                                    "pessoa_id": id_pessoa,
                                    "grupo_id": grupo_sel["id"],
                                    "pedido": txt_pedido.strip()
                                })

                        if lista_pedidos:
                            supabase.table("pedidos_oracao").insert(lista_pedidos).execute()

                        st.success("✅ Lancamento atualizado!")
                        st.balloons()
                    except Exception as e:
                        st.error("Erro ao salvar: " + str(e))

            with col_back:
                if st.button("🏠 Voltar ao Inicio", use_container_width=True):
                    st.switch_page("pages/00_Boas_Vindas.py")

    else:
        st.warning("Nenhum lancamento encontrado para o dia " + data_reuniao.strftime("%d/%m/%Y") + ".")
        if st.button("🏠 Voltar ao Inicio", use_container_width=True):
            st.switch_page("pages/00_Boas_Vindas.py")
