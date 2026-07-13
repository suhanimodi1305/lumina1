"""
Scanner views for image upload and analysis
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import ScanResult
from apps.products.models import SkinConcern
from .face_detector import detect_face, extract_face_roi, divide_face_into_zones
from .hf_analyzer import run_full_skin_analysis, map_skin_tone_from_image
import os
import logging
import json
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)

# Demo profiles for testing without uploading photos
DEMO_PROFILES = {
    'combination_warm': {
        'skin_tone': 'medium',
        'undertone': 'warm',
        'face_shape': 'oval',
        'skin_type': 'combination',
        'skin_age': 26,
        'real_age': 25,
        'harmony_score': 74,
        'hydration_score': 65,
        'pigmentation_score': 48,
        'acne_score': 30,
        'aging_score': 20,
        'elasticity_score': 65,
        'hf_acne_severity': 'mild',
        'hf_skin_type': 'combination',
        'hf_undertone': 'warm',
        'hf_acne_confidence': 85.0,
        'hf_skin_type_confidence': 78.0,
        'hf_undertone_confidence': 72.0,
        'facial_zones': {
            'forehead': 'mild',
            'nose': 'moderate',
            'left_cheek': 'mild',
            'right_cheek': 'mild',
            'chin': 'moderate'
        },
        'concerns': ['dark_circles', 'pigmentation', 'blackheads', 'acne']
    },
    'dry_cool': {
        'skin_tone': 'fair',
        'undertone': 'cool',
        'face_shape': 'heart',
        'skin_type': 'dry',
        'skin_age': 29,
        'real_age': 28,
        'harmony_score': 68,
        'hydration_score': 40,
        'pigmentation_score': 30,
        'acne_score': 10,
        'aging_score': 35,
        'elasticity_score': 55,
        'hf_acne_severity': 'none',
        'hf_skin_type': 'dry',
        'hf_undertone': 'cool',
        'hf_acne_confidence': 92.0,
        'hf_skin_type_confidence': 88.0,
        'hf_undertone_confidence': 81.0,
        'facial_zones': {
            'forehead': 'none',
            'nose': 'none',
            'left_cheek': 'none',
            'right_cheek': 'none',
            'chin': 'none'
        },
        'concerns': ['dryness', 'redness', 'fine_lines', 'dark_circles']
    },
    'oily_warm': {
        'skin_tone': 'tan',
        'undertone': 'warm',
        'face_shape': 'round',
        'skin_type': 'oily',
        'skin_age': 23,
        'real_age': 22,
        'harmony_score': 78,
        'hydration_score': 75,
        'pigmentation_score': 55,
        'acne_score': 65,
        'aging_score': 10,
        'elasticity_score': 70,
        'hf_acne_severity': 'moderate',
        'hf_skin_type': 'oily',
        'hf_undertone': 'warm',
        'hf_acne_confidence': 89.0,
        'hf_skin_type_confidence': 91.0,
        'hf_undertone_confidence': 76.0,
        'facial_zones': {
            'forehead': 'severe',
            'nose': 'severe',
            'left_cheek': 'moderate',
            'right_cheek': 'moderate',
            'chin': 'moderate'
        },
        'concerns': ['acne', 'large_pores', 'oiliness', 'blackheads']
    },
    'mature_neutral': {
        'skin_tone': 'light',
        'undertone': 'neutral',
        'face_shape': 'square',
        'skin_type': 'normal',
        'skin_age': 38,
        'real_age': 37,
        'harmony_score': 65,
        'hydration_score': 55,
        'pigmentation_score': 60,
        'acne_score': 15,
        'aging_score': 55,
        'elasticity_score': 50,
        'hf_acne_severity': 'none',
        'hf_skin_type': 'normal',
        'hf_undertone': 'neutral',
        'hf_acne_confidence': 87.0,
        'hf_skin_type_confidence': 83.0,
        'hf_undertone_confidence': 79.0,
        'facial_zones': {
            'forehead': 'none',
            'nose': 'none',
            'left_cheek': 'none',
            'right_cheek': 'none',
            'chin': 'none'
        },
        'concerns': ['aging', 'fine_lines', 'dullness', 'pigmentation']
    }
}


def upload(request):
    """
    Scanner upload view - handles both demo mode and real photo uploads
    """
    
    # ============================================
    # GET REQUEST - Display upload page or demo
    # ============================================
    if request.method == 'GET':
        # Check for demo mode
        if request.GET.get('demo') == 'true':
            logger.info("Demo mode activated")
            
            # Get selected profile (default to combination_warm)
            profile_key = request.GET.get('profile', 'combination_warm')
            
            if profile_key not in DEMO_PROFILES:
                return render(request, 'scanner/upload.html', {
                    'title': 'Skin Analysis',
                    'demo_profiles': list(DEMO_PROFILES.keys()),
                    'initial_state': 'no-face',
                    'no_face_message': f'Invalid demo profile "{profile_key}". Please choose a valid option.',
                })
            
            profile = DEMO_PROFILES[profile_key].copy()
            
            # Extract concerns list
            concerns_list = profile.pop('concerns', [])
            
            # Ensure session exists
            if not request.session.session_key:
                request.session.save()

            # Get gender from query param (default female for demo)
            gender = request.GET.get('gender', 'female')
            if gender not in ('male', 'female', 'other'):
                gender = 'female'
            
            # Create demo ScanResult
            scan = ScanResult.objects.create(
                is_demo=True,
                session_key=request.session.session_key or 'demo',
                user=request.user if request.user.is_authenticated else None,
                gender=gender,
                **profile
            )
            
            # Add concerns
            for concern_slug in concerns_list:
                try:
                    concern = SkinConcern.objects.get(slug=concern_slug)
                    scan.detected_concerns.add(concern)
                except SkinConcern.DoesNotExist:
                    logger.warning(f"Concern not found: {concern_slug}")
            
            # Store scan ID in session
            request.session['latest_scan_id'] = scan.id
            
            logger.info(f"Demo scan created: ID={scan.id}, Profile={profile_key}")
            
            # Skip questionnaire — go straight to results
            return redirect('results:detail', scan_id=scan.id)
        
        # Normal GET - show upload page
        context = {
            'title': 'Skin Analysis',
            'demo_profiles': list(DEMO_PROFILES.keys()),
            'initial_state': 'default',
            'no_face_message': '',
        }
        return render(request, 'scanner/upload.html', context)
    
    # ============================================
    # POST REQUEST - Process uploaded photo
    # ============================================
    elif request.method == 'POST':
        logger.info("Processing photo upload...")
        
        # Ensure session exists
        if not request.session.session_key:
            request.session.save()
        
        # Get uploaded file
        scan_image = request.FILES.get('scan_image')
        
        if not scan_image:
            return render(request, 'scanner/upload.html', {
                'title': 'Skin Analysis',
                'demo_profiles': list(DEMO_PROFILES.keys()),
                'initial_state': 'no-face',
                'no_face_message': 'No photo received. Please upload or capture a photo first.',
            })
        
        # ── File security validation ──────────────────────────────────────────
        from django.conf import settings as _settings
        import imghdr

        MAX_IMAGE_BYTES = getattr(_settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 5 * 1024 * 1024)
        ALLOWED_TYPES   = getattr(_settings, 'ALLOWED_IMAGE_TYPES',
                                  ['image/jpeg', 'image/png', 'image/webp'])
        ALLOWED_EXTS    = getattr(_settings, 'ALLOWED_IMAGE_EXTENSIONS',
                                  ['.jpg', '.jpeg', '.png', '.webp'])

        # Get gender from form POST
        gender = request.POST.get('gender', 'female')
        if gender not in ('male', 'female', 'other'):
            gender = 'female'

        # Size check
        if scan_image.size > MAX_IMAGE_BYTES:
            return render(request, 'scanner/upload.html', {
                'title': 'Skin Analysis',
                'demo_profiles': list(DEMO_PROFILES.keys()),
                'initial_state': 'no-face',
                'no_face_message': f'File too large. Maximum allowed size is {MAX_IMAGE_BYTES // (1024*1024)} MB.',
            })

        # Extension check
        _, ext = os.path.splitext(scan_image.name.lower())
        if ext not in ALLOWED_EXTS:
            return render(request, 'scanner/upload.html', {
                'title': 'Skin Analysis',
                'demo_profiles': list(DEMO_PROFILES.keys()),
                'initial_state': 'no-face',
                'no_face_message': 'Invalid file type. Please upload a JPEG, PNG, or WebP image.',
            })

        # MIME type check (client-reported — secondary check)
        if scan_image.content_type and scan_image.content_type not in ALLOWED_TYPES:
            return render(request, 'scanner/upload.html', {
                'title': 'Skin Analysis',
                'demo_profiles': list(DEMO_PROFILES.keys()),
                'initial_state': 'no-face',
                'no_face_message': 'Invalid file type. Only JPEG, PNG, or WebP images are accepted.',
            })
        
        # Create scans directory if it doesn't exist
        scans_dir = Path(settings.MEDIA_ROOT) / 'scans'
        scans_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(scan_image.name)[1]
        unique_filename = f"{uuid4()}{file_extension}"
        file_path = scans_dir / unique_filename
        
        # Save uploaded file
        with open(file_path, 'wb+') as destination:
            for chunk in scan_image.chunks():
                destination.write(chunk)
        
        logger.info(f"File saved: {file_path}")
        
        # ── Magic bytes check (real content type, not client-reported) ────────
        real_type = imghdr.what(str(file_path))
        if real_type not in ('jpeg', 'png', 'webp', 'gif'):
            try:
                os.remove(file_path)
            except Exception:
                pass
            return render(request, 'scanner/upload.html', {
                'title': 'Skin Analysis',
                'demo_profiles': list(DEMO_PROFILES.keys()),
                'initial_state': 'no-face',
                'no_face_message': 'Invalid image file. Please upload a real JPEG or PNG photo.',
            })
        
        # ============================================
        # FACE DETECTION AND ANALYSIS
        # ============================================
        try:
            # Step 1: Detect face
            logger.info("Step 1: Detecting face...")
            face_result = detect_face(file_path)
            
            # If no face detected - render the error state directly (no redirect)
            if not face_result['detected']:
                logger.warning(f"No face detected: {face_result['message']}")

                # Delete uploaded file — nothing to keep
                if file_path.exists():
                    os.remove(file_path)

                # Render the upload page with error state — JS will show no-face card
                return render(request, 'scanner/upload.html', {
                    'title': 'Skin Analysis',
                    'demo_profiles': list(DEMO_PROFILES.keys()),
                    'initial_state': 'no-face',
                    'no_face_message': face_result['message'],
                })
            
            logger.info(f"Face detected successfully with {face_result['confidence']}% confidence")
            
            # Step 2: Run full skin analysis (3 HuggingFace APIs)
            logger.info("Step 2: Running HuggingFace AI analysis...")
            analysis_result = run_full_skin_analysis(file_path, face_result['face_rect'])
            
            # Step 3: Determine skin tone from image
            logger.info("Step 3: Determining skin tone...")
            # Use vision-detected skin tone if available, else OpenCV
            skin_tone = analysis_result.get('skin_tone_from_vision') or map_skin_tone_from_image(file_path, face_result['face_rect'])
            
            # Step 4: Create ScanResult with all analysis data
            logger.info("Step 4: Creating scan result...")
            
            # Enrich hf_acne_raw with MediaPipe geometry data so it survives to the results view
            try:
                raw_data = json.loads(analysis_result.get('hf_acne_raw', '{}') or '{}')
            except Exception:
                raw_data = {}
            raw_data['face_shape_confidence']  = analysis_result.get('face_shape_confidence', 0)
            raw_data['face_shape_reason']       = analysis_result.get('face_shape_reason', '')
            raw_data['face_shape_measurements'] = analysis_result.get('face_shape_measurements', {})
            raw_data['face_shape_ratios']       = analysis_result.get('face_shape_ratios', {})
            enriched_hf_acne_raw = json.dumps(raw_data)
            
            # Calculate relative path for scan_image field
            relative_path = f"scans/{unique_filename}"
            
            scan = ScanResult.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                scan_image=relative_path,
                is_demo=False,
                gender=gender,
                
                # Basic attributes — only store what was actually detected
                skin_tone=skin_tone,
                undertone=analysis_result['undertone'],
                face_shape=analysis_result.get('face_shape') or 'oval',
                skin_type=analysis_result['skin_type'],
                
                # Ages (skin_age based on aging_score)
                skin_age=25 + (analysis_result['aging_score'] // 4),
                real_age=25,  # Default - can be collected from user later
                
                # Scores
                harmony_score=analysis_result['harmony_score'],
                hydration_score=analysis_result['hydration_score'],
                pigmentation_score=analysis_result['pigmentation_score'],
                acne_score=analysis_result['acne_score'],
                aging_score=analysis_result['aging_score'],
                elasticity_score=analysis_result['elasticity_score'],
                
                # HuggingFace API results
                hf_acne_severity=analysis_result['hf_acne_severity'],
                hf_skin_type=analysis_result['hf_skin_type'],
                hf_undertone=analysis_result['hf_undertone'],
                
                hf_acne_confidence=analysis_result['hf_acne_confidence'] or 0.0,
                hf_skin_type_confidence=analysis_result['hf_skin_type_confidence'] or 0.0,
                hf_undertone_confidence=analysis_result['hf_undertone_confidence'] or 0.0,
                
                hf_acne_raw=enriched_hf_acne_raw,
                hf_skin_type_raw=analysis_result['hf_skin_type_raw'],
                hf_undertone_raw=analysis_result['hf_undertone_raw'],
                
                # Facial zones
                facial_zones=analysis_result['facial_zones']
            )
            
            # Step 5: Add detected concerns based on scores
            logger.info("Step 5: Detecting skin concerns...")
            
            concerns_to_add = []

            # From vision visible_concerns (direct from AI image analysis)
            vision_concerns_map = {
                'acne': 'acne', 'pimples': 'acne', 'breakout': 'acne',
                'blackheads': 'blackheads', 'dark spots': 'pigmentation',
                'hyperpigmentation': 'pigmentation', 'dark circles': 'dark_circles',
                'dryness': 'dryness', 'oiliness': 'oiliness', 'redness': 'redness',
                'fine lines': 'fine_lines', 'wrinkles': 'fine_lines',
                'large pores': 'large_pores', 'dullness': 'dullness',
            }
            for vc in analysis_result.get('visible_concerns', []):
                vc_lower = str(vc).lower().strip()
                for key, slug in vision_concerns_map.items():
                    if key in vc_lower:
                        concerns_to_add.append(slug)
                        break
            
            # Dark circles (always if hydration < 70)
            if analysis_result['hydration_score'] < 70:
                concerns_to_add.append('dark_circles')
            
            # Pigmentation (score > 40)
            if analysis_result['pigmentation_score'] > 40:
                concerns_to_add.append('pigmentation')
            
            # Blackheads (acne score > 30)
            if analysis_result['acne_score'] > 30:
                concerns_to_add.append('blackheads')
            
            # Dryness (hydration < 50)
            if analysis_result['hydration_score'] < 50:
                concerns_to_add.append('dryness')
            
            # Aging (aging score > 40)
            if analysis_result['aging_score'] > 40:
                concerns_to_add.append('aging')
                concerns_to_add.append('fine_lines')
            
            # Large pores (oily skin + acne > 30)
            if analysis_result['skin_type'] == 'oily' and analysis_result['acne_score'] > 30:
                concerns_to_add.append('large_pores')
            
            # Redness (moderate or severe acne)
            if analysis_result['hf_acne_severity'] in ['moderate', 'severe']:
                concerns_to_add.append('redness')
            
            # Oiliness (oily skin type)
            if analysis_result['skin_type'] == 'oily':
                concerns_to_add.append('oiliness')
            
            # Dullness (low hydration or low harmony)
            if analysis_result['hydration_score'] < 55 or analysis_result['harmony_score'] < 65:
                concerns_to_add.append('dullness')
            
            # Add concerns to scan
            for concern_slug in set(concerns_to_add):  # Remove duplicates
                try:
                    concern = SkinConcern.objects.get(slug=concern_slug)
                    scan.detected_concerns.add(concern)
                    logger.info(f"Added concern: {concern_slug}")
                except SkinConcern.DoesNotExist:
                    logger.warning(f"Concern not found: {concern_slug}")
            
            # Store scan ID in session
            request.session['latest_scan_id'] = scan.id
            
            logger.info(f"Scan completed successfully: ID={scan.id}")
            messages.success(request, 'Your skin analysis is complete!')
            
            # Scan done → go straight to Smart AI Quiz
            return redirect('diagnostic:smart_start')
            
        except Exception as e:
            # Log the full error
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)

            # Delete uploaded file if it exists
            try:
                if file_path.exists():
                    os.remove(file_path)
            except Exception:
                pass

            # Render error state directly — no redirect so message doesn't vanish
            error_msg = 'Analysis failed. Please try again with a clearer, well-lit photo facing the camera.'
            return render(request, 'scanner/upload.html', {
                'title': 'Skin Analysis',
                'demo_profiles': list(DEMO_PROFILES.keys()),
                'initial_state': 'no-face',
                'no_face_message': error_msg,
            })


# ─────────────────────────────────────────────────────────────────────────────
# POST-SCAN QUESTIONNAIRE VIEW
# ─────────────────────────────────────────────────────────────────────────────

def questionnaire(request, scan_id):
    """
    After the scan completes, show a short questionnaire to improve accuracy.
    The user answers lifestyle / age / concern questions, we patch the ScanResult,
    then redirect to results.
    """
    scan = get_object_or_404(ScanResult, id=scan_id)

    # Ownership check — must be the session owner or the logged-in user
    is_owner = (
        (request.user.is_authenticated and scan.user == request.user)
        or scan.session_key == request.session.session_key
    )
    if not is_owner:
        from django.contrib import messages as _msg
        _msg.warning(request, "This scan doesn't belong to your session.")
        return redirect('scanner:upload')

    # If already completed, skip straight to results
    if scan.qa_completed:
        return redirect('results:detail', scan_id=scan.id)

    if request.method == 'POST':
        # Handle skip
        if request.POST.get('skip') == '1':
            scan.qa_completed = True
            scan.save(update_fields=['qa_completed'])
            # Skip → go straight to results
            return redirect('results:detail', scan_id=scan.id)

        # Parse answers
        try:
            age = int(request.POST.get('age', 0))
            if 10 <= age <= 100:
                scan.real_age = age
                scan.qa_age   = age
                # Recalculate skin_age from aging_score + real_age context
                scan.skin_age = age + max(0, (scan.aging_score - 30) // 5)
        except (ValueError, TypeError):
            pass

        scan.qa_water_intake  = request.POST.get('water_intake', '')[:20]
        scan.qa_sleep_hours   = request.POST.get('sleep_hours', '')[:20]
        scan.qa_stress_level  = request.POST.get('stress_level', '')[:20]
        scan.qa_diet          = request.POST.get('diet', '')[:20]
        scan.qa_outdoor_hours = request.POST.get('outdoor_hours', '')[:20]
        scan.qa_completed     = True

        # User-selected additional concerns
        user_concerns = request.POST.getlist('extra_concerns')
        if user_concerns:
            scan.qa_skin_concerns = user_concerns[:10]
            # Also add them to detected_concerns M2M
            from apps.products.models import SkinConcern
            for slug in user_concerns:
                try:
                    concern = SkinConcern.objects.get(slug=slug)
                    scan.detected_concerns.add(concern)
                except SkinConcern.DoesNotExist:
                    pass

        # Adjust scores based on lifestyle answers
        _apply_lifestyle_adjustments(scan)

        scan.save()
        logger.info(f"Questionnaire completed for scan {scan_id}")
        # After questionnaire → go to Smart AI Quiz for deeper analysis
        return redirect('diagnostic:smart_start')

    # GET — build concern choices list
    from apps.products.models import SkinConcern
    all_concerns = SkinConcern.objects.all().order_by('name')
    # Exclude concerns already detected by AI scan
    detected_slugs = set(scan.detected_concerns.values_list('slug', flat=True))
    concern_choices = [
        (c.slug, c.name)
        for c in all_concerns
        if c.slug not in detected_slugs
    ]

    return render(request, 'scanner/questionnaire.html', {
        'scan':            scan,
        'scan_id':         scan_id,
        'concern_choices': concern_choices,
    })


def _apply_lifestyle_adjustments(scan):
    """
    Nudge scan scores based on questionnaire answers for higher accuracy.
    All adjustments are clamped to [0, 100].
    """
    def clamp(val, lo=0, hi=100):
        return max(lo, min(hi, val))

    # Water intake → hydration
    water_map = {'low': -8, 'moderate': 0, 'high': +6}
    scan.hydration_score = clamp(scan.hydration_score + water_map.get(scan.qa_water_intake, 0))

    # Sleep → elasticity + harmony
    sleep_map = {'<6': -10, '6-8': 0, '>8': +5}
    delta_sleep = sleep_map.get(scan.qa_sleep_hours, 0)
    scan.elasticity_score = clamp(scan.elasticity_score + delta_sleep)
    scan.harmony_score    = clamp(scan.harmony_score    + delta_sleep // 2)

    # Stress → acne + aging
    stress_map = {'low': -5, 'moderate': 0, 'high': +10}
    delta_stress = stress_map.get(scan.qa_stress_level, 0)
    scan.acne_score  = clamp(scan.acne_score  + delta_stress)
    scan.aging_score = clamp(scan.aging_score + delta_stress // 2)

    # Diet → pigmentation + acne
    diet_map = {'balanced': -5, 'oily': +8, 'sugary': +10}
    delta_diet = diet_map.get(scan.qa_diet, 0)
    scan.acne_score         = clamp(scan.acne_score         + delta_diet)
    scan.pigmentation_score = clamp(scan.pigmentation_score + delta_diet // 2)

    # Outdoor exposure → pigmentation
    outdoor_map = {'low': 0, 'moderate': +5, 'high': +12}
    scan.pigmentation_score = clamp(
        scan.pigmentation_score + outdoor_map.get(scan.qa_outdoor_hours, 0)
    )
