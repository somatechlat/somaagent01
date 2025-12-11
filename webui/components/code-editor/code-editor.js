/**
 * Code Editor Component
 * Implements syntax highlighting for 20+ languages with line numbers
 * Requirements: 23.1, 23.2, 23.3, 23.4, 23.5
 */

/**
 * Code Editor Alpine Component using Ace Editor
 */
export function createCodeEditor() {
  return {
    // State
    editor: null,
    value: '',
    language: 'javascript',
    theme: 'monokai',
    readOnly: false,
    showLineNumbers: true,
    showGutter: true,
    fontSize: 14,
    tabSize: 2,
    wrap: false,
    isLoading: true,
    
    // Supported languages
    languages: [
      { id: 'javascript', label: 'JavaScript', mode: 'ace/mode/javascript' },
      { id: 'typescript', label: 'TypeScript', mode: 'ace/mode/typescript' },
      { id: 'python', label: 'Python', mode: 'ace/mode/python' },
      { id: 'java', label: 'Java', mode: 'ace/mode/java' },
      { id: 'csharp', label: 'C#', mode: 'ace/mode/csharp' },
      { id: 'cpp', label: 'C++', mode: 'ace/mode/c_cpp' },
      { id: 'c', label: 'C', mode: 'ace/mode/c_cpp' },
      { id: 'go', label: 'Go', mode: 'ace/mode/golang' },
      { id: 'rust', label: 'Rust', mode: 'ace/mode/rust' },
      { id: 'ruby', label: 'Ruby', mode: 'ace/mode/ruby' },
      { id: 'php', label: 'PHP', mode: 'ace/mode/php' },
      { id: 'swift', label: 'Swift', mode: 'ace/mode/swift' },
      { id: 'kotlin', label: 'Kotlin', mode: 'ace/mode/kotlin' },
      { id: 'scala', label: 'Scala', mode: 'ace/mode/scala' },
      { id: 'html', label: 'HTML', mode: 'ace/mode/html' },
      { id: 'css', label: 'CSS', mode: 'ace/mode/css' },
      { id: 'scss', label: 'SCSS', mode: 'ace/mode/scss' },
      { id: 'json', label: 'JSON', mode: 'ace/mode/json' },
      { id: 'yaml', label: 'YAML', mode: 'ace/mode/yaml' },
      { id: 'xml', label: 'XML', mode: 'ace/mode/xml' },
      { id: 'markdown', label: 'Markdown', mode: 'ace/mode/markdown' },
      { id: 'sql', label: 'SQL', mode: 'ace/mode/sql' },
      { id: 'bash', label: 'Bash', mode: 'ace/mode/sh' },
      { id: 'powershell', label: 'PowerShell', mode: 'ace/mode/powershell' },
      { id: 'dockerfile', label: 'Dockerfile', mode: 'ace/mode/dockerfile' },
      { id: 'plaintext', label: 'Plain Text', mode: 'ace/mode/text' }
    ],
    
    // Themes
    themes: [
      { id: 'monokai', label: 'Monokai' },
      { id: 'github', label: 'GitHub' },
      { id: 'tomorrow_night', label: 'Tomorrow Night' },
      { id: 'dracula', label: 'Dracula' },
      { id: 'solarized_dark', label: 'Solarized Dark' },
      { id: 'solarized_light', label: 'Solarized Light' },
      { id: 'twilight', label: 'Twilight' },
      { id: 'terminal', label: 'Terminal' }
    ],
    
    // Lifecycle
    async init() {
      await this.loadAce();
      this.createEditor();
    },
    
    destroy() {
      if (this.editor) {
        this.editor.destroy();
        this.editor = null;
      }
    },
    
    // Load Ace Editor
    async loadAce() {
      if (window.ace) {
        this.isLoading = false;
        return;
      }
      
      return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'vendor/ace-min/ace.js';
        script.onload = () => {
          this.isLoading = false;
          resolve();
        };
        script.onerror = reject;
        document.head.appendChild(script);
      });
    },
    
    // Create Editor Instance
    createEditor() {
      const container = this.$refs.editorContainer;
      if (!container || !window.ace) return;
      
      this.editor = ace.edit(container);
      
      // Configure editor
      this.editor.setTheme(`ace/theme/${this.theme}`);
      this.editor.session.setMode(this.getModeForLanguage(this.language));
      this.editor.setReadOnly(this.readOnly);
      this.editor.setShowPrintMargin(false);
      this.editor.setFontSize(this.fontSize);
      this.editor.session.setTabSize(this.tabSize);
      this.editor.session.setUseWrapMode(this.wrap);
      this.editor.renderer.setShowGutter(this.showGutter);
      
      // Set initial value
      if (this.value) {
        this.editor.setValue(this.value, -1);
      }
      
      // Listen for changes
      this.editor.on('change', () => {
        this.value = this.editor.getValue();
        this.$dispatch('change', { value: this.value });
      });
      
      // Focus event
      this.editor.on('focus', () => {
        this.$dispatch('focus');
      });
      
      // Blur event
      this.editor.on('blur', () => {
        this.$dispatch('blur');
      });
    },
    
    // Get Ace mode for language
    getModeForLanguage(lang) {
      const language = this.languages.find(l => l.id === lang);
      return language ? language.mode : 'ace/mode/text';
    },
    
    // Public Methods
    setValue(value) {
      this.value = value;
      if (this.editor) {
        this.editor.setValue(value, -1);
      }
    },
    
    getValue() {
      return this.editor ? this.editor.getValue() : this.value;
    },
    
    setLanguage(lang) {
      this.language = lang;
      if (this.editor) {
        this.editor.session.setMode(this.getModeForLanguage(lang));
      }
    },
    
    setTheme(theme) {
      this.theme = theme;
      if (this.editor) {
        this.editor.setTheme(`ace/theme/${theme}`);
      }
    },
    
    setReadOnly(readOnly) {
      this.readOnly = readOnly;
      if (this.editor) {
        this.editor.setReadOnly(readOnly);
      }
    },
    
    setFontSize(size) {
      this.fontSize = size;
      if (this.editor) {
        this.editor.setFontSize(size);
      }
    },
    
    focus() {
      if (this.editor) {
        this.editor.focus();
      }
    },
    
    blur() {
      if (this.editor) {
        this.editor.blur();
      }
    },
    
    // Cursor and Selection
    getCursorPosition() {
      return this.editor ? this.editor.getCursorPosition() : { row: 0, column: 0 };
    },
    
    setCursorPosition(row, column) {
      if (this.editor) {
        this.editor.moveCursorTo(row, column);
      }
    },
    
    getSelectedText() {
      return this.editor ? this.editor.getSelectedText() : '';
    },
    
    insertText(text) {
      if (this.editor) {
        this.editor.insert(text);
      }
    },
    
    // Undo/Redo
    undo() {
      if (this.editor) {
        this.editor.undo();
      }
    },
    
    redo() {
      if (this.editor) {
        this.editor.redo();
      }
    },
    
    // Search
    find(text, options = {}) {
      if (this.editor) {
        this.editor.find(text, {
          backwards: options.backwards || false,
          wrap: options.wrap !== false,
          caseSensitive: options.caseSensitive || false,
          wholeWord: options.wholeWord || false,
          regExp: options.regExp || false
        });
      }
    },
    
    findNext() {
      if (this.editor) {
        this.editor.findNext();
      }
    },
    
    findPrevious() {
      if (this.editor) {
        this.editor.findPrevious();
      }
    },
    
    replace(text) {
      if (this.editor) {
        this.editor.replace(text);
      }
    },
    
    replaceAll(text) {
      if (this.editor) {
        this.editor.replaceAll(text);
      }
    },
    
    // Formatting
    formatCode() {
      // Basic formatting - indent selection
      if (this.editor) {
        this.editor.blockIndent();
      }
    },
    
    // Line numbers
    gotoLine(line) {
      if (this.editor) {
        this.editor.gotoLine(line);
      }
    },
    
    getLineCount() {
      return this.editor ? this.editor.session.getLength() : 0;
    }
  };
}

/**
 * Register Alpine component
 */
export function registerCodeEditor() {
  if (typeof Alpine !== 'undefined') {
    Alpine.data('codeEditor', createCodeEditor);
  }
}

export default createCodeEditor;
