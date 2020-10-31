import json

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

from src.chat_network import ChatNetwork


def create_app_layout(plotly_figure=None):
    return html.Div(
        [
            dcc.Graph(id="network-hot-cold", figure=plotly_figure, config={"displayModeBar": False}),
        ],
        id="network-graph"
    )


app = DjangoDash('NetworkGraph')
app.layout = create_app_layout()


@app.expanded_callback(
    Output('network-hot-cold', 'figure'),
    [Input('network-hot-cold', 'clickData')]
    )
def nodes_selected_callback(clickData, **kwargs):
    node_traces = kwargs["request"].session["node_traces"]
    edge_traces = kwargs["request"].session["edge_traces"]
    selected_nodes = kwargs["request"].session["selected_nodes"]

    if clickData:
        clicked_node = clickData["points"][0]["customdata"]
        if clicked_node in selected_nodes:
            selected_nodes.remove(clicked_node)
        else:
            selected_nodes.append(clicked_node)

    return ChatNetwork().draw(node_traces=node_traces, edge_traces=edge_traces, selected_nodes=selected_nodes)
