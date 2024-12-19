/**
 * WebSocket Handler Module
 * 
 * Handles real-time communication with the server.
 */

class WebSocketHandler {
    constructor() {
        this.ws = null;
        this.clientId = this._generateClientId();
        this.messageCallbacks = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second delay
    }
    
    /**
     * Connect to the WebSocket server
     */
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/ws/${this.clientId}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            this._showNotification('Connected to server', 'success');
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this._handleDisconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this._showNotification('Connection error', 'error');
        };
        
        this.ws.onmessage = (event) => {
            this._handleMessage(event.data);
        };
    }
    
    /**
     * Send a message to the server
     */
    sendMessage(type, content) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            this._showNotification('Not connected to server', 'error');
            return;
        }
        
        const message = {
            type,
            content,
            timestamp: new Date().toISOString()
        };
        
        this.ws.send(JSON.stringify(message));
    }
    
    /**
     * Register a callback for specific message types
     */
    onMessage(type, callback) {
        if (!this.messageCallbacks.has(type)) {
            this.messageCallbacks.set(type, []);
        }
        this.messageCallbacks.get(type).push(callback);
    }
    
    /**
     * Handle incoming messages
     */
    _handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            // Call registered callbacks for this message type
            const callbacks = this.messageCallbacks.get(message.type) || [];
            callbacks.forEach(callback => {
                try {
                    callback(message.content);
                } catch (error) {
                    console.error('Error in message callback:', error);
                }
            });
            
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }
    
    /**
     * Handle WebSocket disconnection
     */
    _handleDisconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this._showNotification(
                `Connection lost. Reconnecting (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`,
                'info'
            );
            
            // Exponential backoff for reconnection
            setTimeout(() => {
                this.connect();
            }, this.reconnectDelay);
            
            // Increase delay for next attempt
            this.reconnectDelay *= 2;
        } else {
            this._showNotification(
                'Could not reconnect to server. Please refresh the page.',
                'error'
            );
        }
    }
    
    /**
     * Generate a unique client ID
     */
    _generateClientId() {
        return 'client_' + Math.random().toString(36).substr(2, 9);
    }
    
    /**
     * Show a notification to the user
     */
    _showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Trigger reflow to enable transition
        notification.offsetHeight;
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 200);
        }, 3000);
    }
}

// Create global WebSocket handler instance
const wsHandler = new WebSocketHandler();

// Connect when the page loads
document.addEventListener('DOMContentLoaded', () => {
    wsHandler.connect();
}); 