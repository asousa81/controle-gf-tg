import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login.")
    st.stop()

st.set_page_config(page_title="Relatório de Atividades", page_icon="📝", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

# --- 1. SELEÇÃO DE PARÂMETROS ---
with st.sidebar:
    st.header("⚙️ Configurações")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses_lista = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses_lista, index=datetime.now().month - 1)
    
    res_g = supabase.table("grupos_familiares").select("id, numero, nome, publico_alvo").eq("ativo", True).order("numero").execute()
    grupo_sel = st.selectbox("Selecione o GF", res_g.data, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

st.title("📄 Relatório de Atividades do Grupo Familiar")
st.subheader(f"{mes_sel} de {ano_sel}")

if grupo_sel:
    # --- 2. COLETA DE DADOS ---
    mes_num = meses_lista.index(mes_sel) + 1
    ultimo_dia = calendar.monthrange(ano_sel, mes_num)[1]
    data_inicio = f"{ano_sel}-{mes_num:02d}-01"
    data_fim = f"{ano_sel}-{mes_num:02d}-{ultimo_dia:02d}"

    # Busca Membros e Presenças
    res_membros = supabase.table("membros_grupo").select("funcao, pessoa_id, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    res_presencas = supabase.table("presencas").select("data_reuniao, observacao, pessoa_id").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", data_inicio).lte("data_reuniao", data_fim).execute()

    # --- 3. CABEÇALHO ESTILIZADO (Igual ao modelo) ---
    lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
    colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']
    
    st.markdown(f"""
    <style>
        .relatorio-header {{ background-color: #f8f9fa; padding: 15px; border: 2px solid #2c3e50; border-radius: 4px; margin-bottom: 20px; font-family: sans-serif; }}
        .label {{ font-weight: bold; text-transform: uppercase; font-size: 0.75em; color: #34495e; display: block; }}
        .value {{ font-size: 1.1em; font-weight: 500; color: #000; padding-bottom: 8px; }}
        .header-table {{ width: 100%; border-collapse: collapse; }}
        .header-table td {{ border: 1px solid #bdc3c7; padding: 8px; }}
    </style>
    <div class="relatorio-header">
        <table class="header-table">
            <tr>
                <td colspan="2"><span class="label">NOME DO GRUPO FAMILIAR:</span><div class="value">GF {grupo_sel['numero']} - {grupo_sel['nome']}</div></td>
                <td style="width: 15%;"><span class="label">Nº DO GF:</span><div class="value">{grupo_sel['numero']}</div></td>
            </tr>
            <tr>
                <td style="width: 50%;"><span class="label">LÍDER:</span><div class="value">{", ".join(lideres) if lideres else "Não definido"}</div></td>
                <td colspan="2"><span class="label">COORDENADOR:</span><div class="value">Pr. Arthur e Pra. Simone</div></td>
            </tr>
            <tr>
                <td><span class="label">LÍDER EM TREINAMENTO (CO-LÍDER):</span><div class="value">{", ".join(colideres) if colideres else "0"}</div></td>
                <td colspan="2"><span class="label">PÚBLICO ALVO:</span><div class="value">{grupo_sel.get('publico_alvo', 'Misto')}</div></td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # --- 4. GRADE DE PRESENÇAS ---
    if res_presencas.data:
        df_p = pd.DataFrame(res_presencas.data)
        datas_reuniao = sorted(df_p['data_reuniao'].unique())
        
        # Mapeamento de datas para colunas do relatório (ex: 01/abr)
        colunas_datas = {d: datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b') for d in datas_reuniao}
        
        lista_presenca = []
        for m in res_membros.data:
            nome = m['pessoas']['nome_completo']
            p_id = m['pessoa_id']
            tipo = "Visitante" if m['funcao'] == "VISITANTE" else "Membro"
            
            row = {"Nome do Membro": nome, "Tipo": tipo}
            for data_orig, data_format in colunas_datas.items():
                # Verifica presença no dataframe baixado
                esta_presente = not df_p[(df_p['data_reuniao'] == data_orig) & (df_p['pessoa_id'] == p_id)].empty
                row[data_format] = "C" if esta_presente else "-"
            lista_presenca.append(row)

        df_final = pd.DataFrame(lista_presenca)

        # Exibição das Tabelas
        st.write("### 📋 Frequência de Membros")
        st.dataframe(df_final[df_final['Tipo'] == 'Membro'].drop(columns=['Tipo']), use_container_width=True, hide_index=True)
        
        df_visit = df_final[df_final['Tipo'] == 'Visitante']
        if not df_visit.empty:
            st.write("### 👣 Visitantes")
            st.dataframe(df_visit.drop(columns=['Tipo']), use_container_width=True, hide_index=True)

        st.divider()

        # --- 5. OBSERVAÇÕES ORGANIZADAS POR DATA ---
        st.write("### 📝 Observações e Notas das Reuniões")
        
        # Agrupamos para garantir uma única nota por dia de reunião
        df_obs = df_p.groupby('data_reuniao')['observacao'].first().reset_index()
        # Ordenamos por data (do mais antigo para o mais novo, como em um relatório histórico)
        df_obs = df_obs.sort_values(by='data_reuniao')

        # Criamos um container para as observações parecerem uma caixa de texto única ou lista
        for _, row in df_obs.iterrows():
            if row['observacao'] and row['observacao'] != 'None':
                data_f = datetime.strptime(row['data_reuniao'], '%Y-%m-%d').strftime('%d/%m/%Y')
                st.markdown(f"**📅 Dia {data_f}:**")
                st.info(row['observacao'])
    else:
        st.info("Nenhum registro de presença para este grupo no mês selecionado.")

else:
    st.info("Selecione um Grupo Familiar no menu lateral para gerar o relatório.")
