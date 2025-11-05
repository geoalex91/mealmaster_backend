import threading
import time
from typing import Any, Callable, Tuple
from resources.logger import Logger
from auth.authentication import delete_unverified_users
from resources.core.entity_cache import ingredient_cache, recipe_cache

_scheduler_started = False
_stop_scheduler_event = threading.Event()
UNVERIFIED_CLEAN_INTERVAL_HOURS = 3 * 60
INGREDIENT_CACHE_SYNC_INTERVAL_HOURS = 2 * 60
RECIEPE_CACHE_SYNC_INTERVAL_HOURS = 2 * 60
logger = Logger()

class QueueNode:
    """
    Represents a node in a queue data structure.
    Attributes:
        data: The value stored in the node.
        next (QueueNode or None): Reference to the next node in the queue.
    """

    def __init__(self, data):
        self.data = data
        self.next = None

class CustomQueue:
    """
    A thread-safe queue implementation using a linked list and condition variables.
    This queue allows multiple threads to safely enqueue and dequeue items.
    Items are stored as nodes in a singly linked list. The queue supports blocking
    retrieval, so threads waiting to get an item will block until an item is available.
    Attributes:
        head (QueueNode): The first node in the queue.
        tail (QueueNode): The last node in the queue.
        lock (threading.Lock): A lock to protect access to the queue.
        condition (threading.Condition): A condition variable for blocking and notification.
    Methods:
        put(item: Tuple[Callable, tuple, dict]):
            Adds an item to the end of the queue and notifies waiting threads.
        get() -> Any:
            Removes and returns an item from the front of the queue.
            Blocks if the queue is empty until an item is available.
        is_empty() -> bool:
            Returns True if the queue is empty, False otherwise.
    """

    def __init__(self):
        self.head = None
        self.tail = None
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
    
    def put(self, item: Tuple[Callable, tuple, dict]):
        new_node = QueueNode(item)
        with self.condition:
            if self.tail is None:
                self.head = new_node
                self.tail = new_node
            else:
                self.tail.next = new_node
                self.tail = new_node
            self.condition.notify()
    
    def get(self) -> Any:
        with self.condition:
            while self.head is None:
                self.condition.wait()
            node = self.head
            self.head = self.head.next
            if self.head is None:
                self.tail = None
            return node.data
    
    def is_empty(self) -> bool:
        with self.lock:
            return self.head is None

class BackgroundTaskQueue:
    def __init__(self, workers: int = 2):
        self.queue = CustomQueue()
        self.workers = workers
        self._threads = []

    def add_task(self, func: Callable, *args, **kwargs):
        self.queue.put((func, args, kwargs))

    def worker(self):
        """
        Continuously processes tasks from the queue.
        Retrieves tasks from the internal queue and executes them. Each task is expected to be a tuple containing a callable,
        positional arguments, and keyword arguments. If an exception occurs during task execution, it is caught and an error
        message is printed.
        This method is intended to run indefinitely, typically in a background thread.
        Raises:
            Prints error messages to standard output if task execution fails.
        """

        while True:
            func, args, kwargs = self.queue.get()
            try:
                func(*args, **kwargs)
            except Exception as e:
                print(f"Error executing task: {e}")

    def start(self):
        for _ in range(self.workers):
                thread = threading.Thread(target=self.worker, daemon=True)
                thread.start()
                self._threads.append(thread)

    def join(self):
        for thread in self._threads:
            thread.join()

task_queue = BackgroundTaskQueue(1)

def schedule_activity(func: Callable, intervarl_hours: int):
    """
    Schedules a background activity by adding the task to the background queue.
    This function adds the specified task to the background task queue for execution.
    """
    while not _stop_scheduler_event.is_set():
        logger.info(f"Scheduler is running: queuing task to {func.__name__}.")
        task_queue.add_task(func)
        time.sleep(intervarl_hours)

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
    thread = threading.Thread(target=schedule_activity, args=(delete_unverified_users, UNVERIFIED_CLEAN_INTERVAL_HOURS), daemon=True)
    thread.start()
    thread2 = threading.Thread(target=schedule_activity, args=(ingredient_cache.start_sync_thread, INGREDIENT_CACHE_SYNC_INTERVAL_HOURS), daemon=True)
    thread2.start()
    thread3 = threading.Thread(target=schedule_activity, args=(recipe_cache.start_sync_thread, RECIEPE_CACHE_SYNC_INTERVAL_HOURS), daemon=True)
    thread3.start()
    _scheduler_started = True
    logger.info("Background scheduler for deleting unverified users has been started.")

def stop_scheduler():
    """
    Signals the scheduler to stop gracefully during application shutdown.
    """
    logger.info("Application shutting down. Signaling scheduler to stop.")
    _stop_scheduler_event.set()