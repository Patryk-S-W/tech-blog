# TechBlog

![Angular21](https://img.shields.io/badge/Angular-17-brightgreen)
![Vercel](https://img.shields.io/github/deployments/Patryk-S-W/tech-blog-frontend/production.svg?logo=vercel&label=vercel)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Patryk-S-W_tech-blog-frontend&metric=alert_status)](https://sonarcloud.io/dashboard?id=Patryk-S-W_tech-blog-frontend)
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
![GitHub last commit](https://img.shields.io/github/last-commit/Patryk-S-W/tech-blog-frontend.svg)
[![StackShare](http://img.shields.io/badge/tech-stack-0690fa.svg?style=flat)](https://stackshare.io/Patryk-S-W/tech-blog-frontend)

![Angular](https://img.shields.io/badge/-Angular-DD0031?style=for-the-badge&logoColor=white&logo=Angular)
![.NET](https://img.shields.io/badge/-.NET-5027D5?style=for-the-badge&logoColor=white&logo=.NET)
![PostgreSQL](https://img.shields.io/badge/-PostgreSQL-4169E1?style=for-the-badge&logoColor=white&logo=postgresql)


The TechBlog project is a fullstack application written in the Angular and .NET that is used to publish articles related to technology, programming and topics related to artificial intelligence.

The repository is used as an orchestration layer for the whole project. The frontend and backend are kept as separate repositories and connected here through Git submodules.

## System requirements

- Node v22+ (see `frontend/.nvmrc`)
- Angular v21+
- .NET 10.0+

## Getting started

```bash
git clone --recurse-submodules https://github.com/Patryk-S-W/tech-blog
cd tech-blog
docker compose up
```

Frontend: http://localhost:4200  
Backend API: http://localhost:8080/api  
Swagger: http://localhost:8080/swagger

## Architecture

```mermaid
graph TD
    User[User / Browser]

    subgraph RootRepo[tech-blog]
        Compose[Docker Compose]
        GitSubmodules[Git Submodules]
        Env[.env / .env.example]
    end

    subgraph FrontendRepo[tech-blog-frontend]
        Node[Node v22+]
        Nx[Nx Workspace]
        Angular[Angular v21+]

        subgraph FrontendApp[Frontend Application]
            App[Angular App]
            Routes[Angular Router]
            Pages[Pages / Features]
            SharedUI[Shared UI Components]
            DataAccess[Data Access / API Clients]
            Assets[Assets / Styles]
        end

        Node --> Nx
        Nx --> Angular
        Angular --> App
        App --> Routes
        Routes --> Pages
        Pages --> SharedUI
        Pages --> DataAccess
        App --> Assets
    end

    subgraph BackendRepo[tech-blog-backend]
        Dotnet[.NET 10.0+]
        Api[ASP.NET Core Web API]
        Controllers[Controllers]
        Services[Application Services]
        Auth[JWT Authentication]
        Mapping[DTOs / Mapping]
        EF[Entity Framework Core]
    end

    subgraph Database[PostgreSQL]
        Users[(Users)]
        Articles[(Articles / Posts)]
        Projects[(Projects)]
        Announcements[(Announcements)]
    end

    User --> App

    Compose --> FrontendRepo
    Compose --> BackendRepo
    Compose --> Database

    GitSubmodules --> FrontendRepo
    GitSubmodules --> BackendRepo
    Env --> Compose

    DataAccess --> Api

    Dotnet --> Api
    Api --> Controllers
    Controllers --> Services
    Controllers --> Auth
    Services --> Mapping
    Services --> EF

    EF --> Users
    EF --> Articles
    EF --> Projects
    EF --> Announcements
```

## Runtime Flow

```mermaid
sequenceDiagram
    participant Browser as User / Browser
    participant Frontend as Angular v21+ Frontend
    participant API as .NET 10 API
    participant Auth as JWT Auth
    participant DB as PostgreSQL

    Browser->>Frontend: Open blog
    Frontend->>Frontend: Resolve route with Angular Router
    Frontend->>API: Request data through API client
    API->>Auth: Validate JWT when endpoint is protected
    API->>DB: Query data with EF Core
    DB-->>API: Return entities
    API-->>Frontend: Return DTO response
    Frontend-->>Browser: Render page
```

## Repository Layout

```mermaid
graph LR
    Main[tech-blog]

    Main --> Compose[docker-compose.yml]
    Main --> Frontend[frontend submodule<br/>tech-blog-frontend]
    Main --> Backend[backend submodule<br/>tech-blog-backend]

    Frontend --> Nx[Nx Workspace]
    Nx --> AngularApp[Angular v21+ App]
    Nx --> FrontendLibs[libs / shared / data-access]

    Backend --> DotnetApi[.NET 10.0+ Web API]
    DotnetApi --> Controllers[Controllers]
    DotnetApi --> Services[Services]
    DotnetApi --> Data[Data / EF Core]
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
