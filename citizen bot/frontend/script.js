/**
 * Municipal Service Assistant - Frontend Controller
 * Handles user input, multi-turn session persistence, API communication,
 * markdown parsing for civic messages, and clear conversation triggers.
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const messagesContainer = document.getElementById('messages-container');
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const clearBtn = document.getElementById('clear-chat-btn');
  const typingIndicator = document.getElementById('typing-indicator');
  const welcomeCard = document.getElementById('welcome-card');

  // Initialize or restore session ID
  let sessionId = sessionStorage.getItem('municipal_session_id');
  if (!sessionId) {
    sessionId = 'session_' + Math.random().toString(36).substring(2, 10);
    sessionStorage.setItem('municipal_session_id', sessionId);
  }

  // Keep track of pending retry query if needed
  let lastFailedQuery = null;

  // ---------------------------------------------------------------------------
  // Input Handling & Textarea Sizing
  // ---------------------------------------------------------------------------
  userInput.addEventListener('input', () => {
    // Auto-grow textarea
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';

    // Enable/disable send button
    sendBtn.disabled = userInput.value.trim().length === 0;
  });

  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) {
        chatForm.dispatchEvent(new Event('submit'));
      }
    }
  });

  // ---------------------------------------------------------------------------
  // Suggestion Chips
  // ---------------------------------------------------------------------------
  document.querySelectorAll('.suggestion-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const query = chip.getAttribute('data-query');
      if (query) {
        userInput.value = query;
        userInput.dispatchEvent(new Event('input'));
        chatForm.dispatchEvent(new Event('submit'));
      }
    });
  });

  // ---------------------------------------------------------------------------
  // Form Submission & API Request
  // ---------------------------------------------------------------------------
  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = userInput.value.trim();
    if (!query) return;

    // Reset input field
    userInput.value = '';
    userInput.style.height = 'auto';
    sendBtn.disabled = true;

    // Hide welcome card on first message
    if (welcomeCard && !welcomeCard.classList.contains('hidden')) {
      welcomeCard.style.display = 'none';
    }

    // Append citizen message to UI
    appendMessage({
      role: 'user',
      content: query,
      timestamp: new Date(),
    });

    // Show loading state
    showTypingIndicator(true);
    scrollToBottom();

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: query,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }

      const data = await response.json();
      showTypingIndicator(false);

      // Append assistant response to UI
      appendMessage({
        role: 'assistant',
        content: data.response,
        sourceMetadata: data.source_metadata,
        timestamp: new Date(),
      });
      lastFailedQuery = null;

    } catch (error) {
      console.error('Chat error:', error);
      showTypingIndicator(false);
      lastFailedQuery = query;

      appendErrorMessage(
        "I'm sorry, I couldn't process your request right now. Please check your connection or try again.",
        query
      );
    }

    scrollToBottom();
  });

  // ---------------------------------------------------------------------------
  // Clear Conversation
  // ---------------------------------------------------------------------------
  clearBtn.addEventListener('click', async () => {
    try {
      await fetch(`/clear?session_id=${encodeURIComponent(sessionId)}`, {
        method: 'POST',
      });
    } catch (err) {
      console.warn('Could not clear backend session:', err);
    }

    // Generate fresh session ID
    sessionId = 'session_' + Math.random().toString(36).substring(2, 10);
    sessionStorage.setItem('municipal_session_id', sessionId);

    // Reset UI
    messagesContainer.innerHTML = '';
    if (welcomeCard) {
      welcomeCard.style.display = 'block';
      messagesContainer.appendChild(welcomeCard);
    }
    userInput.value = '';
    userInput.style.height = 'auto';
    sendBtn.disabled = true;
    showTypingIndicator(false);
  });

  // ---------------------------------------------------------------------------
  // DOM Message Rendering
  // ---------------------------------------------------------------------------
  function appendMessage({ role, content, sourceMetadata, timestamp }) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = role === 'user' ? '👤' : '🏛️';

    const wrapper = document.createElement('div');
    wrapper.className = 'message-content-wrapper';

    // Header
    const header = document.createElement('div');
    header.className = 'message-header';

    const author = document.createElement('span');
    author.className = 'message-author';
    author.textContent = role === 'user' ? 'Citizen' : 'Municipal Assistant';

    const time = document.createElement('span');
    time.className = 'message-time';
    time.textContent = formatTime(timestamp);

    header.appendChild(author);
    header.appendChild(time);
    wrapper.appendChild(header);

    // Bubble
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = formatMarkdown(content);
    wrapper.appendChild(bubble);

    // Source Transparency Provenance
    if (role === 'assistant' && sourceMetadata && sourceMetadata.source) {
      const sourceBox = document.createElement('div');
      sourceBox.className = 'source-provenance';
      sourceBox.innerHTML = `
        <span>Source:</span>
        <span class="source-badge">
          <span>🏛️</span>
          <span>${escapeHtml(sourceMetadata.source)}</span>
        </span>
        ${sourceMetadata.last_updated ? `<span>• Currency: ${escapeHtml(sourceMetadata.last_updated)}</span>` : ''}
      `;
      wrapper.appendChild(sourceBox);
    }

    if (role === 'user') {
      row.appendChild(wrapper);
      row.appendChild(avatar);
    } else {
      row.appendChild(avatar);
      row.appendChild(wrapper);
    }

    messagesContainer.appendChild(row);
  }

  function appendErrorMessage(errorText, retryQuery) {
    const row = document.createElement('div');
    row.className = 'message-row assistant';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '⚠️';

    const wrapper = document.createElement('div');
    wrapper.className = 'message-content-wrapper';

    const header = document.createElement('div');
    header.className = 'message-header';
    header.innerHTML = `<span class="message-author" style="color: #ef4444;">System Notice</span>`;
    wrapper.appendChild(header);

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.style.borderColor = '#fca5a5';
    bubble.style.backgroundColor = '#fef2f2';

    bubble.innerHTML = `
      <p style="color: #991b1b;">${escapeHtml(errorText)}</p>
      ${retryQuery ? `
        <button id="retry-btn" class="btn-secondary" style="margin-top: 0.5rem; background: #fee2e2; color: #991b1b; border-color: #fca5a5;">
          <span>↻</span> Try Again
        </button>
      ` : ''}
    `;

    wrapper.appendChild(bubble);
    row.appendChild(avatar);
    row.appendChild(wrapper);
    messagesContainer.appendChild(row);

    const retryBtn = bubble.querySelector('#retry-btn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        row.remove();
        userInput.value = retryQuery;
        userInput.dispatchEvent(new Event('input'));
        chatForm.dispatchEvent(new Event('submit'));
      });
    }
  }

  function showTypingIndicator(show) {
    if (show) {
      typingIndicator.classList.remove('hidden');
    } else {
      typingIndicator.classList.add('hidden');
    }
  }

  function scrollToBottom() {
    const viewport = document.querySelector('.chat-viewport');
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  }

  function formatTime(date) {
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Basic Markdown formatting for bullet points, bold text, and paragraphs
  function formatMarkdown(text) {
    if (!text) return '';

    let formatted = escapeHtml(text);

    // Bold: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Split lines
    const lines = formatted.split('\n');
    let html = '';
    let inList = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      if (line.startsWith('• ') || line.startsWith('- ') || line.startsWith('* ')) {
        if (!inList) {
          html += '<ul>';
          inList = true;
        }
        const itemContent = line.substring(2).trim();
        html += `<li>${itemContent}</li>`;
      } else {
        if (inList) {
          html += '</ul>';
          inList = false;
        }
        if (line.length > 0) {
          html += `<p>${line}</p>`;
        }
      }
    }

    if (inList) {
      html += '</ul>';
    }

    return html;
  }
});
