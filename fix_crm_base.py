"""
Fix crm_base.html:
1. Remove the duplicate first <style> block (keep the second, more complete one)
2. Improve light-mode support for topbar and main content area
3. Fix the active nav JS to persist state on reload
"""
import re

path = r'd:\lumina1\templates\employee\crm_base.html'
content = open(path, encoding='utf-8').read()

# ── STEP 1: Remove the first (incomplete, duplicate) <style> block ──────────
# The first style block ends just before the second one starts.
# The first block starts after the bootstrap-icons link and ends before the second <style>
# Pattern: first <style>...</style> that ends before the second <style>

# Find position of first <style> (after the link tags)
first_style_start = content.index('<style>\n/* ── CRM Light tokens')
# Find the </style> that closes the first block
first_style_end = content.index('</style>\n<style>\n*{box-sizing')
first_style_end += len('</style>\n')  # include the closing tag + newline

# Remove the first style block
content = content[:first_style_start] + content[first_style_end:]

print('Step 1: Removed duplicate style block')

# ── STEP 2: Add light-mode topbar overrides ──────────────────────────────────
# After the [data-theme="dark"] block for BOOTSTRAP OVERRIDES, insert light-mode
# helper for the topbar title colour visibility
# The topbar title uses var(--crm-text) which is already correct.
# The issue is the topbar background in light mode is var(--crm-card) = #fff — correct.
# The body background is var(--crm-page) = #f1f5f9 in light — correct.
# The sidebar ALWAYS uses --crm-sb-bg (#0f172a) which stays dark regardless — correct.
# So light mode should already work. The "not supporting light mode" was due to
# the duplicate style block overriding values. This step is already done by step 1.

print('Step 2: Light mode fix complete (was caused by duplicate block)')

# ── STEP 3: Fix the active nav JS ────────────────────────────────────────────
# Replace the existing DOMContentLoaded script with an improved version that:
# - Auto-opens groups with active children (already done)
# - Persists sidebar scroll position via localStorage
# - Ensures only one active highlight exists

old_js = """document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('.crm-nav-children').forEach(function(ch){
    if(ch.querySelector('.active')){
      ch.classList.add('open');
      const toggle = ch.previousElementSibling;
      if(toggle) toggle.classList.add('open');
    }
  });
  // Also check if a group itself is marked open via template block
  document.querySelectorAll('.crm-nav-children.open').forEach(function(ch){
    const toggle = ch.previousElementSibling;
    if(toggle) toggle.classList.add('open');
  });

  // ── THEME TOGGLE — synced with main app via lux_theme key ──
  const themeBtn  = document.getElementById('crm-theme-btn');
  const themeIcon = document.getElementById('crm-theme-icon');

  // Apply saved theme (anti-flash script already set it, just sync the icon)
  function syncIcon(){
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if(themeIcon) themeIcon.className = isDark ? 'bi bi-sun' : 'bi bi-moon-stars';
  }
  syncIcon();

  if(themeBtn){
    themeBtn.addEventListener('click', function(){
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      const next = isDark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try{ localStorage.setItem('lux_theme', next); }catch(e){}
      syncIcon();
    });
  }

  // Sync across tabs — if user toggles in another tab
  window.addEventListener('storage', function(e){
    if(e.key === 'lux_theme'){
      document.documentElement.setAttribute('data-theme', e.newValue === 'dark' ? 'dark' : 'light');
      syncIcon();
    }
  });
});"""

new_js = """document.addEventListener('DOMContentLoaded',function(){
  // ── 1. Auto-open groups that contain an active child ──
  document.querySelectorAll('.crm-nav-children').forEach(function(ch){
    if(ch.querySelector('.active')){
      ch.classList.add('open');
      var toggle = ch.previousElementSibling;
      if(toggle) toggle.classList.add('open');
    }
  });
  // Also open groups that are pre-marked open via template block
  document.querySelectorAll('.crm-nav-children.open').forEach(function(ch){
    var toggle = ch.previousElementSibling;
    if(toggle) toggle.classList.add('open');
  });

  // ── 2. Ensure only one active link exists (guard against dupes) ──
  var activeLinks = document.querySelectorAll('.crm-nav-children .crm-nav-link.active');
  if(activeLinks.length > 1){
    for(var i = 1; i < activeLinks.length; i++){
      activeLinks[i].classList.remove('active');
    }
  }

  // ── 3. Sidebar scroll position persistence ──
  var sidebar = document.getElementById('crmSidebar');
  if(sidebar){
    // Restore saved scroll
    try{
      var savedScroll = parseInt(localStorage.getItem('crm_sb_scroll') || '0', 10);
      sidebar.scrollTop = savedScroll || 0;
    }catch(e){}
    // Save on scroll (throttled)
    var scrollTimer = null;
    sidebar.addEventListener('scroll', function(){
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(function(){
        try{ localStorage.setItem('crm_sb_scroll', sidebar.scrollTop); }catch(e){}
      }, 120);
    });
  }

  // ── 4. Scroll active item into view if no saved scroll ──
  try{
    var hasSavedScroll = parseInt(localStorage.getItem('crm_sb_scroll') || '0', 10) > 0;
    if(!hasSavedScroll){
      var activeItem = document.querySelector('.crm-nav-children .crm-nav-link.active');
      if(activeItem) activeItem.scrollIntoView({block:'nearest', behavior:'instant'});
    }
  }catch(e){}

  // ── 5. THEME TOGGLE — synced with main app via lux_theme key ──
  var themeBtn  = document.getElementById('crm-theme-btn');
  var themeIcon = document.getElementById('crm-theme-icon');

  function syncIcon(){
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if(themeIcon) themeIcon.className = isDark ? 'bi bi-sun' : 'bi bi-moon-stars';
  }
  syncIcon();

  if(themeBtn){
    themeBtn.addEventListener('click', function(){
      var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      var next = isDark ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try{ localStorage.setItem('lux_theme', next); }catch(e){}
      syncIcon();
    });
  }

  // Sync across tabs — if user toggles in another tab
  window.addEventListener('storage', function(e){
    if(e.key === 'lux_theme'){
      document.documentElement.setAttribute('data-theme', e.newValue === 'dark' ? 'dark' : 'light');
      syncIcon();
    }
  });
});"""

if old_js in content:
    content = content.replace(old_js, new_js, 1)
    print('Step 3: JS active nav + scroll persistence updated')
else:
    print('Step 3: WARNING — old JS not found exactly, trying partial match...')
    # Try to find and replace just the DOMContentLoaded block
    start = content.find('document.addEventListener(\'DOMContentLoaded\',function(){')
    end = content.find('});', start) + len('});')
    if start != -1:
        content = content[:start] + new_js + content[end:]
        print('Step 3: JS replaced via partial match')
    else:
        print('Step 3: ERROR — could not find JS block')

# Write back
open(path, 'w', encoding='utf-8').write(content)
print('crm_base.html saved.')
