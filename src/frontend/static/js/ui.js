/**
 * UI Handler Module
 * 
 * Manages user interface interactions and state.
 */

class UIHandler {
    constructor() {
        // Store DOM elements
        this.elements = {
            apiKeys: {
                tavilyKey: document.getElementById('tavily-key'),
                hfToken: document.getElementById('hf-token')
            },
            taskInput: {
                url: document.getElementById('url'),
                instructions: document.getElementById('instructions'),
                startButton: document.getElementById('start-task')
            },
            dialogue: {
                container: document.getElementById('dialogue-box'),
                messages: document.getElementById('dialogue-messages'),
                input: document.getElementById('user-message'),
                sendButton: document.getElementById('send-message')
            },
            contentTable: {
                container: document.getElementById('content-table'),
                editButton: document.getElementById('edit-content'),
                saveButton: document.getElementById('save-content')
            }
        };
        
        // Initialize state
        this.state = {
            taskId: null,
            isProcessing: false,
            selectedCells: new Set()
        };
        
        // Bind event handlers
        this._bindEvents();
        
        // Register WebSocket message handlers
        this._setupWebSocketHandlers();
    }
    
    /**
     * Bind UI event handlers
     */
    _bindEvents() {
        // API key handling
        this.elements.apiKeys.tavilyKey.addEventListener('change', () => {
            localStorage.setItem('tavily_key', this.elements.apiKeys.tavilyKey.value);
        });
        
        this.elements.apiKeys.hfToken.addEventListener('change', () => {
            localStorage.setItem('hf_token', this.elements.apiKeys.hfToken.value);
        });
        
        // Task input handling
        this.elements.taskInput.startButton.addEventListener('click', () => {
            this._startTask();
        });
        
        // Dialogue handling
        this.elements.dialogue.input.addEventListener('keypress', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                this._sendMessage();
            }
        });
        
        this.elements.dialogue.sendButton.addEventListener('click', () => {
            this._sendMessage();
        });
        
        // Content table handling
        this.elements.contentTable.editButton.addEventListener('click', () => {
            this._editSelectedCells();
        });
        
        this.elements.contentTable.saveButton.addEventListener('click', () => {
            this._saveContent();
        });
        
        // Load saved API keys
        this._loadSavedApiKeys();
    }
    
    /**
     * Set up WebSocket message handlers
     */
    _setupWebSocketHandlers() {
        wsHandler.onMessage('task_started', (data) => {
            this.state.taskId = data.task_id;
            this.state.isProcessing = true;
            this._showDialogue();
            this._updateUIState();
        });
        
        wsHandler.onMessage('agent_message', (data) => {
            this._addMessage('agent', data.message);
        });
        
        wsHandler.onMessage('content_update', (data) => {
            this._updateContentTable(data.content);
        });
        
        wsHandler.onMessage('task_completed', () => {
            this.state.isProcessing = false;
            this._updateUIState();
        });
        
        wsHandler.onMessage('error', (data) => {
            this._showError(data.message);
        });
    }
    
    /**
     * Start a new content retrieval task
     */
    _startTask() {
        const url = this.elements.taskInput.url.value.trim();
        const instructions = this.elements.taskInput.instructions.value.trim();
        
        if (!url || !instructions) {
            this._showError('Please provide both URL and instructions');
            return;
        }
        
        if (!this._validateApiKeys()) {
            this._showError('Please provide API keys');
            return;
        }
        
        wsHandler.sendMessage('start_task', {
            url,
            instructions,
            api_keys: {
                tavily_key: this.elements.apiKeys.tavilyKey.value,
                hf_token: this.elements.apiKeys.hfToken.value
            }
        });
    }
    
    /**
     * Send a user message
     */
    _sendMessage() {
        const message = this.elements.dialogue.input.value.trim();
        if (!message) return;
        
        this._addMessage('user', message);
        wsHandler.sendMessage('user_message', { message });
        
        this.elements.dialogue.input.value = '';
    }
    
    /**
     * Add a message to the dialogue
     */
    _addMessage(sender, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const contentP = document.createElement('p');
        contentP.textContent = content;
        messageDiv.appendChild(contentP);
        
        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = new Date().toLocaleTimeString();
        messageDiv.appendChild(timestamp);
        
        this.elements.dialogue.messages.appendChild(messageDiv);
        this.elements.dialogue.messages.scrollTop = this.elements.dialogue.messages.scrollHeight;
    }
    
    /**
     * Show the dialogue box
     */
    _showDialogue() {
        this.elements.dialogue.container.classList.remove('hidden');
        this.elements.dialogue.messages.innerHTML = '';
    }
    
    /**
     * Update the content table
     */
    _updateContentTable(content) {
        // Implementation will be in table.js
        if (window.tableHandler) {
            window.tableHandler.updateContent(content);
        }
    }
    
    /**
     * Edit selected table cells
     */
    _editSelectedCells() {
        if (this.state.selectedCells.size === 0) {
            this._showError('Please select cells to edit');
            return;
        }
        
        const cells = Array.from(this.state.selectedCells);
        wsHandler.sendMessage('edit_cells', { cells });
    }
    
    /**
     * Save content to database
     */
    _saveContent() {
        if (!this.state.taskId) {
            this._showError('No content to save');
            return;
        }
        
        wsHandler.sendMessage('save_content', {
            task_id: this.state.taskId
        });
    }
    
    /**
     * Update UI state based on current state
     */
    _updateUIState() {
        this.elements.taskInput.startButton.disabled = this.state.isProcessing;
        this.elements.taskInput.url.disabled = this.state.isProcessing;
        this.elements.taskInput.instructions.disabled = this.state.isProcessing;
        
        if (this.state.isProcessing) {
            this.elements.taskInput.startButton.classList.add('loading');
        } else {
            this.elements.taskInput.startButton.classList.remove('loading');
        }
    }
    
    /**
     * Validate API keys
     */
    _validateApiKeys() {
        return this.elements.apiKeys.tavilyKey.value &&
               this.elements.apiKeys.hfToken.value;
    }
    
    /**
     * Load saved API keys from localStorage
     */
    _loadSavedApiKeys() {
        const tavilyKey = localStorage.getItem('tavily_key');
        const hfToken = localStorage.getItem('hf_token');
        
        if (tavilyKey) this.elements.apiKeys.tavilyKey.value = tavilyKey;
        if (hfToken) this.elements.apiKeys.hfToken.value = hfToken;
    }
    
    /**
     * Show an error message
     */
    _showError(message) {
        this._addMessage('agent', `Error: ${message}`);
    }
}

// Create global UI handler instance
const uiHandler = new UIHandler(); 