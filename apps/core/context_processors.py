"""
Global context processors for Lumina.
Injects sidebar-related user data (real scan count, latest real scan)
into every template so the sidebar always shows accurate numbers.
"""
from apps.scanner.models import ScanResult


def user_scan_context(request):
    """
    Makes the following available in every template:
    - user_real_scan_count : count of non-demo scans for the logged-in user
    - user_latest_real_scan: most recent non-demo scan for the logged-in user
    """
    if not request.user.is_authenticated:
        return {
            'user_real_scan_count': 0,
            'user_latest_real_scan': None,
        }

    real_scans = ScanResult.objects.filter(
        user=request.user,
        is_demo=False,
    ).order_by('-created_at')

    return {
        'user_real_scan_count': real_scans.count(),
        'user_latest_real_scan': real_scans.first(),
    }
