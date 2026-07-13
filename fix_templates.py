"""Fix template encoding and add active nav blocks."""
import os

BASE = r'd:\lumina1\templates\employee\products'

# ── product_list.html ─────────────────────────────────────────────────────
path = os.path.join(BASE, 'product_list.html')
content = open(path, 'rb').read().decode('windows-1252')

# Add nav blocks after page_title block
old = "{% block page_title %}Product Management{% endblock %}"
new = ("{% block page_title %}Product Management{% endblock %}\n"
       "{% block nav_products_open %}open{% endblock %}\n"
       "{% block nav_prod_list %}active{% endblock %}")
assert old in content, "product_list: page_title block not found"
content = content.replace(old, new, 1)
open(path, 'w', encoding='utf-8').write(content)
print('✓ product_list.html fixed')

# ── bulk_import.html ──────────────────────────────────────────────────────
path = os.path.join(BASE, 'bulk_import.html')
content = open(path, 'rb').read().decode('windows-1252')

# The title block has a corrupted em-dash; find start of file
# Insert nav blocks after the {% load static %} line
old = "{% load static %}\n{% block title %}"
new = ("{% load static %}\n"
       "{% block nav_products_open %}open{% endblock %}\n"
       "{% block nav_bulk %}active{% endblock %}\n"
       "{% block title %}")
if old not in content:
    # Try with \r\n
    old = "{% load static %}\r\n{% block title %}"
    new = ("{% load static %}\r\n"
           "{% block nav_products_open %}open{% endblock %}\r\n"
           "{% block nav_bulk %}active{% endblock %}\r\n"
           "{% block title %}")
assert old in content, "bulk_import: load static line not found"
content = content.replace(old, new, 1)
open(path, 'w', encoding='utf-8').write(content)
print('✓ bulk_import.html fixed')

# ── product_form.html ─────────────────────────────────────────────────────
path = os.path.join(BASE, 'product_form.html')
if os.path.exists(path):
    try:
        content = open(path, 'rb').read().decode('windows-1252')
    except Exception:
        content = open(path, encoding='utf-8', errors='replace').read()

    if "{% block nav_products_open %}" not in content:
        # find a block to insert after
        for marker in ["{% block page_title %}", "{% block title %}"]:
            if marker in content:
                # find end of that block line
                idx = content.find(marker)
                end = content.find('\n', idx)
                if end == -1: end = content.find('\r', idx)
                insert_at = end + 1
                nav_blocks = ("{% block nav_products_open %}open{% endblock %}\n"
                              "{% block nav_prod_add %}active{% endblock %}\n")
                content = content[:insert_at] + nav_blocks + content[insert_at:]
                break
    open(path, 'w', encoding='utf-8').write(content)
    print('✓ product_form.html fixed')

# ── product_detail.html ───────────────────────────────────────────────────
path = os.path.join(BASE, 'product_detail.html')
if os.path.exists(path):
    try:
        content = open(path, 'rb').read().decode('windows-1252')
    except Exception:
        content = open(path, encoding='utf-8', errors='replace').read()

    if "{% block nav_products_open %}" not in content:
        for marker in ["{% block page_title %}", "{% block title %}"]:
            if marker in content:
                idx = content.find(marker)
                end = content.find('\n', idx)
                if end == -1: end = content.find('\r', idx)
                insert_at = end + 1
                nav_blocks = ("{% block nav_products_open %}open{% endblock %}\n"
                              "{% block nav_prod_list %}active{% endblock %}\n")
                content = content[:insert_at] + nav_blocks + content[insert_at:]
                break
    open(path, 'w', encoding='utf-8').write(content)
    print('✓ product_detail.html fixed')

print('All done.')
