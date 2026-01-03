# SRS: UI Component Architecture & Permission Patterns

**Document ID:** SA01-SRS-UI-ARCHITECTURE-2025-12-25
**Purpose:** Define reusable UI patterns that reduce code bloat while preserving full permission granularity
**Status:** CANONICAL REFERENCE

---

## 1. Core Principle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PERMISSIONS: Full 78 granular permissions preserved (NO REDUCTION)        │
│  (tenant:create, tenant:delete, agent:configure, infra:ratelimit:edit)     │
├─────────────────────────────────────────────────────────────────────────────┤
│  ROLES: Combine permissions into reusable groups (convenience layer)       │
│  (SysAdmin = all, TenantAdmin = tenant:*, AgentUser = agent:chat)          │
├─────────────────────────────────────────────────────────────────────────────┤
│  UI COMPONENTS: Generic, data-driven, permission-aware                     │
│  (EntityManager checks user permissions dynamically before showing actions)│
└─────────────────────────────────────────────────────────────────────────────┘
```

**Result**: 66 screens → ~15 generic components
**Granularity**: 78 permissions fully preserved

---

## 2. Pattern 1: Generic Entity Manager

One component handles CRUD for ANY entity type:

```typescript
@customElement('entity-manager')
export class EntityManager extends LitElement {
  @property() entity: 'tenant' | 'agent' | 'user' | 'feature' | 'ratelimit';
  @property() apiBase: string;
  @property() columns: ColumnDef[];
  @property() permissions: string[];  // User's actual permissions
  
  render() {
    return html`
      <div class="entity-header">
        <h1>${this.entity}s</h1>
        <!-- Only show Create if user has permission -->
        ${this.hasPermission(`${this.entity}:create`) ? html`
          <button @click=${this.openCreate}>+ Create</button>
        ` : nothing}
      </div>
      
      <data-table
        .data=${this.items}
        .columns=${this.columns}
        .actions=${this.getAvailableActions()}
      />
    `;
  }
  
  private getAvailableActions(): Action[] {
    const actions: Action[] = [];
    if (this.hasPermission(`${this.entity}:view`)) actions.push({ icon: 'visibility', handler: this.view });
    if (this.hasPermission(`${this.entity}:edit`)) actions.push({ icon: 'edit', handler: this.edit });
    if (this.hasPermission(`${this.entity}:delete`)) actions.push({ icon: 'delete', handler: this.delete });
    return actions;
  }
  
  private hasPermission(perm: string): boolean {
    return this.permissions.includes(perm) || this.permissions.includes('*');
  }
}
```

**Usage:**
```html
<entity-manager
  entity="tenant"
  api-base="/api/v2/saas"
  :columns="tenantColumns"
  :permissions="currentUser.permissions"
/>
```

---

## 3. Pattern 2: Settings Inheritance Tree

Three-level settings with cascading overrides:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLATFORM DEFAULTS (God Layer)                                              │
│  └── max_agents: 10                                                         │
│  └── max_voice_minutes: 60                                                  │
│  └── default_llm: gpt-4o                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  TENANT OVERRIDES (Tier-based or custom)                                    │
│  └── max_agents: 50  (inherits rest from Platform)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  AGENT OVERRIDES (Per-agent customization)                                  │
│  └── default_llm: claude-3.5  (inherits rest from Tenant)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Django Model:**
```python
class Setting(models.Model):
    key = models.CharField(max_length=100)
    value = models.JSONField()
    level = models.CharField(choices=['PLATFORM', 'TENANT', 'AGENT'])
    platform = models.ForeignKey('Platform', null=True)
    tenant = models.ForeignKey('Tenant', null=True)
    agent = models.ForeignKey('Agent', null=True)
    
    class Meta:
        unique_together = ['key', 'level', 'platform', 'tenant', 'agent']

def get_effective_setting(key: str, agent_id: UUID) -> Any:
    """Cascade: Agent → Tenant → Platform → Default"""
    agent = Agent.objects.get(id=agent_id)
    
    # Try agent-level
    if (s := Setting.objects.filter(key=key, agent=agent).first()):
        return s.value
    
    # Try tenant-level
    if (s := Setting.objects.filter(key=key, tenant=agent.tenant).first()):
        return s.value
    
    # Platform default
    if (s := Setting.objects.filter(key=key, level='PLATFORM').first()):
        return s.value
    
    return DEFAULTS.get(key)
```

---

## 4. Pattern 3: Dynamic Form Builder

Forms generated from JSON Schema (no hardcoded forms):

```typescript
@customElement('settings-form')
export class SettingsForm extends LitElement {
  @property() schemaUrl: string;  // e.g., /api/v2/schemas/postgresql
  @property() values: Record<string, any>;
  @property() permissions: string[];
  
  @state() schema: JSONSchema;
  
  async connectedCallback() {
    this.schema = await fetch(this.schemaUrl).then(r => r.json());
  }
  
  render() {
    return html`
      <form @submit=${this.save}>
        ${this.schema.properties.map(prop => this.renderField(prop))}
        
        ${this.hasPermission('settings:write') ? html`
          <button type="submit">Save</button>
        ` : html`
          <p class="read-only-notice">View only</p>
        `}
      </form>
    `;
  }
  
  private renderField(prop: SchemaProperty) {
    switch(prop.type) {
      case 'string': return html`<input-text .field=${prop} .value=${this.values[prop.key]}/>`;
      case 'number': return html`<input-number .field=${prop} .value=${this.values[prop.key]}/>`;
      case 'boolean': return html`<input-toggle .field=${prop} .value=${this.values[prop.key]}/>`;
      case 'enum': return html`<input-select .field=${prop} .value=${this.values[prop.key]}/>`;
    }
  }
}
```

**Backend Schema API:**
```python
@router.get("/schemas/{entity}")
def get_schema(entity: str) -> dict:
    """Return JSON Schema from Django model introspection."""
    model = apps.get_model('admin.core', entity.title())
    return model_to_json_schema(model)
```

---

## 5. Pattern 4: Tab-Based Composition

One route, multiple views via tabs:

```typescript
// Instead of 5 routes:
// /platform/infrastructure/database
// /platform/infrastructure/redis
// /platform/infrastructure/temporal
// /platform/infrastructure/health
// /platform/infrastructure/degradation

// One route with tabs:
@customElement('infrastructure-dashboard')
export class InfrastructureDashboard extends LitElement {
  @state() activeTab: 'health' | 'ratelimits' | 'degradation' = 'health';
  
  render() {
    return html`
      <tab-bar .active=${this.activeTab} @change=${(e) => this.activeTab = e.detail}>
        <tab name="health">Service Health</tab>
        <tab name="ratelimits">Rate Limits</tab>
        <tab name="degradation">Degradation Mode</tab>
      </tab-bar>
      
      ${this.activeTab === 'health' ? this.renderHealth() : nothing}
      ${this.activeTab === 'ratelimits' ? this.renderRateLimits() : nothing}
      ${this.activeTab === 'degradation' ? this.renderDegradation() : nothing}
    `;
  }
}
```

**Benefit**: 5 routes → 1 route, 5 components → 1 component with 3 render methods

---

## 6. Pattern 5: Permission-Aware Action Menus

Generic action menu that filters based on permissions:

```typescript
@customElement('action-menu')
export class ActionMenu extends LitElement {
  @property() entity: string;
  @property() entityId: string;
  @property() permissions: string[];
  
  private actions = [
    { key: 'view', icon: 'visibility', label: 'View', permission: ':view' },
    { key: 'edit', icon: 'edit', label: 'Edit', permission: ':edit' },
    { key: 'duplicate', icon: 'content_copy', label: 'Duplicate', permission: ':create' },
    { key: 'delete', icon: 'delete', label: 'Delete', permission: ':delete', danger: true },
    { key: 'suspend', icon: 'pause', label: 'Suspend', permission: ':suspend' },
    { key: 'impersonate', icon: 'person', label: 'Impersonate', permission: ':impersonate' },
  ];
  
  render() {
    const available = this.actions.filter(a => 
      this.permissions.includes(`${this.entity}${a.permission}`)
    );
    
    return html`
      <dropdown-menu>
        ${available.map(a => html`
          <menu-item 
            icon=${a.icon} 
            ?danger=${a.danger}
            @click=${() => this.emit(a.key)}
          >${a.label}</menu-item>
        `)}
      </dropdown-menu>
    `;
  }
}
```

---

## 7. Permission Hierarchy (Preserved Granularity)

```
PLATFORM PERMISSIONS (28)
├── platform:manage           # Full platform control
├── tenant:list               # List all tenants
├── tenant:view               # View tenant details
├── tenant:create             # Create new tenant
├── tenant:edit               # Edit tenant settings
├── tenant:delete             # Delete tenant
├── tenant:suspend            # Suspend tenant
├── tenant:impersonate        # Act as tenant admin
├── tier:list                 # List subscription tiers
├── tier:create               # Create tier
├── tier:edit                 # Modify tier limits
├── tier:delete               # Remove tier
├── billing:view              # View platform revenue
├── billing:refund            # Issue refunds
├── infra:health:view         # View service health
├── infra:ratelimit:view      # View rate limits
├── infra:ratelimit:edit      # Modify rate limits
├── infra:degradation:view    # View degradation status
├── infra:degradation:control # Start/stop monitoring
├── role:list                 # List roles
├── role:create               # Create roles
├── role:edit                 # Modify roles
├── role:delete               # Delete roles
├── permission:view           # Browse SpiceDB
├── audit:view                # View all audit logs
├── feature:manage            # Enable/disable features
├── mcp:manage                # MCP server registry
└── secret:manage             # Platform secrets

TENANT PERMISSIONS (25)
├── tenant:settings           # Tenant settings
├── user:list                 # List tenant users
├── user:invite               # Invite users
├── user:edit                 # Edit user roles
├── user:remove               # Remove users
├── agent:list                # List agents
├── agent:create              # Create agent
├── agent:edit                # Configure agent
├── agent:delete              # Delete agent
├── usage:view                # View usage metrics
├── billing:view              # View invoices
├── billing:pay               # Make payments
├── apikey:list               # List API keys
├── apikey:create             # Generate keys
├── apikey:revoke             # Revoke keys
├── integration:list          # List integrations
├── integration:enable        # Enable integrations
├── integration:configure     # Configure integrations
├── audit:view                # Tenant audit log
├── role:list                 # Tenant roles
├── role:assign               # Assign roles
├── webhook:manage            # Webhook configuration
├── export:data               # Export tenant data
├── mcp:enable                # Enable MCP servers
└── voice:configure           # Voice settings

AGENT PERMISSIONS (25)
├── agent:chat                # Use chat
├── agent:voice               # Use voice
├── agent:memory:read         # Read memories
├── agent:memory:write        # Create memories
├── agent:memory:delete       # Delete memories
├── agent:tool:use            # Use approved tools
├── agent:tool:configure      # Configure tool access
├── agent:settings:view       # View settings
├── agent:settings:edit       # Edit settings
├── agent:model:select        # Choose LLM model
├── agent:persona:edit        # Edit persona
├── agent:context:manage      # Manage context
├── agent:file:upload         # Upload files
├── agent:file:delete         # Delete files
├── agent:image:generate      # Generate images
├── agent:screenshot:capture  # Screen capture
├── agent:diagram:generate    # Generate diagrams
├── agent:code:execute        # Run code
├── agent:web:browse          # Web browsing
├── agent:api:call            # External APIs
├── agent:share               # Share conversations
├── agent:export              # Export data
├── dev:console               # Developer console
├── dev:metrics               # Dev metrics
└── trn:cognitive             # Trainer mode
```

**Total: 78 permissions** → All preserved, UI components just filter based on user's granted permissions.

---

## 8. Implementation Priority

| Phase | Pattern | Components |
|-------|---------|------------|
| **P0** | Tab Composition | ✅ Done (Infrastructure Dashboard) |
| **P1** | Entity Manager | `<entity-manager>` for CRUD screens |
| **P2** | Settings Form | `<settings-form>` with JSON Schema |
| **P3** | Action Menu | `<action-menu>` permission-aware |
| **P4** | Settings Cascade | Django model + API |

---

*Document created: December 25, 2025*
*Maintains full 78-permission granularity while reducing UI code through reusable patterns*
