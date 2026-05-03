import streamlit as st

# Configuração da página
st.set_page_config(page_title="Bem-vindo", page_icon="👋", layout="wide")

# Saudação personalizada
nome = st.session_state.get("nome_usuario", "Líder")
st.title(f"👋 Olá, {nome}!")
st.subheader("Bem-vindo ao Portal de Gestão dos Grupos Familiares – GF's")

st.divider()

# Conteúdo Estilo "Sketchnote" (Visual e direto)
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🎯 O que você pode fazer por aqui?
    
    *   **Lançar Presenças:** Registre os encontros do seu GF de forma rápida.
    *   **Editar Lançamentos:** Corrija horários ou presenças de reuniões passadas.
    *   **Ver Relatórios:** Acompanhe o engajamento e as notas pastorais do seu grupo.
    *   **Mural de Oração:** Acompanhe os pedidos de orações do seu grupo
    """)

with col2:
    st.info("""
    **💡 Dica de Líder:**
    O lançamento regular das presenças nos ajuda a entender a saúde do GF e a apoiar melhor cada membro em sua caminhada.
    """)

st.divider()
st.image("logo_tg.jpg", width=150)
st.write("---")
st.caption("IEQ Templo Gospel - Uma igreja para Permanecer")
