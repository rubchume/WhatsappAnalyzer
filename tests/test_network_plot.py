import unittest
from unittest.mock import patch

import networkx as nx
import numpy as np
import pandas as pd
from pandas._testing import assert_frame_equal

from src import network, network_drawing, whatsapp


class NetworkPlotTests(unittest.TestCase):
    def test_network_to_directed_edges(self):
        # Given
        G = nx.DiGraph()
        G.add_weighted_edges_from([("Bowen", "Valen", 10), ("Bowen", "Ale", 20), ("Ale", "Bowen", 30)])
        expected_edges = pd.DataFrame([
            ("Bowen", "Valen", 10),
            ("Bowen", "Ale", 20),
            ("Ale", "Bowen", 30),
        ], columns=["Source", "Target", "weight"]).rename_axis(index="edge")
        # When
        edges = network.network_to_directed_edges(G)
        # Then
        assert_frame_equal(expected_edges, edges)

    def test_network_to_node_positions_does_not_fail(self):
        # Given
        G = nx.DiGraph()
        G.add_weighted_edges_from([("Bowen", "Valen", 10), ("Bowen", "Ale", 20), ("Ale", "Bowen", 30)])
        # When
        network.network_to_directed_edges(G)

    @patch("src.network.network_to_node_positions")
    def test_network_to_edge_node_positions(self, network_to_node_positions_mock):
        # Given
        G = nx.DiGraph()
        G.add_weighted_edges_from([("Bowen", "Valen", 10), ("Bowen", "Ale", 20), ("Ale", "Bowen", 30)])
        network_to_node_positions_mock.return_value = pd.DataFrame({
            "Bowen": [0, 0],
            "Ale": [1, 2],
            "Valen": [3, 4],
        }, index=["X", "Y"]).transpose().rename_axis(index="node")
        expected_edge_node_positions = pd.DataFrame(
            {
                "Source": ["Bowen", "Bowen", "Ale"],
                "X Source": [0, 0, 1],
                "Y Source": [0, 0, 2],
                "Target": ["Valen", "Ale", "Bowen"],
                "X Target": [3, 1, 0],
                "Y Target": [4, 2, 0],
            },
        ).rename_axis(index="edge")
        # When
        edge_node_positions = network.network_to_edge_node_positions(G)
        # Then
        assert_frame_equal(expected_edge_node_positions, edge_node_positions)

    @patch("src.network.network_to_node_positions")
    def test_network_to_edge_plot_line(self, network_to_node_positions_mock):
        G = nx.Graph()
        G.add_weighted_edges_from([
            ("Bowen", "Valen", 10),
            ("Bowen", "Ale", 20),
            ("Valen", "Dani", 30),
            ("Bowen", "Bowen", 1),
            ("Ale", "Dani", 1)
        ])

        network_to_node_positions_mock.return_value = pd.DataFrame({
            "Bowen": [1, 0],
            "Ale": [-1, 0],
            "Valen": [0, 1],
            "Dani": [0, -1],
        }, index=["X", "Y"]).transpose().rename_axis(index="node")

        expected_edge_node_positions = pd.DataFrame(
            {
                "X": [1, 0, np.nan, 1, -1, np.nan, 1, 1, np.nan, 0, 0, np.nan, -1, 0, np.nan],
                "Y": [0, 1, np.nan, 0, 0, np.nan, 0, 0, np.nan, 1, -1, np.nan, 0, -1, np.nan],
            },
            index=[0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4]
        ).rename_axis(index="edge")

        # When
        edge_plot_lines = network.network_to_edges_plot_line(G)

        # Then
        assert_frame_equal(expected_edge_node_positions, edge_plot_lines)

    def test_draw_network_does_not_fail(self):
        # Given
        chat_file = "data/ChatMena.txt"
        chat = whatsapp.read_chat(chat_file)
        G = network.chat_to_directed_network(chat, weight_normalization="expected_directed_edges")
        # When
        network_drawing.draw_network(G, layout=nx.drawing.circular_layout)
