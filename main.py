from fastapi import FastAPI
from db import models
from db.database import engine
from routers import user, ingredient_router
from auth import authentication
from fastapi.middleware.cors import CORSMiddleware
from auth import authentication
import threading
from resources.logger import Logger
from resources.background_task_queue import BackgroundTaskQueue
from auth.authentication import delete_unverified_users
from contextlib import asynccontextmanager
from resources.core.cache import start_sync_thread

UNVERIFIED_CLEAN_INTERVAL_HOURS = 5 * 3600
_scheduler_started = False
_stop_scheduler_event = threading.Event()
logger = Logger()
task_queue = BackgroundTaskQueue()

@asynccontextmanager
async def lifespan(app: FastAPI):
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

def scheduler():
    """
    Periodically schedules the deletion of unverified users.
    This function runs in a loop, adding the `delete_unverified_users` task 
    to the background queue at a fixed interval.
    """
    while not _stop_scheduler_event.is_set():
        try:
            logger.info("Scheduler is running: queuing task to delete unverified users.")
            task_queue.add_task(delete_unverified_users)
            task_queue.add_task(start_sync_thread)
            # Wait for the configured interval, but check for the stop event periodically.
            _stop_scheduler_event.wait(UNVERIFIED_CLEAN_INTERVAL_HOURS)
        except Exception as e:
            logger.error(f"An error occurred in the scheduler loop: {e}")
            # Avoid busy-looping on repeated errors
            _stop_scheduler_event.wait(60)

def schedule_tasks():
    """
    Starts the background scheduler for deleting unverified users.
    This function is triggered on application startup, ensures the scheduler
    is started only once, and logs its status.
    """
    global _scheduler_started
    if _scheduler_started:
        logger.warning("Scheduler already started. Skipping.")
        return

    task_queue.start()
    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()
    _scheduler_started = True
    logger.info("Background scheduler for deleting unverified users has been started.")

def stop_scheduler():
    """
    Signals the scheduler to stop gracefully during application shutdown.
    """
    logger.info("Application shutting down. Signaling scheduler to stop.")
    _stop_scheduler_event.set()