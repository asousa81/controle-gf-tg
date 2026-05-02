import streamlit as st
from supabase import create_client
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
st.caption("Pedidos agrupados por Grupo Familiar para facilitar a intercessão.")

# --- 2. FILTROS LATERAIS ---
with st.sidebar:
    st.header("🔍 Filtros")
    # Filtro de data (últimos 15 dias)
    data_ini = st.date_input("Pedidos desde:", value=datetime.now() - timedelta(days=15))
    st.divider()
    st.info("O agrupamento é feito automaticamente pelo nome do grupo.")

# --- 3. BUSCA DE DADOS ---
query = supabase.table("pedidos_oracao").select(
    "id, data_pedido, pedido, pessoas(nome_completo, telefone), grupos_familiares(nome)"
).gte("data_pedido", str(data_ini)).order("data_pedido", desc=True).execute()

# --- 4. LÓGICA DE AGRUPAMENTO (Python) ---
pedidos_agrupados = {}

if query.data:
    for p in query.data:
        nome_gp = p['grupos_familiares']['nome'] # Nome do GF
        if nome_gp not in pedidos_agrupados:
            pedidos_agrupados[nome_gp] = []
        pedidos_agrupados[nome_gp].append(p)

# --- 5. EXIBIÇÃO AGRUPADA ---
if not pedidos_agrupados:
    st.info("Nenhum pedido de oração encontrado para este período.")
else:
    # Itera sobre cada grupo
    for nome_gf, lista_pedidos in pedidos_agrupados.items():
        with st.expander(f"🏠 {nome_gf} ({len(lista_pedidos)} pedidos)", expanded=True):
            for item in lista_pedidos:
                nome = item['pessoas']['nome_completo']
                telefone = item['pessoas'].get('telefone', '')
                pedido = item['pedido']
                data_f = datetime.strptime(item['data_pedido'], "%Y-%m-%d").strftime("%d/%m/%Y")

                # Layout do Card Interno
                with st.container(border=True):
                    col_txt, col_btn = st.columns([4, 1])
                    
                    with col_txt:
                        st.markdown(f"**{nome}** · <small>{data_f}</small>", unsafe_allow_html=True)
                        st.write(f"💬 {pedido}")
                    
                    with col_btn:
                        if telefone:
                            # Link customizado para o WhatsApp
                            msg = f"Olá {nome.split()[0]}, estou passando para dizer que recebi seu pedido de oração sobre '{pedido}' e estamos intercedendo por você! 🙏"
                            msg_url = urllib.parse.quote(msg)
                            link_wa = f"https://wa.me/55{telefone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')}?text={msg_url}"
                            st.link_button("🟢 Encorajar", link_wa, use_container_width=True)
                        else:
                            st.caption("Sem contato")

st.divider()
