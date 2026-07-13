<?php

namespace App\Http\Controllers\Chat;

use App\Exceptions\AiServiceException;
use App\Http\Controllers\Controller;
use App\Models\Conversation;
use App\Models\QuickPrompt;
use App\Models\ScanResult;
use App\Services\ChatService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ChatController extends Controller
{
    private const VALID_MODES = ['doctor', 'makeup', 'kbeauty'];

    private const MODE_TITLES = [
        'doctor'  => 'AI Doctor Consultation',
        'makeup'  => 'Makeup Consultation',
        'kbeauty' => 'K-Beauty Consultation',
    ];

    public function __construct(private ChatService $chatService) {}

    public function index(Request $request): View
    {
        $conversations = Conversation::where('user_id', $request->user()->id)
            ->withCount('messages')
            ->latest()
            ->paginate(20);

        return view('chat.index', compact('conversations'));
    }

    public function create(Request $request): RedirectResponse
    {
        $mode = $request->query('mode', 'doctor');
        if (!in_array($mode, self::VALID_MODES, true)) {
            $mode = 'doctor';
        }

        $conversation = Conversation::create([
            'user_id' => $request->user()->id,
            'title'   => self::MODE_TITLES[$mode],
            'mode'    => $mode,
        ]);

        // Link scan if provided
        $scanId = $request->query('scan_id');
        if ($scanId) {
            $scan = ScanResult::find($scanId);
            if ($scan && ($scan->user_id === $request->user()->id || $scan->session_key === session()->getId())) {
                $conversation->update([
                    'scan_result_id' => $scan->id,
                    'title'          => (self::MODE_TITLES[$mode] ?? $mode) . " — Scan #{$scan->id}",
                ]);
            }
        }

        return redirect()->route('chat.room', $conversation);
    }

    public function room(Request $request, Conversation $conversation): View
    {
        abort_unless($conversation->user_id === $request->user()->id, 403);

        $messages = $conversation->messages()->get();

        $modePrompts = [
            'doctor'  => QuickPrompt::where('category', 'doctor')->where('is_active', true)->orderBy('sort_order')->pluck('prompt_text'),
            'makeup'  => QuickPrompt::where('category', 'makeup')->where('is_active', true)->orderBy('sort_order')->pluck('prompt_text'),
            'kbeauty' => QuickPrompt::where('category', 'kbeauty')->where('is_active', true)->orderBy('sort_order')->pluck('prompt_text'),
        ];

        return view('chat.room', [
            'conversation' => $conversation->load('scanResult'),
            'messages'     => $messages,
            'modePrompts'  => $modePrompts[$conversation->mode] ?? collect(),
            'validModes'   => self::VALID_MODES,
        ]);
    }

    public function sendMessage(Request $request, Conversation $conversation): JsonResponse
    {
        abort_unless($conversation->user_id === $request->user()->id, 403);

        $request->validate(['message' => 'required|string|max:2000']);

        try {
            $result = $this->chatService->sendMessage(
                $conversation,
                $request->input('message'),
                $request->user()
            );

            return response()->json($result);
        } catch (AiServiceException $e) {
            return response()->json(['error' => $e->getMessage()], 503);
        } catch (\Throwable $e) {
            return response()->json(['error' => 'An error occurred. Please try again.'], 500);
        }
    }

    public function sendPhoto(Request $request, Conversation $conversation): JsonResponse
    {
        abort_unless($conversation->user_id === $request->user()->id, 403);

        $request->validate([
            'photo' => 'required|file|mimes:jpeg,jpg,png,webp|max:5120',
        ]);

        try {
            $result = $this->chatService->sendPhoto(
                $conversation,
                $request->file('photo'),
                $request->user()
            );

            return response()->json($result);
        } catch (AiServiceException $e) {
            return response()->json(['error' => $e->getMessage()], 503);
        } catch (\Throwable $e) {
            return response()->json(['error' => 'Photo upload failed. Please try again.'], 500);
        }
    }

    public function switchMode(Request $request, Conversation $conversation): JsonResponse
    {
        abort_unless($conversation->user_id === $request->user()->id, 403);

        $request->validate(['mode' => 'required|in:doctor,makeup,kbeauty']);

        $conversation->update(['mode' => $request->input('mode')]);

        return response()->json(['success' => true, 'mode' => $conversation->mode]);
    }

    public function destroy(Request $request, Conversation $conversation): RedirectResponse
    {
        abort_unless($conversation->user_id === $request->user()->id, 403);

        $conversation->delete();

        return redirect()->route('chat.index')->with('success', 'Conversation deleted.');
    }
}
