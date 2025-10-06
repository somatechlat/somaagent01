package soma.policy

default allow = false

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
