<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Membership Tier Configuration
    |--------------------------------------------------------------------------
    */
    'tiers' => [
        'normal' => [
            'price_cap'      => 999,
            'upgrade_points' => 500,
            'label'          => 'Normal',
            'color'          => '#6c757d',
            'brands'         => ['Mars', 'Swiss Beauty', 'Insight', 'Blue Heaven', 'Lakmé', 'Pilgrim', 'Mamaearth'],
        ],
        'medium' => [
            'price_cap'      => 2499,
            'upgrade_points' => 1500,
            'label'          => 'Medium',
            'color'          => '#0d6efd',
            'brands'         => ['Maybelline', "L'Oréal Paris", 'Revlon', 'Colorbar', 'Nykaa Cosmetics', 'Cetaphil', 'Minimalist'],
        ],
        'vip' => [
            'price_cap'      => null,
            'upgrade_points' => null,
            'label'          => 'VIP',
            'color'          => '#c9a84c',
            'brands'         => ['MAC', 'Huda Beauty', 'Charlotte Tilbury', 'Dior', 'Estée Lauder', 'Clinique', 'Laneige', 'Sulwhasoo', 'SK-II'],
        ],
    ],

    /*
    |--------------------------------------------------------------------------
    | Log & Earn Points
    |--------------------------------------------------------------------------
    */
    'points' => [
        'login'          => 10,
        'profile'        => 50,
        'scan'           => 25,
        'review'         => 15,
        'referral'       => 100,
        'purchase_rate'  => 1,    // points per ₹100 spent
        'tutorial'       => 5,
    ],

    /*
    |--------------------------------------------------------------------------
    | Referral
    |--------------------------------------------------------------------------
    */
    'referral_code_length' => 10,

    /*
    |--------------------------------------------------------------------------
    | Session
    |--------------------------------------------------------------------------
    */
    'session_expiry_minutes' => 120,

    /*
    |--------------------------------------------------------------------------
    | File Upload Limits
    |--------------------------------------------------------------------------
    */
    'max_scan_size_mb'         => 5,
    'max_prescription_size_mb' => 10,
    'allowed_image_types'      => ['image/jpeg', 'image/png', 'image/webp'],
    'allowed_image_extensions' => ['jpg', 'jpeg', 'png', 'webp'],

    /*
    |--------------------------------------------------------------------------
    | Scanner Demo Profiles
    |--------------------------------------------------------------------------
    */
    'demo_profiles' => [
        'combination_warm',
        'dry_cool',
        'oily_warm',
        'mature_neutral',
    ],

    /*
    |--------------------------------------------------------------------------
    | Chat
    |--------------------------------------------------------------------------
    */
    'chat' => [
        'max_history_messages' => 20,
        'valid_modes'          => ['doctor', 'makeup', 'kbeauty'],
    ],

];
