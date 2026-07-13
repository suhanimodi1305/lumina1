<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="csrf-token" content="<?php echo e(csrf_token()); ?>">
    <title><?php echo $__env->yieldContent('title', 'Lumina Beauty'); ?> — Lumina AI Beauty Platform</title>
    <meta name="description" content="<?php echo $__env->yieldContent('meta_description', 'AI-powered beauty advisor for skincare, makeup, and K-Beauty.'); ?>">

    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <link href="<?php echo e(asset('css/lumina.css')); ?>" rel="stylesheet">
    <link href="<?php echo e(asset('css/animations.css')); ?>" rel="stylesheet">

    <?php echo $__env->yieldPushContent('styles'); ?>
</head>
<body class="lumina-app">


<nav class="navbar navbar-expand-lg lumina-navbar sticky-top">
    <div class="container-fluid px-4">
        <a class="navbar-brand lumina-brand" href="<?php echo e(route('home')); ?>">
            <span class="brand-icon">✨</span> Lumina
        </a>
        <button class="navbar-toggler border-0" type="button" data-bs-toggle="collapse" data-bs-target="#navMain">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navMain">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item"><a class="nav-link" href="<?php echo e(route('scan.upload')); ?>"><i class="bi bi-camera"></i> Skin Scan</a></li>
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">Products</a>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="<?php echo e(route('products.index', ['range'=>'makeup'])); ?>">💄 Makeup</a></li>
                        <li><a class="dropdown-item" href="<?php echo e(route('products.index', ['range'=>'korean'])); ?>">🌸 K-Beauty</a></li>
                        <li><a class="dropdown-item" href="<?php echo e(route('products.index', ['range'=>'ayurvedic'])); ?>">🌿 Ayurvedic</a></li>
                        <li><a class="dropdown-item" href="<?php echo e(route('products.index', ['range'=>'pharmacy'])); ?>">💊 Pharmacy</a></li>
                    </ul>
                </li>
                <li class="nav-item"><a class="nav-link" href="<?php echo e(route('chat.index')); ?>"><i class="bi bi-chat-heart"></i> AI Chat</a></li>
                <li class="nav-item"><a class="nav-link" href="<?php echo e(route('doctor.landing')); ?>"><i class="bi bi-clipboard2-pulse"></i> Doctor</a></li>
                <li class="nav-item"><a class="nav-link" href="<?php echo e(route('memberships.index')); ?>"><i class="bi bi-star"></i> Membership</a></li>
            </ul>

            <ul class="navbar-nav ms-auto align-items-center gap-2">
                
                <li class="nav-item">
                    <a class="nav-link position-relative" href="<?php echo e(route('cart.index')); ?>">
                        <i class="bi bi-bag fs-5"></i>
                        <?php if(count(session('cart', [])) > 0): ?>
                            <span class="cart-badge badge rounded-pill bg-lumina-primary">
                                <?php echo e(collect(session('cart', []))->sum('quantity')); ?>

                            </span>
                        <?php endif; ?>
                    </a>
                </li>

                <?php if(auth()->guard()->check()): ?>
                    
                    <li class="nav-item">
                        <a class="nav-link" href="<?php echo e(route('rewards.index')); ?>">
                            <span class="points-pill">
                                ✨ <?php echo e(number_format(auth()->user()->profile?->loyalty_points ?? 0)); ?> pts
                            </span>
                        </a>
                    </li>

                    
                    <li class="nav-item">
                        <span class="tier-badge tier-<?php echo e(auth()->user()->profile?->effective_tier ?? 'normal'); ?>">
                            <?php echo e(strtoupper(auth()->user()->profile?->effective_tier ?? 'normal')); ?>

                        </span>
                    </li>

                    
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle d-flex align-items-center gap-2" href="#" data-bs-toggle="dropdown">
                            <div class="avatar-xs bg-lumina-primary text-white rounded-circle d-flex align-items-center justify-content-center">
                                <?php echo e(strtoupper(substr(auth()->user()->name, 0, 1))); ?>

                            </div>
                        </a>
                        <ul class="dropdown-menu dropdown-menu-end">
                            <li><h6 class="dropdown-header"><?php echo e(auth()->user()->name); ?></h6></li>
                            <li><a class="dropdown-item" href="<?php echo e(route('dashboard')); ?>"><i class="bi bi-person-circle me-2"></i>My Dashboard</a></li>
                            <li><a class="dropdown-item" href="<?php echo e(route('dashboard.scans')); ?>"><i class="bi bi-camera me-2"></i>My Scans</a></li>
                            <li><a class="dropdown-item" href="<?php echo e(route('dashboard.orders')); ?>"><i class="bi bi-bag-check me-2"></i>My Orders</a></li>
                            <li><a class="dropdown-item" href="<?php echo e(route('rewards.index')); ?>"><i class="bi bi-gift me-2"></i>Rewards</a></li>
                            <?php if(auth()->user()->hasRole(['admin'])): ?>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="/admin"><i class="bi bi-shield-lock me-2"></i>Admin Panel</a></li>
                            <?php endif; ?>
                            <?php if(auth()->user()->hasRole(['employee'])): ?>
                                <li><a class="dropdown-item" href="<?php echo e(route('employee.dashboard')); ?>"><i class="bi bi-briefcase me-2"></i>Employee Portal</a></li>
                            <?php endif; ?>
                            <?php if(auth()->user()->hasRole(['marketing'])): ?>
                                <li><a class="dropdown-item" href="<?php echo e(route('marketing.dashboard')); ?>"><i class="bi bi-megaphone me-2"></i>Marketing</a></li>
                            <?php endif; ?>
                            <li><hr class="dropdown-divider"></li>
                            <li>
                                <form method="POST" action="<?php echo e(route('logout')); ?>">
                                    <?php echo csrf_field(); ?>
                                    <button class="dropdown-item text-danger" type="submit"><i class="bi bi-box-arrow-right me-2"></i>Logout</button>
                                </form>
                            </li>
                        </ul>
                    </li>
                <?php else: ?>
                    <li class="nav-item"><a class="btn btn-outline-lumina btn-sm" href="<?php echo e(route('login')); ?>">Login</a></li>
                    <li class="nav-item"><a class="btn btn-lumina btn-sm" href="<?php echo e(route('register')); ?>">Sign Up</a></li>
                <?php endif; ?>
            </ul>
        </div>
    </div>
</nav>


<?php if(session('success') || session('error') || session('info')): ?>
    <div class="container-fluid px-4 mt-3">
        <?php if(session('success')): ?>
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="bi bi-check-circle-fill me-2"></i><?php echo e(session('success')); ?>

                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        <?php endif; ?>
        <?php if(session('error')): ?>
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="bi bi-exclamation-circle-fill me-2"></i><?php echo e(session('error')); ?>

                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        <?php endif; ?>
        <?php if(session('info')): ?>
            <div class="alert alert-info alert-dismissible fade show" role="alert">
                <i class="bi bi-info-circle-fill me-2"></i><?php echo e(session('info')); ?>

                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        <?php endif; ?>
    </div>
<?php endif; ?>


<main>
    <?php echo $__env->yieldContent('content'); ?>
</main>


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
                    <li><a href="<?php echo e(route('scan.upload')); ?>" class="footer-link">Skin Scan</a></li>
                    <li><a href="<?php echo e(route('products.index')); ?>" class="footer-link">Products</a></li>
                    <li><a href="<?php echo e(route('chat.index')); ?>" class="footer-link">AI Chat</a></li>
                    <li><a href="<?php echo e(route('doctor.landing')); ?>" class="footer-link">Doctor</a></li>
                </ul>
            </div>
            <div class="col-md-2">
                <h6 class="fw-semibold mb-3">Account</h6>
                <ul class="list-unstyled small">
                    <li><a href="<?php echo e(route('dashboard')); ?>" class="footer-link">Dashboard</a></li>
                    <li><a href="<?php echo e(route('memberships.index')); ?>" class="footer-link">Membership</a></li>
                    <li><a href="<?php echo e(route('rewards.index')); ?>" class="footer-link">Rewards</a></li>
                    <li><a href="<?php echo e(route('dashboard.orders')); ?>" class="footer-link">Orders</a></li>
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
            <span>© <?php echo e(date('Y')); ?> Lumina AI Beauty Platform</span>
            <span>Built with ❤️ for beautiful skin</span>
        </div>
    </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="<?php echo e(asset('js/lumina.js')); ?>"></script>
<?php echo $__env->yieldPushContent('scripts'); ?>
</body>
</html>
<?php /**PATH D:\lumina1\lumina-laravel\resources\views/layouts/app.blade.php ENDPATH**/ ?>