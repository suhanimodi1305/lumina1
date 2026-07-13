"""
Shared pytest fixtures for Lumina AI Service tests.
All Django/AI imports are mocked so tests run without a Django environment.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ── Stub Django/AI modules so routers can be imported ────────────────────────
def _make_module(name: str) -> MagicMock:
    m = MagicMock()
    m.__name__ = name
    return m


# Build a fake module tree for `apps.*`
_apps = _make_module("apps")
_apps_scanner = _make_module("apps.scanner")
_apps_scanner_face_detector = _make_module("apps.scanner.face_detector")
_apps_scanner_hf_analyzer = _make_module("apps.scanner.hf_analyzer")
_apps_chat = _make_module("apps.chat")
_apps_chat_ai_service = _make_module("apps.chat.ai_service")

sys.modules.setdefault("apps", _apps)
sys.modules.setdefault("apps.scanner", _apps_scanner)
sys.modules.setdefault("apps.scanner.face_detector", _apps_scanner_face_detector)
sys.modules.setdefault("apps.scanner.hf_analyzer", _apps_scanner_hf_analyzer)
sys.modules.setdefault("apps.chat", _apps_chat)
sys.modules.setdefault("apps.chat.ai_service", _apps_chat_ai_service)


# ── FastAPI test client ───────────────────────────────────────────────────────
from fastapi.testclient import TestClient  # noqa: E402 (after sys.modules setup)
from main import app, AI_SERVICE_TOKEN      # noqa: E402


@pytest.fixture(scope="session")
def client():
    """Unauthenticated test client (token not configured)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers():
    """Bearer token headers matching AI_SERVICE_TOKEN env var."""
    import os
    token = os.getenv("AI_SERVICE_TOKEN", "test-secret-token")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def fake_analysis_result() -> dict:
    return {
        "skin_tone": "medium",
        "undertone": "warm",
        "face_shape": "oval",
        "skin_type": "combination",
        "skin_age": 26,
        "real_age": 25,
        "harmony_score": 74,
        "hydration_score": 65,
        "pigmentation_score": 48,
        "acne_score": 30,
        "aging_score": 20,
        "elasticity_score": 65,
        "hf_acne_severity": "mild",
        "hf_skin_type": "combination",
        "hf_undertone": "warm",
        "hf_acne_confidence": 85.0,
        "hf_skin_type_confidence": 78.0,
        "hf_undertone_confidence": 72.0,
        "hf_acne_raw": "{}",
        "hf_skin_type_raw": "{}",
        "hf_undertone_raw": "{}",
        "facial_zones": {
            "forehead": "mild", "nose": "moderate",
            "left_cheek": "mild", "right_cheek": "mild", "chin": "moderate",
        },
        "visible_concerns": ["acne", "dark spots"],
        "face_shape_confidence": 88.0,
        "face_shape_reason": "Oval contour",
        "face_shape_measurements": {"width": 120, "length": 150},
    }


@pytest.fixture()
def fake_chat_response() -> dict:
    return {
        "reply": "Based on your skin type, I recommend a gentle cleanser. [PRODUCT:CLN-001:Gentle Foam Cleanser]",
        "product_tags": [{"sku": "CLN-001", "name": "Gentle Foam Cleanser"}],
    }
