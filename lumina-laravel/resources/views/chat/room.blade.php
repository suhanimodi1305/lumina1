@extends('layouts.app')
@section('title', $conversation->title)

@push('styles')
<style>
.chat-wrapper { height: calc(100vh - 140px); display:flex; flex-direction:column; }
.chat-messages { flex:1; overflow-y:auto; padding:1.5rem; scroll-behavior:smooth; }
.chat-input-area { border-top:1px solid rgba(0,0,0,.08); padding:1rem 1.5rem; background:#fff; }
.msg-bubble { max-width:75%; }
.msg-user .msg-bubble { background:var(--lumina-primary); color:#fff; border-radius:18px 18px 4px 18px; }
.msg-assistant .msg-bubble { background:#f0f2f5; border-radius:18px 18px 18px 4px; }
.typing-indicator span { display:inline-block; width:8px;height:8px;border-radius:50%;background:#adb5bd;animation:typingBounce .8s infinite; }
.typing-indicator span:nth-child(2){animation-delay:.15s;}
.typing-indicator span:nth-child(3){animation-delay:.3s;}
@keyframes typingBounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-8px)}}
.mode-tab.active { background:var(--lumina-primary); color:#fff; }
.product-card-mini { border:1px solid rgba(0,0,0,.1); border-radius:12px; padding:.75rem; display:flex; gap:.75rem; align-items:center; transition:.2s; }
.product-card-mini:hover { border-color:var(--lumina-primary); box-shadow:0 2px 12px rgba(var(--lumina-primary-rgb),.15); }
</style>
@endpush

@section('content')
<div class="container-fluid px-0">
<div class="row g-0" style="height:calc(100vh - 70px)">

    {{-- Sidebar: quick prompts --}}
    <div class="col-md-3 col-lg-2 border-end bg-white d-none d-md-flex flex-column p-3" style="overflow-y:auto;">
        <h6 class="text-muted fw-semibold mb-3 text-uppercase small">Quick Prompts</h6>
        @foreach($modePrompts as $prompt)
        <button class="btn btn-sm btn-light text-start mb-2 quick-prompt-btn" data-prompt="{{ $prompt }}">
            {{ $prompt }}
        </button>
        @endforeach

        <hr class="my-3">
        <a href="{{ route('chat.index') }}" class="btn btn-sm btn-outline-secondary">
            <i class="bi bi-arrow-left me-1"></i>All Chats
        </a>
        <form method="POST" action="{{ route('chat.destroy', $conversation) }}" class="mt-2"
              onsubmit="return confirm('Delete this conversation?')">
            @csrf @method('DELETE')
            <button class="btn btn-sm btn-outline-danger w-100">
                <i class="bi bi-trash me-1"></i>Delete
            </button>
        </form>
    </div>

    {{-- Main chat --}}
    <div class="col-md-9 col-lg-10 d-flex flex-column bg-white" style="height:calc(100vh - 70px);">

        {{-- Chat header --}}
        <div class="border-bottom px-4 py-3 d-flex justify-content-between align-items-center">
            <div>
                <h6 class="mb-0 fw-semibold">{{ $conversation->title }}</h6>
                @if($conversation->scanResult)
                <small class="text-muted">🔬 Linked to Scan #{{ $conversation->scanResult->id }}</small>
                @endif
            </div>
            {{-- Mode tabs --}}
            <div class="d-flex gap-2">
                @foreach(['doctor'=>['emoji'=>'👩‍⚕️','label'=>'Doctor'],'makeup'=>['emoji'=>'💄','label'=>'Makeup'],'kbeauty'=>['emoji'=>'🌸','label'=>'K-Beauty']] as $mode=>$info)
                <button class="btn btn-sm mode-tab {{ $conversation->mode===$mode?'active':'btn-outline-secondary' }}"
                        data-mode="{{ $mode }}">
                    {{ $info['emoji'] }} {{ $info['label'] }}
                </button>
                @endforeach
            </div>
        </div>

        {{-- Messages --}}
        <div class="chat-messages" id="chat-messages">
            @forelse($messages as $msg)
            <div class="d-flex mb-3 {{ $msg->role==='user'?'justify-content-end msg-user':'justify-content-start msg-assistant' }}">
                @if($msg->role==='assistant')
                <div class="avatar-xs bg-lumina-primary text-white rounded-circle d-flex align-items-center justify-content-center me-2 flex-shrink-0" style="width:32px;height:32px;font-size:.75rem">✨</div>
                @endif
                <div>
                    @if($msg->image_data)
                    <div class="msg-bubble p-0 overflow-hidden mb-1">
                        <img src="data:image/jpeg;base64,{{ $msg->image_data }}" style="max-width:200px;border-radius:12px;" alt="Photo">
                    </div>
                    @endif
                    <div class="msg-bubble p-3 fs-sm">{!! nl2br(e($msg->content)) !!}</div>
                    <div class="text-muted" style="font-size:.7rem;margin-top:2px;">{{ $msg->created_at->format('h:i A') }}</div>
                </div>
            </div>
            @empty
            <div class="text-center text-muted py-5">
                <div class="fs-1 mb-2">{{ $conversation->mode==='doctor'?'👩‍⚕️':($conversation->mode==='makeup'?'💄':'🌸') }}</div>
                <p>Start a conversation below</p>
            </div>
            @endforelse

            {{-- Typing indicator (hidden) --}}
            <div id="typing-indicator" class="d-flex mb-3 justify-content-start d-none">
                <div class="avatar-xs bg-lumina-primary text-white rounded-circle d-flex align-items-center justify-content-center me-2 flex-shrink-0" style="width:32px;height:32px;font-size:.75rem">✨</div>
                <div class="msg-bubble p-3">
                    <div class="typing-indicator"><span></span><span></span><span></span></div>
                </div>
            </div>
        </div>

        {{-- Product suggestions area --}}
        <div id="product-suggestions" class="px-4 pb-2 d-none">
            <p class="text-muted small mb-2">🛍️ Suggested products:</p>
            <div class="d-flex gap-3 overflow-x-auto pb-2" id="product-list"></div>
        </div>

        {{-- Input --}}
        <div class="chat-input-area">
            <form id="message-form" class="d-flex gap-2 align-items-end">
                @csrf
                <div class="flex-grow-1">
                    <textarea id="message-input" class="form-control border-0 bg-light rounded-3"
                              rows="1" placeholder="Ask Dr. Lumina anything about your skin..."
                              style="resize:none;max-height:120px;overflow-y:auto;"></textarea>
                </div>
                <label class="btn btn-outline-secondary btn-sm p-2" style="cursor:pointer;" title="Upload photo">
                    <i class="bi bi-image fs-5"></i>
                    <input type="file" id="photo-input" accept="image/jpeg,image/png,image/webp" class="d-none">
                </label>
                <button type="submit" class="btn btn-lumina px-3" id="send-btn" style="height:42px;">
                    <i class="bi bi-send-fill"></i>
                </button>
            </form>
        </div>
    </div>
</div>
</div>
@endsection

@push('scripts')
<script>
const conversationId = '{{ $conversation->id }}';
const csrfToken = document.querySelector('meta[name=csrf-token]').content;
const messagesEl = document.getElementById('chat-messages');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const typingIndicator = document.getElementById('typing-indicator');

// Scroll to bottom
function scrollBottom() { messagesEl.scrollTop = messagesEl.scrollHeight; }
scrollBottom();

// Auto-grow textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Send on Enter (Shift+Enter for newline)
messageInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); document.getElementById('message-form').requestSubmit(); }
});

// Quick prompt buttons
document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
    btn.addEventListener('click', () => { messageInput.value = btn.dataset.prompt; messageInput.focus(); });
});

// Send message
document.getElementById('message-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    const text = messageInput.value.trim();
    if (!text) return;

    appendMessage('user', text, new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}));
    messageInput.value = ''; messageInput.style.height = 'auto';
    showTyping(true); sendBtn.disabled = true;

    try {
        const res = await fetch(`/chat/${conversationId}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrfToken },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        showTyping(false); sendBtn.disabled = false;

        if (data.error) { appendMessage('assistant', '⚠️ ' + data.error, ''); return; }

        appendMessage('assistant', data.reply, data.timestamp);
        if (data.product_suggestions?.length) showProducts(data.product_suggestions);
    } catch {
        showTyping(false); sendBtn.disabled = false;
        appendMessage('assistant', '⚠️ Connection error. Please try again.', '');
    }
});

// Photo upload
document.getElementById('photo-input').addEventListener('change', async function() {
    const file = this.files[0]; if (!file) return;
    const fd = new FormData(); fd.append('photo', file);

    appendMessage('user', '[📷 Photo uploaded]', '');
    showTyping(true); sendBtn.disabled = true;

    try {
        const res = await fetch(`/chat/${conversationId}/photo`, {
            method:'POST', headers:{'X-CSRF-TOKEN':csrfToken}, body:fd
        });
        const data = await res.json();
        showTyping(false); sendBtn.disabled = false;
        if (data.error) { appendMessage('assistant','⚠️ '+data.error,''); return; }
        appendMessage('assistant', data.reply, data.timestamp);
    } catch { showTyping(false); sendBtn.disabled = false; }
    this.value = '';
});

// Mode switch
document.querySelectorAll('.mode-tab').forEach(btn => {
    btn.addEventListener('click', async function() {
        const mode = this.dataset.mode;
        await fetch(`/chat/${conversationId}/mode`, {
            method:'POST', headers:{'Content-Type':'application/json','X-CSRF-TOKEN':csrfToken},
            body:JSON.stringify({mode})
        });
        document.querySelectorAll('.mode-tab').forEach(b => b.classList.remove('active','btn-outline-secondary'));
        this.classList.add('active');
    });
});

function appendMessage(role, content, time) {
    const isUser = role === 'user';
    const div = document.createElement('div');
    div.className = `d-flex mb-3 ${isUser?'justify-content-end msg-user':'justify-content-start msg-assistant'}`;
    div.innerHTML = `
        ${!isUser?`<div class="avatar-xs bg-lumina-primary text-white rounded-circle d-flex align-items-center justify-content-center me-2 flex-shrink-0" style="width:32px;height:32px;font-size:.75rem">✨</div>`:''}
        <div>
            <div class="msg-bubble p-3">${content.replace(/\n/g,'<br>')}</div>
            ${time?`<div class="text-muted" style="font-size:.7rem;margin-top:2px;">${time}</div>`:''}
        </div>`;
    typingIndicator.before(div);
    scrollBottom();
}

function showTyping(show) {
    typingIndicator.classList.toggle('d-none', !show);
    scrollBottom();
}

function showProducts(products) {
    const container = document.getElementById('product-list');
    const area = document.getElementById('product-suggestions');
    container.innerHTML = '';
    products.forEach(p => {
        container.innerHTML += `
        <div class="product-card-mini flex-shrink-0" style="min-width:200px;max-width:220px;">
            ${p.image_url?`<img src="${p.image_url}" style="width:48px;height:48px;object-fit:cover;border-radius:8px;" alt="">`:'<div style="width:48px;height:48px;background:#f0f2f5;border-radius:8px;"></div>'}
            <div class="flex-grow-1 overflow-hidden">
                <div class="fw-semibold small text-truncate">${p.name}</div>
                <div class="text-muted" style="font-size:.72rem;">${p.brand??''}</div>
                <div class="text-lumina-primary fw-bold small">${p.price??''}</div>
            </div>
        </div>`;
    });
    area.classList.remove('d-none');
}
</script>
@endpush
