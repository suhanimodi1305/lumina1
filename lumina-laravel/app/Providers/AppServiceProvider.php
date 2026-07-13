<?php

namespace App\Providers;

use App\Models\User;
use App\Observers\UserObserver;
use App\Services\AiService;
use App\Services\MembershipService;
use App\Services\RewardsService;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(AiService::class);
        $this->app->singleton(MembershipService::class);
        $this->app->singleton(RewardsService::class);
    }

    public function boot(): void
    {
        User::observe(UserObserver::class);
    }
}
