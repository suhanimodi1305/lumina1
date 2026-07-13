<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $this->call([
            RolesAndPermissionsSeeder::class,
            AdminUserSeeder::class,
            SkinConcernSeeder::class,
            MembershipPlanSeeder::class,
            BrandSeeder::class,
            CategorySeeder::class,
            QuickPromptSeeder::class,
        ]);
    }
}
