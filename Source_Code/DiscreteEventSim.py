import inspect
from enum import Enum
from queue import PriorityQueue
from datetime import datetime, timedelta
import logging
import threading
from time import sleep
from tqdm import tqdm


import utils as UITLS

logger = logging.getLogger(__name__)


class EventType(Enum):
    TXN_CREATE = "TXN_CREATED"
    TXN_SEND = "TXN_SENT"
    TXN_RECEIVE = "TXN_RECEIVED"
    TXN_BROADCAST = "TXN_BROADCASTED"

    BLOCK_CREATE = "BLOCK_CREATED"
    BLOCK_SEND = "BLOCK_SENT"
    BLOCK_RECEIVE = "BLOCK_RECEIVED"
    BLOCK_BROADCAST = "BLOCK_BROADCASTED"
    BLOCK_ACCEPTED = "BLOCK_ACCEPTED"  # BLOCK VALIDATED, ACCEPTED INTO BLOCKCHAIN

    BLOCK_MINE_START = "BLOCK_MINE_STARTED"
    BLOCK_MINE_FINISH = "BLOCK_MINE_FINISHED"
    BLOCK_MINE_SUCCESS = "BLOCK_MINE_SUCCESSFUL"
    BLOCK_MINE_FAIL = "BLOCK_MINE_FAILED"

    def __str__(self):
        return f"{self.value}"


class Event:
    def __init__(
        self,
        event_type: EventType,
        created_at,
        delay,
        action,
        payload,
        meta_description="",
    ):
        self.id = UITLS.generate_random_id(6)
        self.type: EventType = event_type  # type of the event
        self.created_at = created_at  # when it is created
        self.delay = delay
        self.actionable_at = self.created_at + delay  # when it should be executed
        self.action = action  # what to execute
        self.payload = payload  # arguments for the action
        self.log_message = ""  # log message
        # additional information about the event
        self.meta_description = meta_description
        self.is_cancelled = False

        self.owner = "nan"
        try:
            caller_class = inspect.currentframe().f_back.f_locals["self"]
            self.owner = caller_class
            caller_class_name = caller_class.__class__.__name__
            if caller_class_name == "BlockChain":
                self.owner = f"{caller_class.peer_id}"
            if caller_class_name == "OneWayLINK":
                self.owner = f"{caller_class.from_peer}->{caller_class.to_peer}"
        except Exception:
            try:
                self.owner = inspect.currentframe().f_back.f_locals["module"]
            except Exception:
                pass

    def __gt__(self, other):
        return self.actionable_at > other.actionable_at

    def __lt__(self, other):
        return self.actionable_at < other.actionable_at

    @property
    def created_at_formatted(self):
        return format(round(self.created_at, 6), ",")

    @property
    def actionable_at_formatted(self):
        return format(round(self.actionable_at, 6), ",")

    def description(self):
        return f'📆({self.id} 🔀:{self.type} 👷:{self.owner} ⏰️:{self.created_at_formatted}-{self.actionable_at_formatted} 📦:{self.payload}) 📝:"{self.meta_description}"'

    def __repr__(self) -> str:
        return f"📆(🔀:{self.type} 👷:{self.owner} ⏰️:{self.created_at_formatted}-{self.actionable_at_formatted} 📦:{self.payload})"

    def cancel(self):
        """cancel the event from the event queue."""
        self.is_cancelled = True


class Simulation:
    def __init__(self):
        self.clock = 0.0
        self.event_queue = PriorityQueue()
        self.__run_hooks = []
        self.stop_sim = False
        self.force_stop = False

        self.blocks_created = 0

        self.completed_event_counter = tqdm(
            desc="Completed: ",
            unit="events",
            dynamic_ncols=True,
            position=0,
            leave=True,
        )
        self.scheduled_event_counter = tqdm(
            desc="Scheduled: ",
            unit="events",
            dynamic_ncols=True,
            position=1,
            leave=True,
        )

    def count_block_creation(self):
        self.blocks_created += 1

    def __enqueue(self, event):
        self.event_queue.put(event)
        self.scheduled_event_counter.update(1)
        # logger.debug("Scheduled: %s", event)
        # logger.info(f"Event payload: {event.payload}\n")

    def enqueue(self, event):
        """
        Enqueue an event to the event queue.
        """
        if self.stop_sim:
            if event.type in [
                EventType.BLOCK_RECEIVE,
            ]:
                self.__enqueue(event)
            return
        self.__enqueue(event)

    def reg_run_hooks(self, fn):
        """
        Register a function to be called before running an event.
        """
        self.__run_hooks.append(fn)

    def __execute_run_hooks(self, event):
        """
        Run hooks for the event.
        """
        for hook in self.__run_hooks:
            hook(event)

    def __run_event(self, event):
        self.__execute_run_hooks(event)
        if self.force_stop:
            return
        if event.type in [EventType.TXN_SEND, EventType.BLOCK_SEND]:
            logger.debug("Running: %s", event)
            logger.debug("Details: %s", event.description())
        else:
            logger.info("Running: %s", event)

        if self.stop_sim and event.type == EventType.BLOCK_RECEIVE:
            event.action(*event.payload)
            return

        event.action(*event.payload)

    def __run_loop(self):
        while not self.event_queue.empty() and not self.force_stop:
            next_event = self.event_queue.get()
            if next_event.is_cancelled:
                continue
            self.clock = next_event.actionable_at
            self.__run_event(next_event)

            self.completed_event_counter.update(1)

    def run(self):
        """
        Start the simulation.
        """
        # self.is_running = True
        # self.__dequeue_timer()
        self.__run_loop()


simulation = Simulation()
