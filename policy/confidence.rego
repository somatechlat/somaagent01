# OPA Policy for Confidence-Based Authorization
# Per Confidence Score Spec T7 (REQ-CONF-006)
# Extended for typed decision signals (p_safe / risk) — fail-closed
#
# VIBE COMPLIANT:
# - Real OPA policy (no stubs)
# - Fail-closed when a confidence/Clef dimension is requested
# - Integrates with existing OPA infrastructure
#
# Input:
# - input.confidence: float or null (entropy confidence from Choice/Score)
# - input.confidence_enabled: boolean
# - input.p_safe: float or null (Noul P(true)/P(safe) — NEVER confidence)
# - input.risk: float or null (Score risk expectation)
# - input.decision_guard: boolean — true when a decision-model guard applies
# - input.tier: string ("1"|"2"|"3") or null
# - input.min_acceptance: float (default applied in rules as 0.5)
# - input.request_id: string
# - input.tenant_id: string
# - input.endpoint: string
#
# Outcome (result.outcome):
#   "allow" | "approval_required" | "denied"
# (aligned with tool_calling.decide_and_authorize_tool)

package soma.confidence

import future.keywords.contains
import future.keywords.in
import future.keywords.every

default allow := false

# ---------------------------------------------------------------------------
# Dimension applicability
#   - decision_guard == true  → Clef evidence is MANDATORY (fail-closed)
#   - confidence_enabled == true → confidence is MANDATORY (fail-closed)
#   - neither → this policy does not veto (ordinary request)
# ---------------------------------------------------------------------------

decision_guard_required {
    input.decision_guard == true
}

conf_required {
    input.confidence_enabled == true
}

dimension_requested {
    decision_guard_required
}

dimension_requested {
    conf_required
}

tier3 {
    input.tier == "3"
}

tier3 {
    input.tier == 3
}

# ---------------------------------------------------------------------------
# DENY (fail-closed)
# ---------------------------------------------------------------------------

# decision guard requested but P(safe) missing (Clef down / not called)
deny contains msg {
    decision_guard_required
    input.p_safe == null
    msg := "decision guard required but p_safe is null (fail-closed)"
}

# decision guard requested but P(safe) missing by absence (key not set)
deny contains msg {
    decision_guard_required
    not input.p_safe
    msg := "decision guard required but p_safe is missing (fail-closed)"
}

# P(safe) below critical
deny contains msg {
    decision_guard_required
    input.p_safe != null
    input.p_safe < 0.3
    msg := sprintf("p_safe %v is below critical threshold 0.3", [input.p_safe])
}

# High risk always blocks auto-allow path at policy level (approval path)
# (this deny is informational for auto; outcome computes approval_required)

# Confidence required but missing
deny contains msg {
    conf_required
    input.confidence == null
    msg := "confidence_enabled but confidence is null (fail-closed)"
}

deny contains msg {
    conf_required
    not input.confidence
    msg := "confidence_enabled but confidence is missing (fail-closed)"
}

# Confidence below critical
deny contains msg {
    conf_required
    input.confidence != null
    input.confidence < 0.3
    msg := sprintf("Confidence %v is below critical threshold 0.3", [input.confidence])
}

# ---------------------------------------------------------------------------
# ALLOW (only when dimension not requested, or evidence is acceptable)
# ---------------------------------------------------------------------------

# Not applicable — no confidence/Clef dimension on this request
allow {
    not dimension_requested
}

# Clef: acceptable P(safe) and not high-risk
allow {
    decision_guard_required
    input.p_safe != null
    input.p_safe >= 0.7
    not high_risk
}

# Confidence acceptable
allow {
    conf_required
    input.confidence != null
    input.confidence >= 0.3
    not high_risk
}

high_risk {
    input.risk != null
    input.risk >= 2
}

# ---------------------------------------------------------------------------
# approval_required (not auto-allow, not hard-deny)
# ---------------------------------------------------------------------------

approval_required {
    decision_guard_required
    input.p_safe != null
    input.p_safe >= 0.3
    input.p_safe < 0.7
}

approval_required {
    high_risk
    dimension_requested
    count(deny) == 0
}

approval_required {
    decision_guard_required
    input.p_safe != null
    input.p_safe >= 0.7
    high_risk
}

approval_required {
    conf_required
    input.confidence != null
    input.confidence >= 0.3
    input.confidence < min_acceptance
}

min_acceptance := x {
    x := input.min_acceptance
    x != null
} else := 0.5

should_flag {
    dimension_requested
    count(deny) == 0
    approval_required
}

should_flag {
    conf_required
    input.confidence != null
    input.confidence >= 0.3
    input.confidence < min_acceptance
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

confidence_status := "acceptable" {
    input.confidence != null
    input.confidence >= min_acceptance
} else := "low" {
    input.confidence != null
    input.confidence >= 0.3
    input.confidence < min_acceptance
} else := "critical" {
    input.confidence != null
    input.confidence < 0.3
} else := "unknown" {
    true
}

outcome := "denied" {
    count(deny) > 0
} else := "approval_required" {
    approval_required
} else := "allow" {
    true
}

result := {
    "allow": outcome == "allow",
    "outcome": outcome,
    "deny_reasons": deny,
    "approval_required": approval_required,
    "should_flag": should_flag,
    "confidence_status": confidence_status,
}
