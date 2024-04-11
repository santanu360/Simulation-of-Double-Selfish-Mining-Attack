from utils import generate_random_id
import logging

from DiscreteEventSim import EventType

logger = logging.getLogger(__name__)


class Transaction:
    def __init__(self, from_id, to_id, amount, timestamp):
        self.txn_id: str = generate_random_id(6)
        self.from_id: "Peer" = from_id
        self.to_id: "Peer" = to_id
        self.amount: float = amount
        self.timestamp: float = timestamp
        self.size: int = 1  # KB

        logger.debug(f"{self} <{EventType.TXN_CREATE}>: {self.description()}")

    @property
    def __dict__(self) -> dict:
        return {
            "txn_id": self.txn_id,
            "from_id": self.from_id.__repr__(),
            "to_id": self.to_id.__repr__(),
            "amount": self.amount,
            "timestamp": self.timestamp
        }

    def description(self) -> str:
        return (f"Transaction(id:{self.txn_id}, from:{(self.from_id)}, to:{(self.to_id)}, :{self.amount}, 󰔛:{self.timestamp})")

    def __repr__(self) -> str:
        return f"Txn(id={self.txn_id})"


class CoinBaseTransaction(Transaction):
    def __init__(self, to_id, timestamp):
        super().__init__(from_id=None, to_id=to_id, amount=50, timestamp=timestamp)
        logger.debug(
            f"{self} coinbase <{EventType.TXN_CREATE}>: {self.description()}")

    def description(self) -> str:
        return (f"CoinBase(id:{self.txn_id} to:{(self.to_id)}, :{self.amount}, 󰔛:{self.timestamp})")

    def __repr__(self) -> str:
        return f"CoinBaseTxn(id={self.txn_id})"
