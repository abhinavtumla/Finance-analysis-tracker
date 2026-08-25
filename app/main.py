from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import auth, categories, transactions, budgets

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Personal Finance Tracker API",
    description="Backend API for a personal finance tracker",
    version="0.1.0"
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(budgets.router)

@app.get("/")
def root():
    return {"message": "Finance Tracker API is running"}