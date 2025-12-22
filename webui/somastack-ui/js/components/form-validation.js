/**
 * SomaStack UI - Form Validation Component
 * Version: 1.0.0
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('formValidation', (config = {}) => ({
    fields: config.fields || {},
    errors: {},
    touched: {},
    isSubmitting: false,
    
    init() {
      // Initialize errors object
      Object.keys(this.fields).forEach(key => {
        this.errors[key] = null;
        this.touched[key] = false;
      });
    },
    
    validate(fieldName) {
      const field = this.fields[fieldName];
      if (!field) return true;
      
      const value = field.value;
      const rules = field.rules || [];
      
      for (const rule of rules) {
        const result = this.checkRule(rule, value, fieldName);
        if (result !== true) {
          this.errors[fieldName] = result;
          return false;
        }
      }
      
      this.errors[fieldName] = null;
      return true;
    },
    
    checkRule(rule, value, fieldName) {
      if (typeof rule === 'function') {
        return rule(value);
      }
      
      if (typeof rule === 'object') {
        const { type, message, ...params } = rule;
        
        switch (type) {
          case 'required':
            if (!value || (typeof value === 'string' && !value.trim())) {
              return message || `${fieldName} is required`;
            }
            break;
            
          case 'email':
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (value && !emailRegex.test(value)) {
              return message || 'Invalid email address';
            }
            break;
            
          case 'minLength':
            if (value && value.length < params.min) {
              return message || `Must be at least ${params.min} characters`;
            }
            break;
            
          case 'maxLength':
            if (value && value.length > params.max) {
              return message || `Must be no more than ${params.max} characters`;
            }
            break;
            
          case 'min':
            if (value !== '' && Number(value) < params.min) {
              return message || `Must be at least ${params.min}`;
            }
            break;
            
          case 'max':
            if (value !== '' && Number(value) > params.max) {
              return message || `Must be no more than ${params.max}`;
            }
            break;
            
          case 'pattern':
            if (value && !params.regex.test(value)) {
              return message || 'Invalid format';
            }
            break;
            
          case 'match':
            const matchField = this.fields[params.field];
            if (matchField && value !== matchField.value) {
              return message || `Must match ${params.field}`;
            }
            break;
        }
      }
      
      return true;
    },
    
    validateAll() {
      let isValid = true;
      
      Object.keys(this.fields).forEach(key => {
        this.touched[key] = true;
        if (!this.validate(key)) {
          isValid = false;
        }
      });
      
      return isValid;
    },
    
    touch(fieldName) {
      this.touched[fieldName] = true;
      this.validate(fieldName);
    },
    
    reset() {
      Object.keys(this.fields).forEach(key => {
        this.errors[key] = null;
        this.touched[key] = false;
        if (this.fields[key].default !== undefined) {
          this.fields[key].value = this.fields[key].default;
        }
      });
    },
    
    getError(fieldName) {
      return this.touched[fieldName] ? this.errors[fieldName] : null;
    },
    
    hasError(fieldName) {
      return this.touched[fieldName] && this.errors[fieldName] !== null;
    },
    
    get isValid() {
      return Object.values(this.errors).every(e => e === null);
    },
    
    get hasErrors() {
      return Object.values(this.errors).some(e => e !== null);
    },
    
    async submit(handler) {
      if (this.isSubmitting) return;
      
      if (!this.validateAll()) {
        return;
      }
      
      this.isSubmitting = true;
      
      try {
        const data = {};
        Object.keys(this.fields).forEach(key => {
          data[key] = this.fields[key].value;
        });
        
        await handler(data);
      } finally {
        this.isSubmitting = false;
      }
    }
  }));
});
