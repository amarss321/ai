/**
 * Main application logic for AI Meeting Assistant
 */
class MeetingAssistantApp {
    constructor() {
        // UI Elements
        this.startCaptureButton = document.getElementById('startCapture');
        this.stopCaptureButton = document.getElementById('stopCapture');
        this.captureStatusElement = document.getElementById('captureStatus');
        this.statusLightElement = document.getElementById('statusLight');
        this.settingsForm = document.getElementById('settingsForm');
        
        // App state
        this.isCapturing = false;
        this.settings = {
            phoneNumber: '',
            aiResponseFrequency: 60,
            sendMobileNotifications: false
        };
        
        // Initialize
        this.loadSettings();
        this.bindEvents();
    }

    /**
     * Initialize the application
     */
    initialize() {
        // Initialize WebSocket connection
        websocketService.initialize();
        
        // Load session ID from local storage if available
        const savedSessionId = localStorage.getItem('meetingAssistantSessionId');
        if (savedSessionId) {
            websocketService.sessionId = savedSessionId;
        }
    }

    /**
     * Bind event listeners
     */
    bindEvents() {
        // Capture control buttons
        this.startCaptureButton.addEventListener('click', this.startCapture.bind(this));
        this.stopCaptureButton.addEventListener('click', this.stopCapture.bind(this));
        
        // Settings form
        this.settingsForm.addEventListener('submit', this.saveSettings.bind(this));
        
        // Load settings into form
        document.getElementById('phoneNumber').value = this.settings.phoneNumber;
        document.getElementById('aiResponseFrequency').value = this.settings.aiResponseFrequency;
        document.getElementById('sendMobileNotifications').checked = this.settings.sendMobileNotifications;
    }

    /**
     * Start screen and audio capture
     */
    async startCapture() {
        // Initialize screen capture if not already done
        if (!screenCaptureService.mediaStream) {
            const initialized = await screenCaptureService.initialize();
            if (!initialized) {
                alert('Failed to initialize screen capture. Please check permissions and try again.');
                return;
            }
        }
        
        // Start capture
        const started = screenCaptureService.startCapture();
        if (!started) {
            alert('Failed to start capture. Please try again.');
            return;
        }
        
        // Update UI
        this.isCapturing = true;
        this.startCaptureButton.disabled = true;
        this.stopCaptureButton.disabled = false;
        this.captureStatusElement.textContent = 'Capturing';
        this.statusLightElement.classList.remove('inactive');
        this.statusLightElement.classList.add('active');
        
        // Send settings to server
        websocketService.sendMessage({
            type: 'update_settings',
            settings: this.settings
        });
        
        // Notify server that capture has started
        websocketService.sendMessage({
            type: 'capture_started'
        });
    }

    /**
     * Stop screen and audio capture
     */
    stopCapture() {
        // Stop capture
        screenCaptureService.stopCapture();
        
        // Update UI
        this.isCapturing = false;
        this.startCaptureButton.disabled = false;
        this.stopCaptureButton.disabled = true;
        this.captureStatusElement.textContent = 'Not capturing';
        this.statusLightElement.classList.remove('active');
        this.statusLightElement.classList.add('inactive');
        
        // Notify server that capture has stopped
        websocketService.sendMessage({
            type: 'capture_stopped'
        });
    }

    /**
     * Save user settings
     * @param {Event} event - Form submit event
     */
    saveSettings(event) {
        event.preventDefault();
        
        // Get form values
        const phoneNumber = document.getElementById('phoneNumber').value;
        const aiResponseFrequency = parseInt(document.getElementById('aiResponseFrequency').value);
        const sendMobileNotifications = document.getElementById('sendMobileNotifications').checked;
        
        // Update settings
        this.settings = {
            phoneNumber,
            aiResponseFrequency,
            sendMobileNotifications
        };
        
        // Save to local storage
        localStorage.setItem('meetingAssistantSettings', JSON.stringify(this.settings));
        
        // Send to server if connected
        if (websocketService.isConnected) {
            websocketService.sendMessage({
                type: 'update_settings',
                settings: this.settings
            });
        }
        
        alert('Settings saved successfully!');
    }

    /**
     * Load user settings from local storage
     */
    loadSettings() {
        const savedSettings = localStorage.getItem('meetingAssistantSettings');
        if (savedSettings) {
            try {
                this.settings = JSON.parse(savedSettings);
            } catch (error) {
                console.error('Error parsing saved settings:', error);
            }
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new MeetingAssistantApp();
    app.initialize();
});