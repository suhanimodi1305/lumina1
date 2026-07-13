@extends('layouts.app')
@section('title', 'My Profile')

@section('content')
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-lg-7">
            <h2 class="fw-bold mb-4">My Profile</h2>

            @if(session('success'))
            <div class="alert alert-success">{{ session('success') }}</div>
            @endif

            <div class="card lumina-card shadow-sm mb-4">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Personal Details</h5>
                    <form method="POST" action="{{ route('dashboard.profile.update') }}">
                        @csrf @method('PUT')
                        <div class="mb-3">
                            <label class="form-label">Full Name</label>
                            <input type="text" name="name" class="form-control @error('name') is-invalid @enderror"
                                   value="{{ old('name', $user->name) }}" required>
                            @error('name')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Email</label>
                            <input type="email" class="form-control" value="{{ $user->email }}" disabled>
                            <div class="form-text">Email cannot be changed here.</div>
                        </div>
                        <div class="row g-3 mb-3">
                            <div class="col-md-6">
                                <label class="form-label">Phone</label>
                                <input type="tel" name="phone" class="form-control @error('phone') is-invalid @enderror"
                                       value="{{ old('phone', $user->profile?->phone) }}">
                                @error('phone')<div class="invalid-feedback">{{ $message }}</div>@enderror
                            </div>
                            <div class="col-md-6">
                                <label class="form-label">Date of Birth</label>
                                <input type="date" name="date_of_birth" class="form-control @error('date_of_birth') is-invalid @enderror"
                                       value="{{ old('date_of_birth', $user->profile?->date_of_birth?->format('Y-m-d')) }}">
                                @error('date_of_birth')<div class="invalid-feedback">{{ $message }}</div>@enderror
                            </div>
                        </div>
                        <div class="mb-4">
                            <label class="form-label">Gender</label>
                            <div class="d-flex gap-3">
                                @foreach(['female'=>'👩 Female','male'=>'👨 Male','other'=>'🧑 Other'] as $val=>$label)
                                <div class="form-check">
                                    <input class="form-check-input" type="radio" name="gender" id="g_{{ $val }}" value="{{ $val }}"
                                           {{ old('gender', $user->profile?->gender) === $val ? 'checked' : '' }}>
                                    <label class="form-check-label" for="g_{{ $val }}">{{ $label }}</label>
                                </div>
                                @endforeach
                            </div>
                        </div>
                        <button type="submit" class="btn btn-lumina">Save Changes</button>
                    </form>
                </div>
            </div>

            {{-- Account info --}}
            <div class="card lumina-card shadow-sm">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Account Info</h5>
                    <div class="row g-3">
                        <div class="col-6">
                            <div class="text-muted small mb-1">Membership Tier</div>
                            <span class="tier-badge tier-{{ $user->profile?->effective_tier ?? 'normal' }}">
                                {{ strtoupper($user->profile?->effective_tier ?? 'normal') }}
                            </span>
                        </div>
                        <div class="col-6">
                            <div class="text-muted small mb-1">Loyalty Points</div>
                            <div class="fw-bold text-lumina-primary">
                                ✨ {{ number_format($user->profile?->loyalty_points ?? 0) }} pts
                            </div>
                        </div>
                        @if($user->profile?->referral_code)
                        <div class="col-12">
                            <div class="text-muted small mb-1">Your Referral Code</div>
                            <div class="d-flex align-items-center gap-2">
                                <code class="fs-6 bg-light px-3 py-2 rounded-3">{{ $user->profile->referral_code }}</code>
                                <button class="btn btn-sm btn-outline-secondary copy-btn" data-text="{{ $user->profile->referral_code }}">
                                    <i class="bi bi-clipboard"></i>
                                </button>
                            </div>
                        </div>
                        @endif
                        <div class="col-6">
                            <div class="text-muted small mb-1">Member Since</div>
                            <div class="small fw-semibold">{{ $user->created_at->format('M Y') }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
@endsection

@push('scripts')
<script>
document.querySelectorAll('.copy-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        navigator.clipboard.writeText(this.dataset.text).then(() => {
            this.innerHTML = '<i class="bi bi-check2"></i>';
            setTimeout(() => this.innerHTML = '<i class="bi bi-clipboard"></i>', 2000);
        });
    });
});
</script>
@endpush
