import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# 1. CONFIGURAÇÃO E CONEXÃO
st.set_page_config(page_title="Mural de Intercessão", page_icon="🙏", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Faça login para acessar o mural.")
    st.stop()

st.title("🙏 Mural de Intercessão")
st.caption("Acompanhe e encoraje os membros do seu Grupo Familiar.")

# --- 2. FILTROS LATERAIS ---
with st.sidebar:
    st.header("🔍 Filtros")
    # Filtro de data (últimos 15 dias por padrão)
    data_ini = st.date_input("A partir de:", value=datetime.now() - timedelta(days=15))
    
    # Busca grupos para o filtro
    res_g = supabase.table("grupos_familiares").select("id, nome").eq("ativo", True).execute()
    dict_grupos = {g['nome']: g['id'] for g in res_g.data} if res_g.data else {}
    gf_escolhido = st.selectbox("Filtrar por Grupo", ["Todos"] + list(dict_grupos.keys()))

# --- 3. BUSCA DE DADOS ---
# Note que buscamos o telefone da tabela pessoas para o WhatsApp
query = supabase.table("pedidos_oracao").select(
    "id, data_pedido, pedido, pessoas(nome_completo, telefone), grupos_familiares(nome)"
).gte("data_pedido", str(data_ini)).order("data_pedido", desc=True)

if gf_escolhido != "Todos":
    query = query.eq("grupo_id", dict_grupos[gf_escolhido])

res = query.execute()

# --- 4. EXIBIÇÃO EM CARDS ---
if not res.data:
    st.info("Nenhum pedido de oração encontrado para este período.")
else:
    for item in res.data:
        nome = item['pessoas']['nome_completo']
        telefone = item['pessoas'].get('telefone', '') # Garante que o campo existe
        pedido = item['pedido']
        data_f = datetime.strptime(item['data_pedido'], "%Y-%m-%d").strftime("%d/%m/%Y")
        gf_nome = item['grupos_familiares']['nome']

        with st.container(border=True):
            col_txt, col_btn = st.columns([4, 1])
            
            with col_txt:
                st.markdown(f"**{nome}** · <small>{gf_nome} ({data_f})</small>", unsafe_allow_html=True)
                st.write(f"💬 *{pedido}*")
            
            with col_btn:
                if telefone:
                    # Formata a mensagem para o WhatsApp
                    msg = f"Olá {nome.split()[0]}, estou passando para dizer que recebi seu pedido de oração sobre '{pedido}' e estamos intercedendo por você! 🙏"
                    msg_url = urllib.parse.quote(msg)
                    link_wa = f"https://wa.me/55{telefone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')}?text={msg_url}"
                    
                    st.link_button("🟢 Encorajar", link_wa, use_container_width=True)
                else:
                    st.caption("Sem telefone")

st.divider()
