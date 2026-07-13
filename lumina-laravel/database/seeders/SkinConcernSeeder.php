<?php

namespace Database\Seeders;

use App\Models\SkinConcern;
use Illuminate\Database\Seeder;

class SkinConcernSeeder extends Seeder
{
    public function run(): void
    {
        $concerns = [
            ['name' => 'Acne',           'slug' => 'acne',         'icon' => '🔴', 'description' => 'Inflammatory acne including papules, pustules, and comedones.'],
            ['name' => 'Pigmentation',   'slug' => 'pigmentation', 'icon' => '🟤', 'description' => 'Dark spots, melasma, and post-inflammatory hyperpigmentation.'],
            ['name' => 'Dark Circles',   'slug' => 'dark_circles', 'icon' => '👁️',  'description' => 'Periorbital hyperpigmentation and under-eye discolouration.'],
            ['name' => 'Dryness',        'slug' => 'dryness',      'icon' => '💧', 'description' => 'Dehydrated or xerotic skin lacking adequate moisture.'],
            ['name' => 'Oiliness',       'slug' => 'oiliness',     'icon' => '✨', 'description' => 'Excess sebum production causing a shiny appearance.'],
            ['name' => 'Redness',        'slug' => 'redness',      'icon' => '🌹', 'description' => 'Skin redness from rosacea, irritation, or inflammation.'],
            ['name' => 'Fine Lines',     'slug' => 'fine_lines',   'icon' => '〰️', 'description' => 'Early signs of aging including fine lines and wrinkles.'],
            ['name' => 'Large Pores',    'slug' => 'large_pores',  'icon' => '🔵', 'description' => 'Visibly enlarged pores, often associated with oily skin.'],
            ['name' => 'Aging',          'slug' => 'aging',        'icon' => '⏳', 'description' => 'General signs of skin aging including sagging and loss of elasticity.'],
            ['name' => 'Dullness',       'slug' => 'dullness',     'icon' => '🌫️', 'description' => 'Lack of radiance and uneven skin texture.'],
            ['name' => 'Blackheads',     'slug' => 'blackheads',   'icon' => '⚫', 'description' => 'Open comedones appearing as small dark bumps.'],
            ['name' => 'Sensitivity',    'slug' => 'sensitivity',  'icon' => '⚠️', 'description' => 'Skin that reacts easily to products or environmental factors.'],
        ];

        foreach ($concerns as $concern) {
            SkinConcern::firstOrCreate(['slug' => $concern['slug']], $concern);
        }

        $this->command->info('Skin concerns seeded.');
    }
}
