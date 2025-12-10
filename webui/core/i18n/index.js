/**
 * Internationalization (i18n) Module
 * 
 * Enhanced i18n system with:
 * - Translation loading from /i18n/{locale}.json
 * - Locale switching without page reload
 * - Date/number formatting according to locale
 * - RTL layout support
 * - Interpolation support
 * 
 * @module core/i18n
 * Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6
 */

/**
 * Supported locales with metadata
 */
export const LOCALES = {
  en: { name: 'English', nativeName: 'English', dir: 'ltr' },
  es: { name: 'Spanish', nativeName: 'Español', dir: 'ltr' },
  fr: { name: 'French', nativeName: 'Français', dir: 'ltr' },
  de: { name: 'German', nativeName: 'Deutsch', dir: 'ltr' },
  pt: { name: 'Portuguese', nativeName: 'Português', dir: 'ltr' },
  zh: { name: 'Chinese', nativeName: '中文', dir: 'ltr' },
  ja: { name: 'Japanese', nativeName: '日本語', dir: 'ltr' },
  ko: { name: 'Korean', nativeName: '한국어', dir: 'ltr' },
  ar: { name: 'Arabic', nativeName: 'العربية', dir: 'rtl' },
  he: { name: 'Hebrew', nativeName: 'עברית', dir: 'rtl' },
};

/**
 * Default fallback locale
 */
const DEFAULT_LOCALE = 'en';

/**
 * i18n Manager class
 */
class I18nManager {
  constructor() {
    this.locale = DEFAULT_LOCALE;
    this.translations = {};
    this.fallbackTranslations = {};
    this.listeners = new Set();
  }
  
  /**
   * Initialize i18n with saved or detected locale
   */
  async init() {
    // Load saved locale or detect from browser
    const savedLocale = this.getSavedLocale();
    const browserLocale = this.detectBrowserLocale();
    const locale = savedLocale || browserLocale || DEFAULT_LOCALE;
    
    // Load fallback translations first
    if (locale !== DEFAULT_LOCALE) {
      await this.loadTranslations(DEFAULT_LOCALE, true);
    }
    
    // Load target locale
    await this.setLocale(locale);
    
    // Set up Alpine store if available
    this.setupAlpineStore();
    
    return this;
  }
  
  /**
   * Get saved locale from localStorage
   * @returns {string|null}
   */
  getSavedLocale() {
    try {
      return localStorage.getItem('locale');
    } catch {
      return null;
    }
  }
  
  /**
   * Detect browser locale
   * @returns {string}
   */
  detectBrowserLocale() {
    const browserLang = navigator.language || navigator.userLanguage;
    const shortLang = browserLang?.split('-')[0];
    return LOCALES[shortLang] ? shortLang : DEFAULT_LOCALE;
  }
  
  /**
   * Load translations for a locale
   * @param {string} locale - Locale code
   * @param {boolean} asFallback - Store as fallback translations
   */
  async loadTranslations(locale, asFallback = false) {
    try {
      const response = await fetch(`/static/i18n/${locale}.json`);
      if (!response.ok) {
        console.warn(`[i18n] Failed to load ${locale} translations (HTTP ${response.status})`);
        return {};
      }
      
      const translations = await response.json();
      
      if (asFallback) {
        this.fallbackTranslations = translations;
      } else {
        this.translations = translations;
      }
      
      return translations;
    } catch (error) {
      console.error(`[i18n] Error loading ${locale} translations:`, error);
      return {};
    }
  }
  
  /**
   * Set the current locale
   * @param {string} locale - Locale code
   */
  async setLocale(locale) {
    if (!LOCALES[locale]) {
      console.warn(`[i18n] Unknown locale: ${locale}, falling back to ${DEFAULT_LOCALE}`);
      locale = DEFAULT_LOCALE;
    }
    
    // Load translations if different from current
    if (locale !== this.locale || Object.keys(this.translations).length === 0) {
      await this.loadTranslations(locale);
    }
    
    this.locale = locale;
    
    // Save to localStorage
    try {
      localStorage.setItem('locale', locale);
    } catch {
      // Ignore storage errors
    }
    
    // Update document attributes
    this.updateDocumentAttributes();
    
    // Apply translations to DOM
    this.applyTranslations();
    
    // Notify listeners
    this.notifyListeners();
  }
  
  /**
   * Update document attributes for locale
   */
  updateDocumentAttributes() {
    const localeInfo = LOCALES[this.locale];
    
    document.documentElement.setAttribute('lang', this.locale);
    document.documentElement.setAttribute('dir', localeInfo?.dir || 'ltr');
    
    // Toggle RTL class for CSS
    document.documentElement.classList.toggle('rtl', localeInfo?.dir === 'rtl');
  }
  
  /**
   * Translate a key with optional interpolation
   * @param {string} key - Translation key
   * @param {Object} params - Interpolation parameters
   * @returns {string} Translated string
   */
  t(key, params = {}) {
    let text = this.translations[key] ?? this.fallbackTranslations[key];
    
    if (text === undefined) {
      console.warn(`[i18n] Missing translation for key: ${key}`);
      return key;
    }
    
    // Interpolate parameters
    if (params && typeof text === 'string') {
      text = text.replace(/\{(\w+)\}/g, (match, paramKey) => {
        return params[paramKey] !== undefined ? params[paramKey] : match;
      });
      
      // Also support {{param}} syntax
      text = text.replace(/\{\{(\w+)\}\}/g, (match, paramKey) => {
        return params[paramKey] !== undefined ? params[paramKey] : match;
      });
    }
    
    return text;
  }
  
  /**
   * Format a date according to locale
   * @param {Date|string|number} date - Date to format
   * @param {Object} options - Intl.DateTimeFormat options
   * @returns {string} Formatted date
   */
  formatDate(date, options = {}) {
    const dateObj = date instanceof Date ? date : new Date(date);
    
    const defaultOptions = {
      dateStyle: 'medium',
      ...options,
    };
    
    try {
      return new Intl.DateTimeFormat(this.locale, defaultOptions).format(dateObj);
    } catch {
      return dateObj.toLocaleDateString();
    }
  }
  
  /**
   * Format a time according to locale
   * @param {Date|string|number} date - Date to format
   * @param {Object} options - Intl.DateTimeFormat options
   * @returns {string} Formatted time
   */
  formatTime(date, options = {}) {
    const dateObj = date instanceof Date ? date : new Date(date);
    
    const defaultOptions = {
      timeStyle: 'short',
      ...options,
    };
    
    try {
      return new Intl.DateTimeFormat(this.locale, defaultOptions).format(dateObj);
    } catch {
      return dateObj.toLocaleTimeString();
    }
  }
  
  /**
   * Format a date and time according to locale
   * @param {Date|string|number} date - Date to format
   * @param {Object} options - Intl.DateTimeFormat options
   * @returns {string} Formatted date and time
   */
  formatDateTime(date, options = {}) {
    const dateObj = date instanceof Date ? date : new Date(date);
    
    const defaultOptions = {
      dateStyle: 'medium',
      timeStyle: 'short',
      ...options,
    };
    
    try {
      return new Intl.DateTimeFormat(this.locale, defaultOptions).format(dateObj);
    } catch {
      return dateObj.toLocaleString();
    }
  }
  
  /**
   * Format a relative time (e.g., "2 hours ago")
   * @param {Date|string|number} date - Date to format
   * @returns {string} Relative time string
   */
  formatRelativeTime(date) {
    const dateObj = date instanceof Date ? date : new Date(date);
    const now = new Date();
    const diffMs = now - dateObj;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    
    try {
      const rtf = new Intl.RelativeTimeFormat(this.locale, { numeric: 'auto' });
      
      if (diffDay > 0) return rtf.format(-diffDay, 'day');
      if (diffHour > 0) return rtf.format(-diffHour, 'hour');
      if (diffMin > 0) return rtf.format(-diffMin, 'minute');
      return rtf.format(-diffSec, 'second');
    } catch {
      if (diffDay > 0) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
      if (diffHour > 0) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
      if (diffMin > 0) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
      return 'just now';
    }
  }
  
  /**
   * Format a number according to locale
   * @param {number} number - Number to format
   * @param {Object} options - Intl.NumberFormat options
   * @returns {string} Formatted number
   */
  formatNumber(number, options = {}) {
    try {
      return new Intl.NumberFormat(this.locale, options).format(number);
    } catch {
      return number.toString();
    }
  }
  
  /**
   * Format a currency amount according to locale
   * @param {number} amount - Amount to format
   * @param {string} currency - Currency code (e.g., 'USD')
   * @returns {string} Formatted currency
   */
  formatCurrency(amount, currency = 'USD') {
    try {
      return new Intl.NumberFormat(this.locale, {
        style: 'currency',
        currency,
      }).format(amount);
    } catch {
      return `${currency} ${amount.toFixed(2)}`;
    }
  }
  
  /**
   * Format a percentage according to locale
   * @param {number} value - Value to format (0-1 or 0-100)
   * @param {boolean} isDecimal - If true, value is 0-1; if false, 0-100
   * @returns {string} Formatted percentage
   */
  formatPercent(value, isDecimal = true) {
    const normalizedValue = isDecimal ? value : value / 100;
    
    try {
      return new Intl.NumberFormat(this.locale, {
        style: 'percent',
        maximumFractionDigits: 1,
      }).format(normalizedValue);
    } catch {
      return `${(normalizedValue * 100).toFixed(1)}%`;
    }
  }
  
  /**
   * Apply translations to DOM elements with data-i18n attributes
   * @param {Element} root - Root element to search within
   */
  applyTranslations(root = document) {
    if (!root) return;
    
    // Text content: data-i18n-key
    root.querySelectorAll('[data-i18n-key]').forEach(el => {
      const key = el.getAttribute('data-i18n-key');
      const params = el.getAttribute('data-i18n-params');
      if (key) {
        const parsedParams = params ? JSON.parse(params) : {};
        el.textContent = this.t(key, parsedParams);
      }
    });
    
    // Placeholder: data-i18n-placeholder
    root.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
      const key = el.getAttribute('data-i18n-placeholder');
      if (key) {
        el.setAttribute('placeholder', this.t(key));
      }
    });
    
    // ARIA label: data-i18n-aria-label
    root.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
      const key = el.getAttribute('data-i18n-aria-label');
      if (key) {
        el.setAttribute('aria-label', this.t(key));
      }
    });
    
    // Title: data-i18n-title
    root.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      if (key) {
        el.setAttribute('title', this.t(key));
      }
    });
  }
  
  /**
   * Add a locale change listener
   * @param {Function} callback - Callback function
   * @returns {Function} Unsubscribe function
   */
  onLocaleChange(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }
  
  /**
   * Notify all listeners of locale change
   */
  notifyListeners() {
    this.listeners.forEach(callback => {
      try {
        callback(this.locale);
      } catch (error) {
        console.error('[i18n] Listener error:', error);
      }
    });
  }
  
  /**
   * Set up Alpine.js store for reactive translations
   */
  setupAlpineStore() {
    document.addEventListener('alpine:init', () => {
      if (!globalThis.Alpine) return;
      
      globalThis.Alpine.store('i18n', {
        locale: this.locale,
        t: (key, params) => this.t(key, params),
        formatDate: (date, options) => this.formatDate(date, options),
        formatTime: (date, options) => this.formatTime(date, options),
        formatDateTime: (date, options) => this.formatDateTime(date, options),
        formatRelativeTime: (date) => this.formatRelativeTime(date),
        formatNumber: (number, options) => this.formatNumber(number, options),
        formatCurrency: (amount, currency) => this.formatCurrency(amount, currency),
        formatPercent: (value, isDecimal) => this.formatPercent(value, isDecimal),
        setLocale: async (locale) => {
          await this.setLocale(locale);
          globalThis.Alpine.store('i18n').locale = locale;
        },
        locales: LOCALES,
        isRTL: () => LOCALES[this.locale]?.dir === 'rtl',
      });
    });
    
    // Update store when locale changes
    this.onLocaleChange((locale) => {
      if (globalThis.Alpine?.store) {
        const store = globalThis.Alpine.store('i18n');
        if (store) store.locale = locale;
      }
    });
  }
  
  /**
   * Check if current locale is RTL
   * @returns {boolean}
   */
  isRTL() {
    return LOCALES[this.locale]?.dir === 'rtl';
  }
  
  /**
   * Get current locale info
   * @returns {Object}
   */
  getLocaleInfo() {
    return {
      code: this.locale,
      ...LOCALES[this.locale],
    };
  }
  
  /**
   * Get list of available locales
   * @returns {Array}
   */
  getAvailableLocales() {
    return Object.entries(LOCALES).map(([code, info]) => ({
      code,
      ...info,
    }));
  }
}

// Create singleton instance
export const i18n = new I18nManager();

// Convenience exports
export const t = (key, params) => i18n.t(key, params);
export const formatDate = (date, options) => i18n.formatDate(date, options);
export const formatTime = (date, options) => i18n.formatTime(date, options);
export const formatDateTime = (date, options) => i18n.formatDateTime(date, options);
export const formatRelativeTime = (date) => i18n.formatRelativeTime(date);
export const formatNumber = (number, options) => i18n.formatNumber(number, options);
export const formatCurrency = (amount, currency) => i18n.formatCurrency(amount, currency);
export const formatPercent = (value, isDecimal) => i18n.formatPercent(value, isDecimal);
export const setLocale = (locale) => i18n.setLocale(locale);

export default i18n;
