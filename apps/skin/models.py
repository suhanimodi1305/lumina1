"""
Skin Diagnosis app models — 15-step AI consultation wizard.
Covers: skin type, acne, pigmentation, sensitivity, aging, under-eye,
        lifestyle, diet, skincare routine, makeup, K-beauty, ayurvedic,
        medical history, product preferences, and AI goals.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid


class SkinSession(models.Model):
    """Stores one completed 15-step skin diagnostic wizard run."""

    SKIN_TYPE_CHOICES = [
        ('oily',        'Oily'),
        ('dry',         'Dry'),
        ('combination', 'Combination'),
        ('normal',      'Normal'),
        ('sensitive',   'Sensitive'),
    ]

    ACNE_SEVERITY_CHOICES = [
        ('none',     'No Acne'),
        ('mild',     'Mild'),
        ('moderate', 'Moderate'),
        ('severe',   'Severe'),
    ]

    STRESS_CHOICES = [
        ('low',    'Low'),
        ('medium', 'Medium'),
        ('high',   'High'),
    ]

    SLEEP_CHOICES = [
        ('lt6',  'Less than 6 hours'),
        ('6to8', '6–8 hours'),
        ('gt8',  'More than 8 hours'),
    ]

    BUDGET_CHOICES = [
        ('affordable', 'Affordable (< ₹500)'),
        ('mid',        'Mid-range (₹500–₹2000)'),
        ('premium',    'Premium (₹2000–₹5000)'),
        ('luxury',     'Luxury (₹5000+)'),
    ]

    ROUTINE_DETAIL_CHOICES = [
        ('simple',   'Simple (3-step)'),
        ('balanced', 'Balanced (5-step)'),
        ('detailed', 'Full K-beauty (7–10 step)'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='skin_sessions')
    session_key = models.CharField(max_length=100, blank=True)

    # ── Step 1: Basic Information ───────────────────────────────
    age         = models.PositiveSmallIntegerField(default=25)
    age_group   = models.CharField(max_length=20, blank=True)
    gender      = models.CharField(max_length=20, blank=True)
    country     = models.CharField(max_length=80, blank=True)
    city        = models.CharField(max_length=80, blank=True)
    climate     = models.CharField(max_length=30, blank=True)
    current_season = models.CharField(max_length=20, blank=True)  # summer/winter/monsoon/spring
    occupation  = models.CharField(max_length=20, blank=True)     # indoor/outdoor
    main_skin_concern = models.CharField(max_length=60, blank=True)
    skin_concerns = models.JSONField(default=list)

    # ── Step 2: Skin Type ───────────────────────────────────────
    face_feel_after_wash  = models.CharField(max_length=30, blank=True)
    oiliness_timing       = models.CharField(max_length=30, blank=True)
    oily_zone             = models.CharField(max_length=30, blank=True)  # forehead/nose/chin/tzone
    pores_visible         = models.CharField(max_length=20, blank=True)
    skin_peels            = models.CharField(max_length=20, blank=True)
    sweats_heavily        = models.BooleanField(default=False)
    makeup_melts          = models.BooleanField(default=False)
    moisturizer_absorbs_fast = models.BooleanField(default=False)
    face_wash_freq        = models.CharField(max_length=20, blank=True)  # once/twice/thrice/more
    skin_changes_season   = models.BooleanField(default=False)
    told_skin_type        = models.CharField(max_length=30, blank=True)

    # ── Step 3: Acne Assessment ──────────────────────────────────
    has_pimples      = models.BooleanField(default=False)
    has_whiteheads   = models.BooleanField(default=False)
    has_blackheads   = models.BooleanField(default=False)
    has_painful_acne = models.BooleanField(default=False)
    has_acne_scars   = models.BooleanField(default=False)
    has_redness      = models.BooleanField(default=False)
    has_itching      = models.BooleanField(default=False)
    has_burning      = models.BooleanField(default=False)
    has_cystic_acne  = models.BooleanField(default=False)
    acne_severity    = models.CharField(max_length=20, choices=ACNE_SEVERITY_CHOICES, default='none')
    acne_duration    = models.CharField(max_length=30, blank=True)    # lt1m/1to6m/6to12m/gt1y
    acne_location    = models.JSONField(default=list)                  # forehead/nose/cheeks/chin/jawline/neck/back/chest
    picks_pimples    = models.BooleanField(default=False)
    acne_worsens_period   = models.BooleanField(default=False)
    acne_worsens_stress   = models.BooleanField(default=False)
    acne_worsens_dairy    = models.BooleanField(default=False)
    acne_worsens_oily_food = models.BooleanField(default=False)
    on_acne_medication    = models.BooleanField(default=False)
    visited_derm_for_acne = models.BooleanField(default=False)

    # ── Step 4: Pigmentation ────────────────────────────────────
    pigmentation_concerns = models.JSONField(default=list)
    tans_easily           = models.BooleanField(default=False)
    uneven_tone           = models.BooleanField(default=False)
    dark_spots_increased  = models.BooleanField(default=False)
    wears_sunscreen_daily = models.BooleanField(default=False)
    had_pigment_treatment = models.BooleanField(default=False)
    top_pigment_concern   = models.CharField(max_length=60, blank=True)

    # ── Step 5: Sensitive Skin ──────────────────────────────────
    sensitivity_symptoms  = models.JSONField(default=list)
    skin_stings_skincare  = models.BooleanField(default=False)
    skin_burns_sun        = models.BooleanField(default=False)
    has_eczema            = models.BooleanField(default=False)
    has_rosacea           = models.BooleanField(default=False)
    has_psoriasis         = models.BooleanField(default=False)

    # ── Step 6: Aging & Dryness ──────────────────────────────────
    aging_concerns        = models.JSONField(default=list)
    hydration_issues      = models.JSONField(default=list)
    has_neck_wrinkles     = models.BooleanField(default=False)
    skin_losing_firmness  = models.BooleanField(default=False)
    has_sagging           = models.BooleanField(default=False)
    uses_retinol          = models.BooleanField(default=False)
    flaky_skin            = models.BooleanField(default=False)
    rough_texture         = models.BooleanField(default=False)
    patchy_makeup         = models.BooleanField(default=False)
    dry_lips              = models.BooleanField(default=False)

    # ── Step 7: Under-Eye ────────────────────────────────────────
    has_dark_circles      = models.BooleanField(default=False)
    has_undereye_bags     = models.BooleanField(default=False)
    has_undereye_puffiness = models.BooleanField(default=False)
    dry_eyes              = models.BooleanField(default=False)
    rubs_eyes             = models.BooleanField(default=False)
    wears_contacts        = models.BooleanField(default=False)
    screen_hours          = models.CharField(max_length=10, blank=True)  # lt4/4to8/gt8

    # ── Step 8: Lifestyle ────────────────────────────────────────
    water_intake       = models.CharField(max_length=20, blank=True)
    sleep_hours        = models.CharField(max_length=20, choices=SLEEP_CHOICES, blank=True)
    stress_level       = models.CharField(max_length=20, choices=STRESS_CHOICES, blank=True)
    exercise           = models.CharField(max_length=20, blank=True)
    smoking            = models.BooleanField(default=False)
    alcohol            = models.CharField(max_length=20, blank=True)
    sun_exposure_daily = models.BooleanField(default=False)
    reapplies_sunscreen= models.BooleanField(default=False)
    pillowcase_change  = models.CharField(max_length=20, blank=True)   # daily/weekly/biweekly/rarely
    phone_cleaning     = models.CharField(max_length=20, blank=True)   # daily/weekly/rarely/never
    brush_cleaning     = models.CharField(max_length=20, blank=True)   # daily/weekly/monthly/rarely/never

    # ── Step 9: Diet ─────────────────────────────────────────────
    food_habits           = models.JSONField(default=list)
    eats_fruits_freq      = models.CharField(max_length=20, blank=True)  # daily/few/rarely/never
    eats_veg_freq         = models.CharField(max_length=20, blank=True)
    eats_dairy_freq       = models.CharField(max_length=20, blank=True)
    eats_sugar_freq       = models.CharField(max_length=20, blank=True)
    eats_fried_freq       = models.CharField(max_length=20, blank=True)
    drinks_softdrinks     = models.BooleanField(default=False)
    drinks_coffee_tea     = models.BooleanField(default=False)
    takes_supplements     = models.BooleanField(default=False)
    food_affects_skin     = models.BooleanField(default=False)

    # ── Step 10: Skincare Routine ────────────────────────────────
    morning_cleanser      = models.BooleanField(default=False)
    moisturizer           = models.BooleanField(default=False)
    sunscreen             = models.BooleanField(default=False)
    night_routine         = models.BooleanField(default=False)
    uses_vitamin_c        = models.BooleanField(default=False)
    uses_niacinamide      = models.BooleanField(default=False)
    uses_exfoliation      = models.BooleanField(default=False)
    uses_hyaluronic_acid  = models.BooleanField(default=False)
    uses_aha_bha          = models.BooleanField(default=False)
    uses_face_masks       = models.BooleanField(default=False)
    removes_makeup_before_sleep = models.BooleanField(default=False)
    routine_satisfied     = models.BooleanField(default=False)
    cleanser_name         = models.CharField(max_length=100, blank=True)
    moisturizer_name      = models.CharField(max_length=100, blank=True)
    sunscreen_spf         = models.CharField(max_length=10, blank=True)
    active_ingredients    = models.JSONField(default=list)   # vitamin_c/niacinamide/retinol/salicylic/ha

    # ── Step 11: Makeup Habits ───────────────────────────────────
    wears_makeup_daily    = models.BooleanField(default=False)
    wears_foundation      = models.BooleanField(default=False)
    wears_concealer       = models.BooleanField(default=False)
    wears_primer          = models.BooleanField(default=False)
    wears_setting_spray   = models.BooleanField(default=False)
    makeup_items_used     = models.JSONField(default=list)   # full list
    foundation_type       = models.CharField(max_length=30, blank=True)  # liquid/powder/stick/bb/cc
    makeup_oxidizes       = models.BooleanField(default=False)
    makeup_separates      = models.BooleanField(default=False)
    preferred_finish      = models.CharField(max_length=20, blank=True)  # matte/dewy/satin/natural
    cleans_brushes_regularly = models.BooleanField(default=False)
    sleeps_with_makeup    = models.CharField(max_length=20, blank=True)
    had_makeup_allergy    = models.BooleanField(default=False)
    makeup_budget         = models.CharField(max_length=20, blank=True, choices=BUDGET_CHOICES)
    preferred_makeup_brands = models.CharField(max_length=200, blank=True)

    # ── Step 12: Medical History ─────────────────────────────────
    is_pregnant           = models.BooleanField(default=False)
    is_breastfeeding      = models.BooleanField(default=False)
    has_pcos              = models.BooleanField(default=False)
    has_thyroid           = models.BooleanField(default=False)
    has_diabetes          = models.BooleanField(default=False)
    on_hormonal_meds      = models.BooleanField(default=False)
    on_skin_medication    = models.BooleanField(default=False)
    uses_isotretinoin     = models.BooleanField(default=False)
    uses_steroids         = models.BooleanField(default=False)
    under_derm_treatment  = models.BooleanField(default=False)
    known_allergies       = models.CharField(max_length=200, blank=True)
    medical_notes         = models.TextField(blank=True)

    # ── Step 13: Product Preferences ────────────────────────────
    skincare_budget       = models.CharField(max_length=20, blank=True, choices=BUDGET_CHOICES)
    prefers_korean        = models.BooleanField(default=False)
    prefers_organic       = models.BooleanField(default=False)
    prefers_fragrance_free = models.BooleanField(default=False)
    prefers_vegan         = models.BooleanField(default=False)
    prefers_cruelty_free  = models.BooleanField(default=False)
    preferred_textures    = models.JSONField(default=list)   # gel/cream/lotion/serum/oil
    ingredients_to_avoid  = models.JSONField(default=list)   # parabens/sulphates/fragrance/alcohol/silicones
    trusted_brands        = models.CharField(max_length=300, blank=True)
    shops_online          = models.BooleanField(default=True)
    tier_preference       = models.CharField(max_length=20, blank=True)  # affordable/premium/luxury
    wants_ayurvedic       = models.BooleanField(default=False)
    ayurvedic_ingredients = models.JSONField(default=list)   # turmeric/neem/rose/sandalwood/aloe/ashwagandha

    # ── Step 14: Under-Eye + Acne Marks (extended) ───────────────
    # (covered under steps 3, 6, 7 fields — additional UI flags)
    wants_undereye_focus  = models.BooleanField(default=False)
    wants_acne_mark_focus = models.BooleanField(default=False)

    # ── Step 15: AI Goals ────────────────────────────────────────
    top_priority          = models.CharField(max_length=60, blank=True)  # glow/acne/aging/pigment/hydration/makeup
    routine_detail_level  = models.CharField(max_length=20, blank=True, choices=ROUTINE_DETAIL_CHOICES)
    wants_ingredient_explanations = models.BooleanField(default=False)
    open_to_actives       = models.BooleanField(default=False)
    wants_makeup_matched  = models.BooleanField(default=False)
    wants_kbeauty_suggestions = models.BooleanField(default=False)
    wants_organic_alternatives = models.BooleanField(default=False)
    wants_progress_reminders   = models.BooleanField(default=False)

    # ── Computed Results ─────────────────────────────────────────
    skin_type_result    = models.CharField(max_length=20, choices=SKIN_TYPE_CHOICES, blank=True)
    primary_concern     = models.CharField(max_length=60, blank=True)
    recommended_routine = models.JSONField(default=dict)
    ai_summary          = models.TextField(blank=True)

    completed    = models.BooleanField(default=False)
    current_step = models.PositiveSmallIntegerField(default=1)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Skin Session'

    def __str__(self):
        user_str = self.user.username if self.user else 'anon'
        return f"[{self.skin_type_result or 'incomplete'}] {user_str} — {self.created_at:%d %b %Y}"

    def compute_skin_type(self):
        """Rule-based skin type computation."""
        feel = self.face_feel_after_wash
        oils = self.oiliness_timing
        if feel == 'oily' and oils in ('afternoon', 'within2h'):
            return 'oily'
        if feel == 'tight':
            return 'dry'
        if feel == 'combination' or oils == 'afternoon':
            return 'combination'
        if self.sensitivity_symptoms or self.has_rosacea or self.has_eczema:
            return 'sensitive'
        return 'normal'

    def compute_acne_severity(self):
        """Rule-based acne severity from step 3."""
        count = sum([
            self.has_pimples, self.has_whiteheads, self.has_blackheads,
            self.has_painful_acne, self.has_cystic_acne,
        ])
        if self.has_cystic_acne:
            return 'severe'
        if count >= 3:
            return 'moderate'
        if count >= 1:
            return 'mild'
        return 'none'
