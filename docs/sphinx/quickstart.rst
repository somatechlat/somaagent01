=================
Quick Start Guide
=================

Get SomaAgent01 running in 10 minutes.

Prerequisites
=============

+-----------------+-----------------+-------------------------+
| Component       | Minimum Version | Check Command           |
+=================+=================+=========================+
| Docker          | 24.0+           | ``docker --version``    |
+-----------------+-----------------+-------------------------+
| Docker Compose  | 2.20+           | ``docker compose version`` |
+-----------------+-----------------+-------------------------+
| Python          | 3.11+           | ``python3 --version``   |
+-----------------+-----------------+-------------------------+
| Node.js         | 20+             | ``node --version``      |
+-----------------+-----------------+-------------------------+
| RAM             | 16GB            | -                       |
+-----------------+-----------------+-------------------------+

Step 1: Clone & Configure
=========================

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/somatech/somaAgent01.git
   cd somaAgent01

   # Copy environment template
   cp .env.example .env

Required Environment Variables
------------------------------

Edit ``.env`` and configure:

.. code-block:: bash

   # Database
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=somastack2024
   POSTGRES_DB=somaagent

   # Redis
   REDIS_PASSWORD=somastack2024

   # Keycloak (Identity)
   KEYCLOAK_URL=http://localhost:20880
   KEYCLOAK_REALM=somaagent
   KEYCLOAK_CLIENT_ID=eye-of-god

   # LLM Provider
   OPENAI_API_KEY=your-api-key-here
   SAAS_DEFAULT_CHAT_MODEL=gpt-4o

Step 2: Start Infrastructure
============================

**Option A: Clean Start (Recommended)**

.. code-block:: bash

   make reset-infra

This command destroys all containers and volumes, starts PostgreSQL, runs SpiceDB migrations, and brings up the full stack.

**Option B: Normal Start**

.. code-block:: bash

   docker compose up -d

Step 3: Verify Health
=====================

.. code-block:: bash

   # Check all services
   docker compose ps

   # Verify API health
   curl http://localhost:20020/health

Step 4: Access Services
=======================

+-----------------+------------------------------------+-------------------+
| Service         | URL                                | Credentials       |
+=================+====================================+===================+
| **API Docs**    | http://localhost:20020/api/v2/docs | -                 |
+-----------------+------------------------------------+-------------------+
| **Keycloak**    | http://localhost:20880/admin       | admin / admin     |
+-----------------+------------------------------------+-------------------+
| **Grafana**     | http://localhost:20300             | admin / admin     |
+-----------------+------------------------------------+-------------------+
| **Frontend**    | http://localhost:20080             | -                 |
+-----------------+------------------------------------+-------------------+

Port Namespace
==============

**SomaAgent01 uses port 20xxx:**

+-----------------+-------+
| Service         | Port  |
+=================+=======+
| PostgreSQL      | 20432 |
+-----------------+-------+
| Redis           | 20379 |
+-----------------+-------+
| Kafka           | 20092 |
+-----------------+-------+
| Milvus          | 20530 |
+-----------------+-------+
| SpiceDB         | 20051 |
+-----------------+-------+
| Keycloak        | 20880 |
+-----------------+-------+
| Django API      | 20020 |
+-----------------+-------+
| Frontend        | 20080 |
+-----------------+-------+

**Related Services:**

- SomaBrain: Port 30xxx
- SomaFractalMemory: Port 9xxx

Next Steps
==========

* Read :doc:`agent-quickstart` for AI agent context
* Explore `API Documentation <http://localhost:20020/api/v2/docs>`_
