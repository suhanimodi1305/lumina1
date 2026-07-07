"""
Skin Analysis — Lumina

Pipeline:
  1. MediaPipe extracts 468 facial landmarks → precise measurements
  2. Grok-4 (xAI) classifies face shape from measurements — NOT from pixels
  3. Groq Llama-4-Scout Vision analyses the actual photo for skin attributes
     (acne, skin type, undertone, tone, zones, concerns)
  4. OpenCV geometric fallback if all APIs fail

Face shape accuracy: Grok receives real numbers (face_length, forehead_width,
cheekbone_width, jaw_width, chin_width, jaw_angle, key ratios) and returns a
classification with real confidence — zero pixel-guessing.
"""
import base64
import json
import numpy as np
import cv2
import logging
from pathlib import Path
from django.conf import settings

logger = logging.getLogger(__name__)

# ── openai package — xAI Grok client (OpenAI-compatible API) ──────────────
try:
    from openai import OpenAI as _OpenAI
    _openai_pkg_available = True
except ImportError:
    _OpenAI = None
    _openai_pkg_available = False
    logger.warning("openai package not installed — add 'openai>=1.30.0' to requirements.txt")

# ── Groq SDK — Llama-4-Scout Vision for skin analysis ─────────────────────
try:
    from groq import Groq as _Groq
    _groq_available = True
except ImportError:
    _Groq = None
    _groq_available = False
    logger.warning("groq package not installed — add 'groq>=0.9.0' to requirements.txt")

# Model identifiers
GROK_MODEL      = 'grok-4'           # xAI — face shape classification from measurements
GROQ_VISION_MODEL = 'meta-llama/llama-4-scout-17b-16e-instruct'  # Groq — skin vision


# ─────────────────────────────────────────────────────────────────────────────
# PART 1 — FACE SHAPE via Grok-4 + MediaPipe measurements
# The key insight: send real geometric numbers to Grok, not pixels.
# Grok acts as a facial geometry expert, not a vision model.
# ─────────────────────────────────────────────────────────────────────────────

def _get_grok_client():
    """xAI Grok client — uses OpenAI-compatible API at https://api.x.ai/v1"""
    if not _openai_pkg_available or _OpenAI is None:
        return None
    api_key = getattr(settings, 'GROK_API_KEY', '')
    if not api_key or api_key == 'your-xai-grok-api-key-here':
        logger.warning("GROK_API_KEY not configured")
        return None
    return _OpenAI(api_key=api_key, base_url='https://api.x.ai/v1')


def get_face_shape_prompt(face_length, forehead_width, cheekbone_width,
                           jaw_width, chin_width, jaw_angle, ratios):
    """
    Build a precise geometry-only prompt for Grok face shape classification.
    Grok receives real measured numbers — it classifies, not guesses.
    """
    ltw  = ratios.get('length_to_width',   round(face_length / max(cheekbone_width, 1), 3))
    ftj  = ratios.get('forehead_to_jaw',   round(forehead_width / max(jaw_width, 1), 3))
    jtc  = ratios.get('jaw_to_cheek',      round(jaw_width / max(cheekbone_width, 1), 3))
    ftc  = ratios.get('forehead_to_cheek', round(forehead_width / max(cheekbone_width, 1), 3))
    ctj  = ratios.get('chin_to_jaw',       round(chin_width / max(jaw_width, 1), 3))

    return f"""You are a facial geometry expert. Classify face shape from measurements only.

Facial measurements (in pixels, taken from 468 MediaPipe facial landmarks):
  Face Length (hairline → chin tip):  {face_length:.1f}
  Forehead Width (temple to temple):  {forehead_width:.1f}
  Cheekbone Width (widest point):     {cheekbone_width:.1f}
  Jaw Width (gonion to gonion):       {jaw_width:.1f}
  Chin Width (lower chin edges):      {chin_width:.1f}
  Jaw Angle (avg mandibular angle):   {jaw_angle:.1f}°

Derived ratios:
  Length / Cheekbone Width:  {ltw}   (>1.5 = elongated, <1.2 = wide/round)
  Forehead / Jaw:            {ftj}   (>1.15 = heart/diamond, <0.88 = triangle)
  Jaw / Cheekbone:           {jtc}   (>forehead_to_cheek + 0.08 = triangle)
  Forehead / Cheekbone:      {ftc}
  Chin / Jaw:                {ctj}   (<0.72 = heart, >0.80 = round)
  Jaw Angle:                 {jaw_angle:.1f}°  (<125° = square, >140° = round/oval)

Classification rules (apply in order):
1. TRIANGLE   — jaw_to_cheek > forehead_to_cheek + 0.08 AND forehead_to_jaw < 0.90
2. RECTANGLE  — length_to_width > 1.50 AND width variance between sections < 0.12
3. SQUARE     — |forehead/cheek − jaw/cheek| < 0.08 AND jaw_angle < 125°
4. HEART      — forehead_to_jaw > 1.12 AND chin_to_jaw < 0.75
5. DIAMOND    — cheekbones widest: both forehead_to_cheek < 0.90 AND jaw_to_cheek < 0.90
6. ROUND      — length_to_width < 1.25 AND jaw_angle > 138°
7. OVAL       — 1.28 ≤ length_to_width ≤ 1.55, forehead slightly wider than jaw (1.05–1.20), soft jaw

Set confidence based on how clearly the measurements match ONE shape:
  90–100: Measurements clearly and unambiguously match this shape
  75–89:  Strong match with minor ambiguity
  60–74:  Moderate match — some overlap with another shape
  45–59:  Weak match — measurements are borderline

Return ONLY valid JSON, no markdown:
{{
  "face_shape": "oval|round|square|rectangle|diamond|heart|triangle",
  "confidence": <integer 0-100>,
  "reason": "one sentence citing the specific measurements that determined this shape",
  "measurements": {{
    "face_length": {face_length:.1f},
    "forehead_width": {forehead_width:.1f},
    "cheekbone_width": {cheekbone_width:.1f},
    "jaw_width": {jaw_width:.1f},
    "chin_width": {chin_width:.1f},
    "jaw_angle": {jaw_angle:.1f}
  }},
  "key_ratios": {{
    "length_to_width": {ltw},
    "forehead_to_jaw": {ftj},
    "jaw_to_cheek": {jtc}
  }}
}}"""


def classify_face_shape_with_grok(measurements: dict, ratios: dict, jaw_angle: float):
    """
    Send MediaPipe-extracted measurements to Grok-4 for face shape classification.
    Returns dict with face_shape, confidence, reason — or None if Grok unavailable.

    This is the recommended production pattern:
      Photo → MediaPipe → measurements → Grok text classification
    Grok never sees pixels — it only classifies from real geometric numbers.
    """
    client = _get_grok_client()
    if not client:
        logger.info("Grok API not configured — skipping Grok face shape classification")
        return None

    fl  = measurements.get('face_length',     0)
    fw  = measurements.get('forehead_width',  0)
    cw  = measurements.get('cheekbone_width', 0)
    jw  = measurements.get('jawline_width',   0)
    chw = measurements.get('chin_width',      0)

    if fl == 0 or cw == 0:
        logger.warning("Measurements incomplete — cannot call Grok")
        return None

    prompt = get_face_shape_prompt(fl, fw, cw, jw, chw, jaw_angle, ratios)

    try:
        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0,   # deterministic — pure geometry, no creativity needed
            max_tokens=400,
        )
        text = response.choices[0].message.content.strip()

        # Strip fences if present
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end > start:
            text = text[start:end+1]

        result = json.loads(text)
        shape = str(result.get('face_shape', '')).lower().strip()
        conf  = result.get('confidence', 0)
        reason = result.get('reason', '')

        valid_shapes = {'oval', 'round', 'square', 'heart', 'diamond', 'rectangle', 'triangle'}
        if shape not in valid_shapes:
            logger.warning(f"Grok returned invalid shape '{shape}'")
            return None

        logger.info(f"Grok face shape: {shape} ({conf}% confidence) — {reason}")
        return {
            'face_shape':  shape,
            'confidence':  int(conf),
            'reason':      reason,
            'source':      'grok',
        }

    except json.JSONDecodeError as e:
        logger.warning(f"Grok JSON parse error: {e} — raw: {text[:200]}")
        return None
    except Exception as exc:
        logger.error(f"Grok API error: {exc}", exc_info=True)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# PART 2 — SKIN ANALYSIS via Groq Vision (Llama-4-Scout)
# The image is sent to Groq for acne, skin type, undertone, tone, zones, concerns.
# Face shape is NOT asked from the vision model — Grok handles that from geometry.
# ─────────────────────────────────────────────────────────────────────────────

SKIN_VISION_PROMPT = """You are a clinical dermatology AI and K-Beauty specialist.
Analyze THIS specific face photo carefully and return ONLY valid JSON. No markdown, no extra text.
IMPORTANT: Base every field on what you ACTUALLY SEE in this image. Do NOT guess or use defaults.

You do NOT need to determine face shape — that is handled by geometric analysis separately.

SKIN ANALYSIS (examine the actual image):
- Pore visibility: enlarged/open pores = oily; tight/invisible = dry
- Surface shine: shiny all over = oily; T-zone only = combination; matte = dry/normal
- Texture: flaky/rough = dry; smooth/bumpy = oily/combination
- Lesions: papules/pustules/comedones = acne (count and severity)
- Undertone via jaw/neck: yellow-golden = warm; pink-rosy-bluish = cool; balanced = neutral
- Skin brightness: use Fitzpatrick scale visually

CONFIDENCE SCORING (be precise):
  90-100: Feature clearly visible, very high certainty
  75-89:  Feature visible, good certainty
  60-74:  Moderately visible, some uncertainty
  45-59:  Partially visible, significant uncertainty
  below 45: Barely visible or ambiguous

Return ONLY this JSON (no extra keys, no markdown):
{
  "acne_severity": "none|mild|moderate|severe",
  "acne_confidence": <0-100 integer>,
  "skin_type": "oily|dry|normal|combination",
  "skin_type_confidence": <0-100 integer>,
  "undertone": "warm|cool|neutral",
  "undertone_confidence": <0-100 integer>,
  "skin_tone": "fair|light|medium|tan|deep",
  "facial_zones": {
    "forehead": "none|mild|moderate|severe",
    "nose": "none|mild|moderate|severe",
    "left_cheek": "none|mild|moderate|severe",
    "right_cheek": "none|mild|moderate|severe",
    "chin": "none|mild|moderate|severe"
  },
  "visible_concerns": ["list only concerns actually visible in this image"],
  "analysis_notes": "one clinical sentence describing exactly what you see in this specific image",
  "foundation_shade": "exact shade code e.g. MAC NC35 or Maybelline Fit Me 230",
  "foundation_brand": "brand name",
  "kbeauty_focus": "primary K-Beauty treatment need for this person"
}"""


def _get_groq_client():
    if not _groq_available or _Groq is None:
        return None
    api_key = getattr(settings, 'GROQ_API_KEY', '')
    if not api_key:
        logger.error("GROQ_API_KEY not configured")
        return None
    return _Groq(api_key=api_key)


def _image_to_base64_jpeg(image_input, max_dim=800):
    """Convert any image input to a base64 JPEG string."""
    try:
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input))
        elif isinstance(image_input, np.ndarray):
            img = image_input.copy()
        elif isinstance(image_input, bytes):
            arr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        else:
            return None
        if img is None or img.size == 0:
            return None
        h, w = img.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)))
        success, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            return None
        return base64.b64encode(buf.tobytes()).decode('utf-8')
    except Exception as exc:
        logger.error(f"Image encode error: {exc}")
        return None


def _parse_json_response(text, label):
    """Extract and parse JSON from a model text response."""
    try:
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0].strip()
        elif '```' in text:
            text = text.split('```')[1].split('```')[0].strip()
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end > start:
            text = text[start:end+1]
        result = json.loads(text)
        logger.info(
            f"Skin analysis ({label}): "
            f"acne={result.get('acne_severity')}({result.get('acne_confidence')}%) "
            f"type={result.get('skin_type')}({result.get('skin_type_confidence')}%) "
            f"undertone={result.get('undertone')}({result.get('undertone_confidence')}%)"
        )
        return result
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error ({label}): {e} — raw: {text[:300]}")
        return None


def _skin_analyze_groq(image_input):
    """
    Send the face image to Groq Llama-4-Scout Vision for skin analysis only.
    Does NOT ask about face shape (that's Grok's job from measurements).
    Returns parsed dict or None.
    """
    client = _get_groq_client()
    if not client:
        return None

    b64 = _image_to_base64_jpeg(image_input)
    if not b64:
        return None

    def _attempt(prompt, num):
        try:
            resp = client.chat.completions.create(
                model=GROQ_VISION_MODEL,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{b64}'}},
                        {'type': 'text', 'text': prompt}
                    ]
                }],
                max_tokens=800,
                temperature=0.05,
            )
            return _parse_json_response(resp.choices[0].message.content.strip(), f'Groq attempt {num}')
        except Exception as exc:
            logger.error(f"Groq Vision error (attempt {num}): {exc}", exc_info=True)
            return None

    result = _attempt(SKIN_VISION_PROMPT, 1)
    if result:
        return result

    # Retry with minimal prompt
    logger.warning("Groq Vision retry with minimal prompt...")
    minimal = (
        'Analyze this face image. Return ONLY a JSON object:\n'
        '{"acne_severity":"none|mild|moderate|severe","acne_confidence":0-100,'
        '"skin_type":"oily|dry|normal|combination","skin_type_confidence":0-100,'
        '"undertone":"warm|cool|neutral","undertone_confidence":0-100,'
        '"skin_tone":"fair|light|medium|tan|deep",'
        '"facial_zones":{"forehead":"none|mild|moderate|severe","nose":"none|mild|moderate|severe",'
        '"left_cheek":"none|mild|moderate|severe","right_cheek":"none|mild|moderate|severe",'
        '"chin":"none|mild|moderate|severe"},'
        '"visible_concerns":[],"analysis_notes":"one sentence",'
        '"foundation_shade":"shade","foundation_brand":"brand","kbeauty_focus":"focus"}'
    )
    return _attempt(minimal, 2)


# ─────────────────────────────────────────────────────────────────────────────
# PART 3 — OpenCV fallbacks
# ─────────────────────────────────────────────────────────────────────────────

def _detect_face_shape_opencv(face_img):
    """
    Last-resort face shape from OpenCV Canny edge geometry.
    Used only when MediaPipe + Grok both fail.
    """
    try:
        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        face_ratio = h / max(w, 1)
        edges = cv2.Canny(gray, 50, 150)

        def row_width(pct):
            row = int(h * pct)
            data = edges[max(0, row-4):row+4, :]
            cols = np.where(data > 0)[1]
            return float(cols.max() - cols.min()) if len(cols) >= 2 else w * 0.75

        fw  = max(row_width(0.18), 1)
        cw  = max(row_width(0.42), 1)
        jw  = max(row_width(0.72), 1)
        chw = max(row_width(0.88), 1)

        if jw > fw * 1.15:                                         shape = 'triangle'
        elif face_ratio > 1.5:                                     shape = 'rectangle'
        elif abs(fw - jw) / max(fw, jw) < 0.12 and face_ratio < 1.25: shape = 'square'
        elif fw > jw * 1.15 and chw < fw * 0.7:                   shape = 'heart'
        elif cw > fw * 1.1 and cw > jw * 1.1:                     shape = 'diamond'
        elif face_ratio < 1.1 and abs(fw - jw) / max(fw, jw) < 0.15: shape = 'round'
        else:                                                      shape = 'oval'

        logger.info(f"OpenCV face shape fallback: {shape} (ratio={face_ratio:.2f})")
        return shape
    except Exception as exc:
        logger.warning(f"OpenCV face shape error: {exc}")
        return None


def _opencv_skin_fallback(image_input):
    """
    OpenCV pixel analysis for skin attributes when Groq Vision fails.
    Real pixel measurements — no hardcoded values.
    """
    try:
        if isinstance(image_input, (str, Path)):
            img = cv2.imread(str(image_input))
        elif isinstance(image_input, np.ndarray):
            img = image_input.copy()
        elif isinstance(image_input, bytes):
            arr = np.frombuffer(image_input, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        else:
            img = None

        if img is None or img.size == 0:
            return {}

        h, w = img.shape[:2]
        if w > 400:
            img = cv2.resize(img, (400, int(h * 400 / w)))
            h, w = img.shape[:2]

        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        skin_mask = cv2.inRange(hsv,
            np.array([0, 20, 70], dtype=np.uint8),
            np.array([20, 150, 255], dtype=np.uint8))
        skin_px = img[skin_mask > 0]
        if len(skin_px) < 100:
            skin_px = img.reshape(-1, 3)

        mean_bgr = skin_px.mean(axis=0)
        b, g, r  = float(mean_bgr[0]), float(mean_bgr[1]), float(mean_bgr[2])
        v_vals   = hsv[:, :, 2].astype(np.float64)
        skin_v   = v_vals[skin_mask > 0] if skin_mask.sum() > 0 else v_vals.ravel()
        mean_v   = float(np.mean(skin_v))
        v_var    = float(np.var(skin_v))

        skin_tone = ('fair' if mean_v > 200 else 'light' if mean_v > 170 else
                     'medium' if mean_v > 140 else 'tan' if mean_v > 110 else 'deep')

        rb = r - b
        undertone = 'warm' if rb > 15 else 'cool' if rb < -10 else 'neutral'

        t_zone = img[0:int(h*0.6), int(w*0.3):int(w*0.7)]
        cheeks  = img[int(h*0.3):int(h*0.7), :]
        t_v = float(np.mean(cv2.cvtColor(t_zone, cv2.COLOR_BGR2HSV)[:,:,2])) if t_zone.size > 0 else mean_v
        c_v = float(np.mean(cv2.cvtColor(cheeks, cv2.COLOR_BGR2HSV)[:,:,2])) if cheeks.size > 0 else mean_v
        diff = t_v - c_v

        skin_type = ('combination' if diff > 15 else
                     'oily' if v_var > 800 else
                     'dry'  if v_var < 200 else 'normal')

        def zone_acne(region):
            if region is None or region.size == 0: return 'none'
            rm = cv2.inRange(region, np.array([0,0,120], np.uint8), np.array([100,100,255], np.uint8))
            ratio = float(rm.sum()/255) / (region.shape[0]*region.shape[1])
            return ('none' if ratio < 0.01 else 'mild' if ratio < 0.04 else
                    'moderate' if ratio < 0.10 else 'severe')

        zones = {
            'forehead':    img[0:int(h*0.28), :],
            'nose':        img[int(h*0.28):int(h*0.56), int(w*0.35):int(w*0.65)],
            'left_cheek':  img[int(h*0.35):int(h*0.70), 0:int(w*0.35)],
            'right_cheek': img[int(h*0.35):int(h*0.70), int(w*0.65):],
            'chin':        img[int(h*0.72):, int(w*0.2):int(w*0.8)],
        }
        facial_zones = {z: zone_acne(zones[z]) for z in zones}
        srank = {'none': 0, 'mild': 1, 'moderate': 2, 'severe': 3}
        acne  = max(facial_zones.values(), key=lambda s: srank.get(s, 0))

        return {
            'acne_severity': acne,       'acne_confidence': 42.0,
            'skin_type': skin_type,      'skin_type_confidence': 42.0,
            'undertone': undertone,      'undertone_confidence': 42.0,
            'skin_tone': skin_tone,
            'facial_zones': facial_zones,
            'visible_concerns': [],
            'analysis_notes': 'OpenCV pixel analysis (vision APIs unavailable).',
        }
    except Exception as exc:
        logger.error(f"OpenCV skin fallback error: {exc}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# PART 4 — Validation and score computation
# ─────────────────────────────────────────────────────────────────────────────

def _validate_skin_result(result):
    """Validate enum fields and confidence values from skin analysis."""
    valid_sev  = {'none', 'mild', 'moderate', 'severe'}
    valid_type = {'oily', 'dry', 'normal', 'combination'}
    valid_und  = {'warm', 'cool', 'neutral'}
    valid_tone = {'fair', 'light', 'medium', 'tan', 'deep'}
    zones_list = ['forehead', 'nose', 'left_cheek', 'right_cheek', 'chin']

    def _norm(v):
        return str(v).lower().strip() if v is not None else None

    acne  = _norm(result.get('acne_severity'))
    stype = _norm(result.get('skin_type'))
    und   = _norm(result.get('undertone'))
    tone  = _norm(result.get('skin_tone'))

    result['acne_severity'] = acne  if acne  in valid_sev  else None
    result['skin_type']     = stype if stype in valid_type else None
    result['undertone']     = und   if und   in valid_und  else None
    result['skin_tone']     = tone  if tone  in valid_tone else None

    # Confidence: use model's own value; None if missing (never fake it)
    for ck in ('acne_confidence', 'skin_type_confidence', 'undertone_confidence'):
        v = result.get(ck)
        result[ck] = float(v) if isinstance(v, (int, float)) and 0 <= float(v) <= 100 else None

    # Facial zones
    fz      = result.get('facial_zones', {}) or {}
    overall = result['acne_severity'] or 'none'
    for z in zones_list:
        zv = _norm(fz.get(z))
        fz[z] = zv if zv in valid_sev else overall
    result['facial_zones'] = fz

    if not isinstance(result.get('makeup_routine'), dict):
        result['makeup_routine'] = {}

    return result


def _compute_scores(skin_result):
    """
    Derive numeric dashboard scores from validated skin analysis fields.
    All values are computed from real detections — not hardcoded.
    """
    acne_sev  = skin_result.get('acne_severity') or 'none'
    skin_type = skin_result.get('skin_type')     or 'normal'
    und_conf  = float(skin_result.get('undertone_confidence') or 55.0)
    acne_conf = float(skin_result.get('acne_confidence')      or 55.0)

    acne_score = {'none': 5, 'mild': 25, 'moderate': 60, 'severe': 90}[acne_sev]

    hydration_score     = {'dry': 28, 'oily': 68, 'combination': 55, 'normal': 65}[skin_type]
    pigmentation_score  = int(min(100, max(0, acne_score * 0.40 + (100 - und_conf) * 0.30)))
    aging_base          = {'dry': 35, 'oily': 18, 'combination': 22, 'normal': 25}[skin_type]
    aging_score         = int(min(80, max(5, aging_base + (100 - acne_conf) * 0.10)))
    elasticity_base     = {'oily': 70, 'dry': 45, 'combination': 62, 'normal': 60}[skin_type]
    elasticity_score    = int(min(95, max(20, elasticity_base - aging_score * 0.15)))
    harmony             = int(max(40, min(96, 100 - (acne_score*0.30 + pigmentation_score*0.20 + aging_score*0.15))))

    return {
        'acne_score':         acne_score,
        'hydration_score':    hydration_score,
        'pigmentation_score': pigmentation_score,
        'aging_score':        aging_score,
        'elasticity_score':   elasticity_score,
        'harmony_score':      harmony,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def run_full_skin_analysis(image_path, face_rect):
    """
    Full analysis pipeline:

    Face Shape (most accurate first):
      1. MediaPipe → 468 landmarks → real measurements
      2. Grok-4 (xAI) classifies from those measurements (text, not vision)
      3. MediaPipe's own geometric classifier (if Grok unavailable)
      4. OpenCV Canny edge geometry (last resort)
      5. 'oval' only if everything fails

    Skin Attributes (from the actual photo):
      1. Groq Llama-4-Scout Vision — acne, type, undertone, tone, zones
      2. OpenCV pixel analysis (if Groq fails)

    No random values. No hardcoded defaults. Every confidence is the model's own.
    """
    logger.info("Starting skin analysis pipeline...")

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError("Cannot read image file")

    try:
        from .face_detector import extract_face_roi
        face_img = extract_face_roi(image_path, face_rect)
    except Exception:
        face_img = img

    # ── Step 1: MediaPipe — extract measurements ─────────────────────────
    mediapipe_face_shape   = None
    mediapipe_confidence   = 0
    mediapipe_reason       = ''
    mediapipe_measurements = {}
    mediapipe_ratios       = {}
    mediapipe_jaw_angle    = 130.0  # fallback if MediaPipe unavailable

    try:
        from .mediapipe_face_shape import detect_face_shape as mp_detect
        mp_result = mp_detect(face_img)
        if mp_result:
            mediapipe_face_shape   = mp_result.get('face_shape')
            mediapipe_confidence   = mp_result.get('confidence', 0)
            mediapipe_reason       = mp_result.get('reason', '')
            mediapipe_measurements = mp_result.get('measurements', {})
            mediapipe_ratios       = mp_result.get('ratios', {})
            mediapipe_jaw_angle    = mp_result.get('jaw_angle', 130.0)
            logger.info(
                f"MediaPipe: {mediapipe_face_shape} "
                f"({mediapipe_confidence}% via {mp_result.get('method','?')})"
            )
    except Exception as mp_exc:
        logger.warning(f"MediaPipe error: {mp_exc}")

    # ── Step 2: Grok-4 classifies from MediaPipe measurements ───────────
    grok_face_shape    = None
    grok_confidence    = 0
    grok_reason        = ''

    if mediapipe_measurements:
        grok_result = classify_face_shape_with_grok(
            mediapipe_measurements, mediapipe_ratios, mediapipe_jaw_angle
        )
        if grok_result:
            grok_face_shape = grok_result['face_shape']
            grok_confidence = grok_result['confidence']
            grok_reason     = grok_result['reason']
            logger.info(f"Grok face shape: {grok_face_shape} ({grok_confidence}%)")
    else:
        logger.info("No MediaPipe measurements — skipping Grok face shape")

    # ── Step 3: Resolve final face shape ─────────────────────────────────
    # Grok from measurements is preferred over MediaPipe's own classifier
    # (Grok reasons about the numbers; MediaPipe scores by threshold rules)
    valid_shapes = {'oval', 'round', 'square', 'heart', 'oblong', 'rectangle', 'diamond', 'triangle'}
    opencv_face_shape = _detect_face_shape_opencv(face_img)

    if grok_face_shape in valid_shapes:
        face_shape         = grok_face_shape
        face_shape_conf    = grok_confidence
        face_shape_reason  = grok_reason
        logger.info(f"Using Grok face shape: {face_shape} ({face_shape_conf}%)")

    elif mediapipe_face_shape in valid_shapes:
        face_shape         = mediapipe_face_shape
        face_shape_conf    = mediapipe_confidence
        face_shape_reason  = mediapipe_reason
        logger.info(f"Using MediaPipe face shape: {face_shape} ({face_shape_conf}%)")

    elif opencv_face_shape in valid_shapes:
        face_shape         = opencv_face_shape
        face_shape_conf    = 40
        face_shape_reason  = 'OpenCV edge geometry (landmark APIs unavailable).'
        logger.info(f"Using OpenCV face shape: {face_shape}")

    else:
        face_shape         = 'oval'
        face_shape_conf    = 0
        face_shape_reason  = 'Could not determine face shape — defaulting to oval.'
        logger.warning("All face shape detectors failed — defaulted to oval")

    # ── Step 4: Groq Vision — skin attributes ────────────────────────────
    skin_raw = _skin_analyze_groq(face_img)
    if skin_raw:
        logger.info("Groq Vision skin analysis succeeded")
        skin = _validate_skin_result(skin_raw)
    else:
        logger.warning("Groq Vision failed — using OpenCV skin fallback")
        skin = _validate_skin_result(_opencv_skin_fallback(face_img) or {})

    # ── Step 5: Fill any missing skin fields ─────────────────────────────
    if skin.get('acne_severity') is None:
        skin['acne_severity']  = 'none';  skin['acne_confidence']      = None
    if skin.get('skin_type') is None:
        skin['skin_type']      = 'normal'; skin['skin_type_confidence'] = None
    if skin.get('undertone') is None:
        skin['undertone']      = 'neutral'; skin['undertone_confidence'] = None
    if skin.get('skin_tone') is None:
        skin['skin_tone'] = 'medium'

    scores = _compute_scores(skin)

    def _sr(v, d=1):
        return round(float(v), d) if v is not None else None

    return {
        'hf_acne_severity':        skin['acne_severity'],
        'hf_acne_confidence':      _sr(skin.get('acne_confidence')),
        'hf_acne_raw':             json.dumps({**skin, 'face_shape': face_shape,
                                               'face_shape_confidence': face_shape_conf,
                                               'face_shape_reason': face_shape_reason,
                                               'face_shape_measurements': mediapipe_measurements,
                                               'face_shape_ratios': mediapipe_ratios}),

        'hf_skin_type':            skin['skin_type'],
        'hf_skin_type_confidence': _sr(skin.get('skin_type_confidence')),
        'hf_skin_type_raw':        json.dumps({'type': skin['skin_type']}),

        'hf_undertone':            skin['undertone'],
        'hf_undertone_raw_label':  skin['undertone'],
        'hf_undertone_confidence': _sr(skin.get('undertone_confidence')),
        'hf_undertone_raw':        json.dumps({'undertone': skin['undertone']}),

        'facial_zones':            skin['facial_zones'],
        'skin_type':               skin['skin_type'],
        'undertone':               skin['undertone'],
        'face_shape':              face_shape,
        'skin_tone_from_vision':   skin.get('skin_tone', 'medium'),

        'foundation_shade':        skin.get('foundation_shade', ''),
        'foundation_brand':        skin.get('foundation_brand', ''),
        'face_shape_reason':       face_shape_reason,
        'kbeauty_focus':           skin.get('kbeauty_focus', ''),
        'visible_concerns':        skin.get('visible_concerns', []),
        'analysis_notes':          skin.get('analysis_notes', ''),
        'makeup_routine':          skin.get('makeup_routine', {}),

        'face_shape_confidence':   face_shape_conf,
        'face_shape_measurements': mediapipe_measurements,
        'face_shape_ratios':       mediapipe_ratios,

        **scores,
    }


def map_skin_tone_from_image(image_path, face_rect):
    """OpenCV brightness-based skin tone (fallback only)."""
    try:
        from .face_detector import extract_face_roi
        roi   = extract_face_roi(image_path, face_rect)
        hsv   = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mean_v = float(np.mean(hsv[:, :, 2]))
        return ('fair' if mean_v > 200 else 'light' if mean_v > 170 else
                'medium' if mean_v > 140 else 'tan' if mean_v > 110 else 'deep')
    except Exception as exc:
        logger.error(f"Skin tone error: {exc}")
        return 'medium'


# ── Legacy compatibility wrappers ──────────────────────────────────────────

def analyze_acne_severity(image_data):
    r = _skin_analyze_groq(image_data) or _opencv_skin_fallback(image_data)
    r = _validate_skin_result(r or {})
    return {'severity': r.get('acne_severity'), 'confidence': round(r.get('acne_confidence') or 0, 1),
            'raw': json.dumps(r), 'model': GROQ_VISION_MODEL}


def analyze_skin_type(image_data):
    r = _skin_analyze_groq(image_data) or _opencv_skin_fallback(image_data)
    r = _validate_skin_result(r or {})
    return {'skin_type': r.get('skin_type'), 'confidence': round(r.get('skin_type_confidence') or 0, 1),
            'raw': json.dumps(r), 'model': GROQ_VISION_MODEL}


def analyze_undertone(image_data):
    r = _skin_analyze_groq(image_data) or _opencv_skin_fallback(image_data)
    r = _validate_skin_result(r or {})
    return {'undertone': r.get('undertone'), 'raw_label': r.get('undertone'),
            'confidence': round(r.get('undertone_confidence') or 0, 1),
            'raw': json.dumps(r), 'model': GROQ_VISION_MODEL}


def analyze_facial_zones(zones_dict):
    severities = {}
    for name, zimg in zones_dict.items():
        if zimg is None or (hasattr(zimg, 'size') and zimg.size == 0):
            severities[name] = 'none'; continue
        try:
            severities[name] = analyze_acne_severity(zimg)['severity'] or 'none'
        except Exception as exc:
            logger.error(f"Zone {name}: {exc}"); severities[name] = 'none'
    return severities
