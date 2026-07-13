<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Spatie\Permission\Models\Permission;
use Spatie\Permission\Models\Role;

class RolesAndPermissionsSeeder extends Seeder
{
    public function run(): void
    {
        // Reset cached roles and permissions
        app()[\Spatie\Permission\PermissionRegistrar::class]->forgetCachedPermissions();

        // ── Permissions ───────────────────────────────────────────────────
        $permissions = [
            // Products
            'products.view', 'products.create', 'products.edit', 'products.delete',
            'products.import', 'products.sync',
            // Orders
            'orders.view', 'orders.manage', 'orders.export',
            // Users
            'users.view', 'users.edit', 'users.delete',
            // Memberships
            'memberships.manage',
            // Marketing
            'marketing.view', 'marketing.manage',
            // Doctor
            'doctor.view', 'doctor.manage',
            // Reports
            'reports.view',
            // Settings
            'settings.manage',
        ];

        foreach ($permissions as $permission) {
            Permission::firstOrCreate(['name' => $permission]);
        }

        // ── Roles ─────────────────────────────────────────────────────────
        $user = Role::firstOrCreate(['name' => 'user']);
        $user->syncPermissions(['products.view', 'orders.view']);

        $employee = Role::firstOrCreate(['name' => 'employee']);
        $employee->syncPermissions([
            'products.view', 'orders.view', 'orders.manage',
        ]);

        $marketing = Role::firstOrCreate(['name' => 'marketing']);
        $marketing->syncPermissions([
            'products.view', 'marketing.view', 'marketing.manage', 'reports.view',
        ]);

        $doctor = Role::firstOrCreate(['name' => 'doctor']);
        $doctor->syncPermissions([
            'doctor.view', 'doctor.manage',
        ]);

        $admin = Role::firstOrCreate(['name' => 'admin']);
        $admin->syncPermissions(Permission::all());

        $this->command->info('Roles and permissions seeded.');
    }
}
