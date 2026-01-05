/**
 * Permission Guard - Frontend Permission Enforcement
 * Implements route guards and action guards per SRS-PERMISSION-JOURNEYS.md
 *
 * VIBE COMPLIANT:
 * - TypeScript implementation
 * - Uses JWT claims from localStorage
 * - Supports wildcard (*) for super admin
 *
 * 7-Persona Implementation:
 * - 🔒 Security Auditor: Client-side checks (defense in depth)
 * - 📈 PM: UI conditional rendering
 */

// =============================================================================
// PERMISSION CONSTANTS (per SRS Section 1)
// =============================================================================

export const PERMISSIONS = {
    // Platform
    PLATFORM_MANAGE: 'platform:manage',
    PLATFORM_READ_METRICS: 'platform:read_metrics',
    PLATFORM_MANAGE_BILLING: 'platform:manage_billing',
    PLATFORM_MANAGE_FEATURES: 'platform:manage_features',
    PLATFORM_IMPERSONATE: 'platform:impersonate',

    // Tenant
    TENANT_CREATE: 'tenant:create',
    TENANT_READ: 'tenant:read',
    TENANT_UPDATE: 'tenant:update',
    TENANT_DELETE: 'tenant:delete',
    TENANT_SUSPEND: 'tenant:suspend',

    // User
    USER_CREATE: 'user:create',
    USER_READ: 'user:read',
    USER_UPDATE: 'user:update',
    USER_DELETE: 'user:delete',
    USER_ASSIGN_ROLES: 'user:assign_roles',

    // Agent
    AGENT_CREATE: 'agent:create',
    AGENT_READ: 'agent:read',
    AGENT_UPDATE: 'agent:update',
    AGENT_DELETE: 'agent:delete',
    AGENT_START: 'agent:start',
    AGENT_STOP: 'agent:stop',
    AGENT_CONFIGURE_PERSONALITY: 'agent:configure_personality',
    AGENT_CONFIGURE_TOOLS: 'agent:configure_tools',
    AGENT_VIEW_LOGS: 'agent:view_logs',

    // Conversation
    CONVERSATION_CREATE: 'conversation:create',
    CONVERSATION_READ: 'conversation:read',
    CONVERSATION_DELETE: 'conversation:delete',
    CONVERSATION_SEND_MESSAGE: 'conversation:send_message',
    CONVERSATION_EXPORT: 'conversation:export',

    // Memory
    MEMORY_READ: 'memory:read',
    MEMORY_SEARCH: 'memory:search',
    MEMORY_DELETE: 'memory:delete',
    MEMORY_EXPORT: 'memory:export',

    // Infrastructure
    INFRA_VIEW: 'infra:view',
    INFRA_CONFIGURE: 'infra:configure',
    INFRA_RATELIMIT: 'infra:ratelimit',

    // Audit
    AUDIT_READ: 'audit:read',
    AUDIT_EXPORT: 'audit:export',

    // Billing
    BILLING_VIEW_INVOICES: 'billing:view_invoices',
    BILLING_VIEW_USAGE: 'billing:view_usage',
    BILLING_CHANGE_PLAN: 'billing:change_plan',
} as const;


// =============================================================================
// ROUTE → PERMISSION MAPPING (per SRS Section 2-4)
// =============================================================================

export const ROUTE_PERMISSIONS: Record<string, string[]> = {
    // Platform Admin
    '/platform': [PERMISSIONS.PLATFORM_READ_METRICS],
    '/platform/tenants': [PERMISSIONS.TENANT_READ],
    '/platform/tenants/new': [PERMISSIONS.TENANT_CREATE],
    '/platform/subscriptions': [PERMISSIONS.PLATFORM_MANAGE_BILLING],
    '/platform/permissions': [PERMISSIONS.PLATFORM_MANAGE],
    '/platform/roles': [PERMISSIONS.PLATFORM_MANAGE],
    '/platform/role-matrix': [PERMISSIONS.PLATFORM_MANAGE],
    '/platform/infrastructure': [PERMISSIONS.INFRA_VIEW],
    '/platform/metrics': [PERMISSIONS.PLATFORM_READ_METRICS],
    '/platform/features': [PERMISSIONS.PLATFORM_MANAGE_FEATURES],
    '/platform/audit': [PERMISSIONS.AUDIT_READ],
    '/platform/integrations': [PERMISSIONS.PLATFORM_MANAGE],
    '/platform/tiers': [PERMISSIONS.PLATFORM_MANAGE_BILLING],
    '/platform/usage': [PERMISSIONS.PLATFORM_READ_METRICS],

    // Tenant Admin
    '/admin': [PERMISSIONS.TENANT_READ],
    '/admin/users': [PERMISSIONS.USER_READ],
    '/admin/agents': [PERMISSIONS.AGENT_READ],
    '/admin/usage': [PERMISSIONS.BILLING_VIEW_USAGE],
    '/admin/billing': [PERMISSIONS.BILLING_VIEW_INVOICES],
    '/admin/settings': [PERMISSIONS.TENANT_UPDATE],
    '/admin/audit': [PERMISSIONS.AUDIT_READ],

    // Agent User
    '/chat': [PERMISSIONS.CONVERSATION_READ],
    '/memory': [PERMISSIONS.MEMORY_READ],
    '/settings': [PERMISSIONS.AGENT_READ],
    '/profile': [PERMISSIONS.USER_READ],
};


// =============================================================================
// ACTION → PERMISSION MAPPING (per SRS Section 9.2)
// =============================================================================

export const ACTION_PERMISSIONS: Record<string, string> = {
    // Tenant actions
    create_tenant: PERMISSIONS.TENANT_CREATE,
    delete_tenant: PERMISSIONS.TENANT_DELETE,
    suspend_tenant: PERMISSIONS.TENANT_SUSPEND,

    // User actions
    invite_user: PERMISSIONS.USER_CREATE,
    delete_user: PERMISSIONS.USER_DELETE,
    assign_role: PERMISSIONS.USER_ASSIGN_ROLES,

    // Agent actions
    create_agent: PERMISSIONS.AGENT_CREATE,
    delete_agent: PERMISSIONS.AGENT_DELETE,
    start_agent: PERMISSIONS.AGENT_START,
    stop_agent: PERMISSIONS.AGENT_STOP,

    // Infrastructure actions
    configure_ratelimits: PERMISSIONS.INFRA_RATELIMIT,
    configure_services: PERMISSIONS.INFRA_CONFIGURE,

    // Billing actions
    change_plan: PERMISSIONS.BILLING_CHANGE_PLAN,

    // Export actions
    export_audit: PERMISSIONS.AUDIT_EXPORT,
    export_conversation: PERMISSIONS.CONVERSATION_EXPORT,
    export_memory: PERMISSIONS.MEMORY_EXPORT,
};


// =============================================================================
// PERMISSION UTILITIES
// =============================================================================

/**
 * Get user permissions from JWT in localStorage.
 */
export function getUserPermissions(): string[] {
    try {
        const token = localStorage.getItem('auth_token') || localStorage.getItem('saas_auth_token');
        if (!token) return [];

        // Decode JWT payload
        const parts = token.split('.');
        if (parts.length !== 3) return [];

        const payload = JSON.parse(atob(parts[1]));
        return payload.permissions || [];
    } catch {
        return [];
    }
}

/**
 * Check if user has a specific permission.
 */
export function hasPermission(permission: string): boolean {
    const permissions = getUserPermissions();
    return permissions.includes('*') || permissions.includes(permission);
}

/**
 * Check if user has any of the specified permissions.
 */
export function hasAnyPermission(...permissions: string[]): boolean {
    const userPerms = getUserPermissions();
    if (userPerms.includes('*')) return true;
    return permissions.some(p => userPerms.includes(p));
}

/**
 * Check if user has all of the specified permissions.
 */
export function hasAllPermissions(...permissions: string[]): boolean {
    const userPerms = getUserPermissions();
    if (userPerms.includes('*')) return true;
    return permissions.every(p => userPerms.includes(p));
}

/**
 * Check if user can access a route.
 */
export function canAccessRoute(route: string): boolean {
    const required = ROUTE_PERMISSIONS[route];
    if (!required) return true; // No permission required

    const userPerms = getUserPermissions();
    if (userPerms.includes('*')) return true;

    return required.some(p => userPerms.includes(p));
}

/**
 * Check if user can perform an action.
 */
export function canPerformAction(action: string): boolean {
    const required = ACTION_PERMISSIONS[action];
    if (!required) return true; // No permission required

    return hasPermission(required);
}

/**
 * Filter navigation items based on permissions.
 */
export function filterNavigationByPermissions<T extends { route: string }>(
    items: T[]
): T[] {
    return items.filter(item => canAccessRoute(item.route));
}

/**
 * Get current user's role name from JWT.
 */
export function getUserRole(): string | null {
    try {
        const token = localStorage.getItem('auth_token');
        if (!token) return null;

        const parts = token.split('.');
        if (parts.length !== 3) return null;

        const payload = JSON.parse(atob(parts[1]));
        return payload.role || payload.role_name || null;
    } catch {
        return null;
    }
}

/**
 * Check if user is a super admin.
 */
export function isSuperAdmin(): boolean {
    return hasPermission('*') || getUserRole() === 'saas_super_admin';
}

/**
 * Check if user is a tenant admin.
 */
export function isTenantAdmin(): boolean {
    const role = getUserRole();
    return role === 'tenant_admin' || isSuperAdmin();
}


// =============================================================================
// ROUTE GUARD (for routing)
// =============================================================================

/**
 * Route check - returns true if allowed, false otherwise.
 * Use in router beforeEnter guards.
 */
export function checkRoutePermission(route: string): { allowed: boolean; redirect?: string } {
    if (canAccessRoute(route)) {
        return { allowed: true };
    }

    // Determine fallback based on route
    if (route.startsWith('/platform')) {
        return { allowed: false, redirect: '/login' };
    }
    if (route.startsWith('/admin')) {
        return { allowed: false, redirect: '/403' };
    }

    return { allowed: false, redirect: '/403' };
}
