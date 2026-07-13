@extends('layouts.app')
@section('title', 'Customer Requirements')

@section('content')
<div class="container py-5">
    <h2 class="fw-bold mb-4">Assigned Requirements</h2>

    @if(session('success'))
    <div class="alert alert-success">{{ session('success') }}</div>
    @endif

    @if($requirements->isEmpty())
    <div class="text-center py-5 text-muted">
        <i class="bi bi-inbox fs-1 mb-3 d-block"></i>
        <p>No requirements assigned to you yet.</p>
    </div>
    @else
    <div class="d-flex flex-column gap-4">
        @foreach($requirements as $req)
        <div class="card lumina-card shadow-sm" id="req-{{ $req->id }}">
            <div class="card-body p-4">
                <div class="row g-3">
                    <div class="col-lg-8">
                        <div class="d-flex align-items-start gap-2 mb-2">
                            <h5 class="fw-semibold mb-0">{{ $req->title }}</h5>
                            <span class="badge bg-{{ match($req->status){ 'delivered'=>'success','processing'=>'primary','dispatched'=>'info','pending'=>'warning',default=>'secondary' } }}">
                                {{ ucfirst($req->status) }}
                            </span>
                        </div>
                        <p class="text-muted small mb-2">
                            <i class="bi bi-person me-1"></i>{{ $req->user?->name }}
                            · <i class="bi bi-clock me-1"></i>{{ $req->created_at->format('d M Y') }}
                        </p>
                        <p class="mb-2">{{ $req->description }}</p>
                        @if($req->budget_range)
                        <p class="text-muted small"><i class="bi bi-currency-rupee me-1"></i>Budget: {{ $req->budget_range }}</p>
                        @endif
                        @if($req->employee_notes)
                        <div class="alert alert-info py-2 small mb-0">
                            <strong>Your note:</strong> {{ $req->employee_notes }}
                        </div>
                        @endif
                    </div>
                    <div class="col-lg-4">
                        <form method="POST" action="{{ route('employee.requirements.status', $req) }}">
                            @csrf
                            <div class="mb-2">
                                <label class="form-label small fw-semibold">Update Status</label>
                                <select name="status" class="form-select form-select-sm">
                                    @foreach(['pending','accepted','processing','dispatched','delivered','rejected'] as $s)
                                    <option value="{{ $s }}" {{ $req->status===$s?'selected':'' }}>{{ ucfirst($s) }}</option>
                                    @endforeach
                                </select>
                            </div>
                            <div class="mb-3">
                                <textarea name="employee_notes" class="form-control form-control-sm" rows="2"
                                          placeholder="Add a note...">{{ old('employee_notes', $req->employee_notes) }}</textarea>
                            </div>
                            <button type="submit" class="btn btn-sm btn-lumina w-100">Update</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        @endforeach
    </div>
    <div class="mt-4">{{ $requirements->links() }}</div>
    @endif
</div>
@endsection
