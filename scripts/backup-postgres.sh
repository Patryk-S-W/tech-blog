#!/usr/bin/env bash
set -euo pipefail
umask 077

# Local dumps contain account/token data; they do not protect against host loss.
# Usage: bash scripts/backup-postgres.sh MANIFEST PROJECT_DIRECTORY PROJECT ENV_FILE OUTPUT_DIRECTORY PORT
# Supply every Compose context explicitly; PORT is the container's PostgreSQL port.
fail() { printf '%s\n' "$1" >&2; exit 1; }
[[ $# == 6 ]] || fail 'Usage: backup-postgres.sh MANIFEST PROJECT_DIRECTORY PROJECT ENV_FILE OUTPUT_DIRECTORY PORT'
manifest=$1 directory=$2 project=$3 env_file=$4 output=$5 port=$6
[[ -f $manifest && -d $directory && -f $env_file && $project =~ ^[a-z0-9][a-z0-9_-]*$ ]] || fail 'Invalid backup context.'
[[ $port =~ ^[0-9]{1,5}$ ]] && (( 10#$port >= 1 && 10#$port <= 65535 )) || fail 'Invalid PostgreSQL port.'
mkdir -p -- "$output"
[[ -O $output && ! -L $output ]] || fail 'Output directory must be owned by the current user and not a symlink.'
chmod 700 -- "$output"
temporary=$(mktemp -d "$output/.backup.XXXXXXXXXX")
published_checksum=''
complete=false
cleanup() {
    if [[ $complete == false && -n $published_checksum ]]; then rm -f -- "$published_checksum"; fi
    rm -rf -- "$temporary"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
compose=(docker compose --project-directory "$directory" --env-file "$env_file" -f "$manifest" -p "$project")
name="postgres-$(date -u +%Y%m%dT%H%M%SZ)-${temporary##*.}.dump"
dump="$temporary/$name"
"${compose[@]}" exec -T postgres sh -c \
    'exec pg_dump --format=custom --no-password --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --port="$1"' sh "$port" \
    > "$dump" 2>/dev/null || fail 'PostgreSQL dump failed.'
[[ -s $dump ]] || fail 'PostgreSQL dump was empty.'
"${compose[@]}" exec -T postgres pg_restore --list < "$dump" >/dev/null 2>&1 || fail 'Dump validation failed.'
(cd "$temporary" && sha256sum -- "$name" > "$name.sha256")
# Hard links publish complete files atomically without ever replacing an existing backup.
ln -- "$temporary/$name.sha256" "$output/$name.sha256" || fail 'Checksum destination already exists or cannot be created.'
published_checksum="$output/$name.sha256"
if ! ln -- "$dump" "$output/$name"; then
    fail 'Dump destination already exists or cannot be created.'
fi
complete=true
printf 'Local backup created: %s\n' "$name"
