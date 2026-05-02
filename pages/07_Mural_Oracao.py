import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import urllib.parse
from fpdf import FPDF

# 1. CONFIGURAÇÃO E CONEXÃO
st.set_page_config(page_title="Mural de Intercessão", page_icon="🙏", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- FUNÇÃO PARA GERAR PDF DE UM DIA ESPECÍFICO ---
def gerar_pdf_dia(data_f, grupos_do_dia):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Cabeçalho do Documento
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, f"Lista de Oração - {data_f}", ln=True, align="C")
    pdf.ln(5)

    for nome_gf, lista_pedidos in grupos_do_dia.items():
        # Nome do Grupo com destaque
        pdf.set_font("helvetica", "B", 13)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 10, f" Grupo: {nome_gf}", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 11)
        for item in lista_pedidos:
            nome = item['pessoas']['nome_completo']
            pedido = item['pedido']
            # Texto do pedido com quebra automática
            pdf.multi_cell(0, 7, f"• {nome}: {pedido}")
            pdf.ln(1)
        pdf.ln(4)
            
    return pdf.output()

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Faça login para acessar o mural.")
    st.stop()

st.title("🙏 Mural de Intercessão")

# --- 2. BUSCA DE DADOS ---
with st.sidebar:
    st.header("🔍 Filtros")
    data_base = st.date_input("Buscar encontros desde:", value=datetime.now() - timedelta(days=30))

# Busca dados do banco
query = supabase.table("pedidos_oracao").select(
    "id, data_pedido, pedido, pessoas(nome_completo, telefone), grupos_familiares(nome)"
).gte("data_pedido", str(data_base)).order("data_pedido", desc=True).execute()

# --- 3. LÓGICA DE AGRUPAMENTO (Data -> Grupo) ---
pedidos_hierarquia = {}
if query.data:
    for p in query.data:
        dt = p['data_pedido']
        nome_gp = p['grupos_familiares']['nome']
        if dt not in pedidos_hierarquia: pedidos_hierarquia[dt] = {}
        if nome_gp not in pedidos_hierarquia[dt]: pedidos_hierarquia[dt][nome_gp] = []
        pedidos_hierarquia[dt][nome_gp].append(p)

# --- 4. EXIBIÇÃO NA TELA ---
if not pedidos_hierarquia:
    st.info("Nenhum pedido encontrado no período selecionado.")
else:
    for data_iso, grupos in pedidos_hierarquia.items():
        data_f = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        
        # LINHA DE TÍTULO DA DATA COM BOTÃO DE EXPORTAR
        col_tit, col_exp = st.columns([4, 1])
        with col_tit:
            st.markdown(f"### 📅 Encontros de {data_f}")
        with col_exp:
            pdf_bytes = gerar_pdf_dia(data_f, grupos)
            st.download_button(
                label="📥 Exportar PDF",
                data=pdf_bytes,
                file_name=f"oracoes_{data_iso}.pdf",
                mime="application/pdf",
                key=f"btn_{data_iso}", # Chave única para evitar erro de widget
                use_container_width=True
            )
        
        # Itera pelos grupos daquela data
        for nome_gf, lista_pedidos in grupos.items():
            with st.expander(f"🏠 {nome_gf} ({len(lista_pedidos)} pedidos)"):
                for item in lista_pedidos:
                    with st.container(border=True):
                        col_txt, col_btn = st.columns([4, 1])
                        with col_txt:
                            st.markdown(f"**{item['pessoas']['nome_completo']}**")
                            st.write(f"💬 {item['pedido']}")
                        with col_btn:
                            tel = item['pessoas'].get('telefone', '')
                            if tel:
                                tel_l = "".join(filter(str.isdigit, tel))
                                if not tel_l.startswith('55'): tel_l = '55' + tel_l
                                link = f"https://wa.me/{tel_l}?text={urllib.parse.quote('Olá, estou intercedendo por você! 🙏')}"
                                st.link_button("🟢 Encorajar", link, use_container_width=True)
        st.divider()
