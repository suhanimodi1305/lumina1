/* ═══════════════════════════════════════════════════════════════
   LUMINA — Core JavaScript (no jQuery dependency)
   ═══════════════════════════════════════════════════════════════ */

'use strict';

// ── CSRF helper ────────────────────────────────────────────────
window.lumina = {
    csrf: () => document.querySelector('meta[name=csrf-token]')?.content ?? '',
};

// ── Intersection Observer: fade-in-up on scroll ────────────────
(function initScrollAnimations() {
    const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
                io.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    // Pause all fade-in-up elements until they scroll into view
    document.querySelectorAll('.fade-in-up').forEach(el => {
        // Only pause elements that are not already in view
        const rect = el.getBoundingClientRect();
        if (rect.top > window.innerHeight) {
            el.style.animationPlayState = 'paused';
            io.observe(el);
        }
    });
})();

// ── Count-up animation for dashboard stats ─────────────────────
(function initCountUp() {
    const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            const el  = entry.target;
            const end = parseInt(el.dataset.count, 10);
            if (isNaN(end)) return;

            let start = 0;
            const duration = 1500;
            const step = Math.ceil(end / (duration / 16));
            const timer = setInterval(() => {
                start = Math.min(start + step, end);
                el.textContent = start.toLocaleString();
                if (start >= end) clearInterval(timer);
            }, 16);

            io.unobserve(el);
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('[data-count]').forEach(el => io.observe(el));
})();

// ── Score bars: animate when visible ──────────────────────────
(function initScoreBars() {
    const io = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            entry.target.querySelectorAll('.score-bar[data-width]').forEach(bar => {
                const w = bar.dataset.width;
                requestAnimationFrame(() => {
                    bar.style.transition = 'width 1.2s cubic-bezier(.25,.46,.45,.94)';
                    bar.style.width      = w + '%';
                });
            });
            io.unobserve(entry.target);
        });
    }, { threshold: 0.3 });

    document.querySelectorAll('.lumina-card').forEach(card => {
        if (card.querySelector('.score-bar')) io.observe(card);
    });
})();

// ── Add-to-cart AJAX (replaces full page reload) ───────────────
(function initAjaxCart() {
    document.addEventListener('submit', async function(e) {
        const form = e.target;
        if (!form.classList.contains('cart-ajax-form') && !form.querySelector('[name=product_id]')) return;

        // Only intercept product card add-to-cart forms
        const addBtn = form.querySelector('.add-cart-btn');
        if (!addBtn) return;

        e.preventDefault();

        const originalHtml = addBtn.innerHTML;
        addBtn.disabled    = true;
        addBtn.innerHTML   = '<span class="spinner-border spinner-border-sm"></span>';

        try {
            const res  = await fetch(form.action, {
                method:  'POST',
                headers: { 'X-CSRF-TOKEN': lumina.csrf() },
                body:    new FormData(form),
            });
            const data = await res.json();

            if (data.success) {
                addBtn.innerHTML = '<i class="bi bi-check-lg me-1"></i>Added!';
                addBtn.classList.add('btn-success');
                addBtn.classList.remove('btn-lumina');

                // Update cart badge
                const badge = document.querySelector('.cart-badge');
                if (badge && data.cart_count) {
                    badge.textContent = data.cart_count;
                    badge.classList.remove('d-none');
                }

                setTimeout(() => {
                    addBtn.innerHTML = originalHtml;
                    addBtn.disabled  = false;
                    addBtn.classList.remove('btn-success');
                    addBtn.classList.add('btn-lumina');
                }, 2000);
            }
        } catch {
            addBtn.innerHTML = originalHtml;
            addBtn.disabled  = false;
        }
    });
})();

// ── Auto-dismiss alerts after 5s ──────────────────────────────
(function initAutoDismissAlerts() {
    setTimeout(() => {
        document.querySelectorAll('.alert.alert-dismissible').forEach(alert => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        });
    }, 5000);
})();

// ── Rewards points pop animation on redeem ─────────────────────
(function initRewardsPop() {
    document.querySelectorAll('.redeem-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const badge = document.querySelector('.points-balance-badge');
            if (badge) badge.classList.add('points-pop');
        });
    });
})();

// ── Checkout step transitions ──────────────────────────────────
(function initCheckoutSteps() {
    const steps = document.querySelectorAll('.checkout-step');
    if (!steps.length) return;

    steps.forEach((step, i) => {
        step.style.animationDelay = (i * 0.1) + 's';
        step.classList.add('checkout-step-enter');
    });
})();

// ── Gender card highlight ──────────────────────────────────────
(function initGenderCards() {
    document.querySelectorAll('.gender-check').forEach(card => {
        card.addEventListener('click', function() {
            document.querySelectorAll('.gender-check').forEach(c => c.classList.remove('selected'));
            this.classList.add('selected');
            const radio = this.querySelector('input[type=radio]');
            if (radio) radio.checked = true;
        });
        // Highlight already-checked on page load
        const radio = card.querySelector('input[type=radio]');
        if (radio?.checked) card.classList.add('selected');
    });
})();
