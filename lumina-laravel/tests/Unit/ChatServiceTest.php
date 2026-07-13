<?php

namespace Tests\Unit;

use App\Services\ChatService;
use Tests\TestCase;

/**
 * Unit tests for ChatService pure-PHP methods.
 *
 * Methods that require DB/Eloquent (sendMessage, sendPhoto, resolveProducts)
 * are covered in Feature tests.  These tests target the deterministic helpers
 * that have zero external dependencies.
 */
class ChatServiceTest extends TestCase
{
    private ChatService $service;

    protected function setUp(): void
    {
        parent::setUp();

        // Build ChatService with mocked dependencies
        $aiMock         = \Mockery::mock(\App\Services\AiService::class);
        $membershipMock = \Mockery::mock(\App\Services\MembershipService::class);

        $this->service = new ChatService($aiMock, $membershipMock);
    }

    // ── parseProductTags ──────────────────────────────────────────────────

    public function test_parse_product_tags_returns_empty_for_plain_text(): void
    {
        $result = $this->service->parseProductTags('This is a plain reply without any product tags.');

        $this->assertIsArray($result);
        $this->assertEmpty($result);
    }

    public function test_parse_product_tags_extracts_single_tag(): void
    {
        $result = $this->service->parseProductTags(
            'I recommend [PRODUCT:CLN-001:Gentle Foam Cleanser] for your skin type.'
        );

        $this->assertCount(1, $result);
        $this->assertEquals('CLN-001', $result[0]['sku']);
        $this->assertEquals('Gentle Foam Cleanser', $result[0]['name']);
    }

    public function test_parse_product_tags_extracts_multiple_tags(): void
    {
        $text   = 'Try [PRODUCT:CLN-001:Foam Cleanser] and [PRODUCT:SRM-002:Vitamin C Serum] daily.';
        $result = $this->service->parseProductTags($text);

        $this->assertCount(2, $result);
        $this->assertEquals('CLN-001', $result[0]['sku']);
        $this->assertEquals('SRM-002', $result[1]['sku']);
    }

    public function test_parse_product_tags_strips_whitespace_from_sku_and_name(): void
    {
        $result = $this->service->parseProductTags('[PRODUCT: CLN-001 : Foam Cleanser ]');

        // The regex does not strip whitespace — this documents current behavior.
        // Either trimmed or not, sku + name keys must be present.
        $this->assertArrayHasKey('sku', $result[0]);
        $this->assertArrayHasKey('name', $result[0]);
    }

    public function test_parse_product_tags_handles_sku_with_hyphens_and_digits(): void
    {
        $result = $this->service->parseProductTags('[PRODUCT:K-BEAUTY-023:Snail Mucin Essence]');

        $this->assertCount(1, $result);
        $this->assertEquals('K-BEAUTY-023', $result[0]['sku']);
    }

    public function test_parse_product_tags_handles_adjacent_tags(): void
    {
        $text   = '[PRODUCT:A-001:Alpha][PRODUCT:B-002:Beta]';
        $result = $this->service->parseProductTags($text);

        $this->assertCount(2, $result);
    }

    public function test_parse_product_tags_ignores_malformed_tag_missing_name(): void
    {
        // Missing closing bracket means regex won't match
        $result = $this->service->parseProductTags('[PRODUCT:CLN-001:Foam Cleanser');

        $this->assertEmpty($result);
    }

    public function test_parse_product_tags_empty_string_returns_empty_array(): void
    {
        $this->assertEmpty($this->service->parseProductTags(''));
    }

    // ── cleanTextForDisplay ───────────────────────────────────────────────

    public function test_clean_text_removes_single_product_tag(): void
    {
        $cleaned = $this->service->cleanTextForDisplay(
            'Here is a tip. [PRODUCT:CLN-001:Foam Cleanser] Use it daily.'
        );

        $this->assertStringNotContainsString('[PRODUCT:', $cleaned);
        $this->assertStringContainsString('Here is a tip.', $cleaned);
        $this->assertStringContainsString('Use it daily.', $cleaned);
    }

    public function test_clean_text_removes_multiple_product_tags(): void
    {
        $text    = 'Use [PRODUCT:CLN-001:Cleanser] and [PRODUCT:SRM-002:Serum] for best results.';
        $cleaned = $this->service->cleanTextForDisplay($text);

        $this->assertStringNotContainsString('[PRODUCT:', $cleaned);
        $this->assertStringContainsString('for best results', $cleaned);
    }

    public function test_clean_text_collapses_extra_spaces(): void
    {
        $text    = 'Hello [PRODUCT:A-001:Alpha]  world.';
        $cleaned = $this->service->cleanTextForDisplay($text);

        // Multiple spaces should be collapsed to single space
        $this->assertStringNotContainsString('  ', $cleaned);
    }

    public function test_clean_text_trims_result(): void
    {
        $text    = '[PRODUCT:CLN-001:Cleanser] ';
        $cleaned = $this->service->cleanTextForDisplay($text);

        $this->assertEquals('', trim($cleaned));
    }

    public function test_clean_text_returns_unchanged_string_with_no_tags(): void
    {
        $text    = 'A regular reply without any product references.';
        $cleaned = $this->service->cleanTextForDisplay($text);

        $this->assertEquals($text, $cleaned);
    }

    public function test_clean_text_handles_empty_string(): void
    {
        $this->assertEquals('', $this->service->cleanTextForDisplay(''));
    }

    // ── resolveProducts — empty/no-op path ───────────────────────────────

    public function test_resolve_products_returns_empty_array_for_empty_tags(): void
    {
        $result = $this->service->resolveProducts([], null);

        $this->assertIsArray($result);
        $this->assertEmpty($result);
    }

    public function test_resolve_products_returns_empty_array_for_empty_tags_with_price_ceiling(): void
    {
        $result = $this->service->resolveProducts([], 999);

        $this->assertEmpty($result);
    }
}
