import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import date, datetime

st.set_page_config(page_title="Editar Presença", page_icon="✏️", layout="wide")

@st.cache_resource
def get_supabase_client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase_client()

st.title("✏️ Ajustar Lançamentos")

# --- PASSO 1: SELEÇÃO ---
col_g, col_d = st.columns(2)

with col_g:
    res_g = supabase.table("grupos_familiares").select("id, numero, nome").eq("ativo", True).order("numero").execute()
    g_opcoes = res_g.data if res_g.data else []
    grupo_sel = st.selectbox("Selecione o GF", g_opcoes, format_func=lambda x: f"GF {x['numero']} - {x['nome']}")

with col_d:
    data_reuniao = st.date_input("Data do Lançamento que deseja editar", value=date.today())

st.divider()

# --- PASSO 2: BUSCA E VALIDAÇÃO DE DADOS ---
if grupo_sel:
    res_presencas_existentes = supabase.table("presencas").select("*").eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()
    
    # VERIFICAÇÃO: Só prosseguimos se houver dados lançados
    if res_presencas_existentes.data:
        mapa_p = {p['pessoa_id']: p for p in res_presencas_existentes.data}
        dados_reuniao = res_presencas_existentes.data[0]
        
        # Função de limpeza para evitar erros de nulos
        def format_time_safe(val, default):
            if val is None or str(val).lower() == 'none':
                return default
            return str(val)[:5]

        obs_previa = dados_reuniao.get('observacao', "")
        h_i_previa = format_time_safe(dados_reuniao.get('horario_inicio'), "20:00")
        h_f_previa = format_time_safe(dados_reuniao.get('horario_termino'), "21:30")

        # --- PASSO 3: INTERFACE DE EDIÇÃO (SÓ APARECE SE HOUVER DADOS) ---
        st.write("### ⏰ Ajustar Horários e Notas")
        c1, c2 = st.columns(2)
        with c1:
            h_inicio = st.time_input("Início", value=datetime.strptime(h_i_previa, "%H:%M").time())
        with c2:
            h_fim = st.time_input("Término", value=datetime.strptime(h_f_previa, "%H:%M").time())

        st.write("### 👥 Lista de Membros")
        
        res_m = supabase.table("membros_grupo").select("pessoa_id, funcao, pessoas(nome_completo)").eq("grupo_id", grupo_sel["id"]).eq("ativo", True).execute()
        
        presencas_editadas = {}
        
        if res_m.data:
            ordem = {"LÍDER": 0, "CO-LÍDER": 1, "ANFITRIÃO": 2, "MEMBRO": 3}
            membros_ordenados = sorted(res_m.data, key=lambda x: ordem.get(x["funcao"], 99))

            for m in membros_ordenados:
                p_id = m["pessoa_id"]
                nome = m['pessoas']['nome_completo']
                col_n, col_p = st.columns([3, 1])
                with col_n:
                    st.write(f"**{nome}** ({m['funcao']})")
                with col_p:
                    presencas_editadas[p_id] = st.checkbox("Presente", value=(p_id in mapa_p), key=f"ed_{p_id}_{data_reuniao}")

            st.divider()
            nova_obs = st.text_area("Observações da Reunião", value=obs_previa)

            # --- PASSO 4: SALVAR ---
            col_save, col_back = st.columns(2)
            
            with col_save:
                if st.button("💾 Atualizar Lançamento", type="primary", use_container_width=True):
                    try:
                        supabase.table("presencas").delete().eq("grupo_id", grupo_sel["id"]).eq("data_reuniao", str(data_reuniao)).execute()
                        
                        lista_nova = []
                        for id_pessoa, marcado in presencas_editadas.items():
                            if marcado:
                                lista_nova.append({
                                    "data_reuniao": str(data_reuniao),
                                    "pessoa_id": id_pessoa,
                                    "grupo_id": grupo_sel["id"],
                                    "observacao": nova_obs,
                                    "horario_inicio": h_inicio.strftime("%H:%M:%S"),
                                    "horario_termino": h_fim.strftime("%H:%M:%S")
                                })
                        
                        if lista_nova:
                            supabase.table("presencas").insert(lista_nova).execute()
                        
                        st.success("✅ Lançamento atualizado!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
            
            with col_back:
                if st.button("🏠 Voltar ao Início", use_container_width=True):
                    st.switch_page("app.py")
    
    else:
        # --- CASO NÃO HAJA DADOS: MOSTRA APENAS A FAIXA AMARELA ---
        st.warning(f"🔍 Nenhum lançamento encontrado para o dia {data_reuniao.strftime('%d/%m/%Y')}.")
        if st.button("🏠 Voltar ao Início", use_container_width=True):
            st.switch_page("app.py")
