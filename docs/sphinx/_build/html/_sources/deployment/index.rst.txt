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

+---------------+-------+
| Service       | Port  |
+===============+=======+
| PostgreSQL    | 20432 |
+---------------+-------+
| Redis         | 20379 |
+---------------+-------+
| Kafka         | 20092 |
+---------------+-------+
| Milvus        | 20530 |
+---------------+-------+
| SpiceDB       | 20051 |
+---------------+-------+
| OPA           | 20181 |
+---------------+-------+
| Keycloak      | 20880 |
+---------------+-------+
| Prometheus    | 20090 |
+---------------+-------+
| Grafana       | 20300 |
+---------------+-------+
| Django API    | 20020 |
+---------------+-------+
| Frontend      | 20080 |
+---------------+-------+

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
