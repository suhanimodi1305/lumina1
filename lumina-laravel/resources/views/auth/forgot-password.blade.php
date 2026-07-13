@section('title', 'Forgot Password')

<h5 class="fw-bold mb-2 text-center">Reset Password</h5>
<p class="text-muted small text-center mb-4">Enter your email and we'll send a reset link.</p>

@if (session('status'))
<div class="alert alert-success mb-3">{{ session('status') }}</div>
@endif

<form method="POST" action="{{ route('password.email') }}">
    @csrf
    <div class="mb-4">
        <label for="email" class="form-label">Email</label>
        <input id="email" type="email" name="email" class="form-control @error('email') is-invalid @enderror"
               value="{{ old('email') }}" required autofocus>
        @error('email')<div class="invalid-feedback">{{ $message }}</div>@enderror
    </div>
    <button type="submit" class="btn btn-lumina w-100">Send Reset Link</button>
</form>

<p class="text-center mt-4 mb-0 small">
    <a href="{{ route('login') }}" class="text-lumina-primary text-decoration-none">← Back to Login</a>
</p>
