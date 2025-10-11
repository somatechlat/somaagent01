# Kafka Initialization and OpenFGA Migration

## Kafka Service
- **Healthcheck**: Uses `kafka-topics.sh --list` with a timeout to verify the broker is ready before reporting *healthy*.
- **Start period**: 300 seconds to allow KRaft initialization.
- **Why**: The previous TCP check failed because the Bitnami image does not expose `/dev/tcp`. Listing topics ensures the broker can accept client connections.

## `somaAgent01_kafka-init`
- **Purpose**: Creates the required `somastack.delegation` topic after Kafka is up.
- **Implementation**: Added a retry loop that repeatedly attempts to list topics until the broker responds, then creates the topic.
- **Depends_on**: Waits for the `kafka` service to be healthy before starting.
- **Behavior**: Guarantees the topic is created on every compose start, even if Kafka takes longer than usual to become ready.

## OpenFGA Migration (`somaAgent01_openfga-migrate`)
- **Purpose**: Runs the OpenFGA schema migration against the PostgreSQL datastore.
- **Depends_on**: Waits for the `postgres` service to be healthy.
- **Restart policy**: `"no"` – runs once per compose start. This ensures the migration is applied each time the stack is brought up, without leaving a lingering container.

## Recommendations
- Keep the healthcheck start period at **300 s** unless you have a faster Kafka startup configuration.
- Monitor logs with `docker logs somaAgent01_kafka` and `docker logs somaAgent01_kafka-init` to verify topic creation.
- The migration container will exit with status `0` after successful run; this is expected.
