import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema de Gestão - GFs", page_icon="📋", layout="wide")

SENHA_ADMIN = "gf123"
DB_NAME = "gf_gestao_final.db"

# --- FUNÇÕES DE BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, lider_1 TEXT, lider_2 TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reunioes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, gf_id INTEGER, 
        horario_inicio TEXT, horario_termino TEXT, UNIQUE(data, gf_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS membros (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, estado_civil INTEGER,
        data_nascimento TEXT, data_casamento TEXT, gf_id INTEGER, FOREIGN KEY(gf_id) REFERENCES gfs(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS presencas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, membro_id INTEGER, gf_id INTEGER, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS visitantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, nome TEXT, gf_id INTEGER)''')
    
    c.execute("SELECT COUNT(*) FROM gfs")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO gfs (nome, lider_1, lider_2) VALUES (?, ?, ?)", ("GF Sede", "Pr. Arthur", "Pra. Simone"))
    conn.commit()
    conn.close()

init_db()

# --- AUXILIARES ---
opcoes_chamada = {"C": "C - No horário", "A": "A - Atraso", "F": "F - Falta", "D": "D - Justificada", "E": "E - Evento"}
estado_civil_dict = {1: "Casado(a)", 2: "Solteiro(a)", 3: "Casado s/ cônjuge", 4: "Viúvo(a)", 5: "Divorciado(a)"}
meses = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}

def check_password():
    if "admin_logado" not in st.session_state: st.session_state.admin_logado = False
    if not st.session_state.admin_logado:
        senha = st.text_input("Senha de Admin", type="password")
        if st.button("Entrar"):
            if senha == SENHA_ADMIN:
                st.session_state.admin_logado = True
                st.rerun()
            else: st.error("Senha incorreta")
        return False
    return True

# --- INTERFACE ---
st.title("📋 Sistema de Gestão Multi-GF")

conn = sqlite3.connect(DB_NAME)
df_gfs = pd.read_sql_query("SELECT * FROM gfs", conn)

with st.sidebar:
    st.header("Configuração da Reunião")
    if not df_gfs.empty:
        gf_opcoes = dict(zip(df_gfs['id'], df_gfs['nome']))
        gf_selecionado_id = st.selectbox("Selecione o GF", options=list(gf_opcoes.keys()), format_func=lambda x: gf_opcoes[x])
        gf_atual = df_gfs[df_gfs['id'] == gf_selecionado_id].iloc[0]
        st.info(f"**Líderes:** {gf_atual['lider_1']} & {gf_atual['lider_2']}")
    else:
        st.error("Nenhum GF cadastrado.")
        st.stop()
    
    data_reuniao = st.date_input("Data", date.today())
    h_inicio = st.time_input("Início", datetime.strptime("20:00", "%H:%M").time())
    h_fim = st.time_input("Término", datetime.strptime("22:00", "%H:%M").time())

aba_chamada, aba_visitantes, aba_datas, aba_relatorio, aba_admin = st.tabs(["👥 Chamada", "👋 Visitantes", "🎉 Datas", "📊 Relatório Mensal", "🔐 Admin"])

# --- CHAMADA ---
with aba_chamada:
    st.subheader(f"Chamada: {gf_atual['nome']}")
    membros_df = pd.read_sql_query("SELECT id, nome FROM membros WHERE gf_id = ? ORDER BY nome", conn, params=(gf_selecionado_id,))
    
    if membros_df.empty: st.info("Adicione membros na aba Admin para este grupo.")
    else:
        with st.form("form_chamada"):
            resultados = {}
            for _, row in membros_df.iterrows():
                col1, col2 = st.columns([3, 2])
                col1.write(f"**{row['nome']}**")
                resultados[row['id']] = col2.selectbox("Status", options=list(opcoes_chamada.keys()), format_func=lambda x: opcoes_chamada[x], key=f"m_{row['id']}", label_visibility="collapsed")
            
            if st.form_submit_button("Salvar Relatório do Dia", use_container_width=True):
                data_s = data_reuniao.strftime('%Y-%m-%d')
                c = conn.cursor()
                c.execute("REPLACE INTO reunioes (data, gf_id, horario_inicio, horario_termino) VALUES (?, ?, ?, ?)", 
                          (data_s, gf_selecionado_id, h_inicio.strftime("%H:%M"), h_fim.strftime("%H:%M")))
                c.execute("DELETE FROM presencas WHERE data = ? AND gf_id = ?", (data_s, gf_selecionado_id))
                for m_id, status in resultados.items():
                    c.execute("INSERT INTO presencas (data, m_id, gf_id, status)", (data_s, m_id, gf_selecionado_id, status)) # Corrigido aqui
                    # Ajustando para os nomes de colunas corretos
                    c.execute("INSERT INTO presencas (data, membro_id, gf_id, status) VALUES (?, ?, ?, ?)", (data_s, m_id, gf_selecionado_id, status))
                conn.commit()
                st.success("Dados salvos com sucesso!")

# --- VISITANTES ---
with aba_visitantes:
    st.subheader("Visitantes")
    nome_v = st.text_input("Nome do Visitante")
    if st.button("Registrar Visitante"):
        if nome_v:
            c = conn.cursor()
            c.execute("INSERT INTO visitantes (data, nome, gf_id) VALUES (?, ?, ?)", (data_reuniao.strftime('%Y-%m-%d'), nome_v, gf_selecionado_id))
            conn.commit()
            st.success("Visitante registrado!")

# --- DATAS ---
with aba_datas:
    st.subheader("Aniversariantes do Mês (Todos os GFs)")
    hoje = date.today()
    df_m = pd.read_sql_query("SELECT nome, data_nascimento, data_casamento FROM membros", conn)
    if not df_m.empty:
        df_m['mes_nasc'] = df_m['data_nascimento'].apply(lambda x: int(x.split('/')[1]) if x and '/' in x else 0)
        aniv = df_m[df_m['mes_nasc'] == hoje.month][['nome', 'data_nascimento']]
        if not aniv.empty: st.dataframe(aniv, hide_index=True, use_container_width=True)
        else: st.write("Nenhum aniversário de vida este mês.")
    else: st.write("Nenhum membro cadastrado.")

# --- RELATÓRIO MENSAL ---
with aba_relatorio:
    st.subheader("📊 Acompanhamento Mensal")
    col_ano, col_mes = st.columns(2)
    ano_sel = col_ano.selectbox("Ano", [2025, 2026, 2027], index=1)
    mes_sel = col_mes.selectbox("Mês", options=list(meses.keys()), format_func=lambda x: meses[x], index=hoje.month-1)
    
    data_filtro = f"{ano_sel}-{mes_sel:02d}%"
    
    df_reu = pd.read_sql_query("SELECT data, horario_inicio, horario_termino FROM reunioes WHERE gf_id = ? AND data LIKE ?", conn, params=(gf_selecionado_id, data_filtro))
    if not df_reu.empty:
        st.markdown("#### Horários das Reuniões")
        st.dataframe(df_reu.rename(columns={'data': 'Data', 'horario_inicio': 'Início', 'horario_termino': 'Término'}), hide_index=True)
        
        query_frequencia = "SELECT m.nome as Membro, p.data as Data, p.status as Status FROM presencas p JOIN membros m ON p.membro_id = m.id WHERE p.gf_id = ? AND p.data LIKE ?"
        df_freq = pd.read_sql_query(query_frequencia, conn, params=(gf_selecionado_id, data_filtro))
        if not df_freq.empty:
            st.markdown("#### Tabela de Presença")
            df_pivot = df_freq.pivot(index='Membro', columns='Data', values='Status').fillna('-')
            st.table(df_pivot)
    else: st.warning("Sem registros para este mês.")

# --- ADMIN (RESTAURADO E COMPLETO) ---
with aba_admin:
    if check_password():
        st.subheader("Painel de Controle")
        tarefa = st.radio("Selecione a tarefa administrativa", ["Gerenciar GFs", "Gerenciar Membros"], horizontal=True)
        
        if tarefa == "Gerenciar GFs":
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.markdown("#### Novo GF")
                n_gf = st.text_input("Nome")
                l1 = st.text_input("Líder 1")
                l2 = st.text_input("Líder 2")
                if st.button("Salvar Grupo"):
                    c = conn.cursor()
                    c.execute("INSERT INTO gfs (nome, lider_1, lider_2) VALUES (?, ?, ?)", (n_gf, l1, l2))
                    conn.commit()
                    st.rerun()
            with col_b:
                st.markdown("#### GFs Ativos")
                st.dataframe(df_gfs, hide_index=True)
                id_del_gf = st.number_input("ID do GF para excluir", min_value=0, step=1)
                if st.button("Excluir GF"):
                    c = conn.cursor()
                    c.execute("DELETE FROM gfs WHERE id = ?", (id_del_gf,))
                    conn.commit()
                    st.rerun()

        elif tarefa == "Gerenciar Membros":
            col_c, col_d = st.columns([1, 2])
            with col_c:
                st.markdown("#### Novo Membro")
                with st.form("add_m_form"):
                    gf_dest = st.selectbox("Vincular ao GF", options=list(gf_opcoes.keys()), format_func=lambda x: gf_opcoes[x])
                    nome_m = st.text_input("Nome Completo")
                    ec = st.selectbox("Estado Civil", list(estado_civil_dict.keys()), format_func=lambda x: estado_civil_dict[x])
                    dn = st.date_input("Nascimento", value=None, min_value=date(1940,1,1))
                    dc = st.date_input("Casamento", value=None) if ec in [1,3] else None
                    if st.form_submit_button("Cadastrar"):
                        c = conn.cursor()
                        c.execute("INSERT INTO membros (nome, estado_civil, data_nascimento, data_casamento, gf_id) VALUES (?,?,?,?,?)",
                                  (nome_m, ec, dn.strftime('%d/%m/%Y') if dn else "", dc.strftime('%d/%m/%Y') if dc else "", gf_dest))
                        conn.commit()
                        st.success("Membro Cadastrado!")
                        st.rerun()
            with col_d:
                st.markdown("#### Lista de Membros")
                df_all_m = pd.read_sql_query("SELECT m.id, m.nome, g.nome as GF FROM membros m JOIN gfs g ON m.gf_id = g.id", conn)
                st.dataframe(df_all_m, hide_index=True)
                id_del_m = st.number_input("ID do Membro para excluir", min_value=0, step=1)
                if st.button("Excluir Membro"):
                    c = conn.cursor()
                    c.execute("DELETE FROM membros WHERE id = ?", (id_del_m,))
                    conn.commit()
                    st.rerun()

conn.close()
