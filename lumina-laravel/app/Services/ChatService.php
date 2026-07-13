<?php

namespace App\Services;

use App\Exceptions\AiServiceException;
use App\Models\Conversation;
use App\Models\Message;
use App\Models\Product;
use App\Models\User;
use Illuminate\Http\UploadedFile;

class ChatService
{
    public function __construct(
        private AiService          $aiService,
        private MembershipService  $membershipService,
    ) {}

    /**
     * Send a text message and get AI response.
     */
    public function sendMessage(Conversation $conversation, string $userMessage, User $user): array
    {
        // Save user message
        Message::create([
            'conversation_id' => $conversation->id,
            'role'            => 'user',
            'content'         => $userMessage,
            'created_at'      => now(),
        ]);

        $history     = $this->buildHistory($conversation);
        $scanContext = $conversation->scanResult ? $conversation->scanResult->toAiContext() : null;
        $tier        = $this->membershipService->getEffectiveTier($user);

        $aiResult = $this->aiService->getChatResponse($history, $scanContext, $conversation->mode, $tier);

        $reply = $aiResult['reply'] ?? '';

        $aiMessage = Message::create([
            'conversation_id' => $conversation->id,
            'role'            => 'assistant',
            'content'         => $reply,
            'created_at'      => now(),
        ]);

        // Auto-title from first user message
        if ($conversation->messageCount() === 2 && str_contains($conversation->title, 'Consultation')) {
            $conversation->update(['title' => mb_substr($userMessage, 0, 50) . (mb_strlen($userMessage) > 50 ? '…' : '')]);
        }

        $productTags        = $this->parseProductTags($reply);
        $priceCeiling       = $this->membershipService->getPriceCeiling($tier);
        $productSuggestions = $this->resolveProducts($productTags, $priceCeiling);

        return [
            'reply'               => $this->cleanTextForDisplay($reply),
            'raw_reply'           => $reply,
            'timestamp'           => $aiMessage->created_at->format('h:i A'),
            'conversation_title'  => $conversation->fresh()->title,
            'product_suggestions' => $productSuggestions,
        ];
    }

    /**
     * Send a photo for AI analysis within a chat context.
     */
    public function sendPhoto(Conversation $conversation, UploadedFile $photo, User $user): array
    {
        $bytes       = file_get_contents($photo->getRealPath());
        $base64      = base64_encode($bytes);
        $contentType = $photo->getMimeType() ?? 'image/jpeg';

        Message::create([
            'conversation_id' => $conversation->id,
            'role'            => 'user',
            'content'         => '[Photo uploaded for analysis]',
            'image_data'      => $base64,
            'created_at'      => now(),
        ]);

        $history  = $this->buildHistory($conversation);
        $aiResult = $this->aiService->analyzePhoto($history, $base64, $contentType, $conversation->mode);

        $reply = $aiResult['reply'] ?? '';

        $aiMessage = Message::create([
            'conversation_id' => $conversation->id,
            'role'            => 'assistant',
            'content'         => $reply,
            'created_at'      => now(),
        ]);

        $tier               = $this->membershipService->getEffectiveTier($user);
        $priceCeiling       = $this->membershipService->getPriceCeiling($tier);
        $productTags        = $this->parseProductTags($reply);
        $productSuggestions = $this->resolveProducts($productTags, $priceCeiling);

        return [
            'reply'               => $this->cleanTextForDisplay($reply),
            'raw_reply'           => $reply,
            'timestamp'           => $aiMessage->created_at->format('h:i A'),
            'image_url'           => "data:{$contentType};base64,{$base64}",
            'product_suggestions' => $productSuggestions,
        ];
    }

    /**
     * Parse [PRODUCT:SKU:name] tags from AI reply text.
     */
    public function parseProductTags(string $text): array
    {
        preg_match_all('/\[PRODUCT:([^:]+):([^\]]+)\]/', $text, $matches, PREG_SET_ORDER);

        return array_map(fn ($m) => [
            'sku'  => trim($m[1]),
            'name' => trim($m[2]),
        ], $matches);
    }

    /**
     * Strip product tags from text for clean display.
     */
    public function cleanTextForDisplay(string $text): string
    {
        $cleaned = preg_replace('/\[PRODUCT:[^:]+:[^\]]+\]/', '', $text);
        return preg_replace('/\s{2,}/', ' ', trim($cleaned));
    }

    /**
     * Resolve product tags to DB product dicts, filtered by price ceiling.
     */
    public function resolveProducts(array $productTags, ?int $priceCeiling): array
    {
        if (empty($productTags)) {
            return [];
        }

        $skus = array_column($productTags, 'sku');

        $query = Product::with('brand')->whereIn('sku', $skus);

        if ($priceCeiling !== null) {
            $query->whereNotNull('price')->where('price', '<=', $priceCeiling);
        }

        return $query->get()->map(fn (Product $p) => [
            'sku'         => $p->sku,
            'name'        => $p->name,
            'brand'       => $p->brand?->name,
            'description' => mb_substr($p->description ?? '', 0, 100),
            'image_url'   => $p->image_url,
            'price'       => $p->price_display,
        ])->toArray();
    }

    // ── Private helpers ────────────────────────────────────────────────────

    private function buildHistory(Conversation $conversation): array
    {
        $limit = config('lumina.chat.max_history_messages', 20);

        return $conversation->messages()
            ->latest('created_at')
            ->limit($limit)
            ->get()
            ->sortBy('created_at')
            ->map(fn (Message $m) => [
                'role'    => $m->role,
                'content' => $m->content,
            ])
            ->values()
            ->toArray();
    }
}
