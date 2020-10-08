import unittest

import pandas as pd
from pandas._testing import assert_frame_equal

from src import whatsapp


class WhatsappReaderTests(unittest.TestCase):
    WHATSAPP_EXPORT_NAME = "tests/helpers/ChatExample.txt"
    WHATSAPP_EXPORT_SPLIT_LINES_NAME = "tests/helpers/ChatExampleSplitLines.txt"
    WHATSAPP_EXPORT_SPLIT_LINES_WITH_BAR_NAME = "tests/helpers/ChatExampleSplitLinesWithBar.txt"
    WHATSAPP_EXPORT_CONTIGUOUS_SAME_USER_MESSAGES = "tests/helpers/ChatExampleContiguousMessages.txt"
    WHATSAPP_EXPORT_LOCATION = "tests/helpers/ChatExampleLocation.txt"

    def test_read_whatsapp_expport_and_return_dataframe(self):
        # Given
        expected_chat = pd.DataFrame(
            {
                "Time": [
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:49"),
                ],
                "User": ["Rubén", "Bowen", "Valen"],
                "Message": ["¿Hey qué tal?", "Bieenn, y tu", "¿Cómo estáis?"],
            },
            index=[1, 2, 3],
        )
        # When
        chat = whatsapp.read_chat(self.WHATSAPP_EXPORT_NAME)
        # Then
        assert_frame_equal(expected_chat, chat)

    def test_read_whatsapp_export_with_messages_split_in_multiple_lines(self):
        # Given
        expected_chat = pd.DataFrame(
            {
                "Time": [
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:49"),
                ],
                "User": ["Rubén", "Bowen", "Valen"],
                "Message": ["¿Hey qué tal?", "Bieenn\ny tu", "¿Cómo estáis?"],
            },
            index=[1, 2, 3],
        )
        # When
        chat = whatsapp.read_chat(self.WHATSAPP_EXPORT_SPLIT_LINES_NAME)
        # Then
        assert_frame_equal(expected_chat, chat)

    def test_read_whatsapp_export_with_messages_split_in_multiple_lines_with_bar(self):
        # Given
        expected_chat = pd.DataFrame(
            {
                "Time": [
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:49"),
                ],
                "User": ["Rubén", "Bowen", "Valen"],
                "Message": ["¿Hey qué tal?", "Bieenn\ny - tu", "¿Cómo estáis?"],
            },
            index=[1, 2, 3],
        )
        # When
        chat = whatsapp.read_chat(self.WHATSAPP_EXPORT_SPLIT_LINES_WITH_BAR_NAME)
        # Then
        assert_frame_equal(expected_chat, chat)

    def test_collapse_same_user_messages(self):
        # Given
        expected_chat = pd.DataFrame(
            {
                "Time": [
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:49"),
                ],
                "User": ["Rubén", "Bowen", "Valen"],
                "Message": [
                    "¿Hey qué tal?",
                    "Bieenn, y tu\nYa has terminado el grado?",
                    "¿Cómo estáis?",
                ],
            },
            index=[1, 2, 3],
        )
        # When
        chat = whatsapp.read_chat(
            self.WHATSAPP_EXPORT_CONTIGUOUS_SAME_USER_MESSAGES, collapse=True
        )
        # Then
        assert_frame_equal(expected_chat, chat)

    def test_do_not_collapse_same_user_messages(self):
        # Given
        expected_chat = pd.DataFrame(
            {
                "Time": [
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:46"),
                    pd.to_datetime("2020-05-10 15:49"),
                ],
                "User": ["Rubén", "Bowen", "Bowen", "Valen"],
                "Message": [
                    "¿Hey qué tal?",
                    "Bieenn, y tu",
                    "Ya has terminado el grado?",
                    "¿Cómo estáis?",
                ],
            },
            index=[1, 2, 3, 4],
        )
        # When
        chat = whatsapp.read_chat(
            self.WHATSAPP_EXPORT_CONTIGUOUS_SAME_USER_MESSAGES, collapse=False
        )
        # Then
        assert_frame_equal(expected_chat, chat)

    def test_do_not_identify_location_as_user(self):
        # Given
        expected_chat = pd.DataFrame(
            {
                "Time": [
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:44"),
                    pd.to_datetime("2020-05-10 15:49"),
                ],
                "User": ["Rubén", "Bowen", "Valen"],
                "Message": [
                    "¿Hey qué tal?",
                    "ubicación: https://maps.google.com/?q=38.9744246,-0.1414064",
                    "¿Cómo estáis?",
                ],
            },
            index=[1, 2, 3],
        )
        # When
        chat = whatsapp.read_chat(self.WHATSAPP_EXPORT_LOCATION)
        # Then
        assert_frame_equal(expected_chat, chat)
