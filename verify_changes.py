with open('templates/employee/crm_base.html', encoding='utf-8') as f:
    c = f.read()

with open('templates/employee/products/bulk_import.html', encoding='utf-8') as f:
    b = f.read()

results = [
    ('crm_base: --surface alias', '--surface:         var(--emp-surface)' in c),
    ('crm_base: --border alias', '--border:          var(--emp-border)' in c),
    ('crm_base: --teal alias', '--teal:            var(--emp-accent)' in c),
    ('crm_base: dark alert-success', 'data-theme="dark"] .emp-alert-success' in c),
    ('crm_base: dark alert-error', 'data-theme="dark"] .emp-alert-error' in c),
    ('crm_base: extra_css after vars', c.index('block extra_css') > c.index('.emp-shell')),
    ('bulk_import: emp-surface used', 'var(--emp-surface)' in b),
    ('bulk_import: emp-accent used', 'var(--emp-accent)' in b),
    ('bulk_import: dark result-created', '.result-created { background: rgba' in b),
    ('bulk_import: emp-alert class', 'emp-alert emp-alert-' in b),
    ('bulk_import: no hardcoded msg inline', 'background:#f0fdf4;color:#166534' not in b),
]

all_ok = True
for label, ok in results:
    status = 'PASS' if ok else 'FAIL'
    if not ok:
        all_ok = False
    print(f'  [{status}] {label}')

print()
print('All checks passed!' if all_ok else 'Some checks FAILED - review above.')
