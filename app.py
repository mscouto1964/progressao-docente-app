import streamlit as st
from datetime import datetime, timedelta

def calcular_data_progressao(
    data_entrada_escalao: datetime,
    escalão_atual: int,
    dias_cong_1: int,
    dias_cong_2: int,
    acelerador_2023: bool,
    dias_remanescentes: int,
    merito: str,
    grau: str
):
    dias_recuperados_anteriores = 1018
    modulo_escalao = 730 if escalão_atual == 5 else 1460

    # 1. Calcular dias congelados e a recuperar
    dias_congelados = dias_cong_1 + dias_cong_2
    dias_a_recuperar = dias_congelados - dias_recuperados_anteriores
    if acelerador_2023:
        dias_a_recuperar -= 365

    # 2. Tranches de recuperação
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

    # 3. Inicialização do tempo de serviço acumulado
    dias_acumulados = dias_remanescentes
    ordem_explicacao = []

    # 3.1. Bonificação por mérito (primeiro)
    if merito == "Excelente":
        dias_acumulados += 365
        ordem_explicacao.append("Bonificação por mérito (Excelente): +365 dias")
    elif merito == "Muito Bom":
        dias_acumulados += 180
        ordem_explicacao.append("Bonificação por mérito (Muito Bom): +180 dias")

    # 3.2. Redução por grau académico (depois)
    if grau == "Doutor":
        dias_acumulados += 730
        ordem_explicacao.append("Redução por Doutoramento: +730 dias")
    elif grau == "Mestre":
        dias_acumulados += 365
        ordem_explicacao.append("Redução por Mestrado: +365 dias")

    # 3.3. Somar serviço real e tranches de recuperação (por último)
    datas = []
    data_atual = data_entrada_escalao
    hoje = datetime.today()
    tranches_futuras = [(d, n) for d, n in tranches_recuperacao if d >= data_atual]

    while dias_acumulados < modulo_escalao:
        if tranches_futuras and data_atual >= tranches_futuras[0][0]:
            proxima_data, dias_tranche = tranches_futuras.pop(0)
            dias_acumulados += dias_tranche
            ordem_explicacao.append(f"Tranche de {dias_tranche} dias em {proxima_data.strftime('%d-%m-%Y')}")
            datas.append((data_atual, dias_acumulados))
        else:
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
        "ordem_explicacao": ordem_explicacao
    }

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Progressão Docente", page_icon="🎓")
st.title("Calculadora de Progressão Docente")
st.write("Desenvolvido por **Manuel Couto**")
st.write("Preveja a sua próxima progressão de escalão com base no tempo de serviço efetivo e recuperado.\n\nA ordem legal de contabilização é: bonificação por mérito → redução por grau académico → tempo recuperado.")

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
    merito = st.selectbox("Menção de mérito no escalão anterior?", options=["Nenhuma", "Muito Bom", "Excelente"], index=0)
    grau = st.selectbox("Grau académico com redução?", options=["Nenhum", "Mestre", "Doutor"], index=0)
    submitted = st.form_submit_button("Calcular Progressão")

if submitted:
    resultado = calcular_data_progressao(
        data_entrada_escalao=datetime.combine(data_entrada_escalao, datetime.min.time()),
        escalão_atual=escalão_atual,
        dias_cong_1=dias_cong_1,
        dias_cong_2=dias_cong_2,
        acelerador_2023=acelerador_2023,
        dias_remanescentes=dias_remanescentes,
        merito=merito,
        grau=grau
    )

    st.success(f"Data previsível de progressão: **{resultado['data_progressao']}**")
    st.write(f"Tempo total acumulado no escalão: **{resultado['dias_no_escalao']} dias**")
    st.write(f"Dias de serviço a recuperar: **{resultado['dias_a_recuperar']}**")
    st.write(f"Tempo de serviço necessário para progressão (módulo): **{resultado['modulo_escalao']} dias**")
    st.subheader("Ordem de contabilização aplicada:")
    for linha in resultado['ordem_explicacao']:
        st.write("-", linha)
    st.subheader("Tranches de recuperação:")
    for data, dias in resultado['tranches']:
        st.write(f"- {data.date()}: {dias} dias")
    st.subheader("Evolução do tempo de serviço no escalão:")
    for data, dias in resultado["historico"]:
        st.write(f"{data.date()}: {dias} dias")

st.markdown("---")
st.caption("""
Sugestões ou dúvidas: mscouto@aecorga.pt
Confirme sempre os resultados junto da legislação e da escola/agrupamento.
""")
