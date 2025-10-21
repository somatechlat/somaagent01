These compose variants were moved here to avoid duplicate top-level docker-compose files.

Files:
- `docker-compose.slim.yaml` - a smaller/lean production-oriented compose that uses the `somaagent01-slim` image and alternative default host ports.
- `docker-compose.slim-browser.yaml` - slim image that includes browser features (`FEATURE_BROWSER=true`).

If you want to run one of these variants, you can still do so from this folder, for example:

```sh
docker compose -f agent-zero/docker/compose_variants/docker-compose.slim.yaml up -d
```

The canonical and full development compose remains at `agent-zero/docker-compose.yaml`.
