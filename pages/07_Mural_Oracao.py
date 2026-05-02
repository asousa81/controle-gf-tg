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
st.caption("Histórico de pedidos organizado por data de encontro e grupo familiar.")

# --- 2. FILTROS LATERAIS ---
with st.sidebar:
    st.header("🔍 Filtros")
    data_ini = st.date_input("Ver pedidos desde:", value=datetime.now() - timedelta(days=30))
    st.divider()
    st.info("Os pedidos são agrupados por data (mais recentes primeiro) e depois por GF.")

# --- 3. BUSCA DE DADOS ---
query = supabase.table("pedidos_oracao").select(
    "id, data_pedido, pedido, pessoas(nome_completo, telefone), grupos_familiares(nome)"
).gte("data_pedido", str(data_ini)).order("data_pedido", desc=True).execute()

# --- 4. LÓGICA DE AGRUPAMENTO DUPLO (Data -> Grupo) ---
# Estrutura: { "2026-05-02": { "GF Vida": [...], "GF Esperança": [...] } }
pedidos_hierarquia = {}

if query.data:
    for p in query.data:
        dt = p['data_pedido']
        nome_gp = p['grupos_familiares']['nome']
        
        if dt not in pedidos_hierarquia:
            pedidos_hierarquia[dt] = {}
        
        if nome_gp not in pedidos_hierarquia[dt]:
            pedidos_hierarquia[dt][nome_gp] = []
            
        pedidos_hierarquia[dt][nome_gp].append(p)

# --- 5. EXIBIÇÃO HIERÁRQUICA ---
if not pedidos_hierarquia:
    st.info("Nenhum pedido de oração encontrado para este período.")
else:
    # Itera pelas Datas (Nível 1)
    for data_iso, grupos in pedidos_hierarquia.items():
        data_formatada = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        st.markdown(f"### 📅 Encontros de {data_formatada}")
        
        # Itera pelos Grupos daquela data (Nível 2)
        for nome_gf, lista_pedidos in grupos.items():
            with st.expander(f"🏠 {nome_gf} ({len(lista_pedidos)} pedidos)"):
                for item in lista_pedidos:
                    nome = item['pessoas']['nome_completo']
                    telefone = item['pessoas'].get('telefone', '')
                    pedido = item['pedido']

                    # Layout do Card de Pedido
                    with st.container(border=True):
                        col_txt, col_btn = st.columns([4, 1])
                        
                        with col_txt:
                            st.markdown(f"**{nome}**")
                            st.write(f"💬 {pedido}")
                        
                        with col_btn:
                            if telefone:
                                # Link para WhatsApp com mensagem personalizada
                                msg = f"Olá {nome.split()[0]}, estou intercedendo pelo seu pedido de oração sobre '{pedido}'. Conte comigo! 🙏"
                                msg_url = urllib.parse.quote(msg)
                                # Limpeza básica do telefone para o link
                                tel_limpo = "".join(filter(str.isdigit, telefone))
                                if not tel_limpo.startswith('55'): tel_limpo = '55' + tel_limpo
                                
                                link_wa = f"https://wa.me/{tel_limpo}?text={msg_url}"
                                st.link_button("🟢 Encorajar", link_wa, use_container_width=True)
                            else:
                                st.caption("Sem telefone")
        st.divider()
