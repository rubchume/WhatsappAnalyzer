import unittest

import pandas as pd
from pandas._testing import assert_frame_equal, assert_series_equal
import plotly.graph_objects as go

from src.chat_network import ChatNetwork


class ChatNetworkTests(unittest.TestCase):
    WHATSAPP_EXPORT_NAME = "tests/helpers/ChatExample.txt"

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
        network_chat.get_directed_graph(weight_normalization="MLE_multinomial_distribution_CDF")

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

    def test_unite_symmetric_edges(self):
        # Given
        directed_edges = pd.DataFrame(
            {
                "Source": ["Valen", "Ale", "Dani"],
                "Target": ["Ale", "Dani", "Ale"],
                "weight": [1, 2, 3]
            }
        )
        expected_united_edges = pd.DataFrame(
            {
                "Source": ["Ale", "Valen"],
                "Target": ["Dani", "Ale"],
                "weight_Source_to_Target": [2, 1],
                "weight_Target_to_Source": [3, 0]
            },
            index=["AleDani", "AleValen"]
        )
        # When
        united_edges = ChatNetwork.unite_symmetric_directed_edges(directed_edges)
        # Then
        assert_frame_equal(expected_united_edges, united_edges)

    def test_get_directed_edges_with_kwargs(self):
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
        expected_edges = pd.DataFrame(
            {
                "Cuantos": [2, 1, 1],
                "PorcentajeRecibidos": [1, 1, 1],
                "PorcentajeEnviados": [1, 0.5, 0.5],
            },
            index=pd.MultiIndex.from_tuples([("Ale", "Bowen"), ("Bowen", "Ale"), ("Bowen", "Valen")], names=["Source", "Target"])
        )
        chat_network = ChatNetwork()
        chat_network.chat = chat
        # When
        edges = chat_network.get_directed_edges(Cuantos="count", PorcentajeRecibidos="in_edges", PorcentajeEnviados="out_edges")
        # Then
        assert_frame_equal(expected_edges, edges)

    def test_get_directed_edges_with_unknown_normalization_raises_error(self):
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
        chat_network = ChatNetwork()
        chat_network.chat = chat
        # Then
        self.assertRaises(
            ValueError,
            chat_network.get_directed_edges,
            weight_normalization="unknown_normalization"
        )

    def test_get_directed_edges_does_not_fail_when_estimated_variance_is_0(self):
        # Given
        chat = pd.DataFrame(
            {
                "Time": pd.to_datetime(
                    [
                        "2020-10-05 19:02",
                        "2020-10-05 19:03",
                        "2020-10-05 19:04",
                    ]
                ),
                "User": ["Valen", "Bowen", "Ale"],
                "Message": ["Hola", "Ciao", "Que mais"],
            },
        )
        expected_edges = pd.DataFrame(
            {
                "weight": [0.0],
            },
            index=pd.MultiIndex.from_tuples([("Bowen", "Valen")], names=["Source", "Target"])
        )
        chat_network = ChatNetwork()
        chat_network.chat = chat
        # When
        edges = chat_network.get_directed_edges(weight_normalization=ChatNetwork.NORMALIZATION_TYPE_DEVIATION)
        # Then
        assert_frame_equal(expected_edges, edges)

    def test_get_no_edge_traces_and_just_soft_nodes_when_selected_nodes_are_null(self):
        # Given
        node_traces = {
            "user1": go.Scatter(
                x=(0,),
                y=(0,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
            "user2": go.Scatter(
                x=(2,),
                y=(2,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
        }
        expected_filtered_node_traces = [
            go.Scatter(
                x=(0,),
                y=(0,),
                marker={
                    "symbol": 'circle',
                    "opacity": 0.25,
                },
            ),
            go.Scatter(
                x=(2,),
                y=(2,),
                marker={
                    "symbol": 'circle',
                    "opacity": 0.25,
                },
            ),
        ]

        edge_traces = {
            "user1:user2": ["trace1", "trace2"],
            "user1:user3": ["trace3", "trace4"],
        }

        # When
        node_traces, edge_traces = ChatNetwork.filter_traces(node_traces, edge_traces, None)
        # Then
        self.assertEqual(expected_filtered_node_traces, node_traces)
        self.assertEqual(["trace1", "trace2", "trace3", "trace4"], edge_traces)

    def test_get_all_nodes_but_add_transparency_to_the_not_selected(self):
        # Given
        node_traces = {
            "user1": go.Scatter(
                x=(0,),
                y=(0,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
            "user2": go.Scatter(
                x=(2,),
                y=(2,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
            "user3": go.Scatter(
                x=(3,),
                y=(3,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
        }

        expected_filtered_node_traces = [
            go.Scatter(
                x=(0,),
                y=(0,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
            go.Scatter(
                x=(2,),
                y=(2,),
                marker={
                    "symbol": 'circle',
                    "opacity": 0.25,
                },
            ),
            go.Scatter(
                x=(3,),
                y=(3,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
        ]

        edge_traces = {
            "does_not_matter:doesnotmatter": ["trace1", "trace2"],
        }
        # When
        node_traces_filtered, _ = ChatNetwork.filter_traces(node_traces, edge_traces, ["user1", "user3"])
        # Then
        self.assertEqual(expected_filtered_node_traces, node_traces_filtered)

    def test_get_only_edge_traces_for_selected_nodes(self):
        # Given
        node_traces = {
            "user1": go.Scatter(
                x=(0,),
                y=(0,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
        }
        edge_traces = {
            "user3:user1": ["trace3", "trace4"],
            "user1:user4": ["trace1", "trace2"],
            "user2:user3": ["trace5", "trace6"],
        }
        # When
        _, edge_traces = ChatNetwork.filter_traces(node_traces, edge_traces, ["user1", "user3", "user2"])
        # Then
        self.assertEqual(["trace3", "trace4", "trace5", "trace6"], edge_traces)

    def test_get_all_traces_but_just_one_selected_node_when_there_is_only_one_selected_node(self):
        # Given
        node_traces = {
            "user1": go.Scatter(
                x=(0,),
                y=(0,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
            "user2": go.Scatter(
                x=(2,),
                y=(2,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
            "user3": go.Scatter(
                x=(3,),
                y=(3,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
        }

        expected_filtered_node_traces = [
            go.Scatter(
                x=(0,),
                y=(0,),
                marker={
                    "symbol": 'circle',
                    "opacity": 0.25,
                },
            ),
            go.Scatter(
                x=(2,),
                y=(2,),
                marker={
                    "symbol": 'circle',
                    "opacity": 1,
                },
            ),
            go.Scatter(
                x=(3,),
                y=(3,),
                marker={
                    "symbol": 'circle',
                    "opacity": 0.25,
                },
            ),
        ]

        edge_traces = {
            "user3:user1": ["trace3", "trace4"],
            "user1:user2": ["trace1", "trace2"],
            "user2:user3": ["trace5", "trace6"],
        }

        # When
        node_traces_filtered, edge_traces_filtered = ChatNetwork.filter_traces(node_traces, edge_traces, ["user2"])
        # Then
        self.assertEqual(expected_filtered_node_traces, node_traces_filtered)
        self.assertEqual(["trace1", "trace2", "trace5", "trace6"], edge_traces_filtered)

    def test_get_nodes(self):
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
        # When
        chat_network = ChatNetwork()
        chat_network.chat = chat
        # Then
        self.assertEqual(["Valen", "Bowen", "Ale"], chat_network.get_nodes())
