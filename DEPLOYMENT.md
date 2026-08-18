# FIFA Auction Production Deployment

## 1. Architecture

The application is a Vite/React single-page frontend and a FastAPI/SQLAlchemy API in one repository.

### Local

1. The browser loads the Vite development server.
2. Vite proxies relative `/api` requests to Uvicorn on port 8000.
3. FastAPI runs the same routers and scoring/import services used in production.
4. SQLAlchemy uses `backend/auction_v2.db` when `DATABASE_URL` is not set.
5. The bundled workbook seeds each empty room independently.

### Vercel production

1. Vercel builds `frontend/dist` with the locked frontend dependencies.
2. Static requests are served from that build; SPA routes rewrite to `index.html`.
3. `/api/*` rewrites to the Python function at `api/index.py`.
4. The function imports the FastAPI application and bundled backend modules/workbook.
5. SQLAlchemy connects to the pooled Neon PostgreSQL URL in `DATABASE_URL`.
6. A PostgreSQL advisory lock makes schema creation and first seed safe across concurrent cold starts.
7. Room 1 and Room 2 retain separate players, teams, settings, transactions, sales, captains, backups, and leaderboards in PostgreSQL.

There are no background workers, long-running jobs, in-memory state stores, subprocesses, runtime-generated assets, or persistent local-file writes. Authentication is stateless; durable auction state is in PostgreSQL.

## 2. Environment variables

Copy `.env.example` for local development. Keep real values in `backend/.env` locally and in Vercel Project Settings in production. Never commit the real file.

| Name | Production | Purpose |
|---|---:|---|
| `DATABASE_URL` | Required | Pooled Neon PostgreSQL connection string. |
| `AUTH_SECRET` | Required | HMAC token-signing secret, at least 32 characters. |
| `AUTH_TOKEN_TTL_SECONDS` | Optional | Login lifetime; defaults to 43,200 seconds. |
| `ROOM1_ADMIN_USERNAME` | Optional | Defaults to `room1_admin`. |
| `ROOM1_ADMIN_PASSWORD` | Required | Room 1 administrator password. |
| `ROOM2_ADMIN_USERNAME` | Optional | Defaults to `room2_admin`. |
| `ROOM2_ADMIN_PASSWORD` | Required | Room 2 administrator password. |
| `SUPER_ADMIN_USERNAME` | Optional | Defaults to `super_admin`. |
| `SUPER_ADMIN_PASSWORD` | Required | Super-administrator password. |
| `ALLOWED_ORIGINS` | Required in practice | Comma-separated browser origins allowed by CORS. |
| `VITE_API_BASE` | Optional | Browser API prefix; defaults to `/api` and should remain relative on Vercel. |

Vercel supplies `VERCEL` automatically. The backend uses it only to reject missing secrets or an ephemeral SQLite production configuration.

Generate a signing secret locally, then paste the output into Vercel without saving it in source control:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 3. Dataset

- Production asset: `backend/FIFA AUCTION 2026.xlsx`
- Format: XLSX, four sheets (`GK`, `MF`, `DEF`, `ATT`)
- Repository size at audit: 25,933 bytes
- Valid imported result: 152 players per room
- Purpose: first-deployment seed, import template, and the default dataset for an empty room
- Production access: resolved from the backend module directory, never from a machine-specific path

The workbook is explicitly included in the Vercel Python function bundle. It is read-only at runtime. On an empty database, each room receives its own copy of the rows. A later super-admin import replaces only the selected room's dataset and activity.

Uploads support `.xlsx`, `.xls`, and `.csv`, are case-insensitive, and are limited to 4 MB so they remain below Vercel's 4.5 MB request limit. XLSX expanded content is limited to 32 MB to reduce compressed-file memory abuse. Validation completes before existing room data is changed.

## 4. Model and inference requirements

This repository contains no trained model, tokenizer, Transformer, ML/NLP preprocessing, inference pipeline, GPU dependency, or model artifact. Auction scoring is deterministic Python business logic in `backend/services/scoring.py`. No external inference service is needed.

## 5. External services

- Vercel: static frontend hosting and the FastAPI serverless function.
- Neon PostgreSQL: permanent data for both isolated auctions.

Use Neon's pooled connection string for serverless traffic. No object storage is required because the small read-only seed workbook is bundled; imports are parsed in memory and committed to PostgreSQL.

## 6. Reproducible build and checks

Required runtimes:

- Python 3.12 (pinned by `.python-version` for Vercel)
- Node.js 22.12 or newer

Run from the repository root:

```powershell
py -3.12 -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
npm --prefix frontend ci
backend\.venv\Scripts\python.exe -m pytest backend -q
npm --prefix frontend run lint
npm --prefix frontend run build
```

Vercel's configured build command is:

```text
npm --prefix frontend ci && npm --prefix frontend run build
```

The output directory is `frontend/dist`.

## 7. Local development

1. Copy `.env.example` to `backend/.env`.
2. Fill `AUTH_SECRET` and all three password variables. Leave `DATABASE_URL` unset to use local SQLite, or set a PostgreSQL development database.
3. Install the dependencies shown above.
4. Start the backend:

   ```powershell
   backend\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --reload --port 8000
   ```

5. In another terminal, start the frontend:

   ```powershell
   npm --prefix frontend run dev
   ```

6. Open `http://127.0.0.1:5173`.

The local browser and production browser both call relative `/api` URLs and execute the same API, import, auction, Best 8, chemistry, captain, and leaderboard logic.

## 8. Vercel and Neon deployment

1. Create a Neon project and database.
2. Copy the pooled connection string, including TLS settings. Percent-encode special characters in the database password if needed.
3. Import this repository into Vercel with the repository root as the project root.
4. Select Python 3.12 and a supported Node.js version meeting the frontend engine requirement.
5. Add every required server-side variable from the table to Production. Add equivalent isolated values to Preview only if preview deployments should be functional.
6. Set `ALLOWED_ORIGINS` to the exact Vercel production origin. Add preview origins as comma-separated entries only when they are trusted.
7. Leave `VITE_API_BASE` unset or set it to `/api`.
8. Deploy. The first API startup creates the schema, Rooms 1 and 2, 20 teams per room, default settings, and 152 player rows per room.
9. Verify `https://YOUR-DOMAIN/api/health` reports both API and database online.
10. Log in as each administrator and verify the room number, 20 teams, and 152 initial players. Make a test sale/reset in each room before the live event.

No local database, local server, hidden `.env`, manual dataset copy, or developer workstation is used by production.

## 9. Vercel configuration

`vercel.json` defines:

- the frontend production build and output directory;
- the single FastAPI Python function;
- only the backend Python sources and production workbook as extra function files;
- a 60-second maximum function duration;
- `/api/*` rewrites to FastAPI;
- SPA fallback routing for browser refreshes;
- basic browser security headers.

`.vercelignore` explicitly excludes local secrets, virtual environments, SQLite files, logs, caches, source `node_modules`, and prior build output.

## 10. API route status

All business routes were exercised through FastAPI's HTTP layer.

| Method | Route | Authentication / production status |
|---|---|---|
| GET | `/api/health` | Public; checks database connectivity. |
| POST | `/api/auth/login` | Public; environment-backed account login. |
| GET | `/api/auth/me` | Authenticated. |
| GET | `/api/players` | Authenticated and room-scoped. |
| GET | `/api/players/{player_id}` | Authenticated and room-scoped. |
| GET | `/api/teams` | Authenticated and room-scoped. |
| GET | `/api/teams/{team_id}` | Authenticated and room-scoped. |
| POST | `/api/teams/{team_id}/captain` | Authenticated and room-scoped. |
| POST | `/api/auction/sell` | Authenticated, room-scoped, row-locked on PostgreSQL. |
| POST | `/api/auction/unsold` | Authenticated and room-scoped. |
| POST | `/api/auction/undo` | Authenticated; only the latest sale can be undone. |
| POST | `/api/auction/return-to-pool` | Authenticated and room-scoped. |
| GET | `/api/auction/history` | Authenticated and room-scoped. |
| GET | `/api/results` | Authenticated and room-scoped. |
| POST | `/api/admin/import` | Super admin only; selected room only. |
| GET | `/api/admin/sample-template` | Authenticated. |
| GET | `/api/admin/backup` | Authenticated and room-scoped. |
| POST | `/api/admin/reset` | Authenticated and room-scoped. |
| GET | `/api/settings` | Authenticated and room-scoped. |
| PUT | `/api/settings` | Authenticated and room-scoped. |

Room administrators always use their token's room even if a conflicting `X-Room-ID` is sent. Only the super admin can select Room 1 or Room 2. API responses use `Cache-Control: no-store`.

## 11. Security and operational notes

- Passwords and signing secrets remain server-side deployment secrets.
- Tokens are HMAC-signed, expire, and are checked against the configured username/role/room mapping.
- User-provided team, player, and room identifiers are constrained by room-scoped database queries.
- SQLAlchemy parameterization is used; no shell commands or dynamic SQL are built from input.
- Imports are restricted to the super admin, size checked, parsed in memory, and validated before replacement.
- CORS should contain only trusted origins.
- Enable Vercel Firewall rate limiting for `/api/auth/login`; there is no distributed application-level login limiter.
- Browser tokens are stored in local storage. The frontend does not render raw user HTML, but a future cookie-based session would provide additional defense against a frontend XSS defect.

## 12. Known limitations

1. `Base.metadata.create_all` is sufficient for a new Neon database but is not a versioned migration system. Add Alembic before a future schema-changing release.
2. Backup export exists, but the original application has no backup-restore endpoint.
3. Dataset requests above 4 MB require direct object storage/upload architecture because Vercel caps function request bodies at 4.5 MB.
4. A real Neon connection and authenticated remote Vercel build must still be verified in the target accounts. Local production simulation cannot prove account permissions, DNS, or provider configuration.

None of these changes removes existing auction functionality. Item 4 is the final deployment-account verification step, not a code fallback.

## 13. Troubleshooting

### `DATABASE_URL is required on Vercel`

Add the pooled Neon URL to the same Vercel environment (Production or Preview) being deployed.

### `Authentication is not configured` or startup lists missing variables

Add `AUTH_SECRET` and all three password variables. Redeploy after changing environment variables.

### Database connection failure

Confirm the URL is the pooled Neon URL, TLS is enabled, special password characters are encoded, the database is active, and the Vercel environment has the latest value.

### Frontend loads but API returns 404

Deploy from the repository root and keep the committed `vercel.json`. Do not set `VITE_API_BASE` to localhost.

### Nested frontend route returns 404 on refresh

Confirm the SPA fallback rewrite in `vercel.json` is present.

### Dataset seed fails

Confirm `backend/FIFA AUCTION 2026.xlsx` is committed and appears in the Python function bundle. Startup intentionally fails instead of silently substituting random data.

### Import returns 413

Use a file no larger than 4 MB. Larger imports need an object-storage upload flow before they can be supported on Vercel.

## 14. Architectural changes made for production

- Replaced legacy Vercel `builds`/`routes` configuration with build, function, output, header, and rewrite settings.
- Prevented Vercel from silently using non-persistent SQLite.
- Added fail-fast production secret validation.
- Made clean-database bootstrap atomic and concurrency-safe on PostgreSQL.
- Included only required backend sources and the real workbook in the function bundle.
- Added upload, archive-expansion, filename, and settings validation.
- Added PostgreSQL row locking around auction mutations and stricter undo semantics.
- Added database-aware health checks and no-cache API responses.
- Added route-level regression coverage for authentication, isolation, auction behavior, data management, and every business route.

