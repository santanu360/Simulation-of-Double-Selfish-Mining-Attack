from typing import Any
import logging

from Block import Block
from Transaction import CoinBaseTransaction
from DiscreteEventSim import simulation, Event, EventType
from BlockChainBase import BlockChainBase

logger = logging.getLogger(__name__)


class PrivateBlockChain(BlockChainBase):
    def __init__(
        self,
        cpu_power: float,
        broadcast_block_function: Any,
        peers: list[Any],
        owner_peer: Any,
    ):
        super().__init__(cpu_power, broadcast_block_function, peers, owner_peer)

        self._secret_chain_leaf: Block = None

        self._current_parent_block: Block = None

        self.secret_blocks: list[Block] = []
        self.state: int = 0

        self._current_parent_block = self._longest_chain_leaf
        self._generate_block()

    def add_block(self, block: Block) -> bool:
        """
        validate and then add a block to the chain
        """
        if not self._validate_block(block):
            return False

        self._add_block(block)

        self._validate_saved_blocks()

        if block.miner == self._peer_id:
            self._secret_chain_leaf = block
            self._update_lead()
        elif self._longest_chain_length < self._branch_length(block):
            self._longest_chain_length = self._branch_length(block)
            self._longest_chain_leaf = block
            self._update_lead()
        self.plot_frame()

    def _mine_success_handler(self, block: Block):
        self.secret_blocks.append(block)
        self.add_block(block)
        self._generate_block()

    def _mine_fail_handler(self):
        self._generate_block()

    def _generate_block(self) -> Block:
        """
        Generate a new block and
        start mining
        """
        sorted(self._new_transactions, key=lambda x: x.timestamp)
        valid_transactions_for_longest_chain = []
        # if len(self.secret_blocks):
        # parent_block = self.secret_blocks[-1]
        # else:

        parent_block = self._current_parent_block
        balances_upto_block = self._branch_balance(parent_block).copy()
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
            prev_block=parent_block,
            transactions=valid_transactions_for_longest_chain,
            timestamp=simulation.clock,
            miner=self._peer_id,
            is_private=True,
        )
        self._mine_block_start(new_block)

    def _get_longest_chain(self):
        chain1 = self._get_chain(self._longest_chain_leaf)
        chain2 = self._get_chain(self._secret_chain_leaf)
        return chain1 if len(chain1) > len(chain2) else chain2

    def _update_current_parent_block(self, block):
        """
        update the block on which mining is done
        if the block changes cancel mining and start a new mine
        """
        if self._current_parent_block == block:
            return
        self._cancel_mining()
        self._current_parent_block = block
        self._generate_block()

    def _calculate_new_lead(self):
        secret_branch_len = self._branch_length(self._secret_chain_leaf)
        public_branch_len = self._branch_length(self._longest_chain_leaf)
        return secret_branch_len - public_branch_len

    def _update_lead(self):
        new_lead = self._calculate_new_lead()
        old_state = self.state

        if new_lead < 0:
            # reject the whole selfish branch
            # start mining on public branch
            # move to state 0
            for block in self.secret_blocks:
                self._blocks.remove(block)
            self.secret_blocks = []
            self._secret_chain_leaf = self._longest_chain_leaf
            self._update_current_parent_block(self._secret_chain_leaf)
            self.state = 0

        elif self.state == 0.5:
            # current state is 0' and some block mined or received
            new_block = self._blocks[-1]
            if new_block.miner == self._peer_id:
                # if mine successful publish it and mine on that
                block = self.secret_blocks.pop(0)
                self.publish_block(block)
                self._update_current_parent_block(block)
            else:
                # else mine on the received block
                self._update_current_parent_block(new_block)
            self.state = 0

        elif self.state == 0:
            # current state is 0 and some block mined or received
            # start mining on last mined or received block
            new_block = self._blocks[-1]
            self._update_current_parent_block(new_block)
            if new_block.miner == self._peer_id:
                self.state = 1
            else:
                self.state = 0

        elif self.state == 1 and new_lead == 0:  # move to 0' state
            for block in self.secret_blocks:
                self.publish_block(block)
            self.secret_blocks = []
            self.state = 0.5
            self._update_current_parent_block(self._secret_chain_leaf)

        elif self.state == 2 and new_lead == 1:  # move to 0 state
            for block in self.secret_blocks:
                self.publish_block(block)
            self.secret_blocks = []
            self.state = 0
            self._update_current_parent_block(self._secret_chain_leaf)

        elif self.state > 2:
            new_block = self._blocks[-1]
            if new_block.miner == self._peer_id:
                # go to t+1 state
                self.state += 1
            else:
                # release one block and go to t-1 state
                block = self.secret_blocks.pop(0)
                self.publish_block(block)
                self.state -= 1
            self._update_current_parent_block(self._secret_chain_leaf)
        else:
            self._update_current_parent_block(self._secret_chain_leaf)
            self.state = new_lead

        logger.debug(
            "%s state change %s -> %s lead: %s",
            self.peer_id,
            old_state,
            self.state,
            new_lead,
        )
