# Shared Infrastructure Reference

This note captures the key connection details from
`~/work/infra/AI_AGENT_INTEGRATION_GUIDE.md` so project documentation can link to
stable endpoints without browsing the external guide.

## Core Services

| Service  | Host Endpoint        | Docker Endpoint            | Credentials / Notes |
|----------|----------------------|----------------------------|----------------------|
| Postgres | `127.0.0.1:5432`     | `shared-postgres:5432`     | user `checker_user`, password `PG_PASSWORD` from `.env.infra` |
| MongoDB  | `127.0.0.1:27017`    | `shared-mongo:27017`       | user `admin`, password `MONGO_PASSWORD` |
| Redis    | `127.0.0.1:6379`     | `shared-redis:6379`        | password `REDIS_PASSWORD` (legacy setups may keep it empty) |
| Kafka    | `127.0.0.1:29092`    | `shared-kafka:9092`        | PLAINTEXT cluster, no auth |

Projects running inside Docker should join the external network
`infra_infra_app-network`:

```yaml
networks:
  infra_infra_app-network:
    external: true
```

## Local LLM (Qwen 2.5)

- Start: `cd ~/work/infra/llm && ./start.sh`
- Stop: `cd ~/work/infra/llm && ./stop.sh`
- Endpoints (OpenAI-compatible):
  - `http://127.0.0.1:8000/v1/chat/completions`
  - `http://127.0.0.1:8000/v1/models`
  - `http://127.0.0.1:8000/health`
- Pull model for Ollama backend: `docker exec ollama ollama pull qwen2.5:7b`
- Prometheus metrics (optional): `http://127.0.0.1:8000/v1/metrics`

## Monitoring Stack

- Prometheus: `http://127.0.0.1:9090`
- Grafana: `http://127.0.0.1:3000`
  - Login `admin`, password `GRAFANA_PASSWORD`
- Script to start exporters: `~/work/infra/scripts/start-monitoring.sh`

## Credential Propagation

Export shared environment variables in new projects:

```bash
cp ~/work/infra/.env.infra .env
set -a
source .env
set +a
```

## Kafka Quick Reference

- List topics: `docker exec shared-kafka kafka-topics --bootstrap-server kafka:9092 --list`
- Create topic: `docker exec shared-kafka kafka-topics --bootstrap-server kafka:9092 --create --topic demo --partitions 3 --replication-factor 1`
- Produce message: `docker exec -it shared-kafka kafka-console-producer --broker-list kafka:9092 --topic demo`

Keep this reference in sync with the upstream guide; when the infra changes, update
both documents together.
