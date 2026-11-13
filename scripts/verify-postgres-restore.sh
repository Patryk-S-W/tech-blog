#!/usr/bin/env bash
set -euo pipefail
umask 077

# Usage: bash scripts/verify-postgres-restore.sh TRUSTED_CUSTOM_DUMP
# Docker access is privileged. Only restore trusted dumps; no live target is accepted.
fail() { printf '%s\n' "$1" >&2; exit 1; }
[[ $# == 1 && -f $1 && -s $1 ]] || fail 'Usage: verify-postgres-restore.sh TRUSTED_CUSTOM_DUMP'
dump=$1
temporary=$(mktemp -d)
container=''
cleanup() {
    status=$?
    if [[ -n $container ]]; then
        docker rm -f "$container" >/dev/null 2>&1 || { printf 'Disposable container cleanup failed.\n' >&2; status=1; }
    fi
    rmdir -- "$temporary"
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
name="techblog-restore-${temporary##*/}"
# tmpfs overrides the image's data volume; there is no persistent storage or network.
created=$(docker create --name "$name" --network none --tmpfs /var/lib/postgresql/data \
    --env POSTGRES_HOST_AUTH_METHOD=trust --env POSTGRES_DB=restore_check postgres:17-alpine 2>/dev/null) \
    || fail 'Could not create disposable PostgreSQL container.'
[[ $created =~ ^[a-f0-9]{64}$ ]] || fail 'Docker did not return a container ID.'
container=$created
docker start "$container" >/dev/null 2>&1 || fail 'Could not start disposable PostgreSQL container.'
ready=false
for ((attempt=0; attempt<60; attempt++)); do
    if docker exec "$container" pg_isready -U postgres -d restore_check >/dev/null 2>&1; then ready=true; break; fi
    sleep 1
done
[[ $ready == true ]] || fail 'Disposable PostgreSQL readiness timed out.'
docker exec -i "$container" pg_restore --exit-on-error --no-owner --no-privileges \
    -U postgres -d restore_check < "$dump" >/dev/null 2>&1 || fail 'Disposable restore failed.'
tables=$(docker exec "$container" psql -X -A -t -v ON_ERROR_STOP=1 -U postgres -d restore_check \
    -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" 2>/dev/null) \
    || fail 'Restored database verification failed.'
[[ $tables =~ ^[0-9]+$ ]] && (( tables > 0 )) || fail 'Restored database has no public tables.'
printf 'Restore verified: %s public tables.\n' "$tables"
