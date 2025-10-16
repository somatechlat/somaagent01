scripts/takedown.sh — safely stop and cleanup local SomaAgent01 compose stack

Usage:

  # dry-run (show what would be removed)
  ./scripts/takedown.sh --dry

  # stop compose stack and remove orphans
  ./scripts/takedown.sh

Options:
  --project <name>   Use a different compose project name (default: somaagent01)
  --file <path>      Compose file to use (default: infra/docker-compose.somaagent01.yaml)

