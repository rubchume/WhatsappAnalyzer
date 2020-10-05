import unittest

import pandas as pd

from src import network


class WhatsappReaderTests(unittest.TestCase):
    def test_create_multi_directed_graph_from_chat(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime(["2020-10-05 19:00", "2020-10-05 19:01", "2020-10-05 19:02"]),
                "User": ["Valen", "Bowen", "Ale"],
                "Message": ["Hola", "Ciao", "Que mais"]
            },
        )
        expected_edges = [
            ("Bowen", "Valen", 1, pd.to_datetime("2020-10-05 19:01")),
            ("Ale", "Bowen", 2, pd.to_datetime("2020-10-05 19:02"))
        ]
        # When
        g = network.chat_to_multi_directed_network(chat)
        # Then
        self.assertEqual({"Valen", "Bowen", "Ale"}, set(g.nodes()))
        self.assertEqual(expected_edges, list(g.edges(data="Time", keys=True)))
