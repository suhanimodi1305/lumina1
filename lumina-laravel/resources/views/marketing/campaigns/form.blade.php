@extends('layouts.app')
@section('title', isset($campaign) ? 'Edit Campaign' : 'New Campaign')

@section('content')
<div class="container py-5" style="max-width:720px;">
    <div class="d-flex align-items-center gap-2 mb-4">
        <a href="{{ route('marketing.campaigns.index') }}" class="btn btn-sm btn-outline-secondary">
            <i class="bi bi-arrow-left"></i>
        </a>
        <h2 class="fw-bold mb-0">{{ isset($campaign) ? 'Edit Campaign' : 'New Campaign' }}</h2>
    </div>

    @if($errors->any())
    <div class="alert alert-danger">
        <ul class="mb-0 ps-3">@foreach($errors->all() as $e)<li>{{ $e }}</li>@endforeach</ul>
    </div>
    @endif

    <div class="card lumina-card shadow-sm">
        <div class="card-body p-4">
            <form method="POST"
                  action="{{ isset($campaign) ? route('marketing.campaigns.update', $campaign) : route('marketing.campaigns.store') }}">
                @csrf
                @if(isset($campaign)) @method('PUT') @endif

                <div class="mb-3">
                    <label class="form-label fw-semibold">Campaign Name <span class="text-danger">*</span></label>
                    <input type="text" name="name" class="form-control @error('name') is-invalid @enderror"
                           value="{{ old('name', $campaign?->name) }}" placeholder="e.g. Summer Sale 2025" required>
                    @error('name')<div class="invalid-feedback">{{ $message }}</div>@enderror
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Type <span class="text-danger">*</span></label>
                        <select name="type" class="form-select @error('type') is-invalid @enderror" required>
                            @foreach(['email' => 'Email', 'sms' => 'SMS', 'push' => 'Push Notification', 'social' => 'Social Media', 'banner' => 'Banner'] as $val => $label)
                            <option value="{{ $val }}" {{ old('type', $campaign?->type) === $val ? 'selected' : '' }}>{{ $label }}</option>
                            @endforeach
                        </select>
                        @error('type')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Status <span class="text-danger">*</span></label>
                        <select name="status" class="form-select @error('status') is-invalid @enderror" required>
                            @foreach(['draft' => 'Draft', 'active' => 'Active', 'paused' => 'Paused', 'ended' => 'Ended'] as $val => $label)
                            <option value="{{ $val }}" {{ old('status', $campaign?->status ?? 'draft') === $val ? 'selected' : '' }}>{{ $label }}</option>
                            @endforeach
                        </select>
                        @error('status')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    </div>
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Start Date <span class="text-danger">*</span></label>
                        <input type="date" name="start_date" class="form-control @error('start_date') is-invalid @enderror"
                               value="{{ old('start_date', $campaign?->start_date?->format('Y-m-d')) }}" required>
                        @error('start_date')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">End Date</label>
                        <input type="date" name="end_date" class="form-control @error('end_date') is-invalid @enderror"
                               value="{{ old('end_date', $campaign?->end_date?->format('Y-m-d')) }}">
                        @error('end_date')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    </div>
                </div>

                <div class="mb-4">
                    <label class="form-label fw-semibold">Content / Notes</label>
                    <textarea name="content" rows="5" class="form-control @error('content') is-invalid @enderror"
                              placeholder="Campaign copy, targeting notes, etc.">{{ old('content', $campaign?->content) }}</textarea>
                    @error('content')<div class="invalid-feedback">{{ $message }}</div>@enderror
                </div>

                <div class="d-flex gap-2 justify-content-end">
                    <a href="{{ route('marketing.campaigns.index') }}" class="btn btn-outline-secondary">Cancel</a>
                    <button type="submit" class="btn btn-lumina">
                        <i class="bi bi-check-lg me-1"></i>{{ isset($campaign) ? 'Update Campaign' : 'Create Campaign' }}
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
@endsection
