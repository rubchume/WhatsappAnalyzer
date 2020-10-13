import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.optimize import minimize
from scipy.stats import norm

from src import whatsapp


class ChatNetwork(object):
    def __init__(self, whatsapp_export_file=None):
        self.chat = whatsapp.read_chat(whatsapp_export_file) if whatsapp_export_file else None

    def draw(self, layout=nx.drawing.circular_layout):
        node_positions = self.node_positions(layout)
        num_nodes = len(node_positions)
        edges = self.get_directed_edges(weight_normalization="expected_directed_edges").reset_index()
        node_sizes = pd.Series([
            edges.loc[(edges["Source"] == node) | (edges["Target"] == node), "weight"].sum() / (num_nodes - 1)
            for node in node_positions.index
        ], index=node_positions.index)

        node_traces = self.get_node_traces(node_positions, node_sizes)
        edge_traces = self.get_edge_traces(node_positions, edges)

        return go.Figure(data=edge_traces + node_traces, layout=self._graph_layout())

    @classmethod
    def _graph_layout(cls):
        layout_plotly = go.Layout(
            xaxis=go.layout.XAxis(
                range=[-1.25, 1.25],
                visible=False
            ),
            yaxis=go.layout.YAxis(
                visible=False,
                scaleanchor="x",
                scaleratio=1
            ),
            showlegend=True,
            plot_bgcolor='rgba(0,0,0,0)'
        )
        return layout_plotly

    def node_positions(self, layout=nx.drawing.circular_layout):
        pos = layout(self.get_directed_graph("count"))

        return (pd.DataFrame(pos, index=["X", "Y"])
                .transpose()
                .rename_axis(index="node"))

    @classmethod
    def get_node_traces(cls, node_positions, size_magnitude):
        node_traces = [go.Scatter(
            x=(x,),
            y=(y,),
            mode='markers+text',
            name=f"{node} ({num})",
            marker={
                "symbol": 'circle',
                "size": np.sqrt(num) * 60,
                "opacity": 1,
            },
            text=node,
            textposition="middle center",
            hoverinfo="text",
        ) for node, (x, y, num) in pd.concat([node_positions, size_magnitude], axis="columns").iterrows()]
        return node_traces

    @classmethod
    def get_edge_traces(cls, node_positions, edges):
        def node_positions_to_edge_node_positions():
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

        edge_node_positions = node_positions_to_edge_node_positions()
        lines_width = edges["weight"] * 20
        alphas = edges["weight"] / edges["weight"].max() * 0.8

        edge_traces = [go.Scatter(
            x=[x_source, x_target],
            y=[y_source, y_target],
            name=f"{source} -> {target}",
            mode='lines',
            line={
                "color": f'rgba(25,25,112,{alpha})',
                "width": width,
            }
            ,
            text=f"{source} -> {target}",
            hoverinfo='none',
            showlegend=False,
        ) for edge, (source, x_source, y_source, target, x_target, y_target, width, alpha)
            in pd.concat([edge_node_positions, lines_width, alphas], axis="columns").iterrows()]

        return edge_traces

    def get_directed_graph(self, weight_normalization="no_normalization"):
        directed_edges_weighted = self.get_directed_edges(weight_normalization)

        return nx.from_pandas_edgelist(
            directed_edges_weighted.reset_index(),
            source="Source",
            target="Target",
            edge_attr="weight",
            create_using=nx.DiGraph,
        )

    def get_multi_directed_graph(self):
        source_target = self.get_directed_edges()

        return nx.from_pandas_edgelist(
            source_target,
            source="Source",
            target="Target",
            edge_attr="Time",
            edge_key="index",
            create_using=nx.MultiDiGraph,
        )

    def get_directed_edges(self, weight_normalization="no_normalization"):
        multi_directed_edges = (
            pd.concat(
                [
                    self.chat["Time"],
                    self.chat["User"].rename("Source"),
                    self.chat["User"].shift(1).rename("Target"),
                ],
                axis="columns",
            )
            .dropna(axis="index")
            .reset_index(drop=False)
        )

        if weight_normalization == "no_normalization":
            return multi_directed_edges

        return self.directed_edges_to_weighted(
            multi_directed_edges, normalization=weight_normalization
        )

    @classmethod
    def directed_edges_to_weighted(cls, directed_edges, normalization="count"):
        directed_edges_count = (
            directed_edges.groupby(["Source", "Target"])["index"]
            .count()
            .rename("weight")
        )

        if normalization == "count":
            return directed_edges_count

        if normalization == "expected_directed_edges":
            expected_directed_edges = cls.get_expected_directed_edges(directed_edges)
            deviations = cls.standard_deviations_from_expected_value(directed_edges_count, expected_directed_edges)
            return pd.Series(norm.cdf(deviations), index=deviations.index, name="weight")

        normalization_fields = {"out_edges": "Source", "in_edges": "Target"}
        group_field = normalization_fields[normalization]
        return (
            directed_edges_count
            .groupby(level=group_field)
            .transform(lambda group: group / group.sum())
        )

    @classmethod
    def get_expected_directed_edges(cls, directed_edges):
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
            proportion_edges_expected.index.get_level_values("Source")
            != proportion_edges_expected.index.get_level_values("Target")
        ]

        return (proportion_edges_expected / proportion_edges_expected.sum()) * num_edges_by_node.sum()

    @classmethod
    def standard_deviations_from_expected_value(cls, directed_edges_weighted, expected_directed_edges):
        probability_source = expected_directed_edges.groupby("Target").transform(lambda group: group / group.sum())
        num_messages_to_target = expected_directed_edges.groupby("Target").transform(lambda group: group.sum())
        variance_binomial = probability_source * (1 - probability_source) * num_messages_to_target
        std_binomial = np.sqrt(variance_binomial)
        deviation = ((directed_edges_weighted - expected_directed_edges) / std_binomial).dropna()
        return deviation
