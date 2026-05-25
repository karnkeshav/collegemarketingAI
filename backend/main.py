import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from database import init_db, AsyncSessionLocal
from models import State
from api.colleges import router as colleges_router
from api.contacts import router as contacts_router
from api.campaigns import router as campaigns_router
from api.scraper import router as scraper_router
from api.reports import router as reports_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialised")
    yield


app = FastAPI(
    title="CollegeMarketingAI",
    description="Discover and contact college officials across India",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(colleges_router)
app.include_router(contacts_router)
app.include_router(campaigns_router)
app.include_router(scraper_router)
app.include_router(reports_router)


@app.get("/api/states")
async def get_states():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(State).where(State.is_active == True))
        states = result.scalars().all()
        return [
            {"id": s.id, "name": s.name, "code": s.code}
            for s in states
        ]


@app.get("/health")
async def health():
    return {"status": "ok"}
