import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import pickle
import pygraphviz as pgv

from utils import create_directory


def draw_graph(peers):
    """
    Draws a graph of the peers and their connections.
    """
    G = nx.Graph()
    for peer in peers:
        G.add_node(peer.id)
        for connected_peer in peer.connected_peers:
            G.add_edge(peer.id, connected_peer.id)
    nx.draw(G, with_labels=True)
    plt.show()


def visualize_peer(peer, save_path):
    block_chain = peer["block_chain"]
    peer_id = peer["id"]
    G = pgv.AGraph(
        strict=False,
        directed=True,
        rankdir="LR",
    )
    G.graph_attr["label"] = f"Peer {peer_id} description: {peer['cpu_net_description']}"
    G.node_attr["shape"] = "circle"
    G.node_attr["style"] = "filled, solid"
    G.node_attr["width"] = 0.1

    for block in block_chain["blocks"]:
        label = f'{block["block_id"]}\n #txns: {len(block["transactions"])}\n timestamp: {round(block["timestamp"],2)}'
        if block["block_id"] != "gen_blk":
            label = (
                label
                + f'\n prev_hash: {block["prev_block"]["hash"]} \n miner: {block["miner"]}'
            )
        if "S01" in block["miner"]:
            G.add_node(block["block_id"], fillcolor="red", label="", tooltip=label)
        elif "S02" in block["miner"]:
            G.add_node(block["block_id"], fillcolor="orange", label="", tooltip=label)
        elif block["block_id"] == "gen_blk":
            G.add_node(block["block_id"], fillcolor="blue", label="", tooltip=label)
        else:
            G.add_node(block["block_id"], label="", tooltip=label)

        # if block["self"] in block_chain["longest_chain"]:
        #     G.add_node(block["block_id"], color="green", label="", tooltip=label)

        if block["is_private"]:
            G.get_node(block["block_id"]).attr["shape"] = "diamond"
            G.get_node(block["block_id"]).attr["height"] = 0.2
    for block in block_chain["blocks"]:
        if block["prev_block"] == "":
            continue
        prev_block = block["prev_block"]
        if block["self"] in block_chain["longest_chain"]:
            G.add_edge(prev_block["id"], block["block_id"], color="green")
        else:
            G.add_edge(prev_block["id"], block["block_id"])
    G.draw(save_path, prog="dot")


def visualize(results):
    create_directory("graphs")
    num_peers = len(results["peers"])
    for peer in results["peers"]:
        peer_id = peer["id"]
        visualize_peer(peer, f"graphs/peer_{peer_id}.svg")


if __name__ == "__main__":
    results = ""
    with open("results.pkl", "rb") as fileobj:
        results = pickle.load(fileobj)

    visualize(results=results)
