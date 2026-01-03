# SRS: System Architecture — UI and Backend Layers

**Document ID:** SA01-SRS-ARCHITECTURE-2025-12
**Purpose:** Clarify how Custom UI, Django Ninja API, and Django Admin relate
**Status:** CANONICAL REFERENCE

---

## 1. The Question

> "Can our custom UIs run on top of Django Admin infrastructure?"

**Answer: YES and NO. Let me explain step-by-step.**

---

## 2. Step-by-Step Architecture Breakdown

### Step 1: What is the DATABASE Layer?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PostgreSQL Database                               │
│                                                                             │
│   Tables: tenants, agents, users, features, tiers, usage_records, etc.      │
│                                                                             │
│   This is the SINGLE SOURCE OF TRUTH for all data.                          │
│   EVERYTHING reads and writes here.                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 2: What is the Django ORM Layer?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Django ORM                                     │
│                                                                             │
│   Models: Tenant, Agent, SubscriptionTier, SaasFeature, etc.               │
│                                                                             │
│   This is the PYTHON INTERFACE to the database.                             │
│   ALL Python code uses this to read/write data.                             │
│                                                                             │
│   Location: admin/saas/models/, admin/permissions/models.py, etc.           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 3: What are the TWO Entry Points?

There are **TWO SEPARATE** ways to access this ORM:

```
                    ┌───────────────────┐
                    │   PostgreSQL DB   │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
                    │    Django ORM     │
                    └─────────┬─────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Django Admin   │ │ Django Ninja    │ │ Django Commands │
│  (Built-in UI)  │ │ (REST API)      │ │ (CLI)           │
│  /django-admin/ │ │ /api/v2/*       │ │ manage.py       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
          │                   │
          │                   │
          ▼                   ▼
┌─────────────────┐ ┌─────────────────┐
│ Django Admin UI │ │ Custom UI (Lit) │
│ (Auto-generated)│ │ (Our branded UI)│
│ Session Auth    │ │ Calls API       │
└─────────────────┘ └─────────────────┘
```

---

## 3. Entry Point #1: Django Admin

**What it is:**
- Built-in Django feature
- Auto-generates CRUD forms for registered models
- Lives at `/django-admin/`

**How it works:**
```
Browser → /django-admin/ → Django Admin Views → Django ORM → PostgreSQL
```

**Authentication:**
- Django session-based auth
- Requires `is_staff=True` or `is_superuser=True`
- Direct login at `/django-admin/login/`

**What it looks like:**
- Generic table views
- Auto-generated forms
- No branding, no custom UI

**Who uses it:**
- **Infrastructure operators** (DevOps)
- **Emergency access** (bypass custom UI if broken)
- **Database seed/migrations** (initial setup)

**Registered in:**
```python
# admin/saas/admin.py
@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'tier', 'status']
    ...
```

---

## 4. Entry Point #2: Django Ninja API + Custom UI

**What it is:**
- REST API built with Django Ninja
- Custom Lit web components for UI
- Our branded, designed experience

**How it works:**
```
Browser → Custom UI (Lit) → HTTP Fetch → Django Ninja API → Django ORM → PostgreSQL
            (localhost:5173)              (/api/v2/*)
```

**Authentication:**
- JWT tokens from Keycloak
- AuthBearer middleware
- Multi-tenant context injection

**What it looks like:**
- Our designed screens
- Branded experience
- Role-based access

**Who uses it:**
- **SAAS Admins** (Platform management)
- **Tenant Admins** (Organization management)
- **End Users** (Chat, memory, etc.)

---

## 5. How They Share the Same Infrastructure

### Shared Components:

| Component | Used By Django Admin | Used By Custom UI |
|-----------|---------------------|-------------------|
| PostgreSQL Database | ✅ YES | ✅ YES |
| Django ORM Models | ✅ YES | ✅ YES (via API) |
| Django Settings | ✅ YES | ✅ YES |
| Django Middleware | ⚠️ SOME | ✅ YES |
| Django Templates | ✅ YES (admin templates) | ❌ NO |
| Lit Components | ❌ NO | ✅ YES |
| Django Ninja Routers | ❌ NO | ✅ YES |
| Keycloak Auth | ❌ NO (uses session) | ✅ YES |

### Different Components:

| Aspect | Django Admin | Custom UI |
|--------|--------------|-----------|
| Auth System | Django Sessions | Keycloak JWT |
| UI Framework | Django Templates | Lit Web Components |
| URL Prefix | `/django-admin/` | `/saas/*`, `/admin/*`, `/chat/*` |
| Purpose | Infrastructure access | User-facing application |
| Customization | Limited | Full control |

---

## 6. The ACTUAL Flow (Step by Step)

### Scenario: SAAS Admin views tenant list

**Using Django Admin:**
```
1. Admin goes to http://localhost:8000/django-admin/
2. Django checks session cookie
3. Admin sees auto-generated Tenant table
4. Clicks on tenant → sees auto-generated form
5. Saves → Django ORM writes to PostgreSQL
```

**Using Custom UI:**
```
1. Admin goes to http://localhost:5173/platform/tenants
2. Lit component mounts
3. Component calls: fetch('/api/v2/saas/tenants')
4. Django Ninja checks JWT token (Keycloak)
5. Django Ninja uses ORM to query tenants
6. Returns JSON to Lit component
7. Component renders our designed table
```

---

## 7. Why Have Both?

| Use Case | Best Entry Point | Reason |
|----------|------------------|--------|
| Emergency database fix | Django Admin | Direct model access |
| Normal platform operation | Custom UI | Designed experience |
| Superuser creates first tenant | Django Admin | No UI yet |
| Daily tenant management | Custom UI | Full features |
| Debug database values | Django Admin | Raw data view |
| User-facing features | Custom UI | Branded, validated |

---

## 8. Current Implementation Status

### Django Admin (Ready):
- ✅ All models registered in `admin/saas/admin.py`
- ✅ Superuser can access at `/django-admin/`
- ✅ CRUD for all tables works

### Custom UI (Partially Implemented):
- ✅ Platform Dashboard (`/saas/dashboard`)
- ✅ Tenant List (`/platform/tenants`)
- ✅ Subscription Tiers (`/saas/subscriptions`)
- ⚠️ Permission Browser (`/platform/permissions`) - NEEDS IMPLEMENTATION
- ⚠️ Role Builder (`/platform/roles`) - NEEDS IMPLEMENTATION
- ⚠️ Feature Catalog (`/platform/features`) - NEEDS IMPLEMENTATION

### Django Ninja API (Ready):
- ✅ 62 routers mounted in `admin/api.py`
- ✅ 80+ endpoints available
- ✅ AuthBearer middleware working

---

## 9. Summary: The Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER'S BROWSER                                     │
├──────────────────────────────┬──────────────────────────────────────────────┤
│   Custom UI (Lit/Vite)       │           Django Admin (Built-in)            │
│   Our branded interface      │           Auto-generated forms               │
│   Port 5173 (dev)            │           /django-admin/                     │
├──────────────────────────────┴──────────────────────────────────────────────┤
│                                                                             │
│                     HTTP Requests (JSON or HTML)                            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Django Server                                     │
│             ┌─────────────────────┬─────────────────────┐                   │
│             │  Django Ninja API   │  Django Admin Views │                   │
│             │  /api/v2/*          │  /django-admin/*    │                   │
│             │  JWT Auth           │  Session Auth       │                   │
│             └──────────┬──────────┴──────────┬──────────┘                   │
│                        │                     │                              │
│                        └──────────┬──────────┘                              │
│                                   │                                         │
│                        ┌──────────┴──────────┐                              │
│                        │     Django ORM      │                              │
│                        │     (Shared)        │                              │
│                        └──────────┬──────────┘                              │
│                                   │                                         │
├───────────────────────────────────┼─────────────────────────────────────────┤
│                        ┌──────────┴──────────┐                              │
│                        │    PostgreSQL       │                              │
│                        │    (Single DB)      │                              │
│                        └─────────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Answer to Your Question

**"Can our custom UIs run on top of Django Admin infrastructure?"**

**YES, they SHARE:**
- Same Django server process
- Same Django ORM
- Same PostgreSQL database
- Same Django settings

**NO, they are SEPARATE:**
- Different URL paths
- Different authentication systems
- Different UI frameworks
- Different purposes

**The Custom UI does NOT "run inside" Django Admin.**
**They are parallel entry points to the same backend.**
