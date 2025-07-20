import streamlit as st
from datetime import datetime, timedelta

def calcular_data_progressao(
    data_entrada_escalao: datetime,
    escalão_atual: int,
    dias_cong_1: int,
    dias_cong_2: int,
    acelerador_2023: bool,
    dias_remanescentes: int
):
    # Parâmetros do ECD
    dias_recuperados_anteriores = 1018
    modulo_escalao = 730 if escalão_atual == 5 else 1460

    # 1. Calcular dias congelados e a recuperar
    dias_congelados = dias_cong_1 + dias_cong_2
    dias_a_recuperar = dias_congelados - dias_recuperados_anteriores
    if acelerador_2023:
        dias_a_recuperar -= 365

    # 2. Distribuir pelas tranches (regra: acelerador = 4 parcelas iguais, caso contrário tranches de 599/598)
    if acelerador_2023:
        parcela = dias_a_recuperar // 4
        tranches = [parcela]*4
        resto = dias_a_recuperar - parcela*4
        for i in range(resto):
            tranches[i] += 1
        tranches_recuperacao = [
            (datetime(2024,9,1), tranches[0]),
            (datetime(2025,7,1), tranches[1]),
            (datetime(2026,7,1), tranches[2]),
            (datetime(2027,7,1), tranches[3]),
        ]
    else:
        tranches_recuperacao = [
            (datetime(2024,9,1), min(599, dias_a_recuperar)),
            (datetime(2025,7,1), min(598, max(dias_a_recuperar-599,0))),
            (datetime(2026,7,1), min(598, max(dias_a_recuperar-1197,0))),
            (datetime(2027,7,1), min(598, max(dias_a_recuperar-1795,0))),
        ]

    # 3. Cálculo do tempo de serviço acumulado no escalão
    datas = []
    dias_acumulados = dias_remanescentes
    data_atual = data_entrada_escalao
    hoje = datetime.today()

    # Listar as datas das tranches futuras
    tranches_futuras = [(d, n) for d, n in tranches_recuperacao if d >= data_atual]

    while dias_acumulados < modulo_escalao:
        # Próxima tranche (ou data de hoje se já passou)
        if tranches_futuras and data_atual >= tranches_futuras[0][0]:
            # Se já passou a tranche, soma e remove da lista
            _, dias_tranche = tranches_futuras.pop(0)
            dias_acumulados += dias_tranche
            datas.append((data_atual, dias_acumulados))
        else:
            # Conta dias de serviço real até à próxima tranche ou até perfazer o módulo
            proxima_data = tranches_futuras[0][0] if tranches_futuras else hoje + timedelta(days=modulo_escalao)
            dias_ate_proxima_tranche = (proxima_data - data_atual).days
            dias_para_modulo = modulo_escalao - dias_acumulados
            dias_a_contar = min(dias_ate_proxima_tranche, dias_para_modulo)
            dias_acumulados += dias_a_contar
            data_atual += timedelta(days=dias_a_contar)
            datas.append((data_atual, dias_acumulados))
            if dias_acumulados >= modulo_escalao:
                break

    data_progressao = data_atual

    return {
        "data_progressao": data_progressao.date(),
        "dias_no_escalao": dias_acumulados,
        "historico": datas,
        "dias_a_recuperar": dias_a_recuperar,
        "tranches": tranches_recuperacao,
        "modulo_escalao": modulo_escalao,
    }

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Progressão Docente", page_icon="🎓")
st.title("Calculadora de Progressão Docente")
st.write("Desenvolvido por **Manuel Couto**")
st.write("Preveja a sua próxima progressão de escalão com base no tempo de serviço efetivo e recuperado.")

with st.form("dados_professor"):
    st.header("Dados para o cálculo")
    dias_cong_1 = st.number_input(
        "Dias trabalhados no 1º congelamento (30/08/2005–31/12/2007)",
        min_value=0, max_value=854, value=854
    )
    dias_cong_2 = st.number_input(
        "Dias trabalhados no 2º congelamento (01/01/2011–31/12/2017)",
        min_value=0, max_value=2557, value=2557
    )
    acelerador_2023 = st.checkbox(
        "Usufruiu da aceleração da progressão ao abrigo do DL n.º 74/2023?", value=False
    )
    data_entrada_escalao = st.date_input("Data de entrada no escalão atual", value=datetime(2024,10,27))
    escalão_atual = st.selectbox("Escalão atual", options=list(range(1,11)), index=8)
    dias_remanescentes = st.number_input("Tempo de serviço que transita para o escalão atual (em dias)", min_value=0, value=0)
    submitted = st.form_submit_button("Calcular Progressão")

if submitted:
    resultado = calcular_data_progressao(
        data_entrada_escalao=datetime.combine(data_entrada_escalao, datetime.min.time()),
        escalão_atual=escalão_atual,
        dias_cong_1=dias_cong_1,
        dias_cong_2=dias_cong_2,
        acelerador_2023=acelerador_2023,
        dias_remanescentes=dias_remanescentes
    )

    st.success(f"Data previsível de progressão: **{resultado['data_progressao']}**")
    st.write(f"Tempo total acumulado no escalão: **{resultado['dias_no_escalao']} dias**")
    st.write(f"Dias de serviço a recuperar: **{resultado['dias_a_recuperar']}**")
    st.write(f"Tempo de serviço necessário para progressão (módulo): **{resultado['modulo_escalao']} dias**")
    st.subheader("Tranches de recuperação:")
    for data, dias in resultado['tranches']:
        st.write(f"- {data.date()}: {dias} dias")
    st.subheader("Evolução do tempo de serviço no escalão:")
    for data, dias in resultado["historico"]:
        st.write(f"{data.date()}: {dias} dias")

st.markdown("---")
st.caption("Confirme sempre os resultados junto da legislação e da escola/agrupamento.")
