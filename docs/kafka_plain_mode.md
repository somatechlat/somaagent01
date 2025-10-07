# Kafka Plain‑Text Configuration (Default)

The `docker-compose.somaagent01.yaml` file configures the **Kafka** service to run in plain‑text mode by default. This avoids the production warning about a PLAINTEXT listener and keeps the stack simple for local development and testing.

## Key Settings
| Variable | Value (default) | Description |
|----------|----------------|-------------|
| `KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP` | `INTERNAL:PLAINTEXT,CONTROLLER:PLAINTEXT` | Maps the internal broker listener to PLAINTEXT. |
| `KAFKA_CFG_ALLOW_PLAINTEXT_LISTENER` | `yes` | Allows plain‑text connections (required for local dev). |
| `KAFKA_ENABLE_SSL` | `false` | Toggle to enable SSL – keep `false` for plain mode. |
| `KAFKA_CFG_KRAFT_CLUSTER_ID` | `soma-cluster-01` | Stable KRaft cluster identifier. |
| `KAFKA_CFG_KRAFT_CLUSTER_ID` | `soma-cluster-01` | Stable KRaft cluster identifier. |

## How to Switch to SSL (Production)
1. Set environment variables before running compose:
   ```bash
   export KAFKA_ENABLE_SSL=true
   export KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP="INTERNAL:SSL,CONTROLLER:PLAINTEXT"
   export KAFKA_CFG_ALLOW_PLAINTEXT_LISTENER=no
   ```
2. Provide real keystore/truststore files in `./kafka_certs` (mounted into the container).
3. Re‑build and restart the stack.

## Building & Restarting the Cluster
```bash
# Build the custom images (delegation services use DockerfileLocal)
docker compose -f infra/docker-compose.somaagent01.yaml build

# Bring the whole stack down and start fresh
docker compose -f infra/docker-compose.somaagent01.yaml down
docker compose -f infra/docker-compose.somaagent01.yaml up -d
```

All services should start cleanly, with Kafka reporting **healthy** (plain‑text mode) and the warning suppressed.

---
*Generated on $(date)*
