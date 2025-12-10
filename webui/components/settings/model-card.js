/**
 * Model Card Component
 * 
 * Settings card for LLM model configuration (Chat, Utility, Browser, Embedding).
 * 
 * @module components/settings/model-card
 */

/**
 * Provider options with icons
 */
const PROVIDERS = [
  { value: 'openai', label: 'OpenAI', icon: '🟢' },
  { value: 'anthropic', label: 'Anthropic', icon: '🟠' },
  { value: 'google', label: 'Google', icon: '🔵' },
  { value: 'azure', label: 'Azure OpenAI', icon: '🔷' },
  { value: 'ollama', label: 'Ollama', icon: '🦙' },
  { value: 'fireworks', label: 'Fireworks', icon: '🔥' },
  { value: 'together', label: 'Together', icon: '🤝' },
  { value: 'groq', label: 'Groq', icon: '⚡' },
  { value: 'mistral', label: 'Mistral', icon: '🌬️' },
  { value: 'cohere', label: 'Cohere', icon: '🔮' },
];

/**
 * Model Card component factory
 * @param {Object} options - Card options
 * @param {string} options.type - Model type (chat, utility, browser, embedding)
 * @param {Object} options.config - Current configuration
 * @param {Function} options.onChange - Change handler
 * @returns {Object} Alpine component data
 */
export default function ModelCard(options = {}) {
  return {
    type: options.type ?? 'chat',
    providers: PROVIDERS,
    
    // Form state
    provider: options.config?.provider ?? 'openai',
    modelName: options.config?.model_name ?? '',
    contextLength: options.config?.context_length ?? 4096,
    rateLimit: options.config?.rate_limit ?? 60,
    temperature: options.config?.temperature ?? 0.7,
    maxTokens: options.config?.max_tokens ?? 2048,
    kwargs: options.config?.kwargs ?? {},
    
    // UI state
    showAdvanced: false,
    kwargsText: '',
    
    init() {
      // Initialize kwargs text
      this.kwargsText = JSON.stringify(this.kwargs, null, 2);
    },
    
    /**
     * Get title based on type
     */
    get title() {
      const titles = {
        chat: 'Chat Model',
        utility: 'Utility Model',
        browser: 'Browser Model',
        embedding: 'Embedding Model',
      };
      return titles[this.type] ?? 'Model';
    },
    
    /**
     * Get icon based on type
     */
    get icon() {
      const icons = {
        chat: '💬',
        utility: '🔧',
        browser: '🌐',
        embedding: '📊',
      };
      return icons[this.type] ?? '🤖';
    },
    
    /**
     * Get current provider object
     */
    get currentProvider() {
      return this.providers.find(p => p.value === this.provider);
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
     * Handle model name change
     * @param {string} value - New model name
     */
    onModelNameChange(value) {
      this.modelName = value;
      this.emitChange();
    },
    
    /**
     * Handle context length change
     * @param {number} value - New context length
     */
    onContextLengthChange(value) {
      this.contextLength = parseInt(value, 10);
      this.emitChange();
    },
    
    /**
     * Handle rate limit change
     * @param {number} value - New rate limit
     */
    onRateLimitChange(value) {
      this.rateLimit = parseInt(value, 10);
      this.emitChange();
    },
    
    /**
     * Handle temperature change
     * @param {number} value - New temperature
     */
    onTemperatureChange(value) {
      this.temperature = parseFloat(value);
      this.emitChange();
    },
    
    /**
     * Handle max tokens change
     * @param {number} value - New max tokens
     */
    onMaxTokensChange(value) {
      this.maxTokens = parseInt(value, 10);
      this.emitChange();
    },
    
    /**
     * Handle kwargs change
     * @param {string} text - JSON text
     */
    onKwargsChange(text) {
      this.kwargsText = text;
      try {
        this.kwargs = JSON.parse(text);
        this.emitChange();
      } catch (e) {
        // Invalid JSON, don't update
      }
    },
    
    /**
     * Emit change to parent
     */
    emitChange() {
      const config = {
        provider: this.provider,
        model_name: this.modelName,
        context_length: this.contextLength,
        rate_limit: this.rateLimit,
        temperature: this.temperature,
        max_tokens: this.maxTokens,
        kwargs: this.kwargs,
      };
      options.onChange?.(this.type, config);
    },
    
    /**
     * Toggle advanced settings
     */
    toggleAdvanced() {
      this.showAdvanced = !this.showAdvanced;
    },
    
    /**
     * Reset to defaults
     */
    resetDefaults() {
      this.provider = 'openai';
      this.modelName = '';
      this.contextLength = 4096;
      this.rateLimit = 60;
      this.temperature = 0.7;
      this.maxTokens = 2048;
      this.kwargs = {};
      this.kwargsText = '{}';
      this.emitChange();
    },
  };
}

export { PROVIDERS };
