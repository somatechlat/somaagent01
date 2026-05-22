"""Capsule Export/Import REST API.

Provides endpoints for:
- Full Capsule export/import
- Partial exports (tools, persona, governance)
- Export verification

VIBE Compliance:
- Rule 82: Professional comments, zero AI slop
- Rule 216: Django 5+ Backend Sovereignty
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from admin.core.models import Capsule
from services.capsule_export import (
    export_capsule,
    export_capsule_governance,
    export_capsule_persona,
    export_capsule_tools,
    verify_export_checksum,
)
from services.capsule_import import ImportResult, import_capsule

logger = logging.getLogger(__name__)


# =============================================================================
# EXPORT ENDPOINTS
# =============================================================================


@require_http_methods(["GET"])
def export_capsule_full(request, capsule_id: str):
    """Export a complete Capsule bundle.

    GET /api/capsules/<capsule_id>/export
    """
    try:
        data = export_capsule(UUID(capsule_id), include_instances=False, include_sessions=False)
        return JsonResponse(data, safe=False)
    except Capsule.DoesNotExist:
        return JsonResponse({"error": "Capsule not found"}, status=404)
    except Exception as exc:
        logger.error("Export failed: %s", exc, exc_info=True)
        return JsonResponse({"error": str(exc)}, status=500)


@require_http_methods(["GET"])
def export_capsule_tools_endpoint(request, capsule_id: str):
    """Export just the tools from a Capsule.

    GET /api/capsules/<capsule_id>/export/tools
    """
    try:
        data = export_capsule_tools(UUID(capsule_id))
        return JsonResponse(data, safe=False)
    except Capsule.DoesNotExist:
        return JsonResponse({"error": "Capsule not found"}, status=404)
    except Exception as exc:
        logger.error("Tools export failed: %s", exc, exc_info=True)
        return JsonResponse({"error": str(exc)}, status=500)


@require_http_methods(["GET"])
def export_capsule_persona_endpoint(request, capsule_id: str):
    """Export just the persona from a Capsule.

    GET /api/capsules/<capsule_id>/export/persona
    """
    try:
        data = export_capsule_persona(UUID(capsule_id))
        return JsonResponse(data, safe=False)
    except Capsule.DoesNotExist:
        return JsonResponse({"error": "Capsule not found"}, status=404)
    except Exception as exc:
        logger.error("Persona export failed: %s", exc, exc_info=True)
        return JsonResponse({"error": str(exc)}, status=500)


@require_http_methods(["GET"])
def export_capsule_governance_endpoint(request, capsule_id: str):
    """Export just the governance from a Capsule.

    GET /api/capsules/<capsule_id>/export/governance
    """
    try:
        data = export_capsule_governance(UUID(capsule_id))
        return JsonResponse(data, safe=False)
    except Capsule.DoesNotExist:
        return JsonResponse({"error": "Capsule not found"}, status=404)
    except Exception as exc:
        logger.error("Governance export failed: %s", exc, exc_info=True)
        return JsonResponse({"error": str(exc)}, status=500)


# =============================================================================
# IMPORT ENDPOINTS
# =============================================================================


@csrf_exempt
@require_http_methods(["POST"])
def import_capsule_endpoint(request):
    """Import a Capsule from an export bundle.

    POST /api/capsules/import
    Body: JSON export bundle
    """
    try:
        import json

        body = json.loads(request.body)
        target_tenant = request.headers.get("X-Tenant-ID") or body.get("target_tenant")

        result: ImportResult = import_capsule(
            export_data=body,
            target_tenant=target_tenant,
            skip_checksum=False,
            import_related_data=True,
        )

        if result.success and result.capsule:
            return JsonResponse(
                {
                    "success": True,
                    "capsule_id": str(result.capsule.id),
                    "name": result.capsule.name,
                    "version": result.capsule.version,
                    "status": result.capsule.status,
                    "warnings": result.warnings,
                },
                status=201,
            )
        else:
            return JsonResponse(
                {
                    "success": False,
                    "error": result.error,
                    "warnings": result.warnings,
                },
                status=400,
            )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    except Exception as exc:
        logger.error("Import failed: %s", exc, exc_info=True)
        return JsonResponse({"error": str(exc)}, status=500)


# =============================================================================
# VERIFICATION ENDPOINT
# =============================================================================


@csrf_exempt
@require_http_methods(["POST"])
def verify_export_endpoint(request):
    """Verify the integrity of an export bundle.

    POST /api/capsules/verify
    Body: JSON export bundle
    """
    try:
        import json

        body = json.loads(request.body)
        is_valid = verify_export_checksum(body)
        return JsonResponse({"valid": is_valid})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    except Exception as exc:
        logger.error("Verify failed: %s", exc, exc_info=True)
        return JsonResponse({"error": str(exc)}, status=500)
