/**
 * Avatar Component
 * 
 * User avatar with image, initials, or icon fallback.
 * 
 * Usage:
 * <div x-data="avatar({ name: 'John Doe', src: '/avatar.jpg' })" class="avatar">
 *   <img x-show="hasImage" :src="src" :alt="name" @error="onImageError" />
 *   <span x-show="!hasImage" x-text="initials"></span>
 * </div>
 * 
 * @module components/base/avatar
 */

/**
 * Avatar component factory
 * @param {Object} options - Avatar options
 * @param {string} [options.name=''] - User name for initials
 * @param {string} [options.src=''] - Image source URL
 * @param {string} [options.fallback='?'] - Fallback character
 * @returns {Object} Alpine component data
 */
export default function Avatar(options = {}) {
  return {
    name: options.name ?? '',
    src: options.src ?? '',
    imageError: false,
    
    /**
     * Check if image should be shown
     */
    get hasImage() {
      return this.src && !this.imageError;
    },
    
    /**
     * Generate initials from name
     */
    get initials() {
      if (!this.name) return options.fallback ?? '?';
      
      const parts = this.name.trim().split(/\s+/);
      if (parts.length === 1) {
        return parts[0].charAt(0).toUpperCase();
      }
      return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
    },
    
    /**
     * Handle image load error
     */
    onImageError() {
      this.imageError = true;
    },
    
    /**
     * Update avatar source
     * @param {string} newSrc - New image URL
     */
    setSrc(newSrc) {
      this.src = newSrc;
      this.imageError = false;
    },
    
    /**
     * Update name
     * @param {string} newName - New name
     */
    setName(newName) {
      this.name = newName;
    },
  };
}
