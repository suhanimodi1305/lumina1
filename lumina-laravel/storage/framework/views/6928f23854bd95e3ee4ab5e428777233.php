
<?php $__env->startSection('title', 'AI Skin Analysis'); ?>

<?php $__env->startPush('styles'); ?>
<style>
.scan-drop-zone { border: 2px dashed var(--lumina-primary); border-radius: 16px; min-height: 280px; cursor: pointer; transition: all .3s; }
.scan-drop-zone:hover, .scan-drop-zone.dragover { border-color: var(--lumina-accent); background: rgba(var(--lumina-primary-rgb),.05); transform: scale(1.01); }
#preview-img { max-height: 280px; object-fit: cover; border-radius: 12px; }
</style>
<?php $__env->stopPush(); ?>

<?php $__env->startSection('content'); ?>
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-lg-8">

            
            <div class="text-center mb-5 fade-in-up">
                <div class="scan-pulse-ring d-inline-block mb-3">
                    <div class="scan-icon-wrap"><i class="bi bi-camera-fill fs-1 text-lumina-primary"></i></div>
                </div>
                <h1 class="fw-bold mb-2">AI Skin Analysis</h1>
                <p class="text-muted fs-5">Upload a clear selfie for your personalised skin report</p>
            </div>

            <?php if($errors->any()): ?>
            <div class="alert alert-danger mb-4">
                <ul class="mb-0"><?php $__currentLoopData = $errors->all(); $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $e): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?><li><?php echo e($e); ?></li><?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?></ul>
            </div>
            <?php endif; ?>

            
            <div class="card lumina-card shadow-sm mb-4 fade-in-up">
                <div class="card-body p-4">
                    <form method="POST" action="<?php echo e(route('scan.process')); ?>" enctype="multipart/form-data" id="scan-form">
                        <?php echo csrf_field(); ?>

                        
                        <div class="mb-4">
                            <label class="form-label fw-semibold">Select Gender</label>
                            <div class="d-flex gap-3">
                                <?php $__currentLoopData = ['female'=>'👩 Female','male'=>'👨 Male','other'=>'🧑 Other']; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $val=>$label): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                                <div class="form-check gender-check flex-fill text-center border rounded-3 p-3">
                                    <input class="form-check-input d-none" type="radio" name="gender" id="g_<?php echo e($val); ?>" value="<?php echo e($val); ?>" <?php echo e($val==='female'?'checked':''); ?>>
                                    <label class="form-check-label fw-medium w-100 cursor-pointer" for="g_<?php echo e($val); ?>"><?php echo e($label); ?></label>
                                </div>
                                <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
                            </div>
                        </div>

                        
                        <div class="scan-drop-zone d-flex flex-column align-items-center justify-content-center p-4 mb-3" id="drop-zone">
                            <div id="drop-placeholder" class="text-center">
                                <i class="bi bi-cloud-arrow-up fs-1 text-lumina-primary mb-2 d-block"></i>
                                <h5 class="fw-semibold mb-1">Drag & Drop Your Photo</h5>
                                <p class="text-muted small mb-3">or click to browse · JPEG, PNG, WebP · Max 5MB</p>
                                <button type="button" class="btn btn-outline-lumina" id="browse-btn">
                                    <i class="bi bi-folder2-open me-2"></i>Browse Photo
                                </button>
                            </div>
                            <img id="preview-img" class="d-none img-fluid" alt="Preview">
                        </div>
                        <input type="file" id="scan_image" name="scan_image" accept="image/jpeg,image/png,image/webp" class="d-none">

                        
                        <div class="scan-tips d-flex gap-3 flex-wrap mb-4">
                            <?php $__currentLoopData = ['Good lighting ✓','No glasses ✓','Face the camera ✓','No heavy makeup ✓']; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $tip): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                            <span class="badge bg-success-soft text-success px-3 py-2"><?php echo e($tip); ?></span>
                            <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
                        </div>

                        
                        <div class="d-flex gap-3 flex-wrap mb-4">
                            <button type="button" class="btn btn-outline-secondary" id="webcam-btn">
                                <i class="bi bi-webcam me-2"></i>Use Webcam
                            </button>
                        </div>

                        
                        <div id="webcam-area" class="d-none mb-4">
                            <video id="webcam-video" class="w-100 rounded-3 mb-2" autoplay playsinline style="max-height:260px;object-fit:cover;"></video>
                            <div class="d-flex gap-2">
                                <button type="button" class="btn btn-lumina" id="capture-btn"><i class="bi bi-camera me-2"></i>Capture</button>
                                <button type="button" class="btn btn-outline-secondary" id="stop-webcam-btn"><i class="bi bi-x-circle me-2"></i>Cancel</button>
                            </div>
                            <canvas id="webcam-canvas" class="d-none"></canvas>
                        </div>

                        <button type="submit" class="btn btn-lumina btn-lg w-100" id="analyze-btn" disabled>
                            <span id="analyze-text"><i class="bi bi-cpu me-2"></i>Analyse My Skin</span>
                            <span id="analyze-loading" class="d-none">
                                <span class="spinner-border spinner-border-sm me-2"></span>Analysing...
                            </span>
                        </button>
                    </form>
                </div>
            </div>

            
            <div id="analysis-progress" class="card lumina-card shadow-sm mb-4 d-none fade-in-up">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4 text-center">🔬 Analysing Your Skin...</h5>
                    <div class="analysis-steps">
                        <?php $__currentLoopData = [
                            ['icon'=>'bi-camera','label'=>'Processing image'],
                            ['icon'=>'bi-person-bounding-box','label'=>'Detecting face & landmarks'],
                            ['icon'=>'bi-palette','label'=>'Detecting skin tone & undertone'],
                            ['icon'=>'bi-emoji-frown','label'=>'Analysing acne & concerns'],
                            ['icon'=>'bi-bar-chart','label'=>'Generating your report'],
                        ]; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $i=>$s): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                        <div class="analysis-step d-flex align-items-center gap-3 mb-3" style="animation-delay:<?php echo e($i*0.8); ?>s">
                            <div class="step-dot"><i class="bi <?php echo e($s['icon']); ?>"></i></div>
                            <span><?php echo e($s['label']); ?></span>
                            <div class="step-spinner ms-auto spinner-border spinner-border-sm text-lumina-primary"></div>
                        </div>
                        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
                    </div>
                </div>
            </div>

            
            <div class="card lumina-card border-dashed fade-in-up">
                <div class="card-body p-4 text-center">
                    <p class="text-muted mb-3">Don't have a photo? Try our demo profiles</p>
                    <div class="d-flex flex-wrap gap-2 justify-content-center">
                        <?php $__currentLoopData = $demoProfiles; $__env->addLoop($__currentLoopData); foreach($__currentLoopData as $profile): $__env->incrementLoopIndices(); $loop = $__env->getLastLoop(); ?>
                        <a href="<?php echo e(route('scan.demo', ['profile'=>$profile])); ?>"
                           class="btn btn-sm btn-outline-secondary">
                            <?php echo e(ucwords(str_replace('_', ' ', $profile))); ?>

                        </a>
                        <?php endforeach; $__env->popLoop(); $loop = $__env->getLastLoop(); ?>
                    </div>
                </div>
            </div>

        </div>
    </div>
</div>
<?php $__env->stopSection(); ?>

<?php $__env->startPush('scripts'); ?>
<script>
const dropZone   = document.getElementById('drop-zone');
const fileInput  = document.getElementById('scan_image');
const browseBtn  = document.getElementById('browse-btn');
const previewImg = document.getElementById('preview-img');
const placeholder= document.getElementById('drop-placeholder');
const analyzeBtn = document.getElementById('analyze-btn');
const scanForm   = document.getElementById('scan-form');

browseBtn.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', e => showPreview(e.target.files[0]));

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
    e.preventDefault(); dropZone.classList.remove('dragover');
    if (e.dataTransfer.files[0]) { fileInput.files = e.dataTransfer.files; showPreview(e.dataTransfer.files[0]); }
});

function showPreview(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        previewImg.src = e.target.result;
        previewImg.classList.remove('d-none');
        placeholder.classList.add('d-none');
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

scanForm.addEventListener('submit', () => {
    document.getElementById('analyze-text').classList.add('d-none');
    document.getElementById('analyze-loading').classList.remove('d-none');
    document.getElementById('analysis-progress').classList.remove('d-none');
    analyzeBtn.disabled = true;
});

// Gender card selection
document.querySelectorAll('.gender-check').forEach(card => {
    card.addEventListener('click', function() {
        document.querySelectorAll('.gender-check').forEach(c => c.classList.remove('selected'));
        this.classList.add('selected');
        this.querySelector('input').checked = true;
    });
});

// Webcam
const webcamBtn    = document.getElementById('webcam-btn');
const webcamArea   = document.getElementById('webcam-area');
const webcamVideo  = document.getElementById('webcam-video');
const captureBtn   = document.getElementById('capture-btn');
const stopWebcamBtn= document.getElementById('stop-webcam-btn');
const webcamCanvas = document.getElementById('webcam-canvas');
let stream = null;

webcamBtn.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
        webcamVideo.srcObject = stream;
        webcamArea.classList.remove('d-none');
    } catch { alert('Camera access denied.'); }
});

captureBtn.addEventListener('click', () => {
    webcamCanvas.width  = webcamVideo.videoWidth;
    webcamCanvas.height = webcamVideo.videoHeight;
    webcamCanvas.getContext('2d').drawImage(webcamVideo, 0, 0);
    webcamCanvas.toBlob(blob => {
        const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        showPreview(file);
        stopStream();
    }, 'image/jpeg', 0.92);
});

stopWebcamBtn.addEventListener('click', stopStream);
function stopStream() {
    if (stream) stream.getTracks().forEach(t => t.stop());
    webcamArea.classList.add('d-none');
}
</script>
<?php $__env->stopPush(); ?>

<?php echo $__env->make('layouts.app', array_diff_key(get_defined_vars(), ['__data' => 1, '__path' => 1]))->render(); ?><?php /**PATH D:\lumina1\lumina-laravel\resources\views/scanner/upload.blade.php ENDPATH**/ ?>