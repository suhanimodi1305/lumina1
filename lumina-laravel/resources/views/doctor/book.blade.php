@extends('layouts.app')
@section('title', 'Book Appointment')

@section('content')
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-lg-7">
            <h2 class="fw-bold mb-4">Book a Consultation</h2>

            <div class="card lumina-card shadow-sm">
                <div class="card-body p-4">
                    <form method="POST" action="{{ route('doctor.store') }}">
                        @csrf

                        {{-- Doctor picker --}}
                        <div class="mb-4">
                            <label class="form-label fw-semibold">Choose a Doctor</label>
                            @foreach($doctors as $doctor)
                            <div class="doctor-option mb-3 border rounded-3 p-3 {{ old('doctor_id') == $doctor->id ? 'border-lumina' : '' }}">
                                <div class="form-check d-flex align-items-center gap-3">
                                    <input class="form-check-input flex-shrink-0" type="radio" name="doctor_id"
                                           id="doc_{{ $doctor->id }}" value="{{ $doctor->id }}"
                                           {{ old('doctor_id') == $doctor->id ? 'checked' : '' }} required>
                                    <label class="form-check-label flex-grow-1 cursor-pointer" for="doc_{{ $doctor->id }}">
                                        <div class="fw-semibold">Dr. {{ $doctor->user?->name }}</div>
                                        <div class="text-muted small">{{ $doctor->specialisation }} · {{ $doctor->experience_years }} yrs</div>
                                        <div class="text-lumina-primary small fw-semibold">₹{{ number_format($doctor->consultation_fee, 0) }}/session</div>
                                    </label>
                                </div>
                            </div>
                            @endforeach
                            @error('doctor_id')<div class="text-danger small">{{ $message }}</div>@enderror
                        </div>

                        {{-- Date & slot --}}
                        <div class="row g-3 mb-4">
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Appointment Date</label>
                                <input type="date" name="appointment_date" class="form-control @error('appointment_date') is-invalid @enderror"
                                       value="{{ old('appointment_date') }}" min="{{ date('Y-m-d', strtotime('+1 day')) }}" required>
                                @error('appointment_date')<div class="invalid-feedback">{{ $message }}</div>@enderror
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-semibold">Time Slot</label>
                                <select name="slot_time" class="form-select @error('slot_time') is-invalid @enderror" required>
                                    <option value="">Select a slot</option>
                                    @foreach(['09:00','10:00','11:00','14:00','15:00','16:00','17:00'] as $slot)
                                    <option value="{{ $slot }}" {{ old('slot_time') === $slot ? 'selected' : '' }}>
                                        {{ date('h:i A', strtotime($slot)) }}
                                    </option>
                                    @endforeach
                                </select>
                                @error('slot_time')<div class="invalid-feedback">{{ $message }}</div>@enderror
                            </div>
                        </div>

                        {{-- Link scan --}}
                        @if($latestScan)
                        <div class="mb-4">
                            <label class="form-label fw-semibold">Attach Scan Results</label>
                            <div class="form-check border rounded-3 p-3">
                                <input class="form-check-input" type="checkbox" name="scan_result_id"
                                       id="attach_scan" value="{{ $latestScan->id }}"
                                       {{ old('scan_result_id') ? 'checked' : '' }}>
                                <label class="form-check-label" for="attach_scan">
                                    Share my latest scan results with the doctor
                                    <span class="text-muted small">({{ ucfirst($latestScan->skin_type) }} skin · {{ $latestScan->created_at->format('d M Y') }})</span>
                                </label>
                            </div>
                        </div>
                        @endif

                        {{-- Notes --}}
                        <div class="mb-4">
                            <label class="form-label fw-semibold">Notes <span class="text-muted small fw-normal">(optional)</span></label>
                            <textarea name="notes" class="form-control" rows="3"
                                      placeholder="Describe your concerns or questions for the doctor...">{{ old('notes') }}</textarea>
                        </div>

                        <button type="submit" class="btn btn-lumina btn-lg w-100">
                            <i class="bi bi-calendar-check me-2"></i>Confirm Booking
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
@endsection
