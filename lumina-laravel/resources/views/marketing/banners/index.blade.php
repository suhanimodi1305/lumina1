@extends('layouts.app')
@section('title', 'Banners')

@section('content')
<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold mb-0"><i class="bi bi-image me-2"></i>Banners</h2>
        <a href="{{ route('marketing.banners.create') }}" class="btn btn-lumina">
            <i class="bi bi-plus-lg me-2"></i>New Banner
        </a>
    </div>

    @if(session('success'))
    <div class="alert alert-success alert-dismissible fade show" role="alert">
        {{ session('success') }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    @endif

    <div class="card lumina-card shadow-sm">
        <div class="card-body p-0">
            @if($banners->isEmpty())
            <div class="text-center py-5 text-muted">
                <i class="bi bi-image fs-1 d-block mb-2"></i>
                <p>No banners yet. <a href="{{ route('marketing.banners.create') }}">Add the first one.</a></p>
            </div>
            @else
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="bg-light small text-muted">
                        <tr>
                            <th style="width:60px;">#</th>
                            <th>Preview</th>
                            <th>Title</th>
                            <th>Placement</th>
                            <th class="text-center">Order</th>
                            <th class="text-center">Status</th>
                            <th class="text-end">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        @foreach($banners as $banner)
                        <tr>
                            <td class="text-muted small">{{ $banner->id }}</td>
                            <td>
                                @if($banner->image_url)
                                <img src="{{ $banner->image_url }}" alt="{{ $banner->title }}"
                                     style="width:72px;height:44px;object-fit:cover;border-radius:6px;border:1px solid #eee;">
                                @else
                                <div style="width:72px;height:44px;background:#f0f2f5;border-radius:6px;display:flex;align-items:center;justify-content:center;">
                                    <i class="bi bi-image text-muted"></i>
                                </div>
                                @endif
                            </td>
                            <td class="fw-semibold">
                                {{ $banner->title }}
                                @if($banner->link_url)
                                <a href="{{ $banner->link_url }}" target="_blank" class="ms-1 text-muted small">
                                    <i class="bi bi-box-arrow-up-right"></i>
                                </a>
                                @endif
                            </td>
                            <td><span class="badge bg-light text-dark">{{ $banner->placement }}</span></td>
                            <td class="text-center small">{{ $banner->sort_order }}</td>
                            <td class="text-center">
                                @if($banner->is_active)
                                <span class="badge bg-success">Active</span>
                                @else
                                <span class="badge bg-secondary">Inactive</span>
                                @endif
                            </td>
                            <td class="text-end">
                                <a href="{{ route('marketing.banners.edit', $banner) }}"
                                   class="btn btn-sm btn-outline-secondary">Edit</a>
                                <form method="POST" action="{{ route('marketing.banners.destroy', $banner) }}"
                                      class="d-inline" onsubmit="return confirm('Delete this banner?')">
                                    @csrf @method('DELETE')
                                    <button class="btn btn-sm btn-outline-danger">Delete</button>
                                </form>
                            </td>
                        </tr>
                        @endforeach
                    </tbody>
                </table>
            </div>
            @endif
        </div>
    </div>
    <div class="mt-4">{{ $banners->links() }}</div>
</div>
@endsection
