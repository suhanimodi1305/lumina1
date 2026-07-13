<?php

namespace Database\Seeders;

use App\Models\Brand;
use Illuminate\Database\Seeder;
use Illuminate\Support\Str;

class BrandSeeder extends Seeder
{
    public function run(): void
    {
        $brands = [
            // Normal tier brands
            ['name' => 'Mars Cosmetics',    'country_of_origin' => 'India'],
            ['name' => 'Swiss Beauty',      'country_of_origin' => 'India'],
            ['name' => 'Insight Cosmetics', 'country_of_origin' => 'India'],
            ['name' => 'Blue Heaven',       'country_of_origin' => 'India'],
            ['name' => 'Lakmé',             'country_of_origin' => 'India'],
            ['name' => 'Pilgrim',           'country_of_origin' => 'India'],
            ['name' => 'Mamaearth',         'country_of_origin' => 'India'],
            // Medium tier brands
            ['name' => 'Maybelline New York', 'country_of_origin' => 'USA'],
            ['name' => "L'Oréal Paris",       'country_of_origin' => 'France'],
            ['name' => 'Revlon',              'country_of_origin' => 'USA'],
            ['name' => 'Colorbar',            'country_of_origin' => 'India'],
            ['name' => 'Nykaa Cosmetics',     'country_of_origin' => 'India'],
            ['name' => 'Cetaphil',            'country_of_origin' => 'Switzerland'],
            ['name' => 'Minimalist',          'country_of_origin' => 'India'],
            // VIP tier brands
            ['name' => 'MAC',                'country_of_origin' => 'Canada'],
            ['name' => 'Huda Beauty',        'country_of_origin' => 'UAE'],
            ['name' => 'Charlotte Tilbury',  'country_of_origin' => 'UK'],
            ['name' => 'Dior Beauty',        'country_of_origin' => 'France'],
            ['name' => 'Estée Lauder',       'country_of_origin' => 'USA'],
            ['name' => 'Clinique',           'country_of_origin' => 'USA'],
            ['name' => 'Laneige',            'country_of_origin' => 'South Korea'],
            ['name' => 'Sulwhasoo',          'country_of_origin' => 'South Korea'],
            ['name' => 'SK-II',              'country_of_origin' => 'Japan'],
            // K-Beauty
            ['name' => 'COSRX',             'country_of_origin' => 'South Korea'],
            ['name' => 'Some By Mi',        'country_of_origin' => 'South Korea'],
            ['name' => 'Innisfree',         'country_of_origin' => 'South Korea'],
            ['name' => 'Dr. Jart+',         'country_of_origin' => 'South Korea'],
            ['name' => 'Anua',              'country_of_origin' => 'South Korea'],
            // SAS Global K-Beauty
            ['name' => 'Resurrection Aesthetic', 'country_of_origin' => 'South Korea'],
            ['name' => 'Differensea',            'country_of_origin' => 'South Korea'],
            ['name' => 'Phyto PDRN',             'country_of_origin' => 'South Korea'],
            // Ayurvedic
            ['name' => 'Forest Essentials',  'country_of_origin' => 'India'],
            ['name' => 'Kama Ayurveda',      'country_of_origin' => 'India'],
            ['name' => 'Biotique',           'country_of_origin' => 'India'],
            ['name' => 'Khadi Naturals',     'country_of_origin' => 'India'],
            // Pharmacy
            ['name' => 'Neutrogena',         'country_of_origin' => 'USA'],
            ['name' => 'Himalaya',           'country_of_origin' => 'India'],
            ['name' => 'Avène',              'country_of_origin' => 'France'],
            ['name' => 'La Roche-Posay',     'country_of_origin' => 'France'],
        ];

        foreach ($brands as $brand) {
            Brand::firstOrCreate(
                ['slug' => Str::slug($brand['name'])],
                array_merge($brand, ['slug' => Str::slug($brand['name']), 'is_active' => true])
            );
        }

        $this->command->info('Brands seeded (' . count($brands) . ').');
    }
}
