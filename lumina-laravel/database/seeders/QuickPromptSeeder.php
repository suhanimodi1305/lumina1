<?php

namespace Database\Seeders;

use App\Models\QuickPrompt;
use Illuminate\Database\Seeder;

class QuickPromptSeeder extends Seeder
{
    public function run(): void
    {
        $prompts = [
            // Doctor mode
            ['prompt_text' => 'I have acne on my cheeks',             'category' => 'doctor',  'sort_order' => 1],
            ['prompt_text' => 'My skin is very dry and flaky',        'category' => 'doctor',  'sort_order' => 2],
            ['prompt_text' => 'I have dark spots / pigmentation',     'category' => 'doctor',  'sort_order' => 3],
            ['prompt_text' => 'My skin is oily and shiny',            'category' => 'doctor',  'sort_order' => 4],
            ['prompt_text' => 'I have sensitive, reactive skin',      'category' => 'doctor',  'sort_order' => 5],
            ['prompt_text' => "What's my basic skincare routine?",    'category' => 'doctor',  'sort_order' => 6],
            // Makeup mode
            ['prompt_text' => 'Help me find my foundation shade',     'category' => 'makeup',  'sort_order' => 1],
            ['prompt_text' => 'What lipstick suits warm undertones?', 'category' => 'makeup',  'sort_order' => 2],
            ['prompt_text' => 'Recommend eyeshadow for brown eyes',   'category' => 'makeup',  'sort_order' => 3],
            ['prompt_text' => 'I want a natural no-makeup look',      'category' => 'makeup',  'sort_order' => 4],
            ['prompt_text' => 'Best drugstore products for Indian skin', 'category' => 'makeup', 'sort_order' => 5],
            ['prompt_text' => 'How to do a glass skin base?',         'category' => 'makeup',  'sort_order' => 6],
            // K-Beauty mode
            ['prompt_text' => 'Give me a K-Beauty routine for acne', 'category' => 'kbeauty', 'sort_order' => 1],
            ['prompt_text' => 'What is double cleansing?',            'category' => 'kbeauty', 'sort_order' => 2],
            ['prompt_text' => 'How do I get glass skin?',             'category' => 'kbeauty', 'sort_order' => 3],
            ['prompt_text' => 'Best K-Beauty routine for anti-aging', 'category' => 'kbeauty', 'sort_order' => 4],
            ['prompt_text' => 'What is the 3-skin method?',          'category' => 'kbeauty', 'sort_order' => 5],
            ['prompt_text' => 'Recommend products for sensitive skin','category' => 'kbeauty', 'sort_order' => 6],
        ];

        foreach ($prompts as $prompt) {
            QuickPrompt::firstOrCreate(
                ['prompt_text' => $prompt['prompt_text']],
                array_merge($prompt, ['is_active' => true])
            );
        }

        $this->command->info('Quick prompts seeded.');
    }
}
