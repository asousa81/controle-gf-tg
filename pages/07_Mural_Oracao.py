import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
import urllib.parse
from fpdf import FPDF
import io

# 1. CONFIGURAÇÃO E CONEXÃO
st.set_page_config(page_title="Mural de Intercessão", page_icon="🙏", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- FUNÇÃO PARA GERAR PDF (FILTRADO) ---
def gerar_pdf_oracao(dados_hierarquia, datas_alvo):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Relatório de Pedidos de Oração Selecionados", ln=True, align="C")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
    pdf.ln(10)

    # Ordena as datas para o PDF (mais recentes primeiro)
    datas_ordenadas = sorted(datas_alvo, reverse=True)

    for data_iso in datas_ordenadas:
        if data_iso in dados_hierarquia:
            grupos = dados_hierarquia[data_iso]
            data_f = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
            
            pdf.set_font("helvetica", "B", 14)
            pdf.set_fill_color(240, 240, 240)
            pdf.cell(0, 10, f"Encontros de {data_f}", ln=True, fill=True)
            pdf.ln(4)

            for nome_gf, lista_pedidos in grupos.items():
                pdf.set_font("helvetica", "B", 12)
                pdf.cell(0, 8, f"Grupo: {nome_gf}", ln=True)
                
                pdf.set_font("helvetica", "", 11)
                for item in lista_pedidos:
                    nome = item['pessoas']['nome_completo']
                    pedido = item['pedido']
                    pdf.multi_cell(0, 6, f"* {nome}: {pedido}")
                    pdf.ln(1)
                pdf.ln(5)
            
    return pdf.output()

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Faça login para acessar o mural.")
    st.stop()

st.title("🙏 Mural de Intercessão")

# --- 2. BUSCA DE DADOS ---
with st.sidebar:
    st.header("🔍 Filtros")
    data_base = st.date_input("Buscar pedidos desde:", value=datetime.now() - timedelta(days=60))
    st.divider()

# Busca os dados no banco
query = supabase.table("pedidos_oracao").select(
    "id, data_pedido, pedido, pessoas(nome_completo, telefone), grupos_familiares(nome)"
).gte("data_pedido", str(data_base)).order("data_pedido", desc=True).execute()

# --- 3. LÓGICA DE AGRUPAMENTO ---
pedidos_hierarquia = {}
todas_as_datas = []

if query.data:
    for p in query.data:
        dt = p['data_pedido']
        if dt not in todas_as_datas: todas_as_datas.append(dt)
        
        nome_gp = p['grupos_familiares']['nome']
        if dt not in pedidos_hierarquia: pedidos_hierarquia[dt] = {}
        if nome_gp not in pedidos_hierarquia[dt]: pedidos_hierarquia[dt][nome_gp] = []
        pedidos_hierarquia[dt][nome_gp].append(p)

# --- 4. SELEÇÃO DE DATAS PARA PDF ---
if todas_as_datas:
    with st.sidebar:
        st.write("### 📄 Exportar Relatório")
        # Formata datas para o seletor
        opcoes_datas = {datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y"): d for d in todas_as_datas}
        
        datas_selecionadas_nomes = st.multiselect(
            "Selecione os dias para o PDF:",
            options=list(opcoes_datas.keys()),
            help="Escolha um ou mais dias para gerar o relatório específico."
        )
        
        if datas_selecionadas_nomes:
            # Converte de volta para o formato ISO para o filtro
            datas_para_pdf = [opcoes_datas[n] for n in datas_selecionadas_nomes]
            
            pdf_bytes = gerar_pdf_oracao(pedidos_hierarquia, datas_para_pdf)
            st.download_button(
                label="📥 Baixar PDF dos dias selecionados",
                data=pdf_bytes,
                file_name=f"relatorio_oracao_selecionado.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("Selecione ao menos um dia acima para exportar.")

# --- 5. EXIBIÇÃO NA TELA ---
if not pedidos_hierarquia:
    st.info("Nenhum pedido encontrado no período selecionado.")
else:
    for data_iso, grupos in pedidos_hierarquia.items():
        data_f = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        st.markdown(f"### 📅 Encontros de {data_f}")
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
