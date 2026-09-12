# Multi-Agent System — Deployment Bundle v1.0.0

**Startup Script · Docker Compose · Operational Guide**

Master Prompt: *Precision · Resilience · Transparency*

Environment: Linux (Ubuntu 22.04+) / macOS 13+

> **Bundle Scope:** This bundle is suitable for internal and local deployment rehearsal. Before any real production rollout, replace the bundled internal-only Vault development configuration, enable Gateway TLS, and complete the full security checklist below.

---

## Table of Contents

1. Quick Start
2. Prerequisites
3. Environment Variables Reference
4. `startup.sh` Annotated Reference
5. `docker-compose.yml` Annotated Reference
6. Service Endpoint Reference
7. Useful Operational Commands
8. Security Checklist
9. Troubleshooting

---

## 1. Quick Start

**Three-Step Startup**

1. Make the startup script executable: `chmod +x startup.sh`
2. Launch the bundle: `GRAFANA_PASS='change-me' MAS_ENV=staging ./startup.sh`
3. Open the Gateway API: http://localhost:8080

> **Note:** Full startup takes approximately 3–5 minutes on first run due to image pulls. Subsequent starts complete in approximately 60 seconds once images are cached locally.

---

## 2. Prerequisites

The Phase 0 preflight check validates tools automatically, but host-level resource requirements must be confirmed manually.

| Requirement | Minimum Version / Notes |
|---|---|
| Docker Engine | 24.0+ |
| Docker Compose | v2.20+ (plugin or standalone); use `docker compose` for plugin, `docker-compose` for standalone |
| Python | 3.10+ — used to safely serialize generated `.env` values for Compose |
| curl | Any recent version — used for health polling and smoke tests |
| jq | 1.6+ — used for JSON inspection in preflight daemon validation and diagnostic commands |
| openssl | 3.0+ — required for secret generation (HMAC, RSA 4096, mTLS CA) |
| Disk space | ≥ 10 GB free (preflight warns if below threshold) |
| RAM | ≥ 16 GB recommended (Qdrant + Memory agent each consume up to 4 GB) |
| CPU | ≥ 4 cores recommended; executor pool runs ×3 replicas at 2.0 CPU each |
| OS | Linux (Ubuntu 22.04+) or macOS 13+ (Ventura or later) |

---

## 3. Environment Variables Reference

All variables are consumed by `startup.sh` and propagated into the Docker Compose environment. Override any variable by exporting it before invoking the startup script. The script writes a minimal `.env` at Phase 1 (secret bootstrapping) for subsequent Compose operations.

| Variable | Default | Description |
|---|---|---|
| `MAS_ENV` | `production` | Deployment environment: production / staging / dev |
| `MAS_VERSION` | `1.0.0` | Semantic version tag applied to all custom agent images |
| `MAS_COMPOSE_FILE` | `docker-compose.yml` | Path to the Compose file passed to all Compose invocations |
| `MAS_LOG_DIR` | `./logs` | Host filesystem path for the shared log volume mount |
| `MAS_HEALTH_TIMEOUT` | `120` | Maximum seconds the health poller waits for any service to reach healthy state |
| `MAS_ROTATE_HMAC` | `false` | Optional manual rotation flag; set to `true` to rotate the HMAC key during startup while retaining `HMAC_PREVIOUS_KEY` overlap |
| `POSTGRES_PASS` | `changeme` | PostgreSQL password — MUST be changed in production |
| `REDIS_PASS` | `changeme` | Redis password — MUST be changed in production |
| `RABBITMQ_PASS` | `changeme` | RabbitMQ password — MUST be changed in production |
| `RABBITMQ_COOKIE` | `mas-secret-cookie` | Erlang cluster cookie — change in production to a high-entropy value |
| `VAULT_TOKEN` | `root` | Vault root token — replace with proper auto-unseal or key share mechanism in production |
| `PROMETHEUS_IMAGE` | `prom/prometheus:v2.53.0` | Prometheus image used for deployment and preflight `promtool` validation |
| `GRAFANA_PASS` | _(required)_ | Grafana administrator password |
| `LOG_LEVEL` | `info` | Log verbosity across all agents: debug / info / warn / error |

> **Security Warning:** Never commit `.env` or the `.secrets/` directory to version control. Both are already added to `.gitignore`. The `.secrets/` directory contains plaintext private keys and HMAC material. The generated `.env` file contains the live HMAC signing key and, during coordinated key rotation, may also include `HMAC_PREVIOUS_KEY` for overlap verification.

---

## 4. `startup.sh` Annotated Reference

The startup script implements an 8-phase sequential boot sequence with colour-coded terminal output (ANSI escape codes), automatic secret generation and rotation, per-service health polling via `docker inspect`, and a graceful shutdown trap registered for `SIGINT` and `SIGTERM`. Each phase is isolated into a named function; failures in any phase abort the entire sequence with a non-zero exit code (`set -euo pipefail`).

### Phase Summary

| Phase | Function | What It Does |
|---|---|---|
| 0 | `preflight_checks()` | Verifies required tools (docker, Docker Compose plugin or docker-compose, Python, curl, jq, openssl), Docker daemon responsiveness, Compose file presence and syntax validity, and ≥ 10 GB free disk space |
| 1 | `bootstrap_secrets()` | Generates a 256-bit HMAC-SHA256 signing key, optionally rotates it when `MAS_ROTATE_HMAC=true` while retaining the previous key for overlap rollout, generates an RS256 4096-bit JWT key pair, writes an mTLS CA certificate (365-day validity), and writes `.env` |
| 2 | `prepare_infrastructure()` | Creates `mas-overlay` bridge network (172.28.0.0/16) and 5 named Docker volumes if absent; creates the host log directory |
| 3 | `pull_images()` | Pulls all service images defined in `docker-compose.yml` using Compose pull in quiet mode and validates `prometheus.yml` with `promtool` |
| 4 | `start_infrastructure()` | Starts postgres, redis, qdrant, rabbitmq with per-service health polling and configurable timeouts |
| 5 | `start_agents()` | Starts Jaeger first so OTLP exports have a live collector, then starts gateway, orchestrator, planner, memory with health polling; then scales executor to ×3 replicas and starts critic |
| 6 | `start_observability()` | Starts prometheus and grafana and logs the Grafana, Jaeger, and Prometheus URLs |
| 7 | `smoke_tests()` | Runs 5 curl-based endpoint checks against Gateway, Orchestrator, Memory, Grafana, and Prometheus with bounded retries; reports PASS / FAIL count |

See `./startup.sh` for the full source.

---

## 5. `docker-compose.yml` Annotated Reference

### Service Overview

| Service | Image | Port(s) | CPU Limit | Memory Limit | Role |
|---|---|---|---|---|---|
| postgres | postgres:16-alpine | 5432 (internal) | 1.0 | 1 GB | Persistent state + audit log |
| redis | redis:7-alpine | 6379 (internal) | 0.5 | 512 MB | Cache, sessions, idempotency |
| qdrant | qdrant/qdrant:v1.10.0 | 6333/6334 (internal) | 2.0 | 4 GB | Vector DB for Memory Agent RAG |
| rabbitmq | rabbitmq:3.13-management | 5672, 15672 | 1.0 | 1 GB | AMQP message bus |
| vault (optional `vault-dev` profile) | hashicorp/vault:1.17 | 8200 (internal) | — | — | Dev-only secret management sandbox |
| gateway | mas/gateway:1.0.0 | 8080 (public) | 1.0 | 512 MB | External interface, authentication |
| orchestrator | mas/orchestrator:1.0.0 | 8081 (internal) | 2.0 | 1 GB | Central coordinator |
| planner | mas/planner:1.0.0 | 8082 (internal) | 2.0 | 2 GB | DAG task planning |
| executor (×3) | mas/executor:1.0.0 | 8084 (scalable) | 2.0 each | 2 GB each | Stateless task workers |
| critic | mas/critic:1.0.0 | 8085 (internal) | 2.0 | 2 GB | Output validation |
| memory | mas/memory:1.0.0 | 8083 (internal) | 2.0 | 4 GB | Episodic + semantic memory |
| prometheus | prom/prometheus:v2.53.0 | 9090 | — | — | Metrics scraping |
| grafana | grafana/grafana:11.1.0 | 3000 | — | — | Dashboards |
| jaeger | jaegertracing/all-in-one:1.58 | 16686, 4317/4318 | — | — | Distributed tracing |

### YAML Anchor Pattern — `x-mas-defaults` and `x-agent-env`

All services inherit a common base configuration via the `&mas-defaults` YAML anchor. This anchor injects three shared concerns into every service block using the `<<: *mas-defaults` merge key: (1) restart policy set to `unless-stopped`, (2) membership in the `mas-overlay` bridge network, and (3) structured JSON logging configured with `json-file` driver at 50 MB maximum file size and a 5-file rotation window.

All 7 agent containers additionally inherit the `&agent-env` environment block via `<<: *agent-env`, which injects the shared runtime wiring: `HMAC_KEY`, `RABBITMQ_URL`, `POSTGRES_URL`, `REDIS_URL`, `QDRANT_URL`, and the OpenTelemetry `OTEL_EXPORTER_OTLP_ENDPOINT` pointing to the Jaeger collector at `http://jaeger:4317`.

### Health Check Defaults

Every service in the Compose file defines a Docker health check. The general pattern across all services is: `interval: 10–15s | timeout: 5–10s | retries: 5 | start_period: 20–40s`. Infrastructure services with longer startup windows (RabbitMQ, Qdrant) use a higher `start_period`. The startup script's `wait_for_healthy()` function polls each container by reading `docker inspect` JSON and parsing the health state with `jq` on a 2-second loop until healthy or the configured timeout is exceeded.

See `./docker-compose.yml` for the full source.

---

## 6. Service Endpoint Reference

| Service | URL | Access | Notes |
|---|---|---|---|
| Gateway API | http://localhost:8080 | Public | Primary external interface |
| Orchestrator | http://localhost:8081 | Internal | `/health`, `/ready`, `/metrics` |
| Planner | http://localhost:8082 | Internal | `/health`, `/ready` |
| Memory | http://localhost:8083 | Internal | `/health`, `/ready`, `/query` |
| RabbitMQ Mgmt | http://localhost:15672 | Internal | Credentials: `mas` / `$RABBITMQ_PASS` |
| Grafana | http://localhost:3000 | Internal | Credentials: `admin` / configured `GRAFANA_PASS` |
| Jaeger UI | http://localhost:16686 | Internal | Distributed trace explorer |
| Prometheus | http://localhost:9090 | Internal | Raw metrics scrape targets and query UI |
| Vault (optional `vault-dev` profile) | http://vault:8200 | Internal | Compose-network-only endpoint; for host-side checks use `docker compose exec vault vault status` |

---

## 7. Useful Operational Commands

Live logs from all services:

```bash
docker compose logs -f
```

Live logs from a specific service:

```bash
docker compose logs -f orchestrator
```

Scale executor pool up or down:

```bash
docker compose up -d --scale executor=5
```

Check container health status:

```bash
docker compose ps
```

Graceful shutdown (30-second drain):

```bash
docker compose down --timeout 30
```

Hard stop + remove volumes — **DESTRUCTIVE** — all persistent data lost:

```bash
docker compose down -v
```

Rotate HMAC signing key manually with overlap material retained and restart affected services:

```bash
MAS_ROTATE_HMAC=true GRAFANA_PASS='your-grafana-password' ./startup.sh
```

Force Prometheus configuration reload (no container restart required):

```bash
curl -X POST http://localhost:9090/-/reload
```

---

## 8. Security Checklist

Complete all items before promoting to a production or internet-facing environment. Items marked with default credential warnings are the highest priority.

- [ ] Replace all `changeme` passwords (`POSTGRES_PASS`, `REDIS_PASS`, `RABBITMQ_PASS`) before going live
- [ ] Remove `VAULT_TOKEN=root`; unseal Vault properly using auto-unseal (KMS) or Shamir key shares
- [ ] Verify `.secrets/` and `.env` remain ignored by Git — check with `git check-ignore -v .secrets/ .env`
- [ ] Enable TLS on the Gateway by wiring real TLS certificate and key material into the gateway container configuration
- [ ] Keep the optional `vault-dev` profile internal-only unless you explicitly opt into a local dev port mapping for debugging
- [ ] Rotate HMAC key on schedule by running `MAS_ROTATE_HMAC=true ./startup.sh`; verify modification time with `stat -c %y .secrets/hmac_key` (Linux) or `stat -f %Sm .secrets/hmac_key` (macOS)
- [ ] Enable RabbitMQ TLS by configuring `ssl_options` in `rabbitmq.conf` and mounting cert material
- [ ] Set Grafana `GF_SERVER_PROTOCOL=https` and mount a valid TLS certificate
- [ ] Review audit log retention policy: 90 days hot storage, 365 days cold storage
- [ ] Run `docker scan` (or equivalent — Trivy, Grype) on all custom agent images before every deployment

---

## 9. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Service stuck in "starting" / never reaches healthy | Image not yet pulled locally | Run `docker compose pull` before starting |
| Health check consistently fails at startup | Insufficient RAM; OOM killer terminating containers | Ensure ≥ 16 GB RAM available; check `dmesg` for OOM events |
| Gateway returns 401 Unauthorized | JWT public key mismatch between generator and gateway | Verify `jwt_public.pem` is correctly mounted into `/run/mas-secrets` |
| RabbitMQ fails to start / crashes on boot | Erlang cluster cookie mismatch on restart | Check `RABBITMQ_COOKIE` env var; delete `mas-rabbitmq` data volume if stale state persists |
| Qdrant container OOMKilled | 4 GB memory limit too low for loaded collections | Increase Qdrant memory limit in Compose `mem_limit` |
| Smoke test FAIL on Grafana (phase 7) | Grafana is slow to initialise on first boot | Wait 60–90 seconds, check `docker compose ps grafana`, then retry `curl http://localhost:3000/api/health` |
| `docker-compose: command not found` | Using Docker Compose v2 plugin (no standalone binary) | Use `docker compose` (space, no hyphen); alias: `alias docker-compose='docker compose'` |

---

*MAS Kit Generator | Multi-Agent System Deployment Bundle v1.0.0 | Internal Operations Use Only*
