import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from streamlit_app.utils.api_client import api_client
from streamlit_app.utils.session import store_token


def render() -> None:
    st.markdown(
        """
        <div style='text-align:center;padding:60px 0 30px;'>
            <div style='font-size:56px;'>⚖️</div>
            <div style='font-size:26px;font-weight:600;
            color:#8b1a4a;margin:12px 0 4px;'>RAG Droit</div>
            <div style='font-size:14px;color:#c06080;'>
            Ton assistant juridique personnel</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            username = st.text_input(
                "Identifiant",
                placeholder="khalil",
            )
            password = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="••••••••",
            )
            submitted = st.form_submit_button(
                "Se connecter",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            if not username or not password:
                st.error("Remplis les deux champs.")
                return

            with st.spinner("Connexion..."):
                result = api_client.login(username, password)

            if "error" in result:
                st.error(result["error"])
                return

            store_token(
                token=result["access_token"],
                username=result["username"],
            )
            st.rerun()