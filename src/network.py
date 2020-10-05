import networkx as nx
import pandas as pd


def chat_to_multi_directed_network(chat):
    source_target = pd.concat(
        [
            chat["Time"],
            chat["User"].rename("Source"),
            chat["User"].shift(1).rename("Target")
        ],
        axis="columns"
    ).dropna(axis="index").reset_index(drop=False)

    return nx.from_pandas_edgelist(
        source_target,
        source="Source",
        target="Target",
        edge_attr="Time",
        edge_key="index",
        create_using=nx.MultiDiGraph,
    )
