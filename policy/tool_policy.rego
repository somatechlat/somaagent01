package soma.policy

default allow = false

# ==============================
# MEMORY & SECURITY POLICIES
# ==============================

# --- Conversation Operations ---
allow {
  input.action == "conversation.send"
  # Allow by default in DEV mode
  input.context.environment == "dev"
}

allow {
  input.action == "conversation.send"
  # Tenant-scoped authorization
  input.tenant == input.context.allowed_tenant
  input.context.session_belongs_to_tenant
}

allow {
  input.action == "conversation.reset"
  input.tenant == input.context.session_tenant
}

allow {
  input.action == "conversation.delete"
  input.tenant == input.context.session_tenant
}

# --- Memory Operations with Tenant Isolation ---
allow {
  input.action == "memory.write"
  input.resource == "somabrain"
  # Ensure tenant isolation
  input.tenant == input.payload.tenant
  # Rate limiting: max 1000 writes per tenant per minute
  not exceeds_rate_limit(input.tenant, "memory_write", 1000, 60)
}

allow {
  input.action == "memory.recall"
  # Tenant-scoped recall
  input.tenant == input.query.tenant
  # Session ownership check for recall
  input.context.session_belongs_to_tenant
}

allow {
  input.action == "memory.delete"
  # Admin or tenant owner
  input.context.is_admin
}

allow {
  input.action == "memory.delete"
  input.tenant == input.context.session_tenant
  input.context.is_session_owner
}

# --- Conversation Memory with PII Protection ---
allow {
  input.action == "memory.write"
  input.resource == "conversation_memory"
  # Basic tenant isolation
  input.tenant == input.payload.metadata.tenant
  # PII content filtering
  not contains_pii(input.payload.content)
}

# --- Tool Execution with Parameter Validation ---
allow {
  input.action == "tool.execute"
  input.resource == "echo"
  # Basic validation
  is_string(input.context.args.message)
  len(input.context.args.message) <= 10000
}

allow {
  input.action == "tool.execute"
  input.resource == "timestamp"
  input.context.args.format != "DENY"
  # Validate format parameter
  is_valid_timestamp_format(input.context.args.format)
}

allow {
  input.action == "tool.execute"
  input.resource == "document_ingest"
  # Tenant-scoped document ingestion
  input.tenant == input.context.allowed_tenant
  not exceeds_file_size(input.context.attachment_size, 50 * 1024 * 1024)  # 50MB limit
}

# --- Settings Management ---
allow {
  input.action == "settings.update"
  input.tenant == input.context.allowed_tenant
  # Prevent sensitive setting updates by non-admins
  not is_sensitive_setting(input.context.setting_key)
}

allow {
  input.action == "settings.update"
  input.context.is_admin
  # Admin can update any setting
}

# --- Tool Catalog Management ---
allow {
  input.action == "tool.catalog.update"
  input.context.is_admin
}

# ==============================
# UTILITY FUNCTIONS
# ==============================

# Rate limiting helper
exceeds_rate_limit(tenant, action_type, max_count, window_seconds) {
  count := rate_limit_count(tenant, action_type, window_seconds)
  count > max_count
}

# PII detection helper (basic patterns)
contains_pii(content) {
  # Basic email pattern
  regex.match(`[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`, content)
}

contains_pii(content) {
  # Basic phone pattern
  regex.match(`\b\d{3}-\d{3}-\d{4}\b`, content)
}

# Content validation helpers
is_string(x) {
  is_string(x)
}

is_valid_timestamp_format(fmt) {
  fmt in ["ISO", "UNIX", "RFC3339", "US"]
}

# File size validation
exceeds_file_size(size_bytes, max_bytes) {
  size_bytes > max_bytes
}

# Sensitive settings detection
is_sensitive_setting(key) {
  key in ["api_key", "secret_key", "password", "token", "private_key"]
}
