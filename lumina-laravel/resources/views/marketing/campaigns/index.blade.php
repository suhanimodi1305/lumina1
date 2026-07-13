@extends('layouts.app')
@section('title', 'Campaigns')

@section('content')
<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold mb-0">Campaigns</h2>
        <a href="{{ route('marketing.campaigns.create') }}" class="btn btn-lumina">
            <i class="bi bi-plus-lg me-2"></i>New Campaign
        </a>
    </div>

    @if(session('success'))<div class="alert alert-success">{{ session('success') }}</div>@endif

    <div class="card lumina-card shadow-sm">
        <div class="card-body p-0">
            @if($campaigns->isEmpty())
            <div class="text-center py-5 text-muted"><p>No campaigns yet.</p></div>
            @else
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="bg-light small text-muted"><tr><th>Name</th><th>Type</th><th>Status</th><th>Start</th><th>End</th><th class="text-end">Actions</th></tr></thead>
                    <tbody>
                        @foreach($campaigns as $c)
                        <tr>
                            <td class="fw-semibold">{{ $c->name }}</td>
                            <td><span class="badge bg-light text-dark text-capitalize">{{ $c->type }}</span></td>
                            <td><span class="badge bg-{{ $c->status==='active'?'success':($c->status==='draft'?'secondary':'warning') }} text-capitalize">{{ $c->status }}</span></td>
                            <td class="small">{{ $c->start_date?->format('d M Y') }}</td>
                            <td class="small">{{ $c->end_date?->format('d M Y') ?? '—' }}</td>
                            <td class="text-end">
                                <a href="{{ route('marketing.campaigns.edit', $c) }}" class="btn btn-sm btn-outline-secondary">Edit</a>
                                <form method="POST" action="{{ route('marketing.campaigns.destroy', $c) }}" class="d-inline" onsubmit="return confirm('Delete?')">
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
    <div class="mt-4">{{ $campaigns->links() }}</div>
</div>
@endsection
