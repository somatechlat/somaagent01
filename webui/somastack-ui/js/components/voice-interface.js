/**
 * SomaStack UI - Voice Interface Component
 * Version: 1.0.0
 * 
 * Provides waveform visualization, real-time transcription,
 * TTS progress, PTT/VAD modes, and connection status.
 */

document.addEventListener('alpine:init', () => {
  /**
   * Waveform Visualizer Component
   * Displays audio waveform using Web Audio API
   */
  Alpine.data('waveformVisualizer', (config = {}) => ({
    isActive: false,
    audioContext: null,
    analyser: null,
    dataArray: null,
    canvasCtx: null,
    animationId: null,
    barCount: config.barCount || 32,
    barColor: config.barColor || 'var(--soma-color-primary-500)',
    backgroundColor: config.backgroundColor || 'transparent',
    
    init() {
      this.$nextTick(() => {
        const canvas = this.$refs.waveformCanvas;
        if (canvas) {
          this.canvasCtx = canvas.getContext('2d');
          this.resizeCanvas();
          window.addEventListener('resize', () => this.resizeCanvas());
        }
      });
    },
    
    resizeCanvas() {
      const canvas = this.$refs.waveformCanvas;
      if (canvas) {
        canvas.width = canvas.offsetWidth * window.devicePixelRatio;
        canvas.height = canvas.offsetHeight * window.devicePixelRatio;
        this.canvasCtx.scale(window.devicePixelRatio, window.devicePixelRatio);
      }
    },
    
    async startVisualization(stream) {
      try {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 64;
        
        const source = this.audioContext.createMediaStreamSource(stream);
        source.connect(this.analyser);
        
        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.isActive = true;
        this.draw();
      } catch (err) {
        console.error('Failed to start waveform visualization:', err);
      }
    },
    
    draw() {
      if (!this.isActive || !this.canvasCtx) return;
      
      this.animationId = requestAnimationFrame(() => this.draw());
      
      const canvas = this.$refs.waveformCanvas;
      if (!canvas) return;
      
      const width = canvas.offsetWidth;
      const height = canvas.offsetHeight;
      
      this.analyser.getByteFrequencyData(this.dataArray);
      
      this.canvasCtx.fillStyle = this.backgroundColor;
      this.canvasCtx.fillRect(0, 0, width, height);
      
      const barWidth = width / this.barCount;
      const gap = 2;
      
      for (let i = 0; i < this.barCount; i++) {
        const dataIndex = Math.floor(i * this.dataArray.length / this.barCount);
        const value = this.dataArray[dataIndex] / 255;
        const barHeight = Math.max(4, value * height * 0.8);
        
        const x = i * barWidth + gap / 2;
        const y = (height - barHeight) / 2;
        
        this.canvasCtx.fillStyle = this.barColor;
        this.canvasCtx.beginPath();
        this.canvasCtx.roundRect(x, y, barWidth - gap, barHeight, 2);
        this.canvasCtx.fill();
      }
    },
    
    stopVisualization() {
      this.isActive = false;
      if (this.animationId) {
        cancelAnimationFrame(this.animationId);
        this.animationId = null;
      }
      if (this.audioContext) {
        this.audioContext.close();
        this.audioContext = null;
      }
      
      // Clear canvas
      const canvas = this.$refs.waveformCanvas;
      if (canvas && this.canvasCtx) {
        this.canvasCtx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);
      }
    },
    
    destroy() {
      this.stopVisualization();
      window.removeEventListener('resize', this.resizeCanvas);
    }
  }));

  /**
   * Transcription Display Component
   * Shows real-time speech-to-text transcription
   */
  Alpine.data('transcriptionDisplay', (config = {}) => ({
    transcript: '',
    interimTranscript: '',
    isListening: false,
    language: config.language || 'en-US',
    
    get displayText() {
      return this.transcript + (this.interimTranscript ? ` ${this.interimTranscript}` : '');
    },
    
    get hasContent() {
      return this.transcript.length > 0 || this.interimTranscript.length > 0;
    },
    
    appendTranscript(text, isFinal = true) {
      if (isFinal) {
        this.transcript += (this.transcript ? ' ' : '') + text;
        this.interimTranscript = '';
      } else {
        this.interimTranscript = text;
      }
      
      // Auto-scroll
      this.$nextTick(() => {
        const container = this.$refs.transcriptContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },
    
    clear() {
      this.transcript = '';
      this.interimTranscript = '';
    },
    
    startListening() {
      this.isListening = true;
    },
    
    stopListening() {
      this.isListening = false;
      this.interimTranscript = '';
    }
  }));

  /**
   * TTS Progress Component
   * Shows text-to-speech playback progress
   */
  Alpine.data('ttsProgress', (config = {}) => ({
    isPlaying: false,
    progress: 0,
    duration: 0,
    currentTime: 0,
    text: '',
    
    get progressPercent() {
      if (this.duration === 0) return 0;
      return (this.currentTime / this.duration) * 100;
    },
    
    get timeDisplay() {
      const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
      };
      return `${formatTime(this.currentTime)} / ${formatTime(this.duration)}`;
    },
    
    start(text, duration) {
      this.text = text;
      this.duration = duration;
      this.currentTime = 0;
      this.isPlaying = true;
    },
    
    updateProgress(currentTime) {
      this.currentTime = currentTime;
      this.progress = this.progressPercent;
    },
    
    stop() {
      this.isPlaying = false;
      this.progress = 0;
      this.currentTime = 0;
    },
    
    pause() {
      this.isPlaying = false;
    },
    
    resume() {
      this.isPlaying = true;
    }
  }));

  /**
   * Voice Interface Component
   * Main voice interaction interface combining all voice components
   */
  Alpine.data('voiceInterface', (config = {}) => ({
    mode: config.mode || 'ptt',
    isRecording: false,
    isProcessing: false,
    isConnected: false,
    connectionStatus: 'disconnected',
    mediaStream: null,
    websocket: null,
    wsEndpoint: config.wsEndpoint || 'ws://localhost:25000/ws/voice',
    vadThreshold: config.vadThreshold || 0.01,
    vadSilenceMs: config.vadSilenceMs || 1500,
    
    init() {
      this.checkConnection();
    },
    
    // Connection management
    async connect() {
      try {
        this.connectionStatus = 'connecting';
        this.websocket = new WebSocket(this.wsEndpoint);
        
        this.websocket.onopen = () => {
          this.isConnected = true;
          this.connectionStatus = 'connected';
        };
        
        this.websocket.onclose = () => {
          this.isConnected = false;
          this.connectionStatus = 'disconnected';
        };
        
        this.websocket.onerror = (err) => {
          console.error('WebSocket error:', err);
          this.connectionStatus = 'error';
        };
        
        this.websocket.onmessage = (event) => {
          this.handleMessage(JSON.parse(event.data));
        };
      } catch (err) {
        console.error('Failed to connect:', err);
        this.connectionStatus = 'error';
      }
    },
    
    disconnect() {
      if (this.websocket) {
        this.websocket.close();
        this.websocket = null;
      }
      this.isConnected = false;
      this.connectionStatus = 'disconnected';
    },
    
    async checkConnection() {
      try {
        const httpEndpoint = this.wsEndpoint.replace('ws://', 'http://').replace('wss://', 'https://').replace('/ws/voice', '/health');
        const response = await fetch(httpEndpoint);
        this.connectionStatus = response.ok ? 'available' : 'unavailable';
      } catch {
        this.connectionStatus = 'unavailable';
      }
    },
    
    handleMessage(data) {
      switch (data.type) {
        case 'transcription':
          this.$dispatch('voice-transcription', { text: data.text, isFinal: data.is_final });
          break;
        case 'tts_start':
          this.$dispatch('voice-tts-start', { text: data.text, duration: data.duration });
          break;
        case 'tts_progress':
          this.$dispatch('voice-tts-progress', { currentTime: data.current_time });
          break;
        case 'tts_end':
          this.$dispatch('voice-tts-end');
          break;
        case 'error':
          console.error('Voice error:', data.message);
          if (window.$toast) {
            window.$toast.error(data.message);
          }
          break;
      }
    },
    
    // Recording controls
    async startRecording() {
      try {
        this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.isRecording = true;
        
        // Dispatch event for waveform visualizer
        this.$dispatch('voice-stream-start', { stream: this.mediaStream });
        
        // Send audio to websocket if connected
        if (this.isConnected && this.websocket) {
          // Audio processing would go here
          // For now, we just signal recording started
          this.websocket.send(JSON.stringify({ type: 'start_recording' }));
        }
      } catch (err) {
        console.error('Failed to start recording:', err);
        if (window.$toast) {
          window.$toast.error('Microphone access denied');
        }
      }
    },
    
    stopRecording() {
      if (this.mediaStream) {
        this.mediaStream.getTracks().forEach(track => track.stop());
        this.mediaStream = null;
      }
      this.isRecording = false;
      
      this.$dispatch('voice-stream-stop');
      
      if (this.isConnected && this.websocket) {
        this.websocket.send(JSON.stringify({ type: 'stop_recording' }));
      }
    },
    
    toggleRecording() {
      if (this.isRecording) {
        this.stopRecording();
      } else {
        this.startRecording();
      }
    },
    
    // Mode switching
    setMode(newMode) {
      if (this.isRecording) {
        this.stopRecording();
      }
      this.mode = newMode;
    },
    
    get isPTT() {
      return this.mode === 'ptt';
    },
    
    get isVAD() {
      return this.mode === 'vad';
    },
    
    // Status helpers
    get statusIcon() {
      if (this.isProcessing) return '⏳';
      if (this.isRecording) return '🎤';
      if (this.isConnected) return '🟢';
      return '⚪';
    },
    
    get statusText() {
      if (this.isProcessing) return 'Processing...';
      if (this.isRecording) return 'Recording...';
      if (this.isConnected) return 'Connected';
      return 'Disconnected';
    },
    
    get connectionClass() {
      const classes = {
        connected: 'soma-voice-status--connected',
        connecting: 'soma-voice-status--connecting',
        disconnected: 'soma-voice-status--disconnected',
        error: 'soma-voice-status--error',
        available: 'soma-voice-status--available',
        unavailable: 'soma-voice-status--unavailable'
      };
      return classes[this.connectionStatus] || '';
    },
    
    // Cleanup
    destroy() {
      this.stopRecording();
      this.disconnect();
    }
  }));

  /**
   * Voice Button Component
   * Push-to-talk or toggle button for voice recording
   */
  Alpine.data('voiceButton', (config = {}) => ({
    mode: config.mode || 'toggle',
    isPressed: false,
    size: config.size || 'md',
    
    get buttonClass() {
      const classes = ['soma-voice-btn', `soma-voice-btn--${this.size}`];
      if (this.isPressed) classes.push('soma-voice-btn--active');
      return classes.join(' ');
    },
    
    handleMouseDown() {
      if (this.mode === 'ptt') {
        this.isPressed = true;
        this.$dispatch('voice-ptt-start');
      }
    },
    
    handleMouseUp() {
      if (this.mode === 'ptt') {
        this.isPressed = false;
        this.$dispatch('voice-ptt-stop');
      }
    },
    
    handleClick() {
      if (this.mode === 'toggle') {
        this.isPressed = !this.isPressed;
        this.$dispatch(this.isPressed ? 'voice-toggle-on' : 'voice-toggle-off');
      }
    }
  }));
});
