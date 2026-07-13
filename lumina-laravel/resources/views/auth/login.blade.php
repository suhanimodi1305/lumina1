@section('title', 'Login')

@if (session('status'))
<div class="alert alert-success mb-3">{{ session('status') }}</div>
@endif

<h5 class="fw-bold mb-4 text-center">Sign in to Lumina</h5>

<form method="POST" action="{{ route('login') }}">
    @csrf
    <div class="mb-3">
        <label for="email" class="form-label">Email</label>
        <input id="email" type="email" name="email" class="form-control @error('email') is-invalid @enderror"
               value="{{ old('email') }}" required autofocus>
        @error('email')<div class="invalid-feedback">{{ $message }}</div>@enderror
    </div>
    <div class="mb-3">
        <div class="d-flex justify-content-between">
            <label for="password" class="form-label">Password</label>
            @if(Route::has('password.request'))
            <a href="{{ route('password.request') }}" class="small text-lumina-primary text-decoration-none">Forgot password?</a>
            @endif
        </div>
        <input id="password" type="password" name="password" class="form-control @error('password') is-invalid @enderror" required>
        @error('password')<div class="invalid-feedback">{{ $message }}</div>@enderror
    </div>
    <div class="form-check mb-4">
        <input class="form-check-input" type="checkbox" name="remember" id="remember">
        <label class="form-check-label small" for="remember">Remember me for 30 days</label>
    </div>
    <button type="submit" class="btn btn-lumina w-100 py-2">Sign In</button>
</form>

<p class="text-center mt-4 mb-0 small text-muted">
    Don't have an account?
    <a href="{{ route('register') }}" class="text-lumina-primary text-decoration-none fw-semibold">Sign Up Free</a>
</p>
