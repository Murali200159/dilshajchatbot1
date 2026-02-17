
document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const chatToggleBtn = document.getElementById('chat-toggle-btn');
    const chatWindow = document.getElementById('chat-window');
    const chatMessages = document.querySelector('.chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const refreshChatBtn = document.getElementById('refresh-chat-btn');
    const minimizeChatBtn = document.getElementById('minimize-chat-btn');
    const quickRepliesContainer = document.getElementById('quick-replies');

    // --- State ---
    let isOpen = false;
    // Initial state matching the hardcoded assistant message in HTML
    const INITIAL_MESSAGE = { role: 'assistant', content: "Hi! I'm the Dilshaj Infotech AI Assistant. How can I help you today?" };
    let messages = [INITIAL_MESSAGE];

    const SUGGESTED_QUESTIONS = [
        { text: "About Company", type: "primary" },
        { text: "Our Services", type: "outline" },
        { text: "Placement Policy", type: "outline" },
        { text: "Contact Info", type: "outline" }
    ];

    const API_URL = '/api/v1/chatbot/chat/stream';

    // --- Event Listeners ---
    chatToggleBtn.addEventListener('click', toggleChat);
    minimizeChatBtn.addEventListener('click', toggleChat);
    refreshChatBtn.addEventListener('click', refreshChat);

    sendBtn.addEventListener('click', () => sendMessage());

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });

    // Make toggle button appear smoothly
    setTimeout(() => {
        chatToggleBtn.style.opacity = '1';
        chatToggleBtn.style.transform = 'scale(1)';
    }, 500);

    // --- Functions ---

    function renderQuickReplies() {
        if (!quickRepliesContainer) return;
        quickRepliesContainer.innerHTML = '';
        SUGGESTED_QUESTIONS.forEach(q => {
            const btn = document.createElement('button');
            btn.innerText = q.text;
            btn.className = `quick-reply-pill ${q.type}`;
            btn.onclick = () => sendMessage(q.text);
            quickRepliesContainer.appendChild(btn);
        });
    }

    function getFormattedDate() {
        const options = { weekday: 'long', month: 'short', day: 'numeric' };
        return new Date().toLocaleDateString('en-US', options);
    }

    function addDateSeparatorToUI() {
        const dateDiv = document.createElement('div');
        dateDiv.classList.add('date-separator');
        dateDiv.innerText = getFormattedDate();
        chatMessages.appendChild(dateDiv);
    }

    async function refreshChat() {
        // Clear backend state
        try {
            await fetch('/api/v1/chatbot/messages', { method: 'DELETE' });
        } catch (e) {
            console.error("Failed to clear backend history", e);
        }

        // Clear local state
        messages = [INITIAL_MESSAGE];
        // Clear UI and rebuild
        chatMessages.innerHTML = '';
        addDateSeparatorToUI();
        addMessageToUI(INITIAL_MESSAGE.content, 'assistant');
        renderQuickReplies();
    }

    // Initialize UI on load
    loadChatHistory();

    async function loadChatHistory() {
        try {
            const response = await fetch('/api/v1/chatbot/messages');
            if (response.ok) {
                const data = await response.json();

                // Reset state
                messages = [INITIAL_MESSAGE];

                // Clear UI
                chatMessages.innerHTML = '';
                addDateSeparatorToUI();
                addMessageToUI(INITIAL_MESSAGE.content, 'assistant');

                if (data.messages && Array.isArray(data.messages)) {
                    data.messages.forEach(msg => {
                        // Only show user and assistant messages with content
                        if ((msg.role === 'user' || msg.role === 'assistant') && msg.content) {
                            messages.push(msg);
                            addMessageToUI(msg.content, msg.role);
                        }
                    });
                }
            } else {
                initDefaultChat();
            }
        } catch (error) {
            console.error("Failed to load history:", error);
            initDefaultChat();
        }
        renderQuickReplies();
        // Scroll to bottom after loading
        setTimeout(scrollToBottom, 100);
    }

    function initDefaultChat() {
        messages = [INITIAL_MESSAGE];
        chatMessages.innerHTML = '';
        addDateSeparatorToUI();
        addMessageToUI(INITIAL_MESSAGE.content, 'assistant');
    }

    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            chatWindow.classList.remove('hidden');
            chatToggleBtn.style.transform = 'scale(0)';
            setTimeout(() => {
                chatToggleBtn.style.display = 'none';
            }, 300);
            userInput.focus();
        } else {
            chatWindow.classList.add('hidden');
            setTimeout(() => {
                chatToggleBtn.style.display = 'flex';
                // Trigger reflow
                void chatToggleBtn.offsetWidth;
                chatToggleBtn.style.transform = 'scale(1)';
            }, 300);
        }
    }

    async function sendMessage(customText = null) {
        const text = customText || userInput.value.trim();
        if (!text) return;

        // 1. Add User Message to UI and State
        addMessageToUI(text, 'user');

        userInput.value = '';
        userInput.disabled = true;

        // 2. Add Loading Indicator
        const loadingEl = addLoadingIndicator();

        try {
            // 3. Prepare Payload
            const payload = {
                messages: [{
                    role: 'user',
                    content: text
                }]
            };

            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            // Remove loading indicator immediately as we start streaming
            removeLoadingIndicator(loadingEl);

            // 4. Handle Streaming Response
            // Create a placeholder message for the assistant
            const messageTextDiv = addMessageToUI('', 'assistant');
            let fullText = "";

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            try {
                // Streaming Loop
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop() || ''; // Keep incomplete part

                    for (const line of lines) {
                        const trimmed = line.trim();
                        if (trimmed.startsWith('data: ')) {
                            try {
                                const jsonStr = trimmed.slice(6);
                                const data = JSON.parse(jsonStr);

                                if (data.content) {
                                    fullText += data.content;
                                    // Use innerText to avoid XSS but allow consistent updates
                                    messageTextDiv.innerText = fullText;
                                    scrollToBottom();
                                }
                            } catch (e) {
                                console.warn("Failed to parse SSE data", e);
                            }
                        }
                    }
                }
            } catch (streamError) {
                console.error("Stream reading error", streamError);
            }

            // 5. Update State
            messages.push({ role: 'assistant', content: fullText });

        } catch (error) {
            console.error(error);
            removeLoadingIndicator(loadingEl);
            addMessageToUI("Sorry, I'm having trouble connecting right now.", 'assistant');
        } finally {
            userInput.disabled = false;
            userInput.focus();
        }
    }

    function getCurrentTime() {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function addMessageToUI(text, role) {
        const row = document.createElement('div');
        row.classList.add('message-row', role);

        if (role === 'assistant') {
            const avatar = document.createElement('div');
            avatar.classList.add('message-avatar');
            avatar.innerHTML = '<i class="fas fa-robot"></i>';
            row.appendChild(avatar);
        }

        const messageBubble = document.createElement('div');
        messageBubble.classList.add('message', role);

        const textDiv = document.createElement('div');
        textDiv.classList.add('message-text');
        textDiv.innerText = text;

        const timeDiv = document.createElement('div');
        timeDiv.classList.add('message-time');
        timeDiv.innerText = getCurrentTime();

        messageBubble.appendChild(textDiv);
        messageBubble.appendChild(timeDiv);

        row.appendChild(messageBubble);
        chatMessages.appendChild(row);
        scrollToBottom();

        return textDiv; // Returns the text container for updates
    }

    function addLoadingIndicator() {
        const id = 'loading-' + Date.now();
        const row = document.createElement('div');
        row.id = id;
        row.classList.add('message-row', 'assistant');

        const avatar = document.createElement('div');
        avatar.classList.add('message-avatar');
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        row.appendChild(avatar);

        const div = document.createElement('div');
        div.classList.add('typing-indicator');
        div.innerHTML = `
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        `;

        row.appendChild(div);

        chatMessages.appendChild(row);
        scrollToBottom();
        return row;
    }

    function removeLoadingIndicator(wrapperElement) {
        if (wrapperElement && wrapperElement.parentNode) {
            wrapperElement.remove();
        } else if (typeof wrapperElement === 'string') {
            // Fallback if id was passed
            const el = document.getElementById(wrapperElement);
            if (el) el.remove();
        }
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
