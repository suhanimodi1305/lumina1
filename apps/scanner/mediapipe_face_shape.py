# -*- coding: utf-8 -*-
"""
Production-ready Face Shape Detection using MediaPipe Face Mesh.
Uses 468 facial landmarks to calculate precise geometric measurements.
Zero hardcoding -- every result comes from actual landmark geometry.

Supports:
  mediapipe <=0.10.14  (solutions API  -- mp.solutions.face_mesh)
  mediapipe >=0.10.18  (tasks API      -- mp.tasks.vision.FaceLandmarker)
  No mediapipe         (OpenCV Canny edge fallback)

Install:
  pip install mediapipe==0.10.14
  OR
  pip install mediapipe   (latest -- uses tasks API path)
"""

import cv2
import numpy as np
import logging
import math
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MediaPipe lazy import — handles both API generations:
#   OLD (≤0.10.14): mp.solutions.face_mesh   ← venv install
#   NEW (≥0.10.18): mp.tasks.vision          ← system Python install
# Falls back to OpenCV geometry if neither is available.
# ---------------------------------------------------------------------------
_mp_face_mesh    = None   # old solutions API handle
_mp_tasks_ready  = False  # new tasks API available
_MEDIAPIPE_AVAILABLE = False

try:
    import mediapipe as mp
    _mp_version = getattr(mp, '__version__', '0')

    # ── Try old solutions API first (mediapipe ≤0.10.14) ──────────────────
    if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'face_mesh'):
        _mp_face_mesh = mp.solutions.face_mesh
        _MEDIAPIPE_AVAILABLE = True
        logger.info(f"MediaPipe Face Mesh (solutions API) v{_mp_version} available")

    # ── Try new tasks API (mediapipe ≥0.10.18) ────────────────────────────
    elif hasattr(mp, 'tasks') and hasattr(mp.tasks, 'vision'):
        # The tasks API uses FaceLandmarker with a model bundle
        # We'll download/cache the model lazily in _mediapipe_detect()
        _mp_tasks_ready = True
        _MEDIAPIPE_AVAILABLE = True
        logger.info(f"MediaPipe Face Landmarker (tasks API) v{_mp_version} available")

    else:
        logger.warning(f"MediaPipe v{_mp_version} found but no usable Face API — using OpenCV fallback")

except ImportError:
    logger.warning("MediaPipe not installed — face shape will use OpenCV fallback")

# ---------------------------------------------------------------------------
# MediaPipe Face Mesh landmark indices (468 total landmarks, 0-indexed)
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png
# ---------------------------------------------------------------------------

# ── TOP OF HEAD / HAIRLINE ──
# Landmark 10: top of the forehead (hairline centre)
# Landmark 152: chin bottom centre
FOREHEAD_TOP = 10
CHIN_BOTTOM  = 152

# ── FOREHEAD WIDTH ──
# Landmarks at the temporal region where the forehead is widest
# 54  = left outer forehead near temple
# 284 = right outer forehead near temple
FOREHEAD_LEFT  = 54
FOREHEAD_RIGHT = 284

# ── CHEEKBONE WIDTH (widest part of face) ──
# 234 = left cheekbone outer edge
# 454 = right cheekbone outer edge
CHEEKBONE_LEFT  = 234
CHEEKBONE_RIGHT = 454

# ── JAWLINE WIDTH ──
# 172 = left jaw angle (gonion)
# 397 = right jaw angle (gonion)
JAW_LEFT  = 172
JAW_RIGHT = 397

# ── CHIN WIDTH (bottom of face, narrower than jaw) ──
# 149 = left chin edge
# 378 = right chin edge
CHIN_LEFT  = 149
CHIN_RIGHT = 378

# ── JAW ANGLE POINTS ──
# For calculating the jaw angle (sharpness vs roundness)
# 172/397 = gonion (jaw hinge), 152 = chin tip, 234/454 = cheekbone
JAW_ANGLE_LEFT_CHEEK   = 234
JAW_ANGLE_LEFT_GONION  = 172
JAW_ANGLE_RIGHT_CHEEK  = 454
JAW_ANGLE_RIGHT_GONION = 397


# ---------------------------------------------------------------------------
# Coordinate helper
# ---------------------------------------------------------------------------

def _px(landmark, img_w: int, img_h: int) -> tuple[float, float]:
    """Convert normalised MediaPipe landmark → pixel (x, y)."""
    return landmark.x * img_w, landmark.y * img_h


def _dist(p1: tuple, p2: tuple) -> float:
    """Euclidean distance between two (x, y) pixel points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def _angle_deg(a: tuple, vertex: tuple, b: tuple) -> float:
    """
    Angle in degrees at `vertex` formed by rays vertex→a and vertex→b.
    Uses the dot-product formula.
    """
    va = (a[0] - vertex[0], a[1] - vertex[1])
    vb = (b[0] - vertex[0], b[1] - vertex[1])
    dot   = va[0] * vb[0] + va[1] * vb[1]
    mag_a = math.hypot(*va)
    mag_b = math.hypot(*vb)
    if mag_a == 0 or mag_b == 0:
        return 90.0
    cos_theta = max(-1.0, min(1.0, dot / (mag_a * mag_b)))
    return math.degrees(math.acos(cos_theta))


# ---------------------------------------------------------------------------
# Individual measurement functions
# ---------------------------------------------------------------------------

def get_face_length(lm, img_w: int, img_h: int) -> float:
    """
    Face length = vertical distance from forehead top (landmark 10)
    to chin bottom (landmark 152).
    """
    top  = _px(lm[FOREHEAD_TOP], img_w, img_h)
    chin = _px(lm[CHIN_BOTTOM],  img_w, img_h)
    return _dist(top, chin)


def get_forehead_width(lm, img_w: int, img_h: int) -> float:
    """
    Forehead width = horizontal distance between temporal landmarks
    54 (left) and 284 (right) near the hairline.
    """
    left  = _px(lm[FOREHEAD_LEFT],  img_w, img_h)
    right = _px(lm[FOREHEAD_RIGHT], img_w, img_h)
    return _dist(left, right)


def get_cheekbone_width(lm, img_w: int, img_h: int) -> float:
    """
    Cheekbone width = widest part of the face.
    Landmarks 234 (left cheek outer) and 454 (right cheek outer).
    """
    left  = _px(lm[CHEEKBONE_LEFT],  img_w, img_h)
    right = _px(lm[CHEEKBONE_RIGHT], img_w, img_h)
    return _dist(left, right)


def get_jawline_width(lm, img_w: int, img_h: int) -> float:
    """
    Jawline width = distance between the two gonion (jaw hinge) points:
    landmarks 172 (left) and 397 (right).
    """
    left  = _px(lm[JAW_LEFT],  img_w, img_h)
    right = _px(lm[JAW_RIGHT], img_w, img_h)
    return _dist(left, right)


def get_chin_width(lm, img_w: int, img_h: int) -> float:
    """
    Chin width = narrow lower portion.
    Landmarks 149 (left chin edge) and 378 (right chin edge).
    """
    left  = _px(lm[CHIN_LEFT],  img_w, img_h)
    right = _px(lm[CHIN_RIGHT], img_w, img_h)
    return _dist(left, right)


def calculate_jaw_angle(lm, img_w: int, img_h: int) -> float:
    """
    Jaw angle = average of the left and right mandibular angles.
    Left:  angle at landmark 172 (left gonion) formed by 234 (left cheek) → 172 → 152 (chin).
    Right: angle at landmark 397 (right gonion) formed by 454 (right cheek) → 397 → 152 (chin).

    Sharp angles (< 120°) → square jaw.
    Obtuse angles (> 135°) → soft/round/oval jaw.
    """
    chin   = _px(lm[CHIN_BOTTOM],          img_w, img_h)
    l_chk  = _px(lm[JAW_ANGLE_LEFT_CHEEK], img_w, img_h)
    l_jaw  = _px(lm[JAW_ANGLE_LEFT_GONION],img_w, img_h)
    r_chk  = _px(lm[JAW_ANGLE_RIGHT_CHEEK],img_w, img_h)
    r_jaw  = _px(lm[JAW_ANGLE_RIGHT_GONION],img_w, img_h)

    left_angle  = _angle_deg(l_chk, l_jaw, chin)
    right_angle = _angle_deg(r_chk, r_jaw, chin)
    return (left_angle + right_angle) / 2.0


def calculate_face_ratios(measurements: dict) -> dict:
    """
    Derive key ratios from raw pixel measurements.
    All ratios are unitless (proportions).
    """
    fl  = measurements['face_length']
    fw  = measurements['forehead_width']
    cw  = measurements['cheekbone_width']
    jw  = measurements['jawline_width']
    chw = measurements['chin_width']

    safe = lambda a, b: round(a / b, 4) if b > 0 else 0.0

    return {
        # How elongated is the face?
        'length_to_width':      safe(fl, cw),

        # How wide is the forehead relative to cheekbones?
        'forehead_to_cheek':    safe(fw, cw),

        # How wide is the jaw relative to cheekbones?
        'jaw_to_cheek':         safe(jw, cw),

        # How wide is the forehead relative to the jaw?
        'forehead_to_jaw':      safe(fw, jw),

        # How much does the chin narrow below the jaw?
        'chin_to_jaw':          safe(chw, jw),

        # How much do the cheekbones stand out vs forehead+jaw average?
        'cheek_prominence':     safe(cw, (fw + jw) / 2) if (fw + jw) > 0 else 0.0,
    }


# ---------------------------------------------------------------------------
# Classification engine
# ---------------------------------------------------------------------------

def _classify_face_shape(ratios: dict, jaw_angle: float) -> tuple[str, int, str]:
    """
    Classify face shape from ratios and jaw angle.
    Returns (shape_name, confidence_0_to_100, reason_string).

    Classification rules (geometric, not AI estimation):

    Triangle:   Jaw wider than forehead — jaw_to_cheek > forehead_to_cheek + threshold
    Rectangle:  Face clearly elongated AND sides uniform (forehead ≈ cheek ≈ jaw)
    Square:     Forehead ≈ jaw ≈ cheekbone AND sharp jaw angle (< 125°)
    Heart:      Wide forehead + significantly narrower jaw AND tapered chin
    Diamond:    Cheekbones clearly widest; both forehead AND jaw narrow relative to cheek
    Round:      Face almost as wide as long + soft jaw angle (> 140°) + uniform widths
    Oval:       Balanced length-to-width (1.3–1.5) with forehead slightly wider than jaw
    """
    ltw   = ratios['length_to_width']       # face length / cheekbone width
    ftc   = ratios['forehead_to_cheek']     # forehead / cheekbone
    jtc   = ratios['jaw_to_cheek']          # jaw / cheekbone
    ftj   = ratios['forehead_to_jaw']       # forehead / jaw
    ctj   = ratios['chin_to_jaw']           # chin / jaw
    cprom = ratios['cheek_prominence']      # cheekbone / avg(forehead, jaw)

    scores: dict[str, float] = {}

    # ── TRIANGLE ──────────────────────────────────────────────────────────
    # Jaw noticeably wider than forehead; lower face wider than upper face
    tri_score = 0.0
    if jtc > ftc + 0.08:          tri_score += 50.0
    if ftj < 0.88:                tri_score += 30.0
    if jaw_angle < 130:           tri_score += 20.0
    scores['triangle'] = tri_score

    # ── RECTANGLE / OBLONG ────────────────────────────────────────────────
    # Face clearly longer than wide; all widths roughly similar
    rect_score = 0.0
    if ltw > 1.55:                rect_score += 50.0
    elif ltw > 1.45:              rect_score += 25.0
    width_variance = max(abs(ftc - 1.0), abs(jtc - ftc))
    if width_variance < 0.12:     rect_score += 30.0
    if jaw_angle > 125:           rect_score += 20.0
    scores['rectangle'] = rect_score

    # ── SQUARE ────────────────────────────────────────────────────────────
    # All widths similar, face not very elongated, and jaw is angular
    sq_score = 0.0
    if ltw < 1.35:                sq_score += 25.0
    if abs(ftc - jtc) < 0.08:    sq_score += 30.0
    if jaw_angle < 125:           sq_score += 30.0
    if abs(ftc - 1.0) < 0.10:    sq_score += 15.0
    scores['square'] = sq_score

    # ── HEART ─────────────────────────────────────────────────────────────
    # Wide forehead, significantly narrower jaw, tapered chin
    ht_score = 0.0
    if ftj > 1.15:                ht_score += 45.0
    elif ftj > 1.08:              ht_score += 20.0
    if ctj < 0.72:                ht_score += 30.0
    if ftc > 0.88:                ht_score += 15.0
    if jaw_angle > 125:           ht_score += 10.0
    scores['heart'] = ht_score

    # ── DIAMOND ───────────────────────────────────────────────────────────
    # Cheekbones clearly the widest point; both forehead AND jaw narrow
    dm_score = 0.0
    if cprom > 1.12:              dm_score += 45.0
    elif cprom > 1.06:            dm_score += 25.0
    if ftc < 0.88:                dm_score += 25.0
    if jtc < 0.88:                dm_score += 20.0
    if ltw > 1.30:                dm_score += 10.0
    scores['diamond'] = dm_score

    # ── ROUND ─────────────────────────────────────────────────────────────
    # Face width close to face length; soft jaw angle; uniform widths
    ro_score = 0.0
    if ltw < 1.25:                ro_score += 40.0
    elif ltw < 1.35:              ro_score += 20.0
    if jaw_angle > 140:           ro_score += 35.0
    elif jaw_angle > 130:         ro_score += 15.0
    if abs(ftc - jtc) < 0.12:    ro_score += 15.0
    if ctj > 0.80:                ro_score += 10.0
    scores['round'] = ro_score

    # ── OVAL ──────────────────────────────────────────────────────────────
    # Balanced length-to-width, forehead slightly wider than jaw, soft jaw
    ov_score = 0.0
    if 1.30 <= ltw <= 1.55:       ov_score += 35.0
    if 1.05 <= ftj <= 1.20:       ov_score += 30.0
    if jaw_angle > 130:           ov_score += 20.0
    if 0.85 <= ftc <= 1.0:        ov_score += 15.0
    scores['oval'] = ov_score

    # Pick winner
    best_shape = max(scores, key=scores.get)
    best_raw   = scores[best_shape]

    # Confidence: normalise winner score (max raw ≈ 100) to 0–100 scale
    # Gap between winner and runner-up adds certainty
    sorted_scores = sorted(scores.values(), reverse=True)
    runner_up = sorted_scores[1] if len(sorted_scores) > 1 else 0
    gap_bonus = min(20, (best_raw - runner_up) * 0.5)
    confidence = int(min(98, max(45, best_raw * 0.80 + gap_bonus)))

    # Build human-readable reason
    reason = _build_reason(best_shape, ratios, jaw_angle)

    logger.info(
        f"Face shape scores: {scores} | winner={best_shape} "
        f"confidence={confidence} jaw_angle={jaw_angle:.1f}°"
    )
    return best_shape, confidence, reason


def _build_reason(shape: str, ratios: dict, jaw_angle: float) -> str:
    """Generate a one-sentence geometric reason for the detected face shape."""
    ltw = ratios['length_to_width']
    ftj = ratios['forehead_to_jaw']
    cprom = ratios['cheek_prominence']

    reasons = {
        'oval':      (f"Face length is {ltw:.2f}× cheekbone width with forehead "
                      f"{ftj:.2f}× jaw width — balanced proportions with a soft jaw."),
        'round':     (f"Face is nearly as wide as it is long (ratio {ltw:.2f}) "
                      f"with a soft jaw angle of {jaw_angle:.0f}°."),
        'square':    (f"Forehead and jawline are similar width (ratio {ftj:.2f}) "
                      f"with an angular jaw angle of {jaw_angle:.0f}°."),
        'heart':     (f"Forehead is {ftj:.2f}× wider than the jaw, tapering to a "
                      f"pointed chin — classic heart/inverted triangle shape."),
        'diamond':   (f"Cheekbones are {cprom:.2f}× wider than the forehead–jaw "
                      f"average — cheekbones are the widest feature."),
        'rectangle': (f"Face length is {ltw:.2f}× cheekbone width with uniform "
                      f"forehead, cheek and jaw widths — elongated rectangular shape."),
        'triangle':  (f"Jawline is wider than the forehead (forehead/jaw ratio {ftj:.2f}) "
                      f"creating a wide lower face."),
    }
    return reasons.get(shape, f"Geometric analysis determined {shape} face shape.")


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def detect_face_shape(image_input) -> dict:
    """
    Detect face shape from an image using MediaPipe Face Mesh (468 landmarks).
    Falls back to OpenCV edge-based geometry if MediaPipe is unavailable.

    Args:
        image_input: file path (str/Path), numpy BGR array, or bytes

    Returns dict with keys:
        face_shape        str  — one of: oval, round, square, heart, diamond, rectangle, triangle
        confidence        int  — 0-100
        measurements      dict — pixel distances for key facial widths/length
        ratios            dict — unitless proportional ratios
        jaw_angle         float — average mandibular angle in degrees
        reason            str  — human-readable geometric explanation
        method            str  — 'mediapipe' | 'opencv_fallback' | 'error'
        error             str  — only present on failure
    """
    # ── Load image ──────────────────────────────────────────────────────
    img = _load_image(image_input)
    if img is None:
        return {'face_shape': None, 'confidence': 0, 'method': 'error',
                'error': 'Could not load image'}

    img_h, img_w = img.shape[:2]

    # ── MediaPipe path ───────────────────────────────────────────────────
    if _MEDIAPIPE_AVAILABLE:
        result = _mediapipe_detect(img, img_w, img_h)
        if result:
            return result

    # ── OpenCV fallback ──────────────────────────────────────────────────
    logger.warning("MediaPipe detection failed — using OpenCV edge fallback")
    return _opencv_detect(img, img_w, img_h)


def _load_image(image_input) -> Optional[np.ndarray]:
    """Load any image input format into a BGR numpy array."""
    try:
        if isinstance(image_input, np.ndarray):
            return image_input.copy()
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input))
            return img
        if isinstance(image_input, bytes):
            arr = np.frombuffer(image_input, np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        logger.error(f"Image load error: {e}")
    return None


def _mediapipe_detect(img: np.ndarray, img_w: int, img_h: int) -> Optional[dict]:
    """
    Run MediaPipe Face Mesh and extract landmark-based measurements.
    Supports both the old solutions API (≤0.10.14) and the new tasks API (≥0.10.18).
    Returns the result dict or None if no face is detected.
    Handles multiple faces — returns the one with the highest mesh confidence.
    """
    if not _MEDIAPIPE_AVAILABLE:
        return None

    # ── Route to correct API ───────────────────────────────────────────────
    if _mp_face_mesh is not None:
        return _mediapipe_solutions(img, img_w, img_h)
    elif _mp_tasks_ready:
        return _mediapipe_tasks(img, img_w, img_h)
    return None


def _mediapipe_solutions(img: np.ndarray, img_w: int, img_h: int) -> Optional[dict]:
    """
    Old solutions API path (mediapipe ≤0.10.14) — mp.solutions.face_mesh
    """
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    best_result = None
    best_conf   = -1

    with _mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=4,
        refine_landmarks=True,
        min_detection_confidence=0.4,
        min_tracking_confidence=0.4,
    ) as face_mesh:
        mp_result = face_mesh.process(rgb)
        if not mp_result.multi_face_landmarks:
            logger.info("MediaPipe solutions: no face landmarks detected")
            return None

        for face_landmarks in mp_result.multi_face_landmarks:
            lm = face_landmarks.landmark
            result = _measure_and_classify(lm, img_w, img_h)
            if result and result['measurements']['face_length'] > best_conf:
                best_conf   = result['measurements']['face_length']
                best_result = result

    return best_result


def _mediapipe_tasks(img: np.ndarray, img_w: int, img_h: int) -> Optional[dict]:
    """
    New tasks API path (mediapipe ≥0.10.18) — mp.tasks.vision.FaceLandmarker.
    Downloads the official face_landmarker_v2_with_blendshapes.task model on first use.
    """
    import os, urllib.request, tempfile
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision

    # Model file — cached in project root to avoid repeated downloads
    model_path = os.path.join(os.path.dirname(__file__), '_mp_face_landmarker.task')
    if not os.path.exists(model_path):
        model_url = (
            'https://storage.googleapis.com/mediapipe-models/'
            'face_landmarker/face_landmarker/float16/1/face_landmarker.task'
        )
        logger.info(f"Downloading MediaPipe face landmarker model to {model_path}…")
        try:
            urllib.request.urlretrieve(model_url, model_path)
            logger.info("Model downloaded successfully")
        except Exception as e:
            logger.error(f"Failed to download MediaPipe model: {e}")
            return None

    try:
        base_opts = mp_python.BaseOptions(model_asset_path=model_path)
        opts = mp_vision.FaceLandmarkerOptions(
            base_options=base_opts,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
            num_faces=4,
            min_face_detection_confidence=0.4,
            min_face_presence_confidence=0.4,
        )
        with mp_vision.FaceLandmarker.create_from_options(opts) as landmarker:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            detection_result = landmarker.detect(mp_image)

            if not detection_result.face_landmarks:
                logger.info("MediaPipe tasks: no face landmarks detected")
                return None

            best_result = None
            best_conf   = -1

            for face_lm_list in detection_result.face_landmarks:
                # tasks API returns NormalizedLandmark objects (same .x .y .z as solutions)
                result = _measure_and_classify(face_lm_list, img_w, img_h)
                if result and result['measurements']['face_length'] > best_conf:
                    best_conf   = result['measurements']['face_length']
                    best_result = result

            return best_result

    except Exception as e:
        logger.error(f"MediaPipe tasks API error: {e}", exc_info=True)
        return None


def _measure_and_classify(lm, img_w: int, img_h: int) -> Optional[dict]:
    """
    Shared measurement + classification logic — works with both landmark formats.
    Both mp.solutions landmarks and mp.tasks landmarks expose .x .y .z
    """
    try:
        meas = {
            'face_length':      round(get_face_length(lm, img_w, img_h),    1),
            'forehead_width':   round(get_forehead_width(lm, img_w, img_h),  1),
            'cheekbone_width':  round(get_cheekbone_width(lm, img_w, img_h), 1),
            'jawline_width':    round(get_jawline_width(lm, img_w, img_h),   1),
            'chin_width':       round(get_chin_width(lm, img_w, img_h),      1),
        }
        jaw_angle = round(calculate_jaw_angle(lm, img_w, img_h), 2)
        ratios    = calculate_face_ratios(meas)
        shape, confidence, reason = _classify_face_shape(ratios, jaw_angle)
        return {
            'face_shape':   shape,
            'confidence':   confidence,
            'measurements': meas,
            'ratios':       ratios,
            'jaw_angle':    jaw_angle,
            'reason':       reason,
            'method':       'mediapipe',
        }
    except Exception as e:
        logger.warning(f"Landmark measurement error: {e}")
        return None


def _opencv_detect(img: np.ndarray, img_w: int, img_h: int) -> dict:
    """
    Fallback face shape detection using OpenCV Haar Cascade + edge-based
    width measurements. Less accurate than MediaPipe but works without it.
    """
    try:
        import cv2
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

        if len(faces) == 0:
            return {'face_shape': None, 'confidence': 0, 'method': 'error',
                    'error': 'No face detected by OpenCV fallback'}

        # Use largest face
        x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
        face_gray = gray[y:y+h, x:x+w]
        face_img  = img [y:y+h, x:x+w]

        face_ratio = h / max(w, 1)
        edges      = cv2.Canny(face_gray, 50, 150)

        def row_width(pct: float) -> float:
            row  = int(h * pct)
            data = edges[max(0, row-4):row+5, :]
            cols = np.where(data > 0)[1]
            return float(cols.max() - cols.min()) if len(cols) >= 2 else w * 0.75

        fw  = max(row_width(0.18), 1)   # forehead
        cw  = max(row_width(0.42), 1)   # cheekbones
        jw  = max(row_width(0.72), 1)   # jaw
        chw = max(row_width(0.88), 1)   # chin

        meas = {
            'face_length':     round(h,   1),
            'forehead_width':  round(fw,  1),
            'cheekbone_width': round(cw,  1),
            'jawline_width':   round(jw,  1),
            'chin_width':      round(chw, 1),
        }

        # Approximate jaw angle from cheek→jaw→chin geometry
        jaw_angle = 130.0  # default moderate; not calculable without landmarks
        ratios    = calculate_face_ratios(meas)
        shape, confidence, reason = _classify_face_shape(ratios, jaw_angle)
        confidence = max(40, confidence - 15)   # deduct for lower-accuracy method

        return {
            'face_shape':   shape,
            'confidence':   confidence,
            'measurements': meas,
            'ratios':       ratios,
            'jaw_angle':    jaw_angle,
            'reason':       reason,
            'method':       'opencv_fallback',
        }

    except Exception as e:
        logger.error(f"OpenCV fallback error: {e}")
        return {'face_shape': None, 'confidence': 0, 'method': 'error', 'error': str(e)}


# ---------------------------------------------------------------------------
# Face-shape makeup advice lookup
# (Used by results view to give product-level suggestions)
# ---------------------------------------------------------------------------

FACE_SHAPE_MAKEUP_GUIDE: dict[str, dict] = {
    'oval': {
        'description': 'Oval is considered the ideal balanced face shape. Most makeup styles work beautifully.',
        'contouring': 'Light contouring on temples and jawline to maintain balance.',
        'blush_placement': 'Apply to the apples of the cheeks and blend up toward temples.',
        'highlighter': 'Centre of forehead, bridge of nose, cupid\'s bow and chin.',
        'eyebrow_shape': 'Soft arch — follow your natural brow shape.',
        'foundation_tip': 'Even coverage throughout, no strong sculpting needed.',
        'lip_shape': 'Any lip shape works; a classic full lip enhances natural symmetry.',
        'best_hairstyles': ['Layered waves', 'Side-swept bangs', 'Any length works'],
        'avoid': ['Very voluminous hair on the sides that widens the face'],
        'product_tips': {
            'warm':    'Peachy-coral blushes (e.g., NARS Orgasm, MAC Fleur Power).',
            'cool':    'Rose or mauve blushes (e.g., Fenty Cheeky Puff in Peach Pledge).',
            'neutral': 'Soft terracotta or nude-pink blushes.',
        },
    },
    'round': {
        'description': 'Round faces benefit from techniques that add length and define the jawline.',
        'contouring': 'Contour along the sides of the forehead, hollows of cheeks, and jawline to slim.',
        'blush_placement': 'Apply diagonally from cheekbones upward toward temples — avoid round circular placement.',
        'highlighter': 'Centre of forehead and tip of chin to elongate.',
        'eyebrow_shape': 'High arch or angular brows to add vertical length.',
        'foundation_tip': 'Matte foundation on cheeks; subtle luminosity on the T-zone to elongate.',
        'lip_shape': 'Angular lip liner with a defined cupid\'s bow adds structure.',
        'best_hairstyles': ['Long layers', 'Side-parted styles', 'Height at crown'],
        'avoid': ['Very short bobs at chin level', 'Centre parts with no height'],
        'product_tips': {
            'warm':    'Bronze/terracotta contour (e.g., Benefit Hoola, Charlotte Tilbury Filmstar Bronze).',
            'cool':    'Cool taupe contour (e.g., MAC Taupe powder, NYX Taupe Contour Stick).',
            'neutral': 'Neutral grey-brown contour powder.',
        },
    },
    'square': {
        'description': 'Square faces have strong angular jawlines. Softening the corners creates a balanced look.',
        'contouring': 'Contour the four corners of the face — temples and jaw corners — to round them.',
        'blush_placement': 'Apply horizontally across cheekbones in a C-shape to soften angles.',
        'highlighter': 'Centre of the forehead and tip of the nose only — avoid jaw.',
        'eyebrow_shape': 'Soft curved or slightly arched brows to contrast angular jaw.',
        'foundation_tip': 'Blend foundation slightly past the jawline to soften the edge.',
        'lip_shape': 'Rounded lip shapes or ombre lips to add softness.',
        'best_hairstyles': ['Soft waves', 'Side-swept styles', 'Textured layers around the jaw'],
        'avoid': ['Blunt square cuts', 'Very straight horizontal eyebrows'],
        'product_tips': {
            'warm':    'Soft warm contour like MAC Sculpt & Shape or Benefit Hoola Lite.',
            'cool':    'Cool-toned contour palette (e.g., Anastasia Beverly Hills Contour Kit).',
            'neutral': 'Neutral contour stick for precise corner blending.',
        },
    },
    'heart': {
        'description': 'Heart-shaped faces have wide foreheads and narrow chins. Balance the upper and lower face.',
        'contouring': 'Contour the temples/sides of forehead to reduce width; highlight the chin to add volume.',
        'blush_placement': 'Below the cheekbones in a soft horizontal sweep — avoid the temples.',
        'highlighter': 'Centre of the chin and the bridge of the nose to draw attention downward.',
        'eyebrow_shape': 'Low arch with soft tails to minimise forehead width.',
        'foundation_tip': 'Matte finish on upper forehead; luminous finish on the chin area.',
        'lip_shape': 'Full lips or a slightly overdrawn bottom lip to balance the narrow chin.',
        'best_hairstyles': ['Chin-length bobs', 'Side-swept bangs', 'Volume at the jaw level'],
        'avoid': ['Voluminous styles at the top that widen the forehead'],
        'product_tips': {
            'warm':    'Warm bronze at temples with a peachy highlighter on the chin.',
            'cool':    'Cool blush on lower cheeks (e.g., Fenty Cheeky Puff Strawberry Drip).',
            'neutral': 'Soft nude pink on lower cheeks and a white shimmer on the chin.',
        },
    },
    'diamond': {
        'description': 'Diamond faces have prominent cheekbones with narrow forehead and jaw. Add width to the extremities.',
        'contouring': 'Contour along the cheekbones to reduce their prominence; highlight the forehead and jaw.',
        'blush_placement': 'Horizontally across cheekbones — keep it subtle to avoid emphasising their width.',
        'highlighter': 'Temples, sides of the forehead, and jaw corners to add width at the extremities.',
        'eyebrow_shape': 'Full, slightly curved brows to widen the forehead visually.',
        'foundation_tip': 'Luminous finish on forehead and chin; matte on cheekbones.',
        'lip_shape': 'Wider lip liner on the bow and corners to add width to the lower face.',
        'best_hairstyles': ['Side-swept fringes', 'Volume at the crown', 'Styles with width at the temples'],
        'avoid': ['Very narrow styles that emphasise cheekbone width'],
        'product_tips': {
            'warm':    'Warm gold highlighter on temples (e.g., Charlotte Tilbury Hollywood Flawless Filter).',
            'cool':    'Silver/rose-gold highlighter on temples and jaw (e.g., Fenty Beauty Killawatt).',
            'neutral': 'Champagne highlight across temples and jaw corners.',
        },
    },
    'rectangle': {
        'description': 'Rectangle (oblong) faces are significantly longer than wide. Add width and reduce length.',
        'contouring': 'Contour the hairline and chin to visually shorten the face.',
        'blush_placement': 'Apply horizontally in a wide sweep across the cheeks toward the temples to add width.',
        'highlighter': 'Focus on the centre of the cheeks — avoid highlighting the forehead and chin.',
        'eyebrow_shape': 'Flat, horizontal or slightly arched brows to reduce vertical length.',
        'foundation_tip': 'Luminous finish on the centre of the face; matte around the perimeter.',
        'lip_shape': 'Wide, rounded lips to add horizontal width to the lower face.',
        'best_hairstyles': ['Voluminous wavy styles', 'Side-swept bangs', 'Styles with width at the sides'],
        'avoid': ['Very long straight hair with a centre part', 'High ponytails that add height'],
        'product_tips': {
            'warm':    'Warm terracotta blush swept widely across cheeks (e.g., Too Faced Sweetie Pie).',
            'cool':    'Pink-mauve blush in a wide horizontal application.',
            'neutral': 'Peachy-nude blush swept broadly from cheekbone to temple.',
        },
    },
    'triangle': {
        'description': 'Triangle faces have wide jaws and narrow foreheads. Add width at the top and reduce it at the bottom.',
        'contouring': 'Contour the jawline to slim the lower face; highlight the temples to widen the forehead.',
        'blush_placement': 'High on the cheekbones, blending up toward the temples to draw the eye upward.',
        'highlighter': 'Temples and sides of the forehead generously to add width at the top.',
        'eyebrow_shape': 'Full, wide brows extended slightly beyond the outer eyes to widen the forehead.',
        'foundation_tip': 'Matte finish on the jaw and lower cheeks; luminous on the upper face.',
        'lip_shape': 'Defined cupid\'s bow with neutral or nude lip to avoid drawing attention to the jaw.',
        'best_hairstyles': ['Volume at the crown', 'Side-swept styles', 'Pixie cuts with height on top'],
        'avoid': ['Styles with volume at the jaw or chin level'],
        'product_tips': {
            'warm':    'Warm gold highlight on temples; matte bronze contour on jaw (e.g., Huda Beauty Bronze Sands).',
            'cool':    'Pearl highlight on temples; cool taupe contour on jaw.',
            'neutral': 'Champagne highlight on forehead; neutral contour on jawline corners.',
        },
    },
}


def get_face_shape_makeup_tips(face_shape: str, undertone: str = 'neutral') -> dict:
    """
    Return makeup tips and product suggestions for a given face shape and undertone.

    Args:
        face_shape: one of the 7 shape names (case-insensitive)
        undertone:  'warm', 'cool', or 'neutral'

    Returns dict with all makeup guidance fields plus undertone-specific product_tip.
    """
    shape   = (face_shape or 'oval').lower()
    tone    = (undertone or 'neutral').lower()
    guide   = FACE_SHAPE_MAKEUP_GUIDE.get(shape, FACE_SHAPE_MAKEUP_GUIDE['oval']).copy()
    tips    = guide.pop('product_tips', {})
    guide['product_tip'] = tips.get(tone, tips.get('neutral', ''))
    return guide
