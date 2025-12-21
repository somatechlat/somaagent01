group "default" {
  targets = ["somaagent01"]
}

target "somaagent01" {
  context = "."
  dockerfile = "Dockerfile"
  tags = ["somaagent01-dev:latest"]
}
