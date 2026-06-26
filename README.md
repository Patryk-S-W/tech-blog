# TechBlog

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Patryk-S-W_tech-blog&metric=alert_status)](https://sonarcloud.io/dashboard?id=Patryk-S-W_tech-blog)
[![StackShare](http://img.shields.io/badge/tech-stack-0690fa.svg?style=flat)](https://stackshare.io/Patryk-S-W/tech-blog-frontend)
[![Frontend Build](https://img.shields.io/github/actions/workflow/status/Patryk-S-W/tech-blog-frontend/build.yaml?branch=master&label=frontend%20build&style=flat-square&logo=githubactions&logoColor=white)](https://github.com/Patryk-S-W/tech-blog-frontend/actions/workflows/build.yaml)

![Angular](https://img.shields.io/badge/-Angular_22-DD0031?style=for-the-badge&logoColor=white&logo=Angular)
![.NET](https://img.shields.io/badge/-.NET_10-5027D5?style=for-the-badge&logoColor=white&logo=.NET)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL_17-4169E1?style=for-the-badge&logoColor=white&logo=postgresql)
![Docker](https://img.shields.io/badge/-Docker-2496ED?style=for-the-badge&logoColor=white&logo=docker)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

The TechBlog project is a fullstack application written in the Angular and .NET that is used to publish articles related to technology, programming and topics related to artificial intelligence.

The repository is used as an orchestration layer for the whole project. The frontend and backend are kept as separate repositories and connected here through Git submodules.

## System requirements

- Node v22+ (see `frontend/.nvmrc`)
- Angular v21+
- .NET 10.0+

## Getting started

### Docker

```bash
git clone --recurse-submodules https://github.com/Patryk-S-W/tech-blog
cd tech-blog
cp .env.example .env
docker compose up --build
```

| Service          | URL                           |
| ---------------- | ----------------------------- |
| Frontend         | http://localhost:4200         |
| Backend API      | http://localhost:8080/api     |
| Swagger / Scalar | http://localhost:8080/swagger |
| Health check     | http://localhost:8080/health  |

### Development

```bash
# Frontend
cd frontend && npm i
npx nx serve blog          # dev server :4200
npx nx test blog           # vitest (unit)
npx nx e2e blog-e2e        # Playwright (e2e)
npx nx lint blog
npx nx graph               # dependency graph

# Backend
cd backend
dotnet run --project src/TechBlog.WebApi   # :8080
dotnet test                                 # tests

# EF Core — first migration
dotnet ef migrations add InitialCreate \
  --project src/TechBlog.Infrastructure \
  --startup-project src/TechBlog.WebApi
dotnet ef database update \
  --project src/TechBlog.Infrastructure \
  --startup-project src/TechBlog.WebApi
```

---

## Tech stack

| Layer               | Technology                            |
| --------------------- | -------------------------------------- |
| Frontend framework    | Angular 22 (standalone, zoneless, SSR) |
| Monorepo              | Nx 20                                  |
| Bundler               | esbuild                                |
| State management      | Signals + `resource()` API             |
| Styling               | SCSS + CSS custom properties           |
| Unit tests (frontend) | vitest-angular                         |
| E2E tests             | Playwright                             |
| Backend framework     | ASP.NET Core 10 Minimal API            |
| Architecture          | Clean Architecture                     |
| CQRS / mediator       | MediatR 12                             |
| Validation            | FluentValidation 11                    |
| Mapping               | AutoMapper 13                          |
| ORM                   | Entity Framework Core 10               |
| Database              | PostgreSQL 17 (Npgsql)                 |
| Auth                  | JWT Bearer                             |
| Hash                  | BCrypt.Net                             |
| Integration tests     | xUnit + Testcontainers.PostgreSql      |
| Assertions            | FluentAssertions                       |
| Mocking               | NSubstitute                            |
| Contenarization       | Docker Compose                         |
| CI/CD                 | GitHub Actions                         |

---



## Architecture

```mermaid
graph TB
    subgraph Browser["Browser"]
        direction TB
        APP["apps/blog\nAngular 22 · zoneless · SSR · esbuild"]

        subgraph LIBS["Nx Libraries"]
            direction LR
            FP["feature-posts\nPostListComponent\nPostDetailComponent"]
            FA["feature-auth\nLoginComponent"]
            DAP["data-access-posts\nPostStore · PostApiService\nsignal resource()"]
            DAA["data-access-auth\nAuthStore · AuthApiService"]
            UI["ui\nButton · Card · Spinner\nPagination · Tag · Badge"]
            ENV["environments\napiUrl"]
        end

        APP -->|"lazy load"| FP
        APP -->|"lazy load"| FA
        FP --> DAP
        FA --> DAA
        FP --> UI
        FA --> UI
        DAP --> ENV
        DAA --> ENV
    end

    subgraph DOCKER["Docker Compose"]
        direction TB

        subgraph NGINX["nginx :80"]
            STATIC["Angular SPA\n/usr/share/nginx/html"]
        end

        subgraph API["ASP.NET Core :8080"]
            direction TB
            WEB["WebApi\nMinimal API · JWT · Scalar"]

            subgraph CA["Clean Architecture"]
                direction TB
                APP_LAYER["Application\nMediatR CQRS\nFluentValidation\nAutoMapper"]
                DOMAIN["Domain\nPost · Author · Tag\nSlug (VO)\nDomain Events"]
                INFRA["Infrastructure\nEF Core 10 · Npgsql\nJwtTokenService\nDatabaseSeeder"]
            end

            WEB -->|"IMediator.Send()"| APP_LAYER
            APP_LAYER -->|"depends on"| DOMAIN
            APP_LAYER -->|"IPostRepository\nIUnitOfWork"| INFRA
            INFRA -->|"implements"| DOMAIN
        end

        subgraph DB["PostgreSQL 17 :5432"]
            TABLES["posts · authors · tags\npost_tags · app_users"]
        end

        NGINX -->|"/api/* proxy_pass"| API
        INFRA -->|"Npgsql"| DB
    end

    Browser -->|"HTTPS"| NGINX
    DAP -->|"GET /api/posts\nGET /api/posts/:slug"| API
    DAA -->|"POST /api/auth/login\nGET /api/auth/me"| API

    subgraph CICD["GitHub Actions"]
        FE_CI["frontend.yml\nlint → test → build → e2e"]
        BE_CI["backend.yml\nrestore → build → test → publish"]
    end
```

---

## Structure

```
tech-blog/                         ← umbrella repo
├── frontend/                      ← submodule → tech-blog-frontend
│   ├── apps/
│   │   ├── blog/                  ← Angular 22 app
│   │   │   ├── src/app/
│   │   │   │   ├── app.config.ts  ← zoneless, provideRouter, HttpClient
│   │   │   │   ├── app.routes.ts  ← lazy loading
│   │   │   │   ├── app.component.ts
│   │   │   │   └── core/auth/     ← interceptor, guard, token service
│   │   │   └── src/styles/        ← design tokens, reset, typography
│   │   └── blog-e2e/              ← Playwright tests
│   ├── libs/
│   │   ├── ui/                    ← Button, Card, Spinner, Pagination, Tag, Badge
│   │   ├── feature-posts/         ← PostListComponent, PostDetailComponent, PostCard
│   │   ├── feature-auth/          ← LoginComponent + authRoutes
│   │   ├── data-access-posts/     ← PostApiService, PostStore (signals + resource API)
│   │   ├── data-access-auth/      ← AuthApiService, AuthStore
│   │   └── environments/          ← apiUrl config
│   ├── nx.json
│   ├── Dockerfile                 ← multi-stage (builder → nginx)
│   └── nginx.conf
│
└── backend/                       ← submodule → tech-blog-backend
    ├── src/
    │   ├── TechBlog.Domain/       ← Post, Author, Tag, Slug (VO), domain events
    │   ├── TechBlog.Application/  ← CQRS queries/commands, behaviors, DTOs
    │   ├── TechBlog.Infrastructure/← EF Core, Npgsql, repositories, JWT, seeder
    │   └── TechBlog.WebApi/       ← Minimal API endpoints, middleware, Program.cs
    ├── tests/
    │   ├── TechBlog.Domain.Tests/        ← xUnit + FluentAssertions
    │   ├── TechBlog.Application.Tests/   ← xUnit + NSubstitute
    │   └── TechBlog.Infrastructure.Tests/← xUnit + Testcontainers (PostgreSQL)
    ├── TechBlog.sln
    └── Dockerfile                 ← multi-stage (sdk → aspnet runtime)
```

---

## Request flow

```mermaid
sequenceDiagram
    actor U as Użytkownik
    participant NG as Angular 22<br/>(Browser)
    participant NX as nginx
    participant API as Minimal API<br/>(WebApi)
    participant MED as MediatR<br/>Pipeline
    participant VAL as FluentValidation<br/>Behavior
    participant H as QueryHandler
    participant REPO as PostRepository<br/>(Infrastructure)
    participant PG as PostgreSQL 17

    U->>NG: otwiera stronę główną
    NG->>NX: GET /api/posts?page=1
    NX->>API: proxy_pass
    API->>MED: Send(GetPostsQuery)
    MED->>VAL: ValidationBehavior
    VAL-->>MED: valid ✓
    MED->>H: Handle(query)
    H->>REPO: GetPagedAsync(page, pageSize)
    REPO->>PG: SELECT ... WHERE is_published = true
    PG-->>REPO: rows
    REPO-->>H: List<Post>
    H-->>MED: PagedResult<PostDto>
    MED-->>API: result
    API-->>NX: 200 OK (JSON)
    NX-->>NG: response
    NG->>NG: PostStore.posts signal updated
    NG->>U: renderuje listę postów
```

---

## Clean Architecture

```mermaid
graph LR
    subgraph DOMAIN["Domain (jądro — zero zależności)"]
        E["Entities\nPost · Author · Tag"]
        VO["Value Objects\nSlug"]
        DE["Domain Events\nPostPublishedEvent"]
        I["Interfaces\nIPostRepository\nITagRepository\nIUnitOfWork"]
    end

    subgraph APP["Application (zależy tylko od Domain)"]
        Q["Queries\nGetPostsQuery\nGetPostBySlugQuery"]
        C["Commands\nCreatePostCommand\nUpdatePostCommand\nDeletePostCommand"]
        B["MediatR Behaviors\nValidationBehavior\nLoggingBehavior"]
        DTO["DTOs + AutoMapper\nPostDto · AuthorDto · TagDto"]
    end

    subgraph INFRA["Infrastructure (implementacje)"]
        CTX["TechBlogDbContext\nEF Core 10 · Npgsql"]
        REPO["Repositories\nPostRepository\nTagRepository"]
        JWT["JwtTokenService"]
        SEED["DatabaseSeeder"]
    end

    subgraph WEB["WebApi (wejście)"]
        EP["Endpoints\nPostsEndpoints\nAuthEndpoints\nTagsEndpoints"]
        MW["Middleware\nExceptionHandling"]
        EXT["Extensions\nJWT Auth\nCORS · Health"]
    end

    APP -->|"IPostRepository\nIUnitOfWork"| DOMAIN
    INFRA -->|"implements"| DOMAIN
    INFRA -->|"implements"| APP
    WEB -->|"IMediator.Send()"| APP
    WEB -.->|"nie zależy bezpośrednio"| DOMAIN
    WEB -.->|"nie zależy bezpośrednio"| INFRA
```

## License

MIT License

Copyright (c) 2024-2026 Patryk Sadowski

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.