<?php

namespace App\Observers;

use App\Models\User;
use App\Models\UserProfile;

class UserObserver
{
    /**
     * Auto-create UserProfile when a new User registers.
     */
    public function created(User $user): void
    {
        UserProfile::create([
            'user_id'    => $user->id,
            'tier'       => 'normal',
            'staff_role' => 'none',
        ]);
    }
}
