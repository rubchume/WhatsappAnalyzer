import json

import matplotlib as mpl
import matplotlib.cm as cm
import networkx as nx
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
from scipy.optimize import minimize
from scipy.stats import norm

from src import whatsapp


class ChatNetwork(object):
    NORMALIZATION_TYPE_DEVIATION = "MLE_multinomial_distribution_difference_in_standard_deviations"
    NORMALIZATION_TYPE_CDF = "MLE_multinomial_distribution_CDF"

    def __init__(self, whatsapp_export_file=None):
        self.chat = whatsapp.read_chat(whatsapp_export_file) if whatsapp_export_file else None

    def draw(
            self,
            layout=nx.drawing.circular_layout,
            return_traces=False,
            node_traces=None,
            edge_traces=None,
            selected_nodes=None,
    ):
        if not (node_traces and edge_traces):
            node_traces, edge_traces = self.get_traces(layout)
        else:
            node_traces = json.loads(node_traces)
            edge_traces = json.loads(edge_traces)

        node_traces_filtered, edge_traces_filtered = self.filter_traces(node_traces, edge_traces, selected_nodes)

        if return_traces:
            return (
                go.Figure(data=edge_traces_filtered + node_traces_filtered, layout=self._graph_layout()),
                json.dumps(node_traces, cls=plotly.utils.PlotlyJSONEncoder),
                json.dumps(edge_traces, cls=plotly.utils.PlotlyJSONEncoder),
            )

        return go.Figure(data=edge_traces_filtered + node_traces_filtered, layout=self._graph_layout())

    @classmethod
    def filter_traces(cls, node_traces, edge_traces, selected_nodes=None):
        def node_belongs_to_selected_nodes(node_key):
            return node_key in selected_nodes if selected_nodes else False

        def edge_belongs_to_selected_nodes(edge_key):
            if not selected_nodes:
                return True

            node1, node2 = edge_key.split(":")
            if len(selected_nodes) == 1:
                return (
                    node1 in selected_nodes
                    or node2 in selected_nodes
                )

            return (
                node1 in selected_nodes
                and node2 in selected_nodes
            )

        def adapt_opacity(node, trace):
            if node_belongs_to_selected_nodes(node):
                trace["marker"]["opacity"] = 1
            else:
                trace["marker"]["opacity"] = 0.25

            return trace

        node_traces_filtered = [
            adapt_opacity(node, trace) for node, trace in node_traces.items()
        ]

        edge_traces_filtered = [
            trace
            for key, traces in edge_traces.items()
            for trace in traces
            if edge_belongs_to_selected_nodes(key)
        ]

        return node_traces_filtered, edge_traces_filtered

    def get_traces(self, layout=nx.drawing.circular_layout):
        node_positions, node_sizes, edges = self.get_drawing_parameters(layout)

        node_traces = self.get_node_traces(node_positions, node_sizes)
        edge_traces = self.get_edge_traces(node_positions, edges)

        return node_traces, edge_traces

    def get_drawing_parameters(self, layout):
        node_positions = self.node_positions(layout)
        edges = self.get_directed_edges(
            count="count", CDF=self.NORMALIZATION_TYPE_CDF, deviations=self.NORMALIZATION_TYPE_DEVIATION
        ).reset_index()
        node_sizes = pd.Series([
            edges.loc[edges["Target"] == node, "count"].sum()
            for node in node_positions.index
        ], index=node_positions.index)

        return node_positions, node_sizes, edges

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
            plot_bgcolor='rgba(128,128,128,1)',
            clickmode='event',
        )
        return layout_plotly

    def node_positions(self, layout=nx.drawing.circular_layout):
        pos = layout(self.get_directed_graph("count"))

        return (pd.DataFrame(pos, index=["X", "Y"])
                .transpose()
                .rename_axis(index="node"))

    @classmethod
    def get_node_traces(cls, node_positions, size_magnitude):
        size_magnitude_normalized = size_magnitude / size_magnitude.sum()
        radius = node_positions.apply(lambda g: np.linalg.norm(g), axis="columns").mean()
        circumference = radius * 2 * np.pi
        arc_longitude = circumference / len(size_magnitude)
        scale_factor = arc_longitude / 2 * np.sqrt(np.pi / size_magnitude_normalized.max())
        node_traces = {node: go.Scatter(
            x=(x,),
            y=(y,),
            mode='markers+text',
            name=f"{node} ({num*100:.2f}%)",
            marker={
                "symbol": 'circle',
                "size": np.sqrt(num) * scale_factor * 150,
                "opacity": 1,
            },
            text=node,
            textposition="middle center",
            hoverinfo="text",
            textfont={
                "color": "white",
                "family": "Arial, sans-serif"
            },
            customdata=[node],
        ) for node, (x, y, num) in pd.concat([node_positions, size_magnitude_normalized], axis="columns").iterrows()}
        return node_traces

    @classmethod
    def get_edge_traces(cls, node_positions, edges):
        def node_positions_to_edge_node_positions(edges):
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

        def get_edge_segment_traces(
            x_source,
            y_source,
            x_target,
            y_target,
            weight_source_to_target,
            weight_target_to_source,
            text=None,
        ):
            normalizer = mpl.colors.Normalize(vmin=0, vmax=1)
            mappable = mpl.cm.ScalarMappable(norm=normalizer, cmap=cm.bwr)

            num_segments = 40

            x_joints = np.linspace(x_source, x_target, num_segments + 1)
            y_joints = np.linspace(y_source, y_target, num_segments + 1)
            weight_joints = np.linspace(weight_source_to_target, weight_target_to_source, num_segments)

            return [go.Scatter(
                x=[x_origin, x_destination],
                y=[y_origin, y_destination],
                line={
                    "color": f"rgba{mappable.to_rgba(weight, bytes=True)}",
                    "width": 10,
                },
                mode="lines",
                showlegend=False,
                hovertext=text,
                hoverinfo="text",
            ) for x_origin, x_destination, y_origin, y_destination, weight in zip(
                x_joints[:-1],
                x_joints[1:],
                y_joints[:-1],
                y_joints[1:],
                weight_joints)]

        united_edges = cls.unite_symmetric_directed_edges(edges)
        edge_node_positions = node_positions_to_edge_node_positions(united_edges)

        edge_traces = {
            f"{source}:{target}":
            get_edge_segment_traces(
                x_source,
                y_source,
                x_target,
                y_target,
                CDF_source_to_target,
                CDF_target_to_source,
                text=(f"{source} -> {target}. Deviated {deviations_source_to_target:.2f} $\\sigma$ <br>"
                      f"{target} -> {source}. Deviated {deviations_target_to_source:.2f} $\\sigma$")
            )
            for edge_id, (
                source,
                x_source,
                y_source,
                target,
                x_target,
                y_target,
                CDF_source_to_target,
                CDF_target_to_source,
                deviations_source_to_target,
                deviations_target_to_source,
            )
            in pd.concat(
                [
                    edge_node_positions,
                    united_edges[[
                        "CDF_Source_to_Target",
                        "CDF_Target_to_Source",
                        "deviations_Source_to_Target",
                        "deviations_Target_to_Source"
                    ]]
                ],
                axis="columns"
            ).iterrows()
        }

        return edge_traces

    def get_nodes(self):
        return list(self.chat["User"].unique())

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

    def get_directed_edges(self, weight_normalization="no_normalization", **kwargs):
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

        kwargs_present = bool(kwargs)

        if weight_normalization == "no_normalization" and not kwargs_present:
            return multi_directed_edges

        return self.directed_edges_to_weighted(
            multi_directed_edges, normalization=weight_normalization, **kwargs
        )

    @classmethod
    def directed_edges_to_weighted(cls, directed_edges, normalization="count", **kwargs):
        directed_edges_count = (
            directed_edges.groupby(["Source", "Target"])["index"]
            .count()
        )

        normalization_columns = kwargs if kwargs else {"weight": normalization}

        weighted_edges = []
        for column_name, normalization_type in normalization_columns.items():
            if normalization_type == "count":
                weight = directed_edges_count.rename(column_name)

            elif (
                    normalization_type == "MLE_multinomial_distribution_CDF"
                    or normalization_type == "MLE_multinomial_distribution_difference_in_standard_deviations"
            ):
                expected_directed_edges = cls.get_expected_directed_edges(directed_edges)
                deviations = cls.standard_deviations_from_expected_value(directed_edges_count, expected_directed_edges)
                if normalization_type == "MLE_multinomial_distribution_difference_in_standard_deviations":
                    weight = deviations.rename(column_name)
                else:
                    weight = pd.Series(norm.cdf(deviations), index=deviations.index, name=column_name)

            elif normalization_type in ("out_edges", "in_edges"):
                normalization_fields = {"out_edges": "Source", "in_edges": "Target"}
                group_field = normalization_fields[normalization_type]
                weight = (
                    directed_edges_count
                    .groupby(level=group_field)
                    .transform(lambda group: group / group.sum())
                    .rename(column_name)
                )

            else:
                raise ValueError("Unknown normalization type")

            weighted_edges.append(weight)

        return pd.concat(weighted_edges, axis="columns")

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
        std_binomial = np.sqrt(variance_binomial).replace(0, 0.001)
        deviation = ((directed_edges_weighted - expected_directed_edges) / std_binomial).dropna()
        return deviation

    @classmethod
    def unite_symmetric_directed_edges(cls, directed_edges):
        def unite_edges_subgroup(group):
            nodeA = group["Source"].iloc[0]
            nodeB = group["Target"].iloc[0]

            weight_columns = group.columns.difference(["Source", "Target"])
            A_to_B_weights = (
                group
                .loc[group["Source"] == nodeA, weight_columns]
                .sum()
                .rename(index=lambda name: f"{name}_Source_to_Target")
            )
            B_to_A_weights = (
                group
                .loc[group["Source"] == nodeB, weight_columns]
                .sum()
                .rename(index=lambda name: f"{name}_Target_to_Source")
            )

            return pd.concat([group[["Source", "Target"]].iloc[0], A_to_B_weights, B_to_A_weights], axis="index")

        pair_id = directed_edges[["Source", "Target"]].apply(lambda row: row.sort_values(ascending=True).str.cat(), axis="columns")
        return directed_edges.groupby(pair_id).apply(unite_edges_subgroup)
