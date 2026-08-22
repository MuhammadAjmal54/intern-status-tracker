from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, wait_for_db
from .candidate_routes import router as candidate_router
from .status_routes import router as status_router
from .statistics_routes import router as statistics_router


app = FastAPI(
    title="Intern Status Tracker",
    description="API for tracking candidate daily work status",
    version="1.0.0",
)


# =========================
# CORS Middleware
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# Startup: wait for DB & create tables
# =========================

@app.on_event("startup")
def on_startup():
    wait_for_db()
    Base.metadata.create_all(bind=engine)


# =========================
# Include Routers
# =========================

app.include_router(candidate_router)
app.include_router(status_router)
app.include_router(statistics_router)


# =========================
# Root & Health
# =========================

@app.get("/")
def root():
    return {
        "message": "Intern Status Tracker API is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }