package soma.policy.integrator

# Development policy - allow all for local testing
# VIBE Rule 34: Real infrastructure with permissive dev policy

default allow = true

# Allow all health checks
allow if {
    input.request_path == "/health"
}

# Allow all API endpoints in development
allow if {
    startswith(input.request_path, "/api/")
}

# Allow all admin endpoints
allow if {
    startswith(input.request_path, "/admin/")
}
