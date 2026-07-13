<?php

namespace Tests\Feature;

use App\Exceptions\AiServiceException;
use App\Services\AiService;
use Illuminate\Http\Client\Request;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

/**
 * Feature-level integration tests for AiService.
 *
 * These tests verify that AiService correctly constructs requests to the
 * FastAPI microservice and handles all response scenarios, using Http::fake().
 *
 * No real network calls are made.
 */
class AiServiceIntegrationTest extends TestCase
{
    private AiService $service;

    protected function setUp(): void
    {
        parent::setUp();

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

    // ── Bearer token is attached to every request ─────────────────────────

    public function test_bearer_token_is_sent_with_health_check(): void
    {
        Http::fake([
            'localhost:8001/api/v1/health' => Http::response(['status' => 'ok'], 200),
        ]);

        $this->service->healthCheck();

        Http::assertSent(function (Request $request) {
            return $request->hasHeader('Authorization', 'Bearer test-secret-token');
        });
    }

    public function test_bearer_token_is_sent_with_scan_analyze(): void
    {
        Http::fake([
            'localhost:8001/api/v1/scan/analyze' => Http::response($this->fakeScanPayload(), 200),
        ]);

        $file = UploadedFile::fake()->image('face.jpg');
        $this->service->analyzeScan($file, 'female');

        Http::assertSent(function (Request $request) {
            return $request->hasHeader('Authorization', 'Bearer test-secret-token');
        });
    }

    public function test_bearer_token_is_sent_with_chat_message(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/message' => Http::response(['reply' => 'ok', 'product_tags' => []], 200),
        ]);

        $this->service->getChatResponse([], null, 'doctor', 'normal');

        Http::assertSent(function (Request $request) {
            return $request->hasHeader('Authorization', 'Bearer test-secret-token');
        });
    }

    // ── Correct HTTP method + URL ─────────────────────────────────────────

    public function test_health_check_uses_get_method(): void
    {
        Http::fake([
            'localhost:8001/api/v1/health' => Http::response(['status' => 'ok'], 200),
        ]);

        $this->service->healthCheck();

        Http::assertSent(fn (Request $r) => $r->method() === 'GET' && str_contains($r->url(), '/api/v1/health'));
    }

    public function test_analyze_scan_uses_post_method(): void
    {
        Http::fake([
            'localhost:8001/api/v1/scan/analyze' => Http::response($this->fakeScanPayload(), 200),
        ]);

        $file = UploadedFile::fake()->image('face.jpg');
        $this->service->analyzeScan($file);

        Http::assertSent(fn (Request $r) => $r->method() === 'POST');
    }

    public function test_get_scan_demo_posts_to_correct_url(): void
    {
        Http::fake([
            'localhost:8001/api/v1/scan/demo' => Http::response(
                array_merge($this->fakeScanPayload(), ['is_demo' => true]),
                200
            ),
        ]);

        $this->service->getScanDemo('dry_cool');

        Http::assertSent(fn (Request $r) => str_contains($r->url(), '/api/v1/scan/demo'));
    }

    public function test_get_chat_response_posts_to_correct_url(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/message' => Http::response(['reply' => 'ok', 'product_tags' => []], 200),
        ]);

        $this->service->getChatResponse([], null);

        Http::assertSent(fn (Request $r) => str_contains($r->url(), '/api/v1/chat/message'));
    }

    public function test_analyze_photo_posts_to_correct_url(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/analyze-photo' => Http::response(['reply' => 'ok', 'product_tags' => []], 200),
        ]);

        $this->service->analyzePhoto([], base64_encode('img'), 'image/jpeg');

        Http::assertSent(fn (Request $r) => str_contains($r->url(), '/api/v1/chat/analyze-photo'));
    }

    // ── Exception message quality ─────────────────────────────────────────

    public function test_analyze_scan_exception_message_is_user_friendly(): void
    {
        Http::fake([
            'localhost:8001/api/v1/scan/analyze' => Http::response(null, 503),
        ]);

        try {
            $file = UploadedFile::fake()->image('face.jpg');
            $this->service->analyzeScan($file);
            $this->fail('Expected AiServiceException');
        } catch (AiServiceException $e) {
            $this->assertNotEmpty($e->getMessage());
            // Message should be user-readable, not a stack trace
            $this->assertStringNotContainsString('Trace', $e->getMessage());
        }
    }

    public function test_get_chat_response_exception_message_is_user_friendly(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/message' => Http::response(null, 500),
        ]);

        try {
            $this->service->getChatResponse([], null);
            $this->fail('Expected AiServiceException');
        } catch (AiServiceException $e) {
            $this->assertNotEmpty($e->getMessage());
        }
    }

    // ── Response body is decoded correctly ────────────────────────────────

    public function test_get_scan_demo_response_json_is_decoded_to_array(): void
    {
        $payload = array_merge($this->fakeScanPayload(), ['is_demo' => true, 'gender' => 'male']);

        Http::fake([
            'localhost:8001/api/v1/scan/demo' => Http::response($payload, 200),
        ]);

        $result = $this->service->getScanDemo('oily_warm', 'male');

        $this->assertIsArray($result);
        $this->assertTrue($result['is_demo']);
        $this->assertEquals('male', $result['gender']);
    }

    public function test_analyze_photo_response_is_decoded(): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/analyze-photo' => Http::response(
                ['reply' => 'Great skin!', 'product_tags' => [['sku' => 'A-001', 'name' => 'SPF Cream']]],
                200
            ),
        ]);

        $result = $this->service->analyzePhoto([], base64_encode('img'), 'image/jpeg');

        $this->assertEquals('Great skin!', $result['reply']);
        $this->assertCount(1, $result['product_tags']);
        $this->assertEquals('A-001', $result['product_tags'][0]['sku']);
    }

    // ── All 5 DEMO profile keys are usable ────────────────────────────────

    /**
     * @dataProvider demoProfileProvider
     */
    public function test_get_scan_demo_accepts_all_valid_profile_keys(string $profileKey): void
    {
        Http::fake([
            'localhost:8001/api/v1/scan/demo' => Http::response(
                array_merge($this->fakeScanPayload(), ['is_demo' => true]),
                200
            ),
        ]);

        $result = $this->service->getScanDemo($profileKey);

        $this->assertIsArray($result);
        $this->assertTrue($result['is_demo']);
    }

    public static function demoProfileProvider(): array
    {
        return [
            'combination_warm' => ['combination_warm'],
            'dry_cool'         => ['dry_cool'],
            'oily_warm'        => ['oily_warm'],
            'mature_neutral'   => ['mature_neutral'],
        ];
    }

    // ── Chat modes ────────────────────────────────────────────────────────

    /**
     * @dataProvider chatModeProvider
     */
    public function test_get_chat_response_accepts_all_chat_modes(string $mode): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/message' => Http::response(['reply' => 'ok', 'product_tags' => []], 200),
        ]);

        $result = $this->service->getChatResponse([], null, $mode, 'normal');

        $this->assertArrayHasKey('reply', $result);
    }

    public static function chatModeProvider(): array
    {
        return [
            'doctor'  => ['doctor'],
            'makeup'  => ['makeup'],
            'kbeauty' => ['kbeauty'],
        ];
    }

    // ── User tiers ────────────────────────────────────────────────────────

    /**
     * @dataProvider userTierProvider
     */
    public function test_get_chat_response_accepts_all_user_tiers(string $tier): void
    {
        Http::fake([
            'localhost:8001/api/v1/chat/message' => Http::response(['reply' => 'ok', 'product_tags' => []], 200),
        ]);

        $result = $this->service->getChatResponse([], null, 'doctor', $tier);

        $this->assertArrayHasKey('reply', $result);
    }

    public static function userTierProvider(): array
    {
        return [
            'normal' => ['normal'],
            'medium' => ['medium'],
            'vip'    => ['vip'],
        ];
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
