# TechBlog

TechBlog is a personal technology blog built with Angular, ASP.NET Core and
PostgreSQL. This umbrella repository pins the independently versioned frontend
and backend as Git submodules.

## Repositories

- [Frontend](https://github.com/Patryk-S-W/tech-blog-frontend): Angular 21,
  NgModules, server-side rendering, Jest.
- [Backend](https://github.com/Patryk-S-W/tech-blog-backend): .NET 10,
  controllers, application/domain/infrastructure layers, EF Core and JWT.
- Database: PostgreSQL 17.

Use Node 22 for the frontend, the .NET 10 SDK for the backend, and Docker Engine
with Compose v2 for container deployment. The pinned frontend is not an Nx
workspace; use its npm scripts rather than `nx` commands.

## Start with Docker

```sh
git clone --recurse-submodules https://github.com/Patryk-S-W/tech-blog
cd tech-blog
cp .env.example .env
```

Fill in `.env` with independent random secrets: a hexadecimal
`POSTGRES_PASSWORD`, a `JWT_SECRET` of at least 64 ASCII characters, and a unique
`RELEASE` tag. Never commit that file.

```sh
docker compose config --quiet
docker compose up --build -d
```

Open **http://127.0.0.1:4200**. The frontend serves SSR and proxies API requests
to the backend; no public database or backend port is required.

| Endpoint | Purpose |
| --- | --- |
| `/health` | Backend readiness |
| `/api/v1/blog/announcements` | Published articles |
| `/api/v1/blog/projects` | Published projects |
| `/api/v1/blog/categories` | Article categories |

The backend applies checked-in EF migrations on startup. There is no default
account or demo content. Public registration is disabled because authenticated
accounts can edit content. See [DEPLOY.md](DEPLOY.md) for provisioning limits,
secrets, HTTPS precautions, backups and rollback.

## Development

```sh
cd frontend
npm ci
npm start
npm run test:ci
npm run build:prod
```

Frontend development API configuration is in
`frontend/src/environments/environment.ts`. Container production uses same-origin
API requests through nginx; setting a container `API_URL` does not rewrite an
Angular build.

Before starting or testing the backend, provide `ConnectionStrings__Postgres_Db`
for a reachable PostgreSQL database and `AppSettings__Token` for a signing key
of at least 64 UTF-8 bytes. Integration tests need a **separate disposable
database**, never the live database.

```sh
cd backend
dotnet run --project src/TechBlog.WebApi
dotnet test TechBlog.sln --configuration Release
```

## Layout

```text
tech-blog/
├── frontend/                    # Git submodule
│   ├── src/app/                 # Modules, services and stores
│   ├── server.ts                # Express / Angular SSR
│   └── Dockerfile
├── backend/                     # Git submodule
│   ├── src/TechBlog.Domain/
│   ├── src/TechBlog.Application/
│   ├── src/TechBlog.Infrastructure/
│   ├── src/TechBlog.WebApi/
│   └── tests/TechBlog.Tests/
├── docker-compose.yml           # Local bridge network
├── compose.production.yml       # Standalone Linux host-network deployment
└── DEPLOY.md
```

The production manifest preserves the existing VPS's Xray/SSH ports and binds
the database/API to loopback. Run it **instead of**, not alongside, the local
manifest. The deployment guide explains its reduced network isolation.

## Git workflow

Create a topic branch from `master`, keep separate conventional commits per
feature/fix, and open a pull request. Push frontend/backend commits before
updating this repository's submodule pins, so recursive clones can fetch them.
Do not merge umbrella pins until the referenced component changes are reviewed.

## License

[MIT](LICENSE).
