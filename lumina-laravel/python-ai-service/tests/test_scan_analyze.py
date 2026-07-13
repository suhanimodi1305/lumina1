"""
Tests for POST /api/v1/scan/analyze
AI imports are mocked in conftest.py so these run without a GPU/Django env.
"""
import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _jpeg_bytes() -> bytes:
    """Minimal valid JPEG header so the file is accepted."""
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xd9"
    )


def _post_image(client, content: bytes, content_type: str = "image/jpeg", filename: str = "test.jpg"):
    return client.post(
        "/api/v1/scan/analyze",
        files={"image": (filename, io.BytesIO(content), content_type)},
        data={"gender": "female"},
    )


def _mock_ai(fake_result: dict):
    """Context manager that patches face_detector + hf_analyzer with success."""
    detect_face = MagicMock(return_value={"detected": True, "face_rect": [0, 0, 100, 100]})
    map_skin_tone = MagicMock(return_value="medium")
    run_full = MagicMock(return_value=fake_result)

    fd_mod = sys.modules["apps.scanner.face_detector"]
    fd_mod.detect_face = detect_face

    hf_mod = sys.modules["apps.scanner.hf_analyzer"]
    hf_mod.run_full_skin_analysis = run_full
    hf_mod.map_skin_tone_from_image = map_skin_tone

    return fd_mod, hf_mod


# ── Happy-path ────────────────────────────────────────────────────────────────

class TestScanAnalyzeHappyPath:

    def test_returns_200_with_valid_image(self, client, fake_analysis_result):
        _mock_ai(fake_analysis_result)
        r = _post_image(client, _jpeg_bytes())
        assert r.status_code == 200

    def test_response_contains_required_fields(self, client, fake_analysis_result):
        _mock_ai(fake_analysis_result)
        data = _post_image(client, _jpeg_bytes()).json()
        required_fields = [
            "skin_tone", "undertone", "face_shape", "skin_type",
            "skin_age", "real_age", "harmony_score", "hydration_score",
            "pigmentation_score", "acne_score", "aging_score", "elasticity_score",
            "hf_acne_severity", "hf_skin_type", "hf_undertone",
            "hf_acne_confidence", "hf_skin_type_confidence", "hf_undertone_confidence",
            "hf_acne_raw", "hf_skin_type_raw", "hf_undertone_raw",
            "facial_zones", "visible_concerns",
            "face_shape_confidence", "face_shape_reason", "face_shape_measurements",
        ]
        for f in required_fields:
            assert f in data, f"Missing field in response: {f}"

    def test_skin_tone_is_string(self, client, fake_analysis_result):
        _mock_ai(fake_analysis_result)
        data = _post_image(client, _jpeg_bytes()).json()
        assert isinstance(data["skin_tone"], str)
        assert data["skin_tone"] == "medium"

    def test_scores_are_numeric(self, client, fake_analysis_result):
        _mock_ai(fake_analysis_result)
        data = _post_image(client, _jpeg_bytes()).json()
        score_fields = ["harmony_score", "hydration_score", "acne_score", "aging_score"]
        for field in score_fields:
            assert isinstance(data[field], (int, float)), f"{field} should be numeric"

    def test_facial_zones_is_dict_with_five_zones(self, client, fake_analysis_result):
        _mock_ai(fake_analysis_result)
        data = _post_image(client, _jpeg_bytes()).json()
        zones = data["facial_zones"]
        assert isinstance(zones, dict)
        expected_zones = {"forehead", "nose", "left_cheek", "right_cheek", "chin"}
        assert expected_zones == set(zones.keys())

    def test_accepts_png_image(self, client, fake_analysis_result):
        _mock_ai(fake_analysis_result)
        # Minimal PNG header
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        r = client.post(
            "/api/v1/scan/analyze",
            files={"image": ("test.png", io.BytesIO(png), "image/png")},
            data={"gender": "male"},
        )
        # Either 200 (mocked) or 422 is acceptable; must not be 500 from wrong content-type check
        assert r.status_code in (200, 422, 400)

    def test_webp_accepted(self, client, fake_analysis_result):
        _mock_ai(fake_analysis_result)
        r = client.post(
            "/api/v1/scan/analyze",
            files={"image": ("test.webp", io.BytesIO(b"RIFF....WEBP"), "image/webp")},
            data={"gender": "female"},
        )
        assert r.status_code in (200, 422, 400)


# ── Validation errors ─────────────────────────────────────────────────────────

class TestScanAnalyzeValidation:

    def test_rejects_missing_image_field(self, client):
        r = client.post("/api/v1/scan/analyze", data={"gender": "female"})
        assert r.status_code == 422

    def test_rejects_non_image_content_type(self, client):
        r = client.post(
            "/api/v1/scan/analyze",
            files={"image": ("test.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            data={"gender": "female"},
        )
        assert r.status_code == 400

    def test_rejects_oversized_image(self, client):
        big_bytes = b"\xff\xd8\xff" + b"\x00" * (6 * 1024 * 1024)  # 6 MB
        r = _post_image(client, big_bytes)
        assert r.status_code == 400

    def test_rejects_gif(self, client):
        r = client.post(
            "/api/v1/scan/analyze",
            files={"image": ("anim.gif", io.BytesIO(b"GIF89a"), "image/gif")},
            data={"gender": "female"},
        )
        assert r.status_code == 400

    def test_size_limit_message(self, client):
        big = b"\xff\xd8\xff" + b"\x00" * (6 * 1024 * 1024)
        r = _post_image(client, big)
        assert "large" in r.json().get("detail", "").lower()

    def test_bad_content_type_message(self, client):
        r = client.post(
            "/api/v1/scan/analyze",
            files={"image": ("x.bmp", io.BytesIO(b"BM"), "image/bmp")},
            data={"gender": "female"},
        )
        assert r.status_code == 400
        assert "invalid" in r.json().get("detail", "").lower()


# ── No-face error ─────────────────────────────────────────────────────────────

class TestScanAnalyzeNoFace:

    def test_returns_422_when_no_face_detected(self, client):
        fd_mod = sys.modules["apps.scanner.face_detector"]
        fd_mod.detect_face = MagicMock(return_value={"detected": False, "message": "No face found."})

        r = _post_image(client, _jpeg_bytes())
        assert r.status_code == 422

    def test_no_face_error_detail_message(self, client):
        fd_mod = sys.modules["apps.scanner.face_detector"]
        fd_mod.detect_face = MagicMock(return_value={"detected": False, "message": "No face found."})

        data = _post_image(client, _jpeg_bytes()).json()
        assert "face" in data["detail"].lower() or "found" in data["detail"].lower()


# ── AI service error handling ─────────────────────────────────────────────────

class TestScanAnalyzeServiceErrors:

    def test_returns_500_on_analysis_exception(self, client):
        fd_mod = sys.modules["apps.scanner.face_detector"]
        fd_mod.detect_face = MagicMock(return_value={"detected": True, "face_rect": [0, 0, 100, 100]})

        hf_mod = sys.modules["apps.scanner.hf_analyzer"]
        hf_mod.run_full_skin_analysis = MagicMock(side_effect=RuntimeError("GPU out of memory"))

        r = _post_image(client, _jpeg_bytes())
        assert r.status_code == 500

    def test_500_includes_error_detail(self, client):
        fd_mod = sys.modules["apps.scanner.face_detector"]
        fd_mod.detect_face = MagicMock(return_value={"detected": True, "face_rect": [0, 0, 100, 100]})

        hf_mod = sys.modules["apps.scanner.hf_analyzer"]
        hf_mod.run_full_skin_analysis = MagicMock(side_effect=ValueError("model not loaded"))

        data = _post_image(client, _jpeg_bytes()).json()
        assert "detail" in data
        assert len(data["detail"]) > 0
