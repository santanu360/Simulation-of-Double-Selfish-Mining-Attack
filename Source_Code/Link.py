import random
from typing import Union

from Transaction import Transaction
from Block import Block
from DiscreteEventSim import simulation, Event, EventType
from utils import expon_distribution


class OneWayLINK:
    def __init__(self, from_peer: "Peer", to_peer: "Peer", pij: float, cij: float):
        self.from_peer = from_peer
        self.to_peer = to_peer
        self.pij = pij
        self.cij = cij
        self.transmitted_messages = []

    def __get_delay(self, message: Union[Transaction, Block]):
        dij = expon_distribution((96 / 8) / self.cij)  # ms
        return self.pij + message.size / self.cij + dij  # ms

    def __link_delay_sim(self, message: Union[Transaction, Block]):
        delay = self.__get_delay(message)
        event_type = (
            EventType.TXN_RECEIVE
            if isinstance(message, Transaction)
            else EventType.BLOCK_RECEIVE
        )
        event_description = (
            f"{self.from_peer}->{self.to_peer}*; {message}; Δ:{round(delay,4)}ms"
        )
        receive_msg_event = Event(
            event_type,
            simulation.clock,
            delay,
            self.to_peer.receive_msg,
            (message, self.from_peer),
            event_description,
        )
        simulation.enqueue(receive_msg_event)

    def transmit(self, message: Union[Transaction, Block]):
        """
        Transmit a message to the other peer.
        """
        if message in self.transmitted_messages:
            return
        self.transmitted_messages.append(message)
        self.__link_delay_sim(message)

    def __repr__(self) -> str:
        return f"Link({self.from_peer}->{self.to_peer})"


class Link:
    def __init__(self, peer1: "Peer", peer2: "Peer"):
        self.peer1 = peer1
        self.peer2 = peer2
        # overall latency = ρij + |m|/cij + dij
        self.pij = random.uniform(10, 501)  # ms
        self.cij = 5 if peer1.is_slow_network or peer2.is_slow_network else 100  # Mbps
        self.cij = self.cij * 1024 / (8 * 1000)  # kB/ms

        self.link1 = OneWayLINK(
            from_peer=peer1, to_peer=peer2, pij=self.pij, cij=self.cij
        )
        self.link2 = OneWayLINK(
            from_peer=peer2, to_peer=peer1, pij=self.pij, cij=self.cij
        )

    def get_link(self, peer: "Peer"):
        """
        Get the one way link object for the given peer.
        """
        link = self.link1 if peer == self.peer1 else self.link2
        return link.transmit

    def __repr__(self):
        return f"Link({self.peer1}<->{self.peer2})"

    @property
    def __dict__(self) -> dict:
        return {"pij": self.pij, "cij": self.cij}
