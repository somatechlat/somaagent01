/**
 * Image Renderer Component
 *
 * Renders images with thumbnails and lightbox for full-size view.
 *
 * @module components/chat/image-renderer
 */

/**
 * Image Renderer component factory
 * @param {Object} options - Component options
 * @param {string} options.src - Image source URL
 * @param {string} [options.alt] - Alt text
 * @param {string} [options.caption] - Image caption
 * @param {number} [options.thumbnailWidth=200] - Thumbnail width
 * @param {number} [options.thumbnailHeight=150] - Thumbnail height
 * @returns {Object} Alpine component data
 */
export default function ImageRenderer(options = {}) {
  return {
    src: options.src ?? '',
    alt: options.alt ?? 'Image',
    caption: options.caption ?? '',
    thumbnailWidth: options.thumbnailWidth ?? 200,
    thumbnailHeight: options.thumbnailHeight ?? 150,

    // UI state
    isLightboxOpen: false,
    isLoading: true,
    hasError: false,
    naturalWidth: 0,
    naturalHeight: 0,

    /**
     * Handle image load
     * @param {Event} event - Load event
     */
    onLoad(event) {
      this.isLoading = false;
      this.hasError = false;
      this.naturalWidth = event.target.naturalWidth;
      this.naturalHeight = event.target.naturalHeight;
    },

    /**
     * Handle image error
     */
    onError() {
      this.isLoading = false;
      this.hasError = true;
    },

    /**
     * Open lightbox
     */
    openLightbox() {
      if (this.hasError) return;
      this.isLightboxOpen = true;
      document.body.style.overflow = 'hidden';
    },

    /**
     * Close lightbox
     */
    closeLightbox() {
      this.isLightboxOpen = false;
      document.body.style.overflow = '';
    },


    /**
     * Handle keyboard events in lightbox
     * @param {KeyboardEvent} event - Keyboard event
     */
    onKeydown(event) {
      if (event.key === 'Escape') {
        this.closeLightbox();
      }
    },

    /**
     * Get thumbnail style
     */
    get thumbnailStyle() {
      return {
        maxWidth: `${this.thumbnailWidth}px`,
        maxHeight: `${this.thumbnailHeight}px`,
      };
    },

    /**
     * Get image dimensions text
     */
    get dimensionsText() {
      if (!this.naturalWidth || !this.naturalHeight) return '';
      return `${this.naturalWidth} × ${this.naturalHeight}`;
    },

    /**
     * Bind for thumbnail container
     */
    get thumbnailContainer() {
      return {
        '@click': () => this.openLightbox(),
        ':class': () => ({
          'image-thumbnail': true,
          'image-loading': this.isLoading,
          'image-error': this.hasError,
          'cursor-pointer': !this.hasError,
        }),
        ':style': () => this.thumbnailStyle,
      };
    },

    /**
     * Bind for thumbnail image
     */
    get thumbnailImage() {
      return {
        ':src': () => this.src,
        ':alt': () => this.alt,
        '@load': (e) => this.onLoad(e),
        '@error': () => this.onError(),
        ':style': () => this.thumbnailStyle,
      };
    },

    /**
     * Bind for lightbox backdrop
     */
    get lightboxBackdrop() {
      return {
        'x-show': () => this.isLightboxOpen,
        'x-transition:enter': 'transition ease-out duration-200',
        'x-transition:enter-start': 'opacity-0',
        'x-transition:enter-end': 'opacity-100',
        'x-transition:leave': 'transition ease-in duration-150',
        'x-transition:leave-start': 'opacity-100',
        'x-transition:leave-end': 'opacity-0',
        '@click.self': () => this.closeLightbox(),
        '@keydown.escape.window': () => this.closeLightbox(),
        class: 'lightbox-backdrop',
      };
    },

    /**
     * Bind for lightbox image
     */
    get lightboxImage() {
      return {
        ':src': () => this.src,
        ':alt': () => this.alt,
        'x-show': () => this.isLightboxOpen,
        'x-transition:enter': 'transition ease-out duration-200',
        'x-transition:enter-start': 'opacity-0 scale-95',
        'x-transition:enter-end': 'opacity-100 scale-100',
        'x-transition:leave': 'transition ease-in duration-150',
        'x-transition:leave-start': 'opacity-100 scale-100',
        'x-transition:leave-end': 'opacity-0 scale-95',
        class: 'lightbox-image',
      };
    },

    /**
     * Bind for close button
     */
    get closeButton() {
      return {
        '@click': () => this.closeLightbox(),
        'aria-label': 'Close lightbox',
        class: 'lightbox-close',
      };
    },

    /**
     * Download image
     */
    async downloadImage() {
      try {
        const response = await fetch(this.src);
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.alt || 'image';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Failed to download image:', err);
      }
    },
  };
}
