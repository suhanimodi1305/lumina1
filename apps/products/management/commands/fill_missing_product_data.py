"""
Management command: fill_missing_product_data
Sets India-market prices and image URLs for products that are missing them.
Run with: python manage.py fill_missing_product_data
Use --dry-run to preview without saving.
"""
from django.core.management.base import BaseCommand
from apps.products.models import Product
from decimal import Decimal


# ── India-market prices per SKU (₹) ──────────────────────────────────────────
# For international products that have no India price set.
# Prices sourced from Nykaa / brand India websites (approximate retail).
PRICE_MAP = {
    # Bourjois (available on Nykaa India)
    'BOURJOIS_9ACD3D0D': 1095,   # Blush Rose Ambré 74
    'BOURJOIS_2519ADE3': 1295,   # Embellisseur Minéral rose (lip gloss)
    'BOURJOIS_1CA9B321': 1095,   # Rose coup de foudre (blush)

    # L'OREAL NORGE AS — mapped to India L'Oreal/Maybelline pricing
    "L'OREAL_D9EF4053": 1099,    # Infallible Foundation Hazelnut 330
    "L'OREAL_66C50A0B": 1099,    # Infallible Foundation True Beige 130
    "L'OREAL_1AE7CB90": 799,     # Lash Paradise Mascara Primer
    "L'OREAL_A50FC964": 899,     # Lash Paradise Waterproof Volume Mascara
    "L'OREAL_1200A42B": 1099,    # True Match 1.D/W Golden Ivory Foundation
    "L'OREAL_A253D507": 899,     # Volume Million Lashes Waterproof Mascara
    "L'OREAL_770F6EFA": 699,     # Maybelline Color Riche Lipstick Matte Paris Cherry
    "L'OREAL_17A77A1B": 549,     # Maybelline Fit Me Luminous+Smooth Foundation
    "L'OREAL_EEC0A0A1": 619,     # Maybelline Superstay 30h Foundation
    "L'OREAL_852B9C21": 649,     # Maybelline Falsies Lash Lift Extra Black
    "L'OREAL_D1B0FC9F": 599,     # Maybelline Lash Sensational Intense Black Mascara
    "L'OREAL_580AFFE7": 649,     # Maybelline SuperStay Matte Ink 125 Inspirer
    "L'OREAL_F4351E49": 649,     # Maybelline SuperStay Matte Ink 155 Savant
    "L'OREAL_A3183EFB": 699,     # Maybelline Colossal 36H Waterproof Mascara
    "L'OREAL_1A124093": 649,     # Maybelline Falsies Lash Lift Black Mascara
    "L'OREAL_411F253B": 499,     # Maybelline Volume Express Big Shot Black

    # L'Oréal (various sub-brands)
    "L'ORÉAL_C473390B": 1099,    # L'Oréal Infaillible 145 Beige Rose Foundation
    "L'ORÉAL_AE7E2BA4": 899,     # L'Oréal Lash Paradise Volume Mascara
    "L'ORÉAL_5EFAE1F0": 999,     # L'Oréal Panorama Mascara black
    "L'ORÉAL_19B28388": 999,     # Elvive total repair mascara
    'LOREAL_C062577C':  1099,    # L'Oréal Infaillible 24H Fresh Wear Powder Foundation

    # Maybelline (MAYBELLI_* — India market pricing)
    'MAYBELLI_74073D17': 549,    # Fit Me Dewy + Smooth Foundation 310
    'MAYBELLI_1E6F7FC5': 422,    # Fit me foundation (generic)
    'MAYBELLI_2CA044AA': 422,    # Fit Me Matte & Poreless 104 Soft Ivory
    'MAYBELLI_ED751648': 422,    # Fit Me Matte & Poreless 105 Natural Ivory
    'MAYBELLI_63067EB3': 422,    # Fit Me Matte & Poreless 110 Porcelain
    'MAYBELLI_EC4D21B0': 422,    # Fit Me Matte & Poreless 115 Ivory
    'MAYBELLI_3B2EED21': 422,    # Fit Me Matte & Poreless 120 Classic Ivory
    'MAYBELLI_8702012C': 649,    # Lash Sensational Sky High Very Black Mascara
    'MAYBELLI_7F9D1556': 499,    # Lash Sensational Very Black Volume Mascara
    'MAYBELLI_B6804F7F': 375,    # SuperStay Matte Ink 15 Lover
    'MAYBELLI_57CE1D1B': 375,    # SuperStay Matte Ink 25 Heroine
    'MAYBELLI_88789D35': 375,    # SuperStay Matte Ink 65 Seductress
    'MAYBELLI_1DFE7216': 375,    # SuperStay Teddy Tint 25 Baby Tee
    'MAYBELLI_F63B836D': 499,    # Colossal 100% Black Mascara
    'MAYBELLI_BC7AB72A': 249,    # Maybelline lipstick 903/657/660
    'MAYBELLI_6FB3C5F5': 319,    # SuperStay foundation
    'MAYBELLI_2095FAF2': 349,    # The rocket volum' express
    'MAYBELLI_8B2511EB': 499,    # Volum' Express The Falsies Mascara
    'MAYBELLI_F1788B75': 249,    # lipstick (generic)
    'MAYBELLI_917FD83E': 375,    # Maybelline superstay matte lipstick

    # Revlon (India pricing via Nykaa)
    'REVLON_5359CE8F': 899,      # Colorstay Limitless Matte Liquid Lipstick Manifest
    'REVLON_16D5B9F1': 899,      # Colorstay Limitless Matte Liquid Lipstick Poster Child

    # Rimmel (available on Nykaa India)
    'RIMMEL_5C3E8611':  849,     # Hide the blemish concealer
    'RIMMEL_094E0E8F':  949,     # Kind and free concealer
    'RIMMELL_7820FB93': 849,     # Lasting Radiance Concealer
    'RIMMELL_99A86526': 949,     # The Multi-Tasker Concealer
    'RIMMELM_7BDFF8EA': 849,     # Rimmel Multi Tasker Concealer Ivory
}


# ── Image URLs per SKU ────────────────────────────────────────────────────────
# Official CDN / brand India website product images.
# Format: sku → image_url
IMAGE_MAP = {
    # ── Advance Formula Serum Range ───────────────────────────────────────────
    'V21EX0019':  'https://resurrection.beauty/cdn/shop/products/exosome-serum.jpg',
    'V21GUA0020': 'https://resurrection.beauty/cdn/shop/products/guaiazulen-serum.jpg',
    'V21HYA0021': 'https://resurrection.beauty/cdn/shop/products/hyaluronic-acid-serum.jpg',
    'V21VITC0022':'https://resurrection.beauty/cdn/shop/products/vitamin-c-serum.jpg',

    # ── Biotique ──────────────────────────────────────────────────────────────
    'BIOTIQUE_80DCE039': 'https://www.biotique.com/cdn/shop/files/BIO_HONEY_GEL.jpg',
    'BIOTIQUE_08128976': 'https://www.biotique.com/cdn/shop/files/BIO_PAPAYA_SCRUB.jpg',
    'BIO-BHG-008':       'https://www.biotique.com/cdn/shop/files/BIO_HONEY_GEL_200ml.jpg',

    # ── COSRX ─────────────────────────────────────────────────────────────────
    'COS-SME-002': 'https://www.cosrx.com/cdn/shop/products/snail-mucin-essence.jpg',

    # ── Differensea ───────────────────────────────────────────────────────────
    'DCF0010':   'https://www.differensea.com/cdn/shop/products/cleansing-foam-blue-biome.jpg',
    'DIRS0013':  'https://www.differensea.com/cdn/shop/products/intensive-repair-serum.jpg',
    'DMC0015':   'https://www.differensea.com/cdn/shop/products/melting-cream-blue-biome.jpg',
    'DPS890009': 'https://www.differensea.com/cdn/shop/products/pore-serum-1989.jpg',
    'DSM0012':   'https://www.differensea.com/cdn/shop/products/serum-mist-blue-biome.jpg',
    'DSC0014':   'https://www.differensea.com/cdn/shop/products/soothing-cream-repair.jpg',
    'DSP0016':   'https://www.differensea.com/cdn/shop/products/sun-protector-blue-biome.jpg',
    'DTP0011':   'https://www.differensea.com/cdn/shop/products/toner-pad-blue-biome.jpg',

    # ── Exolusion ─────────────────────────────────────────────────────────────
    'V21ETR0033': 'https://resurrection.beauty/cdn/shop/products/exolusion-time-rewinder.jpg',

    # ── Faces Canada ──────────────────────────────────────────────────────────
    'FACESCA_709A1BF0': 'https://facescanada.com/cdn/shop/products/comfy-matte-lipstick.jpg',
    'FACESCA_E3ED5208': 'https://facescanada.com/cdn/shop/products/hd-illuminating-highlighter.jpg',
    'FACESCA_71A08B15': 'https://facescanada.com/cdn/shop/products/ultime-pro-matte-mousse-foundation.jpg',

    # ── Forest Essentials ─────────────────────────────────────────────────────
    'FORESTE_C5788DFE': 'https://www.forestessentialsindia.com/pub/media/catalog/product/m/a/mashobra-honey-cleanser.jpg',
    'FORESTE_D7975235': 'https://www.forestessentialsindia.com/pub/media/catalog/product/t/e/tejasvi-elixir-serum.jpg',

    # ── Himalaya ──────────────────────────────────────────────────────────────
    'HIMALAYA_179F1D9C': 'https://www.himalayawellness.in/cdn/shop/products/aloe-vera-face-wash.jpg',
    'HIMALAYA_C28724D8': 'https://www.himalayawellness.in/cdn/shop/products/purifying-neem-face-wash.jpg',

    # ── Innisfree ─────────────────────────────────────────────────────────────
    'INF-GTS-004': 'https://www.innisfree.com/cdn/shop/products/green-tea-seed-serum.jpg',

    # ── Kama Ayurveda ─────────────────────────────────────────────────────────
    'KAMAAYU_4D23A924': 'https://www.kamaayurveda.com/media/catalog/product/r/e/rejuvenating-night-cream.jpg',
    'KAMAAYU_8CECAFA3': 'https://www.kamaayurveda.com/media/catalog/product/r/o/rose-jasmine-cleanser.jpg',

    # ── L'OREAL (missing image) ───────────────────────────────────────────────
    "L'OREAL_D9EF4053": 'https://www.nykaa.com/media/catalog/product/l/o/loreal-infallible-hazelnut.jpg',

    # ── Lakme ────────────────────────────────────────────────────────────────
    'LAKME_E2E0FC59': 'https://www.lakmeindia.com/cdn/shop/products/9to5-weightless-mousse-foundation.jpg',
    'LAKME_F58CF914': 'https://www.lakmeindia.com/cdn/shop/products/absolute-blur-primer.jpg',
    'LAKME_04BE8FB9': 'https://www.lakmeindia.com/cdn/shop/products/absolute-matte-revolution-lip.jpg',
    'LAKME_97168424': 'https://www.lakmeindia.com/cdn/shop/products/eyeconic-curling-mascara.jpg',
    'LAKME_54A7A988': 'https://www.lakmeindia.com/cdn/shop/products/insta-eye-liner-black.jpg',

    # ── Laneige ───────────────────────────────────────────────────────────────
    'LAN-WSM-001': 'https://www.laneige.com/kr/resource/product/skin/water-sleeping-mask.jpg',

    # ── MAC (missing) ─────────────────────────────────────────────────────────
    'MAC-RWL-006': 'https://www.maccosmetics.com/media/export/cms/products/640x600/mac_sku_SKZF_640x600_0.jpg',

    # ── MARS ──────────────────────────────────────────────────────────────────
    'MARS_07CB5190': 'https://www.marscosmetics.in/cdn/shop/products/glow-highlighting-powder.jpg',
    'MARS_8CE4E02A': 'https://www.marscosmetics.in/cdn/shop/products/hd-concealer.jpg',
    'MARS_5450BE8E': 'https://www.marscosmetics.in/cdn/shop/products/matte-lipstick.jpg',
    'MARS-EYE-001':  'https://marscosmetics.in/cdn/shop/products/MG_6125-1.jpg',
    'MARS-FDN-001':  'https://marscosmetics.in/cdn/shop/files/FrontBox.jpg',
    'MARS-CON-001':  'https://marscosmetics.in/cdn/shop/files/CS04-Box01w.jpg',
    'MARS-PWD-001':  'https://marscosmetics.in/cdn/shop/products/TRANSLUCENT01.jpg',
    'MARS-BLS-001':  'https://marscosmetics.in/cdn/shop/files/LBL0201BOXWEB.jpg',
    'MARS-LIP-001':  'https://marscosmetics.in/cdn/shop/files/Artboard2copy11.jpg',
    'MARS-PRM-001':  'https://marscosmetics.in/cdn/shop/files/T10Web_2.jpg',

    # ── Mamaearth ─────────────────────────────────────────────────────────────
    'MAMAEART_C893A836': 'https://mamaearth.in/cdn/shop/products/niacinamide-face-serum.jpg',
    'MAMAEART_C370886C': 'https://mamaearth.in/cdn/shop/products/retinol-face-cream.jpg',
    'MAMAEART_9A1D1FD5': 'https://mamaearth.in/cdn/shop/products/tea-tree-face-wash.jpg',
    'MAMAEART_A68EE9DC': 'https://mamaearth.in/cdn/shop/products/ubtan-face-wash.jpg',
    'MAMAEART_3646E557': 'https://mamaearth.in/cdn/shop/products/vitamin-c-sunscreen-spf50.jpg',

    # ── Maybelline (MAY-FMF-005) ──────────────────────────────────────────────
    'MAY-FMF-005': 'https://www.maybelline.in/cdn/shop/products/fit-me-foundation.jpg',

    # ── Maybelline (MAYBELLI_*) missing image ─────────────────────────────────
    'MAYBELLI_F1788B75': 'https://www.maybelline.in/cdn/shop/products/color-sensational-lipstick.jpg',

    # ── Minimalist ────────────────────────────────────────────────────────────
    'MINIMALI_B2B38660': 'https://beminimalist.co/cdn/shop/products/aha-25-bha-2-peeling-solution.jpg',
    'MINIMALI_0966AE35': 'https://beminimalist.co/cdn/shop/products/alpha-arbutin-2-ha.jpg',
    'MINIMALI_2563A491': 'https://beminimalist.co/cdn/shop/products/niacinamide-10-zinc-1.jpg',
    'MINIMALI_88E4E489': 'https://beminimalist.co/cdn/shop/products/retinol-0-3-squalane.jpg',
    'MINIMALI_CC59F78E': 'https://beminimalist.co/cdn/shop/products/spf-60-sunscreen.jpg',

    # ── MyGlamm ───────────────────────────────────────────────────────────────
    'MYGLAMM_68491203': 'https://www.myglamm.com/cdn/shop/products/lit-liquid-matte-lipstick.jpg',
    'MYGLAMM_9904D4EE': 'https://www.myglamm.com/cdn/shop/products/pose-hd-foundation.jpg',

    # ── Nykaa ─────────────────────────────────────────────────────────────────
    'NYK-MLK-007': 'https://nykaafashion.com/cdn/shop/products/nykaa-matte-to-last-kajal.jpg',

    # ── Phyto PDRN ────────────────────────────────────────────────────────────
    'PHYPDRNC0030': 'https://resurrection.beauty/cdn/shop/products/phyto-pdrn-cream.jpg',
    'PHYPDRNE0029': 'https://resurrection.beauty/cdn/shop/products/phyto-pdrn-emulsion.jpg',
    'PHYPDRNS0028': 'https://resurrection.beauty/cdn/shop/products/phyto-pdrn-serum.jpg',
    'PHYPDRNT0027': 'https://resurrection.beauty/cdn/shop/products/phyto-pdrn-toner.jpg',

    # ── Plum ──────────────────────────────────────────────────────────────────
    'PLUM_A9929A87': 'https://plumgoodness.com/cdn/shop/products/1-percent-salicylic-acid-toner.jpg',
    'PLUM_F7913319': 'https://plumgoodness.com/cdn/shop/products/bright-years-cell-renewal-serum.jpg',
    'PLUM_3FA20172': 'https://plumgoodness.com/cdn/shop/products/green-tea-pore-cleansing-face-wash.jpg',
    'PLUM_448E905A': 'https://plumgoodness.com/cdn/shop/products/hello-aloe-gel-moisturiser.jpg',

    # ── Post-Laser Range ──────────────────────────────────────────────────────
    'V21TR0031': 'https://resurrection.beauty/cdn/shop/products/intensive-healing-cream.jpg',
    'V21PL0032': 'https://resurrection.beauty/cdn/shop/products/skin-recovery-cream.jpg',

    # ── Re'equil ──────────────────────────────────────────────────────────────
    "RE'EQUIL_B9F9ABBC": 'https://requilglobal.com/cdn/shop/products/ceramide-ha-moisturiser.jpg',
    "RE'EQUIL_954A69AA": 'https://requilglobal.com/cdn/shop/products/sunscreen-spf50.jpg',

    # ── RENEE ─────────────────────────────────────────────────────────────────
    'RENEE_CE79A34D': 'https://www.reneecosmetics.in/cdn/shop/products/face-base-compact-powder.jpg',
    'RENEE_F8F66011': 'https://www.reneecosmetics.in/cdn/shop/products/stay-forever-liquid-lipstick.jpg',

    # ── Resurrection Aesthetic ────────────────────────────────────────────────
    'RAE0002':       'https://resurrection.beauty/cdn/shop/products/aesthetic-ultimate-cream.jpg',
    'RAUE0003':      'https://resurrection.beauty/cdn/shop/products/aesthetic-ultimate-essence.jpg',
    'RAGC0004':      'https://resurrection.beauty/cdn/shop/products/anti-gravity-cream.jpg',
    'RAGE0001':      'https://resurrection.beauty/cdn/shop/products/anti-gravity-essence.jpg',
    'RCF0005':       'https://resurrection.beauty/cdn/shop/products/cleansing-foam-gentle-balance.jpg',
    'RMIN0007':      'https://resurrection.beauty/cdn/shop/products/mask-intensive-nurturing.jpg',
    'RSBSPF500008':  'https://resurrection.beauty/cdn/shop/products/radiance-sunblock-spf50.jpg',
    'RTDN0006':      'https://resurrection.beauty/cdn/shop/products/toner-dermeist-nurturing.jpg',

    # ── Revital Energy ────────────────────────────────────────────────────────
    'JBMREBS0015':    'https://resurrection.beauty/cdn/shop/products/revital-bachuchiol-serum.jpg',
    'JBMREC0018':     'https://resurrection.beauty/cdn/shop/products/revital-energy-cream.jpg',
    'JBMRECF0017':    'https://resurrection.beauty/cdn/shop/products/revital-gel-to-foam-cleanser.jpg',
    'JBMRESSSPA0016': 'https://resurrection.beauty/cdn/shop/products/revital-energy-sunscreen.jpg',
    'JBMRETUC0017':   'https://resurrection.beauty/cdn/shop/products/revital-tone-up-cream.jpg',
    'JBMRET0018':     'https://resurrection.beauty/cdn/shop/products/revital-energy-toner.jpg',

    # ── Revlon ────────────────────────────────────────────────────────────────
    'REVLON_5359CE8F': 'https://www.revlon.com/media/catalog/product/colorstay-limitless-matte-manifest.jpg',
    'REVLON_16D5B9F1': 'https://www.revlon.com/media/catalog/product/colorstay-limitless-matte-poster-child.jpg',

    # ── Rimmel ────────────────────────────────────────────────────────────────
    'RIMMELM_7BDFF8EA': 'https://www.rimmellondon.com/cdn/shop/products/multi-tasker-concealer-ivory.jpg',

    # ── SP Ayurved ────────────────────────────────────────────────────────────
    'SPA-HAIR-003': 'https://spayurved.com/cdn/shop/products/amla-shampoo-200ml.jpg',
    'SPA-HAIR-004': 'https://spayurved.com/cdn/shop/products/amla-shampoo-500ml.jpg',
    'SPA-SKIN-012': 'https://spayurved.com/cdn/shop/products/bridal-facial-kit.jpg',
    'SPA-SOAP-005': 'https://spayurved.com/cdn/shop/products/bridal-soap.jpg',
    'SPA-SOAP-009': 'https://spayurved.com/cdn/shop/products/coffee-d10-soap.jpg',
    'SPA-SKIN-018': 'https://spayurved.com/cdn/shop/products/d10-pack.jpg',
    'SPA-SKIN-003': 'https://spayurved.com/cdn/shop/products/day-cream.jpg',
    'SPA-SKIN-010': 'https://spayurved.com/cdn/shop/products/face-massager-gel.jpg',
    'SPA-SKIN-019': 'https://spayurved.com/cdn/shop/products/face-pack.jpg',
    'SPA-SKIN-015': 'https://spayurved.com/cdn/shop/products/face-serum.jpg',
    'SPA-SKIN-014': 'https://spayurved.com/cdn/shop/products/face-wash.jpg',
    'SPA-SOAP-001': 'https://spayurved.com/cdn/shop/products/facial-bar.jpg',
    'SPA-SKIN-017': 'https://spayurved.com/cdn/shop/products/foot-balm.jpg',
    'SPA-HAIR-012': 'https://spayurved.com/cdn/shop/products/hair-colour.jpg',
    'SPA-HAIR-007': 'https://spayurved.com/cdn/shop/products/hair-mask-100ml.jpg',
    'SPA-HAIR-008': 'https://spayurved.com/cdn/shop/products/hair-mask-200ml.jpg',
    'SPA-HAIR-009': 'https://spayurved.com/cdn/shop/products/hair-mask-500ml.jpg',
    'SPA-HAIR-011': 'https://spayurved.com/cdn/shop/products/hair-mehandi.jpg',
    'SPA-HAIR-005': 'https://spayurved.com/cdn/shop/products/hair-oil-200ml.jpg',
    'SPA-HAIR-006': 'https://spayurved.com/cdn/shop/products/hair-oil-500ml.jpg',
    'SPA-HAIR-010': 'https://spayurved.com/cdn/shop/products/hair-pack.jpg',
    'SPA-SKIN-021': 'https://spayurved.com/cdn/shop/products/hair-remover-spray.jpg',
    'SPA-SOAP-004': 'https://spayurved.com/cdn/shop/products/haldi-soap.jpg',
    'SPA-SOAP-006': 'https://spayurved.com/cdn/shop/products/hyaluronic-scrub-soap.jpg',
    'SPA-SOAP-003': 'https://spayurved.com/cdn/shop/products/keshuda-soap.jpg',
    'SPA-SKIN-004': 'https://spayurved.com/cdn/shop/products/korean-cream.jpg',
    'SPA-SOAP-010': 'https://spayurved.com/cdn/shop/products/lemon-soap.jpg',
    'SPA-SKIN-016': 'https://spayurved.com/cdn/shop/products/lip-balm.jpg',
    'SPA-SOAP-008': 'https://spayurved.com/cdn/shop/products/multani-mitti-soap.jpg',
    'SPA-SKIN-008': 'https://spayurved.com/cdn/shop/products/neela-moroccan-facial-kit.jpg',
    'SPA-SKIN-013': 'https://spayurved.com/cdn/shop/products/neela-murakkan-facial-kit.jpg',
    'SPA-HAIR-013': 'https://spayurved.com/cdn/shop/products/neem-comb.jpg',
    'SPA-SOAP-007': 'https://spayurved.com/cdn/shop/products/neem-soap.jpg',
    'SPA-SKIN-002': 'https://spayurved.com/cdn/shop/products/night-cream.jpg',
    'SPA-SKIN-006': 'https://spayurved.com/cdn/shop/products/open-pore-gel.jpg',
    'SPA-SKIN-011': 'https://spayurved.com/cdn/shop/products/regular-facial-kit.jpg',
    'SPA-SKIN-007': 'https://spayurved.com/cdn/shop/products/regular-scrub.jpg',
    'SPA-HAIR-001': 'https://spayurved.com/cdn/shop/products/rice-shampoo-200ml.jpg',
    'SPA-HAIR-002': 'https://spayurved.com/cdn/shop/products/rice-shampoo-500ml.jpg',
    'SPA-SOAP-002': 'https://spayurved.com/cdn/shop/products/rice-soap.jpg',
    'SPA-SKIN-001': 'https://spayurved.com/cdn/shop/products/sp-special-skin-care-kit.jpg',
    'SPA-SKIN-009': 'https://spayurved.com/cdn/shop/products/sugar-scrub.jpg',
    'SPA-SKIN-020': 'https://spayurved.com/cdn/shop/products/sunscreen-lotion.jpg',
    'SPA-SKIN-005': 'https://spayurved.com/cdn/shop/products/us-cream.jpg',
    'SPA-WELL-001': 'https://spayurved.com/cdn/shop/products/weight-loss-powder.jpg',

    # ── Some By Mi ────────────────────────────────────────────────────────────
    'SBM-ABP-003': 'https://www.somebymi.com/cdn/shop/products/aha-bha-pha-30days-toner.jpg',

    # ── Soulflower ────────────────────────────────────────────────────────────
    'SOULFLOW_427EBCA7': 'https://soulflower.in/cdn/shop/products/lavender-face-toner.jpg',
    'SOULFLOW_9EEC3C52': 'https://soulflower.in/cdn/shop/products/rosemary-scalp-hair-oil.jpg',

    # ── Sugar Cosmetics ───────────────────────────────────────────────────────
    'SUGARCO_08B0A061': 'https://www.sugarcosmetics.com/cdn/shop/products/contour-de-force-blush.jpg',
    'SUGARCO_8A9332F0': 'https://www.sugarcosmetics.com/cdn/shop/products/first-base-primer-sunscreen.jpg',
    'SUGARCO_689BD689': 'https://www.sugarcosmetics.com/cdn/shop/products/kohl-of-honour-kajal.jpg',
    'SUGARCO_5EBE111A': 'https://www.sugarcosmetics.com/cdn/shop/products/mettle-satin-lipstick.jpg',
    'SUGARCO_E22A1F63': 'https://www.sugarcosmetics.com/cdn/shop/products/tip-tac-toe-lip-liner.jpg',

    # ── The Derma Co ──────────────────────────────────────────────────────────
    'THEDERM_FA8E3F54': 'https://thedermaco.com/cdn/shop/products/1-percent-retinol-face-serum.jpg',
    'THEDERM_D1C52F86': 'https://thedermaco.com/cdn/shop/products/10-niacinamide-face-serum.jpg',
    'THEDERM_698A1B46': 'https://thedermaco.com/cdn/shop/products/aqua-moisturiser.jpg',
    'THEDERM_B016A24D': 'https://thedermaco.com/cdn/shop/products/hyaluronic-acid-ceramide-serum.jpg',

    # ── Ultimate Repair Range ─────────────────────────────────────────────────
    'BURPSC0026': 'https://resurrection.beauty/cdn/shop/products/relief-soothing-cream.jpg',
    'BURC0023':   'https://resurrection.beauty/cdn/shop/products/ultimate-repair-cream.jpg',
    'BURS0025':   'https://resurrection.beauty/cdn/shop/products/ultimate-repair-serum.jpg',
    'BURT0024':   'https://resurrection.beauty/cdn/shop/products/ultimate-repair-toner.jpg',

    # ── WOW Skin Science ──────────────────────────────────────────────────────
    'WOWSKIN_E9F7A34D': 'https://www.mywowskin.com/cdn/shop/products/apple-cider-vinegar-face-wash.jpg',
    'WOWSKIN_7486BD87': 'https://www.mywowskin.com/cdn/shop/products/spf-50-sunscreen-gel.jpg',
    'WOWSKIN_48A68648': 'https://www.mywowskin.com/cdn/shop/products/vitamin-c-serum.jpg',

    # ── mCaffeine ─────────────────────────────────────────────────────────────
    'MCAFFEIN_EC68F187': 'https://mcaffeine.com/cdn/shop/products/coffee-body-scrub.jpg',
    'MCAFFEIN_42041991': 'https://mcaffeine.com/cdn/shop/products/coffee-face-wash.jpg',
    'MCAFFEIN_BE4A8D1D': 'https://mcaffeine.com/cdn/shop/products/coffee-under-eye-cream.jpg',
}


class Command(BaseCommand):
    help = (
        'Fill missing product prices (India market ₹) and image URLs. '
        'Safe to re-run — only updates fields that are blank/null.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without saving to the database.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing prices/images too (not just missing ones).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force   = options['force']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be saved.\n'))

        price_updated = 0
        image_updated = 0
        skipped       = 0

        all_products = {p.sku: p for p in Product.objects.all()}

        # ── Apply prices ─────────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== PRICES ==='))
        for sku, price_inr in PRICE_MAP.items():
            product = all_products.get(sku)
            if not product:
                self.stdout.write(self.style.WARNING(f'  SKU not found: {sku}'))
                continue

            if product.price is not None and not force:
                skipped += 1
                continue

            old = product.price
            if not dry_run:
                product.price = Decimal(str(price_inr))
                product.save(update_fields=['price'])
            price_updated += 1
            self.stdout.write(
                f'  ✓ [{sku}] {product.brand} — {product.name[:50]}: '
                f'₹{old} → ₹{price_inr}'
            )

        # ── Apply images ─────────────────────────────────────────────────────
        self.stdout.write(self.style.MIGRATE_HEADING('\n=== IMAGES ==='))
        for sku, url in IMAGE_MAP.items():
            product = all_products.get(sku)
            if not product:
                self.stdout.write(self.style.WARNING(f'  SKU not found: {sku}'))
                continue

            if product.image_url and not force:
                skipped += 1
                continue

            old = product.image_url or '(none)'
            if not dry_run:
                product.image_url = url
                product.save(update_fields=['image_url'])
            image_updated += 1
            self.stdout.write(f'  ✓ [{sku}] {product.brand} — {product.name[:45]}')

        # ── Summary ──────────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Done.  Prices updated: {price_updated}  |  '
            f'Images updated: {image_updated}  |  '
            f'Skipped (already set): {skipped}'
        ))
        if dry_run:
            self.stdout.write(self.style.WARNING(
                'Nothing was saved. Remove --dry-run to apply changes.'
            ))
