/**
 * SomaStack UI - Sidebar Navigation Component
 * Version: 1.0.0
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('sidebarNav', (config = {}) => ({
    isCollapsed: false,
    activeItem: null,
    
    navGroups: config.navGroups || [],
    
    init() {
      this.loadState();
      this.setActiveFromUrl();
      
      // Listen for navigation changes
      window.addEventListener('popstate', () => this.setActiveFromUrl());
    },
    
    loadState() {
      const saved = localStorage.getItem('soma_sidebar_collapsed');
      if (saved !== null) {
        this.isCollapsed = saved === 'true';
      }
    },
    
    saveState() {
      localStorage.setItem('soma_sidebar_collapsed', this.isCollapsed.toString());
    },
    
    toggleCollapse() {
      this.isCollapsed = !this.isCollapsed;
      this.saveState();
    },
    
    expand() {
      this.isCollapsed = false;
      this.saveState();
    },
    
    collapse() {
      this.isCollapsed = true;
      this.saveState();
    },
    
    setActiveFromUrl() {
      const path = window.location.pathname;
      
      for (const group of this.navGroups) {
        for (const item of group.items || []) {
          if (item.href === path || (item.match && path.startsWith(item.match))) {
            this.activeItem = item.id;
            return;
          }
        }
      }
    },
    
    isActive(item) {
      return this.activeItem === item.id;
    },
    
    hasPermission(permission) {
      if (!permission) return true;
      return Alpine.store('auth').hasPermission(permission);
    },
    
    navigate(item) {
      if (item.href) {
        this.activeItem = item.id;
        
        if (item.external) {
          window.open(item.href, '_blank');
        } else {
          window.location.href = item.href;
        }
      }
      
      if (item.action && typeof item.action === 'function') {
        item.action();
      }
    },
    
    // Keyboard navigation
    handleKeydown(event, item, groupIndex, itemIndex) {
      const group = this.navGroups[groupIndex];
      const items = group?.items || [];
      
      switch (event.key) {
        case 'Enter':
        case ' ':
          event.preventDefault();
          this.navigate(item);
          break;
          
        case 'ArrowDown':
          event.preventDefault();
          this.focusNextItem(groupIndex, itemIndex);
          break;
          
        case 'ArrowUp':
          event.preventDefault();
          this.focusPrevItem(groupIndex, itemIndex);
          break;
      }
    },
    
    focusNextItem(groupIndex, itemIndex) {
      const group = this.navGroups[groupIndex];
      const items = group?.items || [];
      
      if (itemIndex < items.length - 1) {
        this.$refs[`nav-item-${groupIndex}-${itemIndex + 1}`]?.focus();
      } else if (groupIndex < this.navGroups.length - 1) {
        this.$refs[`nav-item-${groupIndex + 1}-0`]?.focus();
      }
    },
    
    focusPrevItem(groupIndex, itemIndex) {
      if (itemIndex > 0) {
        this.$refs[`nav-item-${groupIndex}-${itemIndex - 1}`]?.focus();
      } else if (groupIndex > 0) {
        const prevGroup = this.navGroups[groupIndex - 1];
        const prevItems = prevGroup?.items || [];
        this.$refs[`nav-item-${groupIndex - 1}-${prevItems.length - 1}`]?.focus();
      }
    }
  }));
});
