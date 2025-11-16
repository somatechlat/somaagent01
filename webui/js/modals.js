// Import the component loader and page utilities
import { importComponent } from "/js/components.js";
import { handleError, createErrorBoundary } from "/js/error-handling.js";

// Create error boundary for modal system
const modalErrorBoundary = createErrorBoundary('ModalSystem', (errorData) => {
  // Return fallback modal UI
  const fallbackModal = document.createElement('div');
  fallbackModal.className = 'modal-error-fallback';
  fallbackModal.innerHTML = `
    <div class="modal-error-content">
      <h3>Modal Error</h3>
      <p>${errorData.userMessage}</p>
      <button onclick="this.closest('.modal-error-fallback').remove()">Close</button>
    </div>
  `;
  document.body.appendChild(fallbackModal);
  return fallbackModal;
});

// Modal functionality with improved architecture
const modalStack = [];
const modalState = {
  isInitialized: false,
  activeModalCount: 0,
  backdropZIndex: 2999,
  baseModalZIndex: 3000,
  modalSpacing: 20,
  animationDuration: 300
};

// Create a single backdrop for all modals with improved event handling
const backdrop = document.createElement("div");
backdrop.className = "modal-backdrop";
backdrop.style.display = "none";
backdrop.style.backdropFilter = "blur(5px)";
backdrop.style.transition = `opacity ${modalState.animationDuration}ms ease`;
backdrop.style.opacity = "0";

// Improved backdrop click handling with proper event delegation
backdrop.addEventListener("click", (event) => {
  if (event.target === backdrop) {
    closeModal();
  }
});

// Prevent backdrop clicks from bubbling when clicking inside modal
backdrop.addEventListener("mousedown", (event) => {
  if (event.target === backdrop) {
    event.preventDefault();
  }
});

document.body.appendChild(backdrop);

// Enhanced z-index management with proper stacking and animation
function updateModalZIndexes() {
  const { baseModalZIndex, modalSpacing, backdropZIndex, animationDuration } = modalState;
  
  // Update z-index for all modals with proper stacking
  modalStack.forEach((modal, index) => {
    const zIndex = baseModalZIndex + (index * modalSpacing);
    modal.element.style.zIndex = zIndex;
    
    // Add transition for smooth appearance/disappearance
    if (!modal.element.style.transition) {
      modal.element.style.transition = `transform ${animationDuration}ms ease, opacity ${animationDuration}ms ease`;
    }
  });

  // Enhanced backdrop visibility handling with animation
  if (modalStack.length > 0) {
    backdrop.style.display = "block";
    
    // Animate backdrop opacity
    setTimeout(() => {
      backdrop.style.opacity = "1";
    }, 10);
    
    if (modalStack.length > 1) {
      // For multiple modals, position backdrop between the top two
      const topModalIndex = modalStack.length - 1;
      const previousModalZIndex = baseModalZIndex + ((topModalIndex - 1) * modalSpacing);
      backdrop.style.zIndex = previousModalZIndex + (modalSpacing / 2);
    } else {
      // For single modal, position backdrop below it
      backdrop.style.zIndex = backdropZIndex;
    }
  } else {
    // Animate backdrop fade out
    backdrop.style.opacity = "0";
    
    // Hide backdrop after animation completes
    setTimeout(() => {
      if (modalStack.length === 0) {
        backdrop.style.display = "none";
      }
    }, animationDuration);
  }
  
  modalState.activeModalCount = modalStack.length;
}

// Enhanced modal creation with proper error handling and lifecycle management
function createModalElement(name) {
  try {
    // Create modal element with proper attributes
    const newModal = document.createElement("div");
    newModal.className = "modal";
    newModal.modalName = name || `modal-${Date.now()}`; // save name to the object
    newModal.setAttribute("role", "dialog");
    newModal.setAttribute("aria-modal", "true");
    newModal.setAttribute("aria-labelledby", `modal-title-${name}`);
    newModal.tabIndex = -1; // Make focusable
    
    // Add enhanced click handler with proper event delegation
    newModal.addEventListener("click", (event) => {
      // Only close if clicking directly on the modal container, not its content
      if (event.target === newModal) {
        closeModal();
      }
    });

    // Add keyboard event handling for accessibility
    newModal.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeModal();
      }
    });

    // Create enhanced modal structure with proper accessibility
    newModal.innerHTML = `
      <div class="modal-inner">
        <div class="modal-header">
          <h2 class="modal-title" id="modal-title-${name}"></h2>
          <button class="modal-close" aria-label="Close modal">&times;</button>
        </div>
        <div class="modal-scroll">
          <div class="modal-bd"></div>
        </div>
      </div>
    `;

    // Setup close button handler with proper event prevention
    const close_button = newModal.querySelector(".modal-close");
    close_button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      closeModal();
    });

    // Add modal to DOM
    document.body.appendChild(newModal);

    // Initialize modal state
    const modalData = {
      element: newModal,
      title: newModal.querySelector(".modal-title"),
      body: newModal.querySelector(".modal-bd"),
      close: close_button,
      styles: [],
      scripts: [],
      isOpen: true,
      createdAt: Date.now(),
      name: name
    };

    // Show the modal with proper animation
    requestAnimationFrame(() => {
      newModal.classList.add("show");
      newModal.style.opacity = "0";
      newModal.style.transform = "scale(0.9)";
      
      // Trigger animation
      requestAnimationFrame(() => {
        newModal.style.opacity = "1";
        newModal.style.transform = "scale(1)";
      });
    });

    // Update modal z-indexes
    updateModalZIndexes();

    // Focus management for accessibility
    setTimeout(() => {
      if (modalStack.includes(modalData)) {
        newModal.focus();
      }
    }, 100);

    return modalData;
  } catch (error) {
    console.error("Error creating modal element:", error);
    throw new Error(`Failed to create modal: ${error.message}`);
  }
}

// Enhanced modal opening with proper lifecycle management and error handling
export const openModal = modalErrorBoundary.wrapAsync(async function(modalPath, options = {}) {
  try {
    try {
      // Store the currently focused element for later restoration
      const activeElement = document.activeElement;
      if (activeElement) {
        activeElement.setAttribute('data-last-focused', 'true');
      }

      // Create new modal instance with name
      const modalName = options.name || modalPath || `modal-${Date.now()}`;
      const modal = createModalElement(modalName);

      // Set up mutation observer for modal removal detection
      const observer = new MutationObserver((_, obs) => {
        if (!document.contains(modal.element)) {
          obs.disconnect();
          resolve();
        }
      });
      
      observer.observe(document.body, { 
        childList: true, 
        subtree: true 
      });

      // Set loading state with better UX
      modal.body.innerHTML = `
        <div class="modal-loading">
          <div class="loading-spinner"></div>
          <div class="loading-text">Loading ${modalPath}...</div>
        </div>
      `;

      // Add modal to stack immediately for proper state management
      modalStack.push(modal);

      // Handle body overflow for proper modal behavior
      if (modalStack.length === 1) {
        const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth;
        document.body.style.overflow = "hidden";
        document.body.style.paddingRight = `${scrollbarWidth}px`;
      }

      // Use importComponent to load the modal content with enhanced error handling
      const componentPath = modalPath.startsWith('/') ? modalPath.slice(1) : modalPath;

      // Load modal content with proper error handling and timing
      importComponent(componentPath, modal.body)
        .then((doc) => {
          try {
            // Set the title from the document with fallback
            modal.title.innerHTML = (doc && doc.title) || modalPath;
            
            // Apply CSS classes from document if available
            if (doc && doc.html && doc.html.classList) {
              const inner = modal.element.querySelector(".modal-inner");
              if (inner) {
                inner.classList.add(...Array.from(doc.html.classList));
              }
            }
            
            if (doc && doc.body && doc.body.classList) {
              modal.body.classList.add(...Array.from(doc.body.classList));
            }

            // Trigger modal ready event
            modal.element.dispatchEvent(new CustomEvent('modalReady', {
              detail: { modal, path: modalPath }
            }));

            // Focus management for accessibility
            setTimeout(() => {
              if (modal.element && document.contains(modal.element)) {
                modal.element.focus();
                
                // Move focus to first focusable element if available
                const firstFocusable = modal.element.querySelector(
                  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                if (firstFocusable) {
                  firstFocusable.focus();
                }
              }
            }, 100);

          } catch (renderError) {
            console.error('Error rendering modal content:', renderError);
            modal.body.innerHTML = `
              <div class="modal-error">
                <div class="error-title">Rendering Error</div>
                <div class="error-message">Failed to render modal content: ${renderError.message}</div>
              </div>
            `;
          }
        })
        .catch((error) => {
          console.error("Error loading modal content:", error);
          modal.body.innerHTML = `
            <div class="modal-error">
              <div class="error-title">Loading Error</div>
              <div class="error-message">Failed to load modal content: ${error.message}</div>
              <button class="error-retry" onclick="openModal('${modalPath}')">Retry</button>
            </div>
          `;
          
          // Reject promise if modal loading fails critically
          if (options.rejectOnError) {
            reject(error);
          }
        })
        .finally(() => {
          // Update modal z-indexes regardless of load outcome
          updateModalZIndexes();
        });

    } catch (error) {
      await handleError(error, {
        component: 'ModalSystem',
        function: 'openModal',
        modalPath,
        options: JSON.stringify(options)
      });
      throw error;
    }
  });

// Enhanced modal close function with proper lifecycle management
export function closeModal(modalName = null) {
  if (modalStack.length === 0) return;

  try {
    let modalIndex = modalStack.length - 1; // Default to last modal
    let modal;

    if (modalName) {
      // Find the modal with the specified name in the stack
      modalIndex = modalStack.findIndex((modal) => modal.name === modalName);
      if (modalIndex === -1) return; // Modal not found in stack

      // Get the modal from stack at the found index
      modal = modalStack[modalIndex];
      // Remove the modal from stack
      modalStack.splice(modalIndex, 1);
    } else {
      // Just remove the last modal
      modal = modalStack.pop();
    }

    if (!modal || !modal.element) {
      console.warn('Invalid modal object or element');
      return;
    }

    // Mark modal as closing
    modal.isOpen = false;

    // Remove modal-specific styles and scripts with proper cleanup
    try {
      if (Array.isArray(modal.styles)) {
        modal.styles.forEach((styleId) => {
          const styleElement = document.querySelector(`[data-modal-style="${styleId}"]`);
          if (styleElement) {
            styleElement.remove();
          }
        });
      }
      if (Array.isArray(modal.scripts)) {
        modal.scripts.forEach((scriptId) => {
          const scriptElement = document.querySelector(`[data-modal-script="${scriptId}"]`);
          if (scriptElement) {
            scriptElement.remove();
          }
        });
      }
    } catch (cleanupError) {
      console.warn('Error cleaning up modal resources:', cleanupError);
    }

    // Animate modal closure
    modal.element.style.opacity = "0";
    modal.element.style.transform = "scale(0.9)";
    modal.element.classList.remove("show");

    // Remove the modal element from DOM after animation completes
    const removeModalElement = () => {
      try {
        if (modal.element && modal.element.parentNode) {
          modal.element.parentNode.removeChild(modal.element);
        }
      } catch (removeError) {
        console.warn('Error removing modal element from DOM:', removeError);
      }
    };

    // Use transitionend event for proper animation completion
    const transitionHandler = (event) => {
      if (event.propertyName === 'opacity') {
        modal.element.removeEventListener('transitionend', transitionHandler);
        removeModalElement();
      }
    };

    modal.element.addEventListener('transitionend', transitionHandler, { once: true });

    // Fallback timeout in case transition doesn't fire
    const fallbackTimeout = setTimeout(() => {
      modal.element.removeEventListener('transitionend', transitionHandler);
      removeModalElement();
    }, modalState.animationDuration + 100);

    // Handle backdrop visibility and body overflow
    if (modalStack.length === 0) {
      // No modals left - restore normal state
      document.body.style.overflow = "";
      document.body.style.paddingRight = ""; // Remove potential scrollbar compensation
      
      // Return focus to the element that opened the modal
      const lastFocusedElement = document.querySelector('[data-last-focused]');
      if (lastFocusedElement) {
        lastFocusedElement.focus();
        lastFocusedElement.removeAttribute('data-last-focused');
      }
    } else {
      // Return focus to the previous modal
      if (modalStack.length > 0) {
        const previousModal = modalStack[modalStack.length - 1];
        if (previousModal && previousModal.element) {
          previousModal.element.focus();
        }
      }
    }

    // Update modal z-indexes after state change
    updateModalZIndexes();

    // Clear the fallback timeout if modal was removed successfully
    modal.element.addEventListener('transitionend', () => {
      clearTimeout(fallbackTimeout);
    }, { once: true });

  } catch (error) {
    console.error('Error closing modal:', error);
    // Fallback: force cleanup if something went wrong
    try {
      modalStack.forEach(modal => {
        if (modal.element && modal.element.parentNode) {
          modal.element.parentNode.removeChild(modal.element);
        }
      });
      modalStack.length = 0;
      updateModalZIndexes();
      document.body.style.overflow = "";
    } catch (fallbackError) {
      console.error('Fallback cleanup failed:', fallbackError);
    }
  }
}

// Function to scroll to element by ID within the last modal
export function scrollModal(id) {
  if (!id) return;

  // Get the last modal in the stack
  const lastModal = modalStack[modalStack.length - 1].element;
  if (!lastModal) return;

  // Find the modal container and target element
  const modalContainer = lastModal.querySelector(".modal-scroll");
  const targetElement = lastModal.querySelector(`#${id}`);

  if (modalContainer && targetElement) {
    modalContainer.scrollTo({
      top: targetElement.offsetTop - 20, // 20px padding from top
      behavior: "smooth",
    });
  }
}

// Make scrollModal globally available
globalThis.scrollModal = scrollModal;

// Handle modal content loading from clicks
document.addEventListener("click", async (e) => {
  const modalTrigger = e.target.closest("[data-modal-content]");
  if (modalTrigger) {
    e.preventDefault();
    if (
      modalTrigger.hasAttribute("disabled") ||
      modalTrigger.classList.contains("disabled")
    ) {
      return;
    }
    const modalPath = modalTrigger.getAttribute("href");
    await openModal(modalPath);
  }
});

// Close modal on escape key (closes only the top modal)
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && modalStack.length > 0) {
    closeModal();
  }
});

// also export as global function
globalThis.openModal = openModal;
globalThis.closeModal = closeModal;
globalThis.scrollModal = scrollModal;
