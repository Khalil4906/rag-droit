import os
import sys
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
load_dotenv()

_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
_TIMEOUT_CHAT = 120
_TIMEOUT_DEFAULT = 120


def _url(path: str) -> str:
    return f"{_BASE_URL}{path}"


def _handle_response(response: requests.Response) -> dict[str, Any]:
    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        try:
            detail = response.json().get("detail", "Erreur inconnue")
        except Exception:
            detail = response.text or "Erreur inconnue"
        return {"error": detail}
    except requests.exceptions.ConnectionError:
        return {
            "error": (
                "Impossible de contacter le serveur. "
                f"Vérifie que FastAPI tourne sur {_BASE_URL}."
            )
        }
    except requests.exceptions.Timeout:
        return {
            "error": (
                "Le serveur met trop de temps à répondre. "
                "Réessaie dans quelques instants."
            )
        }
    except Exception as e:
        return {"error": f"Erreur inattendue : {str(e)}"}


class APIClient:

    def send_message(
        self,
        session_id: str,
        message: str,
    ) -> dict[str, Any]:
        try:
            response = requests.post(
                _url("/api/v1/chat"),
                json={"session_id": session_id, "message": message},
                timeout=_TIMEOUT_CHAT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}

    def get_history(self, session_id: str) -> dict[str, Any]:
        try:
            response = requests.get(
                _url(f"/api/v1/history/{session_id}"),
                timeout=_TIMEOUT_DEFAULT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}

    def delete_history(self, session_id: str) -> dict[str, Any]:
        try:
            response = requests.delete(
                _url(f"/api/v1/history/{session_id}"),
                timeout=_TIMEOUT_DEFAULT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}

    def get_sessions(self) -> dict[str, Any]:
        try:
            response = requests.get(
                _url("/api/v1/sessions"),
                timeout=_TIMEOUT_DEFAULT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}

    def upload_document(
        self,
        file_bytes: bytes,
        filename: str,
    ) -> dict[str, Any]:
        try:
            response = requests.post(
                _url("/api/v1/ingest/file"),
                files={
                    "file": (filename, file_bytes, "application/octet-stream")
                },
                timeout=_TIMEOUT_CHAT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}

    def get_documents(self) -> dict[str, Any]:
        try:
            response = requests.get(
                _url("/api/v1/documents"),
                timeout=_TIMEOUT_DEFAULT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}

    def delete_document(self, doc_id: str) -> dict[str, Any]:
        try:
            response = requests.delete(
                _url(f"/api/v1/documents/{doc_id}"),
                timeout=_TIMEOUT_DEFAULT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}

    def get_config(self) -> dict[str, Any]:
        try:
            response = requests.get(
                _url("/api/v1/config"),
                timeout=_TIMEOUT_DEFAULT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}

    def update_config(
        self,
        system_prompt: str,
        rag_prompt: str,
    ) -> dict[str, Any]:
        try:
            response = requests.put(
                _url("/api/v1/config"),
                json={
                    "system_prompt": system_prompt,
                    "rag_prompt": rag_prompt,
                },
                timeout=_TIMEOUT_DEFAULT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}

    def reset_config(self) -> dict[str, Any]:
        try:
            response = requests.post(
                _url("/api/v1/config/reset"),
                timeout=_TIMEOUT_DEFAULT,
            )
            return _handle_response(response)
        except Exception as e:
            return {"error": str(e)}


api_client = APIClient()