import streamlit as st
from supabase import create_client
from datetime import datetime
import urllib.parse
from fpdf import FPDF
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="Mural de Oração", page_icon="🙌", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- CLASSE PDF SKETCHNOTE PREMIUM ---
class SketchNotePDF(FPDF):
    def sketchy_header(self, titulo, data_f):
        # Título com "rabisco" embaixo
        self.set_font("helvetica", "B", 20)
        self.set_text_color(31, 58, 147)
        self.cell(0, 10, titulo, ln=True, align="C")
        
        # Desenha linha de rabisco manual
        self.set_draw_color(31, 58, 147)
        curr_y = self.get_y()
        self.line(70, curr_y, 140, curr_y)
        self.line(71, curr_y + 0.5, 139, curr_y + 0.5)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Notas de Intercessão - Página {self.page_no()}", 0, 0, "C")

def gerar_pdf_sketchnote(data_f, grupos_do_dia):
    pdf = SketchNotePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # Tenta usar fonte manuscrita se existir, senão usa Helvetica
    font_path = "Caveat-Regular.ttf"
    font_main = "helvetica"
    if os.path.exists(font_path):
        pdf.add_font("Sketch", "", font_path)
        font_main = "Sketch"

    pdf.sketchy_header("Mural de Intercessão", data_f)

    for nome_gf, lista_pedidos in grupos_do_dia.items():
        # Banner do Grupo Estilo "Post-it"
        pdf.set_fill_color(255, 255, 200) # Amarelo Post-it claro
        pdf.set_font(font_main, "B" if font_main == "helvetica" else "", 14)
        pdf.cell(0, 10, f"  GF: {nome_gf}", ln=True, fill=True)
        pdf.ln(4)
        
        for item in lista_pedidos:
            nome = item['pessoas']['nome_completo'].split()[0].upper()
            pedido = item['pedido']
            
            # Efeito Marca-Texto no Nome
            pdf.set_font(font_main, "B" if font_main == "helvetica" else "", 11)
            pdf.set_fill_color(200, 255, 200) # Verde marca-texto
            pdf.cell(pdf.get_string_width(f" {nome} ") + 4, 7, f" {nome} ", fill=True)
            pdf.ln(7)
            
            # Texto do Pedido
            pdf.set_font(font_main, "", 12)
            texto_safe = pedido.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, f"  \"{texto_safe}\"")
            
            # Divisória de rabisco
            pdf.set_draw_color(200, 200, 200)
            y_div = pdf.get_y() + 2
            pdf.line(15, y_div, 100, y_div)
            pdf.ln(6)
            
    return bytes(pdf.output())

# --- 2. SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Faça login para acessar o mural.")
    st.stop()

st.title("💌 Mural de Orações")

# --- 3. BUSCA E EXIBIÇÃO ---
try:
    # Busca completa ordenada por data
    query = supabase.table("pedidos_oracao").select(
        "id, data_pedido, pedido, pessoas(nome_completo, telefone), grupos_familiares(nome)"
    ).order("data_pedido", desc=True).execute()

    if not query.data:
        st.info("Nenhum pedido encontrado.")
    else:
        # Agrupamento Data -> Grupo
        pedidos_hierarquia = {}
        for p in query.data:
            dt = p['data_pedido']
            gp = p['grupos_familiares']['nome']
            if dt not in pedidos_hierarquia: pedidos_hierarquia[dt] = {}
            if gp not in pedidos_hierarquia[dt]: pedidos_hierarquia[dt][gp] = []
            pedidos_hierarquia[dt][gp].append(p)

        # Renderização
        for data_iso, grupos in pedidos_hierarquia.items():
            data_f = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
            
            with st.container(border=True):
                c_tit, c_exp = st.columns([3, 1])
                with c_tit:
                    st.subheader(f"📅 Encontros de {data_f}")
                with c_exp:
                    # Gera o PDF estilo SketchNote
                    pdf_bytes = gerar_pdf_sketchnote(data_f, grupos)
                    st.download_button(
                        label="🤲 Exportar Orações",
                        data=pdf_bytes,
                        file_name=f"SketchNote_{data_iso}.pdf",
                        mime="application/pdf",
                        key=f"sk_{data_iso}",
                        use_container_width=True
                    )
                
                for nome_gf, lista_pedidos in grupos.items():
                    with st.expander(f"🏠 {nome_gf} ({len(lista_pedidos)} pedidos)"):
                        for item in lista_pedidos:
                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"**{item['pessoas']['nome_completo']}**")
                                st.write(f"💬 {item['pedido']}")
                            with col2:
                                tel = item['pessoas'].get('telefone', '')
                                if tel:
                                    tel_l = "".join(filter(str.isdigit, tel))
                                    if not tel_l.startswith('55'): tel_l = '55' + tel_l
                                    link = f"https://wa.me/{tel_l}?text={urllib.parse.quote('Olá! Vi seu pedido de oração e estou intercedendo por você. 🙏')}"
                                    st.link_button("🟢 WhatsApp", link, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar o mural: {e}")
