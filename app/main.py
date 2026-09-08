from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.users import router as users_router
from app.routers.categories import router as categories_router
from app.routers.transactions import router as transactions_router
from app.routers.dashboard import router as dashboard_router
from app.routers.reports import router as reports_router

from app.models import User, Category, Transaction


# ==========================================
# FastAPI App
# ==========================================

app = FastAPI(
    title="Expense Tracker API",
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://expense-tracker-frontend-six-ochre.vercel.app",
     ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Routers
# ==========================================

app.include_router(users_router)

app.include_router(categories_router)

app.include_router(transactions_router)

app.include_router(dashboard_router)

app.include_router(reports_router)


