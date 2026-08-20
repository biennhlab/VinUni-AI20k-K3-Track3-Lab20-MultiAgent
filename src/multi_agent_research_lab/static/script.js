document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const queryInput = document.getElementById('query-input');
    const chatMessages = document.getElementById('chat-messages');
    const emptyState = document.getElementById('empty-state');
    const sendBtn = document.getElementById('send-btn');
    
    const agentFlowContainer = document.getElementById('agent-flow-container');
    const toggleFlowBtn = document.getElementById('toggle-flow-btn');
    const agentTimeline = document.getElementById('agent-timeline');
    
    // Configure Marked
    marked.setOptions({
        highlight: function(code, lang) {
            if (lang && hljs.getLanguage(lang)) {
                return hljs.highlight(code, { language: lang }).value;
            }
            return hljs.highlightAuto(code).value;
        },
        breaks: true
    });

    // Auto-resize textarea
    queryInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if(this.value.trim() === '') {
            sendBtn.disabled = true;
        } else {
            sendBtn.disabled = false;
        }
    });

    // Handle Enter to submit (Shift+Enter for new line)
    queryInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if(this.value.trim() !== '') {
                chatForm.dispatchEvent(new Event('submit'));
            }
        }
    });

    // Toggle flow timeline
    toggleFlowBtn.addEventListener('click', () => {
        agentFlowContainer.classList.toggle('collapsed');
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;

        // Hide empty state
        if (emptyState) emptyState.style.display = 'none';

        // Add user message
        appendMessage('user', query);
        
        // Reset and prepare UI
        queryInput.value = '';
        queryInput.style.height = 'auto';
        sendBtn.disabled = true;
        
        // Show Agent Timeline
        agentFlowContainer.style.display = 'block';
        agentFlowContainer.classList.remove('collapsed');
        agentTimeline.innerHTML = '';
        
        // Add loading indicator for Assistant
        const loadingId = 'loading-' + Date.now();
        appendLoading(loadingId);
        
        // Call API using Fetch and EventSource (or reading stream)
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let done = false;

            // Simple parser for SSE format "data: {json}\n\n"
            let buffer = "";

            while (!done) {
                const { value, done: readerDone } = await reader.read();
                done = readerDone;
                if (value) {
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n\n');
                    buffer = lines.pop(); // keep the incomplete part

                    for (const chunk of lines) {
                        if (chunk.startsWith('data: ')) {
                            const dataStr = chunk.substring(6).trim();
                            if (dataStr === '[DONE]') {
                                removeLoading(loadingId);
                                setTimeout(() => {
                                    agentFlowContainer.classList.add('collapsed');
                                }, 3000);
                                break;
                            }
                            
                            try {
                                const data = JSON.parse(dataStr);
                                
                                if (data.error) {
                                    removeLoading(loadingId);
                                    appendMessage('assistant', `**Error:** ${data.error}`);
                                    addTimelineItem('Error', 'Failed', 'failed', 'X');
                                } else if (data.type === 'final_answer') {
                                    removeLoading(loadingId);
                                    appendMessage('assistant', data.content);
                                } else {
                                    // Agent step
                                    addTimelineItem(data.agent, data.status, 'completed', '✓');
                                }
                            } catch (e) {
                                console.error('Error parsing JSON:', e, dataStr);
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error('Error:', error);
            removeLoading(loadingId);
            appendMessage('assistant', '**Error connecting to the AI Lab.** Please make sure the backend is running.');
        } finally {
            sendBtn.disabled = false;
        }
    });

    function appendMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        
        if (role === 'user') {
            bubbleDiv.textContent = content;
        } else {
            bubbleDiv.innerHTML = marked.parse(content);
            // Add copy buttons to code blocks
            bubbleDiv.querySelectorAll('pre').forEach(pre => {
                const btn = document.createElement('button');
                btn.className = 'copy-btn';
                btn.textContent = 'Copy';
                btn.onclick = () => {
                    const code = pre.querySelector('code').innerText;
                    navigator.clipboard.writeText(code);
                    btn.textContent = 'Copied!';
                    setTimeout(() => btn.textContent = 'Copy', 2000);
                };
                pre.appendChild(btn);
            });
        }
        
        msgDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }
    
    function appendLoading(id) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message assistant`;
        msgDiv.id = id;
        
        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'message-bubble';
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        bubbleDiv.appendChild(indicator);
        msgDiv.appendChild(bubbleDiv);
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }
    
    function removeLoading(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }
    
    function addTimelineItem(agent, status, statusClass, iconText) {
        // Only append if it's not the same agent back to back (optional smoothing)
        const items = agentTimeline.querySelectorAll('.timeline-item');
        if (items.length > 0) {
            const lastItem = items[items.length - 1];
            // Add a line between items
            if (!lastItem.nextElementSibling || !lastItem.nextElementSibling.classList.contains('timeline-line')) {
                const line = document.createElement('div');
                line.className = 'timeline-line';
                agentTimeline.appendChild(line);
            }
        }
        
        const item = document.createElement('div');
        item.className = 'timeline-item';
        
        item.innerHTML = `
            <div class="status-dot ${statusClass}">${iconText}</div>
            <div>
                <div class="agent-name">${agent}</div>
                <div class="agent-status">${status}</div>
            </div>
        `;
        
        agentTimeline.appendChild(item);
        
        // Auto scroll timeline
        agentTimeline.scrollTop = agentTimeline.scrollHeight;
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
