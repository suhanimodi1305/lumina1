<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class AdminUserSeeder extends Seeder
{
    public function run(): void
    {
        $admin = User::firstOrCreate(
            ['email' => 'admin@lumina.beauty'],
            [
                'name'              => 'Lumina Admin',
                'password'          => Hash::make('admin@lumina123'),
                'email_verified_at' => now(),
            ]
        );

        $admin->assignRole('admin');

        $this->command->info("Admin user: admin@lumina.beauty / admin@lumina123");
    }
}
