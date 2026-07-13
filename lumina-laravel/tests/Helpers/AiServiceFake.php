<?php

namespace Tests\Helpers;

use App\Services\AiService;
use Illuminate\Http\UploadedFile;

/**
 * In-memory fake for AiService — used in unit tests that cannot call Http::fake()
 * because the service is constructed outside the HTTP layer.
 *
 * Usage:
 *   $fake = AiServiceFake::make();
 *   $fake->queueScanResult(['skin_tone' => 'medium', ...]);
 *   $service = new ScanService($fake->service());
 */
class AiServiceFake
{
    private array $scanQueue   = [];
    private array $demoQueue   = [];
    private array $chatQueue   = [];
    private array $photoQueue  = [];
    private bool  $healthValue = true;

    /** Pre-loaded calls recorded for assertion */
    public array $recordedCalls = [];

    // ── Queuing helpers ────────────────────────────────────────────────────

    public function queueScanResult(array $result): static
    {
        $this->scanQueue[] = $result;
        return $this;
    }

    public function queueDemoResult(array $result): static
    {
        $this->demoQueue[] = $result;
        return $this;
    }

    public function queueChatResponse(array $result): static
    {
        $this->chatQueue[] = $result;
        return $this;
    }

    public function queuePhotoResponse(array $result): static
    {
        $this->photoQueue[] = $result;
        return $this;
    }

    public function setHealthy(bool $value): static
    {
        $this->healthValue = $value;
        return $this;
    }

    // ── Build a mock AiService bound to this fake ─────────────────────────

    public function service(): AiService
    {
        $fake   = $this;
        $mock   = \Mockery::mock(AiService::class);

        $mock->shouldReceive('analyzeScan')
             ->andReturnUsing(function () use ($fake) {
                 $fake->recordedCalls[] = ['method' => 'analyzeScan', 'args' => func_get_args()];
                 return array_shift($fake->scanQueue) ?? $fake->defaultScanResult();
             });

        $mock->shouldReceive('getScanDemo')
             ->andReturnUsing(function () use ($fake) {
                 $fake->recordedCalls[] = ['method' => 'getScanDemo', 'args' => func_get_args()];
                 return array_shift($fake->demoQueue) ?? $fake->defaultDemoResult();
             });

        $mock->shouldReceive('getChatResponse')
             ->andReturnUsing(function () use ($fake) {
                 $fake->recordedCalls[] = ['method' => 'getChatResponse', 'args' => func_get_args()];
                 return array_shift($fake->chatQueue) ?? $fake->defaultChatResponse();
             });

        $mock->shouldReceive('analyzePhoto')
             ->andReturnUsing(function () use ($fake) {
                 $fake->recordedCalls[] = ['method' => 'analyzePhoto', 'args' => func_get_args()];
                 return array_shift($fake->photoQueue) ?? $fake->defaultChatResponse();
             });

        $mock->shouldReceive('healthCheck')
             ->andReturnUsing(fn () => $fake->healthValue);

        return $mock;
    }

    // ── Default payloads ───────────────────────────────────────────────────

    public function defaultScanResult(): array
    {
        return [
            'skin_tone'               => 'medium',
            'undertone'               => 'warm',
            'face_shape'              => 'oval',
            'skin_type'               => 'combination',
            'skin_age'                => 26,
            'real_age'                => 25,
            'harmony_score'           => 74,
            'hydration_score'         => 65,
            'pigmentation_score'      => 48,
            'acne_score'              => 30,
            'aging_score'             => 20,
            'elasticity_score'        => 65,
            'hf_acne_severity'        => 'mild',
            'hf_skin_type'            => 'combination',
            'hf_undertone'            => 'warm',
            'hf_acne_confidence'      => 85.0,
            'hf_skin_type_confidence' => 78.0,
            'hf_undertone_confidence' => 72.0,
            'hf_acne_raw'             => '{}',
            'hf_skin_type_raw'        => '{}',
            'hf_undertone_raw'        => '{}',
            'facial_zones'            => [
                'forehead' => 'mild', 'nose' => 'moderate',
                'left_cheek' => 'mild', 'right_cheek' => 'mild', 'chin' => 'moderate',
            ],
            'visible_concerns'        => ['acne', 'dark spots'],
            'face_shape_confidence'   => 88.0,
            'face_shape_reason'       => 'Oval contour',
            'face_shape_measurements' => ['width' => 120, 'length' => 150],
        ];
    }

    public function defaultDemoResult(): array
    {
        return array_merge($this->defaultScanResult(), ['is_demo' => true]);
    }

    public function defaultChatResponse(): array
    {
        return [
            'reply'        => 'Use a gentle cleanser twice daily. [PRODUCT:CLN-001:Foam Cleanser]',
            'product_tags' => [['sku' => 'CLN-001', 'name' => 'Foam Cleanser']],
        ];
    }

    // ── Factory ────────────────────────────────────────────────────────────

    public static function make(): static
    {
        return new static();
    }
}
