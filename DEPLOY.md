# Deployment

Clone this repository with its pinned submodules:

```sh
git clone --recurse-submodules https://github.com/Patryk-S-W/tech-blog
cd tech-blog
cp .env.example .env
chmod 600 .env
```

Set independent random `POSTGRES_PASSWORD` and `JWT_SECRET` values, and a unique
`RELEASE` image tag in `.env`. Use a hexadecimal database password; the JWT key
must contain at least 64 random ASCII characters. Never commit `.env` or print
expanded Compose configuration into shared logs. Changing an environment value
does not rotate an existing PostgreSQL role's password.

## Local Docker

```sh
docker compose config --quiet
docker compose build backend
docker compose build frontend
docker compose up -d
curl --fail http://127.0.0.1:4200/health
```

The frontend serves SSR and proxies same-origin API requests. Only
`127.0.0.1:4200` is published; the database and backend stay on the private Docker
network. Docker bridge networking must work. Startup can briefly return 502 while
the backend applies its checked-in migrations.

## Existing VPS: host networking without touching Xray

`compose.production.yml` is a **standalone** Linux-only alternative, not an
override. Run it from the same repository root with `frontend/` and `backend/`
submodules present. Do not copy the sibling-checkout layout used during the
initial emergency deployment. Do not run the two Compose variants concurrently.

Host networking avoids Docker NAT/firewall changes on the existing VPS, but
removes container network isolation. PostgreSQL binds `127.0.0.1:15432`, the API
binds `127.0.0.1:18080`, and the frontend's Node SSR listener stays on loopback.
Nginx alone listens publicly on port 80. Ports 443 (Xray) and 2137 (SSH) are not
changed by this project. Keep existing firewall rules; allow only inbound TCP80
for the blog. Do not reload a firewall file that flushes live fail2ban/VPN rules.

Back up existing data before upgrading, because backend startup runs migrations:

```sh
umask 077
docker compose -f compose.production.yml exec -T postgres \
  pg_dump -h 127.0.0.1 -p 15432 -U techblog -d techblog -Fc > backup.dump
test -s backup.dump
docker compose -f compose.production.yml exec -T postgres \
  pg_restore --list < backup.dump > /dev/null
```

On a first installation there is no database to back up. Keep backup files
restricted and copy them off-host; rehearse restoration separately.

```sh
docker compose -f compose.production.yml config --quiet
# Build sequentially on the 2 GB VPS. Builds use host networking.
docker compose -f compose.production.yml build backend
docker compose -f compose.production.yml build frontend
docker compose -f compose.production.yml up -d
docker compose -f compose.production.yml ps
curl --fail http://127.0.0.1/health
curl --fail http://127.0.0.1/api/v1/blog/announcements
curl --fail http://127.0.0.1/api/v1/blog/projects
```

When migrating the initial deployment's server-only `.env`, reuse its database
password and map the existing `AppSettings__Token` value to `JWT_SECRET`; do not
generate a replacement database password against the existing volume. The old
`ConnectionStrings__Postgres_Db` entry is no longer needed by these manifests.
The named volume remains `tech-blog_postgres_data`.

Verify assets, deep links, SSR HTML and anonymous read APIs before accepting
traffic. Public account registration is removed in the backend and also blocked
at nginx; authenticated write APIs still trust existing accounts. Audit users
before reusing a database. No default account or demo content is seeded.
Controlled owner provisioning must use the retained application registration
handler through a trusted local maintenance process; no public bootstrap route
is provided. HTTP exposes passwords and tokens: do not log in over an untrusted
network. Use a trusted SSH tunnel until HTTPS is configured.

## Verification and rollback

Run the configuration regression check with Python 3 and Docker Compose available:

```powershell
python tests/verify_compose.py
```

It validates both manifests using temporary test-only environment values, and
checks private database/API access, API wiring, host bindings and persistent
volume names. It never starts containers.

Keep prior release tags. For a code-only rollback, restore the previous `RELEASE`
in `.env` and run `docker compose -f compose.production.yml up -d --no-build`.
Automatic migrations can make old code incompatible: database rollback requires
a verified pre-upgrade dump and a separately prepared restore target. Never
blindly restore over the only live database.

**Never run `down -v`, remove the database volume, or prune volumes as part of a
deployment.** Reboot persistence, backup restoration and HTTPS need their own
operational verification.
