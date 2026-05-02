import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date

# --- SEGURANÇA ---
if "logado" not in st.session_state or not st.session_state.logado:
    st.title("🔒 Acesso Restrito")
    st.warning("Por favor, faça login na página inicial para gerenciar membros.")
    if st.button("Ir para o Login"):
        st.switch_page("app.py")
    st.stop()

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Gestão de Pessoas", page_icon="👥", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("👥 Gestão de Membros")
st.markdown("Utilize esta página para cadastrar novos membros ou atualizar informações existentes.")

# Definição das abas para organizar o fluxo
tab_cad, tab_edit = st.tabs(["➕ Novo Cadastro", "📝 Editar / Inativar"])

# --- ABA 1: NOVO CADASTRO ---
with tab_cad:
    with st.form("form_cadastro_pessoa", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome Completo*")
            whatsapp = st.text_input("WhatsApp / Telefone", placeholder="(41) 99999-9999")
            data_nasc = st.date_input("Data de Nascimento", value=date(1990, 1, 1), min_value=date(1900, 1, 1))
            genero = st.selectbox("Gênero", ["Masculino", "Feminino", "Outro"])

        with col2:
            est_civil = st.selectbox("Estado Civil", ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"])
            
            # Campo dinâmico para Casamento
            data_casa = None
            if est_civil == "Casado(a)":
                data_casa = st.date_input("Data de Casamento", value=date.today(), min_value=date(1900, 1, 1))
            
            endereco = st.text_input("Endereço")

        st.markdown("---")
        if st.form_submit_button("🚀 Cadastrar Membro", type="primary"):
            if nome:
                try:
                    supabase.table("pessoas").insert({
                        "nome_completo": nome,
                        "telefone": whatsapp,
                        "data_nascimento": str(data_nasc),
                        "genero": genero,
                        "estado_civil": est_civil,
                        "data_casamento": str(data_casa) if data_casa else None,
                        "endereco": endereco,  # ADICIONE ESTA LINHA
                        "ativo": True
                    }).execute()
                    st.success(f"✨ {nome} cadastrado com sucesso!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("O campo Nome Completo é obrigatório.")

# --- ABA 2: EDITAR / INATIVAR ---
with tab_edit:
    st.subheader("Gerenciar Cadastros")
    
    # Busca a lista atualizada de pessoas
    res_p = supabase.table("pessoas").select("*").order("nome_completo").execute()
    
    if res_p.data:
        p_sel = st.selectbox(
            "Selecione a pessoa para gerenciar", 
            res_p.data, 
            format_func=lambda x: f"{x['nome_completo']} ({'Ativo' if x['ativo'] else 'Inativo'})"
        )
        
        if p_sel:
            with st.form("form_edicao_pessoa"):
                c1, c2 = st.columns(2)
                
                with c1:
                    e_nome = st.text_input("Nome Completo", value=p_sel.get('nome_completo', ''))
                    e_tel = st.text_input("Telefone", value=p_sel.get('telefone', ''))
                    
                    # Tratamento robusto para datas
                    dn_banco = p_sel.get('data_nascimento')
                    dn_val = date.fromisoformat(dn_banco) if dn_banco else date(1990, 1, 1)
                    e_nasc = st.date_input("Data de Nascimento", value=dn_val, min_value=date(1900, 1, 1))
                    
                    # Verificação de segurança para o índice do Gênero
                    lista_gen = ["Masculino", "Feminino", "Outro"]
                    gen_banco = p_sel.get('genero')
                    idx_gen = lista_gen.index(gen_banco) if gen_banco in lista_gen else 0
                    e_gen = st.selectbox("Gênero", lista_gen, index=idx_gen)

                with c2:
                    # Verificação de segurança para o índice do Estado Civil
                    lista_civ = ["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)"]
                    civ_banco = p_sel.get('estado_civil')
                    idx_civ = lista_civ.index(civ_banco) if civ_banco in lista_civ else 0
                    e_est = st.selectbox("Estado Civil", lista_civ, index=idx_civ)
                    
                    e_casa = None
                    if e_est == "Casado(a)":
                        dc_banco = p_sel.get('data_casamento')
                        dc_val = date.fromisoformat(dc_banco) if dc_banco else date.today()
                        e_casa = st.date_input("Data de Casamento", value=dc_val, min_value=date(1900, 1, 1))
                    
                    st.write("---")
                    e_ativo = st.toggle("Membro Ativo", value=p_sel.get('ativo', True))

                if st.form_submit_button("💾 Salvar Alterações"):
                    try:
                        supabase.table("pessoas").update({
                            "nome_completo": e_nome,
                            "telefone": e_tel,
                            "data_nascimento": str(e_nasc),
                            "genero": e_gen,
                            "estado_civil": e_est,
                            "data_casamento": str(e_casa) if e_casa else None,
                            "ativo": e_ativo
                        }).eq("id", p_sel["id"]).execute()
                        st.success("Cadastro atualizado com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro na atualização: {e}")
    else:
        st.info("Nenhum membro cadastrado para edição.")
