"""Cliente HTTP compartilhado pelos painéis Streamlit."""

import os

from dotenv import load_dotenv
import requests
import streamlit as st


def call_api(method, path, auth=None, **kwargs):
    load_dotenv()
    api = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        response = requests.request(method, api + path, auth=auth or st.session_state.get("auth"),
                                    timeout=180, **kwargs)
    except requests.RequestException:
        st.error("API indisponível. Confira se o servidor está iniciado.")
        return None
    if not response.ok:
        try:
            detail = response.json().get("detail", "Falha na solicitação.")
        except ValueError:
            detail = "Falha na solicitação."
        st.error(detail if isinstance(detail, str) else "Verifique os campos preenchidos.")
        return None
    return response.json()


def require_login(role):
    if "auth" not in st.session_state:
        with st.form("login"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")
        if submit:
            profile = call_api("GET", "/me", auth=(username, password))
            if profile and profile["role"] == role:
                st.session_state.auth = (username, password)
                st.rerun()
            elif profile:
                st.error("Esta conta não tem acesso a este painel.")
        st.stop()
    if st.sidebar.button("Sair"):
        st.session_state.clear()
        st.rerun()
