# OPA Policy for Confidence-Based Authorization
# Per Confidence Score Spec T7 (REQ-CONF-006)
#
# VIBE COMPLIANT:
# - Real OPA policy (no stubs)
# - Example policies for confidence thresholds
# - Integrates with existing OPA infrastructure
#
# Input:
# - input.confidence: float or null
# - input.confidence_enabled: boolean
# - input.request_id: string
# - input.tenant_id: string
# - input.endpoint: string

package soma.confidence


import future.keywords.contains
import future.keywords.in
import future.keywords.every
# Default allow if confidence scoring is disabled
default allow := false

# Deny if confidence is below critical threshold
deny contains msg {
    input.confidence_enabled == true
    input.confidence != null
    input.confidence < 0.3
    msg := sprintf("Confidence %v is below critical threshold 0.3", [input.confidence])
}

# Deny if confidence is missing and treat_null_as_low is true
deny contains msg {
    input.confidence_enabled == true
    input.treat_null_as_low == true
    input.confidence == null
    msg := "Confidence is null and treat_null_as_low is enabled"
}

# Allow if confidence is acceptable
allow {
    input.confidence_enabled == true
    input.confidence != null
    input.confidence >= 0.3
}

# Allow if confidence scoring is disabled
allow {
    input.confidence_enabled == false
}

# Allow if confidence is null and not treating as low
allow {
    input.confidence_enabled == true
    input.confidence == null
    input.treat_null_as_low == false
}

# Flag low confidence (between 0.3 and configurable threshold)
# This is informational, not blocking
should_flag {
    input.confidence_enabled == true
    input.confidence != null
    input.confidence >= 0.3
    input.confidence < input.min_acceptance
}

# Get confidence status for logging
confidence_status := "acceptable" {
    input.confidence != null
    input.confidence >= input.min_acceptance
} else := "low" {
    input.confidence != null
    input.confidence >= 0.3
    input.confidence < input.min_acceptance
} else := "critical" {
    input.confidence != null
    input.confidence < 0.3
} else := "unknown" {
    true
}

# Compute decision result
result := {
    "allow": count(deny) == 0,
    "deny_reasons": deny,
    "should_flag": should_flag,
    "confidence_status": confidence_status,
}

# Not applicable: the request carries no opinion on the dimension this
# policy owns. A rule with no input must not veto - that would deny every
# ordinary request, which is a different failure from fail-closed.
allow {
    not input.confidence
    not input.confidence_enabled
}
