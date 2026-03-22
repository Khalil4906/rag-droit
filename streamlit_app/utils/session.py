import uuid
from datetime import datetime
import streamlit as st

KEY_SESSION_ID = "session_id"
KEY_MESSAGES = "messages"
KEY_PAGE = "current_page"


def _generate_session_id() -> str:
    now = datetime.now()
    short_uuid = str(uuid.uuid4())[:4]
    return (
        f"session_"
        f"{now.strftime('%Y%m%d_%H%M%S')}_"
        f"{short_uuid}"
    )


def get_session_id() -> str:
    if KEY_SESSION_ID not in st.session_state:
        st.session_state[KEY_SESSION_ID] = _generate_session_id()
    return st.session_state[KEY_SESSION_ID]


def set_session_id(session_id: str) -> None:
    st.session_state[KEY_SESSION_ID] = session_id
    st.session_state[KEY_MESSAGES] = []


def new_session() -> str:
    new_id = _generate_session_id()
    st.session_state[KEY_SESSION_ID] = new_id
    st.session_state[KEY_MESSAGES] = []
    return new_id


def get_messages() -> list[dict]:
    if KEY_MESSAGES not in st.session_state:
        st.session_state[KEY_MESSAGES] = []
    return st.session_state[KEY_MESSAGES]


def add_message(role: str, content: str) -> None:
    messages = get_messages()
    messages.append({
        "role": role,
        "content": content,
    })


def get_current_page() -> str:
    if KEY_PAGE not in st.session_state:
        st.session_state[KEY_PAGE] = "chat"
    return st.session_state[KEY_PAGE]


def set_current_page(page: str) -> None:
    st.session_state[KEY_PAGE] = page