/**
 * Virtual Scrolling Module
 * Implements virtual scrolling for lists with > 100 items
 * Requirements: 16.4
 */

/**
 * Virtual Scroller for large lists
 * Only renders visible items plus a buffer for smooth scrolling
 */
export class VirtualScroller {
  constructor(options = {}) {
    this.container = options.container;
    this.itemHeight = options.itemHeight || 60;
    this.bufferSize = options.bufferSize || 5;
    this.items = options.items || [];
    this.renderItem = options.renderItem || ((item) => `<div>${item}</div>`);
    this.onScroll = options.onScroll || null;
    
    this.scrollTop = 0;
    this.visibleStart = 0;
    this.visibleEnd = 0;
    this.totalHeight = 0;
    
    this.viewport = null;
    this.content = null;
    this.spacerTop = null;
    this.spacerBottom = null;
    this.itemsContainer = null;
    
    this.rafId = null;
    this.isInitialized = false;
  }

  /**
   * Initialize the virtual scroller
   */
  init() {
    if (this.isInitialized || !this.container) return;
    
    // Create structure
    this.viewport = document.createElement('div');
    this.viewport.className = 'virtual-scroll-viewport';
    this.viewport.style.cssText = 'overflow-y: auto; height: 100%; position: relative;';
    
    this.content = document.createElement('div');
    this.content.className = 'virtual-scroll-content';
    this.content.style.cssText = 'position: relative;';
    
    this.spacerTop = document.createElement('div');
    this.spacerTop.className = 'virtual-scroll-spacer-top';
    
    this.itemsContainer = document.createElement('div');
    this.itemsContainer.className = 'virtual-scroll-items';
    
    this.spacerBottom = document.createElement('div');
    this.spacerBottom.className = 'virtual-scroll-spacer-bottom';
    
    this.content.appendChild(this.spacerTop);
    this.content.appendChild(this.itemsContainer);
    this.content.appendChild(this.spacerBottom);
    this.viewport.appendChild(this.content);
    
    // Clear container and add viewport
    this.container.innerHTML = '';
    this.container.appendChild(this.viewport);
    
    // Bind scroll handler
    this.viewport.addEventListener('scroll', this.handleScroll.bind(this), { passive: true });
    
    this.isInitialized = true;
    this.update();
  }

  /**
   * Handle scroll events with RAF throttling
   */
  handleScroll() {
    if (this.rafId) return;
    
    this.rafId = requestAnimationFrame(() => {
      this.scrollTop = this.viewport.scrollTop;
      this.render();
      this.rafId = null;
      
      if (this.onScroll) {
        this.onScroll({
          scrollTop: this.scrollTop,
          visibleStart: this.visibleStart,
          visibleEnd: this.visibleEnd
        });
      }
    });
  }

  /**
   * Update items and re-render
   * @param {Array} items - New items array
   */
  setItems(items) {
    this.items = items || [];
    this.update();
  }

  /**
   * Update calculations and render
   */
  update() {
    if (!this.isInitialized) return;
    
    this.totalHeight = this.items.length * this.itemHeight;
    this.content.style.height = `${this.totalHeight}px`;
    this.render();
  }

  /**
   * Calculate visible range and render items
   */
  render() {
    if (!this.isInitialized) return;
    
    const viewportHeight = this.viewport.clientHeight;
    const scrollTop = this.scrollTop;
    
    // Calculate visible range
    const startIndex = Math.floor(scrollTop / this.itemHeight);
    const endIndex = Math.min(
      Math.ceil((scrollTop + viewportHeight) / this.itemHeight),
      this.items.length
    );
    
    // Add buffer
    this.visibleStart = Math.max(0, startIndex - this.bufferSize);
    this.visibleEnd = Math.min(this.items.length, endIndex + this.bufferSize);
    
    // Update spacers
    const topSpace = this.visibleStart * this.itemHeight;
    const bottomSpace = (this.items.length - this.visibleEnd) * this.itemHeight;
    
    this.spacerTop.style.height = `${topSpace}px`;
    this.spacerBottom.style.height = `${bottomSpace}px`;
    
    // Render visible items
    const visibleItems = this.items.slice(this.visibleStart, this.visibleEnd);
    const html = visibleItems.map((item, index) => {
      const actualIndex = this.visibleStart + index;
      return this.renderItem(item, actualIndex);
    }).join('');
    
    this.itemsContainer.innerHTML = html;
  }

  /**
   * Scroll to a specific item
   * @param {number} index - Item index to scroll to
   * @param {string} position - 'start', 'center', or 'end'
   */
  scrollToIndex(index, position = 'start') {
    if (!this.isInitialized || index < 0 || index >= this.items.length) return;
    
    let scrollTop;
    const viewportHeight = this.viewport.clientHeight;
    const itemTop = index * this.itemHeight;
    
    switch (position) {
      case 'center':
        scrollTop = itemTop - (viewportHeight / 2) + (this.itemHeight / 2);
        break;
      case 'end':
        scrollTop = itemTop - viewportHeight + this.itemHeight;
        break;
      default: // 'start'
        scrollTop = itemTop;
    }
    
    this.viewport.scrollTop = Math.max(0, scrollTop);
  }

  /**
   * Scroll to bottom (useful for chat)
   * @param {boolean} smooth - Use smooth scrolling
   */
  scrollToBottom(smooth = false) {
    if (!this.isInitialized) return;
    
    if (smooth) {
      this.viewport.scrollTo({
        top: this.totalHeight,
        behavior: 'smooth'
      });
    } else {
      this.viewport.scrollTop = this.totalHeight;
    }
  }

  /**
   * Check if scrolled to bottom
   * @param {number} threshold - Pixels from bottom to consider "at bottom"
   * @returns {boolean}
   */
  isAtBottom(threshold = 50) {
    if (!this.isInitialized) return true;
    
    const scrollBottom = this.scrollTop + this.viewport.clientHeight;
    return scrollBottom >= this.totalHeight - threshold;
  }

  /**
   * Destroy the virtual scroller
   */
  destroy() {
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
    }
    
    if (this.viewport) {
      this.viewport.removeEventListener('scroll', this.handleScroll);
    }
    
    this.isInitialized = false;
  }
}

/**
 * Create a virtual scroller for Alpine.js integration
 */
export function createVirtualScroller(options) {
  return new VirtualScroller(options);
}

/**
 * Alpine.js directive for virtual scrolling
 * Usage: x-virtual-scroll="{ items: messages, itemHeight: 80 }"
 */
export function registerVirtualScrollDirective() {
  if (typeof Alpine === 'undefined') return;
  
  Alpine.directive('virtual-scroll', (el, { expression }, { evaluate, effect, cleanup }) => {
    let scroller = null;
    
    effect(() => {
      const options = evaluate(expression);
      
      if (!scroller) {
        scroller = new VirtualScroller({
          container: el,
          itemHeight: options.itemHeight || 60,
          bufferSize: options.bufferSize || 5,
          items: options.items || [],
          renderItem: options.renderItem || ((item) => `<div>${JSON.stringify(item)}</div>`),
          onScroll: options.onScroll
        });
        scroller.init();
      } else {
        scroller.setItems(options.items || []);
      }
    });
    
    cleanup(() => {
      if (scroller) {
        scroller.destroy();
      }
    });
  });
}

export default VirtualScroller;
