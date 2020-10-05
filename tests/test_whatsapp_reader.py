import unittest

import pandas as pd
from pandas._testing import assert_frame_equal

from ..src import whatsapp


class WhatsappReaderTests(unittest.TestCase):
    WHATSAPP_EXPORT_NAME = "helpers/ChatExample.txt"

    def test_read_whatsapp_expport_and_return_dataframe(self):
        # Given
        expected_chat = pd.DataFrame({
            "Time": [pd.to_datetime("2020-10-05 15:44"), pd.to_datetime("2020-10-05 15:44"), pd.to_datetime("2020-10-05 15:49")],
            "User": ["Rubén", "Bowen", "Valen"],
            "Message": ["¿Hey qué tal?", "Bieenn, y tu", "Como estáis"],
        })
        # When
        chat = whatsapp.read_chat(self.WHATSAPP_EXPORT_NAME)
        # Then
        assert_frame_equal(expected_chat, chat)
