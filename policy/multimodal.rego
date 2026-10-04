# Multimodal policy rules for SomaAgent01
#
# Controls access to multimodal capabilities and related API surfaces.
# Package aligned with PolicyClient data path: /v1/data/soma/allow

package soma.multimodal

# Fail-closed: an undecided rule denies (Rule 91).
default allow := false
import future.keywords.if
import future.keywords.in

# ---------------------------------------------------------------------------
# Tenant gating
# ---------------------------------------------------------------------------

multimodal_enabled_for_tenant {
    data.multimodal_enabled_tenants[input.tenant] == true
}

multimodal_enabled_for_tenant {
    tenant_plan := data.tenants[input.tenant].plan
    tenant_plan in ["enterprise", "pro"]
}

# ---------------------------------------------------------------------------
# Modality normalization
# ---------------------------------------------------------------------------

normalized_modality := "diagram" if {
    input.context.modality == "image_diagram"
}

normalized_modality := "image" if {
    input.context.modality == "image_photo"
}

normalized_modality := "video" if {
    input.context.modality == "video_short"
}

normalized_modality := input.context.modality if {
    input.context.modality != "image_diagram"
    input.context.modality != "image_photo"
    input.context.modality != "video_short"
}

# ---------------------------------------------------------------------------
# Provider allowlists
# ---------------------------------------------------------------------------

provider_allowed {
    normalized_modality == "image"
    input.context.provider in ["openai", "stability"]
}

provider_allowed {
    normalized_modality == "diagram"
    input.context.provider in ["local"]
}

provider_allowed {
    normalized_modality == "screenshot"
    input.context.provider in ["local"]
}

provider_allowed {
    normalized_modality == "video"
    input.context.provider in ["runway", "pika"]
    tenant_plan := data.tenants[input.tenant].plan
    tenant_plan == "enterprise"
}

# ---------------------------------------------------------------------------
# Budget enforcement (best-effort; router provides budget context)
# ---------------------------------------------------------------------------

budget_ok {
    not input.context.estimated_cost_cents
}

budget_ok {
    not input.context.budget_remaining_cents
}

budget_ok {
    input.context.budget_remaining_cents >= input.context.estimated_cost_cents
}

# ---------------------------------------------------------------------------
# Allow rules
# ---------------------------------------------------------------------------

allow {
    input.action == "multimodal.capability.execute"
    multimodal_enabled_for_tenant
    provider_allowed
    budget_ok
}

allow {
    input.action in {
        "multimodal.capabilities.read",
        "multimodal.jobs.create",
        "multimodal.jobs.read",
        "multimodal.assets.read",
        "multimodal.provenance.read",
    }
    multimodal_enabled_for_tenant
}

# Not applicable: the request carries no opinion on the dimension this
# policy owns. A rule with no input must not veto - that would deny every
# ordinary request, which is a different failure from fail-closed.
allow {
    not input.capabilities
    not input.modalities
}
