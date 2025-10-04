import threading
from typing import Any, Callable, Tuple

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
    