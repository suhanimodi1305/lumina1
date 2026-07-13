@extends('layouts.app')
@section('title', 'Employee Dashboard')

@section('content')
<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold mb-0"><i class="bi bi-briefcase me-2"></i>Employee Portal</h2>
        <a href="{{ route('employee.requirements') }}" class="btn btn-lumina">
            View All Requirements
        </a>
    </div>

    {{-- Stats --}}
    <div class="row g-3 mb-5">
        @foreach([
            ['label'=>'Pending',    'count'=>$stats['pending'],    'icon'=>'clock',         'color'=>'warning'],
            ['label'=>'Processing', 'count'=>$stats['processing'], 'icon'=>'gear',          'color'=>'primary'],
            ['label'=>'Completed',  'count'=>$stats['completed'],  'icon'=>'check2-circle', 'color'=>'success'],
        ] as $stat)
        <div class="col-md-4 fade-in-up">
            <div class="card lumina-card shadow-sm text-center p-4">
                <i class="bi bi-{{ $stat['icon'] }} fs-2 text-{{ $stat['color'] }} mb-2"></i>
                <div class="fw-bold fs-3 count-up" data-count="{{ $stat['count'] }}">{{ $stat['count'] }}</div>
                <div class="text-muted">{{ $stat['label'] }}</div>
            </div>
        </div>
        @endforeach
    </div>

    {{-- Recent requirements --}}
    <h5 class="fw-semibold mb-3">Recent Assignments</h5>
    @if($recent->isEmpty())
    <p class="text-muted">No assignments yet.</p>
    @else
    <div class="card lumina-card shadow-sm">
        <div class="card-body p-0">
            @foreach($recent as $req)
            <div class="d-flex align-items-center gap-3 p-4 border-bottom">
                <div class="flex-grow-1">
                    <div class="fw-semibold">{{ $req->title }}</div>
                    <div class="text-muted small">{{ $req->user?->name }} · {{ $req->created_at->diffForHumans() }}</div>
                </div>
                <span class="badge bg-{{ match($req->status){ 'delivered'=>'success','processing'=>'primary','pending'=>'warning',default=>'secondary' } }}">
                    {{ ucfirst($req->status) }}
                </span>
                <a href="{{ route('employee.requirements') }}#req-{{ $req->id }}" class="btn btn-sm btn-outline-secondary">View</a>
            </div>
            @endforeach
        </div>
    </div>
    @endif
</div>
@endsection
