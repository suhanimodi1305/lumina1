<?php

namespace App\Services;

use App\Exceptions\AiServiceException;
use Illuminate\Http\Client\RequestException;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class AiService
{
    private string $baseUrl;
    private string $token;
    private int $timeout;
    private int $retry;

    public function __construct()
    {
        $this->baseUrl = rtrim(config('ai.service_url', 'http://localhost:8001'), '/');
        $this->token   = config('ai.token', '');
        $this->timeout = config('ai.timeout', 30);
        $this->retry   = config('ai.retry', 1);
    }

    /**
     * POST multipart image to FastAPI scan/analyze.
     * Returns full analysis JSON array.
     *
     * @throws AiServiceException
     */
    public function analyzeScan(UploadedFile $image, string $gender = 'female'): array
    {
        $endpoint = $this->url('scan_analyze');

        try {
            $response = Http::withToken($this->token)
                ->timeout($this->timeout)
                ->retry($this->retry, 1000)
                ->attach('image', file_get_contents($image->getRealPath()), $image->getClientOriginalName())
                ->post($endpoint, ['gender' => $gender]);

            $response->throw();

            return $response->json();
        } catch (RequestException $e) {
            Log::error('AiService::analyzeScan HTTP error', [
                'status'   => $e->response->status(),
                'body'     => $e->response->body(),
            ]);
            throw new AiServiceException('Skin analysis service is unavailable. Please try again shortly.', 0, $e);
        } catch (\Throwable $e) {
            Log::error('AiService::analyzeScan error', ['message' => $e->getMessage()]);
            throw new AiServiceException('Failed to connect to the AI service.', 0, $e);
        }
    }

    /**
     * Get a demo scan profile by key.
     *
     * @throws AiServiceException
     */
    public function getScanDemo(string $profileKey, string $gender = 'female'): array
    {
        $endpoint = $this->url('scan_demo');

        try {
            $response = Http::withToken($this->token)
                ->timeout($this->timeout)
                ->post($endpoint, ['profile_key' => $profileKey, 'gender' => $gender]);

            $response->throw();

            return $response->json();
        } catch (\Throwable $e) {
            Log::error('AiService::getScanDemo error', ['message' => $e->getMessage()]);
            throw new AiServiceException('Demo profile service is unavailable.', 0, $e);
        }
    }

    /**
     * Send conversation history to get AI chat response.
     *
     * @throws AiServiceException
     */
    public function getChatResponse(
        array $history,
        ?array $scanContext,
        string $mode = 'doctor',
        string $userTier = 'normal'
    ): array {
        $endpoint = $this->url('chat_message');

        try {
            $response = Http::withToken($this->token)
                ->timeout($this->timeout)
                ->retry($this->retry, 500)
                ->post($endpoint, [
                    'history'      => $history,
                    'scan_context' => $scanContext,
                    'mode'         => $mode,
                    'user_tier'    => $userTier,
                ]);

            $response->throw();

            return $response->json();
        } catch (\Throwable $e) {
            Log::error('AiService::getChatResponse error', ['message' => $e->getMessage()]);
            throw new AiServiceException('Chat AI service is unavailable. Please try again.', 0, $e);
        }
    }

    /**
     * Send a photo (base64) for skin analysis in chat context.
     *
     * @throws AiServiceException
     */
    public function analyzePhoto(
        array $history,
        string $base64Image,
        string $mimeType,
        string $mode = 'doctor'
    ): array {
        $endpoint = $this->url('chat_photo');

        try {
            $response = Http::withToken($this->token)
                ->timeout($this->timeout)
                ->post($endpoint, [
                    'history'    => $history,
                    'image'      => $base64Image,
                    'mime_type'  => $mimeType,
                    'mode'       => $mode,
                ]);

            $response->throw();

            return $response->json();
        } catch (\Throwable $e) {
            Log::error('AiService::analyzePhoto error', ['message' => $e->getMessage()]);
            throw new AiServiceException('Photo analysis service is unavailable.', 0, $e);
        }
    }

    /**
     * Check if the AI service is reachable.
     */
    public function healthCheck(): bool
    {
        try {
            $response = Http::withToken($this->token)
                ->timeout(5)
                ->get($this->url('health'));

            return $response->successful();
        } catch (\Throwable) {
            return false;
        }
    }

    // ── Private helpers ───────────────────────────────────────────────────

    private function url(string $endpointKey): string
    {
        return $this->baseUrl . config("ai.endpoints.{$endpointKey}");
    }
}
