/**
 * WebSocket service for real-time communication with the server
 */
class WebSocketService {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000; // 3 seconds
        this.sessionId = null;
        this.connectionStatusElement = document.getElementById('connectionStatus');
        this.connectionStatusTextElement = document.getElementById('connectionStatusText');
    }

    /**
     * Initialize WebSocket connection
     */
    initialize() {
        // Get the host from the current URL
        const host = window.location.host;
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        
        // Create WebSocket connection
        this.socket = new WebSocket(`${protocol}//${host}/ws`);
        
        // Set up event handlers
        this.socket.onopen = this.onOpen.bind(this);
        this.socket.onmessage = this.onMessage.bind(this);
        this.socket.onclose = this.onClose.bind(this);
        this.socket.onerror = this.onError.bind(this);
    }

    /**
     * Handle WebSocket open event
     */
    onOpen() {
        console.log('WebSocket connection established');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateConnectionStatus(true);
        
        // Request a new session ID if we don't have one
        if (!this.sessionId) {
            this.sendMessage({ type: 'create_session' });
        } else {
            // Reconnect to existing session
            this.sendMessage({ 
                type: 'reconnect_session',
                sessionId: this.sessionId
            });
        }
    }

    /**
     * Handle WebSocket message event
     * @param {MessageEvent} event - WebSocket message event
     */
    onMessage(event) {
        try {
            const message = JSON.parse(event.data);
            
            switch (message.type) {
                case 'session_created':
                    this.sessionId = message.sessionId;
                    console.log('Session created:', this.sessionId);
                    // Store session ID in local storage for persistence
                    localStorage.setItem('meetingAssistantSessionId', this.sessionId);
                    break;
                    
                case 'ai_response':
                    this.handleAIResponse(message);
                    break;
                    
                case 'error':
                    console.error('Server error:', message.error);
                    break;
                    
                default:
                    console.log('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }

    /**
     * Handle WebSocket close event
     * @param {CloseEvent} event - WebSocket close event
     */
    onClose(event) {
        console.log('WebSocket connection closed:', event.code, event.reason);
        this.isConnected = false;
        this.updateConnectionStatus(false);
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.initialize();
            }, this.reconnectInterval);
        }
    }

    /**
     * Handle WebSocket error event
     * @param {Event} error - WebSocket error event
     */
    onError(error) {
        console.error('WebSocket error:', error);
    }

    /**
     * Send a message to the server
     * @param {Object} message - Message to send
     */
    sendMessage(message) {
        if (!this.isConnected) {
            console.error('Cannot send message: WebSocket not connected');
            return;
        }
        
        // Add session ID to message if available
        if (this.sessionId) {
            message.sessionId = this.sessionId;
        }
        
        try {
            this.socket.send(JSON.stringify(message));
        } catch (error) {
            console.error('Error sending WebSocket message:', error);
        }
    }

    /**
     * Handle AI response from the server
     * @param {Object} message - AI response message
     */
    handleAIResponse(message) {
        const responseContainer = document.getElementById('responseContainer');
        
        // Remove empty state if present
        const emptyState = responseContainer.querySelector('.empty-state');
        if (emptyState) {
            responseContainer.removeChild(emptyState);
        }
        
        // Create response item
        const responseItem = document.createElement('div');
        responseItem.className = 'response-item';
        
        // Format timestamp
        const timestamp = new Date(message.timestamp);
        const formattedTime = timestamp.toLocaleTimeString();
        
        // Create response content
        responseItem.innerHTML = `
            <div class="timestamp">${formattedTime}</div>
            <div class="content">${message.response}</div>
        `;
        
        // Add to container
        responseContainer.prepend(responseItem);
    }

    /**
     * Update connection status UI
     * @param {boolean} connected - Whether connected to WebSocket
     */
    updateConnectionStatus(connected) {
        if (connected) {
            this.connectionStatusElement.classList.remove('disconnected');
            this.connectionStatusTextElement.textContent = 'Connected';
        } else {
            this.connectionStatusElement.classList.add('disconnected');
            this.connectionStatusTextElement.textContent = 'Disconnected';
        }
    }
}

// Create global instance
const websocketService = new WebSocketService();