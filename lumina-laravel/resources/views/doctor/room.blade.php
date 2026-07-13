@extends('layouts.app')
@section('title', 'Consultation Room')

@section('content')
<div class="container-fluid py-3 px-4">
<div class="row g-4" style="height:calc(100vh - 120px)">

    {{-- Sidebar: appointment info --}}
    <div class="col-lg-3 d-none d-lg-flex flex-column">
        <div class="card lumina-card shadow-sm mb-3">
            <div class="card-body p-4">
                <h5 class="fw-semibold mb-3"><i class="bi bi-clipboard2-pulse text-lumina-primary me-2"></i>Consultation</h5>
                <div class="mb-2">
                    <span class="text-muted small">Doctor</span>
                    <div class="fw-semibold">Dr. {{ $appointment->doctor->user?->name }}</div>
                </div>
                <div class="mb-2">
                    <span class="text-muted small">Patient</span>
                    <div class="fw-semibold">{{ $appointment->patient?->name }}</div>
                </div>
                <div class="mb-2">
                    <span class="text-muted small">Date & Time</span>
                    <div class="fw-semibold">
                        {{ $appointment->appointment_date->format('d M Y') }}
                        at {{ date('h:i A', strtotime($appointment->slot_time)) }}
                    </div>
                </div>
                <div>
                    <span class="text-muted small">Status</span>
                    <div>
                        <span class="badge bg-{{ match($appointment->status){ 'confirmed'=>'success','pending'=>'warning','cancelled'=>'danger',default=>'secondary' } }}">
                            {{ ucfirst($appointment->status) }}
                        </span>
                    </div>
                </div>
            </div>
        </div>

        @if($appointment->scanResult)
        <div class="card lumina-card shadow-sm mb-3">
            <div class="card-body p-3">
                <h6 class="fw-semibold mb-2">🔬 Scan Results</h6>
                <div class="d-flex flex-wrap gap-1">
                    <span class="badge bg-light text-dark border" style="font-size:.7rem;">{{ ucfirst($appointment->scanResult->skin_type) }}</span>
                    <span class="badge bg-light text-dark border" style="font-size:.7rem;">Acne: {{ ucfirst($appointment->scanResult->hf_acne_severity) }}</span>
                </div>
                <a href="{{ route('results.show', $appointment->scanResult) }}" class="btn btn-sm btn-outline-lumina w-100 mt-2">View Full Report</a>
            </div>
        </div>
        @endif

        @if($appointment->prescription)
        <div class="card lumina-card shadow-sm border-success">
            <div class="card-body p-3">
                <h6 class="fw-semibold mb-2 text-success"><i class="bi bi-file-earmark-medical me-1"></i>Prescription</h6>
                <p class="small text-muted mb-2">{{ $appointment->prescription->created_at->format('d M Y') }}</p>
                @if($appointment->prescription->notes)
                <p class="small mb-2">{{ Str::limit($appointment->prescription->notes, 100) }}</p>
                @endif
                @if($appointment->prescription->file_path)
                <a href="{{ Storage::temporaryUrl($appointment->prescription->file_path, now()->addHour()) }}" class="btn btn-sm btn-success w-100" target="_blank">
                    <i class="bi bi-download me-1"></i>Download PDF
                </a>
                @endif
            </div>
        </div>
        @endif
    </div>

    {{-- Chat --}}
    <div class="col-lg-9 d-flex flex-column" style="height:100%">
        <div class="card lumina-card shadow-sm flex-grow-1 d-flex flex-column overflow-hidden">
            {{-- Messages --}}
            <div class="flex-grow-1 p-4 overflow-auto" id="consult-messages">
                @forelse($appointment->messages as $msg)
                <div class="d-flex mb-3 {{ $msg->role==='patient'?'justify-content-end':'justify-content-start' }}">
                    <div>
                        <div class="text-muted mb-1" style="font-size:.7rem;">
                            {{ $msg->role==='doctor'?'👩‍⚕️ Dr. ':'👤 ' }}{{ $msg->sender?->name }}
                        </div>
                        <div class="msg-bubble p-3 {{ $msg->role==='patient'?'bg-lumina-primary text-white':'bg-light' }}"
                             style="border-radius:12px;max-width:480px;">
                            {{ $msg->message }}
                        </div>
                        <div class="text-muted mt-1" style="font-size:.7rem;">{{ $msg->created_at->format('h:i A') }}</div>
                    </div>
                </div>
                @empty
                <div class="text-center text-muted py-5">
                    <i class="bi bi-chat-dots fs-1 mb-3 d-block"></i>
                    <p>Start the consultation by sending a message.</p>
                </div>
                @endforelse
            </div>

            {{-- Input --}}
            <div class="border-top p-3 d-flex gap-2">
                <textarea id="consult-input" class="form-control border-0 bg-light" rows="1"
                          placeholder="Type your message..." style="resize:none;"></textarea>
                <button id="consult-send" class="btn btn-lumina px-3">
                    <i class="bi bi-send-fill"></i>
                </button>
            </div>
        </div>
    </div>
</div>
</div>
@endsection

@push('scripts')
<script>
const appointmentId = '{{ $appointment->id }}';
const csrf = document.querySelector('meta[name=csrf-token]').content;
const messages = document.getElementById('consult-messages');
const input = document.getElementById('consult-input');
messages.scrollTop = messages.scrollHeight;

document.getElementById('consult-send').addEventListener('click', async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    try {
        const res = await fetch(`/doctor/consultation/${appointmentId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrf },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        const div = document.createElement('div');
        div.className = 'd-flex mb-3 justify-content-end';
        div.innerHTML = `<div><div class="msg-bubble p-3 bg-lumina-primary text-white" style="border-radius:12px;max-width:480px;">${data.message}</div><div class="text-muted mt-1" style="font-size:.7rem;">${data.created_at}</div></div>`;
        messages.appendChild(div);
        messages.scrollTop = messages.scrollHeight;
    } catch { alert('Failed to send message.'); }
});

input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); document.getElementById('consult-send').click(); }
});
</script>
@endpush
