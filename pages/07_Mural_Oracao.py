import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("🙏 Mural de Intercessão")

# 2. FILTROS NA SIDEBAR[cite: 5]
with st.sidebar:
    st.subheader("Filtros")
    data_inicio = st.date_input("Início", value=datetime.now())
    # Busca GFs ativos para o filtro
    res_g = supabase.table("grupos_familiares").select("id, nome").eq("ativo", True).execute()
    g_opcoes = {g['nome']: g['id'] for g in res_g.data} if res_g.data else {}
    gf_sel = st.selectbox("Filtrar por GF", ["Todos"] + list(g_opcoes.keys()))

# 3. BUSCA DE DADOS COM JOIN
query = supabase.table("pedidos_oracao").select(
    "data_pedido, pedido, pessoas(nome_completo), grupos_familiares(nome)"
).gte("data_pedido", str(data_inicio)).order("data_pedido", desc=True)

if gf_sel != "Todos":
    query = query.eq("grupo_id", g_opcoes[gf_sel])

res = query.execute()

# 4. EXIBIÇÃO EM FORMATO DE CARDS
if res.data:
    for item in res.data:
        with st.container():
            st.markdown(f"""
            <div style="border-left: 5px solid #764ba2; padding: 15px; background: #f9f9f9; border-radius: 5px; margin-bottom: 10px;">
                <small style="color: #666;">{datetime.strptime(item['data_pedido'], '%Y-%m-%d').strftime('%d/%m/%Y')} - {item['grupos_familiares']['nome']}</small><br>
                <strong>{item['pessoas']['nome_completo']}</strong><br>
                <p style="margin-top: 10px; font-style: italic;">"{item['pedido']}"</p>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("Nenhum pedido registrado para este período.")
