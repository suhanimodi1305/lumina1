<?php

return [

    /*
    |--------------------------------------------------------------------------
    | Python AI Microservice
    |--------------------------------------------------------------------------
    | Laravel calls the FastAPI service for all AI operations.
    | The service wraps the existing Python AI code unchanged.
    */
    'service_url'   => env('AI_SERVICE_URL', 'http://localhost:8001'),
    'token'         => env('AI_SERVICE_TOKEN'),
    'timeout'       => (int) env('AI_SERVICE_TIMEOUT', 30),
    'retry'         => (int) env('AI_SERVICE_RETRY', 1),

    /*
    |--------------------------------------------------------------------------
    | Endpoints
    |--------------------------------------------------------------------------
    */
    'endpoints' => [
        'scan_analyze'    => '/api/v1/scan/analyze',
        'scan_demo'       => '/api/v1/scan/demo',
        'chat_message'    => '/api/v1/chat/message',
        'chat_photo'      => '/api/v1/chat/analyze-photo',
        'health'          => '/api/v1/health',
    ],

];
