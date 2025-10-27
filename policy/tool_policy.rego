package soma.policy

default allow = false

# Allow basic chat messages for the public tenant in DEV
allow {
  input.action == "conversation.send"
  input.tenant == "public"
}

allow {
  input.action == "tool.execute"
  input.resource == "echo"
}

allow {
  input.action == "tool.execute"
  input.resource == "timestamp"
  input.context.args.format != "DENY"
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
