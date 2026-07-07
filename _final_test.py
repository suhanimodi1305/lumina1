# -*- coding: utf-8 -*-
"""Final comprehensive test. Run: python _final_test.py"""
import urllib.request, urllib.parse, http.cookiejar, json, sys, ast, os

BASE = 'http://127.0.0.1:8000'
ok_all = True

def p(mark, name, detail=""):
    global ok_all
    if mark == "FAIL":
        ok_all = False
    print(f"  [{mark}] {name}" + (f"  ({detail})" if detail else ""))

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(path, timeout=12):
    try:
        req = urllib.request.Request(BASE + path, headers={'User-Agent': 'final-test'})
        r = opener.open(req, timeout=timeout)
        return r.status, r.geturl(), r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, BASE + path, e.read().decode('utf-8', 'ignore')
    except Exception as ex:
        return 0, BASE + path, str(ex)

print("\n" + "="*55)
print("  LUMINA FINAL COMPREHENSIVE TEST")
print("="*55)

# ── 1. Python syntax for all key files
print("\n[1] SYNTAX")
for f in ['apps/scanner/hf_analyzer.py', 'apps/scanner/mediapipe_face_shape.py',
          'apps/scanner/face_detector.py', 'apps/scanner/views.py',
          'apps/results/views.py', 'apps/results/urls.py',
          'apps/scanner/models.py', 'apps/dashboard/views.py']:
    try:
        ast.parse(open(f, encoding='utf-8').read())
        p("PASS", f)
    except SyntaxError as e:
        p("FAIL", f, str(e))

# ── 2. No hardcoded random defaults
print("\n[2] NO HARDCODED DEFAULTS")
src = open('apps/scanner/hf_analyzer.py', encoding='utf-8').read()
p("PASS" if 'aging_base_map' in src else "FAIL", "aging computed from skin_type map")
p("PASS" if 'acne_score_map' in src else "FAIL", "acne score from severity map")
p("PASS" if "'severity': 'mild'" not in src else "FAIL", "no legacy default mild")
p("PASS" if 'aging_score        = 25' not in src else "FAIL", "no hardcoded aging_score=25")

vsrc = open('apps/scanner/views.py', encoding='utf-8').read()
p("PASS" if "return redirect('scanner:upload')" not in vsrc else "FAIL", "no redirect on error in scanner view")
p("PASS" if "initial_state': 'no-face'" in vsrc else "FAIL", "render with no-face state on error")
p("PASS" if "initial_state': 'default'" in vsrc else "FAIL", "render with default state on clean GET")

# ── 3. HTTP pages
print("\n[3] HTTP PAGES")
for path, name, expected in [
    ('/', 'Home', 200),
    ('/scan/', 'Scanner', 200),
    ('/accounts/login/', 'Login', 200),
    ('/results/1/', 'Results scan 1', 200),
    ('/results/1/face-shape-api/', 'Face shape API', 200),
]:
    status, url, body = get(path)
    p("PASS" if status == expected else "FAIL", f"{name} HTTP {status}", path)

# ── 4. Scanner page content
print("\n[4] SCANNER PAGE CONTENT")
_, _, body = get('/scan/')
checks = [
    ('INITIAL_STATE = "default"',   "INITIAL_STATE=default on clean GET"),
    ('NO_FACE_MSG',                  "NO_FACE_MSG constant present"),
    ('id="no-face-msg"',             "#no-face-msg element"),
    ("showScanState('default')",     "boot calls showScanState default"),
    ("showScanState('no-face')",     "error path calls showScanState no-face"),
    ('scan-state.*display: none',    "CSS hides all scan states"),
    ('facial landmarks',             "MediaPipe step in loading msgs"),
    ('id="state-default"',           "state-default exists"),
    ('id="state-no-face"',           "state-no-face exists"),
    ('id="state-scanning"',          "state-scanning exists"),
    ('no_face_detected' not in body, "old Django messages tag removed"),
]
import re
for check, name in checks:
    if isinstance(check, bool):
        p("PASS" if check else "FAIL", name)
    elif '.*' in check:
        p("PASS" if re.search(check.replace('.*', '.*'), body) else "FAIL", name)
    else:
        p("PASS" if check in body else "FAIL", name)

# ── 5. Results page content
print("\n[5] RESULTS PAGE CONTENT")
_, _, body = get('/results/1/')
for check, name in [
    ('Face Shape',          "Face Shape shown"),
    ('Skin Type',           "Skin Type shown"),
    ('Not detected',        "Not-detected fallback present"),
    ('Makeup Guide for',    "Face shape makeup guide"),
    ('Contouring',          "Contouring tip"),
    ('K-Beauty',            "K-Beauty tab"),
    ('score-bar-fill',      "Score bars rendered"),
    ('sasglobal.biz',       "SAS Global link"),
    ('facial-zones' or 'Facial Zone', "Facial zones map"),
]:
    p("PASS" if check in body else "FAIL", name)

# ── 6. Face Shape API response
print("\n[6] FACE SHAPE API")
_, _, body = get('/results/1/face-shape-api/')
try:
    data = json.loads(body)
    for key in ('face_shape','confidence','makeup_tips','undertone','skin_type','measurements','ratios'):
        p("PASS" if key in data else "FAIL", f"API has '{key}' key")
    tips = data.get('makeup_tips', {})
    for key in ('contouring','blush_placement','highlighter','product_tip','eyebrow_shape','lip_shape'):
        p("PASS" if key in tips else "FAIL", f"makeup_tips has '{key}'")
    p("PASS", f"face_shape={data['face_shape']} undertone={data['undertone']}")
except Exception as e:
    p("FAIL", "API JSON parse", str(e))

# ── 7. Demo profiles
print("\n[7] DEMO PROFILES")
for profile in ['combination_warm', 'dry_cool', 'oily_warm', 'mature_neutral']:
    status, final_url, _ = get(f'/scan/?demo=true&profile={profile}')
    landed = '/results/' in final_url
    p("PASS" if landed else "FAIL", profile, f"-> {final_url}")

# ── 8. MediaPipe module
print("\n[8] MEDIAPIPE MODULE")
msrc = open('apps/scanner/mediapipe_face_shape.py', encoding='utf-8').read()
p("PASS" if "hasattr(mp, 'solutions')" in msrc else "FAIL", "solutions API guard")
p("PASS" if "hasattr(mp, 'tasks')" in msrc else "FAIL", "tasks API guard")
p("PASS" if "_measure_and_classify" in msrc else "FAIL", "shared measurement function")
p("PASS" if msrc.count("'description':") >= 7 else "FAIL", "7 face shape guides")

# ── 9. Django system check
print("\n[9] DJANGO CHECK")
import subprocess
r = subprocess.run(['python', 'manage.py', 'check'], capture_output=True, text=True)
p("PASS" if 'no issues' in r.stdout.lower() else "FAIL", "manage.py check", r.stdout.strip().split('\n')[-1])

print(f"\n{'='*55}")
print(f"  {'ALL PASSING' if ok_all else 'SOME FAILING'}")
print(f"{'='*55}\n")
sys.exit(0 if ok_all else 1)
