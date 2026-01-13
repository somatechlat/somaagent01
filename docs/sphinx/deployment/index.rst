=================
Deployment Guide
=================

Deployment documentation for SomaAgent01.

.. toctree::
   :maxdepth: 2
   :caption: Deployment Options

   local
   docker
   aws
   kubernetes

Overview
========

**Target Environment**: Docker / AWS ECS (Fargate) / EKS / EC2

**Stack**: Django 5.0, PostgreSQL 16, Redis 7

Port Namespace
--------------

SomaAgent01 uses port **20xxx** to avoid conflicts:

+---------------+-------+---------------+-----------------------------------------+
| Service       | Port  | Range         | Notes                                   |
+===============+=======+===============+=========================================+
| PostgreSQL    | 20432 | 20xxx         | **DEPRECATED: Port 20432 is NOT used**   |
+---------------+-------+---------------+-----------------------------------------+
| Redis         | 20379 | 20xxx         | Cache & sessions                        |
+---------------+-------+---------------+-----------------------------------------+
| Kafka         | 20092 | 20xxx         | Events & audit                          |
+---------------+-------+---------------+-----------------------------------------+
| Milvus        | 20530 | 20xxx         | Vector database                         |
+---------------+-------+---------------+-----------------------------------------+
| SpiceDB       | 20051 | 20xxx         | Authorization                           |
+---------------+-------+---------------+-----------------------------------------+
| OPA           | 20181 | 20xxx         | Policy engine                           |
+---------------+-------+---------------+-----------------------------------------+
| Keycloak      | 20880 | 20xxx         | Identity management                     |
+---------------+-------+---------------+-----------------------------------------+
| Prometheus    | 20090 | 20xxx         | Metrics collection                      |
+---------------+-------+---------------+-----------------------------------------+
| Grafana       | 20300 | 20xxx         | Visualization                           |
+---------------+-------+---------------+-----------------------------------------+
| Django API    | 20020 | 20xxx         | Main entry point                        |
+---------------+-------+---------------+-----------------------------------------+
| Frontend      | 20080 | 20xxx         | Web UI                                  |
+---------------+-------+---------------+-----------------------------------------+

Port Mappings
-------------

**SAAS Deployment (639xx range):**

.. list-table::
   :header-rows: 1

   * - Service
     - Internal
     - External
     - Notes
   * - PostgreSQL
     - 5432
     - 63932
     - All services connect internally
   * - Redis
     - 6379
     - 63979
     - Cache & sessions
   * - Kafka
     - 9092
     - 63992
     - Events & audit
   * - Vault
     - 8200
     - 63982
     - **NO ENV VARS FOR SECRETS**
   * - Agent API
     - 9000
     - 63900
     - Main entry point

**Kubernetes Deployment (32xxx range):**
- PostgreSQL: 32432
- Redis: 32379
- Kafka: 32092
- Vault: 32982

.. warning::
   **Port 20432 is DEPRECATED and NEVER used in current codebase.**
   The documentation mentioning 20432 is outdated.
Quick Start
-----------

.. code-block:: bash

   # Clone and configure
   git clone https://github.com/somatech/somaAgent01.git
   cd somaAgent01
   cp .env.example .env

   # Start infrastructure
   make reset-infra

   # Verify health
   curl http://localhost:20020/health

