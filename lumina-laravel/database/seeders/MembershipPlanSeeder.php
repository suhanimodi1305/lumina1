<?php

namespace Database\Seeders;

use App\Models\MembershipPlan;
use Illuminate\Database\Seeder;

class MembershipPlanSeeder extends Seeder
{
    public function run(): void
    {
        $plans = [
            [
                'name'         => 'normal',
                'display_name' => 'Normal',
                'price'        => 0.00,
                'duration_days' => 36500, // Essentially free forever
                'price_cap'    => 999,
                'features'     => [
                    'AI Skin Analysis',
                    'Basic Product Recommendations',
                    'Budget-friendly brands (Mars, Lakmé, Mamaearth)',
                    'Product catalog access',
                    'Log & Earn rewards',
                ],
                'is_active' => true,
            ],
            [
                'name'         => 'medium',
                'display_name' => 'Medium',
                'price'        => 299.00,
                'duration_days' => 30,
                'price_cap'    => 2499,
                'features'     => [
                    'Everything in Normal',
                    'Mid-range brand recommendations',
                    'Maybelline, L\'Oréal Paris, Minimalist',
                    'Priority AI consultation',
                    'Advanced skin analytics',
                    '2x Rewards points',
                ],
                'is_active' => true,
            ],
            [
                'name'         => 'vip',
                'display_name' => 'VIP',
                'price'        => 999.00,
                'duration_days' => 30,
                'price_cap'    => null,
                'features'     => [
                    'Everything in Medium',
                    'Premium brand access (MAC, Huda, Dior, SK-II)',
                    'No price restrictions',
                    'VIP AI Doctor consultations',
                    'Priority booking',
                    '3x Rewards points',
                    'Exclusive product launches',
                ],
                'is_active' => true,
            ],
        ];

        foreach ($plans as $plan) {
            MembershipPlan::updateOrCreate(['name' => $plan['name']], $plan);
        }

        $this->command->info('Membership plans seeded.');
    }
}
