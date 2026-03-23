import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from streamlit_app.utils.api_client import api_client


def render() -> None:
    st.markdown("### ⚙️ Configuration des prompts")

    config = api_client.get_config()

    if "error" in config:
        st.error(f"Erreur : {config['error']}")
        return

    st.markdown("**System prompt**")
    st.caption("Comportement global de l'agent — langue, ton, règles.")
    system_prompt = st.text_area(
        label="system_prompt",
        value=config.get("system_prompt", ""),
        height=250,
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("**RAG prompt**")
    st.caption("Doit contenir {context} et {question}.")
    rag_prompt = st.text_area(
        label="rag_prompt",
        value=config.get("rag_prompt", ""),
        height=200,
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, _ = st.columns([1, 1, 4])

    with col1:
        if st.button("💾 Sauvegarder", type="primary"):
            result = api_client.update_config(
                system_prompt=system_prompt,
                rag_prompt=rag_prompt,
            )
            if "error" in result:
                st.error(f"Erreur : {result['error']}")
            else:
                st.success("Prompts sauvegardés.")

    with col2:
        if st.button("↺ Réinitialiser"):
            result = api_client.reset_config()
            if "error" in result:
                st.error(f"Erreur : {result['error']}")
            else:
                st.success("Prompts réinitialisés.")
                st.rerun()