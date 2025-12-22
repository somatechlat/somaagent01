/**
 * SomaStack UI - Agent Dashboard Component
 * Version: 1.0.0
 * 
 * Provides neuromodulator gauges, FSM state visualization,
 * reasoning stream, conversation history, and tool monitoring.
 */

document.addEventListener('alpine:init', () => {
  /**
   * Neuromodulator Gauge Component
   * Displays a single neuromodulator level with visual gauge
   */
  Alpine.data('neuroGauge', (config = {}) => ({
    name: config.name || 'Unknown',
    value: config.value || 0,
    color: config.color || 'var(--soma-color-primary-500)',
    icon: config.icon || '🧪',
    
    get percentage() {
      return Math.min(100, Math.max(0, this.value * 100));
    },
    
    get displayValue() {
      return this.value.toFixed(2);
    },
    
    get levelClass() {
      if (this.value < 0.3) return 'soma-neuro-gauge--low';
      if (this.value > 0.7) return 'soma-neuro-gauge--high';
      return 'soma-neuro-gauge--normal';
    },
    
    update(newValue) {
      this.value = Math.min(1, Math.max(0, newValue));
    }
  }));

  /**
   * Neuromodulator Panel Component
   * Displays all four neuromodulators with real-time updates
   */
  Alpine.data('neuromodulatorPanel', (config = {}) => ({
    dopamine: config.dopamine || 0.4,
    serotonin: config.serotonin || 0.5,
    noradrenaline: config.noradrenaline || 0.3,
    acetylcholine: config.acetylcholine || 0.2,
    isPolling: false,
    pollInterval: config.pollInterval || 5000,
    endpoint: config.endpoint || 'http://localhost:9696/neuromodulators',
    
    init() {
      if (config.autoStart !== false) {
        this.startPolling();
      }
    },
    
    async fetchLevels() {
      try {
        const response = await fetch(this.endpoint);
        if (response.ok) {
          const data = await response.json();
          this.dopamine = data.dopamine ?? this.dopamine;
          this.serotonin = data.serotonin ?? this.serotonin;
          this.noradrenaline = data.noradrenaline ?? this.noradrenaline;
          this.acetylcholine = data.acetylcholine ?? this.acetylcholine;
        }
      } catch (err) {
        console.warn('Failed to fetch neuromodulator levels:', err.message);
      }
    },
    
    startPolling() {
      if (this.isPolling) return;
      this.isPolling = true;
      this.fetchLevels();
      this._pollTimer = setInterval(() => this.fetchLevels(), this.pollInterval);
    },
    
    stopPolling() {
      this.isPolling = false;
      if (this._pollTimer) {
        clearInterval(this._pollTimer);
        this._pollTimer = null;
      }
    },
    
    destroy() {
      this.stopPolling();
    }
  }));

  /**
   * FSM State Diagram Component
   * Visualizes the current FSM state and transitions
   */
  Alpine.data('fsmDiagram', (config = {}) => ({
    currentState: config.currentState || 'idle',
    states: config.states || ['idle', 'planning', 'executing', 'verifying', 'error'],
    transitions: [],
    
    get stateIndex() {
      return this.states.indexOf(this.currentState);
    },
    
    isActive(state) {
      return this.currentState === state;
    },
    
    isPast(state) {
      const idx = this.states.indexOf(state);
      return idx < this.stateIndex && this.currentState !== 'error';
    },
    
    getStateClass(state) {
      if (this.isActive(state)) return 'soma-fsm-state--active';
      if (this.isPast(state)) return 'soma-fsm-state--complete';
      if (state === 'error' && this.currentState === 'error') return 'soma-fsm-state--error';
      return '';
    },
    
    getStateIcon(state) {
      const icons = {
        idle: '⏸️',
        planning: '📋',
        executing: '⚡',
        verifying: '✅',
        error: '❌'
      };
      return icons[state] || '●';
    },
    
    transition(newState) {
      if (this.states.includes(newState)) {
        this.transitions.push({
          from: this.currentState,
          to: newState,
          timestamp: new Date()
        });
        this.currentState = newState;
      }
    },
    
    reset() {
      this.currentState = 'idle';
      this.transitions = [];
    }
  }));

  /**
   * Reasoning Stream Component
   * Displays real-time reasoning output from the agent
   */
  Alpine.data('reasoningStream', (config = {}) => ({
    chunks: [],
    isStreaming: false,
    maxChunks: config.maxChunks || 100,
    autoScroll: config.autoScroll !== false,
    
    addChunk(text, type = 'reasoning') {
      this.chunks.push({
        id: Date.now() + Math.random(),
        text,
        type,
        timestamp: new Date()
      });
      
      // Trim old chunks
      if (this.chunks.length > this.maxChunks) {
        this.chunks = this.chunks.slice(-this.maxChunks);
      }
      
      // Auto-scroll
      if (this.autoScroll) {
        this.$nextTick(() => {
          const container = this.$refs.streamContainer;
          if (container) {
            container.scrollTop = container.scrollHeight;
          }
        });
      }
    },
    
    clear() {
      this.chunks = [];
    },
    
    get fullText() {
      return this.chunks.map(c => c.text).join('');
    },
    
    startStream() {
      this.isStreaming = true;
    },
    
    endStream() {
      this.isStreaming = false;
    }
  }));

  /**
   * Conversation History Component
   * Displays message bubbles for conversation history
   */
  Alpine.data('conversationHistory', (config = {}) => ({
    messages: config.messages || [],
    isLoading: false,
    
    addMessage(role, content, metadata = {}) {
      this.messages.push({
        id: Date.now() + Math.random(),
        role,
        content,
        timestamp: new Date(),
        ...metadata
      });
      
      this.$nextTick(() => {
        const container = this.$refs.messagesContainer;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },
    
    getMessageClass(message) {
      const classes = ['soma-message'];
      classes.push(`soma-message--${message.role}`);
      if (message.isError) classes.push('soma-message--error');
      return classes.join(' ');
    },
    
    getRoleIcon(role) {
      const icons = {
        user: '👤',
        assistant: '🤖',
        system: '⚙️',
        tool: '🔧'
      };
      return icons[role] || '💬';
    },
    
    formatTimestamp(date) {
      return new Date(date).toLocaleTimeString();
    },
    
    clear() {
      this.messages = [];
    }
  }));

  /**
   * Tool Monitor Component
   * Displays tool execution status and history
   */
  Alpine.data('toolMonitor', (config = {}) => ({
    executions: [],
    activeExecution: null,
    maxHistory: config.maxHistory || 50,
    
    startExecution(toolName, args = {}) {
      const execution = {
        id: Date.now() + Math.random(),
        toolName,
        args,
        status: 'running',
        startTime: new Date(),
        endTime: null,
        result: null,
        error: null
      };
      
      this.activeExecution = execution;
      this.executions.unshift(execution);
      
      // Trim history
      if (this.executions.length > this.maxHistory) {
        this.executions = this.executions.slice(0, this.maxHistory);
      }
      
      return execution.id;
    },
    
    completeExecution(id, result) {
      const execution = this.executions.find(e => e.id === id);
      if (execution) {
        execution.status = 'success';
        execution.endTime = new Date();
        execution.result = result;
        if (this.activeExecution?.id === id) {
          this.activeExecution = null;
        }
      }
    },
    
    failExecution(id, error) {
      const execution = this.executions.find(e => e.id === id);
      if (execution) {
        execution.status = 'error';
        execution.endTime = new Date();
        execution.error = error;
        if (this.activeExecution?.id === id) {
          this.activeExecution = null;
        }
      }
    },
    
    getStatusIcon(status) {
      const icons = {
        running: '⏳',
        success: '✅',
        error: '❌'
      };
      return icons[status] || '●';
    },
    
    getStatusClass(status) {
      return `soma-tool-status--${status}`;
    },
    
    getDuration(execution) {
      if (!execution.endTime) {
        return 'Running...';
      }
      const ms = execution.endTime - execution.startTime;
      if (ms < 1000) return `${ms}ms`;
      return `${(ms / 1000).toFixed(1)}s`;
    },
    
    clear() {
      this.executions = [];
      this.activeExecution = null;
    }
  }));

  /**
   * Agent Dashboard Container Component
   * Combines all agent-specific components into a unified dashboard
   */
  Alpine.data('agentDashboard', (config = {}) => ({
    agentId: config.agentId || 'agent-0',
    isConnected: false,
    cognitiveLoad: 0,
    
    init() {
      // Initialize connection status
      this.checkConnection();
    },
    
    async checkConnection() {
      try {
        const response = await fetch('http://localhost:21016/v1/health');
        this.isConnected = response.ok;
      } catch {
        this.isConnected = false;
      }
    },
    
    get connectionStatus() {
      return this.isConnected ? 'connected' : 'disconnected';
    },
    
    get loadLevel() {
      if (this.cognitiveLoad < 0.3) return 'low';
      if (this.cognitiveLoad < 0.7) return 'medium';
      return 'high';
    }
  }));
});
