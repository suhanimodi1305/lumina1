
<?php $__env->startSection('title', 'Lumina — AI Beauty Platform'); ?>

<?php $__env->startSection('content'); ?>


<section class="hero-section position-relative overflow-hidden">
    <div class="hero-bg-glow"></div>
    <div class="container py-5">
        <div class="row align-items-center g-5 py-4">
            <div class="col-lg-6 hero-content fade-in-up">
                <span class="hero-badge mb-3 d-inline-block">✨ AI-Powered Beauty Advisor</span>
                <h1 class="hero-title display-4 fw-bold mb-3">
                    Discover Your <br>
                    <span class="gradient-text">Perfect Skin</span>
                </h1>
                <p class="hero-subtitle text-muted mb-4 fs-5">
                    Upload a selfie. Our AI analyses your skin tone, face shape, acne, and concerns — then recommends the perfect products and routine for you.
                </p>
                <div class="d-flex flex-wrap gap-3">
                    <a href="<?php echo e(route('scan.upload')); ?>" class="btn btn-lumina btn-lg px-5 pulse-btn">
                        <i class="bi bi-camera me-2"></i>Start Free Scan
                    </a>
                    <a href="<?php echo e(route('scan.demo')); ?>" class="btn btn-outline-lumina btn-lg px-4">
                        Try Demo
                    </a>
                </div>
                <div class="hero-stats d-flex gap-4 mt-4">
                    <div class="stat-item text-center">
                        <div class="stat-number fw-bold" data-count="50000">50K+</div>
                        <div class="stat-label text-muted small">Scans Done</div>
                    </div>
                    <div class="stat-item text-center">
                        <div class="stat-number fw-bold" data-count="5000">5K+</div>
                        <div class="stat-label text-muted small">Products</div>
                    </div>
                    <div class="stat-item text-center">
                        <div class="stat-number fw-bold" data-count="98">98%</div>
                        <div class="stat-label text-muted small">Accuracy</div>
                    </div>
                </div>
            </div>
            <div class="col-lg-6 text-center hero-visual fade-in-up" style="animation-delay:0.2s">
                <div class="hero-scan-demo position-relative d-inline-block">
                    <div class="scan-ring scan-ring-1"></div>
                    <div class="scan-ring scan-ring-2"></div>
                    <div class="scan-ring scan-ring-3"></div>
                    <div class="hero-face-icon">
                        <i class="bi bi-person-circle"></i>
                    </div>
                    <div class="scan-result-card scan-card-1 fade-in-up" style="animation-delay:0.5s">
                        <span class="badge bg-success">Oily · Warm</span>
                    </div>
                    <div class="scan-result-card scan-card-2 fade-in-up" style="animation-delay:0.7s">
                        <span class="badge bg-primary">Face: Oval</span>
                    </div>
                    <div class="scan-result-card scan-card-3 fade-in-up" style="animation-delay:0.9s">
                        <span class="badge bg-warning text-dark">Harmony: 82%</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>


<section class="py-5 bg-lumina-soft">
    <div class="container">
        <h2 class="section-title text-center mb-5 fade-in-up">How Lumina Works</h2>
        <div class="row g-4 text-center">
            <?php $__currentLoopData = [
                ['icon'=>'bi-camera','step'=>'1','title'=>'Upload Selfie','desc'=>'Take or upload a clear photo. No filters.'],
                ['icon'=>'bi-cpu','step'=>'2','title'=>'AI Analysis','desc'=>'Our AI scans skin tone, face shape, acne, and 12+ concerns.'],
                ['icon'=>'bi-graph-up-arrow','step'=>'3','title'=>'Get Results','desc'=>'See your harmony score, hydration, pigmentation and more.'],
                ['icon'=>'bi-bag-heart','step'=>'4','title'=>'Shop Smarter','desc'=>'Get personalised product picks matched to your exact skin.'],
            ]; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $step): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
            <div class="col-md-3 fade-in-up">
                <div class="step-card h-100">
                    <div class="step-number"><?php echo e($step['step']); ?></div>
                    <div class="step-icon mb-3"><i class="bi <?php echo e($step['icon']); ?> fs-1 text-lumina-primary"></i></div>
                    <h5 class="fw-semibold"><?php echo e($step['title']); ?></h5>
                    <p class="text-muted small"><?php echo e($step['desc']); ?></p>
                </div>
            </div>
            <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
        </div>
    </div>
</section>


<section class="py-5">
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="section-title mb-0 fade-in-up">Shop by Category</h2>
            <a href="<?php echo e(route('products.index')); ?>" class="btn btn-sm btn-outline-lumina">View All</a>
        </div>
        <div class="row g-3">
            <?php $__currentLoopData = $categories; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $cat): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
            <div class="col-6 col-md-3 col-lg-2 fade-in-up">
                <a href="<?php echo e(route('products.index', ['category' => $cat->slug])); ?>" class="category-card text-decoration-none">
                    <div class="category-icon"><?php echo e($cat->icon); ?></div>
                    <div class="category-name"><?php echo e($cat->name); ?></div>
                </a>
            </div>
            <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
        </div>
    </div>
</section>


<?php if($featuredProducts->count()): ?>
<section class="py-5 bg-lumina-soft">
    <div class="container">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="section-title mb-0 fade-in-up">Featured Products</h2>
            <a href="<?php echo e(route('products.index', ['featured'=>1])); ?>" class="btn btn-sm btn-outline-lumina">See All</a>
        </div>
        <div class="row g-4">
            <?php $__currentLoopData = $featuredProducts; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $product): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                <?php echo $__env->make('components.product-card', ['product' => $product], array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?>
            <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
        </div>
    </div>
</section>
<?php endif; ?>


<section class="py-5 membership-cta-section">
    <div class="container">
        <div class="membership-cta-card text-center py-5 px-4 fade-in-up">
            <span class="hero-badge mb-3 d-inline-block">⭐ Upgrade Your Experience</span>
            <h2 class="fw-bold mb-3">Choose Your Membership</h2>
            <p class="text-muted mb-4 fs-5">Normal · Medium · VIP — unlock premium brands, priority AI consultations, and exclusive perks.</p>
            <a href="<?php echo e(route('memberships.index')); ?>" class="btn btn-lumina btn-lg px-5">
                <i class="bi bi-star-fill me-2"></i>View Plans
            </a>
        </div>
    </div>
</section>


<section class="py-5">
    <div class="container">
        <div class="row align-items-center g-4">
            <div class="col-md-6 fade-in-up">
                <span class="hero-badge mb-3 d-inline-block">👩‍⚕️ AI + Human Expertise</span>
                <h2 class="fw-bold mb-3">Book a Doctor Consultation</h2>
                <p class="text-muted mb-4">Start with AI analysis, then connect with a certified dermatologist for personalised prescription advice.</p>
                <a href="<?php echo e(route('doctor.landing')); ?>" class="btn btn-lumina btn-lg">
                    <i class="bi bi-clipboard2-pulse me-2"></i>Consult a Doctor
                </a>
            </div>
            <div class="col-md-6 text-center fade-in-up" style="animation-delay:0.2s">
                <div class="doctor-cta-visual">
                    <i class="bi bi-person-badge fs-1 text-lumina-primary"></i>
                    <div class="doctor-cta-badges mt-3 d-flex justify-content-center gap-2 flex-wrap">
                        <span class="badge bg-success-soft text-success px-3 py-2">✓ AI Analysis First</span>
                        <span class="badge bg-primary-soft text-primary px-3 py-2">✓ 1-on-1 Chat</span>
                        <span class="badge bg-warning-soft text-warning px-3 py-2">✓ Prescription Upload</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<?php $__env->stopSection(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH D:\lumina1\lumina-laravel\resources\views/home.blade.php ENDPATH**/ ?>