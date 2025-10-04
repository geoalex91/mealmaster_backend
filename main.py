from fastapi import FastAPI
from db import models
from db.database import engine
from routers import user, ingredient_router
from auth import authentication
from fastapi.middleware.cors import CORSMiddleware
from auth import authentication

app = FastAPI(lifespan=authentication.lifespan)
# Create database tables before including routers
models.Base.metadata.create_all(bind=engine)
app.include_router(authentication.router) 
app.include_router(user.router)
app.include_router(ingredient_router.router)

@app.get("/")
def read_root():
    return {"message": "MealTracker API is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to restrict origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)