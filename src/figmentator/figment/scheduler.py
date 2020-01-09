"""
This module implements an asyncio based scheduler for generating figments. It balances
the desire for batching versus the need to generate realtime results. It does so by
having a threshold for how long to wait to collect a batch before executing the model.
"""
import logging
from typing import Dict, List, Optional, Tuple, Type, Union
from asyncio import (
    Queue,
    Event,
    gather,
    wait_for,
    ensure_future,
    get_event_loop,
    TimeoutError as AsyncTimeoutError,
)
from asyncio.futures import Future
from concurrent.futures import Executor, ProcessPoolExecutor, CancelledError

from pydantic import BaseSettings, Field

from figmentator.models.figment import FigmentContext
from figmentator.models.storium import SceneEntry
from figmentator.models.suggestion import SuggestionType
from figmentator.figment.base import Figmentator
from figmentator.figment.factory import get_figmentator, remove_figmentator
from figmentator.utils import camel_case, snake_case


async def execute(
    tasks: List[Future],
    err_msg: str,
    ignore: Union[Type[Exception], Tuple[Type[Exception], ...]] = tuple(),
):
    """
    Execute a list of coroutines
    """
    loop = get_event_loop()
    for result in await gather(*tasks, return_exceptions=True):
        if ignore and isinstance(result, ignore):
            continue

        if isinstance(result, Exception):
            loop.call_exception_handler({"message": err_msg, "exception": result})


class _SettingsFactory:
    """
    This class automatically creates a unique settings class for each suggestion type
    """

    def __init__(self):
        """
        Loop through all suggestion types and create a class for each suggestion type
        """
        self.settings: Dict[SuggestionType, BaseSettings] = {}
        for suggestion_type in SuggestionType:
            settings_cls = type(
                camel_case(suggestion_type.value) + "SchedulerSettings",
                (BaseSettings,),
                {
                    "Config": type(
                        "Config",
                        (BaseSettings.Config,),
                        {
                            "env_prefix": "FIG_SCHEDULER_"
                            + snake_case(suggestion_type).upper()
                            + "_"
                        },
                    ),
                    "__annotations__": {
                        "wait_time": float,
                        "max_batch_size": int,
                        "num_workers": int,
                    },
                    "wait_time": Field(
                        0.1,
                        description="How many seconds to wait to accumulate a batch",
                    ),
                    "max_batch_size": Field(
                        10, description="The maximum batch size to generate at once"
                    ),
                    "num_workers": Field(
                        3,
                        description="How many workers can process batches concurrently",
                    ),
                },
            )

            self.settings[suggestion_type] = settings_cls()


_FigmentatorSchedulerSettings = _SettingsFactory()


class FigmentatorResource:
    """
    A context manager to keep track of the state of the Figmentator. It allows
    for catching figmentator exceptions in order to reload the Figmentator.
    """

    def __init__(self, suggestion_type: SuggestionType, num_workers: int):
        self.count = 0
        self.ready = Event()
        self.errored = False
        self.loop = get_event_loop()
        self.num_workers = num_workers
        self.suggestion_type = suggestion_type

        self.executor: Executor
        self.figmentator: Figmentator

    async def __aenter__(self):
        await self.ready.wait()
        self.count += 1

    async def __aexit__(self, *exc):
        self.count -= 1
        if not self.ready.is_set() and not self.count:
            await self.renew()

    async def renew(self):
        """
        Release and reacquire the underlying resources """
        await self.release()
        await self.acquire()

    async def acquire(self):
        """ Replace the current figmentator """
        # Make all workers block on processing another batch
        self.ready.clear()
        logging.info("Creating process pool for %s", self.suggestion_type)
        self.executor = ProcessPoolExecutor(self.num_workers)

        logging.info("Acquiring figmentator for %s", self.suggestion_type)
        self.figmentator = await get_figmentator(self.suggestion_type)
        self.ready.set()

    async def release(self):
        """
        Release all resources associated with the Figmentator
        """
        self.ready.clear()
        if hasattr(self, "executor"):
            logging.info("Shutting down executor")
            self.executor.shutdown()
            del self.executor

        if hasattr(self, "figmentator"):
            logging.info("Removing figmentator for %s", self.suggestion_type)
            await remove_figmentator(self.figmentator)
            del self.figmentator

    async def process(
        self, queue: Queue, futures: List[Future], batch: List[FigmentContext]
    ):
        """ Have the Figmentator process a batch """
        try:
            results = await self.loop.run_in_executor(
                self.executor, self.figmentator.figmentate, batch
            )
            for future, result in zip(futures, results):
                # Set the result of the future
                future.set_result(result)

                # Need to notify the task queue for each item in the batch
                queue.task_done()
        except Exception as e:  # pylint:disable=broad-except
            logging.error("Caught exception: %s", str(e))
            self.ready.clear()
            for future in futures:
                # Set the exception on the future
                future.set_exception(e)

                # Need to notify the task queue for each item in the batch
                queue.task_done()


class FigmentScheduler:
    """
    This class does all the heavy lifting of asynchronously executing models while
    balancing the tradeoff between throughput and realtime results.
    """

    def __init__(self, suggestion_type: SuggestionType):
        """
        Initialize the scheduler
        """

        self.suggestion_type = suggestion_type
        self.settings = _FigmentatorSchedulerSettings.settings[suggestion_type]
        logging.info("Using settings: %s", self.settings.json())

        self.queue: Queue = Queue()
        self.loop = get_event_loop()
        self.workers: List[Future] = []
        self.figmentator = FigmentatorResource(
            self.suggestion_type, self.settings.num_workers  # type:ignore
        )

    async def startup(self):
        """ Initialize the workers """
        logging.info("Starting up figmentator for %s", self.suggestion_type)
        num_workers = self.settings.num_workers  # type:ignore
        await self.figmentator.acquire()
        self.workers = [ensure_future(self.main_loop()) for _ in range(num_workers)]

    async def shutdown(self):
        """ Shutdown the workers """
        # Wait until the queue is fully processed
        logging.info("Waiting for queue to drain")
        await self.queue.join()

        # Cancel all our worker tasks
        logging.info("Cancelling workers")
        for worker in self.workers:
            worker.cancel()

        # Wait until all worker tasks are cancelled
        await execute(
            self.workers,
            "unhandled exception during figmentator shutdown",
            CancelledError,
        )

        # Release Figmentator resources
        await self.figmentator.release()
        del self.figmentator

        # Clear out the workers
        self.workers = []

    async def main_loop(self):
        """ Consume a batch of tasks and execute them """
        while True:
            tasks = [await self.queue.get()]
            while len(tasks) < self.settings.max_batch_size:  # type:ignore
                try:
                    tasks.append(
                        await wait_for(
                            self.queue.get(), self.settings.wait_time  # type:ignore
                        )
                    )
                except AsyncTimeoutError:
                    break

            async with self.figmentator:
                await self.figmentator.process(self.queue, *zip(*tasks))

    async def figmentate(self, context: FigmentContext) -> Optional[SceneEntry]:
        """
        Schedule the figmentator to run and return the result.
        """
        future = self.loop.create_future()
        await self.queue.put((future, context))

        result = await future

        return result


class _FigmentSchedulerCollection:
    """
    This is a collection of figment schedulers, one per suggestion type
    """

    def __init__(self):
        """ Initialize the object """
        self.schedulers = {
            suggestion_type: FigmentScheduler(suggestion_type)
            for suggestion_type in SuggestionType
        }

    async def startup(self):
        """ Initialize the figment schedulers """
        startup_tasks = []
        for scheduler in self.schedulers.values():
            startup_tasks.append(scheduler.startup())

        await execute(startup_tasks, "unhandled exception during figmentator startup")

    async def shutdown(self):
        """ Shutdown the figment schedulers """
        shutdown_tasks = []
        for scheduler in self.schedulers.values():
            shutdown_tasks.append(scheduler.shutdown())

        await execute(shutdown_tasks, "unhandled exception during figmentator shutdown")

    async def figmentate(
        self, suggestion_type: SuggestionType, context: FigmentContext
    ) -> Optional[SceneEntry]:
        """
        Schedule the figmentator to run and return the result.
        """
        return await self.schedulers[suggestion_type].figmentate(context)


Figmentators = _FigmentSchedulerCollection()
