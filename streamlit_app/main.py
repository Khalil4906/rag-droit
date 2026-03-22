import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import re

from streamlit_app.utils.api_client import api_client
from streamlit_app.utils.session import (
    get_session_id,
    set_session_id,
    new_session,
    get_messages,
    add_message,
    get_current_page,
    set_current_page,
)

st.set_page_config(
    page_title="RAG Droit",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stSidebar"] {
    background-color: #2d0a1f;
    border-right: 1px solid #5c1a3a;
}
[data-testid="stSidebar"] * { color: #f0d0e0 !important; }

[data-testid="stSidebar"] button p {
    font-weight: 600 !important;
    font-size: 13px !important;
}

.msg-human {
    display: flex;
    justify-content: flex-end;
    margin: 8px 0;
}
.msg-human .bubble {
    background: #8b1a4a;
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 70%;
    font-size: 15px;
    line-height: 1.5;
}
.msg-assistant {
    display: flex;
    justify-content: flex-start;
    margin: 8px 0;
}
.msg-assistant .bubble {
    background: #fdf0f5;
    color: #2d0a1f;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    max-width: 75%;
    font-size: 15px;
    line-height: 1.5;
}
.source-tag {
    font-size: 11px;
    color: #c06080;
    margin-top: 4px;
    margin-left: 4px;
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}
.source-pill {
    background: #fce8f0;
    color: #8b1a4a;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
}
[data-testid="stHorizontalBlock"] {
    gap: 8px !important;
    padding-top: 0 !important;
    margin-top: 0 !important;
}
[data-testid="stHorizontalBlock"] button {
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    min-width: 120px !important;
}
.block-container {
    padding-top: 1rem !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            "<h2 style='color:#f4a0c0;margin-bottom:20px;'>⚖️ RAG Droit</h2>",
            unsafe_allow_html=True,
        )

        if st.button("✏️ Nouveau chat", use_container_width=True):
            new_session()
            st.rerun()

        st.markdown(
            "<hr style='border-color:#5c1a3a;margin:16px 0;'>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<p style='font-size:12px;color:#c080a0;margin-bottom:8px;"
            "text-transform:uppercase;letter-spacing:1px;'>"
            "Conversations</p>",
            unsafe_allow_html=True,
        )

        sessions_data = api_client.get_sessions()

        if "error" in sessions_data:
            st.markdown(
                "<p style='font-size:12px;color:#a06080;'>"
                "Impossible de charger les sessions.</p>",
                unsafe_allow_html=True,
            )
            return

        sessions = sessions_data.get("sessions", [])

        if not sessions:
            st.markdown(
                "<p style='font-size:12px;color:#a06080;'>"
                "Aucune conversation.</p>",
                unsafe_allow_html=True,
            )
            return

        for session in sessions:
            sid = session["session_id"]
            count = session["message_count"]
            last = session["last_message_at"][:10]
            label = f"💬 {last} · {count} msg"

            col_session, col_del = st.columns([5, 1])

            with col_session:
                if st.button(
                    label,
                    key=f"session_{sid}",
                    use_container_width=True,
                ):
                    set_session_id(sid)
                    st.rerun()

            with col_del:
                if st.button("🗑️", key=f"del_{sid}"):
                    result = api_client.delete_history(sid)
                    if "error" not in result:
                        if get_session_id() == sid:
                            new_session()
                        st.rerun()


def render_navbar() -> str:
    current = get_current_page()
    col1, col2, col3, _ = st.columns([1.5, 1.5, 1.8, 4])

    with col1:
        if st.button(
            "💬 Chat",
            use_container_width=True,
            type="primary" if current == "chat" else "secondary",
        ):
            set_current_page("chat")
            st.rerun()

    with col2:
        if st.button(
            "📄 Documents",
            use_container_width=True,
            type="primary" if current == "documents" else "secondary",
        ):
            set_current_page("documents")
            st.rerun()

    with col3:
        if st.button(
            "⚙️ Configuration",
            use_container_width=True,
            type="primary" if current == "config" else "secondary",
        ):
            set_current_page("config")
            st.rerun()

    return current


def render_message(
    role: str,
    content: str,
    sources_used: bool = False,
    source_names: list[str] | None = None,
) -> None:
    if role == "human":
        st.markdown(
            f'<div class="msg-human"><div class="bubble">{content}</div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="msg-assistant"><div class="bubble">{content}</div></div>',
            unsafe_allow_html=True,
        )
        if sources_used and source_names:
            pills = "".join([
                f'<span class="source-pill">📄 {name}</span>'
                for name in source_names
            ])
            st.markdown(
                f'<div class="source-tag">{pills}</div>',
                unsafe_allow_html=True,
            )


def extract_sources(answer: str) -> list[str]:
    pattern = r'\[\d+\]\s+([^\s—]+\.[a-zA-Z]+)'
    matches = re.findall(pattern, answer)
    seen = set()
    sources = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            sources.append(m)
    return sources


def render_chat_page() -> None:
    session_id = get_session_id()
    messages = get_messages()

    if not messages:
        with st.spinner("Chargement..."):
            history_data = api_client.get_history(session_id)
            if "error" not in history_data:
                for msg in history_data.get("messages", []):
                    add_message(role=msg["role"], content=msg["content"])
                messages = get_messages()

    with st.container():
        if not messages:
            st.markdown(
                """
                <div style='text-align:center;padding:60px 0;'>
                    <div style='font-size:48px;margin-bottom:16px;'>⚖️</div>
                    <div style='font-size:20px;font-weight:500;color:#8b1a4a;
                    margin-bottom:8px;'>Bonjour ! Je suis ton assistant juridique.</div>
                    <div style='font-size:14px;color:#c06080;'>
                    Pose-moi une question sur tes cours de droit.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            for msg in messages:
                render_message(
                    role=msg["role"],
                    content=msg["content"],
                    sources_used=msg.get("sources_used", False),
                    source_names=msg.get("source_names", []),
                )

    if prompt := st.chat_input("Pose ta question sur tes cours de droit..."):
        add_message(role="human", content=prompt)
        render_message(role="human", content=prompt)

        with st.spinner("Recherche en cours..."):
            result = api_client.send_message(
                session_id=session_id,
                message=prompt,
            )

        if "error" in result:
            st.error(f"Erreur : {result['error']}")
            return

        answer = result.get("answer", "")
        sources_used = result.get("sources_used", False)
        source_names = extract_sources(answer) if sources_used else []

        messages = get_messages()
        messages.append({
            "role": "assistant",
            "content": answer,
            "sources_used": sources_used,
            "source_names": source_names,
        })

        render_message(
            role="assistant",
            content=answer,
            sources_used=sources_used,
            source_names=source_names,
        )

        st.rerun()


def render_documents_page() -> None:
    from streamlit_app.pages_views.documents import render as render_docs
    render_docs()


def render_config_page() -> None:
    from streamlit_app.pages_views.config import render as render_cfg
    render_cfg()


def main() -> None:
    render_sidebar()
    page = render_navbar()

    if page == "chat":
        render_chat_page()
    elif page == "documents":
        render_documents_page()
    elif page == "config":
        render_config_page()


main()