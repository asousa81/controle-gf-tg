import streamlit as st
from supabase import create_client
from datetime import datetime
import urllib.parse
import google.generativeai as genai
from fpdf import FPDF
import os
import json

# CONFIGURAÇÃO
st.set_page_config(page_title="Mural de Oração", page_icon="🙌", layout="wide")

# Conexão Supabase
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- NOVA ARQUITETURA: LEITURA DA BÍBLIA LOCAL ---
@st.cache_data
def carregar_biblia():
    try:
        with open("biblia.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

biblia_dados = carregar_biblia()

# Mapa calibrado exatamente para as siglas do seu arquivo JSON
MAPA_LIVROS = {
    "GÊNESIS": "Gn", "ÊXODO": "Êx", "LEVÍTICO": "Lv", "NÚMEROS": "Nm", "DEUTERONÔMIO": "Dt",
    "JOSUÉ": "Js", "JUÍZES": "Jz", "RUTE": "Rt", "1 SAMUEL": "1Sm", "2 SAMUEL": "2Sm",
    "1 REIS": "1Rs", "2 REIS": "2Rs", "1 CRÔNICAS": "1Cr", "2 CRÔNICAS": "2Cr", "ESDRAS": "Ed",
    "NEEMIAS": "Ne", "ESTER": "Et", "JÓ": "Jó", "SALMOS": "Sl", "PROVÉRBIOS": "Pv",
    "ECLESIASTES": "Ec", "CÂNTICOS": "Ct", "ISAÍAS": "Is", "JEREMIAS": "Jr", "LAMENTAÇÕES": "Lm",
    "EZEQUIEL": "Ez", "DANIEL": "Dn", "OSEIAS": "Os", "JOEL": "Jl", "AMÓS": "Am",
    "OBADIAS": "Ob", "JONAS": "Jn", "MIQUEIAS": "Mq", "NAUM": "Na", "HABACUQUE": "Hc",
    "SOFONIAS": "Sf", "AGEU": "Ag", "ZACARIAS": "Zc", "MALAQUIAS": "Ml", "MATEUS": "Mt",
    "MARCOS": "Mc", "LUCAS": "Lc", "JOÃO": "Jo", "ATOS": "At", "ROMANOS": "Rm",
    "1 CORÍNTIOS": "1Co", "2 CORÍNTIOS": "2Co", "GÁLATAS": "Gl", "EFÉSIOS": "Ef",
    "FILIPENSES": "Fp", "COLOSSENSES": "Cl", "1 TESSALONICENSES": "1Ts", "2 TESSALONICENSES": "2Ts",
    "1 TIMÓTEO": "1Tm", "2 TIMÓTEO": "2Tm", "TITO": "Tt", "FILEMOM": "Fm", "HEBREUS": "Hb",
    "TIAGO": "Tg", "1 PEDRO": "1Pe", "2 PEDRO": "2Pe", "1 JOÃO": "1Jo", "2 JOÃO": "2Jo",
    "3 JOÃO": "3Jo", "JUDAS": "Jd", "APOCALIPSE": "Ap"
}

def buscar_versiculo(ref_ia, cap, ver):
    if not biblia_dados: return None
    sigla_alvo = MAPA_LIVROS.get(ref_ia.strip().upper(), ref_ia.strip())
    for livro in biblia_dados:
        if livro.get("abbrev", "").upper() == sigla_alvo.upper():
            try:
                # Ajuste de índice para listas (Cap 1 = index 0)
                c_idx, v_idx = int(cap) - 1, int(ver) - 1
                return livro["chapters"][c_idx][v_idx]
            except: return None
    return None

# --- CONFIGURAÇÃO DA IA (GEMINI) ---
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model_flash = genai.GenerativeModel('gemini-2.5-flash')

def gerar_texto_whatsapp(nome, pedido):
    # SEU PROMPT MANTIDO, com ajuste apenas para extrair as coordenadas da bíblia local
    prompt = f"""
    Atue como um líder de grupo cristão acolhedor e empático.
    Escreva uma resposta direta de WhatsApp em português para {nome}, que pediu oração por: "{pedido}".
    
    A mensagem deve conter duas partes:
    1. Uma frase acolhedora e empática, priorizando empatia PRINCIPALMENTE se o pedido envolver sofrimento. (máximo 300 caracteres).
    2. Um versículo bíblico real e curto, TOTALMENTE conectado ao contexto do pedido.
    3. SEMPRE, gerar um mensagem nova toda vez que for acionado.
    
    REGRAS DE FORMATAÇÃO (OBRIGATÓRIO):
    - NÃO use nenhum tipo de rótulo, título ou colchetes.
    - Escreva de forma natural, como uma pessoa real conversando.
    - Pule uma linha entre a frase de acolhimento e o versículo.
    - Ao final de tudo, em uma nova linha, escreva APENAS as coordenadas assim: REF:[Sigla];CAP:[Número];VER:[Número]
    """
    try:
        config_seguranca = {
            'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
            'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE'
        }
        response = model_flash.generate_content(prompt, safety_settings=config_seguranca)
        texto_bruto = response.text.strip()
        
        # Lógica para separar a mensagem das coordenadas e buscar na sua Bíblia JSON
        if "REF:" in texto_bruto:
            partes = texto_bruto.split("REF:")
            mensagem_base = partes[0].strip()
            coordenadas = partes[1].split(";")
            sigla = coordenadas[0].replace("REF:", "").strip()
            cap = coordenadas[1].replace("CAP:", "").strip()
            ver = coordenadas[2].replace("VER:", "").strip()
            
            texto_sagrado = buscar_versiculo(sigla, cap, ver)
            if texto_sagrado:
                return f"{mensagem_base}\n\n'{texto_sagrado}' ({sigla} {cap}:{ver})"
        
        return texto_bruto # Fallback caso a IA não use o formato de busca
        
    except Exception as e:
        return f"Olá {nome}, estamos em oração pelo seu pedido. Deus te abençoe!"

# --- CLASSE PDF SKETCHNOTE ---
class SketchNotePDF(FPDF):
    def sketchy_header(self, data_f):
        self.set_font("helvetica", "B", 20)
        self.set_text_color(31, 58, 147)
        self.cell(0, 10, "Mural de Intercessao", ln=True, align="C")
        self.set_draw_color(31, 58, 147)
        self.line(70, self.get_y(), 140, self.get_y())
        self.ln(10)

def gerar_pdf_sketchnote(data_f, grupos_do_dia):
    pdf = SketchNotePDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    font_main = "helvetica"
    if os.path.exists("Caveat-Regular.ttf"):
        pdf.add_font("Sketch", "", "Caveat-Regular.ttf")
        font_main = "Sketch"
    pdf.sketchy_header(data_f)
    for nome_gf, lista_pedidos in grupos_do_dia.items():
        pdf.set_fill_color(255, 255, 210)
        pdf.set_font(font_main, "B" if font_main == "helvetica" else "", 14)
        pdf.cell(0, 10, f"  GF: {nome_gf} ({data_f})", ln=True, fill=True)
        pdf.ln(5)
        for item in lista_pedidos:
            nome = item['pessoas']['nome_completo'].split()[0].upper()
            pdf.set_fill_color(210, 255, 210) 
            pdf.set_font(font_main, "B" if font_main == "helvetica" else "", 11)
            pdf.cell(pdf.get_string_width(f" {nome} ") + 4, 7, f" {nome} ", fill=True)
            pdf.ln(8)
            pdf.set_font(font_main, "", 12)
            texto_pdf = item['pedido'].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, f"  \"{texto_pdf}\"")
            pdf.ln(5)
    return bytes(pdf.output())

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
                with col2:
                    pdf_data = gerar_pdf_sketchnote(data_f, grupos)
                    st.download_button("🤲 Exportar Pedidos", pdf_data, f"Mural_{data_iso}.pdf", "application/pdf", key=f"sk_{data_iso}")
                
                for nome_gf, pedidos in grupos.items():
                    with st.expander(f"🏠 {nome_gf}"):
                        for item in pedidos:
                            st.write(f"**{item['pessoas']['nome_completo']}**: {item['pedido']}")
                            nome_p = item['pessoas']['nome_completo'].split()[0]
                            tel = item['pessoas'].get('telefone')
                            if tel:
                                tel_f = str(tel).strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                                if not tel_f.startswith('55'): tel_f = '55' + tel_f
                                msg = gerar_texto_whatsapp(nome_p, item['pedido'])
                                st.link_button(f"📲 Encorajar {nome_p}", f"https://wa.me/{tel_f}?text={urllib.parse.quote(msg)}")
                            else:
                                st.caption("ℹ️ Sem telefone.")
                            st.divider()
except Exception as e:
    st.error(f"Erro: {e}")
