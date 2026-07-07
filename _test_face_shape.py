"""
Quick sanity test for face shape classification.
Run: python _test_face_shape.py
"""
import sys, os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lumina.settings')
sys.path.insert(0, '.')
django.setup()

from apps.scanner.mediapipe_face_shape import (
    _classify_face_shape,
    calculate_face_ratios,
    get_face_shape_makeup_tips,
    FACE_SHAPE_MAKEUP_GUIDE,
)

# Each tuple: (expected_shape, measurements_dict, jaw_angle)
TEST_CASES = [
    # Oval: balanced length (1.42x), forehead slightly wider than jaw
    ('oval',      dict(face_length=320, forehead_width=210, cheekbone_width=225,
                       jawline_width=195, chin_width=155), 135.0),
    # Round: nearly as wide as long, soft jaw
    ('round',     dict(face_length=230, forehead_width=215, cheekbone_width=225,
                       jawline_width=210, chin_width=175), 148.0),
    # Square: jaw ≈ forehead ≈ cheek, sharp angle
    ('square',    dict(face_length=240, forehead_width=225, cheekbone_width=228,
                       jawline_width=222, chin_width=180), 118.0),
    # Heart: wide forehead, narrow chin
    ('heart',     dict(face_length=300, forehead_width=240, cheekbone_width=235,
                       jawline_width=195, chin_width=130), 138.0),
    # Diamond: cheekbones clearly widest, narrow forehead AND jaw
    ('diamond',   dict(face_length=310, forehead_width=185, cheekbone_width=250,
                       jawline_width=183, chin_width=145), 132.0),
    # Rectangle: long face (1.77x), all widths similar
    ('rectangle', dict(face_length=380, forehead_width=210, cheekbone_width=215,
                       jawline_width=208, chin_width=168), 128.0),
    # Triangle: jaw clearly wider than forehead
    ('triangle',  dict(face_length=290, forehead_width=185, cheekbone_width=230,
                       jawline_width=255, chin_width=200), 116.0),
]

print("\n=== Face Shape Classification Test ===\n")
print(f"{'Expected':<12} {'Got':<12} {'Conf':>5}  {'Status':<6}  Key Ratios")
print("-" * 75)

passes = 0
fails  = 0

for expected, meas, jaw_angle in TEST_CASES:
    ratios = calculate_face_ratios(meas)
    shape, conf, reason = _classify_face_shape(ratios, jaw_angle)
    status = "PASS" if shape == expected else "FAIL"
    if shape == expected:
        passes += 1
    else:
        fails += 1
    ltw = ratios['length_to_width']
    ftj = ratios['forehead_to_jaw']
    jtc = ratios['jaw_to_cheek']
    cp  = ratios['cheek_prominence']
    print(f"{expected:<12} {shape:<12} {conf:>4}%  {status:<6}  "
          f"ltw={ltw:.2f} ftj={ftj:.2f} jtc={jtc:.2f} cp={cp:.2f}  jaw={jaw_angle:.0f}°")

print(f"\nResult: {passes}/{len(TEST_CASES)} passed, {fails} failed\n")

# ── Makeup tips test ──────────────────────────────────────────────────────
print("=== Makeup Tips Test ===\n")
for shape in FACE_SHAPE_MAKEUP_GUIDE.keys():
    for tone in ('warm', 'cool', 'neutral'):
        tips = get_face_shape_makeup_tips(shape, tone)
        assert 'contouring' in tips, f"Missing contouring for {shape}"
        assert 'blush_placement' in tips, f"Missing blush_placement for {shape}"
        assert 'product_tip' in tips, f"Missing product_tip for {shape}/{tone}"
    print(f"  {shape}: tips OK for warm/cool/neutral")

print("\nAll makeup tip tests passed!")
