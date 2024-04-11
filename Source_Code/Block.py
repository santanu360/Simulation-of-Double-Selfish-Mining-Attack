from typing import Any
import random
from copy import deepcopy
from functools import reduce
from Transaction import Transaction, CoinBaseTransaction
import logging

from DiscreteEventSim import simulation, Event, EventType
from config import CONFIG
from utils import expon_distribution, generate_random_id
from visualisation import visualize_peer

logger = logging.getLogger(__name__)


class Block:

    def __init__(
        self,
        prev_block,
        transactions: list[Transaction],
        timestamp: float,
        miner: Any = None,
        is_private: bool = False,
        id: int = None,
    ):
        if id:
            self.block_id: int = id
        else:
            self.block_id: int = generate_random_id(4)
        self.prev_block: "Block" = prev_block
        self.transactions: list[Transaction] = transactions
        self.timestamp: float = timestamp
        self.miner: Any = miner
        self.is_private: bool = is_private

        self.prev_block_hash = hash(prev_block) if prev_block else None

        logger.info(f"{self} <{EventType.BLOCK_CREATE}> {self.description()}")

    @property
    def header(self) -> str:
        if self.block_id == 0:
            return hash("genesis block")
        if self.transactions == []:
            transaction_ids = "no transactions"
        else:
            transaction_ids = reduce(
                lambda a, b: a + b, map(lambda x: x.txn_id, self.transactions)
            )
        return (
            f"{self.block_id}-{self.prev_block_hash}-{self.timestamp}-{transaction_ids}"
        )

    @property
    def num_txns(self) -> int:
        return len(self.transactions)

    def __hash__(self) -> int:
        return hash(self.header)

    def __repr__(self) -> str:
        return f"Block(id={self.block_id})"

    @property
    def __dict__(self) -> dict:
        dict_obj = {
            "self": self.__repr__(),
            "block_id": self.block_id,
            "prev_block": "",
            "self_hash": self.__hash__(),
            "num_txns": self.num_txns,
            "transactions": sorted(
                list(map(lambda x: x.__dict__, self.transactions)),
                key=lambda x: x["txn_id"],
            ),
            "timestamp": self.timestamp,
            "prev_block_hash": self.prev_block_hash,
            "miner": self.miner.__repr__(),
            "is_private": self.is_private,
        }
        if self.prev_block:
            dict_obj.update(
                {
                    "prev_block": {
                        "id": self.prev_block.block_id,
                        "hash": self.prev_block.__hash__(),
                    }
                }
            )
        return dict_obj

    def description(self) -> str:
        """
        detailed description of block
        """
        return f"Block id:{self.block_id} 󰔛:{self.timestamp} prev_block:{self.prev_block} txns:{self.transactions} miner:{self.miner}"

    @property
    def size(self) -> int:
        """
        size in kB
        """
        return len(self.transactions) + 1


def gen_genesis_block():
    """
    Generate genesis block
    """
    genesis_block = Block(None, [], 0, "none")
    genesis_block.block_id = "gen_blk"
    return genesis_block


GENESIS_BLOCK = gen_genesis_block()
