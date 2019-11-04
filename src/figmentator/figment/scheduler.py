"""
This module implements an asyncio based scheduler for generating figments. It balances
the desire for batching versus the need to generate realtime results. It does so by
having a threshold for how long to wait to collect a batch before executing the model.
"""
from typing import Any, Dict, List
from asyncio import (
    Queue,
    gather,
    wait_for,
    ensure_future,
    get_event_loop,
    TimeoutError as AsyncTimeoutError,
)
from asyncio.futures import Future
from asyncio.events import AbstractEventLoop

from pydantic import BaseSettings

from figmentator.models.figment import FigmentContext
from figmentator.models.storium import SceneEntry
from figmentator.models.suggestion import SuggestionType
from figmentator.models.utils import Field
from figmentator.figment.base import Figmentator
from figmentator.figment.factory import get_figmentator
from figmentator.utils import camel_case, snake_case


class SchedulerSettings(BaseSettings):
    """ A class representing scheduler settings per suggestion type """

    wait_time: float = Field(
        0.1, description="""How many seconds to wait to accumulate a batch"""
    )

    max_batch_size: int = Field(
        10, description="""The maximum batch size for any single generator to run"""
    )

    num_workers: int = Field(
        3, description="""How many workers will process batches concurrently""",
    )


class _SettingsFactory:
    """
    This class automatically creates a unique settings class for each suggestion type
    """

    def __init__(self):
        """
        Loop through all suggestion types and create a class for each suggestion type
        """
        self.settings: Dict[SuggestionType, SchedulerSettings] = {}
        for suggestion_type in SuggestionType:
            settings_cls = type(
                camel_case(suggestion_type.value) + SchedulerSettings.__name__,
                (SchedulerSettings,),
                {
                    "Config": type(
                        "Config",
                        (object,),
                        {
                            "env_prefix": "FIG_SCHEDULER_"
                            + snake_case(suggestion_type).upper()
                            + "_"
                        },
                    )
                },
            )

            self.settings[suggestion_type] = settings_cls()


_FigmentatorSchedulerSettings = _SettingsFactory()


class FigmentScheduler:
    """
    This class does all the heavy lifting of asynchronously executing models while
    balancing the tradeoff between throughput and realtime results.
    """

    def __init__(self, suggestion_type: SuggestionType):
        """
        Initialize the scheduler
        """

        self.queue: Queue
        self.loop: AbstractEventLoop
        self.figmentator: Figmentator
        self.workers: List[Future[Any]]

        self.suggestion_type = suggestion_type
        self.settings = _FigmentatorSchedulerSettings.settings[suggestion_type]

    async def startup(self, figmentator: Figmentator):
        """ Initialize the workers """
        self.queue = Queue()
        self.loop = get_event_loop()
        self.figmentator = figmentator

        self.workers = [
            ensure_future(self.main_loop()) for _ in range(self.settings.num_workers)
        ]

    async def shutdown(self):
        """ Shutdown the workers """
        if self.queue:
            # Wait until the queue is fully processed
            await self.queue.join()

            # Cancel all our worker tasks
            for worker in self.workers:
                worker.cancel()

            # Wait until all worker tasks are cancelled
            gather(*self.workers, return_exceptions=True)

            # Clear out the workers
            self.workers = []

    async def main_loop(self):
        """ Consume a batch of tasks and execute them """
        while True:
            tasks = [await self.queue.get()]
            while len(tasks) < self.settings.max_batch_size:
                try:
                    tasks.append(
                        await wait_for(self.queue.get(), self.settings.wait_time)
                    )
                except AsyncTimeoutError:
                    break

            futures, batch = zip(*tasks)
            results = await self.loop.run_in_executor(
                None, self.figmentator.figmentate, batch
            )

            for future, result in zip(futures, results):
                # Set the result of the future
                future.set_result(result)

                # Need to notify the task queue for each item in the batch
                self.queue.task_done()

    async def figmentate(self, context: FigmentContext) -> SceneEntry:
        """
        Schedule the figmentator to run and return the result.
        """
        if not self.queue:
            raise RuntimeError(
                f"No figmentator available to handle {self.suggestion_type}!"
            )

        future = self.loop.create_future()
        await self.queue.put((future, context))

        return await future


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
            # Try to get the figmentator for this suggestion type first, if it doesn't
            # exist then there is no use in starting up
            try:
                figmentator = await get_figmentator(scheduler.suggestion_type)
                startup_tasks.append(scheduler.startup(figmentator))
            except ValueError:
                pass

        await gather(*startup_tasks)

    async def shutdown(self):
        """ Shutdown the figment schedulers """
        shutdown_tasks = []
        for scheduler in self.schedulers.values():
            shutdown_tasks.append(scheduler.shutdown())

        await gather(*shutdown_tasks)

    async def figmentate(
        self, suggestion_type: SuggestionType, context: FigmentContext
    ) -> SceneEntry:
        """
        Schedule the figmentator to run and return the result.
        """
        return await self.schedulers[suggestion_type].figmentate(context)


Figmentators = _FigmentSchedulerCollection()
