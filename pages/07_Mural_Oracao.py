import streamlit as st
from supabase import create_client
from datetime import datetime
import urllib.parse
from fpdf import FPDF
import os

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="Mural SketchNote", page_icon="🎨", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- CLASSE PDF SKETCHNOTE ---
class SketchNotePDF(FPDF):
    def sketchy_rect(self, x, y, w, h):
        """Desenha um retângulo com efeito de rabisco (linhas duplas levemente tortas)"""
        self.set_draw_color(100, 100, 100)
        self.rect(x, y, w, h)
        self.rect(x + 0.5, y + 0.3, w - 0.2, h - 0.1) # Linha de 'reforço' desalinhada

    def header(self):
        # Título estilo manchete de caderno
        if os.path.exists("Caveat-Regular.ttf"):
            self.add_font("Sketch", "", "Caveat-Regular.ttf")
            self.set_font("Sketch", "", 28)
        else:
            self.set_font("helvetica", "B", 24)
        
        self.set_text_color(40, 40, 40)
        self.cell(0, 15, "Meus Pedidos de Oracao", ln=True, align="C")
        # Linha de rabisco sob o título
        self.line(60, 22, 150, 22)
        self.line(62, 23, 148, 23)
        self.ln(10)

def gerar_pdf_sketchnote(data_f, grupos_do_dia):
    pdf = SketchNotePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # Define a fonte para o corpo (Tenta carregar a SketchNote, se não, Helvetica)
    font_name = "Sketch" if os.path.exists("Caveat-Regular.ttf") else "helvetica"
    if font_name == "Sketch": pdf.add_font("Sketch", "", "Caveat-Regular.ttf")

    for nome_gf, lista_pedidos in grupos_do_dia.items():
        # Moldura do Grupo (Estilo Post-it)
        curr_y = pdf.get_y()
        pdf.sketchy_rect(10, curr_y, 190, 10)
        
        pdf.set_font(font_name, "B" if font_name == "helvetica" else "", 16)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 10, f"  GF: {nome_gf} - {data_f}", ln=True)
        pdf.ln(5)
        
        for item in lista_pedidos:
            nome = item['pessoas']['nome_completo'].split()[0] # Apenas primeiro nome para intimidade
            pedido = item['pedido']
            
            # Balão de fala ou marcador manual
            pdf.set_font(font_name, "B" if font_name == "helvetica" else "", 12)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(10)
            pdf.cell(0, 6, f"> {nome} disse:", ln=True)
            
            pdf.set_font(font_name, "", 13)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(15)
            
            # Sanitização e multi-cell para o texto
            texto_pdf = pedido.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 7, f"{texto_pdf}")
            pdf.ln(4)
            
        pdf.ln(10)
            
    return bytes(pdf.output())

# --- RESTANTE DA LÓGICA DO STREAMLIT (BUSCA E EXIBIÇÃO) ---
# ... (Mantenha a lógica de busca do Supabase e renderização que já usamos)
