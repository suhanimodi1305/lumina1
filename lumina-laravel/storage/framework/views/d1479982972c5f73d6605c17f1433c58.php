<?php $__env->startSection('title', 'Create Account'); ?>

<h5 class="fw-bold mb-4 text-center">Join Lumina — It's Free</h5>

<form method="POST" action="<?php echo e(route('register')); ?>">
    <?php echo csrf_field(); ?>
    <div class="mb-3">
        <label for="name" class="form-label">Full Name</label>
        <input id="name" type="text" name="name" class="form-control <?php $__errorArgs = ['name'];
$__bag = $errors->getBag($__errorArgs[1] ?? 'default');
if ($__bag->has($__errorArgs[0])) :
if (isset($message)) { $__messageOriginal = $message; }
$message = $__bag->first($__errorArgs[0]); ?> is-invalid <?php unset($message);
if (isset($__messageOriginal)) { $message = $__messageOriginal; }
endif;
unset($__errorArgs, $__bag); ?>"
               value="<?php echo e(old('name')); ?>" required autofocus>
        <?php $__errorArgs = ['name'];
$__bag = $errors->getBag($__errorArgs[1] ?? 'default');
if ($__bag->has($__errorArgs[0])) :
if (isset($message)) { $__messageOriginal = $message; }
$message = $__bag->first($__errorArgs[0]); ?><div class="invalid-feedback"><?php echo e($message); ?></div><?php unset($message);
if (isset($__messageOriginal)) { $message = $__messageOriginal; }
endif;
unset($__errorArgs, $__bag); ?>
    </div>
    <div class="mb-3">
        <label for="email" class="form-label">Email</label>
        <input id="email" type="email" name="email" class="form-control <?php $__errorArgs = ['email'];
$__bag = $errors->getBag($__errorArgs[1] ?? 'default');
if ($__bag->has($__errorArgs[0])) :
if (isset($message)) { $__messageOriginal = $message; }
$message = $__bag->first($__errorArgs[0]); ?> is-invalid <?php unset($message);
if (isset($__messageOriginal)) { $message = $__messageOriginal; }
endif;
unset($__errorArgs, $__bag); ?>"
               value="<?php echo e(old('email')); ?>" required>
        <?php $__errorArgs = ['email'];
$__bag = $errors->getBag($__errorArgs[1] ?? 'default');
if ($__bag->has($__errorArgs[0])) :
if (isset($message)) { $__messageOriginal = $message; }
$message = $__bag->first($__errorArgs[0]); ?><div class="invalid-feedback"><?php echo e($message); ?></div><?php unset($message);
if (isset($__messageOriginal)) { $message = $__messageOriginal; }
endif;
unset($__errorArgs, $__bag); ?>
    </div>
    <div class="row g-3 mb-3">
        <div class="col">
            <label for="password" class="form-label">Password</label>
            <input id="password" type="password" name="password" class="form-control <?php $__errorArgs = ['password'];
$__bag = $errors->getBag($__errorArgs[1] ?? 'default');
if ($__bag->has($__errorArgs[0])) :
if (isset($message)) { $__messageOriginal = $message; }
$message = $__bag->first($__errorArgs[0]); ?> is-invalid <?php unset($message);
if (isset($__messageOriginal)) { $message = $__messageOriginal; }
endif;
unset($__errorArgs, $__bag); ?>"
                   required minlength="8">
            <?php $__errorArgs = ['password'];
$__bag = $errors->getBag($__errorArgs[1] ?? 'default');
if ($__bag->has($__errorArgs[0])) :
if (isset($message)) { $__messageOriginal = $message; }
$message = $__bag->first($__errorArgs[0]); ?><div class="invalid-feedback"><?php echo e($message); ?></div><?php unset($message);
if (isset($__messageOriginal)) { $message = $__messageOriginal; }
endif;
unset($__errorArgs, $__bag); ?>
        </div>
        <div class="col">
            <label for="password_confirmation" class="form-label">Confirm</label>
            <input id="password_confirmation" type="password" name="password_confirmation" class="form-control" required>
        </div>
    </div>

    <?php if(request('ref')): ?>
    <input type="hidden" name="referral_code" value="<?php echo e(request('ref')); ?>">
    <div class="alert alert-success py-2 small mb-3">
        <i class="bi bi-gift me-1"></i>Referral applied! You'll both earn bonus points.
    </div>
    <?php else: ?>
    <div class="mb-3">
        <label for="referral_code" class="form-label small">Referral Code <span class="text-muted">(optional)</span></label>
        <input id="referral_code" type="text" name="referral_code" class="form-control form-control-sm"
               value="<?php echo e(old('referral_code')); ?>" placeholder="Enter friend's code">
    </div>
    <?php endif; ?>

    <div class="form-check mb-4">
        <input class="form-check-input" type="checkbox" name="terms" id="terms" required>
        <label class="form-check-label small" for="terms">
            I agree to the <a href="#" class="text-lumina-primary">Terms</a> and <a href="#" class="text-lumina-primary">Privacy Policy</a>
        </label>
    </div>

    <button type="submit" class="btn btn-lumina w-100 py-2">Create Account</button>
</form>

<p class="text-center mt-4 mb-0 small text-muted">
    Already have an account?
    <a href="<?php echo e(route('login')); ?>" class="text-lumina-primary text-decoration-none fw-semibold">Sign In</a>
</p>
<?php /**PATH D:\lumina1\lumina-laravel\resources\views/auth/register.blade.php ENDPATH**/ ?>