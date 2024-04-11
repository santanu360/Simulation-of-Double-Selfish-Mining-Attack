from typing import Any
import logging

from Block import Block, GENESIS_BLOCK
from Transaction import Transaction, CoinBaseTransaction
from config import CONFIG
from DiscreteEventSim import simulation, Event, EventType
from utils import expon_distribution
from visualisation import visualize_peer

logger = logging.getLogger(__name__)


class BlockChainBase:

    def __init__(
        self,
        cpu_power: float,
        broadcast_block_function: Any,
        peers: list[Any],
        owner_peer: Any,
    ):
        self._blocks: list[Block] = []
        self._peer_id: Any = owner_peer
        self._peers: list[Any] = peers
        self._new_transactions: list[Transaction] = []
        self._block_arrival_time: dict[Block, float] = {}
        self._broadcast_block: Any = broadcast_block_function

        self._current_mining_event: Event = None

        self._longest_chain_length: int = 0
        self._longest_chain_leaf: Block = None

        self._missing_parent_blocks: list[Block] = []

        self.avg_interval_time = CONFIG.AVG_BLOCK_MINING_TIME
        self.cpu_power: float = cpu_power

        self._init_genesis_block(peers)

    @property
    def __dict__(self) -> dict:
        blocks = list(map(lambda x: x.__dict__, self._blocks))
        blocks = sorted(blocks, key=lambda x: x["block_id"])
        block_arrival_times = list(
            map(
                lambda x: {x.__repr__(): self._block_arrival_time[x]},
                self._block_arrival_time,
            )
        )
        block_arrival_times = sorted(
            block_arrival_times, key=lambda x: list(x.values())[0]
        )
        longest_chain = self._get_longest_chain()
        longest_chain = list(map(lambda x: x.__repr__(), longest_chain))
        return {
            "blocks": blocks,
            "block_arrival_time": block_arrival_times,
            "longest_chain_length": self._longest_chain_length,
            "longest_chain_leaf": self._longest_chain_leaf.__repr__(),
            "avg_interval_time": self.avg_interval_time,
            "cpu_power": self.cpu_power,
            "longest_chain": longest_chain,
        }

    @property
    def peer_id(self) -> Any:
        return self._peer_id

    def __repr__(self) -> str:
        return f"BlockChain(👥:{self._peer_id})"

    def _init_genesis_block(self, peers: list[Any]):
        genesis_block = GENESIS_BLOCK
        self._blocks.append(genesis_block)
        self._longest_chain_length = 1
        self._longest_chain_leaf = genesis_block
        for peer in peers:
            self._branch_balance(genesis_block).update({peer: CONFIG.INITIAL_COINS})

    def _branch_length(self, block: Block):
        length = 0
        cur_block = block
        while cur_block:
            length += 1
            cur_block = cur_block.prev_block
        return length

    def _branch_balance(self, block: Block):
        if block == GENESIS_BLOCK:
            return {peer: CONFIG.INITIAL_COINS for peer in self._peers}
        prev_block = block.prev_block
        balances_upto_block = self._branch_balance(prev_block)
        for transaction in block.transactions:
            if transaction.from_id:
                balances_upto_block[transaction.from_id] -= transaction.amount
            balances_upto_block[transaction.to_id] += transaction.amount
        return balances_upto_block

    def _branch_transaction(self, block: Block):
        if block == GENESIS_BLOCK:
            return []
        prev_block = block.prev_block
        prev_branch_txns = self._branch_transaction(prev_block)
        for transaction in block.transactions:
            prev_branch_txns.append(transaction)
        return prev_branch_txns

    def _validate_block(self, block: Block) -> bool:
        """
        1. validate all transactions
        2. transactions are not repeated
        """
        prev_block = block.prev_block
        if prev_block not in self._blocks:
            logger.info(
                "%s block_dropped %s previous block missing !!", self.peer_id, block
            )
            if block not in self._missing_parent_blocks:
                self._missing_parent_blocks.append(block)
            return False
        if block in self._blocks:
            logger.info(
                "%s block_dropped %s block already in blockchain !!",
                self.peer_id,
                block,
            )
            return False
        for transaction in block.transactions:
            if not self._validate_transaction(transaction, prev_block):
                logger.info(
                    "%s block_dropped %s invalid transaction !!", self.peer_id, block
                )
                return False
            if transaction in self._branch_transaction(prev_block):
                logger.info(
                    "%s block_dropped %s %s transaction already in blockchain!!",
                    self.peer_id,
                    block,
                    transaction,
                )
                return False

        # logger.debug(f"Block {block} is valid")
        return True

    def _validate_transaction(
        self, transaction: Transaction, prev_block: Block
    ) -> bool:
        """
        1. no balance of any peer shouldn't go negative
        """
        balances_upto_block = self._branch_balance(prev_block)
        if (
            transaction.from_id
            and balances_upto_block[transaction.from_id] < transaction.amount
        ):
            # logger.debug(f"Transaction {transaction} is invalid")
            return False

        # logger.debug(f"Transaction {transaction} is valid")
        return True

    def _update_avg_interval_time(self, block: Block):
        raise NotImplementedError
        # prev_block = block.prev_block
        # num_blocks = len(self._blocks)
        # if num_blocks == 1:
        #     return
        # interval_time = block.timestamp - prev_block.timestamp
        # self.avg_interval_time = (
        #     self.avg_interval_time * (num_blocks-1) + interval_time) / num_blocks
        # logger.debug("Avg interval updated %s", self.avg_interval_time)

    def _update_block_arrival_time(self, block: Block):
        self._block_arrival_time[block] = simulation.clock

    def _add_block(self, block: Block) -> bool:
        """
        Add a block to the chain
        """
        for transaction in block.transactions:
            # if transaction in self._new_transactions:
            if isinstance(transaction, CoinBaseTransaction):
                continue
            if transaction in self._new_transactions:
                self._new_transactions.remove(transaction)

        self._blocks.append(block)
        self._update_block_arrival_time(block)
        # self._update_avg_interval_time(block)
        # self.plot_frame()
        logger.info("%s %s added", self.peer_id, block)

    def add_block(self, block: Block):
        raise NotImplementedError

    def _get_longest_chain(self) -> list[Block]:
        raise NotImplementedError

    def _mine_block_end(self, block: Block):
        raise NotImplementedError

    def _generate_block(self) -> Block:
        raise NotImplementedError

    def plot_frame(self):
        peer_json = self.peer_id.__dict__
        if not hasattr(self, "frame"):
            self.frame = 0
        self.frame += 1
        import os

        os.makedirs(f"frames/peer_{self.peer_id.id}", exist_ok=True)
        visualize_peer(
            peer_json, f"frames/peer_{self.peer_id.id}/{str(self.frame).zfill(3)}.svg"
        )
        logger.debug("%s plotting frame %s", self.peer_id, self.frame)

    def missing_parent_count(self):
        return len(self._missing_parent_blocks)

    def _validate_saved_blocks(self):
        remove_blocks = []
        for block in self._missing_parent_blocks:
            if self._validate_block(block):
                remove_blocks.append(block)
                self._add_block(block)
        for block in remove_blocks:
            self._missing_parent_blocks.remove(block)

    def _panic_validate_saved_blocks(self):
        logger.debug("%s start panic validate orphan blocks", self._peer_id)
        sorted_blocks = sorted(
            self._missing_parent_blocks, key=lambda x: x.timestamp, reverse=False
        )
        for block in sorted_blocks:
            if self._validate_block(block):
                self._add_block(block)
                if self._longest_chain_length < self._branch_length(block):
                    self._longest_chain_length = self._branch_length(block)
                    self._longest_chain_leaf = block

    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add a transaction to the chain
        """
        # if transaction in self._branch_transactions:
        # return
        self._new_transactions.append(transaction)
        if transaction.from_id == self._peer_id:
            return
        # if (
        #     not self._current_mining_event
        #     and len(self._new_transactions) >= CONFIG.BLOCK_TXNS_TARGET_THRESHOLD
        # ):
        #     self._generate_block()

    def _mine_block_start(self, block: Block):
        delay = expon_distribution(self.avg_interval_time / self.cpu_power)

        mine_finish_event = Event(
            EventType.BLOCK_MINE_FINISH,
            simulation.clock,
            delay,
            self._mine_block_end,
            (block,),
            f"mining block finished {block}",
        )
        self._current_mining_event = mine_finish_event
        simulation.enqueue(mine_finish_event)

    def _mine_block_end(self, block: Block):
        """
        Broadcast a block to all connected peers.
        """
        self._current_mining_event = None
        if block.prev_block == self._current_parent_block and self._validate_block(
            block
        ):
            logger.info(
                "%s <%s> %s", self._peer_id, EventType.BLOCK_MINE_SUCCESS, block
            )
            block.transactions.append(
                CoinBaseTransaction(self._peer_id, block.timestamp)
            )
            min_success_event = Event(
                EventType.BLOCK_MINE_SUCCESS,
                simulation.clock,
                0,
                self._mine_success_handler,
                (block,),
                f"{self._peer_id}->* broadcast {block}",
            )
            simulation.enqueue(min_success_event)
        else:
            logger.info("%s <%s> %s", self._peer_id, EventType.BLOCK_MINE_FAIL, block)

    def _mine_success_handler(self, block: Block):
        raise NotImplementedError

    def _mine_fail_handler(self):
        raise NotImplementedError

    def _cancel_mining(self):
        """cancel current running mine event"""
        if self._current_mining_event:
            self._current_mining_event.cancel()

    def generate_block(self):
        self._generate_block()

    def _get_chain(self, block):
        chain = []
        cur_block = block
        while cur_block:
            chain.append(cur_block)
            cur_block = cur_block.prev_block
        return chain

    def flush_blocks(self):
        for block in self._blocks:
            self.publish_block(block)

    def publish_block(self, block: Block):
        self._broadcast_block(block)
        block.is_private = False

    def get_longest_chain(self) -> list[Block]:
        return self._get_longest_chain()

    def get_blocks(self) -> list[Block]:
        return self._blocks

    def validate_block(self, block: Block) -> bool:
        return self._validate_block(block)

    def add_block_core(self, block: Block):
        self._add_block(block)

    def override_mine_end_handler(self, fn):
        self._mine_block_end_handler = fn
