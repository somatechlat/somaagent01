package soma.policy.integrator

# Development policy - allow all for local testing
# VIBE Rule 34: Real infrastructure with permissive dev policy

default allow = true

# Allow all health checks
allow {
    input.request_path == "/health"
}

# Allow all API endpoints in development
allow {
    startswith(input.request_path, "/api/")
}

# Allow all admin endpoints
allow {
    startswith(input.request_path, "/admin/")
}
