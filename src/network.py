import networkx as nx
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm


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
        directed_edges_weighted.reset_index(),
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
    )

    if not normalization:
        return directed_edges_weighted

    if normalization == "expected_directed_edges":
        expected_directed_edges = get_expected_directed_edges(directed_edges)
        probability_source = expected_directed_edges.groupby("Target").transform(lambda group: group / group.sum())
        num_messages_to_target = expected_directed_edges.groupby("Target").transform(lambda group: group.sum())
        variance_binomial = probability_source * (1 - probability_source) * num_messages_to_target
        std_binomial = np.sqrt(variance_binomial)
        deviation = ((directed_edges_weighted - expected_directed_edges) / std_binomial).dropna()
        return pd.Series(norm.cdf(deviation), index=deviation.index, name="weight")

    normalization_fields = {"out_edges": "Source", "in_edges": "Target"}
    group_field = normalization_fields[normalization]

    return (
        directed_edges_weighted
        .groupby(level=group_field)
        .transform(lambda group: group / group.sum())
    )


def get_expected_directed_edges(directed_edges):
    num_edges_by_node = directed_edges["Target"].groupby(directed_edges["Target"]).count()
    proportion_edges = num_edges_by_node / num_edges_by_node.sum()
    nodes = proportion_edges.index
    num_nodes = len(nodes)

    def optimization_function(p, p_empirical):
        estimated_p_empirical = (p - p ** 2) / (p - p ** 2).sum()
        return np.linalg.norm(estimated_p_empirical - p_empirical)

    constraints = {'type': 'eq', 'fun': lambda p: p.sum() - 1}
    bounds = ((0, 1),) * num_nodes

    proportion_estimated = minimize(
        lambda p: optimization_function(p, proportion_edges),
        proportion_edges,
        tol=1e-8,
        constraints=constraints,
        bounds=bounds
    ).x

    proportion_estimated = pd.Series(proportion_estimated, index=nodes, name="weight")
    index = pd.MultiIndex.from_product([nodes, nodes], names=["Source", "Target"])
    proportion_edges_expected = (
        proportion_estimated.reindex(index, level="Source") * proportion_estimated.reindex(index, level="Target")
    )
    proportion_edges_expected = proportion_edges_expected.loc[
        proportion_edges_expected.index.get_level_values("Source") != proportion_edges_expected.index.get_level_values("Target")
    ]

    return (proportion_edges_expected / proportion_edges_expected.sum()) * num_edges_by_node.sum()


def network_to_edges_plot_line(network, layout=nx.drawing.circular_layout):
    edge_node_positions = network_to_edge_node_positions(network, layout)

    return edge_node_positions_to_edges_plot_line(edge_node_positions)


def edge_node_positions_to_edges_plot_line(edge_node_positions):
    edge_node_positions_melt = (edge_node_positions
                                .reset_index("edge")
                                .melt(
                                    id_vars=["edge"],
                                    value_vars=["X Source", "X Target", "Y Source", "Y Target"],
                                    ignore_index=False,
                                    var_name='Coordinate Type',
                                    value_name='Coordinate Value'
                                )
                                .sort_values(["edge", "Coordinate Type"])).set_index("edge")
    edge_node_positions_melt_x = edge_node_positions_melt[
        edge_node_positions_melt["Coordinate Type"].isin(["X Source", "X Target"])]
    edge_node_positions_melt_y = edge_node_positions_melt[
        edge_node_positions_melt["Coordinate Type"].isin(["Y Source", "Y Target"])]
    edge_line_x = pd.concat(
        [
            edge_node_positions_melt_x["Coordinate Value"],
            pd.Series(np.nan, index=edge_node_positions_melt_x.index.unique(), name="Coordinate Value")
        ],
        axis="index"
    ).sort_index(ascending=True).rename("X")
    edge_line_y = pd.concat(
        [
            edge_node_positions_melt_y["Coordinate Value"],
            pd.Series(np.nan, index=edge_node_positions_melt_y.index.unique(), name="Coordinate Value")
        ],
        axis="index"
    ).sort_index(ascending=True).rename("Y")
    return pd.concat([edge_line_x, edge_line_y], axis="columns")


def network_to_edge_node_positions(network, layout=nx.drawing.circular_layout):
    node_positions = network_to_node_positions(network, layout)
    edges = network_to_directed_edges(network)
    return node_positions_to_edge_node_positions(node_positions, edges)


def node_positions_to_edge_node_positions(node_positions, edges):
    edge_source_positions = (node_positions
                             .loc[edges["Source"]]
                             .reset_index()
                             .rename(columns={"X": "X Source", "Y": "Y Source", "node": "Source"})
                             .set_axis(edges.index, axis="index")
                             )

    edge_target_positions = (node_positions
                             .loc[edges["Target"]]
                             .reset_index()
                             .rename(columns={"X": "X Target", "Y": "Y Target", "node": "Target"})
                             .set_axis(edges.index, axis="index")
                             )

    return pd.concat([edge_source_positions, edge_target_positions], axis="columns")


def network_to_directed_edges(network):
    source, target, data = zip(*network.edges(data=True))

    return pd.concat([
        pd.DataFrame({"Source": source, "Target": target}),
        pd.DataFrame(data)
    ], axis="columns").rename_axis(index="edge")


def network_to_node_positions(network, layout=nx.drawing.circular_layout):
    pos = layout(network)

    return (pd.DataFrame(pos, index=["X", "Y"])
            .transpose()
            .rename_axis(index="node"))


def directed_edges_to_undirected(directed_edges):
    edges = directed_edges.apply(lambda row: row[["Source", "Target"]].sort_values().str.cat(), axis="columns")
    return (
        directed_edges
        .groupby(edges)
        .agg({"Source": "first", "Target":"first", "weight": lambda group: group.sum() / 2})
        .reset_index(drop=True)
    )
