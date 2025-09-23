from fastapi import FastAPI
from db import models
from db.database import engine
from routers import user
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(user.router)
@app.get("/")
def read_root():
    return {"message": "MealTracker API is running"}

models.Base.metadata.create_all(engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)