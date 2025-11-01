from fastapi import FastAPI
from db import models
from db.database import engine
from routers import user, ingredient_router, recipe_router
from auth import authentication
from fastapi.middleware.cors import CORSMiddleware
from auth import authentication
from resources.logger import Logger
from resources.background_task_sheduler import schedule_tasks, stop_scheduler
from contextlib import asynccontextmanager
from resources.core.entity_cache import ingredient_cache, recipe_cache

logger = Logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    ingredient_cache.build_cache()  # Warm cache
    recipe_cache.build_cache()  # Warm cache
    schedule_tasks()
    try:
        yield   # Application runs here
    finally:
        stop_scheduler()

app = FastAPI(lifespan=lifespan)

# Create database tables before including routers
models.Base.metadata.create_all(bind=engine)
app.include_router(authentication.router) 
app.include_router(user.router)
app.include_router(ingredient_router.router)
app.include_router(recipe_router.router)

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
