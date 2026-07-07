/* ============================================
   LUMINA - Main JavaScript File
   Pure Vanilla JS - No Libraries Required
   ============================================ */

// ============================================
// GLOBAL VARIABLES
// ============================================
let scanInterval = null;
let scanProgress = 0;
let scanMessageIndex = 0;

const scanMessages = [
  'Detecting your face...',
  'Checking face boundaries...',
  'Running acne analysis (skintelligent)...',
  'Classifying skin type...',
  'Analysing undertone...',
  'Mapping facial zones...',
  'Matching Korean products...',
  'Finding makeup shades...',
  'Preparing your report...'
];

// ============================================
// NAVIGATION FUNCTIONS
// ============================================

/**
 * Initialize mobile navigation toggle
 */
function initNavToggle() {
  const toggler = document.querySelector('.navbar-toggler-lumina');
  const mobileNav = document.getElementById('mobileNav');

  if (toggler && mobileNav) {
    toggler.addEventListener('click', () => {
      mobileNav.classList.toggle('show');
    });

    // Close mobile nav when clicking outside
    document.addEventListener('click', (e) => {
      if (!toggler.contains(e.target) && !mobileNav.contains(e.target)) {
        mobileNav.classList.remove('show');
      }
    });
  }
}

/**
 * Initialize main tabs for home page sections
 */
function initMainTabs() {
  const tabLinks = document.querySelectorAll('[data-main-tab]');
  
  tabLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const tabName = link.getAttribute('data-main-tab');
      
      // Remove active from all links
      tabLinks.forEach(l => l.classList.remove('active'));
      
      // Add active to clicked link
      link.classList.add('active');
      
      // Hide all sections
      document.querySelectorAll('[data-main-section]').forEach(section => {
        section.style.display = 'none';
      });
      
      // Show target section
      const targetSection = document.querySelector(`[data-main-section="${tabName}"]`);
      if (targetSection) {
        targetSection.style.display = 'block';
      }
    });
  });
}

// ============================================
// SCANNER FUNCTIONS
// ============================================

/**
 * Switch between face and body scanner
 * @param {string} type - 'face' or 'body'
 */
function switchScanner(type) {
  // Update toggle button states
  document.querySelectorAll('.scanner-toggle-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.getAttribute('data-scanner-type') === type) {
      btn.classList.add('active');
    }
  });

  // Show/hide scanner sections
  const faceSection = document.getElementById('face-scanner-section');
  const bodySection = document.getElementById('body-scanner-section');

  if (faceSection && bodySection) {
    if (type === 'face') {
      faceSection.style.display = 'block';
      bodySection.style.display = 'none';
    } else {
      faceSection.style.display = 'none';
      bodySection.style.display = 'block';
    }
  }
}

/**
 * Show specific scan state
 * @param {string} stateName - 'default', 'no-face', 'scanning', 'demo'
 */
function showScanState(stateName) {
  // Hide all states
  const states = ['state-default', 'state-no-face', 'state-scanning', 'state-demo'];
  states.forEach(state => {
    const element = document.getElementById(state);
    if (element) {
      element.classList.remove('active');
      element.style.display = 'none';
    }
  });

  // Show target state
  const targetState = document.getElementById(`state-${stateName}`);
  if (targetState) {
    targetState.classList.add('active');
    targetState.style.display = 'block';
  }

  // Start animation if scanning or demo
  if (stateName === 'scanning' || stateName === 'demo') {
    startScanAnimation();
  }
}

/**
 * Start the scanning animation with progress
 */
function startScanAnimation() {
  scanProgress = 0;
  scanMessageIndex = 0;

  const progressFill = document.querySelector('.scan-progress-fill');
  const statusText = document.querySelector('.scanning-status');

  if (!progressFill || !statusText) return;

  // Reset progress
  progressFill.style.width = '0%';
  statusText.textContent = scanMessages[0];

  // Clear any existing interval
  if (scanInterval) {
    clearInterval(scanInterval);
  }

  // Animate progress and messages
  scanInterval = setInterval(() => {
    // Increment progress
    scanProgress += 2;
    
    if (scanProgress <= 95) {
      progressFill.style.width = scanProgress + '%';
    }

    // Update message every 450ms
    if (scanProgress % 10 === 0 && scanMessageIndex < scanMessages.length - 1) {
      scanMessageIndex++;
      statusText.textContent = scanMessages[scanMessageIndex];
    }
  }, 100);

  // After 3500ms, complete the scan
  setTimeout(() => {
    clearInterval(scanInterval);
    scanProgress = 100;
    progressFill.style.width = '100%';
    statusText.textContent = scanMessages[scanMessages.length - 1];

    // Submit form after a short delay
    setTimeout(() => {
      const scanForm = document.getElementById('scanForm');
      if (scanForm) {
        scanForm.submit();
      }
    }, 400);
  }, 3500);
}

// ============================================
// TAB FUNCTIONS
// ============================================

/**
 * Initialize drag-to-scroll for tab bars
 */
function initScrollTabBar() {
  const tabBars = document.querySelectorAll('.scroll-tab-bar');

  tabBars.forEach(tabBar => {
    let isDown = false;
    let startX;
    let scrollLeft;

    tabBar.addEventListener('mousedown', (e) => {
      isDown = true;
      tabBar.style.cursor = 'grabbing';
      startX = e.pageX - tabBar.offsetLeft;
      scrollLeft = tabBar.scrollLeft;
    });

    tabBar.addEventListener('mouseleave', () => {
      isDown = false;
      tabBar.style.cursor = 'grab';
    });

    tabBar.addEventListener('mouseup', () => {
      isDown = false;
      tabBar.style.cursor = 'grab';
    });

    tabBar.addEventListener('mousemove', (e) => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - tabBar.offsetLeft;
      const walk = (x - startX) * 2;
      tabBar.scrollLeft = scrollLeft - walk;
    });
  });
}

/**
 * Switch between tabs
 * @param {string} tabId - ID of the tab to show
 */
function switchTab(tabId) {
  // Hide all tab panels
  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.remove('active');
    panel.style.display = 'none';
  });

  // Remove active from all tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Show target tab panel
  const targetPanel = document.getElementById(tabId);
  if (targetPanel) {
    targetPanel.classList.add('active');
    targetPanel.style.display = 'block';
  }

  // Add active to clicked button
  const targetBtn = document.querySelector(`[data-tab="${tabId}"]`);
  if (targetBtn) {
    targetBtn.classList.add('active');
  }
}

/**
 * Switch between sub-tabs (e.g., makeup categories)
 * @param {string} subTabId - ID of the sub-tab to show
 */
function switchSubTab(subTabId) {
  // Hide all sub-tab panels
  document.querySelectorAll('.subtab-panel').forEach(panel => {
    panel.classList.remove('active');
    panel.style.display = 'none';
  });

  // Remove active from all sub-tab buttons
  document.querySelectorAll('.subtab-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Show target sub-tab panel
  const targetPanel = document.getElementById(subTabId);
  if (targetPanel) {
    targetPanel.classList.add('active');
    targetPanel.style.display = 'block';
  }

  // Add active to clicked button
  const targetBtn = document.querySelector(`[data-subtab="${subTabId}"]`);
  if (targetBtn) {
    targetBtn.classList.add('active');
  }
}

// ============================================
// PROGRESS BAR ANIMATION
// ============================================

/**
 * Initialize animated progress bars
 */
function initProgressBars() {
  setTimeout(() => {
    const progressBars = document.querySelectorAll('[data-width]');
    
    progressBars.forEach(bar => {
      const targetWidth = bar.getAttribute('data-width');
      bar.style.width = targetWidth + '%';
    });
  }, 300);
}

// ============================================
// FACE ZONE MAP
// ============================================

/**
 * Initialize face zone map with severity data
 * @param {Object} zonesData - Object with zone severities
 */
function initFaceZoneMap(zonesData) {
  const zoneMap = {
    'forehead': zonesData.forehead || 'none',
    'nose': zonesData.nose || 'none',
    'left_cheek': zonesData.left_cheek || 'none',
    'right_cheek': zonesData.right_cheek || 'none',
    'chin': zonesData.chin || 'none'
  };

  const severityColors = {
    'none': '#8FAF9A',    // green
    'clear': '#8FAF9A',   // green
    'mild': '#EF9F27',    // yellow/amber
    'moderate': '#E07070', // orange/red
    'severe': '#B30000'   // dark red
  };

  // Update each zone dot
  Object.keys(zoneMap).forEach(zone => {
    const dot = document.getElementById(`zone-dot-${zone}`);
    if (dot) {
      const severity = zoneMap[zone];
      
      // Remove all severity classes
      dot.classList.remove('severity-none', 'severity-clear', 'severity-mild', 'severity-moderate', 'severity-severe');
      
      // Add current severity class
      dot.classList.add(`severity-${severity}`);
      
      // Set fill color
      dot.setAttribute('fill', severityColors[severity]);
    }
  });
}

// ============================================
// CHAT FUNCTIONS
// ============================================

/**
 * Get CSRF token from cookie
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Send chat message
 */
function sendChatMessage() {
  const messageInput = document.getElementById('messageInput');
  const chatMessages = document.getElementById('chatMessages');
  const conversationId = document.getElementById('conversationId')?.value;

  if (!messageInput || !chatMessages || !conversationId) return;

  const message = messageInput.value.trim();
  
  if (!message) return;

  // Append user message
  appendChatBubble('user', message);

  // Clear input
  messageInput.value = '';
  messageInput.style.height = 'auto';

  // Show typing indicator
  const typingId = appendTypingIndicator();

  // Scroll to bottom
  scrollChatToBottom();

  // Send to server
  fetch(`/chat/${conversationId}/send/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ message: message })
  })
  .then(response => response.json())
  .then(data => {
    // Remove typing indicator
    removeTypingIndicator(typingId);

    // Append AI response
    appendChatBubble('assistant', data.reply);

    // Append product suggestions if any
    if (data.product_suggestions && data.product_suggestions.length > 0) {
      appendProductRow(data.product_suggestions);
    }

    // Update conversation title if changed
    if (data.conversation_title) {
      const titleElement = document.querySelector('.conversation-title');
      if (titleElement && titleElement.textContent !== data.conversation_title) {
        titleElement.textContent = data.conversation_title;
      }
    }

    scrollChatToBottom();
  })
  .catch(error => {
    console.error('Error sending message:', error);
    removeTypingIndicator(typingId);
    appendChatBubble('assistant', 'Sorry, I encountered an error. Please try again.');
  });
}

/**
 * Append chat bubble to messages
 * @param {string} role - 'user' or 'assistant'
 * @param {string} content - Message content
 * @param {string} imageData - Optional base64 image data
 */
function appendChatBubble(role, content, imageData = null) {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;

  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;

  // Convert markdown-like syntax
  let formattedContent = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **bold**
    .replace(/\*(.*?)\*/g, '<em>$1</em>')              // *italic*
    .replace(/\n/g, '<br>');                           // newlines

  // Add image if provided
  if (imageData) {
    formattedContent = `<img src="${imageData}" alt="Uploaded" style="max-width: 200px; border-radius: 8px; margin-bottom: 0.5rem;"><br>${formattedContent}`;
  }

  bubble.innerHTML = formattedContent;
  chatMessages.appendChild(bubble);

  return bubble;
}

/**
 * Append typing indicator
 * @returns {string} Unique ID of the typing indicator
 */
function appendTypingIndicator() {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages) return;

  const typingId = 'typing-' + Date.now();
  const typing = document.createElement('div');
  typing.className = 'typing-indicator';
  typing.id = typingId;
  typing.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';

  chatMessages.appendChild(typing);
  scrollChatToBottom();

  return typingId;
}

/**
 * Remove typing indicator
 * @param {string} id - ID of the typing indicator to remove
 */
function removeTypingIndicator(id) {
  const typing = document.getElementById(id);
  if (typing) {
    typing.remove();
  }
}

/**
 * Append product row to chat
 * @param {Array} products - Array of product objects
 */
function appendProductRow(products) {
  const chatMessages = document.getElementById('chatMessages');
  if (!chatMessages || !products || products.length === 0) return;

  const productRow = document.createElement('div');
  productRow.className = 'chat-product-row';

  products.forEach(product => {
    const card = document.createElement('div');
    card.className = 'chat-product-card';
    
    const imageHtml = product.image_url 
      ? `<img src="${product.image_url}" alt="${product.name}" class="chat-product-image">`
      : '<div class="chat-product-image" style="background: var(--marble);"></div>';

    card.innerHTML = `
      ${imageHtml}
      <div class="chat-product-info">
        <div class="chat-product-name">${product.name}</div>
        ${product.range ? `<span class="badge-range">${product.range}</span>` : ''}
        <div class="chat-product-sku">${product.sku || ''}</div>
      </div>
    `;

    productRow.appendChild(card);
  });

  chatMessages.appendChild(productRow);
  scrollChatToBottom();
}

/**
 * Initialize chat photo upload
 */
function initChatPhotoUpload() {
  const cameraBtn = document.getElementById('chatCameraBtn');
  const photoBtn = document.getElementById('chatPhotoBtn');
  const photoInput = document.getElementById('chatPhotoInput');
  const conversationId = document.getElementById('conversationId')?.value;

  if (!photoInput || !conversationId) return;

  // Camera button click
  if (cameraBtn) {
    cameraBtn.addEventListener('click', () => {
      photoInput.setAttribute('capture', 'environment');
      photoInput.click();
    });
  }

  // Photo button click
  if (photoBtn) {
    photoBtn.addEventListener('click', () => {
      photoInput.removeAttribute('capture');
      photoInput.click();
    });
  }

  // File input change
  photoInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Read file as base64
    const reader = new FileReader();
    reader.onload = (event) => {
      const imageData = event.target.result;

      // Append user message with image
      appendChatBubble('user', '[Photo uploaded]', imageData);

      // Show typing
      const typingId = appendTypingIndicator();

      // Send to server
      const formData = new FormData();
      formData.append('photo', file);

      fetch(`/chat/${conversationId}/photo/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        removeTypingIndicator(typingId);
        appendChatBubble('assistant', data.reply);
        scrollChatToBottom();
      })
      .catch(error => {
        console.error('Error uploading photo:', error);
        removeTypingIndicator(typingId);
        appendChatBubble('assistant', 'Sorry, I couldn\'t process your image. Please try again.');
      });
    };

    reader.readAsDataURL(file);

    // Reset input
    photoInput.value = '';
  });
}

/**
 * Initialize quick prompts
 */
function initQuickPrompts() {
  const promptButtons = document.querySelectorAll('.quick-prompt-btn');
  const messageInput = document.getElementById('messageInput');

  promptButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (messageInput && prompt) {
        messageInput.value = prompt;
        sendChatMessage();

        // Hide quick prompts after selection
        document.querySelectorAll('.quick-prompts').forEach(section => {
          section.style.display = 'none';
        });
      }
    });
  });
}

/**
 * Initialize chat input behavior
 */
function initChatInput() {
  const messageInput = document.getElementById('messageInput');
  const sendBtn = document.getElementById('chatSendBtn');

  if (!messageInput) return;

  // Enter key sends (Shift+Enter for newline)
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  });

  // Auto-resize textarea
  messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = messageInput.scrollHeight + 'px';
  });

  // Send button click
  if (sendBtn) {
    sendBtn.addEventListener('click', sendChatMessage);
  }
}

/**
 * Scroll chat messages to bottom
 */
function scrollChatToBottom() {
  const chatMessages = document.getElementById('chatMessages');
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}

// ============================================
// THEME (DARK MODE) FUNCTIONS
// ============================================

/**
 * Initialize theme based on saved preference or system preference
 */
function initTheme() {
  // Key unified to lux_theme (same as base.html)
  const savedTheme = localStorage.getItem('lux_theme');
  const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
    document.documentElement.setAttribute('data-theme', 'dark');
    updateThemeIcon(true);
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    updateThemeIcon(false);
  }
}

/**
 * Toggle between light and dark theme
 */
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const isDark = currentTheme === 'dark';

  if (isDark) {
    document.documentElement.setAttribute('data-theme', 'light');
    localStorage.setItem('lux_theme', 'light');
    updateThemeIcon(false);
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('lux_theme', 'dark');
    updateThemeIcon(true);
  }
}

/**
 * Update the theme toggle button icon
 */
function updateThemeIcon(isDark) {
  const themeIcon = document.getElementById('themeIcon');
  if (themeIcon) {
    themeIcon.className = isDark ? 'bi bi-sun' : 'bi bi-moon-stars';
  }
}

// ============================================
// VIEW TOGGLE (MOBILE/DESKTOP) FUNCTIONS
// ============================================

/**
 * Initialize view mode based on saved preference
 */
function initViewMode() {
  const savedView = localStorage.getItem('lumina-view');
  const viewButtons = document.querySelectorAll('.view-toggle-btn');
  
  if (savedView) {
    switchView(savedView);
  }
}

/**
 * Switch between mobile and desktop view
 * @param {string} view - 'mobile' or 'desktop'
 */
function switchView(view) {
  // Update button states
  const viewButtons = document.querySelectorAll('.view-toggle-btn');
  viewButtons.forEach(btn => {
    btn.classList.remove('active');
    if (btn.getAttribute('data-view') === view) {
      btn.classList.add('active');
    }
  });
  
  // Update body class for view-specific styling
  document.body.classList.remove('view-mobile', 'view-desktop');
  document.body.classList.add(`view-${view}`);
  
  // Save preference
  localStorage.setItem('lumina-view', view);
}

// ============================================
// INITIALIZATION
// ============================================

/**
 * Initialize all functions on DOM ready
 */
document.addEventListener('DOMContentLoaded', () => {
  // Theme initialization
  initTheme();
  
  // View mode initialization
  initViewMode();
  
  // Theme toggle button
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }

  // View toggle buttons
  const viewButtons = document.querySelectorAll('.view-toggle-btn');
  viewButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const view = btn.getAttribute('data-view');
      switchView(view);
    });
  });
  
  // Navigation
  initNavToggle();
  initMainTabs();

  // Scanner
  const scannerToggles = document.querySelectorAll('.scanner-toggle-btn');
  scannerToggles.forEach(btn => {
    btn.addEventListener('click', () => {
      const type = btn.getAttribute('data-scanner-type');
      switchScanner(type);
    });
  });

  // Tabs
  initScrollTabBar();
  initProgressBars();

  const tabButtons = document.querySelectorAll('[data-tab]');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  const subTabButtons = document.querySelectorAll('[data-subtab]');
  subTabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const subTabId = btn.getAttribute('data-subtab');
      switchSubTab(subTabId);
    });
  });

  // Chat
  initChatInput();
  initChatPhotoUpload();
  initQuickPrompts();

  // Check URL parameters
  const urlParams = new URLSearchParams(window.location.search);

  // Demo mode
  if (urlParams.get('demo') === 'true') {
    showScanState('demo');
  }

  // Initial tab
  const initialTab = urlParams.get('tab');
  if (initialTab) {
    switchTab(initialTab);
  }

  // Check for Django messages about face detection
  const messages = document.querySelectorAll('.alert-lumina');
  messages.forEach(msg => {
    if (msg.textContent.includes('No face detected')) {
      showScanState('no-face');
    }
  });

  // Scroll to bottom of chat on load
  if (document.getElementById('chatMessages')) {
    scrollChatToBottom();
  }

  // Listen for system theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
    if (!localStorage.getItem('lux_theme')) {
      if (e.matches) {
        document.documentElement.setAttribute('data-theme', 'dark');
        updateThemeIcon(true);
      } else {
        document.documentElement.setAttribute('data-theme', 'light');
        updateThemeIcon(false);
      }
    }
  });

  console.log('✨ Lumina initialized successfully');
});
