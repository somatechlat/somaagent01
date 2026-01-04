===================
Agent Context Guide
===================

Essential context for AI agents working on this codebase.

Before You Code
===============

**Read these files FIRST:**

1. ``AGENT.md`` - Complete knowledge base (1000+ lines)
2. ``docs/development/VIBE_CODING_RULES.md`` - Non-negotiable rules
3. Check existing code before creating new files

VIBE Coding Rules Summary
=========================

+------------+-------------------------------------------------------+
| Rule       | Description                                           |
+============+=======================================================+
| **Rule 1** | NO BULLSHIT - No mocks, no placeholders, no TODOs     |
+------------+-------------------------------------------------------+
| **Rule 2** | CHECK FIRST, CODE SECOND - Review architecture first  |
+------------+-------------------------------------------------------+
| **Rule 3** | NO UNNECESSARY FILES - Modify existing when possible  |
+------------+-------------------------------------------------------+
| **Rule 4** | REAL IMPLEMENTATIONS ONLY - Production-grade always   |
+------------+-------------------------------------------------------+
| **Rule 5** | DOCUMENTATION = TRUTH - Verify from official docs     |
+------------+-------------------------------------------------------+
| **Rule 6** | COMPLETE CONTEXT REQUIRED - Understand full flow      |
+------------+-------------------------------------------------------+
| **Rule 7** | REAL DATA, REAL SERVERS - Use actual services         |
+------------+-------------------------------------------------------+

Technology Stack (STRICT)
=========================

+-----------+-------------------------+-------------------+
| Layer     | Technology              | Forbidden         |
+===========+=========================+===================+
| API       | Django 5.0 + Ninja      | ❌ FastAPI        |
+-----------+-------------------------+-------------------+
| ORM       | Django ORM              | ❌ SQLAlchemy     |
+-----------+-------------------------+-------------------+
| Frontend  | Lit 3.x Web Components  | ❌ React          |
+-----------+-------------------------+-------------------+
| Vector DB | Milvus                  | ❌ Qdrant         |
+-----------+-------------------------+-------------------+

Key Files Reference
===================

Backend (Python/Django)
-----------------------

+-------------------------------+-----------------------------------------------+
| File                          | Purpose                                       |
+===============================+===============================================+
| ``admin/api.py``              | Master API router                             |
+-------------------------------+-----------------------------------------------+
| ``admin/auth/api.py``         | Auth endpoints: /token, /login, /refresh      |
+-------------------------------+-----------------------------------------------+
| ``admin/common/auth.py``      | JWT validation: AuthBearer, decode_token()    |
+-------------------------------+-----------------------------------------------+
| ``admin/core/models.py``      | Django ORM models                             |
+-------------------------------+-----------------------------------------------+

Port Namespace
==============

::

   SomaAgent01: 20xxx
   ├── PostgreSQL:  20432
   ├── Redis:       20379
   ├── Django API:  20020
   └── Frontend:    20080

   SomaBrain:           30xxx (port 30101)
   SomaFractalMemory:   40xxx (port 40000)

User Roles
==========

1. ``saas_admin`` → /select-mode
2. ``tenant_sysadmin`` → /select-mode
3. ``tenant_admin`` → /dashboard
4. ``agent_owner`` → /dashboard
5. ``user`` → /chat
6. ``viewer`` → /chat (read-only)

Testing Requirements
====================

**CRITICAL: No Mocks!**

.. code-block:: bash

   # Start test infrastructure
   docker compose --profile core up -d

   # Run tests
   pytest
