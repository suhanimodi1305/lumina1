<?php

namespace App\Console\Commands;

use App\Services\MakeupApiSyncService;
use Illuminate\Console\Command;

class SyncMakeupApi extends Command
{
    protected $signature   = 'makeup:sync {--category= : Filter by category}';
    protected $description = 'Sync products from external Makeup API into the local database';

    public function __construct(private MakeupApiSyncService $syncService) {
        parent::__construct();
    }

    public function handle(): int
    {
        $category = $this->option('category');

        $this->info('Starting Makeup API sync' . ($category ? " (category: {$category})" : '') . '...');

        try {
            $result = $this->syncService->sync($category);

            $this->info("✓ Sync complete.");
            $this->table(
                ['Metric', 'Count'],
                [
                    ['Created',   $result['created']],
                    ['Updated',   $result['updated']],
                    ['Skipped',   $result['skipped']],
                    ['Errors',    $result['errors']],
                    ['Total API', $result['total_api']],
                ]
            );

            return self::SUCCESS;
        } catch (\Throwable $e) {
            $this->error("Sync failed: {$e->getMessage()}");
            return self::FAILURE;
        }
    }
}
