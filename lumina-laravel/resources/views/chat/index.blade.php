@extends('layouts.app')
@section('title', 'My Conversations')

@section('content')
<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold mb-0">AI Conversations</h2>
        <div class="d-flex gap-2">
            @foreach(['doctor'=>['emoji'=>'👩‍⚕️','label'=>'Doctor'],'makeup'=>['emoji'=>'💄','label'=>'Makeup'],'kbeauty'=>['emoji'=>'🌸','label'=>'K-Beauty']] as $mode=>$info)
            <a href="{{ route('chat.create', ['mode'=>$mode]) }}" class="btn btn-sm btn-outline-lumina">
                {{ $info['emoji'] }} {{ $info['label'] }}
            </a>
            @endforeach
        </div>
    </div>

    @if($conversations->isEmpty())
    <div class="text-center py-5">
        <i class="bi bi-chat-heart fs-1 text-muted mb-3 d-block"></i>
        <h5>No conversations yet</h5>
        <p class="text-muted">Start a chat with Dr. Lumina, get makeup advice, or explore K-Beauty routines.</p>
        <div class="d-flex gap-3 justify-content-center mt-3">
            <a href="{{ route('chat.create', ['mode'=>'doctor']) }}" class="btn btn-lumina">👩‍⚕️ Ask Dr. Lumina</a>
            <a href="{{ route('chat.create', ['mode'=>'makeup']) }}" class="btn btn-outline-lumina">💄 Makeup</a>
        </div>
    </div>
    @else
    <div class="row g-3">
        @foreach($conversations as $conv)
        <div class="col-md-6 col-lg-4 fade-in-up">
            <a href="{{ route('chat.room', $conv) }}" class="text-decoration-none">
                <div class="card lumina-card shadow-sm h-100 hover-lift">
                    <div class="card-body p-4">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div class="mode-icon me-2">
                                {{ $conv->mode==='doctor'?'👩‍⚕️':($conv->mode==='makeup'?'💄':'🌸') }}
                            </div>
                            <span class="badge bg-light text-dark border text-capitalize" style="font-size:.7rem;">{{ $conv->mode }}</span>
                        </div>
                        <h6 class="fw-semibold text-dark mb-1">{{ Str::limit($conv->title, 50) }}</h6>
                        <p class="text-muted small mb-3">
                            {{ $conv->messages_count }} message{{ $conv->messages_count!=1?'s':'' }}
                            · {{ $conv->updated_at->diffForHumans() }}
                        </p>
                        @if($conv->scanResult)
                        <span class="badge bg-lumina-soft text-dark" style="font-size:.7rem;">🔬 Linked to Scan</span>
                        @endif
                    </div>
                </div>
            </a>
        </div>
        @endforeach
    </div>
    <div class="mt-4">{{ $conversations->links() }}</div>
    @endif
</div>
@endsection
