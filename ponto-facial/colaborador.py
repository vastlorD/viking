"""Captura de selfie e localização no navegador do colaborador."""

import time

import streamlit as st
from streamlit_js_eval import get_geolocation

from ponto.ui import call_api, require_login

st.set_page_config(page_title="Ponto Facial — Colaborador")
st.title("Registrar presença")
require_login("employee")
st.write("Autorize a localização no navegador e tire uma selfie com o rosto visível.")
location = get_geolocation()
selfie = st.camera_input("Selfie para este registro")

if location and "error" in location:
    st.warning("Localização indisponível. Confira a permissão do navegador e atualize a página.")

if st.button("Registrar ponto"):
    if not location or "coords" not in location:
        st.error("Aguarde a localização e permita o acesso no navegador.")
    elif not selfie:
        st.error("Tire a selfie antes de registrar.")
    elif not isinstance(location.get("timestamp"), (int, float)) or not 0 <= time.time() - location["timestamp"] / 1000 <= 120:
        st.error("Atualize a página para obter uma localização recente e tire outra selfie.")
    else:
        coords = location["coords"]
        with st.spinner("Verificando presença..."):
            result = call_api("POST", "/bater-ponto",
                              data={"lat": coords["latitude"], "lon": coords["longitude"]},
                              files={"selfie": ("selfie.jpg", selfie.getvalue(), "image/jpeg")})
        if result:
            st.success("Presença registrada.")
            st.write(result)

if st.button("Consultar meu extrato"):
    rows = call_api("GET", "/meu-extrato")
    if rows:
        st.dataframe(rows, use_container_width=True)
    elif rows is not None:
        st.info("Nenhum registro encontrado.")
