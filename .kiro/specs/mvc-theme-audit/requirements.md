# Requirements Document

## Introduction

Lumina is a Django-based AI beauty and skincare recommendation platform with eight sub-applications: `accounts`, `chat`, `core`, `dashboard`, `employee`, `products`, `results`, and `scanner`. This feature covers a two-part audit and remediation effort:

1. **MVC Architecture Audit** — enforce proper separation of concerns across all Django apps so that models own data logic, views own request/response orchestration, and templates own presentation. Business logic, inline SQL, and direct AI-service calls that currently live in views (e.g., `results/views.py` embeds `_call_groq`, `_generate_makeup_routine`, `_generate_kbeauty_routine`, `_parse_vision_data`, and a 400-line `CONDITION_INFO` dictionary) must be extracted to appropriate layers.

2. **Theme Consistency Audit** — ensure every page inherits from `base.html`, uses the shared CSS design tokens defined in `style.css`, and renders consistently in both light and dark mode across all eight app template directories.

## Glossary

- **View**: A Django view function or class responsible only for handling HTTP requests, delegating to services, and returning rendered responses or JSON.
- **Service**: A Python module (e.g., `services.py`) inside an app that encapsulates business logic, AI calls, and data-transformation functions.
- **Template**: An HTML file under `templates/` that extends `base.html` and contains only presentation logic (loops, conditionals, template tags).
- **Design Token**: A CSS custom property defined in `:root {}` within `style.css` (e.g., `--lux-gold`, `--page-bg`, `--text`).
- **Base Template**: `templates/base.html` — the single shared layout that provides the sidebar, topbar, mobile nav, dark-mode toggle, and `{% block content %}`.
- **MVC Violation**: Business logic, raw queries, AI calls, or large data dictionaries embedded directly in a view function rather than delegated to a service or model.
- **Theme Violation**: A template that does not extend `base.html`, uses hard-coded colour values instead of design tokens, or renders incorrectly in dark mode.
- **Lumina_App**: Any of the eight Django sub-applications registered in `INSTALLED_APPS`.
- **AI_Service**: An external API call (Groq, HuggingFace, Gemini, etc.) made to produce AI-generated content.
- **Condition_Registry**: The authoritative store of dermatological condition metadata (currently the `CONDITION_INFO` dict in `results/views.py`).

---

## Requirements

### Requirement 1: Extract Business Logic from Views into Service Modules

**User Story:** As a developer, I want all business logic isolated in dedicated service modules, so that views remain thin and easy to test and maintain.

#### Acceptance Criteria

1. THE `results` App SHALL provide a `services.py` module that defines `generate_makeup_routine`, `generate_kbeauty_routine`, `parse_vision_data`, `determine_severity`, `_call_groq`, and `CONDITION_INFO` as module-level symbols.
2. IF the `results/views.py` `skin_results` view is called, THEN THE `results/views.py` module SHALL NOT define or call `generate_makeup_routine`, `generate_kbeauty_routine`, `parse_vision_data`, `determine_severity`, or `_call_groq` directly; all invocations SHALL go through `results.services`.
3. THE `results` App `services.py` `_call_groq` helper SHALL be the sole function that imports and calls the Groq client; on any API error it SHALL return an empty dict `{}`; no Groq import SHALL remain in `views.py`.
4. THE `scanner` App SHALL provide a `services.py` module that defines a `detect_concerns(facial_zones: dict, hf_acne_severity: str) -> list[str]` function encapsulating these concern-detection rules: add `"acne"` when `hf_acne_severity in {"mild","moderate","severe"}`; add `"large_pores"` when `facial_zones.get("nose",{}).get("score",0) >= 60`; add `"oiliness"` when `facial_zones.get("forehead",{}).get("score",0) >= 55`; add `"dryness"` when `facial_zones.get("cheeks",{}).get("score",0) <= 30`; add `"dark_circles"` when `facial_zones.get("eyes",{}).get("score",0) >= 50`.
5. IF the `scanner/views.py` `upload` view processes a POST request, THEN `scanner/views.py` SHALL NOT contain the score-threshold comparisons described in criterion 4; it SHALL call `scanner.services.detect_concerns(scan.facial_zones, scan.hf_acne_severity)` and assign the returned list to the scan's detected concerns.
6. THE `chat` App `views.py` SHALL define `_build_scan_context` and `_resolve_products` as module-level functions; these are view-layer helpers that directly prepare HTTP request context and SHALL NOT be moved to a separate services module.
7. THE `employee` App `views.py` SHALL continue to contain only CRUD request-handling logic; no `services.py` module is required for `employee` because the app has no business logic beyond ORM reads and writes.

---

### Requirement 2: Centralise Dermatological Condition Registry

**User Story:** As a developer, I want the condition metadata defined in one place, so that adding or editing a condition does not require searching multiple files.

#### Acceptance Criteria

1. THE `results` App `services.py` SHALL define `CONDITION_INFO` as the single authoritative registry of condition metadata (display name, description, causes, advice, medicine options, use/avoid ingredients, dermatologist flag); no other file in the project SHALL define a symbol named `CONDITION_INFO`.
2. IF any view, service, or template tag function requires condition metadata, THEN it SHALL import from `results.services.CONDITION_INFO`; direct definition of condition data in any other module is not permitted.
3. THE `CONDITION_INFO` registry SHALL contain exactly twelve top-level keys — `acne`, `dark_circles`, `pigmentation`, `blackheads`, `dryness`, `redness`, `fine_lines`, `large_pores`, `aging`, `oiliness`, `dullness`, and `sensitivity` — and each entry SHALL include these seven fields: `name` (str), `description` (str), `causes` (list[str]), `advice` (list[str]), `medicine` (list[str]), `use_ingredients` (list[str]), `avoid_ingredients` (list[str]), and `see_dermatologist` (bool).

---

### Requirement 3: Resolve `results` App Model Duplication

**User Story:** As a developer, I want a single source of truth for scan result data, so that `results/models.py` does not shadow fields already present on `scanner.ScanResult`.

#### Acceptance Criteria

1. THE `results.ScanResult` model SHALL NOT declare any of these eleven fields that already exist on `scanner.ScanResult`: `skin_type`, `undertone`, `acne_severity` (stored as `hf_acne_severity` on scanner), `hydration_score`, `forehead_severity`, `nose_severity`, `left_cheek_severity`, `right_cheek_severity`, `chin_severity`, `overall_score` (stored as `harmony_score` on scanner), and `skin_health_score` (stored as `elasticity_score` on scanner).
2. IF `results.ScanResult` has no fields with data that is unique to the results layer after removing duplicates, THEN the class docstring SHALL state one of: (a) `"Scheduled for removal — migrate views to read directly from scanner.ScanResult"` with a corresponding migration to drop the table, or (b) `"Extension model — stores <list unique fields> not present on scanner.ScanResult"` identifying at least one field that justifies the model's continued existence.
3. THE `results/views.py` `skin_results` view SHALL obtain its scan data by querying `scanner.ScanResult.objects.get(pk=scan_id)` and SHALL NOT import or instantiate `results.models.ScanResult`; it SHALL read these attributes directly from the `scanner.ScanResult` instance: `skin_tone`, `undertone`, `skin_type`, `hf_acne_severity`, `hydration_score`, `facial_zones`, `harmony_score`, `pigmentation_score`, `acne_score`, `aging_score`, `elasticity_score`, `detected_concerns`, `scan_image`, and `created_at`.

---

### Requirement 4: Uniform Template Inheritance

**User Story:** As a developer, I want every page template to extend `base.html`, so that the sidebar, topbar, dark-mode support, and navigation are consistent across all pages.

#### Acceptance Criteria

1. EVERY HTML file under `templates/` — across all eight app template directories and `templates/treatments/` — SHALL begin with `{% extends 'base.html' %}` as its first non-whitespace line.
2. EVERY template that extends `base.html` SHALL define a `{% block content %}` block; `{% block title %}` and `{% block page_title %}` are optional because `base.html` already supplies defaults for those two blocks.
3. IF any HTML file under `templates/` does not begin with `{% extends 'base.html' %}`, THEN it SHALL be refactored to extend `base.html` and define at minimum `{% block content %}` before this requirement is considered satisfied.

---

### Requirement 5: Exclusive Use of CSS Design Tokens

**User Story:** As a developer, I want all templates and the global stylesheet to use CSS custom properties from `style.css`, so that changing the brand palette requires only updating `:root {}`.

#### Acceptance Criteria

1. ALL CSS colour-bearing properties — including `color`, `background`, `background-color`, `background-image` (gradients), `border-color`, `box-shadow`, `fill`, `stroke`, and `outline-color` — in `style.css` and in any `<style>` block in any template SHALL use `var(--token-name)` references rather than literal hex, rgb, rgba, hsl, or named colour values.
2. EVERY CSS custom property referenced via `var(--X)` anywhere in the project SHALL be declared in the `:root {}` block of `style.css`; a `var()` reference with no matching `:root` declaration is a violation.
3. THE `base.html` inline `<style>` block SHALL retain only layout-shell custom properties (`--sb-w`, `--sb-w-col`, `--top-h`, `--mob-bot-h`) and sidebar-specific colour aliases (`--sb-bg`, `--sb-border`, `--sb-text`, `--sb-text-act`, `--sb-gold`, `--sb-teal`, `--sb-hover`, `--sb-active`); all other colour-valued custom properties in that block (`--page-bg`, `--surface`, `--border`, `--text`, `--muted`, `--font-serif`, `--font-sans`) SHALL be moved to `style.css` `:root {}`.
4. IF a `[data-theme="dark"]` override block in any template's inline `<style>` contains literal colour values, THEN those values SHALL be replaced with `var(--token-name)` references to tokens declared in the `[data-theme="dark"]` block of `style.css`.

---

### Requirement 6: Dark Mode Completeness

**User Story:** As a user, I want every page to display correctly in dark mode, so that the reading experience is consistent regardless of the selected theme.

#### Acceptance Criteria

1. WHEN `data-theme="dark"` is set on `<html>`, THE `[data-theme="dark"]` block in `style.css` SHALL override at minimum these thirteen tokens: `--page-bg`, `--surface`, `--border`, `--text`, `--muted`, `--lux-gold`, `--card-bg`, `--input-bg`, `--input-border`, `--tag-bg`, `--badge-bg`, `--score-track`, and `--overlay-bg`; every template surface and card that uses these tokens SHALL automatically render in dark colours without additional per-template overrides.
2. IF `base.html`'s inline `<style>` block contains a `[data-theme="dark"]` override section, THEN that section SHALL be removed and its token overrides SHALL be consolidated into the `[data-theme="dark"]` block in `style.css` so there is exactly one dark-mode override location.
3. IF any template's inline `<style>` or `<style>` block contains a literal hex, rgb, rgba, or named colour value in a rule that applies to a surface, text, or border element, THEN that value SHALL be replaced with a `var(--token-name)` reference so that switching to dark mode changes the visual without requiring a template edit.
4. THE dark mode toggle button (`#theme-btn`) in `base.html`'s topbar SHALL write the selected theme string to `localStorage` under the key `lux_theme` and, on every page load, the inline script in `base.html` SHALL read `localStorage.getItem('lux_theme')` before first paint and set `document.documentElement.setAttribute('data-theme', value)` to prevent a flash of the wrong theme.
5. THE `.lux-alert-success`, `.lux-alert-error`, `.lux-alert-warning`, and `.lux-alert-info` alert classes defined in `base.html` SHALL use `var(--token-name)` for their `background`, `color`, and `border-color` values, and corresponding dark-mode overrides SHALL be present in `style.css` so alerts are legible in both themes.

---

### Requirement 7: App-Level URL Namespace Consistency

**User Story:** As a developer, I want every Django app to define an `app_name` in its `urls.py`, so that `{% url %}` template tags use consistent namespaced names.

#### Acceptance Criteria

1. THE `urls.py` of every Lumina app — `accounts`, `chat`, `core`, `dashboard`, `employee`, `products`, `results`, `scanner`, and `treatments` — SHALL declare `app_name` as a module-level string whose value matches the app's directory name exactly (e.g., `app_name = "accounts"`).
2. IF any template uses `{% url 'view_name' %}` or any view uses `redirect('view_name')` / `reverse('view_name')` with a bare (non-namespaced) name that resolves through an app URL conf that defines `app_name`, THEN that reference SHALL be replaced with the namespaced form `{% url 'app_name:view_name' %}` or `redirect('app_name:view_name')`.
3. THE `lumina/urls.py` root URL file SHALL pass each app's URL module to `include()` using only the dotted-path string form (e.g., `include('apps.accounts.urls')`) without a `namespace=` keyword argument; the app-level `app_name` variable is the sole source of the namespace.
4. IF a URL name is resolved by a bare string anywhere in the project — in `lumina/urls.py` via a direct view import (e.g., `path('me/', user_home, name='user_home')`), in a template via `{% url 'user_home' %}`, or in view code via `redirect('user_home')` — THEN a code comment at each usage site SHALL explain that the name is registered at the root URL conf level rather than within an app URL conf and that this is intentional.

---

### Requirement 8: Form Handling Separation

**User Story:** As a developer, I want all form logic to live in `forms.py` files, so that views do not manually validate or construct model fields from `request.POST`.

#### Acceptance Criteria

1. THE `employee` app SHALL provide a `forms.py` module containing a `ProductForm` Django `ModelForm` with `model = Product` and `fields` listing all fifteen fields currently parsed manually: `name`, `brand`, `category`, `product_range`, `sku`, `price`, `description`, `key_ingredients`, `full_ingredients`, `image_url`, `coverage`, `finish`, `undertone_match`, `skin_tone_match`, and `is_featured`.
2. WHEN a valid POST request is received by `product_add`, THE view SHALL instantiate `ProductForm(request.POST)`, call `form.is_valid()`, and persist via `form.save()`; no `request.POST.get(...)` or `request.POST[...]` call SHALL remain in the view body for any of the fifteen fields listed in criterion 1.
3. IF `ProductForm(request.POST).is_valid()` returns `False` in either `product_add` or `product_edit`, THEN THE view SHALL re-render the form template passing the bound `form` instance in context so that validation errors are displayed to the user.
4. THE `accounts` app `forms.py` `LuminaSignupForm` SHALL remain the sole form for account creation; no `request.POST.get(...)` or `request.POST[...]` call for account fields (`username`, `email`, `password`, `first_name`, `last_name`) SHALL appear in `accounts/views.py`.

---

### Requirement 9: Static File and Template Loading Correctness

**User Story:** As a developer, I want static files and templates to load without errors in both development and production, so that no broken CSS or JavaScript occurs after deployment.

#### Acceptance Criteria

1. THE `base.html` template SHALL load the global stylesheet using exactly `<link rel="stylesheet" href="{% static 'css/style.css' %}">` and SHALL NOT load any other app-specific stylesheet via a `<link>` tag outside of `{% block extra_css %}`; per-page styles SHALL be placed inside `{% block extra_css %}` in child templates.
2. WHEN `python manage.py collectstatic --noinput` is executed against the production settings, THE command SHALL exit with code 0 and SHALL copy all files from `STATICFILES_DIRS` into `STATIC_ROOT` without raising `FileNotFoundError`, `ManifestStaticFilesStorage` hash errors, or missing-file warnings.
3. THE `lumina/settings.py` SHALL retain `STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'` (or its Django 4.2+ equivalent `STORAGES` dict form) as the static files backend for production; this line SHALL NOT be removed or replaced with an uncompressed backend.
4. IF any template contains more than one `{% load static %}` tag, or contains zero `{% load static %}` tags while using `{% static %}` elsewhere in the file, THEN that template SHALL be corrected so that `{% load static %}` appears exactly once as the first template tag in the file (after `{% extends %}` if present).

---

### Requirement 10: Consistent Staff-Access Guard Pattern

**User Story:** As a developer, I want staff access checks to follow a single consistent pattern, so that no admin route is accidentally left unguarded.

#### Acceptance Criteria

1. THE `employee/views.py` `_is_staff(user)` helper SHALL be the only location in the `employee` app where the staff-check condition is expressed; every view function in `employee/views.py` SHALL call `_is_staff(request.user)` as the first guard after `@login_required` and SHALL NOT inline the condition directly.
2. THE `accounts/views.py` `user_home` view SHALL evaluate staff status using `request.user.is_staff or request.user.is_superuser or request.user.username == 'suhani'` — the exact same three-clause condition used in `_is_staff` — with no additional or missing clauses.
3. IF the staff-check condition (`user.is_staff or user.is_superuser or user.username == 'suhani'`) appears in three or more distinct Python modules, THEN a shared `is_staff(user)` helper SHALL be extracted to `apps/core/utils.py` and all existing call sites SHALL import from there; `employee/views.py` MAY keep a local alias for backwards compatibility.
4. THE `base.html` sidebar Admin section guard SHALL use `{% if user.is_staff or user.is_superuser or user.username == 'suhani' %}` — the same three-clause condition — to show or hide Admin nav items; the user-role badge in `.sb-user-role` SHALL also display `"Admin"` when `user.is_staff or user.is_superuser or user.username == 'suhani'` (the current template omits `user.is_superuser` from the role badge, which is a gap to fix).
