/**
 * Speech Card Component
 *
 * Settings card for Speech/Voice configuration (STT/TTS).
 *
 * @module components/settings/speech-card
 */

/**
 * Speech provider options
 */
const SPEECH_PROVIDERS = [
  { value: 'browser', label: 'Browser (Web Speech API)', icon: '🌐' },
  { value: 'kokoro', label: 'Kokoro', icon: '🎤' },
  { value: 'realtime', label: 'OpenAI Realtime', icon: '⚡' },
  { value: 'whisper', label: 'Whisper', icon: '🔊' },
];

/**
 * Whisper model sizes
 */
const WHISPER_MODELS = [
  { value: 'tiny', label: 'Tiny (fastest)' },
  { value: 'base', label: 'Base' },
  { value: 'small', label: 'Small' },
  { value: 'medium', label: 'Medium' },
  { value: 'large', label: 'Large (most accurate)' },
];

/**
 * Realtime voices
 */
const REALTIME_VOICES = [
  { value: 'alloy', label: 'Alloy' },
  { value: 'echo', label: 'Echo' },
  { value: 'fable', label: 'Fable' },
  { value: 'onyx', label: 'Onyx' },
  { value: 'nova', label: 'Nova' },
  { value: 'shimmer', label: 'Shimmer' },
];

/**
 * Speech Card component factory
 * @param {Object} options - Card options
 * @param {Object} options.config - Current configuration
 * @param {Function} options.onChange - Change handler
 * @returns {Object} Alpine component data
 */
export default function SpeechCard(options = {}) {
  return {
    // Provider selection
    provider: options.config?.provider ?? 'browser',
    providers: SPEECH_PROVIDERS,

    // STT settings
    sttEnabled: options.config?.stt_enabled ?? true,
    whisperModel: options.config?.whisper_model ?? 'base',
    whisperModels: WHISPER_MODELS,
    language: options.config?.language ?? 'en',
    silenceThreshold: options.config?.silence_threshold ?? 0.5,
    vadThreshold: options.config?.vad_threshold ?? 0.3,

    // Realtime settings
    realtimeModel: options.config?.realtime_model ?? 'gpt-4o-realtime-preview',
    realtimeVoice: options.config?.realtime_voice ?? 'alloy',
    realtimeVoices: REALTIME_VOICES,
    realtimeEndpoint: options.config?.realtime_endpoint ?? '',

    // Kokoro settings
    kokoroEnabled: options.config?.kokoro_enabled ?? false,


    // TTS settings
    ttsEnabled: options.config?.tts_enabled ?? true,

    /**
     * Get title
     */
    get title() {
      return 'Speech / Voice';
    },

    /**
     * Get icon
     */
    get icon() {
      return '🎙️';
    },

    /**
     * Get description
     */
    get description() {
      return 'Configure speech-to-text and text-to-speech settings';
    },

    /**
     * Get current provider object
     */
    get currentProvider() {
      return this.providers.find((p) => p.value === this.provider);
    },

    /**
     * Check if realtime provider is selected
     */
    get isRealtime() {
      return this.provider === 'realtime';
    },

    /**
     * Check if Kokoro provider is selected
     */
    get isKokoro() {
      return this.provider === 'kokoro';
    },

    /**
     * Check if Whisper provider is selected
     */
    get isWhisper() {
      return this.provider === 'whisper';
    },

    /**
     * Handle provider change
     * @param {string} value - New provider
     */
    onProviderChange(value) {
      this.provider = value;
      this.emitChange();
    },

    /**
     * Handle STT enabled change
     * @param {boolean} value - New value
     */
    onSttEnabledChange(value) {
      this.sttEnabled = value;
      this.emitChange();
    },

    /**
     * Handle Whisper model change
     * @param {string} value - New model
     */
    onWhisperModelChange(value) {
      this.whisperModel = value;
      this.emitChange();
    },

    /**
     * Handle language change
     * @param {string} value - New language
     */
    onLanguageChange(value) {
      this.language = value;
      this.emitChange();
    },

    /**
     * Handle silence threshold change
     * @param {number} value - New threshold
     */
    onSilenceThresholdChange(value) {
      this.silenceThreshold = parseFloat(value);
      this.emitChange();
    },

    /**
     * Handle VAD threshold change
     * @param {number} value - New threshold
     */
    onVadThresholdChange(value) {
      this.vadThreshold = parseFloat(value);
      this.emitChange();
    },

    /**
     * Handle realtime model change
     * @param {string} value - New model
     */
    onRealtimeModelChange(value) {
      this.realtimeModel = value;
      this.emitChange();
    },

    /**
     * Handle realtime voice change
     * @param {string} value - New voice
     */
    onRealtimeVoiceChange(value) {
      this.realtimeVoice = value;
      this.emitChange();
    },

    /**
     * Handle realtime endpoint change
     * @param {string} value - New endpoint
     */
    onRealtimeEndpointChange(value) {
      this.realtimeEndpoint = value;
      this.emitChange();
    },

    /**
     * Handle Kokoro enabled change
     * @param {boolean} value - New value
     */
    onKokoroEnabledChange(value) {
      this.kokoroEnabled = value;
      this.emitChange();
    },

    /**
     * Handle TTS enabled change
     * @param {boolean} value - New value
     */
    onTtsEnabledChange(value) {
      this.ttsEnabled = value;
      this.emitChange();
    },

    /**
     * Emit change to parent
     */
    emitChange() {
      const config = {
        provider: this.provider,
        stt_enabled: this.sttEnabled,
        whisper_model: this.whisperModel,
        language: this.language,
        silence_threshold: this.silenceThreshold,
        vad_threshold: this.vadThreshold,
        realtime_model: this.realtimeModel,
        realtime_voice: this.realtimeVoice,
        realtime_endpoint: this.realtimeEndpoint,
        kokoro_enabled: this.kokoroEnabled,
        tts_enabled: this.ttsEnabled,
      };
      options.onChange?.('speech', config);
    },

    /**
     * Reset to defaults
     */
    resetDefaults() {
      this.provider = 'browser';
      this.sttEnabled = true;
      this.whisperModel = 'base';
      this.language = 'en';
      this.silenceThreshold = 0.5;
      this.vadThreshold = 0.3;
      this.realtimeModel = 'gpt-4o-realtime-preview';
      this.realtimeVoice = 'alloy';
      this.realtimeEndpoint = '';
      this.kokoroEnabled = false;
      this.ttsEnabled = true;
      this.emitChange();
    },

    /**
     * Get summary text for collapsed state
     */
    get summary() {
      const parts = [];
      parts.push(`Provider: ${this.currentProvider?.label || this.provider}`);
      if (this.sttEnabled) parts.push('STT: On');
      if (this.ttsEnabled) parts.push('TTS: On');
      return parts.join(' • ');
    },
  };
}

export { SPEECH_PROVIDERS, WHISPER_MODELS, REALTIME_VOICES };
