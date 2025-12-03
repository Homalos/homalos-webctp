import logging
import uuid
from abc import ABC, abstractmethod
from queue import Queue, Empty
from typing import Callable, Any

import anyio
from anyio.abc import TaskGroup


class BaseClient(ABC):
    """
    BaseClient is the boundary of websocket and client,
    and the boundary of async code and sync code.
    It is responsible for controlling the status of CTP client.
    """

    def __init__(self) -> None:
        self._rsp_callback: Callable[[dict[str, Any]], None] | None = None
        self._task_group: TaskGroup | None = None
        self._running: bool = False
        self._queue: Queue = Queue()
        self._client = None
        self._client_lock: anyio.Lock = anyio.Lock()
        self._stop_event: anyio.Event | None = None
        self._call_map: dict[str, Callable[[dict[str, Any]], int]] = {}
   
    @property
    def rsp_callback(self) -> Callable[[dict[str, Any]], None]:
        return self._rsp_callback

    @rsp_callback.setter
    def rsp_callback(self, callback: Callable[[dict[str, Any]], None]) -> None:
        self._rsp_callback = callback
    
    @property
    def task_group(self) -> TaskGroup:
        return self._task_group
    
    @task_group.setter
    def task_group(self, task_group: TaskGroup) -> None:
        self._task_group = task_group
    
    def on_rsp_or_rtn(self, data: dict[str, Any]) -> None:
        """Callback to handle response or return data from CTP client"""
        self._queue.put_nowait(data)

    async def start(self, user_id: str, password: str) -> None:
        """
        Start the CTP client with user credentials.
        
        NOTE: This if-clause avoids the following scenario:
        1. start a background coroutine
        2. start login
        3. login failed
        4. start login again
        """
        async with self._client_lock:
            if not self._client:
                self._client = await anyio.to_thread.run_sync(
                    self._create_ctp_client, user_id, password
                )
                self._client.rsp_callback = self.on_rsp_or_rtn
                self._init_call_map()
                # Use UUID to generate unique task name for better tracking and security
                task_name = f"{uuid.uuid4().hex[:8]}-{self._get_client_type()}-bg-task"
                self._task_group.start_soon(self.run, name=task_name)
            await anyio.to_thread.run_sync(self._client.connect)

    async def stop(self) -> None:
        """Stop the CTP client and cleanup resources"""
        logging.debug(f"stopping {self._get_client_type()} client")
        self._running = False
        if self._stop_event:
            await self._stop_event.wait()
            self._stop_event = None
        
        if self._client:
            await anyio.to_thread.run_sync(self._client.release)
        logging.debug(f"{self._get_client_type()} client stopped")

    async def run(self) -> None:
        """Background coroutine to process messages from the queue"""
        logging.info(f"start to run new {self._get_client_type()} coroutine")
        self._stop_event = anyio.Event()
        self._running = True
        while self._running:
            await self._process_a_message(1.0)
        logging.info(f"stop running {self._get_client_type()} coroutine")
        self._stop_event.set()

    async def _process_a_message(self, wait_time: float):
        """Process a single message from the queue"""
        try:
            rsp = await anyio.to_thread.run_sync(
                self._queue.get, True, wait_time, cancellable=True
            )
            await self.rsp_callback(rsp)
        except Empty:
            pass
        except Exception as e:
            logging.exception(f"Exception in {self._get_client_type()} client: {e}")

    @abstractmethod
    def _create_ctp_client(self, user_id: str, password: str):
        """Create the specific CTP client instance (Td or Md)"""
        pass
    
    @abstractmethod
    def _init_call_map(self):
        """Initialize the call map for request routing"""
        pass
    
    @abstractmethod
    def _get_client_type(self) -> str:
        """Return the client type name for logging purposes"""
        pass
