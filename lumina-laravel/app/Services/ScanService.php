<?php

namespace App\Services;

use App\Models\ScanResult;
use App\Models\SkinConcern;
use App\Models\User;
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;

class ScanService
{
    // Demo profiles matching Django DEMO_PROFILES exactly
    private const DEMO_PROFILES = [
        'combination_warm' => [
            'skin_tone' => 'medium', 'undertone' => 'warm', 'face_shape' => 'oval',
            'skin_type' => 'combination', 'skin_age' => 26, 'real_age' => 25,
            'harmony_score' => 74, 'hydration_score' => 65, 'pigmentation_score' => 48,
            'acne_score' => 30, 'aging_score' => 20, 'elasticity_score' => 65,
            'hf_acne_severity' => 'mild', 'hf_skin_type' => 'combination', 'hf_undertone' => 'warm',
            'hf_acne_confidence' => 85.0, 'hf_skin_type_confidence' => 78.0, 'hf_undertone_confidence' => 72.0,
            'facial_zones' => ['forehead' => 'mild', 'nose' => 'moderate', 'left_cheek' => 'mild', 'right_cheek' => 'mild', 'chin' => 'moderate'],
            'concerns' => ['dark_circles', 'pigmentation', 'blackheads', 'acne'],
        ],
        'dry_cool' => [
            'skin_tone' => 'fair', 'undertone' => 'cool', 'face_shape' => 'heart',
            'skin_type' => 'dry', 'skin_age' => 29, 'real_age' => 28,
            'harmony_score' => 68, 'hydration_score' => 40, 'pigmentation_score' => 30,
            'acne_score' => 10, 'aging_score' => 35, 'elasticity_score' => 55,
            'hf_acne_severity' => 'none', 'hf_skin_type' => 'dry', 'hf_undertone' => 'cool',
            'hf_acne_confidence' => 92.0, 'hf_skin_type_confidence' => 88.0, 'hf_undertone_confidence' => 81.0,
            'facial_zones' => ['forehead' => 'none', 'nose' => 'none', 'left_cheek' => 'none', 'right_cheek' => 'none', 'chin' => 'none'],
            'concerns' => ['dryness', 'redness', 'fine_lines', 'dark_circles'],
        ],
        'oily_warm' => [
            'skin_tone' => 'tan', 'undertone' => 'warm', 'face_shape' => 'round',
            'skin_type' => 'oily', 'skin_age' => 23, 'real_age' => 22,
            'harmony_score' => 78, 'hydration_score' => 75, 'pigmentation_score' => 55,
            'acne_score' => 65, 'aging_score' => 10, 'elasticity_score' => 70,
            'hf_acne_severity' => 'moderate', 'hf_skin_type' => 'oily', 'hf_undertone' => 'warm',
            'hf_acne_confidence' => 89.0, 'hf_skin_type_confidence' => 91.0, 'hf_undertone_confidence' => 76.0,
            'facial_zones' => ['forehead' => 'severe', 'nose' => 'severe', 'left_cheek' => 'moderate', 'right_cheek' => 'moderate', 'chin' => 'moderate'],
            'concerns' => ['acne', 'large_pores', 'oiliness', 'blackheads'],
        ],
        'mature_neutral' => [
            'skin_tone' => 'light', 'undertone' => 'neutral', 'face_shape' => 'square',
            'skin_type' => 'normal', 'skin_age' => 38, 'real_age' => 37,
            'harmony_score' => 65, 'hydration_score' => 55, 'pigmentation_score' => 60,
            'acne_score' => 15, 'aging_score' => 55, 'elasticity_score' => 50,
            'hf_acne_severity' => 'none', 'hf_skin_type' => 'normal', 'hf_undertone' => 'neutral',
            'hf_acne_confidence' => 87.0, 'hf_skin_type_confidence' => 83.0, 'hf_undertone_confidence' => 79.0,
            'facial_zones' => ['forehead' => 'none', 'nose' => 'none', 'left_cheek' => 'none', 'right_cheek' => 'none', 'chin' => 'none'],
            'concerns' => ['aging', 'fine_lines', 'dullness', 'pigmentation'],
        ],
    ];

    public function __construct(private AiService $aiService) {}

    public function processUpload(UploadedFile $file, ?User $user, string $gender, string $sessionKey): ScanResult
    {
        $aiResult = $this->aiService->analyzeScan($file, $gender);

        $scan = ScanResult::create([
            'user_id'                 => $user?->id,
            'session_key'             => $sessionKey,
            'is_demo'                 => false,
            'gender'                  => $gender,
            'scan_image'              => $this->storeImage($file),
            'skin_tone'               => $aiResult['skin_tone'] ?? 'medium',
            'undertone'               => $aiResult['undertone'] ?? 'neutral',
            'face_shape'              => $aiResult['face_shape'] ?? 'oval',
            'skin_type'               => $aiResult['skin_type'] ?? 'normal',
            'skin_age'                => $aiResult['skin_age'] ?? 25,
            'real_age'                => 25,
            'harmony_score'           => $aiResult['harmony_score'] ?? 75,
            'hydration_score'         => $aiResult['hydration_score'] ?? 60,
            'pigmentation_score'      => $aiResult['pigmentation_score'] ?? 30,
            'acne_score'              => $aiResult['acne_score'] ?? 20,
            'aging_score'             => $aiResult['aging_score'] ?? 25,
            'elasticity_score'        => $aiResult['elasticity_score'] ?? 65,
            'hf_acne_severity'        => $aiResult['hf_acne_severity'] ?? 'none',
            'hf_skin_type'            => $aiResult['hf_skin_type'] ?? 'normal',
            'hf_undertone'            => $aiResult['hf_undertone'] ?? 'neutral',
            'hf_acne_confidence'      => $aiResult['hf_acne_confidence'] ?? 0.0,
            'hf_skin_type_confidence' => $aiResult['hf_skin_type_confidence'] ?? 0.0,
            'hf_undertone_confidence' => $aiResult['hf_undertone_confidence'] ?? 0.0,
            'hf_acne_raw'             => $aiResult['hf_acne_raw'] ?? '',
            'hf_skin_type_raw'        => $aiResult['hf_skin_type_raw'] ?? '',
            'hf_undertone_raw'        => $aiResult['hf_undertone_raw'] ?? '',
            'facial_zones'            => $aiResult['facial_zones'] ?? [],
        ]);

        $this->mapConcernsFromAiResult($aiResult, $scan);

        return $scan;
    }

    public function createDemo(string $profileKey, string $gender, ?User $user, string $sessionKey): ScanResult
    {
        $profile  = self::DEMO_PROFILES[$profileKey] ?? self::DEMO_PROFILES['combination_warm'];
        $concerns = $profile['concerns'];
        unset($profile['concerns']);

        $scan = ScanResult::create(array_merge($profile, [
            'user_id'     => $user?->id,
            'session_key' => $sessionKey,
            'is_demo'     => true,
            'gender'      => $gender,
        ]));

        foreach ($concerns as $slug) {
            $concern = SkinConcern::where('slug', $slug)->first();
            if ($concern) {
                $scan->detectedConcerns()->attach($concern->id);
            }
        }

        return $scan;
    }

    public function buildScanContext(ScanResult $scan): array
    {
        return $scan->toAiContext();
    }

    private function storeImage(UploadedFile $file): string
    {
        $path = $file->store('scans/' . now()->format('Y/m/d'), 'private');
        return $path;
    }

    private function mapConcernsFromAiResult(array $aiResult, ScanResult $scan): void
    {
        $slugsToAdd = [];

        // From AI visible_concerns
        $visionMap = [
            'acne' => 'acne', 'pimples' => 'acne', 'blackheads' => 'blackheads',
            'dark spots' => 'pigmentation', 'hyperpigmentation' => 'pigmentation',
            'dark circles' => 'dark_circles', 'dryness' => 'dryness',
            'oiliness' => 'oiliness', 'redness' => 'redness',
            'fine lines' => 'fine_lines', 'wrinkles' => 'fine_lines',
            'large pores' => 'large_pores', 'dullness' => 'dullness',
        ];

        foreach ($aiResult['visible_concerns'] ?? [] as $vc) {
            $lower = strtolower(trim($vc));
            foreach ($visionMap as $key => $slug) {
                if (str_contains($lower, $key)) {
                    $slugsToAdd[] = $slug;
                    break;
                }
            }
        }

        // Score-based
        if (($aiResult['hydration_score'] ?? 100) < 70)  $slugsToAdd[] = 'dark_circles';
        if (($aiResult['pigmentation_score'] ?? 0) > 40)  $slugsToAdd[] = 'pigmentation';
        if (($aiResult['acne_score'] ?? 0) > 30)           $slugsToAdd[] = 'blackheads';
        if (($aiResult['hydration_score'] ?? 100) < 50)   $slugsToAdd[] = 'dryness';
        if (($aiResult['aging_score'] ?? 0) > 40) {
            $slugsToAdd[] = 'aging';
            $slugsToAdd[] = 'fine_lines';
        }
        if (($aiResult['skin_type'] ?? '') === 'oily' && ($aiResult['acne_score'] ?? 0) > 30) {
            $slugsToAdd[] = 'large_pores';
        }
        if (in_array($aiResult['hf_acne_severity'] ?? '', ['moderate', 'severe'], true)) {
            $slugsToAdd[] = 'redness';
        }
        if (($aiResult['skin_type'] ?? '') === 'oily') $slugsToAdd[] = 'oiliness';
        if (($aiResult['hydration_score'] ?? 100) < 55 || ($aiResult['harmony_score'] ?? 100) < 65) {
            $slugsToAdd[] = 'dullness';
        }

        $concerns = SkinConcern::whereIn('slug', array_unique($slugsToAdd))->get();
        $scan->detectedConcerns()->sync($concerns->pluck('id')->toArray());
    }
}
