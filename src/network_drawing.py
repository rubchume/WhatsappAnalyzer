import networkx as nx
import numpy as np
import pandas as pd
import plotly.graph_objects as go

import src.network as net


def draw_network(network, layout=nx.drawing.circular_layout):
    node_positions = net.network_to_node_positions(network, layout)
    num_nodes = len(node_positions)
    directed_edges = net.network_to_directed_edges(network)
    edges = net.directed_edges_to_undirected(directed_edges)
    node_sizes = pd.Series([
        edges.loc[(edges["Source"] == node) | (edges["Target"] == node), "weight"].sum() / (num_nodes - 1)
        for node in node_positions.index
    ], index=node_positions.index)

    node_traces = get_node_traces(node_positions, node_sizes)
    edge_traces = get_edge_traces(node_positions, edges)

    return go.Figure(data=edge_traces + node_traces, layout=graph_layout())


def get_edge_traces(node_positions, edges):
    edge_node_positions = net.node_positions_to_edge_node_positions(node_positions, edges)
    lines_width = edges["weight"] * 5
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


def get_node_traces(node_positions, size_magnitude):
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


def graph_layout():
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
