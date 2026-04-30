import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar
from fpdf import FPDF

# 1. CONFIGURAÇÃO DA PÁGINA (Sempre a primeira ação)
st.set_page_config(page_title="Relatório Executivo", page_icon="📈", layout="wide")

# 2. CONEXÃO COM SUPABASE
@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- 3. SEGURANÇA: BLOQUEIO DE ACESSO DIRETO ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login na página inicial.")
    st.stop()

# --- 4. FILTRO DE DADOS POR PERFIL (LOGICA DE ACESSO) ---
usuario_id = st.session_state.get('usuario_id')
perfil = st.session_state.get('perfil')

if perfil == 'ADMIN':
    # Arthur e Simone veem tudo
    res_g = supabase.table("grupos_familiares").select("*").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data
else:
    # Líderes veem apenas seus grupos vinculados no CCM
    res_g = supabase.table("membros_grupo").select(
        "grupo_id, grupos_familiares(*)"
    ).eq("pessoa_id", usuario_id).filter("funcao", "in", '("LÍDER", "CO-LÍDER")').execute()
    g_opcoes = [item['grupos_familiares'] for item in res_g.data] if res_g.data else []

# --- 5. FUNÇÃO PREMIUM PARA GERAÇÃO DO PDF ---
def gerar_pdf_oficial(grupo, mes_ano, lideres, colideres, df_membros, obs_texto, taxa_engaj, mapa_horarios):
    pdf = FPDF()
    pdf.add_page()
    
    def c(texto): return str(texto).encode('latin-1', 'replace').decode('latin-1')

    # Cabeçalho Principal
    pdf.set_fill_color(118, 75, 162) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 12, c(f"RELATÓRIO DE ATIVIDADES - {mes_ano}"), ln=True, align="C", fill=True)
    
    # Box de Analytics
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(245, 245, 245)
    pdf.cell(95, 10, c(f" ENGAJAMENTO: {taxa_engaj:.1f}%"), border=1, fill=True)
    pdf.cell(95, 10, c(f" TOTAL DE MEMBROS: {len(df_membros)}"), border=1, fill=True, ln=True)
    
    pdf.ln(5)
    
    # Grade de Informações
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(130, 5, c("NOME DO GRUPO FAMILIAR"), border=1, fill=True)
    pdf.cell(60, 5, c("Nº DO GF"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(130, 8, c(f"{grupo['nome']}"), border=1)
    pdf.cell(60, 8, c(f"{grupo['numero']}"), border=1, ln=True)
    
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, c("LIDERANÇA"), border=1, fill=True)
    pdf.cell(95, 5, c("COORDENAÇÃO"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(95, 8, c(", ".join(lideres) if lideres else "N/A"), border=1)
    pdf.cell(95, 8, c("Pr. Arthur e Pra. Simone"), border=1, ln=True)

    # Nova linha da grade (Público Alvo e Líder em Treinamento)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(95, 5, c("PÚBLICO ALVO"), border=1, fill=True)
    pdf.cell(95, 5, c("LÍDER EM TREINAMENTO"), border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.cell(95, 8, c(grupo.get('publico_alvo', 'Misto')), border=1)
    pdf.cell(95, 8, c(", ".join(colideres) if colideres else "0"), border=1, ln=True)
    
    pdf.ln(10)
    
    # Tabela de Frequência
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, c("Frequência de Membros"), ln=True)
    
    col_num_w, col_nome_w = 10, 60
    qtd_datas = len(df_membros.columns) - 2
    col_data_w = (190 - col_num_w - col_nome_w) / qtd_datas if qtd_datas > 0 else 30
    
    pdf.set_font("Arial", "B", 7)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(col_num_w, 10, "Nº", border=1, align="C", fill=True)
    pdf.cell(col_nome_w, 10, "Membro", border=1, align="C", fill=True)
    
    for col in df_membros.columns[2:]:
        x, y = pdf.get_x(), pdf.get_y()
        pdf.rect(x, y, col_data_w, 10, 'FD')
        pdf.set_xy(x, y + 1)
        pdf.cell(col_data_w, 4, c(col), align="C")
        pdf.set_xy(x, y + 5)
        pdf.set_font("Arial", "", 6)
        horario = mapa_horarios.get(col, "20:00-21:30")
        pdf.cell(col_data_w, 4, c(horario), align="C")
        pdf.set_xy(x + col_data_w, y)
        pdf.set_font("Arial", "B", 7)
    
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 8)
    for _, row in df_membros.iterrows():
        pdf.cell(col_num_w, 8, c(row.iloc[0]), border=1, align="C")
        pdf.cell(col_nome_w, 8, c(row.iloc[1]), border=1)
        for val in row.iloc[2:]:
            if val == 'C':
                pdf.set_fill_color(212, 237, 218)
                pdf.set_text_color(21, 87, 36)
            else:
                pdf.set_fill_color(248, 215, 218)
                pdf.set_text_color(114, 28, 36)
            pdf.cell(col_data_w, 8, c(val), border=1, align="C", fill=True)
            pdf.set_text_color(0, 0, 0)
        pdf.ln()
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, c("Observações Pastorais"), ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 7, c(obs_texto if obs_texto else "Nenhuma observação registrada."), border=1)
    
    return bytes(pdf.output())

# --- 6. CSS ORIGINAL (ESTILO BI PREMIUM) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
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

# --- 7. FILTROS (SIDEBAR) ---
with st.sidebar:
    st.title("📑 BI Manager")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses, index=datetime.now().month - 1)
    
    # AQUI ESTAVA O FILTRO: Agora usamos a lista 'g_opcoes' gerada no início
    if g_opcoes:
        grupo_sel = st.selectbox("Selecione o GF", g_opcoes, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")
    else:
        st.error("Nenhum grupo vinculado ao seu perfil.")
        st.stop()

st.title("📈 Analytics e Desempenho")

# --- 8. LÓGICA DE GERAÇÃO DO RELATÓRIO ---
if grupo_sel:
    mes_idx = meses.index(mes_sel) + 1
    ult_dia = calendar.monthrange(ano_sel, mes_idx)[1]
    d_ini, d_fim = f"{ano_sel}-{mes_idx:02d}-01", f"{ano_sel}-{mes_idx:02d}-{ult_dia:02d}"

    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", d_ini).lte("data_reuniao", d_fim).execute()

    if res_membros.data:
        lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
        colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']

        total_m = len([m for m in res_membros.data if m['funcao'] != 'VISITANTE'])
        df_p_calc = pd.DataFrame(res_presencas.data) if res_presencas.data else pd.DataFrame()
        reunioes_m = len(set(df_p_calc['data_reuniao'])) if not df_p_calc.empty else 0
        
        taxa_engajamento = 0
        if total_m > 0 and reunioes_m > 0:
            membros_ids = [m['pessoa_id'] for m in res_membros.data if m['funcao'] != 'VISITANTE']
            presencas_reais = len(df_p_calc[df_p_calc['pessoa_id'].isin(membros_ids)])
            taxa_engajamento = (presencas_reais / (total_m * reunioes_m)) * 100

        # Cards de Métricas (Degradê Original)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="metric-card"><small>MEMBROS</small><h2>{total_m}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card"><small>ENCONTROS</small><h2>{reunioes_m}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card"><small>% ENGAJAMENTO</small><h2>{taxa_engajamento:.1f}%</h2></div>', unsafe_allow_html=True)

        # Início do Paper Container
        st.markdown(f"""
<div class="paper-container">
<div style="text-align: center; margin-bottom: 30px;">
<h2 style="color: #764ba2; margin: 0; letter-spacing: 1px;">RELATÓRIO DE ATIVIDADES</h2>
<span style="color: #999; font-weight: 600;">{mes_sel.upper()} / {ano_sel}</span>
</div>
<div class="header-grid">
<div>
<div class="info-item"><span class="label">NOME DO GRUPO FAMILIAR</span><span class="value">{grupo_sel['nome']}</span></div>
<div class="info-item"><span class="label">LIDERANÇA</span><span class="value">{", ".join(lideres) if lideres else "N/A"}</span></div>
<div class="info-item"><span class="label">PÚBLICO ALVO</span><span class="value">{grupo_sel.get('publico_alvo', 'Misto')}</span></div>
</div>
<div>
<div class="info-item"><span class="label">COORDENAÇÃO</span><span class="value">Pr. Arthur e Pra. Simone</span></div>
<div class="info-item"><span class="label">LÍDER EM TREINAMENTO</span><span class="value">{", ".join(colideres) if colideres else "0"}</span></div>
</div>
</div>
""", unsafe_allow_html=True)

        if not df_p_calc.empty:
            datas_orig = sorted(df_p_calc['data_reuniao'].unique())
            df_reunioes = df_p_calc.groupby('data_reuniao').first().reset_index()
            
            table_html = f"""<table class="styled-table"><thead><tr><th rowspan="2" style="width: 45px;">Nº</th><th rowspan="2" style="text-align: left;">MEMBROS</th><th colspan="{len(datas_orig)}">ENCONTROS E HORÁRIOS</th></tr><tr>"""
            
            mapa_horarios = {}
            for d in datas_orig:
                info_r = df_reunioes[df_reunioes['data_reuniao'] == d].iloc[0]
                h_i, h_f = str(info_r.get('horario_inicio', '20:00'))[:5], str(info_r.get('horario_termino', '21:30'))[:5]
                dt_fmt = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')
                mapa_horarios[dt_fmt] = f"{h_i}-{h_f}"
                table_html += f"<th>{dt_fmt}<br><span class='time-sub'>{h_i} às {h_f}</span></th>"
            
            table_html += "</tr></thead><tbody>"

            lista_para_pdf = []
            count = 1
            for m in res_membros.data:
                if m['funcao'] == 'VISITANTE': continue
                nome = m['pessoas']['nome_completo']
                table_html += f"<tr><td>{count:02d}</td><td style='text-align: left; font-weight: 600;'>{nome}</td>"
                row_pdf = {"Nº": f"{count:02d}", "Membro": nome}
                for d in datas_orig:
                    dt_f = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')
                    p = not df_p_calc[(df_p_calc['data_reuniao'] == d) & (df_p_calc['pessoa_id'] == m['pessoa_id'])].empty
                    row_pdf[dt_f] = "C" if p else "F"
                    badge = f'<span class="badge-c">C</span>' if p else f'<span class="badge-f">F</span>'
                    table_html += f"<td>{badge}</td>"
                table_html += "</tr>"
                lista_para_pdf.append(row_pdf)
                count += 1
            
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

            st.markdown('<div class="obs-section"><span class="label">Notas Pastorais</span>', unsafe_allow_html=True)
            obs_pdf_texto = ""
            for _, r in df_reunioes.iterrows():
                if r['observacao'] and str(r['observacao']) != 'None':
                    dt_f = datetime.strptime(r['data_reuniao'], '%Y-%m-%d').strftime('%d/%m')
                    st.write(f"**• {dt_f}:** {r['observacao']}")
                    obs_pdf_texto += f"[{dt_f}] {r['observacao']}\n"
            st.markdown('</div></div>', unsafe_allow_html=True) # Fecha Paper Container

            st.divider()
            try:
                pdf_bytes = gerar_pdf_oficial(grupo_sel, f"{mes_sel}/{ano_sel}", lideres, colideres, pd.DataFrame(lista_para_pdf), obs_pdf_texto, taxa_engajamento, mapa_horarios)
                st.download_button(label="📥 Gerar PDF para Impressão", data=pdf_bytes, file_name=f"Relatorio_{mes_sel}_GF{grupo_sel['numero']}.pdf", mime="application/pdf", type="primary", use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao preparar PDF: {e}")
        else:
            st.markdown("<p style='text-align:center; padding: 50px; color: #999;'>Sem dados de presença para este período.</p></div>", unsafe_allow_html=True)
