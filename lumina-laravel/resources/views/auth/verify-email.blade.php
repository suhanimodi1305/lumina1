@section('title', 'Verify Email')

<div class="text-center py-3">
    <div class="mb-3" style="font-size:3rem;">📧</div>
    <h5 class="fw-bold mb-2">Verify Your Email</h5>
    <p class="text-muted small mb-4">
        Thanks for signing up! Please click the link in the email we sent to activate your account.
    </p>

    @if (session('status') == 'verification-link-sent')
    <div class="alert alert-success mb-3">A new verification link has been sent to your email.</div>
    @endif

    <form method="POST" action="{{ route('verification.send') }}" class="mb-3">
        @csrf
        <button type="submit" class="btn btn-lumina w-100">Resend Verification Email</button>
    </form>

    <form method="POST" action="{{ route('logout') }}">
        @csrf
        <button type="submit" class="btn btn-outline-secondary btn-sm w-100">Log Out</button>
    </form>
</div>
