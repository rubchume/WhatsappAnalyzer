import re

import pandas as pd


MESSAGE_COMPONENTS = ["Time", "User", "Message"]
HEADER_LINES = 3


def read_chat(chat_file_name):
    chat_lines = raw_chat_to_lines(chat_file_name)
    chat_messages = lines_to_messages(chat_lines)
    chat_components = messages_to_components(chat_messages)
    chat = clean_chat_components(chat_components)
    return chat


def raw_chat_to_lines(chat_file_name):
    with open(chat_file_name, "r", encoding="utf8") as f:
        return pd.Series(f.readlines()[HEADER_LINES:])


def lines_to_messages(chat_lines):
    def is_first_line_of_message(chat_lines):
        return chat_lines.str.match(".* - .*: ")

    is_first_line = is_first_line_of_message(chat_lines)
    message_index = is_first_line.cumsum()
    return chat_lines.groupby(message_index).agg(lambda group: group.str.cat())


def messages_to_components(chat_messages):
    time_regex = r"\d{1,2}/\d{1,2}/\d{1,2} \d{2}:\d{2}"
    regex = fr"^(?P<Time>{time_regex}) - (?P<User>.*): (?P<Message>.*)$"
    return chat_messages.str.extract(regex, flags=re.DOTALL)


def clean_chat_components(chat_components):
    chat_components["Time"] = chat_components["Time"].astype("datetime64")
    chat_components["Message"] = chat_components["Message"].str.strip()
    return chat_components
