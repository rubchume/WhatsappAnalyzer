import unittest

import pandas as pd
from pandas._testing import assert_frame_equal

from src import whatsapp


class WhatsappReaderTests(unittest.TestCase):
    WHATSAPP_EXPORT_NAME = "tests/helpers/ChatExample.txt"
    WHATSAPP_EXPORT_SPLIT_LINES_NAME = "tests/helpers/ChatExampleSplitLines.txt"
    WHATSAPP_EXPORT_SPLIT_LINES_WITH_BAR_NAME = "tests/helpers/ChatExampleSplitLinesWithBar.txt"

    def test_read_whatsapp_expport_and_return_dataframe(self):
        # Given
        expected_chat = pd.DataFrame({
            "Time": [pd.to_datetime("2020-05-10 15:44"), pd.to_datetime("2020-05-10 15:44"), pd.to_datetime("2020-05-10 15:49")],
            "User": ["Rubén", "Bowen", "Valen"],
            "Message": ["¿Hey qué tal?", "Bieenn, y tu", "¿Cómo estáis?"],
        }, index=[1,2,3])
        # When
        chat = whatsapp.read_chat(self.WHATSAPP_EXPORT_NAME)
        # Then
        assert_frame_equal(expected_chat, chat)

    def test_read_whatsapp_export_with_messages_split_in_multiple_lines(self):
        # Given
        expected_chat = pd.DataFrame({
            "Time": [pd.to_datetime("2020-05-10 15:44"), pd.to_datetime("2020-05-10 15:44"),
                     pd.to_datetime("2020-05-10 15:49")],
            "User": ["Rubén", "Bowen", "Valen"],
            "Message": ["¿Hey qué tal?", "Bieenn\ny tu", "¿Cómo estáis?"],
        }, index=[1,2,3])
        # When
        chat = whatsapp.read_chat(self.WHATSAPP_EXPORT_SPLIT_LINES_NAME)
        # Then
        assert_frame_equal(expected_chat, chat)

    def test_read_whatsapp_export_with_messages_split_in_multiple_lines_with_bar(self):
        # Given
        expected_chat = pd.DataFrame({
            "Time": [pd.to_datetime("2020-05-10 15:44"), pd.to_datetime("2020-05-10 15:44"),
                     pd.to_datetime("2020-05-10 15:49")],
            "User": ["Rubén", "Bowen", "Valen"],
            "Message": ["¿Hey qué tal?", "Bieenn\ny - tu", "¿Cómo estáis?"],
        }, index=[1,2,3])
        # When
        chat = whatsapp.read_chat(self.WHATSAPP_EXPORT_SPLIT_LINES_WITH_BAR_NAME)
        # Then
        assert_frame_equal(expected_chat, chat)
