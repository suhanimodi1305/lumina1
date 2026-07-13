@section('title', 'Reset Password')

<h5 class="fw-bold mb-4 text-center">Set New Password</h5>

<form method="POST" action="{{ route('password.store') }}">
    @csrf
    <input type="hidden" name="token" value="{{ $request->route('token') }}">
    <div class="mb-3">
        <label for="email" class="form-label">Email</label>
        <input id="email" type="email" name="email" class="form-control @error('email') is-invalid @enderror"
               value="{{ old('email', $request->email) }}" required>
        @error('email')<div class="invalid-feedback">{{ $message }}</div>@enderror
    </div>
    <div class="mb-3">
        <label for="password" class="form-label">New Password</label>
        <input id="password" type="password" name="password" class="form-control @error('password') is-invalid @enderror"
               required minlength="8">
        @error('password')<div class="invalid-feedback">{{ $message }}</div>@enderror
    </div>
    <div class="mb-4">
        <label for="password_confirmation" class="form-label">Confirm Password</label>
        <input id="password_confirmation" type="password" name="password_confirmation" class="form-control" required>
    </div>
    <button type="submit" class="btn btn-lumina w-100">Reset Password</button>
</form>
