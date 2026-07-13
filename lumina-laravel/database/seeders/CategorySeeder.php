<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\Subcategory;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class CategorySeeder extends Seeder
{
    public function run(): void
    {
        $data = [
            [
                'name' => 'Makeup', 'type' => 'makeup', 'icon' => '💄', 'sort_order' => 1,
                'subs' => ['Foundation', 'Concealer', 'Blush', 'Bronzer', 'Highlighter',
                           'Eyeshadow', 'Eyeliner', 'Mascara', 'Lipstick', 'Lip Gloss',
                           'Lip Liner', 'Setting Powder', 'Primer', 'Setting Spray'],
            ],
            [
                'name' => 'Korean Beauty', 'type' => 'korean', 'icon' => '🌸', 'sort_order' => 2,
                'subs' => ['Cleanser', 'Toner', 'Essence', 'Serum', 'Ampoule',
                           'Moisturiser', 'Sunscreen', 'Sheet Mask', 'Eye Cream',
                           'Sleeping Mask', 'Exfoliator', 'Mist'],
            ],
            [
                'name' => 'Ayurvedic', 'type' => 'ayurvedic', 'icon' => '🌿', 'sort_order' => 3,
                'subs' => ['Face Care', 'Body Care', 'Hair Care', 'Oils', 'Herbal Supplements'],
            ],
            [
                'name' => 'Pharmacy', 'type' => 'pharmacy', 'icon' => '💊', 'sort_order' => 4,
                'subs' => ['Acne Treatment', 'Sunscreen SPF', 'Moisturiser', 'Cleanser',
                           'Prescription Skincare', 'Derma Brands'],
            ],
            [
                'name' => 'Treatment', 'type' => 'treatment', 'icon' => '⚗️', 'sort_order' => 5,
                'subs' => ['Serum', 'Peel', 'Mask', 'Spot Treatment', 'Eye Treatment'],
            ],
        ];

        foreach ($data as $cat) {
            $category = Category::firstOrCreate(
                ['slug' => Str::slug($cat['name'])],
                [
                    'name'       => $cat['name'],
                    'slug'       => Str::slug($cat['name']),
                    'type'       => $cat['type'],
                    'icon'       => $cat['icon'],
                    'sort_order' => $cat['sort_order'],
                    'is_active'  => true,
                ]
            );

            foreach ($cat['subs'] as $order => $sub) {
                Subcategory::firstOrCreate(
                    ['slug' => Str::slug($sub)],
                    [
                        'category_id' => $category->id,
                        'name'        => $sub,
                        'slug'        => Str::slug($sub),
                        'sort_order'  => $order,
                        'is_active'   => true,
                    ]
                );
            }
        }

        $this->command->info('Categories and subcategories seeded.');
    }
}
