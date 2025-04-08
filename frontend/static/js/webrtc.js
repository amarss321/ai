/**
 * WebRTC functionality for screen and audio capture
 */
class ScreenCaptureService {
    constructor() {
        this.mediaStream = null;
        this.audioStream = null;
        this.mediaRecorder = null;
        this.audioContext = null;
        this.audioProcessor = null;
        this.isCapturing = false;
        this.chunks = [];
        this.audioChunks = [];
        this.screenPreview = document.getElementById('screenPreview');
        this.previewPlaceholder = document.getElementById('previewPlaceholder');
        this.captureInterval = null;
        this.audioSendInterval = null;
    }

    /**
     * Initialize screen and audio capture
     */
    async initialize() {
        try {
            // Get screen capture stream
            this.mediaStream = await navigator.mediaDevices.getDisplayMedia({
                video: {
                    cursor: 'always',
                    displaySurface: 'monitor'
                },
                audio: true
            });

            // Get audio stream from microphone
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: true
            });

            // Display screen preview
            this.screenPreview.srcObject = this.mediaStream;
            this.screenPreview.style.display = 'block';
            this.previewPlaceholder.style.display = 'none';

            // Setup media recorder for screen capture
            this.mediaRecorder = new MediaRecorder(this.mediaStream, {
                mimeType: 'video/webm;codecs=vp9'
            });

            // Setup audio processing
            this.setupAudioProcessing();

            // Event listeners for media recorder
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.chunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.stopCapture();
            };

            // Handle stream ending (user clicks "Stop sharing")
            this.mediaStream.getVideoTracks()[0].onended = () => {
                this.stopCapture();
            };

            return true;
        } catch (error) {
            console.error('Error initializing capture:', error);
            return false;
        }
    }

    /**
     * Setup audio processing for speech-to-text
     */
    setupAudioProcessing() {
        this.audioContext = new AudioContext();
        const source = this.audioContext.createMediaStreamSource(this.audioStream);
        
        // Create script processor for audio processing
        this.audioProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);
        
        this.audioProcessor.onaudioprocess = (event) => {
            if (this.isCapturing) {
                const audioData = event.inputBuffer.getChannelData(0);
                this.audioChunks.push(new Float32Array(audioData));
            }
        };
        
        source.connect(this.audioProcessor);
        this.audioProcessor.connect(this.audioContext.destination);
    }

    /**
     * Start capturing screen and audio
     */
    startCapture() {
        if (!this.mediaRecorder) {
            console.error('Media recorder not initialized');
            return false;
        }

        this.isCapturing = true;
        this.chunks = [];
        this.audioChunks = [];
        
        // Start media recorder
        this.mediaRecorder.start();
        
        // Set up interval to send screen captures
        this.captureInterval = setInterval(() => {
            this.mediaRecorder.requestData();
            if (this.chunks.length > 0) {
                const blob = new Blob(this.chunks, { type: 'video/webm' });
                this.sendScreenCapture(blob);
                this.chunks = [];
            }
        }, 5000); // Send every 5 seconds
        
        // Set up interval to send audio data
        this.audioSendInterval = setInterval(() => {
            if (this.audioChunks.length > 0) {
                this.sendAudioData(this.audioChunks);
                this.audioChunks = [];
            }
        }, 2000); // Send every 2 seconds
        
        return true;
    }

    /**
     * Stop capturing screen and audio
     */
    stopCapture() {
        if (!this.isCapturing) return;
        
        this.isCapturing = false;
        
        // Stop intervals
        clearInterval(this.captureInterval);
        clearInterval(this.audioSendInterval);
        
        // Stop media recorder if it's active
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        
        // Stop all tracks
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
        
        if (this.audioStream) {
            this.audioStream.getTracks().forEach(track => track.stop());
        }
        
        // Clean up audio processing
        if (this.audioProcessor) {
            this.audioProcessor.disconnect();
            this.audioProcessor = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
        }
        
        // Reset UI
        this.screenPreview.style.display = 'none';
        this.previewPlaceholder.style.display = 'flex';
        this.screenPreview.srcObject = null;
    }

    /**
     * Send screen capture data to the server
     * @param {Blob} blob - Screen capture data
     */
    sendScreenCapture(blob) {
        // Convert blob to base64 and send via WebSocket
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64data = reader.result.split(',')[1];
            websocketService.sendMessage({
                type: 'screen_capture',
                data: base64data
            });
        };
        reader.readAsDataURL(blob);
    }

    /**
     * Send audio data to the server for speech-to-text processing
     * @param {Array} audioChunks - Array of audio data chunks
     */
    sendAudioData(audioChunks) {
        // Concatenate audio chunks into a single Float32Array
        const totalLength = audioChunks.reduce((acc, chunk) => acc + chunk.length, 0);
        const audioData = new Float32Array(totalLength);
        
        let offset = 0;
        for (const chunk of audioChunks) {
            audioData.set(chunk, offset);
            offset += chunk.length;
        }
        
        // Convert to 16-bit PCM
        const pcmData = new Int16Array(audioData.length);
        for (let i = 0; i < audioData.length; i++) {
            pcmData[i] = Math.max(-1, Math.min(1, audioData[i])) * 0x7FFF;
        }
        
        // Send audio data via WebSocket
        websocketService.sendMessage({
            type: 'audio_data',
            data: Array.from(pcmData), // Convert to regular array for JSON serialization
            sampleRate: this.audioContext.sampleRate
        });
    }
}

// Create global instance
const screenCaptureService = new ScreenCaptureService();