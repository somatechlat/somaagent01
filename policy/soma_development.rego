package soma.policy.integrator

# ⚠️  DEVELOPMENT POLICY — NEVER LOAD IN PRODUCTION
# This policy is explicitly gated behind DEBUG mode in the application layer.
# If loaded in production, it allows ALL requests.
# The application MUST check DeploymentMode.is_dev() before using this policy.

# This file is kept ONLY for local development convenience.
# Production systems must use policy/tool_policy.rego, policy/confidence.rego,
# policy/multimodal.rego, and policy/skins.rego which enforce real authorization.

default allow = false

# Only allow in development — the application layer MUST verify DEBUG mode
allow if {
    input.deployment_mode == "dev"
    input.debug == true
}

allow if {
    input.request_path == "/health"
}

allow if {
    input.request_path == "/api/v2/health"
}
