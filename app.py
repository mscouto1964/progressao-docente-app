import streamlit as st
from datetime import datetime, timedelta

def calcular_proxima_progressao(
    data_entrada_escalao: datetime,
    escalão_atual: int,
    dias_servico_efetivo: int,
    horas_formacao: float,
    avaliacao: str,
    observacao_aulas: bool,
    dias_congelados: int = 3411,
    dias_recuperados_anteriores: int = 1018,
    acelerador_2023: bool = False,
    grau_academico: str = None,
    bonificacao_merito: str = None,
    tranches_recuperacao: list = None,
    data_hoje: datetime = None
):
    if data_hoje is None:
        data_hoje = datetime.today()
    modulo_escalao = 730 if escalão_atual == 5 else 1460
    horas_formacao_necessarias = 12.5 if escalão_atual == 5 else 25

    dias_a_recuperar = 2393
    if acelerador_2023:
        dias_a_recuperar -= 365

    if tranches_recuperacao is None:
        tranches_recuperacao = [
            (datetime(2024,9,1), 599),
            (datetime(2025,7,1), 598),
            (datetime(2026,7,1), 598),
            (datetime(2027,7,1), 598),
        ]
    dias_recuperados_rtp = sum(qt for data, qt in tranches_recuperacao if data <= data_hoje)

    dias_bonificacao_merito = 0
    if bonificacao_merito == "Excelente":
        dias_bonificacao_merito = 365
    elif bonificacao_merito == "Muito Bom":
        dias_bonificacao_merito = 180

    dias_reducao_grau = 0
    if grau_academico == "Mestre":
        dias_reducao_grau = 365
    elif grau_academico == "Doutor":
        dias_reducao_grau = 730

    dias_totais = dias_servico_efetivo + dias_recuperados_rtp + dias_bonificacao_merito + dias_reducao_grau

    requisitos = []
    if avaliacao not in ["Bom", "Muito Bom", "Excelente"]:
        requisitos.append("Avaliação mínima de 'Bom'")
    if horas_formacao < horas_formacao_necessarias:
        requisitos.append(f"Faltam {horas_formacao_necessarias - horas_formacao:.1f} horas de formação")
    if escalão_atual in [2,3,4,5] and not observacao_aulas:
        requisitos.append("Necessita observação de aulas no escalão")
    if dias_totais < modulo_escalao:
        requisitos.append(f"Faltam {modulo_escalao - dias_totais} dias de serviço no escalão")

    if not requisitos:
        data_progressao = data_hoje
        mensagem = f"Pode progredir já ao {escalão_atual + 1}º escalão."
        dias_em_falta = 0
    else:
        dias_em_falta = max(modulo_escalao - dias_totais, 0)
        if dias_em_falta > 0:
            data_progressao = data_hoje.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=dias_em_falta)
            mensagem = (f"Prevê-se progressão ao {escalão_atual + 1}º escalão em {data_progressao.date()} "
                        f"se cumprir todos os requisitos.")
        else:
            data_progressao = data_hoje
            mensagem = f"Requisitos pendentes: " + "; ".join(requisitos)

    return {
        "escalão_atual": escalão_atual,
        "dias_no_escalao": dias_totais,
        "dias_em_falta": dias_em_falta,
        "proximo_escalão": escalão_atual + 1,
        "data_progressao": data_progressao.date(),
        "mensagem": mensagem,
        "requisitos_em_falta": requisitos,
        "remanescente_para_novo_escalão": max(dias_totais - modulo_escalao, 0) if not requisitos else 0
    }

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Progressão Docente", page_icon="🎓")
st.title("Calculadora de Progressão Docente")
st.write("Simule a sua próxima progressão de escalão segundo as regras RITS (2024-2027).")

with st.form("dados_professor"):
    st.header("Dados do Docente")
    data_entrada_escalao = st.date_input("Data de entrada no escalão atual", value=datetime(2022,9,1))
    escalão_atual = st.selectbox("Escalão atual", options=list(range(1,11)), index=3)
    dias_servico_efetivo = st.number_input("Dias de serviço efetivo desde a entrada no escalão", min_value=0, value=1200)
    horas_formacao = st.number_input("Horas de formação realizadas (até hoje)", min_value=0.0, value=25.0)
    avaliacao = st.selectbox("Avaliação de desempenho mais recente", options=["Excelente", "Muito Bom", "Bom", "Regular", "Insuficiente"], index=2)
    observacao_aulas = st.checkbox("Cumpriu observação de aulas (obrigatório em alguns escalões)?", value=True)
    acelerador_2023 = st.checkbox("Beneficiou de redução pelo acelerador em 2023/2024?", value=False)
    grau_academico = st.selectbox("Grau académico com redução", options=["Nenhum", "Mestre", "Doutor"], index=0)
    bonificacao_merito = st.selectbox("Bonificação de mérito", options=["Nenhuma", "Muito Bom", "Excelente"], index=0)
    submitted = st.form_submit_button("Calcular Progressão")

if submitted:
    resultado = calcular_proxima_progressao(
        data_entrada_escalao=datetime.combine(data_entrada_escalao, datetime.min.time()),
        escalão_atual=escalão_atual,
        dias_servico_efetivo=dias_servico_efetivo,
        horas_formacao=horas_formacao,
        avaliacao=avaliacao,
        observacao_aulas=observacao_aulas,
        acelerador_2023=acelerador_2023,
        grau_academico=None if grau_academico == "Nenhum" else grau_academico,
        bonificacao_merito=None if bonificacao_merito == "Nenhuma" else bonificacao_merito
    )

    st.success(resultado["mensagem"])
    st.write(f"**Data previsível de progressão:** {resultado['data_progressao']}")
    st.write(f"**Dias de serviço contabilizados:** {resultado['dias_no_escalao']}")
    if resultado["requisitos_em_falta"]:
        st.warning("Requisitos em falta: " + "; ".join(resultado["requisitos_em_falta"]))
    else:
        st.info(f"Remanescente para o novo escalão: {resultado['remanescente_para_novo_escalão']} dias")

st.markdown("---")
st.caption("App de demonstração. Confirme sempre os cálculos com a legislação em vigor.")