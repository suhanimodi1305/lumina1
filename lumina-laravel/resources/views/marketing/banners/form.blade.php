@extends('layouts.app')
@section('title', isset($banner) ? 'Edit Banner' : 'New Banner')

@section('content')
<div class="container py-5" style="max-width:680px;">
    <div class="d-flex align-items-center gap-2 mb-4">
        <a href="{{ route('marketing.banners.index') }}" class="btn btn-sm btn-outline-secondary">
            <i class="bi bi-arrow-left"></i>
        </a>
        <h2 class="fw-bold mb-0">{{ isset($banner) ? 'Edit Banner' : 'New Banner' }}</h2>
    </div>

    @if($errors->any())
    <div class="alert alert-danger">
        <ul class="mb-0 ps-3">@foreach($errors->all() as $e)<li>{{ $e }}</li>@endforeach</ul>
    </div>
    @endif

    <div class="card lumina-card shadow-sm">
        <div class="card-body p-4">
            <form method="POST"
                  action="{{ isset($banner) ? route('marketing.banners.update', $banner) : route('marketing.banners.store') }}">
                @csrf
                @if(isset($banner)) @method('PUT') @endif

                <div class="mb-3">
                    <label class="form-label fw-semibold">Title <span class="text-danger">*</span></label>
                    <input type="text" name="title" class="form-control @error('title') is-invalid @enderror"
                           value="{{ old('title', $banner?->title) }}" placeholder="e.g. Summer Sale Hero" required>
                    @error('title')<div class="invalid-feedback">{{ $message }}</div>@enderror
                </div>

                <div class="mb-3">
                    <label class="form-label fw-semibold">Placement <span class="text-danger">*</span></label>
                    <input type="text" name="placement" class="form-control @error('placement') is-invalid @enderror"
                           value="{{ old('placement', $banner?->placement) }}"
                           placeholder="e.g. home_hero, sidebar, checkout_top" required>
                    @error('placement')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    <div class="form-text text-muted">Identifier used in templates to select this banner slot.</div>
                </div>

                <div class="mb-3">
                    <label class="form-label fw-semibold">Image URL</label>
                    <input type="url" name="image_url" class="form-control @error('image_url') is-invalid @enderror"
                           value="{{ old('image_url', $banner?->image_url) }}" placeholder="https://...">
                    @error('image_url')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    @if(isset($banner) && $banner->image_url)
                    <div class="mt-2">
                        <img src="{{ $banner->image_url }}" alt="Preview"
                             style="max-height:100px;border-radius:6px;border:1px solid #eee;">
                    </div>
                    @endif
                </div>

                <div class="mb-3">
                    <label class="form-label fw-semibold">Link URL</label>
                    <input type="url" name="link_url" class="form-control @error('link_url') is-invalid @enderror"
                           value="{{ old('link_url', $banner?->link_url) }}" placeholder="https://...">
                    @error('link_url')<div class="invalid-feedback">{{ $message }}</div>@enderror
                </div>

                <div class="row g-3 mb-4">
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Sort Order</label>
                        <input type="number" name="sort_order" class="form-control @error('sort_order') is-invalid @enderror"
                               value="{{ old('sort_order', $banner?->sort_order ?? 0) }}" min="0">
                        @error('sort_order')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        <div class="form-text text-muted">Lower numbers appear first.</div>
                    </div>
                    <div class="col-md-6 d-flex align-items-end">
                        <div class="form-check form-switch mb-1">
                            <input class="form-check-input" type="checkbox" name="is_active" value="1" id="isActive"
                                   {{ old('is_active', $banner?->is_active ?? true) ? 'checked' : '' }}>
                            <label class="form-check-label fw-semibold" for="isActive">Active</label>
                        </div>
                    </div>
                </div>

                <div class="d-flex gap-2 justify-content-end">
                    <a href="{{ route('marketing.banners.index') }}" class="btn btn-outline-secondary">Cancel</a>
                    <button type="submit" class="btn btn-lumina">
                        <i class="bi bi-check-lg me-1"></i>{{ isset($banner) ? 'Update Banner' : 'Create Banner' }}
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
@endsection
