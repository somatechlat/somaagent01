package soma.policy

default allow = false

# Allow chat messages unconditionally in DEV (fail-open chat to reduce friction during development).
allow {
  input.action == "conversation.send"
}

# Retain explicit allows for tools/memory/settings below for clarity.

allow {
  input.action == "tool.execute"
  input.resource == "echo"
}

allow {
  input.action == "tool.execute"
  input.resource == "timestamp"
  input.context.args.format != "DENY"
}

# Permit document ingestion tool for public tenant in DEV
allow {
  input.action == "tool.execute"
  input.resource == "document_ingest"
  input.tenant == "public"
}

allow {
  input.action == "memory.write"
  input.resource == "conversation_memory"
}

# Allow memory writes to SomaBrain in DEV
allow {
  input.action == "memory.write"
  input.resource == "somabrain"
}

# Allow UI settings updates for the public tenant in DEV
allow {
  input.action == "settings.update"
  input.tenant == "public"
}

# Allow tool catalog updates for the public tenant in DEV
allow {
  input.action == "tool.catalog.update"
  input.tenant == "public"
}
