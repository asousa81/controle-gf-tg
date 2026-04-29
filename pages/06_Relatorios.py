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
    st.header("⚙️ Configurações do Relatório")
    ano_sel = st.selectbox("Ano", [2025, 2026], index=1)
    meses_lista = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                   "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    mes_sel = st.selectbox("Mês", meses_lista, index=datetime.now().month - 1)
    
    # Busca GFs ativos para o filtro
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

    # Busca Membros e suas funções
    res_membros = supabase.table("membros_grupo").select("funcao, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).execute()
    
    # Busca Presenças e Observações
    res_presencas = supabase.table("presencas").select("data_reuniao, observacao, pessoa_id").eq("grupo_id", grupo_sel["id"]).gte("data_reuniao", data_inicio).lte("data_reuniao", data_fim).execute()

    # --- 3. MONTAGEM DO CABEÇALHO ---
    # Identifica líderes e auxiliares para o cabeçalho
    lideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'LÍDER']
    colideres = [m['pessoas']['nome_completo'] for m in res_membros.data if m['funcao'] == 'CO-LÍDER']
    
    st.markdown(f"""
    <style>
        .relatorio-header {{ background-color: #f0f2f6; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px; }}
        .label {{ font-weight: bold; text-transform: uppercase; font-size: 0.8em; color: #555; }}
        .value {{ font-size: 1em; margin-bottom: 10px; }}
    </style>
    <div class="relatorio-header">
        <table style="width:100%; border-collapse: collapse;">
            <tr>
                <td style="width:70%"><span class="label">NOME DO GRUPO FAMILIAR:</span><br><div class="value">GF {grupo_sel['numero']} - {grupo_sel['nome']}</div></td>
                <td><span class="label">Nº DO GF:</span><br><div class="value">{grupo_sel['numero']}</div></td>
            </tr>
            <tr>
                <td><span class="label">LÍDER:</span><br><div class="value">{", ".join(lideres) if lideres else "Não definido"}</div></td>
                <td><span class="label">COORDENADOR:</span><br><div class="value">Pr. Arthur e Pra. Simone</div></td>
            </tr>
            <tr>
                <td><span class="label">LÍDER EM TREINAMENTO:</span><br><div class="value">{", ".join(colideres) if colideres else "0"}</div></td>
                <td><span class="label">PÚBLICO ALVO:</span><br><div class="value">{grupo_sel.get('publico_alvo', 'Misto')}</div></td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # --- 4. GRADE DE PRESENÇAS ---
    if res_presencas.data:
        df_p = pd.DataFrame(res_presencas.data)
        
        # Mapeia IDs para Nomes de Membros Ativos
        membros_dict = {m['pessoas']['nome_completo']: [] for m in res_membros.data if m['funcao'] != 'VISITANTE'}
        visitantes_dict = {m['pessoas']['nome_completo']: [] for m in res_membros.data if m['funcao'] == 'VISITANTE'}
        
        # Lista de todas as datas que tiveram reunião no mês
        datas_reuniao = sorted(df_p['data_reuniao'].unique())
        
        # Prepara dados para o Pivot
        # Para cada membro, verificamos se o ID dele está na lista de presença daquela data
        lista_final = []
        todas_pessoas_vinc = {m['pessoas']['nome_completo']: m['funcao'] for m in res_membros.data}

        for nome, funcao in todas_pessoas_vinc.items():
            row = {"Membro": nome, "Tipo": "Visitante" if funcao == "VISITANTE" else "Membro"}
            for d in datas_reuniao:
                # Busca se a pessoa (pelo nome, via join) estava presente naquela data
                p_na_data = any(
                    any(pres['pessoa_id'] == m_id['id'] for m_id in supabase.table("pessoas").select("id").eq("nome_completo", nome).execute().data)
                    for pres in res_presencas.data if pres['data_reuniao'] == d
                )
                # Otimização: No mundo real, faríamos um join no DF. Aqui simplificamos a lógica para o Pivot:
                row[datetime.strptime(d, '%Y-%m-%d').strftime('%d/%b')] = "C" if p_na_data else ""
            lista_final.append(row)

        df_grid = pd.DataFrame(lista_final)
        
        st.write("### Frequência de Membros")
        st.dataframe(df_grid[df_grid['Tipo'] == 'Membro'].drop(columns=['Tipo']), use_container_width=True, hide_index=True)
        
        if not df_grid[df_grid['Tipo'] == 'Visitante'].empty:
            st.write("### Visitantes")
            st.dataframe(df_grid[df_grid['Tipo'] == 'Visitante'].drop(columns=['Tipo']), use_container_width=True, hide_index=True)

        # --- 5. OBSERVAÇÕES ---
        st.write("### Observações do Mês")
        # Pega as observações únicas de cada reunião
        obs_mes = df_p.groupby('data_reuniao')['observacao'].first().dropna().unique()
        obs_texto = "\n".join([f"- {o}" for o in obs_mes if o and o != 'None'])
        
        st.text_area("Notas Coletivas", value=obs_texto if obs_texto else "Nenhuma observação registrada.", height=150, disabled=True)

    else:
        st.info("Ainda não há lançamentos de presença para este grupo no mês selecionado.")
