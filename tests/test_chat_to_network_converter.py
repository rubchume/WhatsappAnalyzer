import unittest

import pandas as pd

from src import network


class ChatToNetworkTests(unittest.TestCase):
    def test_create_multi_directed_graph_from_chat(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime([
                    "2020-10-05 19:00",
                    "2020-10-05 19:01",
                    "2020-10-05 19:02",
                    "2020-10-05 19:03",
                    "2020-10-05 19:04",
                ]),
                "User": ["Valen", "Bowen", "Ale", "Bowen", "Ale"],
                "Message": ["Hola", "Ciao", "Que mais", "Bien and you?", "Muy bieeen"]
            },
        )
        expected_edges = [
            ("Bowen", "Valen", 1, pd.to_datetime("2020-10-05 19:01")),
            ("Bowen", "Ale", 3, pd.to_datetime("2020-10-05 19:03")),
            ("Ale", "Bowen", 2, pd.to_datetime("2020-10-05 19:02")),
            ("Ale", "Bowen", 4, pd.to_datetime("2020-10-05 19:04")),
        ]
        # When
        g = network.chat_to_multi_directed_network(chat)
        # Then
        self.assertEqual({"Valen", "Bowen", "Ale"}, set(g.nodes()))
        self.assertEqual(expected_edges, list(g.edges(data="Time", keys=True)))

    def test_create_directed_graph_with_weights_from_chat(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime([
                    "2020-10-05 19:00",
                    "2020-10-05 19:01",
                    "2020-10-05 19:02",
                    "2020-10-05 19:03",
                    "2020-10-05 19:04",
                ]),
                "User": ["Valen", "Bowen", "Ale", "Bowen", "Ale"],
                "Message": ["Hola", "Ciao", "Que mais", "Bien and you?", "Muy bieeen"]
            },
        )
        expected_edges = [
            ("Ale", "Bowen", 2),
            ("Bowen", "Ale", 1),
            ("Bowen", "Valen", 1),
        ]
        # When
        g = network.chat_to_directed_network(chat, weight_normalization=False)
        # Then
        self.assertEqual({"Valen", "Bowen", "Ale"}, set(g.nodes()))
        self.assertEqual(expected_edges, list(g.edges(data="weight")))

    def test_create_directed_graph_with_out_edges_normalized_weights_from_chat(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime([
                    "2020-10-05 19:00",
                    "2020-10-05 19:01",
                    "2020-10-05 19:02",
                    "2020-10-05 19:03",
                    "2020-10-05 19:04",
                ]),
                "User": ["Valen", "Bowen", "Ale", "Bowen", "Ale"],
                "Message": ["Hola", "Ciao", "Que mais", "Bien and you?", "Muy bieeen"]
            },
        )
        expected_edges = [
            ("Ale", "Bowen", 1),
            ("Bowen", "Ale", 0.5),
            ("Bowen", "Valen", 0.5),
        ]
        # When
        g = network.chat_to_directed_network(chat, weight_normalization="out_edges")
        # Then
        self.assertEqual({"Valen", "Bowen", "Ale"}, set(g.nodes()))
        self.assertEqual(expected_edges, list(g.edges(data="weight")))

    def test_create_directed_graph_with_in_edges_normalized_weights_from_chat(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime([
                    "2020-10-05 19:00",
                    "2020-10-05 19:01",
                    "2020-10-05 19:02",
                    "2020-10-05 19:03",
                    "2020-10-05 19:04",
                    "2020-10-05 19:05",
                ]),
                "User": ["Valen", "Bowen", "Ale", "Bowen", "Ale", "Valen"],
                "Message": ["Hola", "Ciao", "Que mais", "Bien and you?", "Muy bieeen", "De lujo amiga"]
            },
        )
        expected_edges = [
            ("Ale", "Bowen", 1),
            ("Bowen", "Ale", 0.5),
            ("Bowen", "Valen", 1),
            ("Valen", "Ale", 0.5),
        ]
        # When
        g = network.chat_to_directed_network(chat, weight_normalization="in_edges")
        # Then
        self.assertEqual({"Valen", "Bowen", "Ale"}, set(g.nodes()))
        self.assertEqual(expected_edges, list(g.edges(data="weight")))
