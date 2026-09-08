# Deployment

The public demo is two Render services from the `main` branch of this repository:
a static site for the client and a Docker web service for the API.

- Client: <https://signalroom-web.onrender.com>
- API: <https://signalroom-api.onrender.com>

Everything hosted is synthetic, and the demo runs without a model key.

## Why the free tier is enough

The API seeds its rooms at startup by replaying committed recordings, so it rebuilds
its own state on every boot. That removes the reason the first deployment needed a
persistent disk. A restart or a redeploy loses nothing that matters, because the four
recorded rooms come back identically and anything a visitor created was disposable.

The cost is a cold start. The service sleeps when idle, so the first request after a
quiet period waits for the container plus a few seconds of seeding.

## API service

| Setting | Value |
|---|---|
| Type | Docker web service |
| Dockerfile | `apps/api/Dockerfile` |
| Build context | `apps/api` |
| Health check | `/health` |
| Instances | 1 |

Environment:

- `SIGNALROOM_CORS_ORIGINS` set to the client origin, comma separated for more than one.
  Localhost is always allowed by a regex in `main.py`, so development needs no entry here.
- No model key. The image defaults to `SIGNALROOM_MODEL_MODE=replay`, which cannot make a
  network call to a provider. Adding a key and setting the mode to `auto` would enable live
  analysis of a pasted transcript, at which point everything pasted is public.

The image copies `evals/fixtures` and `recordings` and points `SIGNALROOM_FIXTURES_DIR` and
`SIGNALROOM_RECORDINGS_DIR` at them. Both paths otherwise resolve relative to the source
tree, which does not survive `pip install` into a container. The start command honours an
injected `PORT`.

## Client static site

| Setting | Value |
|---|---|
| Type | Static site |
| Build command | `cd apps/web && npm ci && npm run build` |
| Publish directory | `apps/web/dist` |

Environment: `VITE_API_URL` set to the API origin. `VITE_SIGNALROOM_API_URL` is read as a
fallback because the first deployment used that name. The value is compiled into the bundle,
so changing it needs a fresh build. It is a public URL, never a secret.

## What is not built

- No authentication. Every room on the hosted API is readable and writable by anyone with
  the URL, which is why nothing but synthetic material may be pasted into it.
- No rate limiting and no abuse controls.
- No custom domain, no multi-region, no zero-downtime deploys.
- Uploaded reference files and any room a visitor creates disappear on the next restart.

## History

The first public build of SignalRoom is preserved on the `codex-initial-build` branch. It is
the scaffold that [AUDIT.md](../AUDIT.md) examines, kept so the audit can be checked against
the code it describes.
