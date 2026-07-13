"""
Tests for POST /api/v1/scan/demo
Does NOT require Django/AI — uses only the in-memory DEMO_PROFILES dict.
"""
import pytest


VALID_PROFILES = ["combination_warm", "dry_cool", "oily_warm", "mature_neutral"]


class TestScanDemo:

    # ── Happy-path profiles ────────────────────────────────────────────────
    @pytest.mark.parametrize("profile_key", VALID_PROFILES)
    def test_returns_200_for_valid_profile(self, client, profile_key):
        r = client.post("/api/v1/scan/demo", json={"profile_key": profile_key})
        assert r.status_code == 200

    @pytest.mark.parametrize("profile_key", VALID_PROFILES)
    def test_response_contains_required_fields(self, client, profile_key):
        data = client.post("/api/v1/scan/demo", json={"profile_key": profile_key}).json()
        required = [
            "skin_tone", "undertone", "face_shape", "skin_type",
            "skin_age", "harmony_score", "hydration_score", "pigmentation_score",
            "acne_score", "aging_score", "elasticity_score",
            "hf_acne_severity", "hf_skin_type", "hf_undertone",
            "hf_acne_confidence", "hf_skin_type_confidence", "hf_undertone_confidence",
            "facial_zones", "visible_concerns",
            "is_demo",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_is_demo_flag_is_true(self, client):
        data = client.post("/api/v1/scan/demo", json={"profile_key": "oily_warm"}).json()
        assert data["is_demo"] is True

    def test_gender_is_echoed(self, client):
        data = client.post("/api/v1/scan/demo", json={"profile_key": "dry_cool", "gender": "male"}).json()
        assert data["gender"] == "male"

    def test_gender_defaults_to_female(self, client):
        data = client.post("/api/v1/scan/demo", json={"profile_key": "dry_cool"}).json()
        assert data["gender"] == "female"

    # ── Fallback for unknown profile ──────────────────────────────────────
    def test_unknown_profile_key_falls_back_to_combination_warm(self, client):
        data = client.post("/api/v1/scan/demo", json={"profile_key": "nonexistent_profile"}).json()
        assert data["skin_type"] == "combination"   # combination_warm profile
        assert data["undertone"] == "warm"

    def test_missing_profile_key_falls_back(self, client):
        data = client.post("/api/v1/scan/demo", json={}).json()
        assert data["is_demo"] is True

    # ── Profile-specific value assertions ─────────────────────────────────
    def test_dry_cool_has_low_hydration(self, client):
        data = client.post("/api/v1/scan/demo", json={"profile_key": "dry_cool"}).json()
        assert data["hydration_score"] < 50

    def test_oily_warm_has_high_acne_score(self, client):
        data = client.post("/api/v1/scan/demo", json={"profile_key": "oily_warm"}).json()
        assert data["acne_score"] >= 60

    def test_mature_neutral_has_high_aging_score(self, client):
        data = client.post("/api/v1/scan/demo", json={"profile_key": "mature_neutral"}).json()
        assert data["aging_score"] >= 50

    def test_facial_zones_is_dict(self, client):
        data = client.post("/api/v1/scan/demo", json={"profile_key": "combination_warm"}).json()
        assert isinstance(data["facial_zones"], dict)
        assert "forehead" in data["facial_zones"]

    def test_visible_concerns_is_list(self, client):
        data = client.post("/api/v1/scan/demo", json={"profile_key": "combination_warm"}).json()
        assert isinstance(data["visible_concerns"], list)
