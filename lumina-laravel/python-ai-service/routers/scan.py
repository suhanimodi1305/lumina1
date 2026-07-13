"""
Scan router — wraps existing hf_analyzer.py and face_detector.py unchanged.
"""
import json
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

# Add Django project to path so we can import existing AI modules
DJANGO_ROOT = Path(__file__).resolve().parents[3]
if str(DJANGO_ROOT) not in sys.path:
    sys.path.insert(0, str(DJANGO_ROOT))

router = APIRouter()

# ── Demo profiles (mirrors Django DEMO_PROFILES exactly) ──────
DEMO_PROFILES = {
    "combination_warm": {
        "skin_tone": "medium", "undertone": "warm", "face_shape": "oval",
        "skin_type": "combination", "skin_age": 26, "real_age": 25,
        "harmony_score": 74, "hydration_score": 65, "pigmentation_score": 48,
        "acne_score": 30, "aging_score": 20, "elasticity_score": 65,
        "hf_acne_severity": "mild", "hf_skin_type": "combination", "hf_undertone": "warm",
        "hf_acne_confidence": 85.0, "hf_skin_type_confidence": 78.0, "hf_undertone_confidence": 72.0,
        "hf_acne_raw": "{}", "hf_skin_type_raw": "{}", "hf_undertone_raw": "{}",
        "facial_zones": {"forehead":"mild","nose":"moderate","left_cheek":"mild","right_cheek":"mild","chin":"moderate"},
        "visible_concerns": ["acne", "dark spots", "blackheads"],
        "face_shape_confidence": 88.0, "face_shape_reason": "Demo profile", "face_shape_measurements": {},
    },
    "dry_cool": {
        "skin_tone": "fair", "undertone": "cool", "face_shape": "heart",
        "skin_type": "dry", "skin_age": 29, "real_age": 28,
        "harmony_score": 68, "hydration_score": 40, "pigmentation_score": 30,
        "acne_score": 10, "aging_score": 35, "elasticity_score": 55,
        "hf_acne_severity": "none", "hf_skin_type": "dry", "hf_undertone": "cool",
        "hf_acne_confidence": 92.0, "hf_skin_type_confidence": 88.0, "hf_undertone_confidence": 81.0,
        "hf_acne_raw": "{}", "hf_skin_type_raw": "{}", "hf_undertone_raw": "{}",
        "facial_zones": {"forehead":"none","nose":"none","left_cheek":"none","right_cheek":"none","chin":"none"},
        "visible_concerns": ["dryness", "fine lines"],
        "face_shape_confidence": 82.0, "face_shape_reason": "Demo profile", "face_shape_measurements": {},
    },
    "oily_warm": {
        "skin_tone": "tan", "undertone": "warm", "face_shape": "round",
        "skin_type": "oily", "skin_age": 23, "real_age": 22,
        "harmony_score": 78, "hydration_score": 75, "pigmentation_score": 55,
        "acne_score": 65, "aging_score": 10, "elasticity_score": 70,
        "hf_acne_severity": "moderate", "hf_skin_type": "oily", "hf_undertone": "warm",
        "hf_acne_confidence": 89.0, "hf_skin_type_confidence": 91.0, "hf_undertone_confidence": 76.0,
        "hf_acne_raw": "{}", "hf_skin_type_raw": "{}", "hf_undertone_raw": "{}",
        "facial_zones": {"forehead":"severe","nose":"severe","left_cheek":"moderate","right_cheek":"moderate","chin":"moderate"},
        "visible_concerns": ["acne", "oiliness", "large pores"],
        "face_shape_confidence": 79.0, "face_shape_reason": "Demo profile", "face_shape_measurements": {},
    },
    "mature_neutral": {
        "skin_tone": "light", "undertone": "neutral", "face_shape": "square",
        "skin_type": "normal", "skin_age": 38, "real_age": 37,
        "harmony_score": 65, "hydration_score": 55, "pigmentation_score": 60,
        "acne_score": 15, "aging_score": 55, "elasticity_score": 50,
        "hf_acne_severity": "none", "hf_skin_type": "normal", "hf_undertone": "neutral",
        "hf_acne_confidence": 87.0, "hf_skin_type_confidence": 83.0, "hf_undertone_confidence": 79.0,
        "hf_acne_raw": "{}", "hf_skin_type_raw": "{}", "hf_undertone_raw": "{}",
        "facial_zones": {"forehead":"none","nose":"none","left_cheek":"none","right_cheek":"none","chin":"none"},
        "visible_concerns": ["fine lines", "dullness"],
        "face_shape_confidence": 85.0, "face_shape_reason": "Demo profile", "face_shape_measurements": {},
    },
}


@router.post("/analyze")
async def analyze_scan(
    image: UploadFile = File(...),
    gender: str = Form("female"),
):
    """
    Full skin analysis using existing Python AI modules.
    Imports hf_analyzer + face_detector from Django apps/scanner/.
    """
    import tempfile, os

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if image.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid image type. Use JPEG, PNG, or WebP.")

    contents = await image.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Max 5MB.")

    # Write to temp file so existing OpenCV code can process it
    suffix = Path(image.filename or "scan.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        # Import existing AI modules (unchanged from Django project)
        from apps.scanner.face_detector import detect_face
        from apps.scanner.hf_analyzer import map_skin_tone_from_image, run_full_skin_analysis

        face_result = detect_face(tmp_path)
        if not face_result["detected"]:
            raise HTTPException(status_code=422, detail=face_result.get("message", "No face detected."))

        analysis = run_full_skin_analysis(tmp_path, face_result["face_rect"])
        skin_tone = analysis.get("skin_tone_from_vision") or map_skin_tone_from_image(tmp_path, face_result["face_rect"])

        # Enrich with face shape data
        try:
            raw_data = json.loads(analysis.get("hf_acne_raw", "{}") or "{}")
        except Exception:
            raw_data = {}
        raw_data["face_shape_confidence"]  = analysis.get("face_shape_confidence", 0)
        raw_data["face_shape_reason"]       = analysis.get("face_shape_reason", "")
        raw_data["face_shape_measurements"] = analysis.get("face_shape_measurements", {})

        return {
            "skin_tone":               skin_tone,
            "undertone":               analysis["undertone"],
            "face_shape":              analysis.get("face_shape") or "oval",
            "skin_type":               analysis["skin_type"],
            "skin_age":                25 + (analysis["aging_score"] // 4),
            "real_age":                25,
            "harmony_score":           analysis["harmony_score"],
            "hydration_score":         analysis["hydration_score"],
            "pigmentation_score":      analysis["pigmentation_score"],
            "acne_score":              analysis["acne_score"],
            "aging_score":             analysis["aging_score"],
            "elasticity_score":        analysis["elasticity_score"],
            "hf_acne_severity":        analysis["hf_acne_severity"],
            "hf_skin_type":            analysis["hf_skin_type"],
            "hf_undertone":            analysis["hf_undertone"],
            "hf_acne_confidence":      analysis.get("hf_acne_confidence") or 0.0,
            "hf_skin_type_confidence": analysis.get("hf_skin_type_confidence") or 0.0,
            "hf_undertone_confidence": analysis.get("hf_undertone_confidence") or 0.0,
            "hf_acne_raw":             json.dumps(raw_data),
            "hf_skin_type_raw":        analysis.get("hf_skin_type_raw", ""),
            "hf_undertone_raw":        analysis.get("hf_undertone_raw", ""),
            "facial_zones":            analysis.get("facial_zones", {}),
            "visible_concerns":        analysis.get("visible_concerns", []),
            "face_shape_confidence":   analysis.get("face_shape_confidence", 0),
            "face_shape_reason":       analysis.get("face_shape_reason", ""),
            "face_shape_measurements": analysis.get("face_shape_measurements", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


@router.post("/demo")
async def scan_demo(body: dict):
    """Return a pre-built demo scan profile."""
    profile_key = body.get("profile_key", "combination_warm")
    gender      = body.get("gender", "female")

    if profile_key not in DEMO_PROFILES:
        profile_key = "combination_warm"

    profile = DEMO_PROFILES[profile_key].copy()
    profile["gender"]  = gender
    profile["is_demo"] = True
    return profile
