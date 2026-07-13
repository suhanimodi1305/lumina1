import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'lumina.settings'
django.setup()
from apps.products.models import Product
p = Product.objects.get(sku='MARS-EYE-001')
print('Name    :', p.name)
print('Category:', p.category)
print('Image   :', p.image_url)
print('Shades  :')
for s in p.shades_available:
    print(f"  {s['shade']:>2}. {s['name']:<22} {s['hex']}  [{s['finish']}]")
