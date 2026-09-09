"""Painel Streamlit que usa a API, sem acesso direto ao banco."""

import csv
from datetime import time
from io import StringIO
import streamlit as st

from ponto.ui import call_api, require_login

st.set_page_config(page_title="Ponto Facial — Administração", layout="wide")
st.title("Ponto Facial — Administração")
require_login("admin")

page = st.sidebar.radio("Menu", ["Cadastrar colaborador", "Registros"])
if page == "Cadastrar colaborador":
    with st.form("cadastro", clear_on_submit=False):
        name = st.text_input("Nome completo")
        username = st.text_input("Usuário do colaborador")
        password = st.text_input("Senha inicial (12 a 128 caracteres)", type="password")
        photo = st.file_uploader("Foto com um único rosto", type=["jpg", "jpeg", "png"])
        start = st.time_input("Horário de entrada", value=time(9, 0))
        tolerance = st.number_input("Tolerância em minutos", min_value=0, max_value=180, value=10)
        submit = st.form_submit_button("Cadastrar")
    if submit:
        if photo is None:
            st.error("Selecione a foto de referência.")
        else:
            result = call_api("POST", "/colaboradores", data={"nome": name, "usuario": username,
                              "senha": password, "horario": start.strftime("%H:%M"), "tolerancia": tolerance},
                              files={"foto": ("reference.jpg", photo.getvalue(), photo.type)})
            if result:
                st.success("Colaborador cadastrado.")
else:
    st.caption("Até 1.000 registros recentes. Horários em UTC, com fuso explícito.")
    rows = call_api("GET", "/registros", params={"limit": 1000})
    if rows:
        st.dataframe(rows, use_container_width=True)
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        # Evita fórmulas ao abrir texto controlado pelo usuário em planilhas.
        writer.writerows({key: ("'" + value if isinstance(value, str)
                                and value.lstrip().startswith(("=", "+", "-", "@")) else value)
                          for key, value in row.items()} for row in rows)
        st.download_button("Baixar CSV", output.getvalue().encode("utf-8-sig"), "registros.csv", "text/csv")
    elif rows is not None:
        st.info("Nenhum registro encontrado.")
