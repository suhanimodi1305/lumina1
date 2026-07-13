"""
Lumina AI Beauty Advisor — Smart Diagnostic Quiz Engine
~40 questions across 11 sections with conditional logic.
Sections: Personal Info → Skin Concerns → Skin Type → Acne (conditional) →
          Pigmentation (conditional) → Sensitive (conditional) → Lifestyle →
          Current Routine → Makeup (optional) → Product Preferences → AI Analysis
"""

# ─────────────────────────────────────────────────────────────────────────────
#  SECTION / STEP DEFINITIONS
#  Each step = one page. Type: 'single' | 'multi' | 'radio_yn' | 'text' | 'photo'
# ─────────────────────────────────────────────────────────────────────────────

# ── SECTION 1 — PERSONAL INFO (4 questions, always shown) ────────────────────

S1_PERSONAL = {
    'id': 1, 'section': 1, 'section_label': 'Personal Information',
    'title': 'About You', 'icon': '👤',
    'sub': 'Quick personal details so we can tailor everything to you.',
    'questions': [
        {
            'name': 'age_group', 'label': 'How old are you?', 'type': 'single', 'required': True,
            'options': [
                {'value': 'under18', 'label': 'Under 18',  'icon': '🧒'},
                {'value': '18_24',   'label': '18 – 24',   'icon': '🧑'},
                {'value': '25_34',   'label': '25 – 34',   'icon': '👤'},
                {'value': '35_44',   'label': '35 – 44',   'icon': '🧔'},
                {'value': '45_54',   'label': '45 – 54',   'icon': '👩'},
                {'value': '55plus',  'label': '55+',        'icon': '🧓'},
            ],
        },
        {
            'name': 'gender', 'label': 'How do you identify?', 'type': 'single', 'required': True,
            'options': [
                {'value': 'female',         'label': 'Female',            'icon': '👩'},
                {'value': 'male',           'label': 'Male',              'icon': '👨'},
                {'value': 'non_binary',     'label': 'Non-binary',        'icon': '🌈'},
                {'value': 'prefer_not',     'label': 'Prefer not to say', 'icon': '🤐'},
            ],
        },
        {
            'name': 'climate', 'label': 'What climate do you live in?', 'type': 'single', 'required': True,
            'options': [
                {'value': 'hot_humid',  'label': 'Hot & Humid',  'icon': '🌴', 'desc': 'Tropical — sweaty, sticky'},
                {'value': 'hot_dry',    'label': 'Hot & Dry',    'icon': '🏜️', 'desc': 'Arid — low humidity'},
                {'value': 'cold',       'label': 'Cold',          'icon': '❄️', 'desc': 'Cold winters, dry air'},
                {'value': 'temperate',  'label': 'Temperate',    'icon': '🌤️', 'desc': 'Mild seasons'},
                {'value': 'humid',      'label': 'Humid',         'icon': '💧', 'desc': 'High humidity, no extreme heat'},
            ],
        },
        {
            'name': 'pregnant_bf', 'label': 'Are you pregnant or breastfeeding?',
            'type': 'single', 'required': False, 'hint': 'This affects which ingredients are safe for you.',
            'options': [
                {'value': 'no',          'label': 'No',               'icon': '🚫'},
                {'value': 'pregnant',    'label': 'Pregnant',         'icon': '🤰'},
                {'value': 'breastfeeding','label': 'Breastfeeding',   'icon': '👶'},
                {'value': 'trying',      'label': 'Trying to conceive','icon': '💗'},
            ],
        },
    ],
}

# ── SECTION 2 — MAIN SKIN CONCERNS (1 question, max 3 selections) ─────────────

S2_CONCERNS = {
    'id': 2, 'section': 2, 'section_label': 'Main Skin Concerns',
    'title': 'Your Skin Concerns', 'icon': '🔍',
    'sub': 'Tell us what\'s bothering your skin the most.',
    'questions': [
        {
            'name': 'skin_concerns',
            'label': 'Select your top concerns', 'type': 'multi', 'max_select': 3,
            'required': True, 'hint': 'Choose up to 3 — these drive your entire recommendation.',
            'options': [
                {'value': 'acne',         'label': '🔴 Acne',              'desc': 'Pimples, breakouts'},
                {'value': 'acne_scars',   'label': '🔶 Acne Scars',        'desc': 'Marks left by pimples'},
                {'value': 'dark_spots',   'label': '🟤 Dark Spots',        'desc': 'Post-acne or sun spots'},
                {'value': 'pigmentation', 'label': '🌑 Pigmentation',      'desc': 'Melasma, uneven patches'},
                {'value': 'oily_skin',    'label': '💧 Oily Skin',         'desc': 'Shine, greasy T-zone'},
                {'value': 'dry_skin',     'label': '🏜️ Dry Skin',          'desc': 'Tight, flaky, rough'},
                {'value': 'sensitive',    'label': '🌸 Sensitive Skin',    'desc': 'Stinging, reactions'},
                {'value': 'large_pores',  'label': '🔵 Large Pores',       'desc': 'Visible pores'},
                {'value': 'wrinkles',     'label': '〰️ Wrinkles',          'desc': 'Deep lines'},
                {'value': 'fine_lines',   'label': '✏️ Fine Lines',         'desc': 'Early aging signs'},
                {'value': 'dull_skin',    'label': '😐 Dull Skin',         'desc': 'No glow, tired-looking'},
                {'value': 'redness',      'label': '🌹 Redness',           'desc': 'Flushing, rosacea'},
                {'value': 'dark_circles', 'label': '👁️ Dark Circles',      'desc': 'Under-eye darkness'},
                {'value': 'blackheads',   'label': '⚫ Blackheads',        'desc': 'Open comedones'},
                {'value': 'whiteheads',   'label': '⚪ Whiteheads',        'desc': 'Closed comedones'},
                {'value': 'uneven_tone',  'label': '🎭 Uneven Skin Tone',  'desc': 'Patchy, inconsistent'},
                {'value': 'sun_damage',   'label': '☀️ Sun Damage',        'desc': 'Spots, texture from UV'},
            ],
        },
        {
            'name': 'skin_conditions', 'type': 'text', 'required': False,
            'label': 'Any skin conditions diagnosed by a doctor?',
            'placeholder': 'e.g. Eczema, Rosacea, Psoriasis, or leave blank',
        },
        {
            'name': 'known_allergies', 'type': 'text', 'required': False,
            'label': 'Any known allergies to skincare or cosmetics?',
            'placeholder': 'e.g. Fragrance, Parabens, Lanolin, or leave blank',
        },
    ],
}

# ── SECTION 3 — SKIN TYPE (4 questions, always shown) ────────────────────────

S3_SKIN_TYPE = {
    'id': 3, 'section': 3, 'section_label': 'Skin Type',
    'title': 'Your Skin Type', 'icon': '💧',
    'sub': 'Understanding your skin\'s baseline behaviour.',
    'questions': [
        {
            'name': 'skin_feel', 'required': True,
            'label': 'How does your skin feel 30 minutes after washing?', 'type': 'single',
            'options': [
                {'value': 'very_dry',    'label': 'Very Dry & Tight',      'icon': '🏜️', 'desc': 'Feels stretched, uncomfortable'},
                {'value': 'normal',      'label': 'Normal & Comfortable',  'icon': '✅',  'desc': 'Not tight, not oily'},
                {'value': 'combination', 'label': 'Combination',           'icon': '☯️',  'desc': 'Dry cheeks, oily T-zone'},
                {'value': 'oily',        'label': 'Oily',                  'icon': '💦',  'desc': 'Shiny, greasy quickly'},
            ],
        },
        {
            'name': 'oily_zone', 'required': True,
            'label': 'Which part of your face becomes oily first?', 'type': 'single',
            'options': [
                {'value': 'tzone',    'label': 'T-Zone',      'icon': '☯️', 'desc': 'Forehead + nose + chin'},
                {'value': 'cheeks',   'label': 'Cheeks',      'icon': '😊', 'desc': 'Side of face'},
                {'value': 'all',      'label': 'Entire Face', 'icon': '💦', 'desc': 'Everything gets oily'},
                {'value': 'never',    'label': 'Never Oily',  'icon': '🌵', 'desc': 'My skin stays dry'},
            ],
        },
        {
            'name': 'skin_tight', 'required': True,
            'label': 'Does your skin feel tight after cleansing?', 'type': 'single',
            'options': [
                {'value': 'yes',       'label': 'Yes',        'icon': '😬'},
                {'value': 'no',        'label': 'No',         'icon': '😊'},
                {'value': 'sometimes', 'label': 'Sometimes',  'icon': '🤔'},
            ],
        },
        {
            'name': 'pores_visible', 'required': True,
            'label': 'Are your pores visible?', 'type': 'single',
            'options': [
                {'value': 'yes',      'label': 'Yes, clearly', 'icon': '🔬'},
                {'value': 'no',       'label': 'No',           'icon': '✨'},
                {'value': 'nose_only','label': 'Only on nose', 'icon': '👃'},
            ],
        },
    ],
}

# ── SECTION 4 — ACNE (conditional: shown only if 'acne' in skin_concerns) ────

S4_ACNE = {
    'id': 4, 'section': 4, 'section_label': 'Acne Assessment',
    'title': 'Acne Details', 'icon': '🔬',
    'sub': 'A few targeted questions to build your acne action plan.',
    'condition': {'field': 'skin_concerns', 'contains': 'acne'},
    'questions': [
        {
            'name': 'acne_severity', 'required': True,
            'label': 'How severe is your acne?', 'type': 'single',
            'options': [
                {'value': 'mild',     'label': 'Mild',     'icon': '🟡', 'desc': 'A few spots occasionally'},
                {'value': 'moderate', 'label': 'Moderate', 'icon': '🟠', 'desc': 'Regular breakouts, noticeable'},
                {'value': 'severe',   'label': 'Severe',   'icon': '🔴', 'desc': 'Widespread, painful, cystic'},
            ],
        },
        {
            'name': 'acne_location', 'required': True,
            'label': 'Where is your acne mainly?', 'type': 'multi',
            'options': [
                {'value': 'forehead', 'label': 'Forehead', 'icon': '🙆'},
                {'value': 'cheeks',   'label': 'Cheeks',   'icon': '😊'},
                {'value': 'chin',     'label': 'Chin',     'icon': '😏'},
                {'value': 'jawline',  'label': 'Jawline',  'icon': '🧔'},
                {'value': 'nose',     'label': 'Nose',     'icon': '👃'},
                {'value': 'back',     'label': 'Back',     'icon': '🔙'},
            ],
        },
        {
            'name': 'acne_leaves_marks', 'required': True,
            'label': 'Do your pimples leave marks or scars?', 'type': 'single',
            'options': [
                {'value': 'yes', 'label': 'Yes', 'icon': '✅'},
                {'value': 'no',  'label': 'No',  'icon': '🚫'},
            ],
        },
        {
            'name': 'acne_painful', 'required': True,
            'label': 'Do you get painful, deep acne (cysts)?', 'type': 'single',
            'options': [
                {'value': 'yes', 'label': 'Yes — painful and deep', 'icon': '😣'},
                {'value': 'no',  'label': 'No — surface level',    'icon': '😌'},
            ],
        },
    ],
}

# ── SECTION 5 — PIGMENTATION (conditional: dark_spots or pigmentation) ───────

S5_PIGMENT = {
    'id': 5, 'section': 5, 'section_label': 'Pigmentation',
    'title': 'Pigmentation & Dark Spots', 'icon': '☀️',
    'sub': 'Let\'s understand your pigmentation to target it correctly.',
    'condition': {'field': 'skin_concerns', 'contains_any': ['dark_spots', 'pigmentation', 'acne_scars', 'sun_damage']},
    'questions': [
        {
            'name': 'spot_duration', 'required': True,
            'label': 'How long have you had these dark spots or patches?', 'type': 'single',
            'options': [
                {'value': 'new',     'label': 'Just appeared (< 3 months)', 'icon': '🆕'},
                {'value': 'months',  'label': '3–12 months',                'icon': '📆'},
                {'value': 'years',   'label': 'More than a year',           'icon': '⏳'},
            ],
        },
        {
            'name': 'sunscreen_daily', 'required': True,
            'label': 'Do you wear sunscreen every day?', 'type': 'single',
            'options': [
                {'value': 'yes',       'label': 'Yes, always',     'icon': '☀️'},
                {'value': 'sometimes', 'label': 'Sometimes',       'icon': '🤔'},
                {'value': 'no',        'label': 'No, rarely/never','icon': '🚫'},
            ],
        },
        {
            'name': 'tans_easily', 'required': True,
            'label': 'Does your skin tan or darken easily in the sun?', 'type': 'single',
            'options': [
                {'value': 'yes', 'label': 'Yes, quickly', 'icon': '🌞'},
                {'value': 'no',  'label': 'Not really',   'icon': '🌤️'},
            ],
        },
    ],
}

# ── SECTION 6 — SENSITIVE SKIN (conditional) ─────────────────────────────────

S6_SENSITIVE = {
    'id': 6, 'section': 6, 'section_label': 'Sensitive Skin',
    'title': 'Skin Sensitivity', 'icon': '🌸',
    'sub': 'Understanding your reactivity keeps your skin safe.',
    'condition': {'field': 'skin_concerns', 'contains_any': ['sensitive', 'redness']},
    'questions': [
        {
            'name': 'skin_stings', 'required': True,
            'label': 'Does skincare sting or burn when applied?', 'type': 'single',
            'options': [
                {'value': 'always',    'label': 'Yes, always',    'icon': '🔥'},
                {'value': 'sometimes', 'label': 'Sometimes',      'icon': '🤔'},
                {'value': 'no',        'label': 'No',             'icon': '✅'},
            ],
        },
        {
            'name': 'reddens_easily', 'required': True,
            'label': 'Does your skin redden or flush easily?', 'type': 'single',
            'options': [
                {'value': 'yes', 'label': 'Yes, very easily', 'icon': '🌹'},
                {'value': 'no',  'label': 'Not usually',      'icon': '✅'},
            ],
        },
        {
            'name': 'had_reactions', 'required': True,
            'label': 'Have you had allergic reactions to skincare before?', 'type': 'single',
            'options': [
                {'value': 'yes', 'label': 'Yes', 'icon': '⚠️'},
                {'value': 'no',  'label': 'No',  'icon': '✅'},
            ],
        },
    ],
}

# ── SECTION 7 — LIFESTYLE (always shown) ─────────────────────────────────────

S7_LIFESTYLE = {
    'id': 7, 'section': 7, 'section_label': 'Lifestyle',
    'title': 'Your Daily Lifestyle', 'icon': '🏃',
    'sub': 'Lifestyle is the hidden driver behind most skin issues.',
    'questions': [
        {
            'name': 'water_glasses', 'required': True,
            'label': 'How many glasses of water do you drink daily?', 'type': 'single',
            'options': [
                {'value': 'lt4',  'label': 'Under 4',    'icon': '🏜️'},
                {'value': '4to6', 'label': '4 – 6',      'icon': '💧'},
                {'value': '6to8', 'label': '6 – 8',      'icon': '✅'},
                {'value': 'gt8',  'label': 'More than 8','icon': '💦'},
            ],
        },
        {
            'name': 'sleep_hours', 'required': True,
            'label': 'How many hours of sleep do you get?', 'type': 'single',
            'options': [
                {'value': 'lt6',  'label': 'Under 6 hrs',   'icon': '😴'},
                {'value': '6to7', 'label': '6 – 7 hrs',     'icon': '🌙'},
                {'value': '7to9', 'label': '7 – 9 hrs',     'icon': '✅'},
                {'value': 'gt9',  'label': '9+ hrs',        'icon': '☀️'},
            ],
        },
        {
            'name': 'stress_level', 'required': True,
            'label': 'How would you rate your stress level?', 'type': 'single',
            'options': [
                {'value': 'low',    'label': 'Low',    'icon': '😌'},
                {'value': 'medium', 'label': 'Medium', 'icon': '😐'},
                {'value': 'high',   'label': 'High',   'icon': '😰'},
            ],
        },
        {
            'name': 'smokes', 'required': False,
            'label': 'Do you smoke?', 'type': 'single',
            'options': [
                {'value': 'no',         'label': 'No',              'icon': '🚭'},
                {'value': 'yes',        'label': 'Yes',             'icon': '🚬'},
                {'value': 'ex_smoker',  'label': 'Ex-smoker',       'icon': '⛔'},
            ],
        },
        {
            'name': 'alcohol', 'required': False,
            'label': 'Do you drink alcohol?', 'type': 'single',
            'options': [
                {'value': 'no',         'label': 'No',          'icon': '🚫'},
                {'value': 'occasional', 'label': 'Occasionally', 'icon': '🍷'},
                {'value': 'regular',    'label': 'Regularly',   'icon': '🍺'},
            ],
        },
    ],
}

# ── SECTION 8 — CURRENT ROUTINE (always shown) ───────────────────────────────

S8_ROUTINE = {
    'id': 8, 'section': 8, 'section_label': 'Current Skincare Routine',
    'title': 'Your Current Routine', 'icon': '🧴',
    'sub': 'What are you already using? We\'ll build on — or fix — what\'s there.',
    'questions': [
        {
            'name': 'current_products', 'required': False,
            'label': 'Which products do you currently use?', 'type': 'multi',
            'options': [
                {'value': 'cleanser',   'label': 'Cleanser',        'icon': '🧼'},
                {'value': 'toner',      'label': 'Toner',           'icon': '💧'},
                {'value': 'serum',      'label': 'Serum',           'icon': '⚗️'},
                {'value': 'moisturizer','label': 'Moisturizer',     'icon': '🫙'},
                {'value': 'sunscreen',  'label': 'Sunscreen / SPF', 'icon': '☀️'},
                {'value': 'face_mask',  'label': 'Face Mask',       'icon': '🎭'},
                {'value': 'none',       'label': 'None at all',     'icon': '❌'},
            ],
        },
        {
            'name': 'active_ingredients', 'required': False,
            'label': 'Which active ingredients are you currently using?', 'type': 'multi',
            'hint': 'Check your product labels — or select None if unsure.',
            'options': [
                {'value': 'vitamin_c',    'label': 'Vitamin C',       'icon': '🍊'},
                {'value': 'niacinamide',  'label': 'Niacinamide',     'icon': '🔬'},
                {'value': 'salicylic',    'label': 'Salicylic Acid',  'icon': '⚗️'},
                {'value': 'retinol',      'label': 'Retinol',         'icon': '✨'},
                {'value': 'hyaluronic',   'label': 'Hyaluronic Acid', 'icon': '💧'},
                {'value': 'aha_bha',      'label': 'AHA / BHA',       'icon': '🧪'},
                {'value': 'none',         'label': 'None / Unsure',   'icon': '❓'},
            ],
        },
    ],
}

# ── SECTION 9 — MAKEUP (optional) ────────────────────────────────────────────

S9_MAKEUP = {
    'id': 9, 'section': 9, 'section_label': 'Makeup',
    'title': 'Makeup Preferences', 'icon': '💄',
    'sub': 'Optional — skip if makeup isn\'t relevant for you.',
    'optional_section': True,
    'questions': [
        {
            'name': 'wears_makeup', 'required': False,
            'label': 'Do you wear makeup regularly?', 'type': 'single',
            'options': [
                {'value': 'yes',   'label': 'Yes, daily',       'icon': '💄'},
                {'value': 'occ',   'label': 'Occasionally',     'icon': '🎉'},
                {'value': 'no',    'label': 'No / Rarely',      'icon': '🚫'},
            ],
        },
        {
            'name': 'skin_tone', 'required': False,
            'label': 'What is your skin tone?', 'type': 'single',
            'hint': 'This helps us match you to the right foundation shade.',
            'options': [
                {'value': 'fair',   'label': 'Fair',   'icon': '🌸', 'desc': 'Very light, porcelain skin'},
                {'value': 'light',  'label': 'Light',  'icon': '🌼', 'desc': 'Light but not the lightest'},
                {'value': 'medium', 'label': 'Medium', 'icon': '🌻', 'desc': 'Wheatish, medium brown'},
                {'value': 'tan',    'label': 'Tan',    'icon': '🌴', 'desc': 'Tan / dusky'},
                {'value': 'deep',   'label': 'Deep',   'icon': '🍫', 'desc': 'Deep brown / very dark'},
            ],
        },
        {
            'name': 'undertone', 'required': False,
            'label': 'What is your skin undertone?', 'type': 'single',
            'hint': 'Check your inner wrist veins — blue/purple = cool, green = warm, both = neutral.',
            'options': [
                {'value': 'warm',    'label': 'Warm',    'icon': '🌅', 'desc': 'Yellow / golden / peachy undertone'},
                {'value': 'cool',    'label': 'Cool',    'icon': '🌊', 'desc': 'Pink / red / bluish undertone'},
                {'value': 'neutral', 'label': 'Neutral', 'icon': '☯️', 'desc': 'Mix of warm and cool'},
                {'value': 'olive',   'label': 'Olive',   'icon': '🫒', 'desc': 'Greenish / yellow-green cast'},
            ],
        },
        {
            'name': 'makeup_finish', 'required': False,
            'label': 'What finish do you prefer?', 'type': 'single',
            'show_if': {'field': 'wears_makeup', 'not_in': ['no']},
            'options': [
                {'value': 'matte',    'label': 'Matte',    'icon': '🔲', 'desc': 'No shine, oil control'},
                {'value': 'dewy',     'label': 'Dewy',     'icon': '✨', 'desc': 'Glowy, skin-like finish'},
                {'value': 'natural',  'label': 'Natural',  'icon': '🌿', 'desc': 'Barely-there, skin forward'},
                {'value': 'satin',    'label': 'Satin',    'icon': '🌟', 'desc': 'Between matte and dewy'},
            ],
        },
        {
            'name': 'makeup_budget', 'required': False,
            'label': 'What is your makeup budget?', 'type': 'single',
            'show_if': {'field': 'wears_makeup', 'not_in': ['no']},
            'options': [
                {'value': 'lt500',    'label': 'Under ₹500',      'icon': '🪙'},
                {'value': '500_1000', 'label': '₹500 – ₹1,000',  'icon': '💳'},
                {'value': '1000_3000','label': '₹1,000 – ₹3,000','icon': '💎'},
                {'value': 'gt3000',   'label': '₹3,000+',         'icon': '👑'},
            ],
        },
        {
            'name': 'preferred_makeup_brands', 'required': False,
            'label': 'Which makeup brands do you prefer or use?', 'type': 'multi',
            'show_if': {'field': 'wears_makeup', 'not_in': ['no']},
            'hint': 'Select all brands you already use or are open to trying.',
            'options': [
                # ── Local / Budget-Friendly Indian Brands ──────────────────
                {'value': 'mars',        'label': 'MARS Cosmetics',     'icon': '🔴', 'desc': 'Affordable, wide shade range'},
                {'value': 'faces_canada','label': 'Faces Canada',       'icon': '🍁', 'desc': 'Budget-friendly, Indian market'},
                {'value': 'miss_claire', 'label': 'Miss Claire',        'icon': '🌸', 'desc': 'Drugstore, easy to find'},
                {'value': 'blue_heaven', 'label': 'Blue Heaven',        'icon': '💙', 'desc': 'Super affordable local brand'},
                {'value': 'ADS',         'label': 'ADS Cosmetics',      'icon': '✨', 'desc': 'Local budget brand'},

                # ── Mid-Range Indian & India-Popular Brands ────────────────
                {'value': 'lakme',       'label': 'Lakmé',              'icon': '🌺', 'desc': 'Most trusted Indian brand'},
                {'value': 'colorbar',    'label': 'Colorbar',           'icon': '🎨', 'desc': 'Premium feel, mid price'},
                {'value': 'sugar',       'label': 'SUGAR Cosmetics',    'icon': '🍬', 'desc': 'Trendy, long-wear formulas'},
                {'value': 'myglamm',     'label': 'MyGlamm',            'icon': '💋', 'desc': 'D2C brand, wide range'},
                {'value': 'nykaa',       'label': 'Nykaa Cosmetics',    'icon': '🛍️', 'desc': 'In-house Nykaa brand'},
                {'value': 'renee',       'label': 'RENÉE Cosmetics',    'icon': '🌹', 'desc': 'Growing D2C Indian brand'},
                {'value': 'swiss_beauty','label': 'Swiss Beauty',       'icon': '🇨🇭', 'desc': 'Quality at mid price'},
                {'value': 'insight',     'label': 'Insight Cosmetics',  'icon': '🔬', 'desc': 'Professional finish, mid-range'},

                # ── Mass-Market International (widely sold in India) ────────
                {'value': 'maybelline',  'label': 'Maybelline',         'icon': '🟡', 'desc': 'Global brand, widely available'},
                {'value': 'loreal_paris','label': "L'Oréal Paris",      'icon': '💛', 'desc': 'Trusted, easily available'},
                {'value': 'revlon',      'label': 'Revlon',             'icon': '💅', 'desc': 'Classic international brand'},
                {'value': 'nyx',         'label': 'NYX Professional',   'icon': '⚡', 'desc': 'Professional-grade, mid price'},

                # ── Other ──────────────────────────────────────────────────
                {'value': 'other',       'label': 'Other / No preference', 'icon': '🤷'},
            ],
        },
    ],
}

# ── SECTION 10 — PRODUCT PREFERENCES (always shown) ──────────────────────────

S10_PREFS = {
    'id': 10, 'section': 10, 'section_label': 'Product Preferences',
    'title': 'What You\'re Looking For', 'icon': '🛍️',
    'sub': 'We\'ll match recommendations to exactly what you want.',
    'questions': [
        {
            'name': 'recommendation_type', 'required': True,
            'label': 'What type of recommendations do you want?', 'type': 'multi',
            'hint': 'Select all that interest you.',
            'options': [
                {'value': 'korean',   'label': '🇰🇷 Korean Skincare',        'desc': 'Glass skin, K-beauty'},
                {'value': 'organic',  'label': '🌿 Organic / Natural',       'desc': 'Clean, plant-based'},
                {'value': 'drugstore','label': '💊 Drugstore / Affordable',  'desc': 'Budget, pharmacy brands'},
                {'value': 'premium',  'label': '💎 Premium / Luxury',        'desc': 'High-end brands'},
                {'value': 'makeup',   'label': '💄 Makeup Products',         'desc': 'Foundation, lips, eyes'},
            ],
        },
        {
            'name': 'skincare_budget', 'required': True,
            'label': 'What is your monthly skincare budget?', 'type': 'single',
            'options': [
                {'value': 'lt500',     'label': 'Under ₹500',       'icon': '🪙'},
                {'value': '500_2000',  'label': '₹500 – ₹2,000',   'icon': '💳'},
                {'value': '2000_5000', 'label': '₹2,000 – ₹5,000', 'icon': '💎'},
                {'value': 'gt5000',    'label': '₹5,000+',          'icon': '👑'},
            ],
        },
        {
            'name': 'fragrance_free', 'required': False,
            'label': 'Do you prefer fragrance-free products?', 'type': 'single',
            'options': [
                {'value': 'yes',   'label': 'Yes, strictly', 'icon': '🚫'},
                {'value': 'pref',  'label': 'Prefer it',     'icon': '🤍'},
                {'value': 'no',    'label': 'No preference', 'icon': '😊'},
            ],
        },
        {
            'name': 'vegan_cf', 'required': False,
            'label': 'Do you prefer vegan or cruelty-free products?', 'type': 'single',
            'options': [
                {'value': 'vegan_cf', 'label': 'Vegan AND cruelty-free',  'icon': '🌱'},
                {'value': 'cf_only',  'label': 'Cruelty-free only',       'icon': '🐰'},
                {'value': 'no',       'label': 'No preference',           'icon': '😊'},
            ],
        },
    ],
}

# ── SECTION 11 — AI PHOTO ANALYSIS (always shown) ────────────────────────────

S11_PHOTO = {
    'id': 11, 'section': 11, 'section_label': 'AI Analysis',
    'title': 'AI Skin Analysis', 'icon': '📸',
    'sub': 'Upload a clear selfie for AI-powered skin analysis.',
    'questions': [
        {
            'name': 'selfie', 'required': False, 'type': 'photo',
            'label': 'Upload a clear selfie (no makeup, natural light)',
            'hint': 'For best results: no makeup, natural daylight, front-facing camera.',
        },
        {
            'name': 'wearing_makeup_photo', 'required': False,
            'label': 'Are you wearing makeup in the photo?', 'type': 'single',
            'show_if': {'field': 'selfie', 'has_value': True},
            'options': [
                {'value': 'yes', 'label': 'Yes', 'icon': '💄'},
                {'value': 'no',  'label': 'No',  'icon': '✅'},
            ],
        },
        {
            'name': 'photo_natural_light', 'required': False,
            'label': 'Is the photo taken in natural light?', 'type': 'single',
            'show_if': {'field': 'selfie', 'has_value': True},
            'options': [
                {'value': 'yes', 'label': 'Yes — near a window / outdoors', 'icon': '☀️'},
                {'value': 'no',  'label': 'No — indoor / artificial light',  'icon': '💡'},
            ],
        },
        {
            'name': 'photo_consent', 'required': False,
            'label': 'Do you consent to AI analysing your uploaded photo?', 'type': 'single',
            'hint': 'Your image is processed locally and never stored or shared.',
            'show_if': {'field': 'selfie', 'has_value': True},
            'options': [
                {'value': 'yes', 'label': 'Yes, I consent', 'icon': '✅'},
                {'value': 'no',  'label': 'No, skip photo analysis', 'icon': '🔒'},
            ],
        },
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
#  STEP SEQUENCE LOGIC — evaluates conditions and returns ordered list of steps
# ─────────────────────────────────────────────────────────────────────────────

ALL_STEPS = [S1_PERSONAL, S2_CONCERNS, S3_SKIN_TYPE, S4_ACNE, S5_PIGMENT,
             S6_SENSITIVE, S7_LIFESTYLE, S8_ROUTINE, S9_MAKEUP, S10_PREFS, S11_PHOTO]


def _condition_met(step: dict, answers: dict) -> bool:
    """Check if a conditional step should be shown given current answers."""
    cond = step.get('condition')
    if not cond:
        return True
    field_val = answers.get(cond['field'], [])
    if isinstance(field_val, str):
        field_val = [field_val]
    if 'contains' in cond:
        return cond['contains'] in field_val
    if 'contains_any' in cond:
        return any(v in field_val for v in cond['contains_any'])
    return True


def get_active_steps(answers: dict) -> list:
    """Return the ordered list of steps that should be shown for these answers."""
    return [s for s in ALL_STEPS if _condition_met(s, answers)]


def get_step_by_position(answers: dict, position: int):
    """Return step at 1-based position in the active step list, or None if out of range."""
    steps = get_active_steps(answers)
    if 1 <= position <= len(steps):
        return steps[position - 1], len(steps)
    return None, len(steps)


def is_last_step(answers: dict, position: int) -> bool:
    """True if this position is the final active step."""
    _, total = get_step_by_position(answers, position)
    return position >= total


# ─────────────────────────────────────────────────────────────────────────────
#  ANALYSIS ENGINE — converts all answers → full AI recommendation output
# ─────────────────────────────────────────────────────────────────────────────

# Issue weight and category mapping
CONCERN_META = {
    'acne':         {'label': 'Acne',             'severity_w': 3, 'category': 'acne'},
    'acne_scars':   {'label': 'Acne Scars',        'severity_w': 2, 'category': 'pigment'},
    'dark_spots':   {'label': 'Dark Spots',        'severity_w': 2, 'category': 'pigment'},
    'pigmentation': {'label': 'Pigmentation',      'severity_w': 3, 'category': 'pigment'},
    'oily_skin':    {'label': 'Oily Skin',         'severity_w': 1, 'category': 'acne'},
    'dry_skin':     {'label': 'Dry Skin',          'severity_w': 2, 'category': 'hydration'},
    'sensitive':    {'label': 'Sensitive Skin',    'severity_w': 2, 'category': 'sensitivity'},
    'large_pores':  {'label': 'Large Pores',       'severity_w': 1, 'category': 'texture'},
    'wrinkles':     {'label': 'Wrinkles',          'severity_w': 2, 'category': 'aging'},
    'fine_lines':   {'label': 'Fine Lines',        'severity_w': 1, 'category': 'aging'},
    'dull_skin':    {'label': 'Dull Skin',         'severity_w': 1, 'category': 'texture'},
    'redness':      {'label': 'Redness',           'severity_w': 2, 'category': 'sensitivity'},
    'dark_circles': {'label': 'Dark Circles',      'severity_w': 1, 'category': 'eyes'},
    'blackheads':   {'label': 'Blackheads',        'severity_w': 1, 'category': 'acne'},
    'whiteheads':   {'label': 'Whiteheads',        'severity_w': 1, 'category': 'acne'},
    'uneven_tone':  {'label': 'Uneven Skin Tone',  'severity_w': 1, 'category': 'pigment'},
    'sun_damage':   {'label': 'Sun Damage',        'severity_w': 2, 'category': 'pigment'},
}

INGREDIENT_MAP = {
    'acne':       ['Salicylic Acid (BHA) 2%', 'Niacinamide 10%', 'Benzoyl Peroxide 2.5%',
                   'Azelaic Acid 10%', 'Tea Tree Extract', 'Zinc PCA'],
    'pigment':    ['Vitamin C 15–20%', 'Alpha Arbutin 2%', 'Niacinamide 10%',
                   'Tranexamic Acid', 'Kojic Acid', 'SPF 50+ (mandatory)'],
    'aging':      ['Retinol 0.025–0.5%', 'Peptides (Argireline, Matrixyl)',
                   'Vitamin C', 'Hyaluronic Acid', 'Bakuchiol', 'Ceramides'],
    'hydration':  ['Hyaluronic Acid', 'Ceramides', 'Glycerin', 'Squalane',
                   'Centella Asiatica', 'Panthenol (B5)'],
    'texture':    ['AHA Glycolic Acid 5–10%', 'BHA Salicylic Acid', 'Niacinamide',
                   'Retinol', 'Polyglutamic Acid'],
    'sensitivity':['Centella Asiatica (Cica)', 'Aloe Vera', 'Allantoin',
                   'Ceramides', 'Colloidal Oat', 'Panthenol'],
    'eyes':       ['Caffeine', 'Vitamin K', 'Peptides', 'Hyaluronic Acid', 'Retinol (eye-safe)'],
}

AVOID_MAP = {
    'acne':       ['Coconut oil (highly comedogenic)', 'Heavy creams on oily zones',
                   'Alcohol-based toners', 'Harsh physical scrubs'],
    'pigment':    ['Unprotected sun exposure', 'DIY lemon juice',
                   'High % AHAs without SPF'],
    'aging':      ['Harsh physical exfoliants', 'Skipping SPF daily',
                   'Alcohol-based toners'],
    'hydration':  ['Sulfate cleansers (SLS/SLES)', 'Hot water face washing',
                   'Alcohol toners', 'Skipping moisturizer'],
    'sensitivity':['Fragrance in skincare', 'Parabens', 'Physical scrubs',
                   'Denatured alcohol', 'Strong AHAs (start slow)'],
    'texture':    ['Over-exfoliating (max 2–3×/week)',
                   'Skipping moisturizer after exfoliation'],
    'eyes':       ['Rubbing eyes', 'Heavily fragranced eye products'],
}

PRODUCT_MAP = {
    'acne': [
        {'sku': 'DPS890009',   'name': 'Pore Serum 1989',          'brand': 'Differensea',   'cat': 'Serum',   'why': 'BHA-based — clears pore blockages and reduces active breakouts'},
        {'sku': 'RCF0005',     'name': 'Cleansing Foam Gentle Balance','brand': 'Resurrection','cat': 'Cleanser','why': 'pH-balanced foam — removes excess oil without stripping barrier'},
        {'sku': 'RTDN0006',    'name': 'Toner Dermeist Nurturing',  'brand': 'Resurrection',  'cat': 'Toner',   'why': 'Preps skin post-cleanse, minimises oil and tightens pores'},
    ],
    'pigment': [
        {'sku': 'PHYPDRNS0028','name': 'Phyto PDRN Serum',         'brand': 'Phyto PDRN',    'cat': 'Serum',   'why': 'PDRN + brightening actives fade dark spots and even skin tone'},
        {'sku': 'RSBSPF500008','name': 'Radiance Sunblock SPF50+', 'brand': 'Resurrection',  'cat': 'SPF',     'why': 'SPF50+ — blocks UV that triggers and worsens all pigmentation'},
        {'sku': 'RAGE0001',    'name': 'Anti Gravity Essence',      'brand': 'Resurrection',  'cat': 'Essence', 'why': 'Exosome tech brightens and reverses UV-induced skin damage'},
    ],
    'aging': [
        {'sku': 'RAE0002',     'name': 'Aesthetic Ultimate Cream',  'brand': 'Resurrection',  'cat': 'Cream',   'why': 'Anti-gravity firming cream with peptides + exosome complex'},
        {'sku': 'PHYPDRNC0030','name': 'Phyto PDRN Cream',         'brand': 'Phyto PDRN',    'cat': 'Cream',   'why': 'PDRN-powered skin regeneration and deep plumping'},
        {'sku': 'JBMREBS0015', 'name': 'Bachuchiol Serum',          'brand': 'Revital Energy', 'cat': 'Serum',  'why': 'Plant-based retinol alternative — safe for sensitive or mature skin'},
    ],
    'hydration': [
        {'sku': 'PHYPDRNT0027','name': 'Phyto PDRN Toner',         'brand': 'Phyto PDRN',    'cat': 'Toner',   'why': 'Multi-layer hydration with PDRN and Hyaluronic Acid'},
        {'sku': 'DSC0014',     'name': 'Soothing Cream Repair',     'brand': 'Differensea',   'cat': 'Cream',   'why': 'Ceramide-rich barrier repair — restores moisture retention'},
        {'sku': 'DIRS0013',    'name': 'Intensive Repair Serum',    'brand': 'Differensea',   'cat': 'Serum',   'why': 'Blue Biome complex — rapidly rebuilds the moisture barrier'},
    ],
    'sensitivity': [
        {'sku': 'JBMRECF0017', 'name': 'Gel to Foam Cleanser',     'brand': 'Revital Energy', 'cat': 'Cleanser','why': 'Centella + Houttuynia — zero irritation for reactive skin'},
        {'sku': 'DSC0014',     'name': 'Soothing Cream Repair',     'brand': 'Differensea',   'cat': 'Cream',   'why': 'Instantly calms redness and rebuilds weakened skin barrier'},
        {'sku': 'DSP0016',     'name': 'Sun Protector',             'brand': 'Differensea',   'cat': 'SPF',     'why': 'Fragrance-free mineral SPF formulated for reactive, sensitive skin'},
    ],
    'texture': [
        {'sku': 'DPS890009',   'name': 'Pore Serum 1989',          'brand': 'Differensea',   'cat': 'Serum',   'why': 'Visibly minimises pores and smooths uneven skin texture'},
        {'sku': 'JBMRETUC0017','name': 'Tone Up Cream',            'brand': 'Revital Energy', 'cat': 'Cream',   'why': 'Instantly blurs surface irregularities for an airbrushed finish'},
        {'sku': 'RAGE0001',    'name': 'Anti Gravity Essence',      'brand': 'Resurrection',  'cat': 'Essence', 'why': 'Refines skin texture and improves surface clarity over time'},
    ],
    'eyes': [
        {'sku': 'PHYPDRNS0028','name': 'Phyto PDRN Serum',         'brand': 'Phyto PDRN',    'cat': 'Serum',   'why': 'PDRN + caffeine reduces periorbital darkness and puffiness'},
        {'sku': 'RAE0002',     'name': 'Aesthetic Ultimate Cream',  'brand': 'Resurrection',  'cat': 'Cream',   'why': 'Peptide-rich cream works as an eye treatment for fine lines'},
    ],
}

# Foundation shades per (skin_tone, undertone)
# Format — fdn: local brand / mid-range brand / international brand
# Local:       MARS Cosmetics, Blue Heaven
# Mid-range:   Lakmé, SUGAR Cosmetics, Colorbar, Faces Canada
# International: Maybelline, L'Oréal Paris
MAKEUP_SHADE_MAP = {
    ('fair','warm'):     {
        'fdn':   'MARS Porcelain 01 / Lakmé Ivory W10 / Maybelline 110',
        'fdn_alt': 'SUGAR Matte As Hell #02 / Faces Canada Natural W10',
        'lip':   'Coral, Nude Beige',
        'lip_local': 'Lakmé 9to5 Coral Coast / SUGAR Matte Attack #04',
        'blush': 'Peachy Keen',
    },
    ('fair','cool'):     {
        'fdn':   'MARS Porcelain 01 / Lakmé Ivory C10 / Maybelline 120',
        'fdn_alt': 'SUGAR Matte As Hell #01 / Colorbar Seamless Foundation C10',
        'lip':   'Rose Pink, Berry',
        'lip_local': 'Lakmé Absolute Moonlit Rose / SUGAR Smudge Me Not Berry',
        'blush': 'Rose Flush',
    },
    ('fair','neutral'):  {
        'fdn':   'MARS Ivory 02 / Lakmé Ivory N10 / Maybelline 115',
        'fdn_alt': 'SUGAR Matte As Hell #03 / Faces Canada Natural N10',
        'lip':   'Nude Pink, Mauve',
        'lip_local': 'Lakmé 9to5 Nude Flush / SUGAR Smudge Me Not Mauve',
        'blush': 'Nude Pink',
    },
    ('light','warm'):    {
        'fdn':   'MARS Ivory 02 / Lakmé Beige W20 / Maybelline 120',
        'fdn_alt': 'SUGAR Matte As Hell #05 / Colorbar Seamless W20',
        'lip':   'Coral Orange, Peach',
        'lip_local': 'Lakmé 9to5 Tangerine Trip / SUGAR Smudge Me Not Peach',
        'blush': 'Coral Kiss',
    },
    ('light','cool'):    {
        'fdn':   'MARS Natural Beige 03 / Lakmé Beige C20 / Maybelline 128',
        'fdn_alt': 'SUGAR Matte As Hell #06 / Faces Canada Beige C20',
        'lip':   'Dusty Rose, Mauve',
        'lip_local': 'Lakmé 9to5 Dusty Rose / SUGAR Smudge Me Not Plum',
        'blush': 'Rose Flush',
    },
    ('light','neutral'): {
        'fdn':   'MARS Natural Beige 03 / Lakmé Beige N20 / Maybelline 125',
        'fdn_alt': 'SUGAR Matte As Hell #04 / Colorbar Seamless N20',
        'lip':   'Nude Beige, Rose',
        'lip_local': 'Lakmé 9to5 Nude Touch / SUGAR Smudge Me Not Rose',
        'blush': 'Nude Pink',
    },
    ('medium','warm'):   {
        'fdn':   'MARS Sand Beige 04 / Lakmé Sand W30 / Maybelline 220',
        'fdn_alt': 'SUGAR Matte As Hell #10 / Faces Canada Caramel W30',
        'lip':   'Terracotta, Coral',
        'lip_local': 'Lakmé 9to5 Brick Lane / SUGAR Smudge Me Not Terracotta',
        'blush': 'Bronzed Glow',
    },
    ('medium','cool'):   {
        'fdn':   'MARS Natural Beige 03 / Lakmé Sand C30 / Maybelline 228',
        'fdn_alt': 'SUGAR Matte As Hell #09 / Colorbar Seamless C30',
        'lip':   'Berry, Burgundy',
        'lip_local': 'Lakmé 9to5 Berry Best / SUGAR Smudge Me Not Burgundy',
        'blush': 'Berry Bliss',
    },
    ('medium','neutral'): {
        'fdn':   'MARS Natural Beige 03 / Lakmé Sand N30 / Maybelline 220',
        'fdn_alt': 'SUGAR Matte As Hell #08 / Faces Canada Caramel N30',
        'lip':   'Nude Beige, Rose',
        'lip_local': 'Lakmé 9to5 Nude Flush / SUGAR Smudge Me Not Nude',
        'blush': 'Nude Pink',
    },
    ('medium','olive'):  {
        'fdn':   'MARS Sand Beige 04 / Lakmé Honey OW30 / Maybelline 230',
        'fdn_alt': 'SUGAR Matte As Hell #11 / Colorbar Seamless OW30',
        'lip':   'Mocha, Terracotta',
        'lip_local': 'Lakmé 9to5 Mocha Magic / SUGAR Smudge Me Not Mocha',
        'blush': 'Bronzed Glow',
    },
    ('tan','warm'):      {
        'fdn':   'MARS Warm Honey 05 / Lakmé Honey W40 / Maybelline 310',
        'fdn_alt': 'SUGAR Matte As Hell #15 / Faces Canada Honey W40',
        'lip':   'Burnt Orange, Coral',
        'lip_local': 'Lakmé 9to5 Orange Peel / SUGAR Smudge Me Not Burnt Orange',
        'blush': 'Bronzed Glow',
    },
    ('tan','cool'):      {
        'fdn':   'MARS Warm Honey 05 / Lakmé Honey C40 / Maybelline 330',
        'fdn_alt': 'SUGAR Matte As Hell #14 / Colorbar Seamless C40',
        'lip':   'Wine, Deep Berry',
        'lip_local': 'Lakmé 9to5 Wine & Dine / SUGAR Smudge Me Not Wine',
        'blush': 'Berry Bliss',
    },
    ('tan','neutral'):   {
        'fdn':   'MARS Warm Honey 05 / Lakmé Honey N40 / Maybelline 320',
        'fdn_alt': 'SUGAR Matte As Hell #13 / Faces Canada Honey N40',
        'lip':   'Nude Mocha, Rose',
        'lip_local': 'Lakmé 9to5 Mocha Magic / SUGAR Smudge Me Not Nude Brown',
        'blush': 'Peachy Keen',
    },
    ('deep','warm'):     {
        'fdn':   'MARS Caramel 06 / Lakmé Caramel W50 / Maybelline 355',
        'fdn_alt': 'SUGAR Matte As Hell #20 / Colorbar Seamless W50',
        'lip':   'Terracotta, Bronze',
        'lip_local': 'Lakmé 9to5 Burnt Terracotta / SUGAR Smudge Me Not Bronze',
        'blush': 'Bronzed Glow',
    },
    ('deep','cool'):     {
        'fdn':   'MARS Caramel 06 / Lakmé Caramel C50 / Maybelline 370',
        'fdn_alt': 'SUGAR Matte As Hell #19 / Faces Canada Caramel C50',
        'lip':   'Dark Wine, Plum',
        'lip_local': 'Lakmé 9to5 Dark Wine / SUGAR Smudge Me Not Deep Plum',
        'blush': 'Berry Bliss',
    },
    ('deep','neutral'):  {
        'fdn':   'MARS Caramel 06 / Lakmé Caramel N50 / Maybelline 360',
        'fdn_alt': 'SUGAR Matte As Hell #18 / Colorbar Seamless N50',
        'lip':   'Nude Brown, Rose',
        'lip_local': 'Lakmé 9to5 Nude Flush / SUGAR Smudge Me Not Nude Brown',
        'blush': 'Berry Bliss',
    },
}


def compute_analysis(answers: dict) -> dict:
    """Convert all answers → full structured analysis + recommendations."""
    concerns = answers.get('skin_concerns', [])
    if isinstance(concerns, str):
        concerns = [concerns]

    result = {
        'detected_issues': [],
        'categories': [],
        'severity': 'minimal',
        'severity_score': 0,
        'top_ingredients': [],
        'avoid_list': [],
        'products': [],
        'routine_am': [],
        'routine_pm': [],
        'lifestyle_flags': [],
        'makeup_shades': None,
        'derm_needed': False,
        'ai_notes': [],
        'skin_type': '',
        'summary': '',
    }

    # ── Skin type from answers ────────────────────────────────────────────────
    feel = answers.get('skin_feel', 'normal')
    skin_type_map = {
        'very_dry': 'Dry', 'normal': 'Normal',
        'combination': 'Combination', 'oily': 'Oily',
    }
    result['skin_type'] = skin_type_map.get(feel, 'Normal')
    if 'sensitive' in concerns:
        result['skin_type'] = 'Sensitive'

    # ── Concern → category mapping ────────────────────────────────────────────
    score = 0
    seen_cats = []
    issues = []
    for c in concerns:
        meta = CONCERN_META.get(c)
        if meta:
            issues.append({'value': c, 'label': meta['label'], 'cat': meta['category']})
            score += meta['severity_w']
            if meta['category'] not in seen_cats:
                seen_cats.append(meta['category'])
    result['detected_issues'] = issues
    result['categories'] = seen_cats

    # ── Acne severity modifier ────────────────────────────────────────────────
    acne_sev = answers.get('acne_severity', '')
    if acne_sev == 'severe':
        score += 4
        result['derm_needed'] = True
        result['ai_notes'].append({
            'type': 'warning', 'icon': '⚠️',
            'text': 'Severe acne — a dermatologist consultation is strongly recommended alongside any skincare routine.'
        })
    elif acne_sev == 'moderate':
        score += 2
    painful = answers.get('acne_painful', '')
    if painful == 'yes':
        score += 2
        result['derm_needed'] = True
        result['ai_notes'].append({
            'type': 'warning', 'icon': '⚠️',
            'text': 'Painful cystic acne may need prescription treatment (Tretinoin / Clindamycin). Please see a dermatologist.'
        })

    # ── Lifestyle flags ───────────────────────────────────────────────────────
    flags = []
    if answers.get('water_glasses') in ('lt4', '4to6'):
        flags.append({'icon': '💧', 'text': 'Low water intake is dehydrating your skin and slowing cell renewal.'})
    if answers.get('sleep_hours') == 'lt6':
        flags.append({'icon': '😴', 'text': 'Under 6 hrs sleep spikes cortisol — a key driver of acne, dullness, and aging.'})
        score += 1
    if answers.get('stress_level') == 'high':
        flags.append({'icon': '😰', 'text': 'High stress raises cortisol → increases oil, triggers breakouts and slows healing.'})
        score += 1
    if answers.get('smokes') == 'yes':
        flags.append({'icon': '🚬', 'text': 'Smoking depletes Vitamin C, accelerates collagen breakdown, and causes dullness.'})
        score += 1
    if answers.get('sunscreen_daily') in ('no', 'sometimes') and 'pigment' in seen_cats:
        flags.append({'icon': '☀️', 'text': 'Not wearing SPF daily is the #1 cause of worsening dark spots and pigmentation.'})
        score += 2
    if answers.get('pregnant_bf') in ('pregnant', 'breastfeeding', 'trying'):
        result['ai_notes'].append({
            'type': 'info', 'icon': '🤰',
            'text': 'Retinol, Salicylic Acid, and Hydroquinone must be avoided. Safe options: Vitamin C, Niacinamide, Azelaic Acid, SPF.'
        })
    if answers.get('skin_conditions', '').strip():
        result['ai_notes'].append({
            'type': 'info', 'icon': '🩺',
            'text': f"Noted skin condition: {answers.get('skin_conditions')}. Recommendations are adjusted accordingly."
        })
    result['lifestyle_flags'] = flags

    # ── Severity label ────────────────────────────────────────────────────────
    result['severity_score'] = score
    if score >= 12:
        result['severity'] = 'severe'
    elif score >= 7:
        result['severity'] = 'moderate'
    elif score >= 3:
        result['severity'] = 'mild'
    else:
        result['severity'] = 'minimal'

    # ── Ingredients + avoid ───────────────────────────────────────────────────
    all_ing, all_avoid = [], []
    for cat in seen_cats:
        all_ing.extend(INGREDIENT_MAP.get(cat, []))
        all_avoid.extend(AVOID_MAP.get(cat, []))
    # Remove duplicates preserving order
    seen = set()
    result['top_ingredients'] = [x for x in all_ing if not (x in seen or seen.add(x))][:8]
    seen = set()
    result['avoid_list'] = [x for x in all_avoid if not (x in seen or seen.add(x))][:6]

    # ── Products ──────────────────────────────────────────────────────────────
    seen_skus = set()
    prods = []
    for cat in seen_cats:
        for p in PRODUCT_MAP.get(cat, []):
            if p['sku'] not in seen_skus and len(prods) < 6:
                prods.append(p)
                seen_skus.add(p['sku'])
    result['products'] = prods

    # ── Routines ──────────────────────────────────────────────────────────────
    result['routine_am'], result['routine_pm'] = _build_routine(seen_cats, feel)

    # ── Makeup shades (if skin_tone + undertone in answers) ───────────────────
    tone = answers.get('skin_tone', '')
    undertone = answers.get('undertone', '')
    if tone and undertone:
        shades = MAKEUP_SHADE_MAP.get((tone, undertone)) or MAKEUP_SHADE_MAP.get((tone, 'neutral'))
        if shades:
            # Resolve preferred Indian brands from quiz answer
            selected_brands = answers.get('preferred_makeup_brands', [])
            if isinstance(selected_brands, str):
                selected_brands = [selected_brands]

            # Map of brand value → display label
            BRAND_LABEL_MAP = {
                'mars': 'MARS Cosmetics', 'faces_canada': 'Faces Canada',
                'miss_claire': 'Miss Claire', 'blue_heaven': 'Blue Heaven',
                'ADS': 'ADS Cosmetics', 'lakme': 'Lakmé',
                'colorbar': 'Colorbar', 'sugar': 'SUGAR Cosmetics',
                'myglamm': 'MyGlamm', 'nykaa': 'Nykaa Cosmetics',
                'renee': 'RENÉE Cosmetics', 'swiss_beauty': 'Swiss Beauty',
                'insight': 'Insight Cosmetics', 'maybelline': 'Maybelline',
                'loreal_paris': "L'Oréal Paris", 'revlon': 'Revlon',
                'nyx': 'NYX Professional', 'other': None,
            }
            preferred_brand_labels = [
                BRAND_LABEL_MAP[b] for b in selected_brands
                if b in BRAND_LABEL_MAP and BRAND_LABEL_MAP[b]
            ]

            # Tier-based foundation suggestion override if Indian brands selected
            makeup_budget = answers.get('makeup_budget', '')
            budget_is_local = makeup_budget in ('lt500', '500_1000')

            # Build a user-friendly brand note
            brand_note = ''
            if preferred_brand_labels:
                brand_note = 'Your picks: ' + ', '.join(preferred_brand_labels)
            elif budget_is_local:
                brand_note = 'Affordable Indian options: Lakmé, MARS, SUGAR Cosmetics, Faces Canada'

            result['makeup_shades'] = {
                'tone': tone.title(),
                'undertone': undertone.title(),
                **shades,
                'preferred_brands': preferred_brand_labels,
                'brand_note': brand_note,
            }

    # ── Summary ───────────────────────────────────────────────────────────────
    concern_labels = [CONCERN_META[c]['label'] for c in concerns if c in CONCERN_META]
    n = len(concern_labels)
    sev = result['severity']
    result['summary'] = (
        f"Based on your answers, your skin profile shows {sev} concerns "
        f"across {n} issue{'s' if n != 1 else ''}"
        f"{': ' + ', '.join(concern_labels[:3]) if concern_labels else ''}. "
        f"Your personalised routine, ingredients, and product recommendations are below."
    )
    return result


def _build_routine(categories: list, skin_feel: str) -> tuple:
    """Build AM and PM routine steps from concern categories and skin feel."""
    am, pm = [], []

    # Cleanser
    if 'acne' in categories or skin_feel == 'oily':
        am.append('Gel / foam cleanser (pH 5.5 — oil control)')
        pm.append('Double cleanse: oil cleanser → gel cleanser')
    elif skin_feel == 'very_dry':
        am.append('Cream or milk cleanser (no sulfates)')
        pm.append('Cleansing balm → gentle cream cleanser')
    else:
        am.append('Gentle low-pH cleanser')
        pm.append('Double cleanse or gentle face wash')

    # Toner
    if 'acne' in categories:
        am.append('BHA toner (Salicylic Acid 2%) — after cleansing')
        pm.append('BHA or AHA toner — or alternate nights')
    elif 'sensitivity' in categories:
        am.append('Soothing toner (Centella Asiatica / Aloe)')
        pm.append('Calming essence or toner')
    else:
        am.append('Hydrating toner (pat in, don\'t wipe)')
        pm.append('Hydrating toner')

    # Treatments
    if 'pigment' in categories:
        am.append('Vitamin C serum 15–20% (brightening + antioxidant)')
    if 'aging' in categories:
        pm.append('Retinol 0.025–0.1% (start 2× per week, PM only)')
        am.append('Peptide serum (AM collagen support)')
    if 'hydration' in categories or skin_feel == 'very_dry':
        am.append('Hyaluronic Acid serum (apply on damp skin)')
        pm.append('Ceramide or Peptide night serum')
    if 'acne' in categories and 'pigment' in categories:
        pm.append('Niacinamide 10% serum (bridges acne + pigmentation)')
    if 'eyes' in categories:
        am.append('Eye cream (caffeine + peptides — dark circles)')
        pm.append('Eye cream or Retinol eye treatment')

    # Moisturiser
    if skin_feel == 'oily':
        am.append('Oil-free gel moisturiser')
        pm.append('Lightweight gel moisturiser or skip if oily')
    elif skin_feel == 'very_dry':
        am.append('Rich ceramide cream moisturiser')
        pm.append('Sleeping mask or ceramide night cream')
    else:
        am.append('Light moisturiser suited to your skin type')
        pm.append('Moisturiser or nourishing night cream')

    # SPF (AM only)
    am.append('SPF 50+ broad spectrum — EVERY morning, reapply every 2 hrs outdoors')

    return am, pm
