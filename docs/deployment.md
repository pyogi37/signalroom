# Deployment plan

## First public demo

Deploy the React client as a Render Static Site and the FastAPI service as a single Render Docker Web
Service. This is the smallest safe public setup for the current local-first architecture.

The API persists SQLite, LangGraph checkpoint, and embedded Qdrant files below `/app/data`. Attach a
1 GB persistent disk at that exact path and set `SIGNALROOM_DATA_DIR=/app/data`. Render disks are
single-instance only, which matches the embedded Qdrant client; keep the API at exactly one instance.
Do not use a free or ephemeral API service for the public demo because its data would disappear on
restart or deployment.

### API service

- Service type: Docker Web Service
- Dockerfile: `apps/api/Dockerfile`
- Docker build context: `apps/api`
- Health check: `/health`
- Persistent disk: mount `/app/data`, start at 1 GB
- Environment: `SIGNALROOM_LLM_PROVIDER=local`
- Environment: `SIGNALROOM_DATA_DIR=/app/data`
- Environment: `SIGNALROOM_CORS_ORIGINS=https://<frontend-host>`
- Do not add a model key for the initial public demo. The deterministic local mode is reproducible and
  keeps all public demo content synthetic.

The Docker command respects the platform `PORT` variable. After the service is live, copy its HTTPS URL
for the frontend configuration.

### Frontend static site

- Service type: Static Site
- Build command: `cd apps/web && npm ci && npm run build`
- Publish directory: `apps/web/dist`
- Build environment: `VITE_SIGNALROOM_API_URL=https://<api-host>`

`VITE_SIGNALROOM_API_URL` is compiled into the static Vite build, so setting it requires a fresh frontend
deploy. It is a public URL, never a secret.

### Release order

1. Push the `main` branch to GitHub and confirm CI passes.
2. Create the API service, attach its disk, and deploy in deterministic-local mode.
3. Copy the API HTTPS URL into `VITE_SIGNALROOM_API_URL` for the static site build.
4. Copy the static-site HTTPS URL into `SIGNALROOM_CORS_ORIGINS` for the API, then redeploy it.
5. Smoke-test `/health`, the demo room, a new synthetic analysis, change request, follow-up, approval,
   and DOCX export from the hosted site.
6. Only then add a custom domain and, separately, a rotated provider key for optional live transcription
   or extraction.

## Known deployment limits

- This is a portfolio demo, not a multi-tenant production system.
- A persistent disk prevents horizontal scaling and zero-downtime API deploys in the current design.
- Public access has no authentication or per-user access control; keep all hosted material synthetic.
- Production scaling requires moving session/audit state to Postgres, using a managed Qdrant deployment
  or pgvector, and adding authentication, trace storage, rate limiting, and structured observability.

Render references: [persistent disks](https://render.com/docs/disks),
[Docker build context](https://render.com/docs/blueprint-spec), and
[static-site deployment](https://render.com/docs/static-sites).
