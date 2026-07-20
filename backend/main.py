"""
PromiseGuard API — AI-powered commitment intelligence platform.

25 endpoints across 9 routers.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from database import engine, Base, init_pgvector
import models  # noqa: F401 — imports all models so Base.metadata is populated

from routers.workspaces import router as workspaces_router
from routers.sources import router as sources_router
from routers.candidates import router as candidates_router
from routers.commitments import router as commitments_router
from routers.capabilities import router as capabilities_router
from routers.conflicts import router as conflicts_router
from routers.legal import router as legal_router
from routers.alerts import router as alerts_router
from routers.reports import router as reports_router
from routers.integrations import router as integrations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.execute(text("CREATE EXTENSION IF NOT EXISTS vector")))
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="PromiseGuard",
    description="AI-powered commitment intelligence. Track every customer promise from sales to fulfilment.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workspaces_router)
app.include_router(sources_router)
app.include_router(candidates_router)
app.include_router(commitments_router)
app.include_router(capabilities_router)
app.include_router(conflicts_router)
app.include_router(legal_router)
app.include_router(alerts_router)
app.include_router(reports_router)
app.include_router(integrations_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "promiseguard-api", "version": "0.1.0"}
