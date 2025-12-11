/**
 * Onboarding Component
 * Welcome modal, tooltips, and help system
 * Requirements: 27.1, 27.2, 27.3, 27.4, 27.5
 */

/**
 * Onboarding Manager
 */
export class OnboardingManager {
  constructor() {
    this.storageKey = 'onboarding-state';
    this.state = this.loadState();
  }

  /**
   * Load onboarding state from storage
   */
  loadState() {
    try {
      const saved = localStorage.getItem(this.storageKey);
      return saved ? JSON.parse(saved) : {
        completed: false,
        currentStep: 0,
        dismissedTips: [],
        lastVisit: null
      };
    } catch (e) {
      return { completed: false, currentStep: 0, dismissedTips: [], lastVisit: null };
    }
  }

  /**
   * Save onboarding state
   */
  saveState() {
    localStorage.setItem(this.storageKey, JSON.stringify(this.state));
  }

  /**
   * Check if onboarding should be shown
   */
  shouldShowOnboarding() {
    return !this.state.completed;
  }

  /**
   * Mark onboarding as complete
   */
  completeOnboarding() {
    this.state.completed = true;
    this.state.lastVisit = new Date().toISOString();
    this.saveState();
  }

  /**
   * Reset onboarding
   */
  resetOnboarding() {
    this.state = { completed: false, currentStep: 0, dismissedTips: [], lastVisit: null };
    this.saveState();
  }

  /**
   * Dismiss a specific tip
   */
  dismissTip(tipId) {
    if (!this.state.dismissedTips.includes(tipId)) {
      this.state.dismissedTips.push(tipId);
      this.saveState();
    }
  }

  /**
   * Check if a tip was dismissed
   */
  isTipDismissed(tipId) {
    return this.state.dismissedTips.includes(tipId);
  }
}

// Singleton instance
export const onboardingManager = new OnboardingManager();

/**
 * Onboarding Steps Configuration
 */
export const onboardingSteps = [
  {
    id: 'welcome',
    title: 'Welcome to SomaAgent01',
    description: 'Your AI-powered assistant for complex tasks. Let\'s take a quick tour!',
    icon: 'waving_hand',
    target: null
  },
  {
    id: 'chat',
    title: 'Chat Interface',
    description: 'Start conversations with the AI agent. Type your message and press Enter to send.',
    icon: 'chat',
    target: '.chat-input'
  },
  {
    id: 'sidebar',
    title: 'Navigation',
    description: 'Access different features like Memory, Scheduler, and Health from the sidebar.',
    icon: 'menu',
    target: '.app-sidebar'
  },
  {
    id: 'sessions',
    title: 'Chat Sessions',
    description: 'Your conversations are saved as sessions. Click "New Chat" to start fresh.',
    icon: 'folder',
    target: '.session-list'
  },
  {
    id: 'settings',
    title: 'Settings',
    description: 'Configure the agent, API keys, and system preferences in Settings.',
    icon: 'settings',
    target: '[data-action="settings"]'
  },
  {
    id: 'shortcuts',
    title: 'Keyboard Shortcuts',
    description: 'Press ⌘K to open the command palette. Use ⌘N for new chat, ⌘, for settings.',
    icon: 'keyboard',
    target: null
  },
  {
    id: 'complete',
    title: 'You\'re All Set!',
    description: 'Start chatting with SomaAgent01. You can revisit this tour from Settings > Help.',
    icon: 'check_circle',
    target: null
  }
];

/**
 * Contextual Tips Configuration
 */
export const contextualTips = [
  {
    id: 'first-message',
    trigger: 'first-message',
    title: 'Pro Tip',
    message: 'You can use Shift+Enter for multi-line messages.',
    position: 'top'
  },
  {
    id: 'tool-execution',
    trigger: 'tool-started',
    title: 'Tool Execution',
    message: 'The agent is using tools to help with your request. Click to see details.',
    position: 'left'
  },
  {
    id: 'memory-save',
    trigger: 'memory-saved',
    title: 'Memory Saved',
    message: 'The agent saved this information to memory for future reference.',
    position: 'bottom'
  }
];

/**
 * Onboarding Alpine Component
 */
export function createOnboarding() {
  return {
    // State
    isOpen: false,
    currentStep: 0,
    steps: onboardingSteps,
    
    // Computed
    get currentStepData() {
      return this.steps[this.currentStep] || this.steps[0];
    },
    
    get isFirstStep() {
      return this.currentStep === 0;
    },
    
    get isLastStep() {
      return this.currentStep === this.steps.length - 1;
    },
    
    get progress() {
      return ((this.currentStep + 1) / this.steps.length) * 100;
    },
    
    // Lifecycle
    init() {
      if (onboardingManager.shouldShowOnboarding()) {
        // Delay showing onboarding to let app load
        setTimeout(() => {
          this.isOpen = true;
        }, 1000);
      }
    },
    
    // Methods
    open() {
      this.currentStep = 0;
      this.isOpen = true;
    },
    
    close() {
      this.isOpen = false;
    },
    
    next() {
      if (this.currentStep < this.steps.length - 1) {
        this.currentStep++;
        this.highlightTarget();
      } else {
        this.complete();
      }
    },
    
    prev() {
      if (this.currentStep > 0) {
        this.currentStep--;
        this.highlightTarget();
      }
    },
    
    goToStep(index) {
      if (index >= 0 && index < this.steps.length) {
        this.currentStep = index;
        this.highlightTarget();
      }
    },
    
    skip() {
      onboardingManager.completeOnboarding();
      this.close();
    },
    
    complete() {
      onboardingManager.completeOnboarding();
      this.close();
      this.$dispatch('toast', { type: 'success', message: 'Welcome aboard! 🎉' });
    },
    
    highlightTarget() {
      // Remove previous highlights
      document.querySelectorAll('.onboarding-highlight').forEach(el => {
        el.classList.remove('onboarding-highlight');
      });
      
      // Add highlight to current target
      const target = this.currentStepData.target;
      if (target) {
        const el = document.querySelector(target);
        if (el) {
          el.classList.add('onboarding-highlight');
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    }
  };
}

/**
 * Contextual Tip Alpine Component
 */
export function createContextualTip() {
  return {
    isVisible: false,
    tip: null,
    
    show(tipId) {
      const tip = contextualTips.find(t => t.id === tipId);
      if (tip && !onboardingManager.isTipDismissed(tipId)) {
        this.tip = tip;
        this.isVisible = true;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
          this.hide();
        }, 5000);
      }
    },
    
    hide() {
      this.isVisible = false;
    },
    
    dismiss() {
      if (this.tip) {
        onboardingManager.dismissTip(this.tip.id);
      }
      this.hide();
    }
  };
}

/**
 * Help Panel Alpine Component
 */
export function createHelpPanel() {
  return {
    isOpen: false,
    activeSection: 'shortcuts',
    
    sections: [
      { id: 'shortcuts', label: 'Keyboard Shortcuts', icon: 'keyboard' },
      { id: 'features', label: 'Features', icon: 'apps' },
      { id: 'faq', label: 'FAQ', icon: 'help' }
    ],
    
    shortcuts: [
      { keys: ['⌘', 'K'], description: 'Open command palette' },
      { keys: ['⌘', 'N'], description: 'New chat' },
      { keys: ['⌘', ','], description: 'Open settings' },
      { keys: ['⌘', '/'], description: 'Show help' },
      { keys: ['Esc'], description: 'Close modal/panel' },
      { keys: ['Enter'], description: 'Send message' },
      { keys: ['Shift', 'Enter'], description: 'New line in message' },
      { keys: ['↑'], description: 'Previous message (in empty input)' }
    ],
    
    features: [
      { title: 'Chat', description: 'Converse with the AI agent', icon: 'chat' },
      { title: 'Memory', description: 'View and manage agent memories', icon: 'psychology' },
      { title: 'Scheduler', description: 'Schedule automated tasks', icon: 'schedule' },
      { title: 'Health', description: 'Monitor system status', icon: 'monitoring' },
      { title: 'Settings', description: 'Configure agent and system', icon: 'settings' }
    ],
    
    faq: [
      { q: 'How do I start a new conversation?', a: 'Click "New Chat" in the sidebar or press ⌘N.' },
      { q: 'Can I export my chat history?', a: 'Yes, use the export feature in the chat menu.' },
      { q: 'How do I configure API keys?', a: 'Go to Settings > API Keys to add your provider keys.' },
      { q: 'What are memories?', a: 'Memories are facts and solutions the agent learns and recalls.' }
    ],
    
    open() {
      this.isOpen = true;
    },
    
    close() {
      this.isOpen = false;
    },
    
    setSection(section) {
      this.activeSection = section;
    },
    
    restartTour() {
      onboardingManager.resetOnboarding();
      this.close();
      this.$dispatch('onboarding:start');
    }
  };
}

/**
 * Register Alpine components
 */
export function registerOnboardingComponents() {
  if (typeof Alpine !== 'undefined') {
    Alpine.data('onboarding', createOnboarding);
    Alpine.data('contextualTip', createContextualTip);
    Alpine.data('helpPanel', createHelpPanel);
  }
}

export default onboardingManager;
