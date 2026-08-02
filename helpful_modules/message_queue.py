"""
You can distribute any version of the Software created and distributed *before* 23:17:55.00 July 28, 2024 GMT-4
under the GNU General Public License version 3 or at your option, any  later option.
But versions of the code created and/or distributed *on or after* that date must be distributed
under the GNU *Affero* General Public License, version 3, or, at your option, any later version.

This file is part of The Discord Math Problem Bot Repo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Author: Samuel Guo (64931063+rf20008@users.noreply.github.com)
"""

import asyncio
import warnings
import inspect
import collections
import fractions
import heapq
import logging
import math
import time
import typing

import disnake

logging.basicConfig(level=logging.INFO)


class NotStartedError(RuntimeError):
    """An exception raised when trying to stop a MessageQueue that isn't started"""

    pass


class ThingToDo:
    """
    Represents a task with priority and creation time.

    Attributes:
        priority (int): Priority level of the task.
        time_created (float): Time when the task was created.
    """

    priority: int
    time_created: float
    __slots__ = ("priority", "time_created")

    def __init__(self, priority: int = 3000):
        """
        Initializes a ThingToDo instance with a given priority.

        Args:
            priority (int, optional): Priority level of the task. Defaults to 3000.
        """
        self.priority = priority
        self.time_created = time.time()

    @property
    def age(self):
        """
        Calculates the age of the task in seconds.

        Returns:
            float: Age of the task in seconds.
        """
        return time.time() - self.time_created

    def __eq__(self, other):
        """
        Checks if this task is equal to another task.

        Args:
            other (ThingToDo): Another ThingToDo instance to compare with.

        Returns:
            bool: True if both tasks are equal, False otherwise.
        """
        return isinstance(other, self.__class__) and self.priority == other.priority

    def __le__(self, other):
        """
        Checks if this task is less than or equal to another task.

        Args:
            other (ThingToDo): Another ThingToDo instance to compare with.

        Returns:
            bool: True if this task is less than or equal to the other task, False otherwise.
        """
        return self < other or self == other

    def __lt__(self, other):
        """
        Checks if this task is less than another task.

        Args:
            other (ThingToDo): Another ThingToDo instance to compare with.

        Returns:
            bool: True if this task is less than the other task, False otherwise.
        """
        if self.priority != other.priority:
            return self.priority < other.priority
        if self.age != other.age:
            return self.age > other.age
        return False

    async def act(self):
        """
        Placeholder method for task execution.

        Raises:
            NotImplementedError: If subclasses do not override this method.
        """
        raise NotImplementedError("Subclasses must implement this")

    def decrement_priority(self):
        """
        Decrements the priority of the task by 1.
        """
        self.priority -= 1

    def __str__(self):
        """
        Returns a string representation of the task.

        Returns:
            str: String representation of the task.
        """
        return f"ThingToDo[priority={self.priority}, age={self.age}]"

    def __call__(self):
        return self.act()


class MessageThing(ThingToDo):
    """
    Represents a message task derived from ThingToDo.

    Attributes:
        to (disnake.abc.Messageable): Destination to send the message.
        stuff (dict): Content of the message.
    """

    to: disnake.abc.Messageable
    stuff: dict
    __slots__ = ("priority", "time_created", "stuff", "to")

    async def act(self):
        """
        Sends the message to its destination asynchronously.
        """
        await self.to.send(**self.stuff)

    def __str__(self):
        """
        Returns a string representation of the message task.

        Returns:
            str: String representation of the message task.
        """
        return f"MessageThing[to={self.to}, stuff={self.stuff}, priority={self.priority}, age={self.age}]"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (
            super().__eq__(other) and self.to == other.to and self.stuff == other.stuff
        )


class FunctionThing(ThingToDo):
    __slots__ = ("priority", "time_created", "func", "args", "kwargs")

    def __init__(
        self,
        func: callable,
        priority: int = 3000,
        args: list | None = None,
        kwargs: dict | None = None,
    ):
        super().__init__(priority)
        if not callable(func):
            raise TypeError("Function must be callable")
        if self.args is None:
            self.args = args
        if not isinstance(args, collections.abc.Sequence):
            raise TypeError("Function args must be sequence")
        if self.kwargs is None:
            self.kwargs = kwargs
        if not isinstance(kwargs, collections.abc.Mapping):
            raise TypeError("Function kwargs must be dict")

    async def act(self):
        r = self.func(*self.args, **self.kwargs)
        if inspect.isawaitable(r):
            return await r
        return r


class MessageQueue:
    """
    Represents a priority queue for managing ThingToDo tasks asynchronously.

    Attributes:
        heap (list[ThingToDo]): Heapified list of tasks based on their priority.
        lock (asyncio.Lock): Asynchronous lock to manage concurrent access to the queue.
    """

    heap: list[tuple[ThingToDo, int, asyncio.Future]]
    lock: asyncio.Lock
    allowed_to_add: bool
    worker: "QueueWorker" | None
    counter: int
    __slots__ = ("heap", "lock", "allowed_to_add", "worker", "counter")

    def __init__(self):
        """
        Initializes an empty MessageQueue.
        """
        self.counter = 0
        self.worker = None
        self.allowed_to_add = True
        self.heap = []
        self.lock = asyncio.Lock()

    def is_empty(self):
        """
        Checks if the message queue is empty.

        Returns:
            bool: True if the queue is empty, False otherwise.
        """
        return len(self.heap) == 0

    async def decrement_priorities_periodically(self, interval=60):
        """
        Decrements the priority of all tasks in the queue periodically.

        Args:
            interval (int, optional): Interval in seconds between each decrement operation. Defaults to 60.
        """
        warnings.warn(
            "Decrementing priorities periodically is deprecated",
            DeprecationWarning,
            stacklevel=2,
        )
        while True:
            await asyncio.sleep(interval)
            await self.decrement_priorities()

    async def decrement_priorities(self):
        """
        Decrements the priority of all tasks in the queue once.
        Re-heapifies the queue after priorities are decremented.
        """
        async with self.lock:
            for item, _, fut in self.heap:
                item.decrement_priority()
            heapq.heapify(self.heap)
            logging.info("Priorities decremented and heap reheapified.")

    async def act_periodically(self, interval=1):
        """
        Executes the top task from the queue periodically.

        Args:
            interval (int, optional): Interval in seconds between each execution. Defaults to 1.
        """
        while True:
            await asyncio.sleep(interval)
            if self.is_empty():
                continue
            await self.act_on_top()

    async def act_on_top(self, raise_act_exc: bool = True):
        """
        Executes the top task from the queue.
        Logs successful execution or errors if any occur.
        Raises:
            RuntimeError: If the queue is empty
            Exception: Any exceptions the top task may raise
        """
        if self.is_empty():
            raise RuntimeError("Cannot send message from an empty MessageQueue")
        top = None
        async with self.lock:
            top, _, future = heapq.heappop(self.heap)
        if future.done():
            return
        try:
            future.set_result(await top.act())
            logging.info(f"Acted on: {top}")
        except Exception as e:
            future.set_exception(e)
            logging.error(f"Error while acting on top item: {e}", e)
            if raise_act_exc:
                raise e

    def act_every_so_often(self, APIRQPS=fractions.Fraction(1, 2)):
        """
        Executes the top task from the queue periodically based on an API request rate.

        Args:
            APIRQPS (fractions.Fraction, optional): API request rate in requests per second. Defaults to 1/2.
        """
        return self.start(
            send_interval=fractions.Fraction(1, 1) / APIRQPS,
            decrement_intervals_periodically_interval=float("inf"),
        )

    async def add_thing(self, thing: ThingToDo):
        """
        Adds a single task to the queue.

        Args:
            thing (ThingToDo): Task to be added to the queue.
        """
        if not self.allowed_to_add:
            raise RuntimeError("Cannot add task to queue (allowed_to_add is False).")
        async with self.lock:
            future = asyncio.get_running_loop().create_future()
            heapq.heappush(self.heap, (thing, self.counter, future))
            self.counter += 1
            logging.info(f"Added thing to heap: {thing}")
        return future

    async def add_things(self, things: list[ThingToDo]):
        """
        Adds multiple tasks to the queue.

        Args:
            things (list[ThingToDo]): List of tasks to be added to the queue.
        """
        if not self.allowed_to_add:
            raise RuntimeError("Cannot add task to queue (allowed_to_add is False).")
        C = len(things)
        N = len(self.heap)
        if not isinstance(things, list):
            raise TypeError(
                f"things is not a list, but an instance of {things.__class__.__name__}"
            )
        new_things = []
        async with self.lock:
            for thing in things:
                if not isinstance(thing, ThingToDo):
                    raise TypeError(
                        f"thing is not an instance of ThingToDo, but an instance of {thing.__class__.__name__}"
                    )

                new_things.append(
                    (thing, self.counter, asyncio.get_running_loop().create_future())
                )
                self.counter += 1
        if 2 * (C + N) > 4 * (C * math.log(N + C, base=2)):
            # strategy: re-heapify

            async with self.lock:
                self.heap.extend(new_things)
                heapq.heapify(self.heap)
        else:
            # strategy: add one at a time
            async with self.lock:
                for thing, ctr, fut in new_things:
                    heapq.heappush(self.heap, (thing, ctr, fut))

    async def empty(
        self,
        *,
        act: bool = True,
        timeout: float = 0.0,
        limit: int = -1,
        delete_undone_tasks: bool = True,
    ):
        """
        Empties the queue by executing and removing all tasks.

        Args:
            act (bool, optional): Flag indicating whether to execute tasks or just clear the queue. Defaults to True.
            timeout (float, optional): Time to wait between each task execution. Defaults to 0.0 (no wait).
            limit (int, optional): Maximum number of tasks to do. Ignored if act is false.
            delete_undone_tasks (bool, optional): Whether to delete undone tasks
        """

        if timeout < 0:
            raise ValueError("Timeout value cannot be negative.")

        if not act:
            async with self.lock:
                self.heap.clear()
            return

        num_rem_tasks = limit
        while not self.is_empty():
            await self.act_on_top()
            # async with self.lock:
            #    thing, future = heapq.heappop(self.heap)
            # if num_rem_tasks == -1 or num_rem_tasks > 0:
            #    await thing.act()
            if num_rem_tasks != -1:
                num_rem_tasks -= 1
                if num_rem_tasks == 0:
                    break

            if timeout:
                await asyncio.sleep(timeout)
        # remove everything else
        if len(self.heap) != 0 and delete_undone_tasks:
            async with self.lock:
                self.heap.clear()

    def start(self, *, send_interval=1):
        if self.worker is not None:
            raise RuntimeError("The queue already has a worker")
        self.worker = QueueWorker(self, send_interval)
        self.worker.start()

    async def stop(
        self,
        *,
        msg: str = "",
        empty: bool = True,
        act: bool = False,
        timeout: float = 0.0,
        limit: int = -1,
        delete_undone_tasks: int = -1,
    ):
        """
        Stops the MessageQueue by canceling periodic tasks and optionally emptying the queue.

        Args:
            msg (str, optional): Message to include in the cancellation reason (default is "").
            empty (bool, optional): Flag indicating whether to empty the queue (default is True).
            act (bool, optional): Flag indicating whether to execute tasks when emptying (default is False).
            timeout (float, optional): Time to wait between each task execution when emptying (default is 0.0).
            limit (int, optional): Maximum number of tasks to do

        Raises:
            NotStartedError: If the queue is not yet started when trying to stop.

        Notes:
            This method cancels the periodic execution tasks (`act_task` and `decrement_task`)
            and optionally empties the queue by executing and removing all tasks.
        """
        if self.worker is None:
            raise NotStartedError("This queue is not started yet")
        self.allowed_to_add = False
        if empty:
            await self.empty(
                act=act,
                timeout=timeout,
                limit=limit,
                delete_undone_tasks=delete_undone_tasks,
            )
        await self.worker.stop()


class QueueWorker:
    queue: MessageQueue
    _stopping: bool
    _task: asyncio.Task
    interval: float

    def __init__(self, queue: MessageQueue, interval: float = 0.1):
        self.queue = queue
        self.interval = interval
        self._stopping = False
        self._task = None

    @property
    def stopping(self):
        return not self.queue.allowed_to_add

    def begin_stopping(self):
        self.queue.allowed_to_add = False

    def start(self):
        if self._task is not None:
            raise RuntimeError("This queue is already running")
        self._task = asyncio.create_task(self.run())

    async def run(self):
        while True:
            if self.queue.empty():
                await asyncio.sleep(self.interval)
                continue
            else:
                await self.queue.act_on_top(raise_act_exc=False)
                await asyncio.sleep(self.interval)

    async def stop(self, cancel_task=True):
        if not self._task:
            raise RuntimeError("This queue is not started yet")
        if self.stopping:
            raise RuntimeError("This queue is already stopping")
        self.begin_stopping()
        if cancel_task and self._task and not self._task.done():
            self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
