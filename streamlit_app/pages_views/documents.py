import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st
from streamlit_app.utils.api_client import api_client


def render() -> None:
    st.markdown("### 📄 Documents indexés")

    data = api_client.get_documents()

    if "error" in data:
        st.error(f"Erreur : {data['error']}")
        return

    documents = data.get("documents", [])

    if not documents:
        st.info("Aucun document indexé.")
    else:
        for doc in documents:
            col1, col2 = st.columns([5, 1])

            with col1:
                st.markdown(
                    f"**{doc['source']}**  \n"
                    f"🗂 {doc['chunk_count']} chunks · "
                    f"📄 {doc['page_count']} pages · "
                    f"📅 {doc['indexed_at'][:10]}",
                )

            with col2:
                if st.button("🗑️", key=f"del_{doc['doc_id']}"):
                    result = api_client.delete_document(doc["doc_id"])
                    if "error" in result:
                        st.error(f"Erreur : {result['error']}")
                    else:
                        st.success(f"{doc['source']} supprimé.")
                        st.rerun()

            st.divider()

    st.markdown("### ⬆️ Ajouter un document")

    uploaded = st.file_uploader(
        "PDF, Word, Markdown ou texte",
        type=["pdf", "docx", "md", "txt"],
    )

    if uploaded:
        if st.button("Indexer ce document", type="primary"):
            with st.spinner(f"Indexation de {uploaded.name}..."):
                result = api_client.upload_document(
                    file_bytes=uploaded.read(),
                    filename=uploaded.name,
                )

            if "error" in result:
                st.error(f"Erreur : {result['error']}")
            elif result.get("status") == "already_indexed":
                st.warning(f"{uploaded.name} est déjà indexé.")
            else:
                st.success(
                    f"{uploaded.name} indexé — "
                    f"{result['chunks_dense']} chunks."
                )
                st.rerun()