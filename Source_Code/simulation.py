import random
import json
import pickle
import sys
from time import time, strftime
from tqdm import tqdm

from logger import init_logger
from network import is_connected, create_network, draw_graph
from DiscreteEventSim import simulation, Event, EventType
from Peer import Peer
from Block import Block
from BlockChainBase import BlockChainBase
from utils import (
    expon_distribution,
    create_directory,
    change_directory,
    copy_to_directory,
    clear_dir,
    delete_pattern,
)
from visualisation import visualize

from config import CONFIG

logger = init_logger()
START_TIME = time()
START_TIME = strftime("%Y-%m-%d_%H:%M:%S")


def log_peers(peers):
    """
    print(peers)
    """
    for peer in peers:
        logger.info("peer: %s", peer)
        logger.info("peer id: %s, neighbours: %s", peer.id, peer.connected_peers)
    logger.info(is_connected(peers))


def schedule_transactions(peers):
    """
    Schedule transactions
    """
    time = 0
    while simulation.event_queue.qsize() < CONFIG.NUMBER_OF_TRANSACTIONS:
        # Generate exponential random variable for interarrival time
        interarrival_time = expon_distribution(CONFIG.AVG_TXN_INTERVAL_TIME)
        # logger.debug(f"Interarrival time: {interarrival_time}")
        from_peer = random.choice(peers)
        new_txn_event = Event(
            EventType.TXN_CREATE,
            time,
            0,
            from_peer.generate_random_txn,
            (time,),
            f"{from_peer} create_txn",
        )
        time = time + interarrival_time
        simulation.enqueue(new_txn_event)
    # for i in range(CONFIG.NUMBER_OF_PEERS):
    miner_peer = random.choice(peers)
    time_stamp = time * 2 / 3
    new_block_event = Event(
        EventType.BLOCK_CREATE,
        time_stamp,
        0,
        miner_peer.block_chain.generate_block,
        (),
        f"{miner_peer} create_block",
    )
    simulation.enqueue(new_block_event)


def calculate_mpu_ratios(peers: list[Peer]):
    """
    Calculate the mining power unit ratios of the peers.
    """

    def calculate_mpu(peer: Peer):
        """
        Calculate the mining power unit of a peer.
        """
        block_chain: BlockChainBase = peer.block_chain
        longest_chain_blocks = block_chain.get_longest_chain()
        all_blocks = block_chain.get_blocks()

        num_blocks_public_chain_by_peer = 0
        for block in longest_chain_blocks:
            if block.miner == peer:
                num_blocks_public_chain_by_peer += 1
        num_blocks_public_chain_by_all = len(longest_chain_blocks)

        num_blocks_mined_by_peer = 0
        for block in all_blocks:
            if block.miner == peer:
                num_blocks_mined_by_peer += 1
        num_blocks_mined_by_all = len(all_blocks)

        if num_blocks_mined_by_peer == 0:
            mpu_adv = 0
        else:
            mpu_adv = num_blocks_public_chain_by_peer / num_blocks_mined_by_peer
        mpu_overall = num_blocks_public_chain_by_all / num_blocks_mined_by_all

        return {
            "peer": peer.__repr__(),
            "peer_id": peer.id,
            "type": peer.type,
            "mpu_adv": mpu_adv,
            "mpu_overall": mpu_overall,
            "num_blocks_public_chain_by_peer": num_blocks_public_chain_by_peer,
            "num_blocks_public_chain_by_all": num_blocks_public_chain_by_all,
            "num_blocks_mined_by_peer": num_blocks_mined_by_peer,
            "num_blocks_mined_by_all": num_blocks_mined_by_all,
        }

    mpu_ratios = []
    for peer in peers:
        mpu_ratios.append(calculate_mpu(peer))
    return mpu_ratios


def export_data(peers):
    """
    Export data to a file
    """
    raw_data = []
    json_data = []
    for peer in peers:
        json_data.append(peer.__dict__)
        raw_data.append(peer)
    mpu_ratios = calculate_mpu_ratios(peers)
    json_data = {"peers": json_data, "mpu_ratios": mpu_ratios}

    if CONFIG.SAVE_RESULTS:
        output_dir = f"output/{CONFIG.TEST_CASE_NAME}"
        create_directory(output_dir)
        copy_to_directory("blockchain_simulation.log", output_dir)
        copy_to_directory("config.py", output_dir)
        copy_to_directory("frames", output_dir)
        change_directory(output_dir)
    clear_dir("graphs")
    with open("results.json", "w") as f:
        json.dump(json_data, f, indent=4)
    with open("results.pkl", "wb") as f:
        pickle.dump(json_data, f)
    with open("summary.json", "w") as f:
        json.dump(mpu_ratios, f, indent=4)
    with open("config.txt", "w") as f:
        for key, value in CONFIG.__dict__().items():
            f.write(f"{key} = {value}\n")
    visualize(json_data)


def setup_progressbars():
    """
    Setup progress bars
    """
    pbar_txns = tqdm(
        desc="Txns: ", total=CONFIG.NUMBER_OF_TRANSACTIONS, position=2, leave=True
    )
    pbar_blocks = tqdm(
        desc="Blks: ",
        total=CONFIG.MAX_NUM_BLOCKS,
        position=3,
        leave=True,
    )
    return (pbar_txns, pbar_blocks)


successful_blocks_mined = 0


def update_progressbars(pbar_txns, pbar_blocks, event):
    """
    Update progress bars
    """
    global successful_blocks_mined
    # text = f"Events: {simulation.event_queue.qsize()}"
    # sys.stdout.write("\r" + text)
    # sys.stdout.flush()
    if event.type == EventType.TXN_CREATE:
        pbar_txns.update(1)
    elif event.type == EventType.BLOCK_MINE_SUCCESS:
        successful_blocks_mined += 1
        pbar_blocks.update(1)

    if successful_blocks_mined > CONFIG.MAX_NUM_BLOCKS:
        if simulation.stop_sim:
            return
        for peer in peers_network:
            peer.flush_blocks()
        print("Flushed blocks")
        simulation.stop_sim = True


if __name__ == "__main__":

    delete_pattern("frames/peer_*")

    peers_network = create_network(CONFIG.NUMBER_OF_PEERS)
    logger.info("Network created")
    print("Network created")
    # draw_graph(peers_network)

    log_peers(peers_network)
    schedule_transactions(peers_network)
    logger.info("Transactions scheduled")
    print("Transactions scheduled")

    logger.info("Simulation started")
    print("Simulation started")
    try:
        (pbar_txns, pbar_blocks) = setup_progressbars()
        simulation.reg_run_hooks(
            lambda event: update_progressbars(pbar_txns, pbar_blocks, event)
        )
        simulation.run()
        logger.info("Simulation ended")
    except KeyboardInterrupt:
        logger.info("Simulation interrupted")
        simulation.force_stop = True
    finally:
        for peer in peers_network:
            peer.block_chain._panic_validate_saved_blocks()
        pbar_txns.close()
        pbar_blocks.close()
        print("Simulation ended")

        for peer in peers_network:
            peer.block_chain.plot_frame()

        export_data(peers_network)
        logger.info("Data exported")
        print("Data exported")
