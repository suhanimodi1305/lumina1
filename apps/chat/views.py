"""
Chat views for Dr. Lumina AI chatbot — 4-tab version
Tabs: AI Doctor | Makeup | K-Beauty
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages as django_messages
from django.conf import settings
import json
import base64
import logging

from .models import Conversation, Message, QuickPrompt
from .ai_service import get_ai_response, parse_product_tags, clean_text_for_display
from apps.scanner.models import ScanResult
from apps.products.models import Product

logger = logging.getLogger(__name__)

VALID_MODES = ('doctor', 'makeup', 'kbeauty')


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────

def _build_scan_context(scan):
    """Convert a ScanResult object to a context dict for the AI."""
    return {
        'skin_tone':       scan.skin_tone,
        'undertone':       scan.undertone,
        'skin_type':       scan.skin_type,
        'face_shape':      scan.face_shape,
        'harmony_score':   scan.harmony_score,
        'hf_acne_severity': scan.hf_acne_severity,
        'hf_skin_type':    scan.hf_skin_type,
        'detected_concerns': [c.slug for c in scan.detected_concerns.all()],
    }


def _resolve_products(product_tags, price_ceiling=None):
    """Turn parsed product-tag list into serialisable dicts.

    Args:
        product_tags:   list of {'sku': ..., 'name': ...} dicts from parse_product_tags()
        price_ceiling:  maximum price (inclusive) to include; None means no ceiling (VIP).
                        When a ceiling is set, products with null price are also excluded.
    """
    if not product_tags:
        return []

    qs = Product.objects.filter(sku__in=[t['sku'] for t in product_tags])

    if price_ceiling is not None:
        # Exclude products exceeding price ceiling, and exclude null-price products
        qs = qs.filter(price__isnull=False, price__lte=price_ceiling)
    # else price_ceiling is None (VIP) — include all products including null-price

    suggestions = []
    for p in qs:
        suggestions.append({
            'sku':         p.sku,
            'name':        p.name,
            'brand':       p.brand,
            'range_name':  p.product_range,
            'description': (p.description or '')[:100],
            'image_url':   p.image_url if p.image_url else None,
        })
    return suggestions


# ─────────────────────────────────────────────
#  INDEX  (list all conversations)
# ─────────────────────────────────────────────

@login_required
def index(request):
    conversations = Conversation.objects.filter(user=request.user)
    return render(request, 'chat/index.html', {'conversations': conversations})


# ─────────────────────────────────────────────
#  CREATE  (start a new conversation)
# ─────────────────────────────────────────────

@login_required
def create_conversation(request):
    mode = request.GET.get('mode', 'doctor')
    if mode not in VALID_MODES:
        mode = 'doctor'

    mode_titles = {
        'doctor':  'AI Doctor Consultation',
        'makeup':  'Makeup Consultation',
        'kbeauty': 'K-Beauty Consultation',
    }

    conversation = Conversation.objects.create(
        user=request.user,
        title=mode_titles.get(mode, 'New Consultation'),
        mode=mode,
    )

    scan_id = request.GET.get('scan_id')
    if scan_id:
        try:
            scan = ScanResult.objects.get(id=scan_id)
            if scan.user == request.user or scan.session_key == request.session.session_key:
                conversation.skin_scan = scan
                conversation.title = f'{mode_titles.get(mode)} — Scan #{scan.id}'
                conversation.save()
                logger.info(f"Linked scan {scan_id} to conversation {conversation.id}")
        except ScanResult.DoesNotExist:
            logger.warning(f"Scan {scan_id} not found")

    return redirect('chat:room', pk=conversation.id)


# ─────────────────────────────────────────────
#  ROOM  (chat UI)
# ─────────────────────────────────────────────

@login_required
def room(request, pk):
    conversation = get_object_or_404(Conversation, id=pk, user=request.user)
    messages     = conversation.messages.all()
    quick_prompts = QuickPrompt.objects.filter(active=True)

    # Mode-specific quick prompts shown in sidebar
    mode_quick_prompts = {
        'doctor': [
            "I have acne on my cheeks",
            "My skin is very dry and flaky",
            "I have dark spots / pigmentation",
            "My skin is oily and shiny",
            "I have sensitive skin that reacts easily",
            "What's my basic skincare routine?",
        ],
        'makeup': [
            "Help me find my foundation shade",
            "What lipstick suits warm undertones?",
            "Recommend eyeshadow for brown eyes",
            "I want a natural no-makeup look",
            "Best drugstore products for Indian skin",
            "How to do a glass skin base?",
        ],
        'kbeauty': [
            "Give me a K-Beauty routine for acne",
            "What is double cleansing?",
            "How do I get glass skin?",
            "Best K-Beauty routine for anti-aging",
            "What is the 3-skin method?",
            "Recommend products for sensitive skin",
        ],
    }

    context = {
        'conversation':    conversation,
        'messages':        messages,
        'quick_prompts':   quick_prompts,
        'mode_prompts':    mode_quick_prompts.get(conversation.mode, []),
    }
    return render(request, 'chat/room.html', context)


# ─────────────────────────────────────────────
#  SEND MESSAGE
# ─────────────────────────────────────────────

@login_required
@require_POST
def send_message(request, pk):
    try:
        conversation = get_object_or_404(Conversation, id=pk, user=request.user)
        data         = json.loads(request.body)
        user_message = data.get('message', '').strip()

        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        logger.info(f"[{conversation.mode}] User: {user_message[:100]}")

        Message.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
        )

        history = [{'role': m.role, 'content': m.content} for m in conversation.messages.all()]

        scan_context = _build_scan_context(conversation.skin_scan) if conversation.skin_scan else None

        # Resolve tier and price ceiling for this user
        try:
            user_tier = request.user.profile.effective_tier
        except Exception:
            user_tier = 'normal'

        price_ceiling = {
            'normal': settings.NORMAL_PRICE_MAX,
            'medium': settings.MEDIUM_PRICE_MAX,
            'vip':    None,
        }.get(user_tier, settings.NORMAL_PRICE_MAX)

        ai_reply = get_ai_response(
            history,
            scan_context=scan_context,
            mode=conversation.mode,
            user_tier=user_tier,
        )

        ai_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_reply,
        )

        product_tags        = parse_product_tags(ai_reply)
        product_suggestions = _resolve_products(product_tags, price_ceiling=price_ceiling)
        clean_reply         = clean_text_for_display(ai_reply)

        # Auto-update title from first user message
        if conversation.message_count() == 2 and 'Consultation' in conversation.title:
            conversation.title = user_message[:50] + ('…' if len(user_message) > 50 else '')
            conversation.save()

        return JsonResponse({
            'reply':               clean_reply,
            'raw_reply':           ai_reply,
            'timestamp':           ai_message.created_at.strftime('%I:%M %p'),
            'conversation_title':  conversation.title,
            'product_suggestions': product_suggestions,
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request format.'}, status=400)
    except Exception as exc:
        logger.error(f"send_message error: {exc}", exc_info=True)
        # Never return raw exception details to the client
        return JsonResponse({'error': 'An error occurred. Please try again.'}, status=500)


# ─────────────────────────────────────────────
#  SEND PHOTO
# ─────────────────────────────────────────────

@login_required
@require_POST
def send_photo(request, pk):
    try:
        conversation = get_object_or_404(Conversation, id=pk, user=request.user)
        photo        = request.FILES.get('photo')

        if not photo:
            return JsonResponse({'error': 'No photo uploaded'}, status=400)

        # ── File security validation ──────────────────────────────────────────
        MAX_PHOTO_BYTES = 5 * 1024 * 1024   # 5 MB
        ALLOWED_TYPES   = getattr(settings, 'ALLOWED_IMAGE_TYPES',
                                  ['image/jpeg', 'image/png', 'image/webp'])
        ALLOWED_EXTS    = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS',
                                  ['.jpg', '.jpeg', '.png', '.webp'])

        if photo.size > MAX_PHOTO_BYTES:
            return JsonResponse({'error': 'Photo too large. Maximum size is 5 MB.'}, status=400)

        import os as _os
        _, ext = _os.path.splitext(photo.name.lower())
        if ext not in ALLOWED_EXTS:
            return JsonResponse({'error': 'Invalid file type. Upload a JPEG or PNG image.'}, status=400)

        if photo.content_type and photo.content_type not in ALLOWED_TYPES:
            return JsonResponse({'error': 'Invalid file type. Upload a JPEG or PNG image.'}, status=400)

        logger.info(f"Photo received: {photo.name}, {photo.size} bytes")

        photo_bytes    = photo.read()
        photo_base64   = base64.b64encode(photo_bytes).decode('utf-8')
        content_type   = photo.content_type or 'image/jpeg'

        Message.objects.create(
            conversation=conversation,
            role='user',
            content='[Photo uploaded for analysis]',
            image_data=photo_base64,
        )

        history = [{'role': m.role, 'content': m.content} for m in conversation.messages.all()]

        scan_context = _build_scan_context(conversation.skin_scan) if conversation.skin_scan else None

        # Resolve tier and price ceiling for this user
        try:
            user_tier = request.user.profile.effective_tier
        except Exception:
            user_tier = 'normal'

        price_ceiling = {
            'normal': settings.NORMAL_PRICE_MAX,
            'medium': settings.MEDIUM_PRICE_MAX,
            'vip':    None,
        }.get(user_tier, settings.NORMAL_PRICE_MAX)

        ai_reply = get_ai_response(
            history,
            scan_context=scan_context,
            image_base64=photo_base64,
            image_media_type=content_type,
            mode=conversation.mode,
            user_tier=user_tier,
        )

        ai_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content=ai_reply,
        )

        product_tags        = parse_product_tags(ai_reply)
        product_suggestions = _resolve_products(product_tags, price_ceiling=price_ceiling)
        clean_reply         = clean_text_for_display(ai_reply)

        return JsonResponse({
            'reply':               clean_reply,
            'raw_reply':           ai_reply,
            'timestamp':           ai_message.created_at.strftime('%I:%M %p'),
            'image_url':           f'data:{content_type};base64,{photo_base64}',
            'product_suggestions': product_suggestions,
        })

    except Exception as exc:
        logger.error(f"send_photo error: {exc}", exc_info=True)
        # Never return raw exception details to the client
        return JsonResponse({'error': 'Photo upload failed. Please try again.'}, status=500)


# ─────────────────────────────────────────────
#  SWITCH MODE  (AJAX — changes mode mid-chat)
# ─────────────────────────────────────────────

@login_required
@require_POST
def switch_mode(request, pk):
    """Switch the active chat tab/mode for an existing conversation."""
    try:
        conversation = get_object_or_404(Conversation, id=pk, user=request.user)
        data = json.loads(request.body)
        new_mode = data.get('mode', 'doctor')
        if new_mode not in VALID_MODES:
            return JsonResponse({'error': 'Invalid mode'}, status=400)
        conversation.mode = new_mode
        conversation.save(update_fields=['mode'])
        return JsonResponse({'success': True, 'mode': new_mode})
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)


# ─────────────────────────────────────────────
#  DELETE
# ─────────────────────────────────────────────

@login_required
@require_POST
def delete_conversation(request, pk):
    conversation = get_object_or_404(Conversation, id=pk, user=request.user)
    conversation.delete()
    django_messages.success(request, 'Conversation deleted successfully.')
    return redirect('chat:index')
