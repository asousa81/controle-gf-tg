import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.title("🔒 Acesso Restrito")
    st.warning("Por favor, faça login na página inicial.")
    if st.button("Ir para o Login"):
        st.switch_page("app.py")
    st.stop()

st.set_page_config(page_title="Relatório Executivo", page_icon="📈", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- FUNÇÃO OFICIAL PARA GERAÇÃO DO PDF ---
def gerar_pdf_oficial(grupo, mes_ano, lideres, colideres, df_membros, obs_texto):
    pdf = FPDF()
    pdf.add_page()
    
    def c(texto): # Tratamento de caracteres Latin-1
        return str(texto).encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, c(f"RELATÓRIO DE ATIVIDADES - {mes_ano}"), ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(240, 242, 246)
    
    pdf.cell(140, 5, c("NOME DO GRUPO FAMILIAR"), border=1, fill=True)
    pdf.cell(50, 5, c("Nº DO GF"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(140, 8, c(f"GF {grupo['numero']} - {grupo['nome']}"), border=1)
    pdf.cell(50, 8, c(f"{grupo['numero']}"), border=1, ln=True)
    
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, c("LÍDER"), border=1, fill=True)
    pdf.cell(95, 5, c("COORDENADOR"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(95, 8, c(", ".join(lideres) if lideres else "N/A"), border=1)
    pdf.cell(95, 8, c("Pr. Arthur e Pra. Simone"), border=1, ln=True)
    
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, c("Frequência de Membros"), ln=True)
    pdf.set_font("Arial", "B", 8)
    
    if not df_membros.empty:
        col_width = 190 / len(df_membros.columns)
        for col in df_membros.columns:
            pdf.cell(col_width, 8, c(col), border=1, align="C", fill=True)
        pdf.ln()
        
        pdf.set_font("Arial", "", 8)
        for _, row in df_membros.iterrows():
            for item in row:
                pdf.cell(col_width, 8, c(item), border=1, align="C")
            pdf.ln()
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, c("Observações"), ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 8, c(obs_texto if obs_texto else "Sem observações registradas."))
    
    return bytes(pdf.output())

# --- CSS PREMIUM ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; }
.paper-container { background-color: white; border-radius: 15px; padding: 35px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); margin-top: 15px; border: 1px solid #eee; }
.header-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 25px; padding-bottom: 20px; border-bottom: 2px solid #f8f9fa; }
.label { font-size: 0.7rem; color: #888; text-transform: uppercase; font-weight: 700; display: block; }
.value { font-size: 1rem; color: #111; font-weight: 600; }
.styled-table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 0.85rem; }
.styled-table thead th { background-color: #fcfcfc; color: #444; padding: 12px; border: 1px solid #eee; text-align: center; font-weight: 700; }
.styled-table td { padding: 10px; border: 1px solid #eee; text-align: center; }
.badge-c { background-color: #d4edda; color: #155724; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
.badge-f { background-color: #f8d7da; color: #721c24; padding: 4px 10px; border-radius: 6px; font-weight: 700; }
.time-sub { font-size: 0.65rem; color: #777; display: block; font-weight: 400; margin-top: 4px; }
.obs-section { background: #fdfdfd; border-radius: 8px; padding: 20px; margin-top: 25px; border-left: 5px solid #764ba2; }
</style>
""", unsafe_allow_html=True)

# --- 1. FILTROS ---
with st.sidebar:
    st.title("📑 BI Manager")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses, index=datetime.now().month - 1)
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

st.title("📈 Analytics e Desempenho")

# --- 2. LÓGICA DE DADOS ---
if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
        colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']

        # Cálculo de Engajamento
        total_m = len([m for m in res_membros.data if m['funcao'] != 'VISITANTE'])
        df_p_calc = pd.DataFrame(res_presencas.data)
        reunioes_m = len(set(df_p_calc['data_reuniao'])) if not df_p_calc.empty else 0
        
        # Engajamento = (Presenças Reais) / (Total de Membros * Total de Reuniões)
        taxa_engajamento = 0
        if total_m > 0 and reunioes_m > 0:
            presencas_reais = len(df_p_calc[df_p_calc['pessoa_id'].isin([m['pessoa_id'] for m in res_membros.data if m['funcao'] != 'VISITANTE'])])
            taxa_engajamento = (presencas_reais / (total_m * reunioes_m)) * 100

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><small>MEMBROS</small><h2>{total_m}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><small>ENCONTROS</small><h2>{reunioes_m}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><small>% ENGAJAMENTO</small><h2>{taxa_engajamento:.1f}%</h2></div>', unsafe_allow_html=True)

        st.markdown(f"""
<div class="paper-container">
<div style="text-align: center; margin-bottom: 30px;">
<h2 style="color: #764ba2; margin: 0; letter-spacing: 1px;">RELATÓRIO DE ATIVIDADES</h2>
<span style="color: #999; font-weight: 600;">{mes_sel.upper()} / {ano_sel}</span>
</div>
<div class="header-grid">
<div>
<div class="info-item"><span class="label">NOME DO GRUPO FAMILIAR</span><span class="value">GF {grupo_sel['numero']} - {grupo_sel['nome']}</span></div>
<div class="info-item"><span class="label">LIDERANÇA</span><span class="value">{", ".join(lideres) if lideres else "N/A"}</span></div>
<div class="info-item"><span class="label">PÚBLICO ALVO</span><span class="value">{grupo_sel.get('publico_alvo', 'Misto')}</span></div>
</div>
<div>
<div class="info-item"><span class="label">COORDENAÇÃO</span><span class="value">Pr. Arthur e Pra. Simone</span></div>
<div class="info-item"><span class="label">LÍDER EM TREINAMENTO</span><span class="value">{", ".join(colideres) if colideres else "0"}</span></div>
<div class="info-item"><span class="label">LOCALIZAÇÃO</span><span class="value">Curitiba, PR</span></div>
</div>
</div>
""", unsafe_allow_html=True)

        if not df_p_calc.empty:
            datas = sorted(df_p_calc['data_reuniao'].unique())
            
            table_html = f"""<table class="styled-table"><thead><tr><th rowspan="2" style="width: 45px;">Nº</th><th rowspan="2" style="text-align: left;">MEMBROS</th><th colspan="{len(datas)}">DATAS E HORÁRIOS</th></tr><tr>"""
            
            def format_time(val, default):
                if val is None or str(val).lower() == 'none': return default
                return str(val)[:5]

            df_reunioes = df_p_calc.groupby('data_reuniao').first().reset_index()
            for d in datas:
                info_r = df_reunioes[df_reunioes['data_reuniao'] == d].iloc[0]
                h_i = format_time(info_r.get('horario_inicio'), '20:00')
                h_f = format_time(info_r.get('horario_termino'), '21:30')
                dt_fmt = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')
                table_html += f"<th>{dt_fmt}<br><span class='time-sub'>{h_i} às {h_f}</span></th>"
            
            table_html += "</tr></thead><tbody>"

            count = 1
            lista_pdf = []
            for m in res_membros.data:
                if m['funcao'] == 'VISITANTE': continue
                nome = m['pessoas']['nome_completo']
                table_html += f"<tr><td>{count:02d}</td><td style='text-align: left; font-weight: 600;'>{nome}</td>"
                row_pdf = {"Nº": f"{count:02d}", "Membro": nome}
                
                for d in datas:
                    presente = not df_p_calc[(df_p_calc['data_reuniao'] == d) & (df_p_calc['pessoa_id'] == m['pessoa_id'])].empty
                    row_pdf[datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')] = "C" if presente else "F"
                    badge = '<span class="badge-c">C</span>' if presente else '<span class="badge-f">F</span>'
                    table_html += f"<td>{badge}</td>"
                
                table_html += "</tr>"
                lista_pdf.append(row_pdf)
                count += 1
            
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

            # Notas
            st.markdown('<div class="obs-section"><span class="label">Notas Pastorais</span>', unsafe_allow_html=True)
            obs_pdf_texto = ""
            for _, r in df_reunioes.iterrows():
                if r['observacao'] and str(r['observacao']) != 'None':
                    dt_f = datetime.strptime(r['data_reuniao'], '%Y-%m-%d').strftime('%d/%m')
                    st.write(f"**• {dt_f}:** {r['observacao']}")
                    obs_pdf_texto += f"[{dt_f}] {r['observacao']}\n"
            st.markdown('</div></div>', unsafe_allow_html=True)

            # --- BOTÃO DE PDF FUNCIONAL ---
            st.divider()
            try:
                pdf_bytes = gerar_pdf_oficial(grupo_sel, f"{mes_sel}/{ano_sel}", lideres, colideres, pd.DataFrame(lista_pdf), obs_pdf_texto)
                st.download_button(label="📥 Gerar PDF para Impressão", data=pdf_bytes, file_name=f"Relatorio_{mes_sel}_GF{grupo_sel['numero']}.pdf", mime="application/pdf", use_container_width=True, type="primary")
            except Exception as e:
                st.error(f"Erro ao preparar impressão: {e}")
        else:
            st.markdown("<p style='text-align:center; padding: 50px; color: #999;'>Sem dados de presença para este período.</p></div>", unsafe_allow_html=True)
