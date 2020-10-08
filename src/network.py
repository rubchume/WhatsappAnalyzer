import networkx as nx
import pandas as pd


def chat_to_multi_directed_network(chat):
    source_target = chat_to_directed_edges(chat)

    return nx.from_pandas_edgelist(
        source_target,
        source="Source",
        target="Target",
        edge_attr="Time",
        edge_key="index",
        create_using=nx.MultiDiGraph,
    )


def chat_to_directed_network(chat, weight_normalization=False):
    directed_edges = chat_to_directed_edges(chat)
    directed_edges_weighted = directed_edges_to_weighted(
        directed_edges, normalization=weight_normalization
    )

    return nx.from_pandas_edgelist(
        directed_edges_weighted,
        source="Source",
        target="Target",
        edge_attr="weight",
        create_using=nx.DiGraph,
    )


def chat_to_directed_edges(chat):
    return (
        pd.concat(
            [
                chat["Time"],
                chat["User"].rename("Source"),
                chat["User"].shift(1).rename("Target"),
            ],
            axis="columns",
        )
        .dropna(axis="index")
        .reset_index(drop=False)
    )


def directed_edges_to_weighted(directed_edges, normalization=None):
    directed_edges_weighted = (
        directed_edges.groupby(["Source", "Target"])["index"]
        .count()
        .rename("weight")
        .reset_index()
    )

    if not normalization:
        return directed_edges_weighted

    normalization_fields = {"out_edges": "Source", "in_edges": "Target"}
    group_field = normalization_fields[normalization]

    directed_edges_weighted["weight"] = (directed_edges_weighted
                                         .groupby(group_field)["weight"]
                                         .transform(lambda group: group / group.sum()))

    return directed_edges_weighted
