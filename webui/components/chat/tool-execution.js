/**
 * Tool Execution Component
 * 
 * Displays tool execution status and results.
 * 
 * @module components/chat/tool-execution
 */

/**
 * Tool icons by type
 */
const TOOL_ICONS = {
  code_execution: '💻',
  search_engine: '🔍',
  memory_save: '💾',
  memory_load: '📖',
  memory_delete: '🗑️',
  memory_forget: '🧹',
  browser_agent: '🌐',
  document_query: '📄',
  vision_load: '👁️',
  call_subordinate: '🤖',
  a2a_chat: '💬',
  response: '💬',
  default: '🔧',
};

/**
 * Tool Execution component factory
 * @param {Object} options - Component options
 * @param {Object} options.tool - Tool execution data
 * @returns {Object} Alpine component data
 */
export default function ToolExecution(options = {}) {
  return {
    tool: options.tool ?? {},
    expanded: false,
    
    /**
     * Get tool name
     */
    get name() {
      return this.tool.name ?? this.tool.tool_name ?? 'Unknown Tool';
    },
    
    /**
     * Get tool icon
     */
    get icon() {
      return TOOL_ICONS[this.name] ?? TOOL_ICONS.default;
    },
    
    /**
     * Get tool status
     */
    get status() {
      return this.tool.status ?? 'running'; // 'running' | 'success' | 'error'
    },
    
    /**
     * Check if running
     */
    get isRunning() {
      return this.status === 'running';
    },
    
    /**
     * Check if successful
     */
    get isSuccess() {
      return this.status === 'success';
    },
    
    /**
     * Check if error
     */
    get isError() {
      return this.status === 'error';
    },
    
    /**
     * Get status badge class
     */
    get statusClass() {
      if (this.isRunning) return 'badge-info';
      if (this.isSuccess) return 'badge-success';
      if (this.isError) return 'badge-error';
      return '';
    },
    
    /**
     * Get tool input
     */
    get input() {
      return this.tool.input ?? this.tool.arguments ?? null;
    },
    
    /**
     * Get tool output
     */
    get output() {
      return this.tool.output ?? this.tool.result ?? null;
    },
    
    /**
     * Get formatted input
     */
    get formattedInput() {
      if (!this.input) return '';
      if (typeof this.input === 'string') return this.input;
      return JSON.stringify(this.input, null, 2);
    },
    
    /**
     * Get formatted output
     */
    get formattedOutput() {
      if (!this.output) return '';
      if (typeof this.output === 'string') return this.output;
      return JSON.stringify(this.output, null, 2);
    },
    
    /**
     * Get duration
     */
    get duration() {
      if (!this.tool.duration) return null;
      return `${(this.tool.duration / 1000).toFixed(2)}s`;
    },
    
    /**
     * Toggle expanded state
     */
    toggle() {
      this.expanded = !this.expanded;
    },
    
    /**
     * Bind for header
     */
    get header() {
      return {
        '@click': () => this.toggle(),
        ':aria-expanded': () => this.expanded,
        'class': 'tool-header cursor-pointer',
      };
    },
    
    /**
     * Bind for details
     */
    get details() {
      return {
        'x-show': () => this.expanded,
        'x-collapse': '',
        'class': 'tool-details',
      };
    },
    
    /**
     * Bind for progress indicator
     */
    get progress() {
      return {
        'x-show': () => this.isRunning,
        'class': 'tool-progress',
      };
    },
  };
}

export { TOOL_ICONS };
