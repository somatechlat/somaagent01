/**
 * Voice Interface Component
 * Implements microphone button, speech recognition, and TTS playback
 * Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6
 */

/**
 * Voice Interface Manager
 * Handles speech-to-text and text-to-speech functionality
 */
export class VoiceInterface {
  constructor(options = {}) {
    this.onTranscript = options.onTranscript || (() => {});
    this.onStateChange = options.onStateChange || (() => {});
    this.onError = options.onError || console.error;
    
    this.recognition = null;
    this.synthesis = window.speechSynthesis;
    this.isListening = false;
    this.isSpeaking = false;
    this.isSupported = this.checkSupport();
    
    this.language = options.language || 'en-US';
    this.continuous = options.continuous || false;
    this.interimResults = options.interimResults || true;
    
    if (this.isSupported.recognition) {
      this.initRecognition();
    }
  }

  /**
   * Check browser support for speech APIs
   */
  checkSupport() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    return {
      recognition: !!SpeechRecognition,
      synthesis: 'speechSynthesis' in window,
      any: !!SpeechRecognition || 'speechSynthesis' in window
    };
  }

  /**
   * Initialize speech recognition
   */
  initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    
    this.recognition.continuous = this.continuous;
    this.recognition.interimResults = this.interimResults;
    this.recognition.lang = this.language;
    
    this.recognition.onstart = () => {
      this.isListening = true;
      this.onStateChange({ type: 'listening', isListening: true });
    };
    
    this.recognition.onend = () => {
      this.isListening = false;
      this.onStateChange({ type: 'stopped', isListening: false });
    };
    
    this.recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';
      
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }
      
      this.onTranscript({
        final: finalTranscript,
        interim: interimTranscript,
        isFinal: !!finalTranscript
      });
    };
    
    this.recognition.onerror = (event) => {
      this.isListening = false;
      this.onStateChange({ type: 'error', isListening: false, error: event.error });
      
      if (event.error !== 'aborted' && event.error !== 'no-speech') {
        this.onError(new Error(`Speech recognition error: ${event.error}`));
      }
    };
  }

  /**
   * Start listening for speech
   */
  startListening() {
    if (!this.isSupported.recognition) {
      this.onError(new Error('Speech recognition not supported'));
      return false;
    }
    
    if (this.isListening) return true;
    
    try {
      this.recognition.start();
      return true;
    } catch (error) {
      this.onError(error);
      return false;
    }
  }

  /**
   * Stop listening for speech
   */
  stopListening() {
    if (!this.recognition || !this.isListening) return;
    
    try {
      this.recognition.stop();
    } catch (error) {
      // Ignore errors when stopping
    }
  }

  /**
   * Toggle listening state
   */
  toggleListening() {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
    return this.isListening;
  }

  /**
   * Speak text using TTS
   * @param {string} text - Text to speak
   * @param {Object} options - Voice options
   */
  speak(text, options = {}) {
    if (!this.isSupported.synthesis) {
      this.onError(new Error('Speech synthesis not supported'));
      return Promise.reject(new Error('Not supported'));
    }
    
    return new Promise((resolve, reject) => {
      // Cancel any ongoing speech
      this.synthesis.cancel();
      
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = options.lang || this.language;
      utterance.rate = options.rate || 1;
      utterance.pitch = options.pitch || 1;
      utterance.volume = options.volume || 1;
      
      // Set voice if specified
      if (options.voice) {
        const voices = this.synthesis.getVoices();
        const voice = voices.find(v => v.name === options.voice || v.voiceURI === options.voice);
        if (voice) utterance.voice = voice;
      }
      
      utterance.onstart = () => {
        this.isSpeaking = true;
        this.onStateChange({ type: 'speaking', isSpeaking: true });
      };
      
      utterance.onend = () => {
        this.isSpeaking = false;
        this.onStateChange({ type: 'done', isSpeaking: false });
        resolve();
      };
      
      utterance.onerror = (event) => {
        this.isSpeaking = false;
        this.onStateChange({ type: 'error', isSpeaking: false, error: event.error });
        reject(new Error(`Speech synthesis error: ${event.error}`));
      };
      
      this.synthesis.speak(utterance);
    });
  }

  /**
   * Stop speaking
   */
  stopSpeaking() {
    if (this.synthesis) {
      this.synthesis.cancel();
      this.isSpeaking = false;
    }
  }

  /**
   * Get available voices
   */
  getVoices() {
    if (!this.isSupported.synthesis) return [];
    return this.synthesis.getVoices();
  }

  /**
   * Set language for recognition
   */
  setLanguage(lang) {
    this.language = lang;
    if (this.recognition) {
      this.recognition.lang = lang;
    }
  }

  /**
   * Destroy the voice interface
   */
  destroy() {
    this.stopListening();
    this.stopSpeaking();
    this.recognition = null;
  }
}

/**
 * Create Alpine.js component for voice interface
 */
export function createVoiceComponent() {
  return {
    voice: null,
    isListening: false,
    isSpeaking: false,
    isSupported: false,
    transcript: '',
    interimTranscript: '',
    error: null,
    
    init() {
      this.voice = new VoiceInterface({
        onTranscript: (result) => {
          if (result.isFinal) {
            this.transcript = result.final;
            this.interimTranscript = '';
            // Dispatch event for parent components
            this.$dispatch('voice:transcript', { text: result.final });
          } else {
            this.interimTranscript = result.interim;
          }
        },
        onStateChange: (state) => {
          this.isListening = state.isListening || false;
          this.isSpeaking = state.isSpeaking || false;
          if (state.error) {
            this.error = state.error;
          }
        },
        onError: (err) => {
          this.error = err.message;
          console.error('Voice error:', err);
        }
      });
      
      this.isSupported = this.voice.isSupported.any;
    },
    
    toggleVoice() {
      if (this.isListening) {
        this.voice.stopListening();
      } else {
        this.transcript = '';
        this.interimTranscript = '';
        this.error = null;
        this.voice.startListening();
      }
    },
    
    speak(text) {
      return this.voice.speak(text);
    },
    
    stopSpeaking() {
      this.voice.stopSpeaking();
    },
    
    destroy() {
      if (this.voice) {
        this.voice.destroy();
      }
    }
  };
}

/**
 * Register Alpine component
 */
export function registerVoiceComponent() {
  if (typeof Alpine !== 'undefined') {
    Alpine.data('voiceInterface', createVoiceComponent);
  }
}

export default VoiceInterface;
