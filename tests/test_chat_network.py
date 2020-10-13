import unittest

import pandas as pd
from pandas._testing import assert_series_equal

from src.chat_network import ChatNetwork


class ChatNetworkTests(unittest.TestCase):
    def test_create_multi_directed_graph_from_chat(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime(
                    [
                        "2020-10-05 19:00",
                        "2020-10-05 19:01",
                        "2020-10-05 19:02",
                        "2020-10-05 19:03",
                        "2020-10-05 19:04",
                    ]
                ),
                "User": ["Valen", "Bowen", "Ale", "Bowen", "Ale"],
                "Message": ["Hola", "Ciao", "Que mais", "Bien and you?", "Muy bieeen"],
            },
        )
        expected_edges = [
            ("Bowen", "Valen", 1, pd.to_datetime("2020-10-05 19:01")),
            ("Bowen", "Ale", 3, pd.to_datetime("2020-10-05 19:03")),
            ("Ale", "Bowen", 2, pd.to_datetime("2020-10-05 19:02")),
            ("Ale", "Bowen", 4, pd.to_datetime("2020-10-05 19:04")),
        ]
        # When
        chat_network = ChatNetwork()
        chat_network.chat = chat
        g = chat_network.get_multi_directed_graph()
        # Then
        self.assertEqual({"Valen", "Bowen", "Ale"}, set(g.nodes()))
        self.assertEqual(expected_edges, list(g.edges(data="Time", keys=True)))

    def test_create_directed_graph_with_weights_from_chat(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime(
                    [
                        "2020-10-05 19:00",
                        "2020-10-05 19:01",
                        "2020-10-05 19:02",
                        "2020-10-05 19:03",
                        "2020-10-05 19:04",
                    ]
                ),
                "User": ["Valen", "Bowen", "Ale", "Bowen", "Ale"],
                "Message": ["Hola", "Ciao", "Que mais", "Bien and you?", "Muy bieeen"],
            },
        )
        network_chat = ChatNetwork()
        network_chat.chat = chat
        expected_edges = [
            ("Ale", "Bowen", 2),
            ("Bowen", "Ale", 1),
            ("Bowen", "Valen", 1),
        ]
        # When
        g = network_chat.get_directed_graph(weight_normalization="count")
        # Then
        self.assertEqual({"Valen", "Bowen", "Ale"}, set(g.nodes()))
        self.assertEqual(expected_edges, list(g.edges(data="weight")))

    def test_create_directed_graph_with_out_edges_normalized_weights_from_chat(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime(
                    [
                        "2020-10-05 19:00",
                        "2020-10-05 19:01",
                        "2020-10-05 19:02",
                        "2020-10-05 19:03",
                        "2020-10-05 19:04",
                    ]
                ),
                "User": ["Valen", "Bowen", "Ale", "Bowen", "Ale"],
                "Message": ["Hola", "Ciao", "Que mais", "Bien and you?", "Muy bieeen"],
            },
        )
        network_chat = ChatNetwork()
        network_chat.chat = chat
        expected_edges = [
            ("Ale", "Bowen", 1),
            ("Bowen", "Ale", 0.5),
            ("Bowen", "Valen", 0.5),
        ]
        # When
        g = network_chat.get_directed_graph(weight_normalization="out_edges")
        # Then
        self.assertEqual({"Valen", "Bowen", "Ale"}, set(g.nodes()))
        self.assertEqual(expected_edges, list(g.edges(data="weight")))

    def test_create_directed_graph_with_in_edges_normalized_weights_from_chat(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime(
                    [
                        "2020-10-05 19:00",
                        "2020-10-05 19:01",
                        "2020-10-05 19:02",
                        "2020-10-05 19:03",
                        "2020-10-05 19:04",
                        "2020-10-05 19:05",
                    ]
                ),
                "User": ["Valen", "Bowen", "Ale", "Bowen", "Ale", "Valen"],
                "Message": [
                    "Hola",
                    "Ciao",
                    "Que mais",
                    "Bien and you?",
                    "Muy bieeen",
                    "De lujo amiga",
                ],
            },
        )
        network_chat = ChatNetwork()
        network_chat.chat = chat
        expected_edges = [
            ("Ale", "Bowen", 1),
            ("Bowen", "Ale", 0.5),
            ("Bowen", "Valen", 1),
            ("Valen", "Ale", 0.5),
        ]
        # When
        g = network_chat.get_directed_graph(weight_normalization="in_edges")
        # Then
        self.assertEqual({"Valen", "Bowen", "Ale"}, set(g.nodes()))
        self.assertEqual(expected_edges, list(g.edges(data="weight")))

    def test_create_directed_graph_with_expectation_normalized_weights_from_chat_does_not_fail(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime(
                    [
                        "2020-10-05 19:00",
                        "2020-10-05 19:01",
                        "2020-10-05 19:02",
                        "2020-10-05 19:03",
                        "2020-10-05 19:04",
                        "2020-10-05 19:05",
                    ]
                ),
                "User": ["Valen", "Bowen", "Ale", "Bowen", "Ale", "Valen"],
                "Message": [
                    "Hola",
                    "Ciao",
                    "Que mais",
                    "Bien and you?",
                    "Muy bieeen",
                    "De lujo amiga",
                ],
            },
        )
        # When
        network_chat = ChatNetwork()
        network_chat.chat = chat
        network_chat.get_directed_graph(weight_normalization="expected_directed_edges")

    def test_get_expected_directed_edges(self):
        # Given
        directed_edges = pd.DataFrame(
            {
                "Source": ["Valen", "Ale", "Dani"],
                "Target": ["Ale", "Dani", "Ale"]
            }
        )
        expected_expected_directed_edges = pd.Series(
            [1.5, 1.5],
            index=pd.MultiIndex.from_tuples([("Ale", "Dani"), ("Dani", "Ale")], names=["Source", "Target"]),
            name="weight"
        )
        # When
        expected_directed_edges = ChatNetwork.get_expected_directed_edges(directed_edges)
        # Then
        assert_series_equal(expected_expected_directed_edges, expected_directed_edges)

    def test_draw_network_does_not_fail(self):
        # Given
        chat_file = "data/ChatMena.txt"
        network_chat = ChatNetwork(chat_file)
        # When
        network_chat.draw()
