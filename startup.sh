#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

MAS_ENV="${MAS_ENV:-production}"
MAS_VERSION="${MAS_VERSION:-1.0.0}"
MAS_COMPOSE_FILE="${MAS_COMPOSE_FILE:-docker-compose.yml}"
MAS_LOG_DIR="${MAS_LOG_DIR:-./logs}"
MAS_HEALTH_TIMEOUT="${MAS_HEALTH_TIMEOUT:-120}"
POSTGRES_PASS="${POSTGRES_PASS:-changeme}"
REDIS_PASS="${REDIS_PASS:-changeme}"
RABBITMQ_PASS="${RABBITMQ_PASS:-changeme}"
RABBITMQ_COOKIE="${RABBITMQ_COOKIE:-mas-secret-cookie}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"
GRAFANA_PASS="${GRAFANA_PASS:-admin}"
LOG_LEVEL="${LOG_LEVEL:-info}"

readonly SCRIPT_DIR

BLUE=$'\033[1;34m'
GREEN=$'\033[1;32m'
YELLOW=$'\033[1;33m'
RED=$'\033[1;31m'
RESET=$'\033[0m'

COMPOSE_CMD=()
COMPOSE_FILE_PATH=""
PYTHON_BIN=""

resolve_path() {
  if [[ "$1" == /* ]]; then
    printf '%s\n' "$1"
  else
    printf '%s/%s\n' "$SCRIPT_DIR" "$1"
  fi
}

log_phase() {
  printf '%s==>%s %s\n' "$BLUE" "$RESET" "$1"
}

log_info() {
  printf '%s[INFO]%s %s\n' "$GREEN" "$RESET" "$1"
}

log_warn() {
  printf '%s[WARN]%s %s\n' "$YELLOW" "$RESET" "$1"
}

log_error() {
  printf '%s[ERROR]%s %s\n' "$RED" "$RESET" "$1" >&2
}

fail() {
  log_error "$1"
  exit 1
}

compose() {
  local cmd=("${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE_PATH")
  if [[ -f "$SCRIPT_DIR/.env" ]]; then
    cmd+=(--env-file "$SCRIPT_DIR/.env")
  fi

  "${cmd[@]}" "$@"
}

detect_compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
  else
    fail "Docker Compose v2 plugin or docker-compose binary is required."
  fi
}

detect_python() {
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    fail "Python 3 is required to write a safely quoted .env file."
  fi
}

file_mtime() {
  if stat -c %Y "$1" >/dev/null 2>&1; then
    stat -c %Y "$1"
  else
    stat -f %m "$1"
  fi
}

file_age_seconds() {
  local now
  now="$(date +%s)"
  echo $((now - "$(file_mtime "$1")"))
}

ensure_hmac_key() {
  local hmac_file="$SCRIPT_DIR/.secrets/hmac_key"
  local previous_hmac_file="$SCRIPT_DIR/.secrets/hmac_key.previous"

  if [[ -f "$hmac_file" ]] && [[ "$(file_age_seconds "$hmac_file")" -le 86400 ]]; then
    log_info "Reusing existing HMAC key (<24h old)."
    return
  fi

  if [[ -f "$hmac_file" ]]; then
    cp "$hmac_file" "$previous_hmac_file"
    chmod 600 "$previous_hmac_file"
    log_warn "Rotating stale HMAC key; previous key retained for overlap rollout."
  fi

  (
    umask 077
    openssl rand -hex 32 >"$hmac_file"
  )
  chmod 600 "$hmac_file"
  log_info "Generated fresh 256-bit HMAC key."
}

ensure_jwt_keypair() {
  local private_key="$SCRIPT_DIR/.secrets/jwt_private.pem"
  local public_key="$SCRIPT_DIR/.secrets/jwt_public.pem"

  if [[ -f "$private_key" && -f "$public_key" ]]; then
    return
  fi

  (
    umask 077
    openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out "$private_key" >/dev/null 2>&1
    openssl rsa -in "$private_key" -pubout -out "$public_key" >/dev/null 2>&1
  )
  chmod 600 "$private_key" "$public_key"
  log_info "Generated RS256 4096-bit JWT key pair."
}

ensure_ca_material() {
  local ca_key="$SCRIPT_DIR/.secrets/ca.key"
  local ca_crt="$SCRIPT_DIR/.secrets/ca.crt"

  if [[ -f "$ca_key" && -f "$ca_crt" ]]; then
    return
  fi

  (
    umask 077
    openssl req -x509 -nodes -newkey rsa:4096 \
      -keyout "$ca_key" \
      -out "$ca_crt" \
      -days 365 \
      -subj "/CN=MAS Local CA" >/dev/null 2>&1
  )
  chmod 600 "$ca_key" "$ca_crt"
  log_info "Generated mTLS CA certificate (365 days)."
}

dotenv_quote() {
  "$PYTHON_BIN" -c 'import json, sys; print(json.dumps(sys.argv[1]))' "$1"
}

write_env_file() {
  local hmac_key
  local previous_hmac_key=""
  hmac_key="$(tr -d '\n' <"$SCRIPT_DIR/.secrets/hmac_key")"
  if [[ -f "$SCRIPT_DIR/.secrets/hmac_key.previous" ]]; then
    previous_hmac_key="$(tr -d '\n' <"$SCRIPT_DIR/.secrets/hmac_key.previous")"
  fi

  {
    printf 'MAS_ENV=%s\n' "$(dotenv_quote "$MAS_ENV")"
    printf 'MAS_VERSION=%s\n' "$(dotenv_quote "$MAS_VERSION")"
    printf 'MAS_COMPOSE_FILE=%s\n' "$(dotenv_quote "$MAS_COMPOSE_FILE")"
    printf 'MAS_LOG_DIR=%s\n' "$(dotenv_quote "$MAS_LOG_DIR")"
    printf 'MAS_HEALTH_TIMEOUT=%s\n' "$(dotenv_quote "$MAS_HEALTH_TIMEOUT")"
    printf 'POSTGRES_PASS=%s\n' "$(dotenv_quote "$POSTGRES_PASS")"
    printf 'REDIS_PASS=%s\n' "$(dotenv_quote "$REDIS_PASS")"
    printf 'RABBITMQ_PASS=%s\n' "$(dotenv_quote "$RABBITMQ_PASS")"
    printf 'RABBITMQ_COOKIE=%s\n' "$(dotenv_quote "$RABBITMQ_COOKIE")"
    printf 'VAULT_TOKEN=%s\n' "$(dotenv_quote "$VAULT_TOKEN")"
    printf 'GRAFANA_PASS=%s\n' "$(dotenv_quote "$GRAFANA_PASS")"
    printf 'LOG_LEVEL=%s\n' "$(dotenv_quote "$LOG_LEVEL")"
    printf 'HMAC_KEY=%s\n' "$(dotenv_quote "$hmac_key")"
    if [[ -n "$previous_hmac_key" ]]; then
      printf 'HMAC_PREVIOUS_KEY=%s\n' "$(dotenv_quote "$previous_hmac_key")"
    fi
  } >"$SCRIPT_DIR/.env"
  chmod 600 "$SCRIPT_DIR/.env"
  log_info "Wrote minimal .env file."
}

wait_for_healthy() {
  local service="$1"
  local timeout="$2"
  local start_time current_ids healthy_count total_count container_id inspect_json has_health status

  start_time="$(date +%s)"

  while true; do
    current_ids=()
    while IFS= read -r container_id; do
      if [[ -n "$container_id" ]]; then
        current_ids+=("$container_id")
      fi
    done < <(compose ps -q "$service" | sed '/^$/d')

    if [[ "${#current_ids[@]}" -eq 0 ]]; then
      if (( "$(date +%s)" - start_time >= timeout )); then
        fail "Timed out waiting for container IDs for service '$service'."
      fi
      sleep 2
      continue
    fi

    healthy_count=0
    total_count="${#current_ids[@]}"

    for container_id in "${current_ids[@]}"; do
      inspect_json="$(docker inspect "$container_id" 2>/dev/null || true)"
      if [[ -z "$inspect_json" ]]; then
        continue
      fi
      IFS=$'\t' read -r has_health status <<EOF
$(printf '%s' "$inspect_json" | jq -r '[.[0].State.Health != null, (if .[0].State.Health != null then .[0].State.Health.Status else .[0].State.Status end)] | @tsv')
EOF
      if [[ "$has_health" == "true" && "$status" == "healthy" ]] || [[ "$has_health" == "false" && "$status" == "running" ]]; then
        healthy_count=$((healthy_count + 1))
      fi
    done

    if [[ "$healthy_count" -eq "$total_count" ]]; then
      log_info "Service '$service' is healthy (${healthy_count}/${total_count})."
      return
    fi

    if (( "$(date +%s)" - start_time >= timeout )); then
      compose ps "$service" || true
      fail "Timed out waiting for service '$service' to become healthy."
    fi

    sleep 2
  done
}

wait_for_scale() {
  local service="$1"
  local expected="$2"
  local timeout="$3"
  local start_time count

  start_time="$(date +%s)"

  while true; do
    count="$(compose ps -q "$service" | sed '/^$/d' | wc -l | tr -d ' ')"
    if [[ "$count" == "$expected" ]]; then
      log_info "Service '$service' reached ${expected} replicas."
      return
    fi

    if (( "$(date +%s)" - start_time >= timeout )); then
      fail "Timed out waiting for $service to reach ${expected} replicas."
    fi

    sleep 2
  done
}

graceful_shutdown() {
  if [[ -n "${COMPOSE_FILE_PATH:-}" ]] && [[ -f "$COMPOSE_FILE_PATH" ]]; then
    log_warn "Signal received, shutting down stack with 30-second drain..."
    compose down --timeout 30 || true
  fi
}

ensure_overlay_network() {
  docker network inspect mas-overlay >/dev/null 2>&1 || \
    docker network create --driver bridge --subnet 172.28.0.0/16 mas-overlay >/dev/null
}

validate_prometheus_config() {
  if command -v promtool >/dev/null 2>&1; then
    promtool check config "$SCRIPT_DIR/prometheus.yml" >/dev/null
    return
  fi

  docker run --rm \
    -v "$SCRIPT_DIR/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
    --entrypoint promtool \
    prom/prometheus:v2.53.0 \
    check config /etc/prometheus/prometheus.yml >/dev/null
}

preflight_checks() {
  log_phase "Phase 0 · Preflight checks"

  command -v docker >/dev/null 2>&1 || fail "Docker is required."
  command -v curl >/dev/null 2>&1 || fail "curl is required."
  command -v jq >/dev/null 2>&1 || fail "jq is required."
  command -v openssl >/dev/null 2>&1 || fail "openssl is required."

  detect_compose
  detect_python

  COMPOSE_FILE_PATH="$(resolve_path "$MAS_COMPOSE_FILE")"

  [[ -f "$COMPOSE_FILE_PATH" ]] || fail "Compose file not found: $COMPOSE_FILE_PATH"

  docker info --format '{{json .}}' | jq -e '.ServerVersion' >/dev/null || fail "Docker daemon is not responding."
  ensure_overlay_network
  if command -v promtool >/dev/null 2>&1; then
    validate_prometheus_config
  else
    log_warn "promtool not found locally; Prometheus config will be validated after image pull."
  fi
  compose config >/dev/null
  log_info "Compose syntax is valid."

  local free_kb
  free_kb="$(df -Pk "$SCRIPT_DIR" | awk 'NR==2 {print $4}')"
  if (( free_kb < 10485760 )); then
    log_warn "Available disk space is below 10 GB."
  else
    log_info "Disk space check passed."
  fi
}

bootstrap_secrets() {
  log_phase "Phase 1 · Bootstrap secrets"

  mkdir -p "$SCRIPT_DIR/.secrets"
  chmod 700 "$SCRIPT_DIR/.secrets"

  ensure_hmac_key
  ensure_jwt_keypair
  ensure_ca_material
  write_env_file
}

prepare_infrastructure() {
  log_phase "Phase 2 · Prepare infrastructure"
  local log_dir_path

  ensure_overlay_network
  log_info "Bridge network mas-overlay is ready."

  local volume
  for volume in mas-postgres mas-redis mas-qdrant mas-rabbitmq mas-grafana; do
    docker volume inspect "$volume" >/dev/null 2>&1 || docker volume create "$volume" >/dev/null
  done
  log_info "Named Docker volumes are ready."

  log_dir_path="$(resolve_path "$MAS_LOG_DIR")"
  mkdir -p "$log_dir_path"
  log_info "Host log directory is ready at $log_dir_path."
}

pull_images() {
  log_phase "Phase 3 · Pull images"
  compose pull --quiet
  validate_prometheus_config
  log_info "Requested pulls for all images in the Compose bundle."
}

start_infrastructure() {
  log_phase "Phase 4 · Start infrastructure"

  compose up -d postgres redis qdrant rabbitmq vault

  local service
  for service in postgres redis qdrant rabbitmq vault; do
    wait_for_healthy "$service" "$MAS_HEALTH_TIMEOUT"
  done
}

start_agents() {
  log_phase "Phase 5 · Start agents"

  compose up -d jaeger
  wait_for_healthy jaeger "$MAS_HEALTH_TIMEOUT"

  compose up -d gateway orchestrator planner memory

  local service
  for service in gateway orchestrator planner memory; do
    wait_for_healthy "$service" "$MAS_HEALTH_TIMEOUT"
  done

  compose up -d --scale executor=3 executor critic
  wait_for_scale executor 3 "$MAS_HEALTH_TIMEOUT"
  wait_for_healthy executor "$MAS_HEALTH_TIMEOUT"
  wait_for_healthy critic "$MAS_HEALTH_TIMEOUT"
}

start_observability() {
  log_phase "Phase 6 · Start observability"

  compose up -d prometheus grafana

  local service
  for service in prometheus grafana; do
    wait_for_healthy "$service" "$MAS_HEALTH_TIMEOUT"
  done

  log_info "Grafana:    http://localhost:3000"
  log_info "Jaeger UI:  http://localhost:16686"
  log_info "Prometheus: http://localhost:9090"
}

probe_http_endpoint() {
  local name="$1"
  local url="$2"
  local start_time

  start_time="$(date +%s)"

  while true; do
    if curl --fail --silent --show-error "$url" >/dev/null; then
      log_info "PASS · $name"
      return 0
    fi

    if (( "$(date +%s)" - start_time >= MAS_HEALTH_TIMEOUT )); then
      log_warn "FAIL · $name"
      return 1
    fi

    sleep 2
  done
}

smoke_tests() {
  log_phase "Phase 7 · Smoke tests"

  local pass_count=0
  local fail_count=0
  local check
  local name
  local url

  for check in \
    "Gateway|http://localhost:8080/health" \
    "Orchestrator|http://localhost:8081/health" \
    "Memory|http://localhost:8083/health" \
    "Grafana|http://localhost:3000/api/health" \
    "Prometheus|http://localhost:9090/-/healthy"; do
    name="${check%%|*}"
    url="${check##*|}"

    if probe_http_endpoint "$name" "$url"; then
      pass_count=$((pass_count + 1))
    else
      fail_count=$((fail_count + 1))
    fi
  done

  log_info "Smoke tests complete: ${pass_count} passed / ${fail_count} failed."

  if (( fail_count > 0 )); then
    fail "One or more smoke tests failed."
  fi
}

main() {
  trap graceful_shutdown INT TERM

  preflight_checks
  bootstrap_secrets
  prepare_infrastructure
  pull_images
  start_infrastructure
  start_agents
  start_observability
  smoke_tests

  log_info "Deployment bundle startup completed successfully."
}

main "$@"
