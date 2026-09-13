# Upstream architecture

Upstream uses a React/TypeScript/Vite frontend, served by Nginx alongside FastAPI and PostgreSQL. Alembic manages schema changes.

The browser uses same-origin `/api` requests. FastAPI authenticates requests and applies domain rules through services; async repositories own database queries and transactions. TanStack Query manages frontend server state, while URLs hold shareable filters and pagination.

- [Frontend architecture](architecture_frontend.md): navigation, state, sessions, forms and artwork.
- [Backend architecture](architecture_backend.md): authentication, content rules, read models and metadata fetching.
- [Product guide](product.md): implemented capabilities and visibility rules.
- [Operations](operations.md): setup requirements, checks and compatibility protections.
- [Engineering standards](../AGENT.md): dependency boundaries and implementation practices.
