from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from apps.scanner.models import ScanResult


@login_required
def dashboard_view(request):
    all_scans = ScanResult.objects.filter(
        user=request.user, is_demo=False
    ).prefetch_related('detected_concerns').order_by('-created_at')
    total_scans = all_scans.count()
    latest_scan = all_scans.first()
    progress = None
    if all_scans.count() >= 2:
        scans_list = list(all_scans[:2])
        progress = scans_list[0].harmony_score - scans_list[1].harmony_score
    avg_harmony = 0
    if total_scans:
        avg_harmony = int(sum(s.harmony_score for s in all_scans) / total_scans)
    return render(request, 'dashboard/dashboard.html', {
        'all_scans':   all_scans,
        'total_scans': total_scans,
        'latest_scan': latest_scan,
        'progress':    progress,
        'avg_harmony': avg_harmony,
    })


@login_required
@require_POST
def delete_scan(request, scan_id):
    scan = get_object_or_404(ScanResult, id=scan_id, user=request.user)
    scan.delete()
    messages.success(request, 'Scan deleted.')
    return redirect('dashboard:dashboard')
