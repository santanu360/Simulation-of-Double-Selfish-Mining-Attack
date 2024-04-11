from typing import Any
import logging

from Block import Block
from Transaction import CoinBaseTransaction
from DiscreteEventSim import simulation, Event, EventType
from BlockChainBase import BlockChainBase

logger = logging.getLogger(__name__)


class HonestBlockChain(BlockChainBase):

    def add_block(self, block: Block) -> bool:
        """
        validate and then add a block to the chain
        """
        if not self._validate_block(block):
            return False

        self._add_block(block)

        chain_len_upto_block = self._branch_length(block)
        self._validate_saved_blocks()
        if chain_len_upto_block > self._longest_chain_length:
            logger.debug(
                "%s <longest_chain> %s %s generating new block !!",
                self._peer_id,
                str(self._longest_chain_length),
                str(chain_len_upto_block),
            )
            self._longest_chain_length = chain_len_upto_block
            self._longest_chain_leaf = block
            self._generate_block()

    @property
    def _current_parent_block(self) -> Block:
        return self._longest_chain_leaf

    def _mine_success_handler(self, block: Block):
        self._add_block(block)
        self.publish_block(block)

    def _mine_fail_handler(self):
        return

    def _generate_block(self) -> Block:
        """
        Generate a new block
        """
        sorted(self._new_transactions, key=lambda x: x.timestamp)
        valid_transactions_for_longest_chain = []
        balances_upto_block = self._branch_balance(self._longest_chain_leaf).copy()
        for transaction in self._new_transactions:
            if balances_upto_block[transaction.from_id] < transaction.amount:
                continue
            balances_upto_block[transaction.from_id] -= transaction.amount
            balances_upto_block[transaction.to_id] += transaction.amount
            valid_transactions_for_longest_chain.append(transaction)

        # if len(valid_transactions_for_longest_chain) < config.BLOCK_TXNS_MIN_THRESHOLD:
        # logger.debug("<num_txns> not enough txns to mine a block !!",)
        # return

        new_block = Block(
            prev_block=self._longest_chain_leaf,
            transactions=valid_transactions_for_longest_chain,
            timestamp=simulation.clock,
            miner=self._peer_id,
            is_private=False,
        )
        self._mine_block_start(new_block)

    def _get_longest_chain(self):
        return self._get_chain(self._longest_chain_leaf)
