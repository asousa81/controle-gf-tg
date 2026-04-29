import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime
import calendar  # Nova biblioteca para gerenciar os dias do mês

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.warning("⚠️ Acesso restrito. Faça login para ver os relatórios.")
    st.stop()

st.set_page_config(page_title="Relatório Mensal", page_icon="📈", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("📈 Relatório Mensal de Desempenho - GFs")

# --- 1. FILTROS MENSAIS ---
with st.sidebar:
    st.header("📅 Período de Análise")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    
    meses_lista = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    
    mes_sel = st.selectbox("Mês", meses_lista, index=datetime.now().month - 1)
    
    # Mapeamento e cálculo do último dia real do mês
    mes_num = meses_lista.index(mes_sel) + 1
    # calendar.monthrange retorna (dia_da_semana_inicial, total_de_dias)
    ultimo_dia = calendar.monthrange(ano_sel, mes_num)[1]

st.divider()

# --- 2. BUSCA DE DADOS ---
try:
    # Datas formatadas corretamente de acordo com o mês selecionado
    data_inicio = f"{ano_sel}-{mes_num:02d}-01"
    data_fim = f"{ano_sel}-{mes_num:02d}-{ultimo_dia:02d}"

    res = supabase.table("presencas").select(
        "data_reuniao, observacao, pessoas(nome_completo), grupos_familiares(numero, nome)"
    ).gte("data_reuniao", data_inicio).lte("data_reuniao", data_fim).execute()

    if res.data:
        df = pd.json_normalize(res.data)
        
        # Mapeamento seguro de colunas
        col_map = {
            'data_reuniao': 'Data',
            'observacao': 'Observacao',
            'pessoas.nome_completo': 'Membro',
            'grupos_familiares.numero': 'GF_Num',
            'grupos_familiares.nome': 'GF_Nome'
        }
        df = df.rename(columns=col_map)

        # Forçar strings para evitar erro de concatenação int + str
        df['GF'] = "GF " + df['GF_Num'].astype(str) + " - " + df['GF_Nome'].astype(str)
        
        # --- 3. MÉTRICAS CONSOLIDADAS ---
        total_presentes = len(df)
        reunioes_mes = df['Data'].nunique()
        media_mensal = round(total_presentes / reunioes_mes, 1) if reunioes_mes > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("Presenças Totais (Mês)", total_presentes)
        c2.metric("Total de Reuniões", reunioes_mes)
        c3.metric("Média de Engajamento", f"{media_mensal} pessoas/GF")

        st.divider()

        # --- 4. VISÃO POR GRUPO (OBSERVAÇÕES COLETIVAS) ---
        st.subheader(f"📝 Notas e Observações de {mes_sel}")
        
        # Agrupamos por Data e GF para pegar a observação única
        df_obs = df.groupby(['Data', 'GF'])['Observacao'].first().reset_index()
        
        for idx, row in df_obs.sort_values(by='Data', ascending=False).iterrows():
            with st.expander(f"🗓️ {row['Data']} | {row['GF']}"):
                st.write("**Relatório da Reunião:**")
                st.info(row['Observacao'] if row['Observacao'] and row['Observacao'] != 'None' else "Sem observações registradas.")
                
                # Lista quem estava presente
                presentes = df[df['Data'] == row['Data']]['Membro'].tolist()
                st.write(f"👥 **Presentes ({len(presentes)}):** {', '.join(presentes)}")

    else:
        st.info(f"Nenhum registro encontrado para {mes_sel} de {ano_sel}.")

except Exception as e:
    st.error(f"Erro ao gerar relatório mensal: {e}")
