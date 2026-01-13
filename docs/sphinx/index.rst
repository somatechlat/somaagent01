.. SomaAgent01 Documentation master file

================================
SomaAgent01 Documentation
================================

**Multi-Agent Cognitive Platform** built on Django 5.0 + Django Ninja

Port Namespace
--------------

Port Namespace: **639xx** (SAAS) or **32xxx** (K8S)

**SAAS Ports:** PostgreSQL: 63932, Redis: 63979, Kafka: 63992, Vault: 63982
**K8S Ports:** PostgreSQL: 32432, Redis: 32379, Kafka: 32092

**⚠️ DEPRECATED: 20432 is NOT used in current codebase.**

Quick Links
-----------

* :doc:`quickstart` - Get started in 5 minutes
* :doc:`deployment/index` - Production deployment guides
* :doc:`api/index` - API Reference

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   quickstart
   agent-quickstart

.. toctree::
   :maxdepth: 2
   :caption: Deployment

   deployment/index

.. toctree::
   :maxdepth: 3
   :caption: API Reference

   api/index
   admin/index
   services/index

.. toctree::
   :maxdepth: 1
   :caption: Development

   development/contributing
   development/vibe-rules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

