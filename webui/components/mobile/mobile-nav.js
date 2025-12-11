/**
 * Mobile Navigation Component
 * Bottom navigation, touch targets, gesture navigation
 * Requirements: 29.1, 29.2, 29.3, 29.4, 29.5
 */

/**
 * Mobile Navigation Alpine Component
 */
export function createMobileNav() {
  return {
    // State
    activeTab: 'chat',
    isVisible: true,
    lastScrollY: 0,
    
    // Navigation items
    navItems: [
      { id: 'chat', label: 'Chat', icon: 'chat' },
      { id: 'memory', label: 'Memory', icon: 'psychology' },
      { id: 'scheduler', label: 'Tasks', icon: 'schedule' },
      { id: 'health', label: 'Health', icon: 'monitoring' },
      { id: 'settings', label: 'Settings', icon: 'settings' }
    ],
    
    // Lifecycle
    init() {
      // Hide nav on scroll down, show on scroll up
      window.addEventListener('scroll', this.handleScroll.bind(this), { passive: true });
      
      // Handle back button
      window.addEventListener('popstate', this.handlePopState.bind(this));
    },
    
    // Methods
    setTab(tabId) {
      this.activeTab = tabId;
      this.$dispatch('navigate', { view: tabId });
      
      // Update URL without reload
      history.pushState({ tab: tabId }, '', `#${tabId}`);
    },
    
    handleScroll() {
      const currentScrollY = window.scrollY;
      
      if (currentScrollY > this.lastScrollY && currentScrollY > 100) {
        // Scrolling down
        this.isVisible = false;
      } else {
        // Scrolling up
        this.isVisible = true;
      }
      
      this.lastScrollY = currentScrollY;
    },
    
    handlePopState(event) {
      if (event.state?.tab) {
        this.activeTab = event.state.tab;
        this.$dispatch('navigate', { view: event.state.tab });
      }
    }
  };
}

/**
 * Gesture Handler for swipe navigation
 */
export class GestureHandler {
  constructor(element, options = {}) {
    this.element = element;
    this.onSwipeLeft = options.onSwipeLeft || (() => {});
    this.onSwipeRight = options.onSwipeRight || (() => {});
    this.onSwipeUp = options.onSwipeUp || (() => {});
    this.onSwipeDown = options.onSwipeDown || (() => {});
    this.threshold = options.threshold || 50;
    
    this.startX = 0;
    this.startY = 0;
    this.startTime = 0;
    
    this.init();
  }

  init() {
    this.element.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
    this.element.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
  }

  handleTouchStart(e) {
    this.startX = e.touches[0].clientX;
    this.startY = e.touches[0].clientY;
    this.startTime = Date.now();
  }

  handleTouchEnd(e) {
    const endX = e.changedTouches[0].clientX;
    const endY = e.changedTouches[0].clientY;
    const duration = Date.now() - this.startTime;
    
    // Only register swipes that are quick enough
    if (duration > 500) return;
    
    const diffX = endX - this.startX;
    const diffY = endY - this.startY;
    
    // Determine if horizontal or vertical swipe
    if (Math.abs(diffX) > Math.abs(diffY)) {
      // Horizontal swipe
      if (Math.abs(diffX) > this.threshold) {
        if (diffX > 0) {
          this.onSwipeRight();
        } else {
          this.onSwipeLeft();
        }
      }
    } else {
      // Vertical swipe
      if (Math.abs(diffY) > this.threshold) {
        if (diffY > 0) {
          this.onSwipeDown();
        } else {
          this.onSwipeUp();
        }
      }
    }
  }

  destroy() {
    this.element.removeEventListener('touchstart', this.handleTouchStart);
    this.element.removeEventListener('touchend', this.handleTouchEnd);
  }
}

/**
 * Pull to Refresh Component
 */
export function createPullToRefresh() {
  return {
    isPulling: false,
    pullDistance: 0,
    isRefreshing: false,
    threshold: 80,
    startY: 0,
    
    init() {
      const container = this.$refs.container;
      if (!container) return;
      
      container.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
      container.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
      container.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    },
    
    handleTouchStart(e) {
      if (window.scrollY === 0) {
        this.startY = e.touches[0].clientY;
        this.isPulling = true;
      }
    },
    
    handleTouchMove(e) {
      if (!this.isPulling || this.isRefreshing) return;
      
      const currentY = e.touches[0].clientY;
      this.pullDistance = Math.max(0, (currentY - this.startY) * 0.5);
      
      if (this.pullDistance > 0) {
        e.preventDefault();
      }
    },
    
    handleTouchEnd() {
      if (!this.isPulling) return;
      
      if (this.pullDistance >= this.threshold) {
        this.refresh();
      } else {
        this.reset();
      }
    },
    
    async refresh() {
      this.isRefreshing = true;
      this.pullDistance = this.threshold;
      
      try {
        await this.$dispatch('refresh');
      } finally {
        this.isRefreshing = false;
        this.reset();
      }
    },
    
    reset() {
      this.isPulling = false;
      this.pullDistance = 0;
    }
  };
}

/**
 * Mobile Sheet Component (bottom sheet)
 */
export function createMobileSheet() {
  return {
    isOpen: false,
    isDragging: false,
    startY: 0,
    currentY: 0,
    sheetHeight: 0,
    
    open() {
      this.isOpen = true;
      document.body.style.overflow = 'hidden';
      this.$nextTick(() => {
        this.sheetHeight = this.$refs.sheet?.offsetHeight || 0;
      });
    },
    
    close() {
      this.isOpen = false;
      document.body.style.overflow = '';
    },
    
    handleDragStart(e) {
      this.isDragging = true;
      this.startY = e.touches[0].clientY;
      this.currentY = 0;
    },
    
    handleDrag(e) {
      if (!this.isDragging) return;
      
      const diff = e.touches[0].clientY - this.startY;
      this.currentY = Math.max(0, diff);
    },
    
    handleDragEnd() {
      if (!this.isDragging) return;
      
      this.isDragging = false;
      
      // Close if dragged more than 30% of height
      if (this.currentY > this.sheetHeight * 0.3) {
        this.close();
      }
      
      this.currentY = 0;
    },
    
    get transform() {
      return this.currentY > 0 ? `translateY(${this.currentY}px)` : '';
    }
  };
}

/**
 * Register Alpine components
 */
export function registerMobileComponents() {
  if (typeof Alpine !== 'undefined') {
    Alpine.data('mobileNav', createMobileNav);
    Alpine.data('pullToRefresh', createPullToRefresh);
    Alpine.data('mobileSheet', createMobileSheet);
  }
}

export { GestureHandler };
export default createMobileNav;
