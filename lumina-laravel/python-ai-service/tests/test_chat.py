"""
Tests for:
  POST /api/v1/chat/message
  POST /api/v1/chat/analyze-photo
AI imports are mocked in conftest.py.
"""
import base64
import sys
from unittest.mock import MagicMock

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mock_chat_ai(reply: str = "Here is my recommendation. [PRODUCT:CLN-001:Foam Cleanser]"):
    ai_mod = sys.modules["apps.chat.ai_service"]
    ai_mod.get_ai_response = MagicMock(return_value=reply)
    ai_mod.parse_product_tags = MagicMock(return_value=[{"sku": "CLN-001", "name": "Foam Cleanser"}])
    return ai_mod


def _minimal_history() -> list:
    return [
        {"role": "user", "content": "What routine do you recommend for oily skin?"}
    ]


# ── /chat/message happy path ──────────────────────────────────────────────────

class TestChatMessage:

    def test_returns_200(self, client, fake_chat_response):
        _mock_chat_ai(fake_chat_response["reply"])
        r = client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
            "scan_context": None,
            "mode": "doctor",
            "user_tier": "normal",
        })
        assert r.status_code == 200

    def test_response_has_reply_and_product_tags(self, client, fake_chat_response):
        _mock_chat_ai(fake_chat_response["reply"])
        data = client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
        }).json()
        assert "reply" in data
        assert "product_tags" in data

    def test_reply_is_string(self, client):
        _mock_chat_ai("A plain reply without tags.")
        data = client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
        }).json()
        assert isinstance(data["reply"], str)
        assert len(data["reply"]) > 0

    def test_product_tags_is_list(self, client, fake_chat_response):
        _mock_chat_ai(fake_chat_response["reply"])
        data = client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
        }).json()
        assert isinstance(data["product_tags"], list)

    def test_mode_doctor_accepted(self, client):
        _mock_chat_ai("Doctor mode reply.")
        r = client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
            "mode": "doctor",
        })
        assert r.status_code == 200

    def test_mode_makeup_accepted(self, client):
        _mock_chat_ai("Makeup mode reply.")
        r = client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
            "mode": "makeup",
        })
        assert r.status_code == 200

    def test_mode_kbeauty_accepted(self, client):
        _mock_chat_ai("K-beauty mode reply.")
        r = client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
            "mode": "kbeauty",
        })
        assert r.status_code == 200

    def test_vip_tier_accepted(self, client):
        _mock_chat_ai("VIP reply.")
        r = client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
            "user_tier": "vip",
        })
        assert r.status_code == 200

    def test_scan_context_is_passed_through(self, client):
        ai_mod = _mock_chat_ai("Reply with context.")
        scan_ctx = {"skin_type": "oily", "undertone": "warm", "acne_score": 65}

        client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
            "scan_context": scan_ctx,
        })
        ai_mod.get_ai_response.assert_called_once()
        call_args = ai_mod.get_ai_response.call_args
        # The router uses keyword args: get_ai_response(conversation_history=..., scan_context=...)
        passed_ctx = call_args.kwargs.get("scan_context")
        if passed_ctx is None and len(call_args.args) > 1:
            passed_ctx = call_args.args[1]
        assert passed_ctx is not None

    def test_empty_product_tags_when_no_tag_in_reply(self, client):
        ai_mod = sys.modules["apps.chat.ai_service"]
        ai_mod.get_ai_response = MagicMock(return_value="No product recommendations today.")
        ai_mod.parse_product_tags = MagicMock(return_value=[])

        data = client.post("/api/v1/chat/message", json={
            "history": _minimal_history(),
        }).json()
        assert data["product_tags"] == []

    def test_multi_message_history_accepted(self, client):
        _mock_chat_ai("Multi-turn reply.")
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi, how can I help?"},
            {"role": "user", "content": "I have dry skin."},
        ]
        r = client.post("/api/v1/chat/message", json={"history": history})
        assert r.status_code == 200

    def test_returns_503_on_ai_exception(self, client):
        ai_mod = sys.modules["apps.chat.ai_service"]
        ai_mod.get_ai_response = MagicMock(side_effect=ConnectionError("Groq API unreachable"))

        r = client.post("/api/v1/chat/message", json={"history": _minimal_history()})
        assert r.status_code == 500


# ── /chat/message validation ──────────────────────────────────────────────────

class TestChatMessageValidation:

    def test_missing_history_field_returns_422(self, client):
        r = client.post("/api/v1/chat/message", json={"mode": "doctor"})
        assert r.status_code == 422

    def test_history_must_be_list(self, client):
        r = client.post("/api/v1/chat/message", json={"history": "not a list"})
        assert r.status_code == 422

    def test_empty_history_accepted(self, client):
        _mock_chat_ai("Opening greeting.")
        r = client.post("/api/v1/chat/message", json={"history": []})
        assert r.status_code == 200


# ── /chat/analyze-photo ───────────────────────────────────────────────────────

class TestChatAnalyzePhoto:

    def _b64_image(self) -> str:
        return base64.b64encode(b"\xff\xd8\xff\xe0" + b"\x00" * 20).decode()

    def test_returns_200_with_valid_payload(self, client):
        _mock_chat_ai("Your skin looks healthy.")
        r = client.post("/api/v1/chat/analyze-photo", json={
            "history": _minimal_history(),
            "image": self._b64_image(),
            "mime_type": "image/jpeg",
        })
        assert r.status_code == 200

    def test_response_has_reply_and_product_tags(self, client):
        _mock_chat_ai("Photo analysis reply. [PRODUCT:SRM-002:Serum]")
        data = client.post("/api/v1/chat/analyze-photo", json={
            "history": _minimal_history(),
            "image": self._b64_image(),
        }).json()
        assert "reply" in data
        assert "product_tags" in data

    def test_default_mime_type_is_jpeg(self, client):
        """Omitting mime_type should not cause a 422."""
        _mock_chat_ai("Reply.")
        r = client.post("/api/v1/chat/analyze-photo", json={
            "history": _minimal_history(),
            "image": self._b64_image(),
        })
        assert r.status_code == 200

    def test_missing_image_returns_422(self, client):
        r = client.post("/api/v1/chat/analyze-photo", json={
            "history": _minimal_history(),
        })
        assert r.status_code == 422

    def test_missing_history_returns_422(self, client):
        r = client.post("/api/v1/chat/analyze-photo", json={
            "image": self._b64_image(),
        })
        assert r.status_code == 422

    def test_mode_is_forwarded_to_ai(self, client):
        ai_mod = _mock_chat_ai("Mode-forwarded reply.")
        client.post("/api/v1/chat/analyze-photo", json={
            "history": _minimal_history(),
            "image": self._b64_image(),
            "mode": "makeup",
        })
        ai_mod.get_ai_response.assert_called_once()

    def test_returns_500_on_ai_error(self, client):
        ai_mod = sys.modules["apps.chat.ai_service"]
        ai_mod.get_ai_response = MagicMock(side_effect=RuntimeError("model error"))

        r = client.post("/api/v1/chat/analyze-photo", json={
            "history": _minimal_history(),
            "image": self._b64_image(),
        })
        assert r.status_code == 500
