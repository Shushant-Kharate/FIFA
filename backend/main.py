import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
import models
from routers import players, teams, auction, results, admin
from services.excel_import import process_excel_import, generate_sample_excel

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FIFA Auction Management System API",
    description="Backend API for 25-team live FIFA player auction",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(teams.router)
app.include_router(auction.router)
app.include_router(results.router)
app.include_router(admin.router)

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "FIFA AUCTION 2026.xlsx")
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                res = process_excel_import(f.read(), "FIFA AUCTION 2026.xlsx", db)
                print(f"Auto-imported real players from FIFA AUCTION 2026.xlsx: {res.message}")
        else:
            player_count = db.query(models.Player).count()
            if player_count == 0:
                sample_bytes = generate_sample_excel()
                process_excel_import(sample_bytes, "fifa_players_sample.xlsx", db)
                print("Auto-seeded database with sample FIFA players and 25 teams!")
    except Exception as e:
        print(f"Error during startup auto-import: {e}")
    finally:
        db.close()

@app.get("/api/health")
def health_check():
    return {"status": "online", "message": "FIFA Auction API operational"}
