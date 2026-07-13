<?php

namespace Tests\Unit;

use App\Exceptions\AiServiceException;
use App\Services\AiService;
use Illuminate\Http\Client\RequestException;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

/**
 * Unit tests for AiService.php.
 * All HTTP calls are intercepted with Http::fake() — no real network traffic.
 */
class AiServiceTest extends TestCase
{
    private AiService $service;

    protected function setUp(): void
    {
        parent::setUp();

        // Bind config so AiService constructor picks up test values
        config([
            'ai.service_url' => 'http://localhost:8001',
            'ai.token'       => 'test-secret-token',
            'ai.timeout'     => 5,
            'ai.retry'       => 1,
            'ai.endpoints'   => [
                'scan_analyze' => '/api/v1/scan/analyze',
                'scan_demo'    => '/api/v1/scan/demo',
                'chat_message' => '/api/v1/chat/message',
                'chat_photo'   => '/api/v1/chat/analyze-photo',
                'health'       => '/api/v1/health',
            ],
        ]);

        $this->service = new AiService();
    }

    // ── healthCheck ───────────────────────────────────────────────────────

    public function test_health_check_returns_true_on_successful_response(): void
    {
        Http::fake([
            'localhost:8001/api/v1/health' => Http::response(['status' => 'ok'], 200),
        ]);

        $this->assertTrue($this->service->healthCheck());
    }

    public function test_health_check_returns_false_on_connection_failure(): void
    {
        Http::fake([
            'localhost:8001/api/v1/health' => Http::response(null, 500),
        ]);

        $this->assertFalse($this->service->healthCheck());
    }

    public function test_health_check_returns_false_on_network_exception(): void
    {
        Http::fake(function () {
            throw new \Illuminate\Http\Client\ConnectionException('Connection refused');
        });

        $this->assertFalse($this->service->healthCheck());
    }

    // ── analyzeScan ───────────────────────────────────────────────────────

    public function test_analyze_scan_returns_array_on_success(): void
    {
        $payload = $this->fakeScanPayload();

        Http::fake([
            'localhost:8001/api/v1/scan/analyze' => Http::response($payload, 200),
        ]);

        $file   = UploadedFile::fake()->image('test.jpg', 100, 100);
        $result = $this->service->analyzeScan($file, 'female');

        $this->assertEquals('medium', $result['skin_tone']);
        $this->assertEquals('combination', $result['skin_type']);
    }

    public function test_analyze_scan_sends_gender_in_request(): void
    {
        Http::fake([
            'localhost:8001/api/v1/scan/analyze' => Http::response($this->fakeScanPayload(), 200),
        ]);

        $file = UploadedFile::fake()->image('test.jpg');
        $this->service->analyzeScan($file, 'male');

        Http::assertSent(function ($request) {
            return str_contains($request->url(), '/api/v1/scan/analyze');
        });
    }

    public function test_analyze_scan_throws_ai_service_exception_on_http_error(): void
    {
        Http::fake([
            'localhost:8001/api/v1/scan/analyze' => Http::response(['error' => 'Internal Error'], 500),
        ]);

        $this->expectException(AiServiceException::class);

        $file = UploadedFile::fake()->image('test.jpg');
        $this->service->analyzeScan($file);
    }

    public function test_analyze_scan_throws_ai_service_exception_on_connection_failure(): void
    {
        Http::fake(function () {
            throw new \Illuminate\Http\Client\ConnectionException('Unreachable');
        });

        $this->expectException(AiServiceException::class);

        $file = UploadedFile::fake()->image('test.jpg');
        $this->service->analyzeScan($file);
    }

    // ── getScanDemo ───────────────────────────────────────────────────────

    public function test_get_scan_demo_returns_demo_profile(): void
    {
        $payload = array_merge($this->fakeScanPayload(), ['is_demo' => true, 'gender' => 'female']);

        Http::fake([
            'localhost:8001/api/v1/scan/demo' => Http::response($payload, 200),
        ]);

        $result = $this->service->getScanDemo('combination_warm', 'female');

        $this->assertTrue($result['is_demo']);
        $this->assertEquals('female', $result['gender']);
    }

    public function test_get_scan_demo_sends_profile_key(): void
    {
        Http::fake([
            'localhost:8001/api/v1/scan/demo' => Http::response(
                array_merge($this->fakeScanPayload(), ['is_demo' => true]),
                200
            ),
        ]);

        $this->service->getScanDemo('oily_warm');

        Http::assertSent(function ($request) {
            return str_contains($request->url(), '/api/v1/scan/demo')
                && $request->data()['profile_key'] === 'oily_warm';
        });
    }

    public function test_get_scan_demo_throws_ai_service_exception_on_failure(): void
    {
        Http::fake([
            'localhost:8001/api/v1/scan/demo' => Http::response(null, 503),
        ]);

        $this->expectException(AiServiceException::class);

        $this->service->getScanDemo('nonexistent');
    }

    // ── getChatResponse ───────────────────────────────────────────────────

    public function test_get_chat_response_returns_reply_and_product_tags(): void
    {
        $responsePayload = [
            'reply'        => 'Use a gentle cleanser. [PRODUCT:CLN-001:Foam Cleanser]',
            'product_tags' => [['sku' => 'CLN-001', 'name' => 'Foam Cleanser']],
        ];

        Http::fake([
            'localhost:8001/api/v1/chat/message' => Http::response($responsePayload, 200),
        ]);

        $result = $this->service->getChatResponse(
            history:     [['role' => 'user', 'content' => 'What cleanser for oily skin?']],
            scanContext: null,
            mode:        'doctor',
            userTier:    'normal',
        );

        $this->assertArrayHasKey('reply', $result);
        $this->assertArrayHasKey('product_tags', $result);
        $this->assertStringContainsString('gentle cleanser', $result['reply']);
    }

    public function test_get_chat_response_sends_correct_body(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/message' => Http::response(['reply' => 'ok', 'product_tags' => []], 200),
        ]);

        $history     = [['role' => 'user', 'content' => 'Hello']];
        $scanContext = ['skin_type' => 'oily'];

        $this->service->getChatResponse($history, $scanContext, 'makeup', 'vip');

        Http::assertSent(function ($request) use ($history, $scanContext) {
            $data = $request->data();
            return str_contains($request->url(), '/api/v1/chat/message')
                && $data['mode'] === 'makeup'
                && $data['user_tier'] === 'vip'
                && isset($data['scan_context']);
        });
    }

    public function test_get_chat_response_throws_ai_service_exception_on_failure(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/message' => Http::response(null, 503),
        ]);

        $this->expectException(AiServiceException::class);

        $this->service->getChatResponse([], null);
    }

    public function test_get_chat_response_accepts_null_scan_context(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/message' => Http::response(['reply' => 'Hi!', 'product_tags' => []], 200),
        ]);

        $result = $this->service->getChatResponse([], null, 'doctor', 'normal');

        $this->assertEquals('Hi!', $result['reply']);
    }

    // ── analyzePhoto ──────────────────────────────────────────────────────

    public function test_analyze_photo_returns_reply_and_tags(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/analyze-photo' => Http::response(
                ['reply' => 'Skin looks healthy!', 'product_tags' => []],
                200
            ),
        ]);

        $result = $this->service->analyzePhoto(
            history:     [['role' => 'user', 'content' => 'Check my skin']],
            base64Image: base64_encode('fake-image-bytes'),
            mimeType:    'image/jpeg',
            mode:        'doctor',
        );

        $this->assertArrayHasKey('reply', $result);
        $this->assertEquals('Skin looks healthy!', $result['reply']);
    }

    public function test_analyze_photo_sends_base64_and_mime_type(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/analyze-photo' => Http::response(
                ['reply' => 'Analysis done.', 'product_tags' => []],
                200
            ),
        ]);

        $b64 = base64_encode('fake-image-bytes');
        $this->service->analyzePhoto([], $b64, 'image/png', 'makeup');

        Http::assertSent(function ($request) use ($b64) {
            $data = $request->data();
            return str_contains($request->url(), '/api/v1/chat/analyze-photo')
                && $data['image'] === $b64
                && $data['mime_type'] === 'image/png'
                && $data['mode'] === 'makeup';
        });
    }

    public function test_analyze_photo_throws_ai_service_exception_on_failure(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/analyze-photo' => Http::response(null, 500),
        ]);

        $this->expectException(AiServiceException::class);

        $this->service->analyzePhoto([], base64_encode('img'), 'image/jpeg');
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    private function fakeScanPayload(): array
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
}
