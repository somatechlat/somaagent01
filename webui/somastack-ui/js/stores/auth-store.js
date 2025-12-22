/**
 * SomaStack Unified UI Design System - Auth Store
 * 
 * Document ID: SOMASTACK-UI-AUTH-STORE
 * Version: 1.0.0
 * 
 * Alpine.js store for authentication and role-based access control.
 * 
 * Requirements: FR-RBAC-001 through FR-RBAC-008
 */

/**
 * Role permission matrix
 * Requirement: FR-RBAC-001
 */
const ROLE_PERMISSIONS = {
  admin: ['view', 'create', 'edit', 'delete', 'approve', 'admin', 'execute', 'monitor'],
  operator: ['view', 'create', 'edit', 'execute', 'monitor'],
  viewer: ['view', 'monitor']
};

/**
 * Parse JWT token payload
 * Requirement: FR-RBAC-005
 * 
 * @param {string} token - JWT token string
 * @returns {object|null} Parsed payload or null if invalid
 */
function parseJWT(token) {
  if (!token || typeof token !== 'string') {
    return null;
  }
  
  try {
    const parts = token.split('.');
    if (parts.length !== 3) {
      return null;
    }
    
    // Decode base64url payload
    const payload = parts[1];
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.warn('Failed to parse JWT token:', e.message);
    return null;
  }
}

/**
 * Check if token is expired
 * 
 * @param {object} payload - JWT payload
 * @returns {boolean} True if expired
 */
function isTokenExpired(payload) {
  if (!payload || !payload.exp) {
    return false; // No expiry claim, assume valid
  }
  
  const now = Math.floor(Date.now() / 1000);
  return payload.exp < now;
}

/**
 * Register the auth store with Alpine.js
 * 
 * Usage:
 *   Alpine.store('auth').isAdmin
 *   Alpine.store('auth').hasPermission('edit')
 *   x-show="$store.auth.isAdmin"
 */
function registerAuthStore(Alpine) {
  Alpine.store('auth', {
    // State
    isAuthenticated: false,
    role: 'viewer',
    tenantId: null,
    userId: null,
    permissions: [],
    tokenExpiry: null,
    
    /**
     * Initialize store on Alpine start
     */
    init() {
      this.loadFromToken();
      
      // Listen for storage changes (logout in another tab)
      window.addEventListener('storage', (e) => {
        if (e.key === 'soma_token') {
          this.loadFromToken();
        }
      });
    },
    
    /**
     * Load authentication state from JWT token in localStorage
     * Requirement: FR-RBAC-005, FR-RBAC-006
     */
    loadFromToken() {
      const token = localStorage.getItem('soma_token');
      
      if (!token) {
        this.setRole('viewer');
        this.isAuthenticated = false;
        return;
      }
      
      const payload = parseJWT(token);
      
      if (!payload || isTokenExpired(payload)) {
        console.warn('Invalid or expired token, defaulting to viewer');
        this.setRole('viewer');
        this.isAuthenticated = false;
        localStorage.removeItem('soma_token');
        return;
      }
      
      // Extract role from token claims
      // Requirement: FR-RBAC-005
      const role = payload.role || payload.roles?.[0] || 'viewer';
      const validRoles = ['admin', 'operator', 'viewer'];
      
      this.isAuthenticated = true;
      this.role = validRoles.includes(role) ? role : 'viewer';
      this.tenantId = payload.tenant_id || payload.tenantId || null;
      this.userId = payload.sub || payload.user_id || null;
      this.tokenExpiry = payload.exp ? new Date(payload.exp * 1000) : null;
      this.permissions = ROLE_PERMISSIONS[this.role] || [];
    },
    
    /**
     * Set role and update permissions
     * Requirement: FR-RBAC-006
     * 
     * @param {string} role - Role name (admin, operator, viewer)
     */
    setRole(role) {
      const validRoles = ['admin', 'operator', 'viewer'];
      this.role = validRoles.includes(role) ? role : 'viewer';
      this.permissions = ROLE_PERMISSIONS[this.role] || [];
    },
    
    /**
     * Check if user has a specific permission
     * 
     * @param {string} permission - Permission to check
     * @returns {boolean} True if user has permission
     */
    hasPermission(permission) {
      return this.permissions.includes(permission);
    },
    
    /**
     * Check if user has any of the specified permissions
     * 
     * @param {string[]} permissions - Permissions to check
     * @returns {boolean} True if user has any permission
     */
    hasAnyPermission(permissions) {
      return permissions.some(p => this.permissions.includes(p));
    },
    
    /**
     * Check if user has all of the specified permissions
     * 
     * @param {string[]} permissions - Permissions to check
     * @returns {boolean} True if user has all permissions
     */
    hasAllPermissions(permissions) {
      return permissions.every(p => this.permissions.includes(p));
    },
    
    /**
     * Computed: Is user an admin?
     * Requirement: FR-RBAC-002
     */
    get isAdmin() {
      return this.role === 'admin';
    },
    
    /**
     * Computed: Is user an operator or higher?
     * Requirement: FR-RBAC-003
     */
    get isOperator() {
      return this.role === 'operator' || this.role === 'admin';
    },
    
    /**
     * Computed: Is user a viewer only?
     * Requirement: FR-RBAC-004
     */
    get isViewer() {
      return this.role === 'viewer';
    },
    
    /**
     * Login with token
     * 
     * @param {string} token - JWT token
     */
    login(token) {
      localStorage.setItem('soma_token', token);
      this.loadFromToken();
    },
    
    /**
     * Logout and clear state
     * Requirement: SEC-AUTH-003
     */
    logout() {
      localStorage.removeItem('soma_token');
      this.isAuthenticated = false;
      this.setRole('viewer');
      this.tenantId = null;
      this.userId = null;
      this.tokenExpiry = null;
    },
    
    /**
     * Get authorization header for API requests
     * 
     * @returns {object} Headers object with Authorization
     */
    getAuthHeaders() {
      const token = localStorage.getItem('soma_token');
      if (!token) {
        return {};
      }
      return {
        'Authorization': `Bearer ${token}`
      };
    }
  });
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { registerAuthStore, parseJWT, ROLE_PERMISSIONS };
}

// Auto-register if Alpine is available
if (typeof Alpine !== 'undefined') {
  registerAuthStore(Alpine);
}
