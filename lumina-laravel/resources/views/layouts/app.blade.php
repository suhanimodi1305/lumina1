<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>@yield('title', 'Lumina Beauty') — Lumina AI Beauty Platform</title>
    <meta name="description" content="@yield('meta_description', 'AI-powered beauty advisor for skincare, makeup, and K-Beauty.')">

    {{-- Bootstrap 5 --}}
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    {{-- Bootstrap Icons --}}
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    {{-- Google Fonts --}}
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    {{-- Lumina styles --}}
    <link href="{{ asset('css/lumina.css') }}" rel="stylesheet">
    <link href="{{ asset('css/animations.css') }}" rel="stylesheet">

    @stack('styles')
</head>
<body class="lumina-app">

{{-- Navigation --}}
<nav class="navbar navbar-expand-lg lumina-navbar sticky-top">
    <div class="container-fluid px-4">
        <a class="navbar-brand lumina-brand" href="{{ route('home') }}">
            <span class="brand-icon">✨</span> Lumina
        </a>
        <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navMain">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navMain">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item"><a class="nav-link" href="{{ route('scan.upload') }}"><i class="bi bi-camera"></i> Skin Scan</a></li>
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Products</a>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="{{ route('products.index', ['range'=>'makeup']) }}">💄 Makeup</a></li>
                        <li><a class="dropdown-item" href="{{ route('products.index', ['range'=>'korean']) }}">🌸 K-Beauty</a></li>
                        <li><a class="dropdown-item" href="{{ route('products.index', ['range'=>'ayurvedic']) }}">🌿 Ayurvedic</a></li>
                        <li><a class="dropdown-item" href="{{ route('products.index', ['range'=>'pharmacy']) }}">💊 Pharmacy</a></li>
                    </ul>
                </li>
                <li class="nav-item"><a class="nav-link" href="{{ route('chat.index') }}"><i class="bi bi-chat-heart"></i> AI Chat</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ route('doctor.landing') }}"><i class="bi bi-clipboard2-pulse"></i> Doctor</a></li>
                <li class="nav-item"><a class="nav-link" href="{{ route('memberships.index') }}"><i class="bi bi-star"></i> Membership</a></li>
            </ul>

            <ul class="navbar-nav ms-auto align-items-center gap-2">
                {{-- Cart --}}
                <li class="nav-item">
                    <a class="nav-link position-relative" href="{{ route('cart.index') }}">
                        <i class="bi bi-bag fs-5"></i>
                        @if(count(session('cart', [])) > 0)
                            <span class="cart-badge badge rounded-pill bg-lumina-primary">
                                {{ collect(session('cart', []))->sum('quantity') }}
                            </span>
                        @endif
                    </a>
                </li>

                @auth
                    {{-- Points badge --}}
                    <li class="nav-item">
                        <a class="nav-link" href="{{ route('rewards.index') }}">
                            <span class="points-pill">
                                ✨ {{ number_format(auth()->user()->profile?->loyalty_points ?? 0) }} pts
                            </span>
                        </a>
                    </li>

                    {{-- Tier badge --}}
                    <li class="nav-item">
                        <span class="tier-badge tier-{{ auth()->user()->profile?->effective_tier ?? 'normal' }}">
                            {{ strtoupper(auth()->user()->profile?->effective_tier ?? 'normal') }}
                        </span>
                    </li>

                    {{-- User menu --}}
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle d-flex align-items-center gap-2" href="#" data-bs-toggle="dropdown">
                            <div class="avatar-xs bg-lumina-primary text-white rounded-circle d-flex align-items-center justify-content-center">
                                {{ strtoupper(substr(auth()->user()->name, 0, 1)) }}
                            </div>
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><h6 class="dropdown-header">{{ auth()->user()->name }}</h6></li>
                            <li><a class="dropdown-item" href="{{ route('dashboard') }}"><i class="bi bi-person-circle me-2"></i>My Dashboard</a></li>
                            <li><a class="dropdown-item" href="{{ route('dashboard.scans') }}"><i class="bi bi-camera me-2"></i>My Scans</a></li>
                            <li><a class="dropdown-item" href="{{ route('dashboard.orders') }}"><i class="bi bi-bag-check me-2"></i>My Orders</a></li>
                            <li><a class="dropdown-item" href="{{ route('rewards.index') }}"><i class="bi bi-gift me-2"></i>Rewards</a></li>
                            @if(auth()->user()->hasRole(['admin']))
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="/admin"><i class="bi bi-shield-lock me-2"></i>Admin Panel</a></li>
                            @endif
                            @if(auth()->user()->hasRole(['employee']))
                                <li><a class="dropdown-item" href="{{ route('employee.dashboard') }}"><i class="bi bi-briefcase me-2"></i>Employee Portal</a></li>
                            @endif
                            @if(auth()->user()->hasRole(['marketing']))
                                <li><a class="dropdown-item" href="{{ route('marketing.dashboard') }}"><i class="bi bi-megaphone me-2"></i>Marketing</a></li>
                            @endif
                            <li><hr class="dropdown-divider"></li>
                            <li>
                                <form method="POST" action="{{ route('logout') }}">
                                    @csrf
                                    <button class="dropdown-item text-danger" type="submit"><i class="bi bi-box-arrow-right me-2"></i>Logout</button>
                                </form>
                            </li>
                        </ul>
                    </li>
                @else
                    <li class="nav-item"><a class="btn btn-outline-lumina btn-sm" href="{{ route('login') }}">Login</a></li>
                    <li class="nav-item"><a class="btn btn-lumina btn-sm" href="{{ route('register') }}">Sign Up</a></li>
                @endauth
            </ul>
        </div>
    </div>
</nav>

{{-- Flash messages --}}
@if(session('success') || session('error') || session('info'))
    <div class="container-fluid px-4 mt-3">
        @if(session('success'))
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="bi bi-check-circle-fill me-2"></i>{{ session('success') }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        @endif
        @if(session('error'))
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="bi bi-exclamation-circle-fill me-2"></i>{{ session('error') }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        @endif
        @if(session('info'))
            <div class="alert alert-info alert-dismissible fade show" role="alert">
                <i class="bi bi-info-circle-fill me-2"></i>{{ session('info') }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        @endif
    </div>
@endif

{{-- Main content --}}
<main>
    @yield('content')
</main>

{{-- Footer --}}
<footer class="lumina-footer mt-5 py-4">
    <div class="container">
        <div class="row g-4">
            <div class="col-md-4">
                <h5 class="lumina-brand mb-3">✨ Lumina</h5>
                <p class="text-muted small">AI-powered beauty advisor for skincare, makeup, and K-Beauty. Personalised recommendations just for you.</p>
            </div>
            <div class="col-md-2">
                <h6 class="fw-semibold mb-3">Explore</h6>
                <ul class="list-unstyled small">
                    <li><a href="{{ route('scan.upload') }}" class="footer-link">Skin Scan</a></li>
                    <li><a href="{{ route('products.index') }}" class="footer-link">Products</a></li>
                    <li><a href="{{ route('chat.index') }}" class="footer-link">AI Chat</a></li>
                    <li><a href="{{ route('doctor.landing') }}" class="footer-link">Doctor</a></li>
                </ul>
            </div>
            <div class="col-md-2">
                <h6 class="fw-semibold mb-3">Account</h6>
                <ul class="list-unstyled small">
                    <li><a href="{{ route('dashboard') }}" class="footer-link">Dashboard</a></li>
                    <li><a href="{{ route('memberships.index') }}" class="footer-link">Membership</a></li>
                    <li><a href="{{ route('rewards.index') }}" class="footer-link">Rewards</a></li>
                    <li><a href="{{ route('dashboard.orders') }}" class="footer-link">Orders</a></li>
                </ul>
            </div>
            <div class="col-md-4">
                <h6 class="fw-semibold mb-3">Newsletter</h6>
                <div class="input-group input-group-sm">
                    <input type="email" class="form-control" placeholder="your@email.com">
                    <button class="btn btn-lumina" type="button">Subscribe</button>
                </div>
            </div>
        </div>
        <hr class="my-3 opacity-25">
        <div class="d-flex justify-content-between align-items-center small text-muted">
            <span>© {{ date('Y') }} Lumina AI Beauty Platform</span>
            <span>Built with ❤️ for beautiful skin</span>
        </div>
    </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="{{ asset('js/lumina.js') }}"></script>
@stack('scripts')
</body>
</html>
