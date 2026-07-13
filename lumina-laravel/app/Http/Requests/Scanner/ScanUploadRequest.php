<?php

namespace App\Http\Requests\Scanner;

use Illuminate\Foundation\Http\FormRequest;

class ScanUploadRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'scan_image' => [
                'required',
                'file',
                'mimes:jpeg,jpg,png,webp',
                'max:' . (config('lumina.max_scan_size_mb', 5) * 1024),
            ],
            'gender' => ['nullable', 'in:male,female,other'],
        ];
    }

    public function messages(): array
    {
        return [
            'scan_image.required' => 'Please upload or capture a photo.',
            'scan_image.mimes'    => 'Only JPEG, PNG, or WebP images are accepted.',
            'scan_image.max'      => 'Image must be under ' . config('lumina.max_scan_size_mb', 5) . 'MB.',
        ];
    }
}
