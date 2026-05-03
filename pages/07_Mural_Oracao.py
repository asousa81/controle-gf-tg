import streamlit as st
from supabase import create_client
from datetime import datetime
import urllib.parse
from fpdf import FPDF
import os

# CONFIGURAÇÃO
st.set_page_config(page_title="Mural de Oração", page_icon="🙌", layout="wide")

# Conexão Supabase
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- CLASSE PDF SKETCHNOTE (Ajustada para o erro de binário) ---
class SketchNotePDF(FPDF):
    def sketchy_header(self, data_f):
        self.set_font("helvetica", "B", 20)
        self.set_text_color(31, 58, 147)
        self.cell(0, 10, "Mural de Intercessao", ln=True, align="C")
        self.set_draw_color(31, 58, 147)
        self.line(70, self.get_y(), 140, self.get_y()) # Linha de rabisco
        self.ln(10)

def gerar_pdf_sketchnote(data_f, grupos_do_dia):
    pdf = SketchNotePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    font_main = "helvetica"
    # Se subir o arquivo Caveat-Regular.ttf para o GitHub, ele ativa aqui
    if os.path.exists("Caveat-Regular.ttf"):
        pdf.add_font("Sketch", "", "Caveat-Regular.ttf")
        font_main = "Sketch"

    pdf.sketchy_header(data_f)

    for nome_gf, lista_pedidos in grupos_do_dia.items():
        pdf.set_fill_color(255, 255, 210) # Cor de Post-it
        pdf.set_font(font_main, "B" if font_main == "helvetica" else "", 14)
        pdf.cell(0, 10, f"  GF: {nome_gf} ({data_f})", ln=True, fill=True)
        pdf.ln(5)
        
        for item in lista_pedidos:
            nome = item['pessoas']['nome_completo'].split()[0].upper()
            pedido = item['pedido']
            
            # Efeito Marca-texto no Nome
            pdf.set_fill_color(210, 255, 210) 
            pdf.set_font(font_main, "B" if font_main == "helvetica" else "", 11)
            pdf.cell(pdf.get_string_width(f" {nome} ") + 4, 7, f" {nome} ", fill=True)
            pdf.ln(8)
            
            # Texto do Pedido
            pdf.set_font(font_main, "", 12)
            texto_pdf = pedido.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, f"  \"{texto_pdf}\"")
            pdf.ln(5)
            
    return bytes(pdf.output()) # Fix para o erro de bytearray

# --- SEGURANÇA ---
if not st.session_state.get("logado"):
    st.warning("⚠️ Sessão expirada. Por favor, volte à página inicial para fazer login.")
    st.stop()

st.title("💌 Mural de Orações")

# --- BUSCA E EXIBIÇÃO ---
try:
    query = supabase.table("pedidos_oracao").select(
        "id, data_pedido, pedido, pessoas(nome_completo, telefone), grupos_familiares(nome)"
    ).order("data_pedido", desc=True).execute()

    if query.data:
        # Agrupamento Data -> Grupo
        hierarquia = {}
        for p in query.data:
            dt, gp = p['data_pedido'], p['grupos_familiares']['nome']
            if dt not in hierarquia: hierarquia[dt] = {}
            if gp not in hierarquia[dt]: hierarquia[dt][gp] = []
            hierarquia[dt][gp].append(p)

        for data_iso, grupos in hierarquia.items():
            data_f = datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                col1.subheader(f"📅 Encontros de {data_f}")
                
                # Exportação Premium SketchNote
                with col2:
                    pdf_data = gerar_pdf_sketchnote(data_f, grupos)
                    st.download_button(
                        "🤲 Exportar Pedidos de Oração", 
                        pdf_data, 
                        f"Mural_{data_iso}.pdf", 
                        "application/pdf", 
                        key=f"sk_{data_iso}"
                    )
                
                for nome_gf, pedidos in grupos.items():
                    with st.expander(f"🏠 {nome_gf}"):
                        for item in pedidos:
                            st.write(f"**{item['pessoas']['nome_completo']}**: {item['pedido']}")
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
