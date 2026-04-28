import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Controle de Chamada - GF", page_icon="📋", layout="centered")

# --- SENHA DO ADMIN ---
# Recomendo alterar esta senha depois ou usar o st.secrets no ambiente de produção
SENHA_ADMIN = "gf123"

# --- FUNÇÕES DE BANCO DE DADOS (SQLite) ---
DB_NAME = "gf_controle.db"

def init_db():
    """Cria as tabelas no banco de dados se não existirem."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela de Membros
    c.execute('''
        CREATE TABLE IF NOT EXISTS membros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            estado_civil INTEGER,
            gf_nome TEXT
        )
    ''')
    
    # Tabela de Presenças (Chamada)
    c.execute('''
        CREATE TABLE IF NOT EXISTS presencas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            membro_id INTEGER,
            status TEXT,
            FOREIGN KEY(membro_id) REFERENCES membros(id)
        )
    ''')
    
    # Tabela de Visitantes
    c.execute('''
        CREATE TABLE IF NOT EXISTS visitantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            nome TEXT NOT NULL
        )
    ''')
    
    # Tabela de Configurações (Líderes, GF atual, etc.)
    c.execute('''
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')
    
    # Inserir configurações padrão se a tabela estiver vazia
    c.execute("SELECT COUNT(*) FROM config")
    if c.fetchone()[0] == 0:
        configs_iniciais = [
            ("lider", "Pr. Arthur"),
            ("coordenador", "Pra. Simone"),
            ("nome_gf", "GF Principal")
        ]
        c.executemany("INSERT INTO config (chave, valor) VALUES (?, ?)", configs_iniciais)
        
    conn.commit()
    conn.close()

def get_config(chave):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT valor FROM config WHERE chave = ?", (chave,))
    resultado = c.fetchone()
    conn.close()
    return resultado[0] if resultado else ""

def set_config(chave, valor):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("REPLACE INTO config (chave, valor) VALUES (?, ?)", (chave, valor))
    conn.commit()
    conn.close()

# Inicializa o banco de dados logo que o app abre
init_db()

# --- AUTENTICAÇÃO ---
def check_password():
    if "admin_logado" not in st.session_state:
        st.session_state.admin_logado = False

    if not st.session_state.admin_logado:
        st.warning("Área restrita à liderança.")
        senha = st.text_input("Senha de Acesso", type="password")
        if st.button("Entrar"):
            if senha == SENHA_ADMIN:
                st.session_state.admin_logado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
        return False
    return True

# --- DICIONÁRIOS DE CÓDIGOS ---
opcoes_chamada = {
    "C": "C - Comparecimento no horário",
    "A": "A - Atraso (até 15 min)",
    "F": "F - Falta sem aviso",
    "D": "D - Falta justificada",
    "E": "E - Evento na Igreja"
}

estado_civil_dict = {
    1: "1 - Casado(a)", 
    2: "2 - Solteiro(a)", 
    3: "3 - Casado s/ cônjuge", 
    4: "4 - Viúvo(a)", 
    5: "5 - Divorciado(a)"
}

# --- INTERFACE PRINCIPAL ---
st.title("📋 Relatório de Atividades do GF")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Detalhes do Encontro")
    
    # Carrega configs do banco
    nome_gf_atual = get_config("nome_gf")
    lider_atual = get_config("lider")
    coord_atual = get_config("coordenador")
    
    data_reuniao = st.date_input("Data da Reunião", date.today())
    st.info(f"**GF:** {nome_gf_atual}\n\n**Líder:** {lider_atual}\n\n**Coordenador:** {coord_atual}")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        inicio = st.time_input("Início")
    with col2:
        termino = st.time_input("Término")

# --- ABAS ---
aba_chamada, aba_visitantes, aba_relatorio, aba_admin = st.tabs([
    "👥 Chamada", "👋 Visitantes", "📊 Relatórios", "🔐 Admin"
])

# ==========================================
# ABA 1: CHAMADA
# ==========================================
with aba_chamada:
    st.subheader(f"Chamada do dia {data_reuniao.strftime('%d/%m/%Y')}")
    
    conn = sqlite3.connect(DB_NAME)
    membros_df = pd.read_sql_query("SELECT id, nome FROM membros ORDER BY nome", conn)
    
    if membros_df.empty:
        st.info("Nenhum membro cadastrado. Vá até a aba 'Admin' para adicionar membros.")
    else:
        with st.form("form_chamada"):
            resultados = {}
            for index, row in membros_df.iterrows():
                col_nome, col_status = st.columns([3, 2])
                with col_nome:
                    st.write(f"**{row['nome']}**")
                with col_status:
                    resultados[row['id']] = st.selectbox(
                        "Status", 
                        options=list(opcoes_chamada.keys()), 
                        format_func=lambda x: opcoes_chamada[x],
                        label_visibility="collapsed",
                        key=f"status_{row['id']}"
                    )
            
            if st.form_submit_button("Salvar Chamada", use_container_width=True):
                # Limpa os registros do dia para evitar duplicidade ao reenviar
                data_str = data_reuniao.strftime('%Y-%m-%d')
                c = conn.cursor()
                c.execute("DELETE FROM presencas WHERE data = ?", (data_str,))
                
                # Insere os novos registros
                for membro_id, status in resultados.items():
                    c.execute("INSERT INTO presencas (data, membro_id, status) VALUES (?, ?, ?)", 
                              (data_str, membro_id, status))
                conn.commit()
                st.success("Chamada salva com sucesso!")
    conn.close()

# ==========================================
# ABA 2: VISITANTES
# ==========================================
with aba_visitantes:
    st.subheader("Registro de Visitantes")
    data_str = data_reuniao.strftime('%Y-%m-%d')
    
    with st.form("form_visitante"):
        nome_visitante = st.text_input("Nome do Visitante")
        if st.form_submit_button("Adicionar Visitante"):
            if nome_visitante.strip():
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("INSERT INTO visitantes (data, nome) VALUES (?, ?)", (data_str, nome_visitante.strip()))
                conn.commit()
                conn.close()
                st.success(f"Visitante '{nome_visitante}' adicionado para a data {data_reuniao.strftime('%d/%m/%Y')}!")
            else:
                st.error("Digite o nome do visitante.")

# ==========================================
# ABA 3: RELATÓRIOS
# ==========================================
with aba_relatorio:
    st.subheader("Visualizar Dados Salvos")
    conn = sqlite3.connect(DB_NAME)
    
    # Relatório de Presenças
    st.markdown("#### Presenças Registradas")
    query_presencas = """
        SELECT p.data as Data, m.nome as Membro, p.status as Status 
        FROM presencas p 
        JOIN membros m ON p.membro_id = m.id 
        ORDER BY p.data DESC, m.nome ASC
    """
    df_presencas = pd.read_sql_query(query_presencas, conn)
    st.dataframe(df_presencas, use_container_width=True, hide_index=True)
    
    # Relatório de Visitantes
    st.markdown("#### Visitantes Recebidos")
    df_visitantes = pd.read_sql_query("SELECT data as Data, nome as Visitante FROM visitantes ORDER BY data DESC", conn)
    st.dataframe(df_visitantes, use_container_width=True, hide_index=True)
    conn.close()

# ==========================================
# ABA 4: ADMINISTRAÇÃO
# ==========================================
with aba_admin:
    if check_password():
        col_header, col_logout = st.columns([4, 1])
        with col_header:
            st.subheader("Painel de Administração")
        with col_logout:
            if st.button("Sair"):
                st.session_state.admin_logado = False
                st.rerun()
                
        menu_admin = st.radio("Selecione a ação:", ["Cadastrar Membros", "Gerenciar Membros", "Configurações do GF"], horizontal=True)
        
        if menu_admin == "Cadastrar Membros":
            with st.form("form_novo_membro"):
                nome_novo = st.text_input("Nome Completo")
                estado_civil = st.selectbox("Estado Civil", list(estado_civil_dict.keys()), format_func=lambda x: estado_civil_dict[x])
                
                if st.form_submit_button("Salvar Membro"):
                    if nome_novo.strip():
                        conn = sqlite3.connect(DB_NAME)
                        c = conn.cursor()
                        c.execute("INSERT INTO membros (nome, estado_civil, gf_nome) VALUES (?, ?, ?)", 
                                  (nome_novo.strip(), estado_civil, get_config("nome_gf")))
                        conn.commit()
                        conn.close()
                        st.success(f"Membro {nome_novo} cadastrado!")
                    else:
                        st.error("O nome não pode estar vazio.")

        elif menu_admin == "Gerenciar Membros":
            conn = sqlite3.connect(DB_NAME)
            df_membros_cadastrados = pd.read_sql_query("SELECT id, nome, estado_civil FROM membros", conn)
            
            if not df_membros_cadastrados.empty:
                st.dataframe(df_membros_cadastrados, hide_index=True, use_container_width=True)
                
                # Excluir membro
                st.markdown("---")
                st.markdown("#### Remover Membro")
                id_remover = st.number_input("Digite o ID do membro para remover", min_value=0, step=1)
                if st.button("Excluir"):
                    c = conn.cursor()
                    # Remove presenças associadas primeiro (integridade referencial)
                    c.execute("DELETE FROM presencas WHERE membro_id = ?", (id_remover,))
                    c.execute("DELETE FROM membros WHERE id = ?", (id_remover,))
                    conn.commit()
                    st.success("Membro removido.")
                    st.rerun()
            else:
                st.info("Nenhum membro cadastrado.")
            conn.close()

        elif menu_admin == "Configurações do GF":
            with st.form("form_config"):
                novo_gf = st.text_input("Nome do Grupo Familiar", value=get_config("nome_gf"))
                novo_lider = st.text_input("Nome do Líder", value=get_config("lider"))
                novo_coord = st.text_input("Nome do Coordenador", value=get_config("coordenador"))
                
                if st.form_submit_button("Salvar Configurações"):
                    set_config("nome_gf", novo_gf)
                    set_config("lider", novo_lider)
                    set_config("coordenador", novo_coord)
                    st.success("Configurações atualizadas com sucesso!")
                    st.rerun()
