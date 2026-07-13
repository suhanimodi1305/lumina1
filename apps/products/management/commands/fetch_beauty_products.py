"""
Management command: fetch_beauty_products
Fetches makeup & skincare product data from Open Beauty Facts API (free, no key)
and seeds the database with Indian + popular international brands.

Usage:
    python manage.py fetch_beauty_products              # fetch + seed all
    python manage.py fetch_beauty_products --clear      # clear makeup/skincare first, then seed
    python manage.py fetch_beauty_products --offline    # skip API, use built-in Indian brand data only
    python manage.py fetch_beauty_products --type makeup
    python manage.py fetch_beauty_products --type skincare
"""
import uuid
import time
import logging
import requests
from django.core.management.base import BaseCommand
from apps.products.models import Product

logger = logging.getLogger(__name__)

OBF_API = "https://world.openbeautyfacts.org/cgi/search.pl"
OBF_PRODUCT_API = "https://world.openbeautyfacts.org/api/v0/product/{barcode}.json"

# ─── Category mapping from OBF tags → your Product.category choices ──────────
OBF_CATEGORY_MAP = {
    'foundations': 'foundation', 'foundation': 'foundation',
    'concealers': 'concealer', 'concealer': 'concealer',
    'lipsticks': 'lipstick', 'lip-sticks': 'lipstick',
    'lip-glosses': 'lip_gloss', 'lip-gloss': 'lip_gloss',
    'lip-liners': 'lip_liner',
    'mascaras': 'mascara', 'mascara': 'mascara',
    'eyeliners': 'eyeliner', 'eyeliner': 'eyeliner',
    'eyeshadows': 'eyeshadow', 'eye-shadows': 'eyeshadow',
    'eyeshadow-palettes': 'eyeshadow_palette',
    'blushes': 'blush', 'blush': 'blush',
    'highlighters': 'highlighter',
    'bronzers': 'bronzer',
    'primers': 'primer', 'face-primers': 'primer',
    'setting-powders': 'setting_powder', 'powders': 'powder',
    'serums': 'serum', 'face-serums': 'serum',
    'moisturizers': 'moisturizer', 'moisturisers': 'moisturizer',
    'cleansers': 'cleanser', 'face-wash': 'cleanser',
    'toners': 'toner', 'face-toners': 'toner',
    'sunscreens': 'sunscreen', 'sunscreen': 'sunscreen',
    'face-masks': 'mask', 'sheet-masks': 'mask',
    'eye-creams': 'eye_cream',
    'oils': 'oil', 'face-oils': 'oil',
    'mists': 'mist', 'face-mists': 'mist',
}

# ─── Built-in Indian + popular brand seed data (offline fallback) ─────────────
INDIAN_PRODUCTS = [
    # ── MAKEUP ────────────────────────────────────────────────────────────────
    # Lakme
    {"brand":"Lakme","name":"9 to 5 Weightless Mousse Foundation","category":"foundation","product_range":"makeup","price":699,"description":"Lightweight mousse formula, buildable coverage, suitable for Indian skin tones.","key_ingredients":"SPF 8, Hyaluronic Acid","suitable_for_skin_types":["combination","oily","normal"],"is_featured":True},
    {"brand":"Lakme","name":"Absolute Matte Revolution Lip Color","category":"lipstick","product_range":"makeup","price":500,"description":"Intense matte finish lipstick. Long-wearing formula in 20+ shades.","key_ingredients":"Vitamin E","suitable_for_skin_types":["all"],"is_featured":True},
    {"brand":"Lakme","name":"Insta Eye Liner Black","category":"eyeliner","product_range":"makeup","price":225,"description":"Smudge-proof liquid eyeliner. Intense black pigment, fine tip brush.","key_ingredients":"","suitable_for_skin_types":["all"]},
    {"brand":"Lakme","name":"Absolute Blur Perfect Makeup Primer","category":"primer","product_range":"makeup","price":575,"description":"Blur and prime for long-lasting makeup. Minimises pores.","key_ingredients":"Dimethicone","suitable_for_skin_types":["all"]},
    {"brand":"Lakme","name":"Eyeconic Curling Mascara","category":"mascara","product_range":"makeup","price":350,"description":"Curls and volumizes lashes. Smudge-resistant formula.","key_ingredients":"","suitable_for_skin_types":["all"]},

    # Sugar Cosmetics
    {"brand":"Sugar Cosmetics","name":"Mettle Satin Lipstick","category":"lipstick","product_range":"makeup","price":699,"description":"Satin finish lipstick with rich pigment. Lasts up to 8 hours.","key_ingredients":"Vitamin E, Jojoba Oil","suitable_for_skin_types":["all"],"is_featured":True},
    {"brand":"Sugar Cosmetics","name":"Contour De Force Blush","category":"blush","product_range":"makeup","price":799,"description":"Buildable blush with natural glow finish. Available in 6 shades.","key_ingredients":"","suitable_for_skin_types":["all"]},
    {"brand":"Sugar Cosmetics","name":"First Base Primer + Sunscreen SPF 30","category":"primer","product_range":"makeup","price":699,"description":"Primes skin and protects with SPF 30. Non-greasy, suitable for humid weather.","key_ingredients":"SPF 30, Niacinamide","suitable_for_skin_types":["oily","combination","normal"]},
    {"brand":"Sugar Cosmetics","name":"Kohl of Honour Intense Kajal","category":"eyeliner","product_range":"makeup","price":349,"description":"Ultra-black kajal pencil. Waterproof, long-lasting up to 16 hours.","key_ingredients":"","suitable_for_skin_types":["all"]},
    {"brand":"Sugar Cosmetics","name":"Tip Tac Toe Creamy Matte Lip Liner","category":"lip_liner","product_range":"makeup","price":449,"description":"Creamy matte lip liner. Long-wearing and easy to blend.","key_ingredients":"","suitable_for_skin_types":["all"]},

    # Faces Canada
    {"brand":"Faces Canada","name":"Ultime Pro Matte Mousse Foundation","category":"foundation","product_range":"makeup","price":599,"description":"Matte mousse foundation with full coverage. Transfer-proof formula.","key_ingredients":"SPF 18","suitable_for_skin_types":["oily","combination"],"is_featured":True},
    {"brand":"Faces Canada","name":"Comfy Matte Lipstick","category":"lipstick","product_range":"makeup","price":449,"description":"Comfortable matte lipstick. Moisturising formula with intense pigment.","key_ingredients":"Shea Butter, Vitamin E","suitable_for_skin_types":["all"]},
    {"brand":"Faces Canada","name":"HD Illuminating Highlighter","category":"highlighter","product_range":"makeup","price":549,"description":"Illuminating highlighter for a natural glow. Finely milled shimmer.","key_ingredients":"","suitable_for_skin_types":["all"]},

    # MyGlamm
    {"brand":"MyGlamm","name":"LIT Liquid Matte Lipstick","category":"lipstick","product_range":"makeup","price":595,"description":"Intense liquid matte lipstick. Non-drying, bold colour payoff.","key_ingredients":"Castor Oil","suitable_for_skin_types":["all"]},
    {"brand":"MyGlamm","name":"Pose HD Foundation","category":"foundation","product_range":"makeup","price":999,"description":"Full coverage HD foundation. 18-hour wear, available in 12 shades.","key_ingredients":"SPF 30, Hyaluronic Acid","suitable_for_skin_types":["all"],"is_featured":True},

    # MARS
    {"brand":"MARS","name":"Matte Lipstick","category":"lipstick","product_range":"makeup","price":299,"description":"Affordable matte lipstick, available in 20+ shades. Budget-friendly pick.","key_ingredients":"Vitamin E","suitable_for_skin_types":["all"]},
    {"brand":"MARS","name":"HD Concealer","category":"concealer","product_range":"makeup","price":299,"description":"HD finish concealer that covers blemishes and dark circles.","key_ingredients":"","suitable_for_skin_types":["all"]},
    {"brand":"MARS","name":"Glow Highlighting Powder","category":"highlighter","product_range":"makeup","price":349,"description":"Glow highlighter powder, buildable shimmer for cheeks and brow bone.","key_ingredients":"","suitable_for_skin_types":["all"]},

    # Renee
    {"brand":"Renee","name":"Stay Forever Liquid Lipstick","category":"lipstick","product_range":"makeup","price":699,"description":"Smudge-proof, transfer-resistant matte lipstick. 12-hour wear.","key_ingredients":"Hyaluronic Acid","suitable_for_skin_types":["all"],"is_featured":True},
    {"brand":"Renee","name":"Face Base Compact Powder","category":"powder","product_range":"makeup","price":599,"description":"Compact powder with SPF 15. Reduces shine and sets makeup.","key_ingredients":"SPF 15","suitable_for_skin_types":["oily","combination"]},

    # ── SKINCARE ──────────────────────────────────────────────────────────────
    # Mamaearth
    {"brand":"Mamaearth","name":"Ubtan Face Wash","category":"cleanser","product_range":"korean","price":249,"description":"Turmeric & saffron face wash for bright, even skin tone. Sulphate-free.","key_ingredients":"Turmeric, Saffron, Kojic Acid","suitable_for_skin_types":["all"],"targets":["pigmentation","dullness"],"is_featured":True},
    {"brand":"Mamaearth","name":"Niacinamide Face Serum 10%","category":"serum","product_range":"korean","price":549,"description":"10% Niacinamide + Zinc serum for pores and sebum control.","key_ingredients":"Niacinamide 10%, Zinc PCA","suitable_for_skin_types":["oily","combination"],"targets":["large_pores","oiliness","acne"],"is_featured":True},
    {"brand":"Mamaearth","name":"Vitamin C Daily Glow Sunscreen SPF 50","category":"sunscreen","product_range":"korean","price":349,"description":"SPF 50 PA+++ sunscreen with Vitamin C for bright skin. Non-greasy.","key_ingredients":"Vitamin C, SPF 50","suitable_for_skin_types":["all"],"targets":["pigmentation","dullness"]},
    {"brand":"Mamaearth","name":"Retinol Face Cream","category":"cream","product_range":"korean","price":549,"description":"Anti-aging face cream with Retinol and Bakuchiol. Reduces fine lines.","key_ingredients":"Retinol, Bakuchiol, Peptides","suitable_for_skin_types":["normal","dry","combination"],"targets":["aging","fine_lines"]},
    {"brand":"Mamaearth","name":"Tea Tree Face Wash","category":"cleanser","product_range":"korean","price":249,"description":"Acne-fighting face wash with Tea Tree Oil. Controls oil and breakouts.","key_ingredients":"Tea Tree Oil, Neem","suitable_for_skin_types":["oily","combination"],"targets":["acne","oiliness","blackheads"]},

    # WOW Skin Science
    {"brand":"WOW Skin Science","name":"Apple Cider Vinegar Foaming Face Wash","category":"cleanser","product_range":"korean","price":349,"description":"Balances skin pH, removes impurities. Sulphate and paraben free.","key_ingredients":"Apple Cider Vinegar, Vitamin B5","suitable_for_skin_types":["oily","combination"],"targets":["oiliness","blackheads","acne"],"is_featured":True},
    {"brand":"WOW Skin Science","name":"Vitamin C Serum","category":"serum","product_range":"korean","price":699,"description":"20% Vitamin C + Hyaluronic Acid serum for bright, even skin.","key_ingredients":"Vitamin C 20%, Hyaluronic Acid, Ferulic Acid","suitable_for_skin_types":["all"],"targets":["pigmentation","dullness","aging"],"is_featured":True},
    {"brand":"WOW Skin Science","name":"SPF 50 Sunscreen Gel","category":"sunscreen","product_range":"korean","price":349,"description":"Lightweight gel sunscreen, SPF 50 PA++++. Non-white cast formula.","key_ingredients":"SPF 50, Hyaluronic Acid","suitable_for_skin_types":["oily","combination","normal"],"targets":[]},

    # Plum Goodness
    {"brand":"Plum","name":"Green Tea Pore Cleansing Face Wash","category":"cleanser","product_range":"korean","price":395,"description":"Removes excess oil and unclogs pores. Vegan and cruelty-free.","key_ingredients":"Green Tea, Glycolic Acid","suitable_for_skin_types":["oily","combination"],"targets":["large_pores","blackheads","oiliness"],"is_featured":True},
    {"brand":"Plum","name":"1% Salicylic Acid & Willow Bark Face Toner","category":"toner","product_range":"korean","price":475,"description":"BHA toner for exfoliation and pore-minimising. Alcohol-free.","key_ingredients":"Salicylic Acid 1%, Willow Bark Extract","suitable_for_skin_types":["oily","combination"],"targets":["acne","blackheads","large_pores"]},
    {"brand":"Plum","name":"Bright Years Cell Renewal Serum","category":"serum","product_range":"korean","price":995,"description":"Anti-aging serum with cell renewal actives. Reduces fine lines and brightens.","key_ingredients":"Retinaldehyde, Peptides, Niacinamide","suitable_for_skin_types":["normal","dry","combination"],"targets":["aging","fine_lines","dullness"],"is_featured":True},
    {"brand":"Plum","name":"Hello Aloe Ultra-Light Gel Moisturiser","category":"moisturizer","product_range":"korean","price":425,"description":"Lightweight aloe gel moisturiser. No white cast, suitable for humid weather.","key_ingredients":"Aloe Vera, Glycerin","suitable_for_skin_types":["oily","combination","normal"],"targets":[]},

    # The Derma Co
    {"brand":"The Derma Co","name":"1% Retinol Face Serum","category":"serum","product_range":"korean","price":799,"description":"Clinical-grade 1% Retinol serum for anti-aging. Reduces wrinkles in 4 weeks.","key_ingredients":"Retinol 1%, Peptides, Vitamin E","suitable_for_skin_types":["normal","dry","combination"],"targets":["aging","fine_lines","pigmentation"],"is_featured":True},
    {"brand":"The Derma Co","name":"10% Niacinamide Face Serum","category":"serum","product_range":"korean","price":599,"description":"Reduces pores, controls sebum, evens skin tone. Dermatologist-approved.","key_ingredients":"Niacinamide 10%, Zinc, Alpha Arbutin","suitable_for_skin_types":["oily","combination"],"targets":["large_pores","acne","pigmentation"]},
    {"brand":"The Derma Co","name":"Hyaluronic Acid 2% + Ceramide Face Serum","category":"serum","product_range":"korean","price":599,"description":"Intense hydration serum. 2% Hyaluronic Acid + Ceramide barrier repair.","key_ingredients":"Hyaluronic Acid 2%, Ceramide, Glycerin","suitable_for_skin_types":["dry","normal","combination"],"targets":["dryness","fine_lines"]},
    {"brand":"The Derma Co","name":"Aqua Moisturiser","category":"moisturizer","product_range":"korean","price":399,"description":"Lightweight moisturiser with Hyaluronic Acid and Ceramides. Fragrance-free.","key_ingredients":"Hyaluronic Acid, Ceramide, Glycerin","suitable_for_skin_types":["all"],"targets":["dryness"]},

    # Minimalist
    {"brand":"Minimalist","name":"Niacinamide 10% + Zinc 1%","category":"serum","product_range":"korean","price":599,"description":"Reduces blemishes and regulates sebum. High-strength formula.","key_ingredients":"Niacinamide 10%, Zinc 1%","suitable_for_skin_types":["oily","combination"],"targets":["acne","large_pores","oiliness"],"is_featured":True},
    {"brand":"Minimalist","name":"Alpha Arbutin 2% + HA","category":"serum","product_range":"korean","price":599,"description":"Brightens dark spots and hyperpigmentation. Gentle, no-irritation formula.","key_ingredients":"Alpha Arbutin 2%, Hyaluronic Acid","suitable_for_skin_types":["all"],"targets":["pigmentation","dark_circles"],"is_featured":True},
    {"brand":"Minimalist","name":"AHA 25% + BHA 2% Exfoliating Peeling Solution","category":"exfoliator","product_range":"korean","price":749,"description":"Chemical exfoliant for dullness, uneven texture, and blackheads. Use weekly.","key_ingredients":"Glycolic Acid 25%, Salicylic Acid 2%","suitable_for_skin_types":["oily","combination","normal"],"targets":["blackheads","dullness","large_pores"]},
    {"brand":"Minimalist","name":"SPF 60 PA++++ Sunscreen","category":"sunscreen","product_range":"korean","price":599,"description":"Broad-spectrum SPF 60 sunscreen. No white cast, no fragrance.","key_ingredients":"SPF 60, Hyaluronic Acid","suitable_for_skin_types":["all"],"targets":[]},
    {"brand":"Minimalist","name":"Retinol 0.3% in Squalane","category":"serum","product_range":"korean","price":699,"description":"Entry-level retinol serum in squalane base. Reduces fine lines and acne.","key_ingredients":"Retinol 0.3%, Squalane","suitable_for_skin_types":["normal","dry","combination"],"targets":["aging","fine_lines","acne"]},

    # mCaffeine
    {"brand":"mCaffeine","name":"Coffee Face Wash","category":"cleanser","product_range":"korean","price":299,"description":"Coffee-powered face wash for deep cleansing and de-tanning. Exfoliating beads.","key_ingredients":"Coffee Extract, Hyaluronic Acid","suitable_for_skin_types":["all"],"targets":["dullness","pigmentation","oiliness"]},
    {"brand":"mCaffeine","name":"Coffee Under Eye Cream","category":"eye_cream","product_range":"korean","price":449,"description":"De-puffs and lightens dark circles with caffeine + Vitamin C.","key_ingredients":"Caffeine, Vitamin C, Peptides","suitable_for_skin_types":["all"],"targets":["dark_circles"],"is_featured":True},
    {"brand":"mCaffeine","name":"Coffee Body Scrub","category":"exfoliator","product_range":"korean","price":349,"description":"Exfoliating coffee body scrub for smooth, tan-free skin.","key_ingredients":"Coffee, Coconut Oil, Vitamin E","suitable_for_skin_types":["all"],"targets":["dullness","pigmentation"]},

    # Himalaya
    {"brand":"Himalaya","name":"Purifying Neem Face Wash","category":"cleanser","product_range":"korean","price":175,"description":"Classic neem + turmeric face wash for acne-prone skin. Budget-friendly.","key_ingredients":"Neem, Turmeric","suitable_for_skin_types":["oily","combination"],"targets":["acne","oiliness"]},
    {"brand":"Himalaya","name":"Moisturising Aloe Vera Face Wash","category":"cleanser","product_range":"korean","price":155,"description":"Gentle, hydrating face wash with aloe vera. Suitable for dry and sensitive skin.","key_ingredients":"Aloe Vera, Cucumber","suitable_for_skin_types":["dry","sensitive","normal"],"targets":["dryness"]},

    # Biotique
    {"brand":"Biotique","name":"Bio Honey Gel Moisturiser","category":"moisturizer","product_range":"korean","price":199,"description":"Ayurvedic moisturiser with honey and wheat germ. Light, non-greasy.","key_ingredients":"Honey, Wheat Germ, Almond Oil","suitable_for_skin_types":["normal","combination"],"targets":[]},
    {"brand":"Biotique","name":"Bio Papaya Revitalizing Tan Removal Scrub","category":"exfoliator","product_range":"korean","price":229,"description":"Papaya enzyme scrub for tan removal and skin brightening.","key_ingredients":"Papaya Enzyme, Saffron","suitable_for_skin_types":["all"],"targets":["pigmentation","dullness"]},

    # Re'equil
    {"brand":"Re'equil","name":"Oxybenzone & OMC Free Sunscreen SPF 50","category":"sunscreen","product_range":"korean","price":595,"description":"Chemical sunscreen without oxybenzone. Lightweight, no white cast.","key_ingredients":"Tinosorb M, Tinosorb S, SPF 50","suitable_for_skin_types":["sensitive","dry","normal"],"targets":[],"is_featured":True},
    {"brand":"Re'equil","name":"Ceramide & Hyaluronic Acid Moisturiser","category":"moisturizer","product_range":"korean","price":549,"description":"Barrier-restoring moisturiser. Ideal for sensitive and dry skin.","key_ingredients":"Ceramide, Hyaluronic Acid, Glycerin","suitable_for_skin_types":["dry","sensitive","normal"],"targets":["dryness"]},

    # Kama Ayurveda
    {"brand":"Kama Ayurveda","name":"Rose Jasmine Face Cleanser","category":"cleanser","product_range":"ayurvedic","price":595,"description":"Luxury Ayurvedic cleanser with rose and jasmine. Gentle, fragrant, hydrating.","key_ingredients":"Rose Water, Jasmine, Aloe Vera","suitable_for_skin_types":["dry","sensitive","normal"],"targets":[]},
    {"brand":"Kama Ayurveda","name":"Rejuvenating & Brightening Ayurvedic Night Cream","category":"cream","product_range":"ayurvedic","price":1395,"description":"Night cream with Ayurvedic herbs for bright, youthful skin.","key_ingredients":"Saffron, Licorice, Ashwagandha, Kumkumadi","suitable_for_skin_types":["all"],"targets":["pigmentation","aging","dullness"],"is_featured":True},

    # Forest Essentials
    {"brand":"Forest Essentials","name":"Delicate Facial Cleanser Mashobra Honey & Cream","category":"cleanser","product_range":"ayurvedic","price":895,"description":"Luxury Ayurvedic facial cleanser with honey and cream. Suitable for dry skin.","key_ingredients":"Honey, Cream, Saffron","suitable_for_skin_types":["dry","sensitive"],"targets":["dryness"]},
    {"brand":"Forest Essentials","name":"Tejasvi Elixir Ultra Rich Face Serum","category":"serum","product_range":"ayurvedic","price":2295,"description":"Luxury anti-aging face serum with Saffron and 24K Gold.","key_ingredients":"Saffron, 24K Gold, Kumkumadi","suitable_for_skin_types":["dry","normal"],"targets":["aging","dullness","pigmentation"],"is_featured":True},

    # Soulflower
    {"brand":"Soulflower","name":"Rosemary Scalp & Hair Oil","category":"oil","product_range":"korean","price":395,"description":"Stimulates hair growth and reduces scalp inflammation with Rosemary.","key_ingredients":"Rosemary Essential Oil, Argan Oil","suitable_for_skin_types":["all"],"targets":[]},
    {"brand":"Soulflower","name":"Lavender Face Toner","category":"toner","product_range":"korean","price":299,"description":"Soothing lavender toner for sensitive and acne-prone skin. Alcohol-free.","key_ingredients":"Lavender Water, Witch Hazel","suitable_for_skin_types":["sensitive","oily","combination"],"targets":["redness","acne"]},
]


# ─── Open Beauty Facts search queries for makeup products ────────────────────
OBF_SEARCH_QUERIES = [
    # (search_term, category, product_range, brand_filter)
    ("Maybelline foundation",         "foundation",   "makeup",  "Maybelline"),
    ("Maybelline mascara",            "mascara",      "makeup",  "Maybelline"),
    ("Maybelline lipstick",           "lipstick",     "makeup",  "Maybelline"),
    ("NYX lip gloss",                 "lip_gloss",    "makeup",  "NYX"),
    ("NYX eyeshadow palette",         "eyeshadow_palette","makeup","NYX"),
    ("L'Oreal foundation",            "foundation",   "makeup",  "L'Oreal"),
    ("L'Oreal mascara",               "mascara",      "makeup",  "L'Oreal"),
    ("Revlon lipstick",               "lipstick",     "makeup",  "Revlon"),
    ("Rimmel concealer",              "concealer",    "makeup",  "Rimmel"),
    ("Bourjois blush",                "blush",        "makeup",  "Bourjois"),
]


class Command(BaseCommand):
    help = 'Fetch makeup & skincare products from Open Beauty Facts + seed Indian brands'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true',
            help='Delete existing makeup/skincare products before loading')
        parser.add_argument('--offline', action='store_true',
            help='Skip Open Beauty Facts API, use built-in data only')
        parser.add_argument('--type', choices=['makeup','skincare','all'], default='all',
            help='Which product type to load (default: all)')

    def handle(self, *args, **options):
        clear   = options['clear']
        offline = options['offline']
        ptype   = options['type']

        if clear:
            ranges_to_clear = []
            if ptype in ('makeup','all'):
                ranges_to_clear.append('makeup')
            if ptype in ('skincare','all'):
                ranges_to_clear += ['korean', 'ayurvedic', 'pharmacy']
            deleted, _ = Product.objects.filter(product_range__in=ranges_to_clear).delete()
            self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing products.'))

        created_total = 0

        # ── 1. Seed Indian brand data (always) ────────────────────────────────
        self.stdout.write(self.style.HTTP_INFO('Loading Indian brand products...'))
        for p in INDIAN_PRODUCTS:
            if ptype == 'makeup' and p['product_range'] != 'makeup':
                continue
            if ptype == 'skincare' and p['product_range'] == 'makeup':
                continue
            created = self._upsert_product(p)
            if created:
                created_total += 1

        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {created_total} Indian brand products loaded.'
        ))

        # ── 2. Fetch from Open Beauty Facts (if online) ───────────────────────
        if not offline and ptype in ('makeup', 'all'):
            self.stdout.write(self.style.HTTP_INFO(
                'Fetching from Open Beauty Facts API...'
            ))
            obf_count = self._fetch_from_obf()
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ {obf_count} products fetched from Open Beauty Facts.'
            ))
            created_total += obf_count

        total = Product.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Done! {created_total} new products added. '
            f'Total products in DB: {total}'
        ))

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _upsert_product(self, data: dict) -> bool:
        """Insert product if it doesn't already exist (match on brand + name)."""
        exists = Product.objects.filter(
            brand__iexact=data['brand'],
            name__iexact=data['name']
        ).exists()
        if exists:
            return False

        sku = f"{data['brand'][:8].upper().replace(' ','')}_{uuid.uuid4().hex[:8].upper()}"

        Product.objects.create(
            name=data['name'],
            brand=data['brand'],
            category=data.get('category', 'serum'),
            product_range=data.get('product_range', 'makeup'),
            description=data.get('description', ''),
            key_ingredients=data.get('key_ingredients', ''),
            price=data.get('price'),
            sku=sku,
            image_url=data.get('image_url', ''),
            suitable_for_skin_types=data.get('suitable_for_skin_types', []),
            targets=data.get('targets', []),
            shades_available=data.get('shades_available', []),
            is_featured=data.get('is_featured', False),
        )
        return True

    def _fetch_from_obf(self) -> int:
        """Fetch products from Open Beauty Facts search API."""
        count = 0
        session = requests.Session()
        session.headers.update({'User-Agent': 'Lumina-Beauty-App/1.0'})

        for search_term, category, product_range, brand in OBF_SEARCH_QUERIES:
            try:
                params = {
                    'search_terms': search_term,
                    'search_simple': 1,
                    'action': 'process',
                    'json': 1,
                    'page_size': 10,
                    'fields': (
                        'product_name,brands,categories_tags,ingredients_text,'
                        'image_front_url,quantity,code'
                    ),
                }
                resp = session.get(OBF_API, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()

                products = data.get('products', [])
                self.stdout.write(f'  {search_term}: {len(products)} results')

                for item in products:
                    name = (item.get('product_name') or '').strip()
                    if not name or len(name) < 3:
                        continue

                    item_brand = (item.get('brands') or brand).split(',')[0].strip()
                    if not item_brand:
                        item_brand = brand

                    ingredients = item.get('ingredients_text', '') or ''
                    image_url   = item.get('image_front_url', '') or ''

                    product_data = {
                        'name':          name,
                        'brand':         item_brand,
                        'category':      category,
                        'product_range': product_range,
                        'description':   f'{item_brand} {name}. From Open Beauty Facts.',
                        'key_ingredients': ingredients[:300] if ingredients else '',
                        'image_url':     image_url,
                        'suitable_for_skin_types': ['all'],
                        'targets':       [],
                        'is_featured':   False,
                    }

                    if self._upsert_product(product_data):
                        count += 1

                time.sleep(0.3)  # Be respectful to the free API

            except requests.Timeout:
                self.stdout.write(self.style.WARNING(
                    f'  Timeout fetching "{search_term}" — skipping.'
                ))
            except requests.RequestException as e:
                self.stdout.write(self.style.WARNING(
                    f'  Error fetching "{search_term}": {e} — skipping.'
                ))
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'  Unexpected error on "{search_term}": {e} — skipping.'
                ))

        return count
