# FIFA Auction — Two-Room Administration

One application hosts two isolated FIFA auction competitions. Each room has its own 20 teams, player dataset, sales, settings, transactions, Best 8, chemistry bonuses, captains, backups, and leaderboard.

## Access model

- `room1_admin`: full control of Room 1 only.
- `room2_admin`: full control of Room 2 only.
- `super_admin`: full control of both rooms and a room switcher.
- Only the super admin can import a dataset. The selected room alone is replaced.

Credentials are read exclusively from environment variables. Do not place real passwords in source files.

For the complete production architecture, environment-variable reference, route matrix, Neon setup, Vercel deployment steps, limits, and troubleshooting, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Local development

Set the variables from `.env.example` in the shell or through a local secret manager. If `DATABASE_URL` is omitted, the backend uses `backend/auction_v2.db`.

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Frontend:

```powershell
cd frontend
npm run dev
```

Vite proxies `/api` to the local FastAPI server.

## Vercel + Neon deployment

1. Create a Neon PostgreSQL database and copy its pooled connection string.
2. Import this repository into Vercel.
3. Add every variable from `.env.example` to Vercel Project Settings → Environment Variables, using strong unique passwords and a random `AUTH_SECRET`.
4. Set `DATABASE_URL` to the Neon connection string and `ALLOWED_ORIGINS` to the final Vercel URL.
5. Deploy. The first application startup atomically creates both rooms and seeds each from `backend/FIFA AUCTION 2026.xlsx`.

The committed `vercel.json` routes `/api/*` to FastAPI and all other paths to the Vite frontend.
