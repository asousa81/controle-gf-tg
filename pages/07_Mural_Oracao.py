import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import urllib.parse
from fpdf import FPDF

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Mural de Intercessão", page_icon="🙏", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- FUNÇÃO PARA GERAR PDF (PROTEGIDA CONTRA ERROS DE ACENTO/EMOJI) ---
def gerar_pdf_dia(data_f, grupos_do_dia):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, f"Lista de Oração - {data_f}", ln=True, align="C")
    pdf.ln(5)

    for nome_gf, lista_pedidos in grupos_do_dia.items():
        # Destaque para o Grupo
        pdf.set_font("helvetica", "B", 13)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(0, 10, f" Grupo: {nome_gf}", ln=True, fill=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 11)
        for item in lista_pedidos:
            nome = item['pessoas']['nome_completo']
            pedido = item['pedido']
            
            # Limpeza de caracteres especiais para evitar erro de encoding
            texto_bruto = f"- {nome}: {pedido}"
            texto_seguro = texto_bruto.encode('latin-1', 'replace').decode('latin-1')
            
            pdf.multi_cell(0, 7, texto_seguro)
            pdf.ln(1)
        pdf.ln(4)
            
    return pdf.output()

# --- 2. SEGURANÇA: BLOQUEIO DE ACESSO ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Faça login para acessar o mural.")
    st.stop()

st.title("🙏 Mural de Intercessão")
st.caption("Acompanhe os pedidos de oração por data e grupo.")

# --- 3. FILTROS NA SIDEBAR ---
with st.sidebar:
    st.header("🔍 Filtros")
    data_limite = st.date_input("Ver encontros desde:", value=datetime.now() - timedelta(days=30))
    st.divider()
    st.info("O botão de exportar gera a lista específica daquela data.")

# --- 4. BUSCA DE DADOS ---
try:
    query = supabase.table("pedidos_oracao").select(
        "id, data_pedido, pedido, pessoas(nome_completo, telefone), grupos_familiares(nome)"
    ).gte("data_pedido", str(data_limite)).order("data_pedido", desc=True).execute()

    # Agrupamento: { "data": { "grupo": [pedidos] } }
    pedidos_hierarquia = {}
    if query.data:
        for p in query.data:
            dt = p['data_pedido']
            nome_gp = p['grupos_familiares']['nome']
            if dt not in pedidos_hierarquia: pedidos_hierarquia[dt] = {}
            if nome_gp not in pedidos_hierarquia[dt]: pedidos_hierarquia[dt][nome_gp] = []
            pedidos_hierarquia[dt][nome_gp].append(p)

    # --- 5. RENDERIZAÇÃO DA INTERFACE ---
    if not pedidos_hierarquia:
        st.info("Nenhum pedido de oração encontrado no período selecionado.")
    else:
        for data_iso, grupos in pedidos_hierarquia.items():
            data_formatada = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
            
            # Cabeçalho da Data + Botão de Exportar[cite: 1]
            col_titulo, col_botao = st.columns([4, 1])
            with col_titulo:
                st.markdown(f"### 📅 Encontros de {data_formatada}")
            
            with col_botao:
                pdf_data = gerar_pdf_dia(data_formatada, grupos)
                st.download_button(
                    label="📥 Exportar PDF",
                    data=pdf_data,
                    file_name=f"oracoes_{data_iso}.pdf",
                    mime="application/pdf",
                    key=f"dl_{data_iso}", # Key única fundamental![cite: 1]
                    use_container_width=True
                )
            
            # Grupos dentro daquela Data
            for nome_gf, lista_pedidos in grupos.items():
                with st.expander(f"🏠 {nome_gf} ({len(lista_pedidos)} pedidos)"):
                    for item in lista_pedidos:
                        with st.container(border=True):
                            c1, c2 = st.columns([4, 1])
                            with c1:
                                st.markdown(f"**{item['pessoas']['nome_completo']}**")
                                st.write(f"💬 {item['pedido']}")
                            with c2:
                                tel = item['pessoas'].get('telefone', '')
                                if tel:
                                    tel_limpo = "".join(filter(str.isdigit, tel))
                                    if not tel_limpo.startswith('55'): tel_limpo = '55' + tel_limpo
                                    texto_wa = urllib.parse.quote(f"Olá, estou orando pelo seu pedido: {item['pedido']}")
                                    st.link_button("🟢 WhatsApp", f"https://wa.me/{tel_limpo}?text={texto_wa}", use_container_width=True)
            st.divider()

except Exception as e:
    st.error(f"Erro ao carregar o mural: {e}")
